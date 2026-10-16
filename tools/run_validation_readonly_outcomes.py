#!/usr/bin/env python3
"""Qualify external file/disk read-only terminal outcomes on private cpmsim disks."""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','suite','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image']
    assert report['target']=='z80pack' and sha(original)==report['sha256']
    hashes={line.split()[1]:line.split()[0] for line in (a.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    a.output.mkdir(parents=True,exist_ok=True);work=Path(tempfile.mkdtemp(prefix='readonly-outcomes-',dir=a.output.resolve()))
    state=work/'STATE.COM';assemble(Path.home()/'bin/z80asm',(ROOT/'tests/fixtures/conformance/returnstate.mac').read_text(),state,work/'state.lst',0x100)
    results=[]
    for item in ('0368','0369','0379','0380','0381','0382','0383','0384'):
        run=work/item;disks=run/'disks';disks.mkdir(parents=True);shutil.copy2(a.baseline/'diskdefs',run/'diskdefs')
        def cpm(*args):return subprocess.run(args,cwd=run,check=True,capture_output=True).stdout
        for drive in 'abd':shutil.copy2(original,disks/f'drive{drive}.dsk')
        for drive in 'bd':cpm('cpmrm','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),'0:*.*')
        def install(file,drive):cpm('cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),str(file),'0:'+file.name)
        name='RANDTEST' if item in ('0368','0369') else 'DISKTEST'
        program=a.suite/f'suite/build/{name}.COM';assert sha(program)==hashes[name+'.COM']
        install(program,'a');install(state,'a')
        protected=disks/('driveb.dsk' if name=='RANDTEST' else 'drived.dsk')
        if name=='RANDTEST':
            install(a.suite/'suite/runtime-payload/BTRO.DAT','b')
            cpm('cpmchmod','-T','raw','-f','bettercpm-default',str(protected),'0444','0:BTRO.DAT')
        else:
            definition=(run/'diskdefs').read_text().split('end',1)[0]
            g={k:int(re.search(r'(?m)^\s*'+k+r'\s+(\d+)',definition)[1]) for k in ('tracks','boottrk','sectrk','seclen','blocksize','maxdir')}
            block=g['blocksize'];blocks=(g['tracks']-g['boottrk'])*g['sectrk']*g['seclen']//block;directory=(g['maxdir']*32+block-1)//block
            control=bytearray(128*128);control[-128:-120]=b'FULL-127'
            for filename,content in [('BTFULL.DAT',control),('BTREL.DAT',bytes(128)),('BTFILL.DAT',bytes((blocks-directory-(len(control)+block-1)//block-1)*block))]:
                file=run/filename;file.write_bytes(content);install(file,'d')
        before=sha(protected);shutil.copy2(protected,run/'protected-before.dsk')
        trace=run/'transcript.bin';diagnostic=b'File R/O' if name=='RANDTEST' else b'Disk R/O';drive=1 if name=='RANDTEST' else 3
        prompt=f'{chr(65+drive)}0>_ '.encode();expected=f'STATE D={drive:02X} U=00 TOP=D501'.encode()
        commands=[(b'B:\r',b'B0>_ ',30)]
        if name=='RANDTEST':commands.append((f'A0:{name} /{item}:REPORT\r'.encode(),diagnostic,30))
        else:commands += [(f'A0:{name} /{item}\r'.encode(),b'Enter its configured drive letter, or Q to quit (B-P or Q): ',30),(b'D',diagnostic,30)]
        # BetterCP/M spec 74 uses immediate WBOOT, unlike DRI's acknowledgement
        # workflow. Do not inject a key into a command processor already resumed.
        commands += [(b'',prompt,30),(b'A0:STATE\r',expected,30),(b'',prompt,30),(b'VER\r',b'BetterCP/M 0.90',30),(b'',prompt,30),(b'BYE\r',b'System halted',10)]
        try:output=session(a.simulator.resolve(),disks,commands,trace)
        except Exception as error:
            assert sha(original)==report['sha256']
            (run/'incomplete.json').write_text(json.dumps({'status':'INCOMPLETE','error':str(error),'protected_before_sha256':before,'protected_after_sha256':sha(protected)},indent=2)+'\n');raise
        assert diagnostic in output
        if name=='RANDTEST':
            assert b'REQUESTED_SCOPE /'+item.encode()+b'\r\n' in output
        else:
            assert item.encode()+b': requesting' in output
        assert b'RESULT FAIL' not in output and b'RESULT ERROR' not in output
        assert b'FAIL:' not in output and b'ERROR:' not in output and b' F  R ' not in output
        assert sha(protected)==before, 'protected disk changed: '+item
        ro_attribute=None
        if name=='RANDTEST':
            # Check every live BTRO extent's T1 bit independently in raw directory.
            definition=(run/'diskdefs').read_text().split('end',1)[0]
            geom={k:int(re.search(r'(?m)^\s*'+k+r'\s+(\d+)',definition)[1]) for k in ('boottrk','sectrk','seclen','maxdir')}
            offset=geom['boottrk']*geom['sectrk']*geom['seclen'];raw=protected.read_bytes();entries=[raw[offset+i*32:offset+(i+1)*32] for i in range(geom['maxdir'])]
            matches=[entry for entry in entries if entry[0]==0 and bytes(v&127 for v in entry[1:12])==b'BTRO    DAT']
            assert matches and all(entry[9]&128 for entry in matches);ro_attribute=True
        check=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(protected)],cwd=run,capture_output=True,text=True)
        (run/'filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
        shipped=[]
        for entry in report['included']:
            filename=entry['name'];user=entry.get('user',0);contents=[]
            for label,image in [('before',original),('after',disks/'drivea.dsk')]:
                extracted=run/(label+'-'+filename)
                cpm('cpmcp','-T','raw','-f','bettercpm-default',str(image),f'{user}:{filename}',str(extracted))
                contents.append(extracted.read_bytes())
            assert contents[0]==contents[1], filename+' changed on System Disk'
            shipped.append(filename)
        result={'item':item,'status':'PASS','program_sha256':sha(program),'diagnostic':diagnostic.decode(),'recovery_state':expected.decode(),'protected_disk_sha256':before,'whole_disk_unchanged':True,'read_only_attribute_verified':ro_attribute,'acknowledgement':'none required by existing BetterCP/M terminal profile','transcript_sha256':sha(trace),'unchanged_shipped_files':shipped}
        (run/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
    assert sha(original)==report['sha256']
    (work/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':sha(original),'simulator_sha256':sha(a.simulator),'runner_sha256':sha(Path(__file__)),'suite_protocol_sha256':sha(a.suite/'suite/TERMINAL-OUTCOME-CASES.md'),'accepted_profile':'BetterCP/M engineering spec 74/previous protected-disk qualification: diagnostic then immediate WBOOT, not DRI key-acknowledgement equivalence','cases':results,'scope':'eight external terminal procedures; no in-process suite PASS rows fabricated; cpmsim only'},indent=2)+'\n');print(work)


if __name__=='__main__':main()
