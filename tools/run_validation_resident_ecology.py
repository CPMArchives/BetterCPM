#!/usr/bin/env python3
"""Capture the external resident-command procedures for ECOTEST 0569/75/77/79."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output','suite'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args()
    procedure=a.suite/'suite/src/ECOTEST.ASM'
    procedure_text=procedure.read_text()
    assert all('P'+item+':' in procedure_text for item in ('0569','0575','0577','0579'))
    report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image']
    assert report['target']=='z80pack' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True);work=Path(tempfile.mkdtemp(prefix='resident-ecology-',dir=a.output.resolve()))
    disks=work/'disks';disks.mkdir();shutil.copy2(a.baseline/'diskdefs',work/'diskdefs')
    for drive in 'ab':shutil.copy2(original,disks/f'drive{drive}.dsk')
    scratch=disks/'driveb.dsk'
    def cpm(*args):return subprocess.run(args,cwd=work,check=True,capture_output=True).stdout
    cpm('cpmrm','-T','raw','-f','bettercpm-default',str(scratch),'0:*.*')
    def install(file,drive='b'):
        cpm('cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),str(file),'0:'+file.name)
    state=work/'STATE.COM';assemble(Path.home()/'bin/z80asm',(ROOT/'tests/fixtures/conformance/returnstate.mac').read_text(),state,work/'state.lst',0x100);install(state,'a')
    keep=work/'KEEP.TXT';keep.write_bytes(b'ECOLOGY KEEP\r\n\x1a');install(keep)
    prefix=b'ECOTYPE\x07\r\n';typefile=work/'BYTE.TXT';payload=prefix+b'Z'*(128-len(prefix)-2)+b'\r\n';typefile.write_bytes(payload);install(typefile)
    trace=work/'transcript.bin';results=[];state0=b'STATE D=01 U=00 TOP=D501'
    def commands():
        prompt=b'B0>_ '
        yield (b'B:\r',prompt,30)
        for command,diagnostic in [(b'DIR MISSING.TXT',b'NO FILE'),(b'ERA MISSING.TXT',b'NO FILE'),(b'REN MISSING.TXT NEW.TXT',b'NO FILE'),(b'SAVE X BAD.COM',b'? SAVE'),(b'TYPE MISSING.TXT',b'NO FILE')]:
            offset=len(trace.read_bytes());yield(command+b'\r',prompt,30)
            delta=trace.read_bytes()[offset:];assert diagnostic in delta,(command,delta)
            yield(b'A0:STATE\r',state0,30);yield(b'',prompt,30)
            yield(b'TYPE KEEP.TXT\r',b'ECOLOGY KEEP',30);yield(b'',prompt,30)
            results.append({'item':'0579','command':command.decode(),'diagnostic':diagnostic.decode(),'caller_state':'B0/D501','status':'PASS'})
        offset=len(trace.read_bytes())
        yield(b'DIR KEEP.TXT\r',b'KEEP',30);yield(b'',prompt,30)
        assert b'B0: KEEP     TXT' in trace.read_bytes()[offset:], 'DIR did not list the fixture'
        yield(b'REN KEEP.TXT NEW.TXT\r',prompt,30)
        yield(b'TYPE NEW.TXT\r',b'ECOLOGY KEEP',30);yield(b'',prompt,30)
        yield(b'ERA NEW.TXT\r',prompt,30)
        yield(b'DIR NEW.TXT\r',b'NO FILE',30);yield(b'',prompt,30)
        yield(b'USER 3\r',b'B3>_ ',30)
        yield(b'A0:STATE\r',b'STATE D=01 U=03 TOP=D501',30);yield(b'',b'B3>_ ',30)
        yield(b'USER 0\r',prompt,30)
        offset=len(trace.read_bytes());yield(b'TYPE BYTE.TXT\r',prompt,30)
        assert payload in trace.read_bytes()[offset:], 'TYPE did not emit the exact graphic/CR/LF/BEL record'
        results.append({'item':'0577','record_bytes':128,'control_byte':'BEL (07h)','status':'PASS'})
        # Resident POKE primes the complete page without a transient/warm boot
        # between initialization and SAVE. A transient primer would be overwritten
        # by reconstruction and would not establish this oracle.
        for offset in range(0,256,16):
            command='POKE %04X '%(0x100+offset)+' '.join('%02X'%value for value in range(offset,offset+16))
            yield(command.encode()+b'\r',prompt,30)
        yield(b'SAVE 1 ECOSAVE.COM\r',prompt,30)
        yield(b'A:\r',b'A0>_ ',30)
        yield(b'BYE /Y\r',b'System halted',10)
    try:session(a.simulator.resolve(),disks,commands(),trace)
    except Exception as error:
        assert sha(original)==report['sha256'], 'reference image changed during incomplete run'
        (work/'incomplete.json').write_text(json.dumps({'status':'INCOMPLETE','error':str(error),'completed_observations':results},indent=2)+'\n');raise
    saved=work/'ECOSAVE.COM';cpm('cpmcp','-T','raw','-f','bettercpm-default',str(scratch),'0:ECOSAVE.COM',str(saved))
    assert saved.read_bytes()==bytes(range(256)), 'SAVE did not map exactly the complete page at 0100h'
    results.append({'item':'0575','bytes':256,'independent_saved_file_sha256':sha(saved),'status':'PASS'})
    cleanup=[(b'B:\r',b'B0>_ ',30),(b'ERA ECOSAVE.COM\r',b'B0>_ ',30),(b'ERA BYTE.TXT\r',b'B0>_ ',30),(b'A:\r',b'A0>_ ',30),(b'ERA STATE.COM\r',b'A0>_ ',30),(b'BYE /Y\r',b'System halted',10)]
    session(a.simulator.resolve(),disks,cleanup,work/'cleanup.bin')
    listing=cpm('cpmls','-T','raw','-f','bettercpm-default',str(scratch)).decode();(work/'scratch-directory.txt').write_text(listing)
    assert not listing.strip(),'scratch files remain: '+listing
    check=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(scratch)],cwd=work,capture_output=True,text=True)
    (work/'scratch-filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
    # Every shipped A0 file is independently compared at record granularity.
    unchanged=[]
    for item in report['included']:
        name=item['name'];user=item.get('user',0);pair=[]
        for label,image in [('before',original),('after',disks/'drivea.dsk')]:
            file=work/(label+'-'+name);cpm('cpmcp','-T','raw','-f','bettercpm-default',str(image),f'{user}:{name}',str(file));pair.append(file.read_bytes())
        assert pair[0]==pair[1],name+' changed';unchanged.append(name)
    a_listing=cpm('cpmls','-T','raw','-f','bettercpm-default',str(disks/'drivea.dsk')).decode()
    assert 'state.com' not in a_listing.lower(), 'A0 fixture remains'
    assert sha(original)==report['sha256']
    results.append({'item':'0569','commands':['DIR','ERA','REN','SAVE','TYPE','USER'],'caller_restored':'A0','scratch_files_removed':True,'status':'PASS'})
    (work/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':sha(original),'simulator_sha256':sha(a.simulator),'procedure_source_sha256':sha(procedure),'runner_sha256':sha(Path(__file__)),'state_source_sha256':sha(ROOT/'tests/fixtures/conformance/returnstate.mac'),'type_fixture_sha256':sha(typefile),'observations':results,'unchanged_shipped_files':unchanged,'scope':'external CCP transcripts for pinned ECOTEST manual cards, not fabricated aggregate suite PASS rows; cpmsim only'},indent=2)+'\n')
    print(work)


if __name__=='__main__':main()
