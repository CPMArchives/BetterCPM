#!/usr/bin/env python3
"""Live checksum-enabled cpmsim media replacement and explicit-reset witness."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_ccp import assemble
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('baseline','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256']
    source=(ROOT/'tests/fixtures/conformance/media-change-probe.mac').read_text();program=a.output/'MEDIA.COM';assemble(Path.home()/'bin/z80asm',source,program,a.output/'probe.lst',0x100);(a.output/'probe.asm').write_text(source);shutil.copy2(__file__,a.output/'executed-runner.py')
    simulator=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';results={}
    for mode in ('write','reset'):
        w=a.output/mode;disks=w/'disks';disks.mkdir(parents=True);shutil.copy2(a.baseline/'diskdefs',w/'diskdefs')
        for d in 'ab':shutil.copy2(original,disks/f'drive{d}.dsk')
        def cpm(tool,image,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(image),*map(str,args)],cwd=w,capture_output=True,check=True)
        for name,data in [('MEDIA.COM',program.read_bytes()),('ANCHOR.DAT',b'PRIVATE CACHE EVICTION ANCHOR\x1a')]:
            f=w/name;f.write_bytes(data);cpm('cpmcp',disks/'drivea.dsk',f,'0:'+name)
        for label,name,data in [('old','OLD.TXT',b'ORIGINAL SENTINEL\r\n\x1a'),('new','NEW.TXT',b'REPLACEMENT SENTINEL\r\n\x1a')]:
            file=w/(label+'.dsk');shutil.copy2(original,file);cpm('cpmrm',file,'0:*.*');payload=w/name;payload.write_bytes(data);cpm('cpmcp',file,payload,'0:'+name)
        old,new=(w/'old.dsk').read_bytes(),(w/'new.dsk').read_bytes();assert sum(directory(w/'old.dsk',w/'diskdefs')[:128])%256!=sum(directory(w/'new.dsk',w/'diskdefs')[:128])%256
        (disks/'driveb.dsk').write_bytes(old);trace=w/'transcript.bin'
        def commands():
            yield((b'A0:MEDIA R\r' if mode=='reset' else b'A0:MEDIA W\r'),b'OR-0143 SWAP LOGGED B NOW\r\n',30)
            # Change only this private drive's existing inode while the guest is
            # blocked in CONIN. This cannot reach another emulator's media.
            with (disks/'driveb.dsk').open('r+b') as f:f.write(new);f.flush();os.fsync(f.fileno())
            yield(b'Y',b'OR-0143 RESET AND CREATE PASS' if mode=='reset' else b'Disk R/O',30)
            yield(b'',b'B0>_ ',30)
            yield(b'VER\r',b'BetterCP/M 0.90',30);yield(b'',b'B0>_ ',30)
            yield(b'A:\r',b'A0>_ ',30);yield(b'BYE\r',b'System halted',10)
        output=session(simulator,disks,commands(),trace);assert b'OR-0143 REPLACEMENT READ AND PROTECTED' in output and b'OR-0143 FAIL' not in output and b'OR-0143 FIXTURE' not in output
        after=(disks/'driveb.dsk').read_bytes()
        if mode=='write':assert after==new,'read-only rejection changed replacement media'
        else:
            before_directory=directory(w/'new.dsk',w/'diskdefs');after_directory=directory(disks/'driveb.dsk',w/'diskdefs');changed=[n for n in range(0,len(after_directory),32) if after_directory[n:n+32]!=before_directory[n:n+32]]
            assert len(changed)==1;row=after_directory[changed[0]:changed[0]+32];assert row[0]==0 and row[1:12]==b'CREATED TXT' and row[12:]==bytes(20)
            # Only that one directory entry may change; independent raw mapping
            # below confirms there are no writes elsewhere in the medium.
            definition=(w/'diskdefs').read_text().split('end',1)[0]
            def number(key):return int(re.search(r'\b'+key+r'\s+(\d+)',definition)[1])
            size,sectors,boot=number('seclen'),number('sectrk'),number('boottrk')
            skew=list(map(int,re.search(r'skewtab\s+([0-9,]+)',definition)[1].split(',')))
            logical,within=divmod(changed[0],size);track,sector=divmod(logical,sectors)
            offset=((boot+track)*sectors+skew[sector])*size+within
            expected=bytearray(new);expected[offset:offset+32]=row
            assert after==expected,'reset/create changed bytes outside the one directory entry'
        exported=w/'NEW-after.TXT';cpm('cpmcp',disks/'driveb.dsk','0:NEW.TXT',exported);assert exported.read_bytes()==b'REPLACEMENT SENTINEL\r\n\x1a'
        q=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks/'driveb.dsk')],cwd=w,capture_output=True,check=True);(w/'filesystem.txt').write_bytes(q.stdout+q.stderr)
        files=audit(a.baseline,report,w,disks/'drivea.dsk');results[mode]={'status':'PASS','replacement_disk_unchanged':mode=='write','replacement_file_preserved':True,'shipped_files':files,'transcript_sha256':sha(trace)}
    assert sha(original)==report['sha256']
    result={'status':'PASS','cards':['0143'],'baseline_sha256':report['sha256'],'simulator_sha256':sha(simulator),'cases':results,'scope':'Actual configured checksum-enabled cpmsim profile; private host inode replacement at a guest input gate, cache eviction, write refusal without mutation, explicit Function-37 reset and one empty-file creation. No real removable-drive timing claim.'};(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cpmsim media replacement protection/reset',a.output)


if __name__=='__main__':main()
