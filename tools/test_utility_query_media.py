#!/usr/bin/env python3
"""Reaccept shipped /VER paths on both platforms using private System/Utilities."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as dmk
from build_z80pack_image import disk_definition,DEFAULT_FORMAT
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run as launch
from test_z80pack_sysgen_install import session
from utility_versions import identities,banner
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('system','utilities','output','simulator'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);metadata=identities();result={'status':'IN_PROGRESS','platforms':{}}
    for platform in ('z80pack','trs80gp'):
        w=a.output/platform;w.mkdir();r=json.loads((a.system/platform/'report.json').read_text());system=a.system/platform/r['image'];source=system.read_bytes()
        utilities=next(a.utilities.glob('*'+platform+('*.dsk' if platform=='z80pack' else '*.dmk')));ub=utilities.read_bytes()
        names=[x['name'][:-4] for x in r['included'] if x['name'].endswith('.COM') and x['name'][:-4] in metadata]
        cases=[('A:'+n,'BetterCP/M '+n if n not in ('DDT','DUMP','SQ','USQ','CR','UNCR','LZH','UNLZH') else n,n) for n in names]
        cases += [('B:'+n,n if n!='XSUB' else 'BetterCP/M XSUB',n) for n in ('DDT','DUMP','XSUB','SQ','USQ','CR','UNCR','LZH','UNLZH')]
        if platform=='z80pack':
            disks=w/'disks';disks.mkdir();(disks/'drivea.dsk').write_bytes(source)
            for letter in 'bcd':(disks/f'drive{letter}.dsk').write_bytes(ub)
            steps=[]
            for command,title,name in cases:
                version,build=metadata[name];expected=f'{title} {version} (Build {build:03d})'.encode()
                steps.extend([((command+' /VER ignored').encode()+b'\r',expected,30),(b'',b'A0>_ ',30)])
            transcript=session(a.simulator,disks,steps,w/'transcript.bin')
            assert b'Invalid /VER usage' not in transcript
            assert (disks/'driveb.dsk').read_bytes()==ub
            (w/'diskdefs').write_text(disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)))
            assert subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks/'drivea.dsk')],cwd=w,capture_output=True).returncode==0
        else:
            raw=extract_raw(source);directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
            for i in range(DIRECTORY_ENTRIES):
                at=directory+i*32
                if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=0xe5
            script=['RSX LOAD M4SCRN','RSX LOAD ADM3A']
            for i,(command,title,name) in enumerate(cases):
                mark=f'QUERY CASE {i:02d} DONE';program=f'Q{i:02d}'
                add_file(raw,program+'.COM',bytes.fromhex('110b010e09cd0500c30000')+(mark+'\r\n$').encode())
                script += [command+' /VER ignored',program]
            add_file(raw,'STARTUP.SUB',('\r\n'.join(script)+'\r\n\x1a').encode());disk=w/'a.dmk';disk.write_bytes(dmk(raw));(w/'b.dmk').write_bytes(ub)
            invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-d1',str(w/'b.dmk'),'-itime','60000']
            for i in range(len(cases)):invocation+=['-iw',f'QUERY CASE {i:02d} DONE','-id','120','-it']
            invocation+=['-ix'];(w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n');launch(invocation,cwd=w,timeout=1200)
            captures=sorted(w.glob('trs80-text-*'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==len(cases)
            for (command,title,name),capture in zip(cases,captures):
                screen=bytes(x&127 for x in capture.read_bytes()[:1920]);version,build=metadata[name]
                assert f'{title} {version} (Build {build:03d})'.encode() in screen,(command,screen)
            assert (w/'b.dmk').read_bytes()==ub
        assert system.read_bytes()==source and utilities.read_bytes()==ub
        result['platforms'][platform]={'status':'PASS','cases':len(cases),'commands':[x[0] for x in cases],'system_sha256':sha(source),'utilities_sha256':sha(ub),'utilities_unchanged':True}
        (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    result['status']='PASS';(a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS shipped utility /VER queries on both platforms')


if __name__=='__main__':main()
