#!/usr/bin/env python3
"""Public DIR paging/abort qualification with the resident package unloaded."""
import argparse
import json
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--platform', choices=('z80pack','model4'), required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--image-dir',type=Path)
    a=p.parse_args(); report=a.report.resolve(); report.mkdir(parents=True,exist_ok=False)
    binary=(ROOT/'build/utilities/DIR.COM').read_bytes()
    fixtures=[(f'PG{i:03}.TXT',b'',1,0) for i in range(30)]
    prompt='MORE -- Space/ENTER for next page; ^C abort.'
    commands=['DIR /C=1 /P A1:PG*.TXT','DIR /C=1 /P /P /A /Z=S A1:PG*.TXT',
              'DIR /C=1 /P A1:PG*.TXT','DIR A1:PG*.TXT']
    if a.platform=='z80pack':
        import shutil
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',report/'disks')
        shutil.copy2(a.image_dir/'diskdefs',report/'diskdefs')
        disk=report/'disks/drivea.dsk'
        def cpm(tool,*args):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=report,check=True)
        cpm('cpmrm','0:*.*')
        cpm('cpmrm','2:*.*')
        cpm('cpmcp',ROOT/'build/utilities/CPX.COM','0:CPX.COM')
        cpm('cpmcp',ROOT/'build/utilities/DIR.COM','0:DIR.COM')
        for name,data,user,_ in fixtures:
            path=report/name;path.write_bytes(data);cpm('cpmcp',path,f'{user}:{name}')
        before={f.name:f.read_bytes() for f in (report/'disks').glob('*.dsk')}
        sequence=[(b'CPX UNLOAD RCP\r',b'A0>_ ',60),(b'B7:\r',b'B7>_ ',60)]
        for i,command in enumerate(commands):
            if i<3:
                sequence.append((command.encode()+b'\r',prompt.encode(),60))
                sequence.append(([b'X ',b'\r',b'\x03'][i],b'B7>_ ',60))
            else:sequence.append((command.encode()+b'\r',b'B7>_ ',60))
        output=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',sequence,report/'transcript.txt').decode(errors='replace')
        assert output.count(prompt)==3,output
        assert output.count('30 FILES, 0K TOTAL')==2,output
        assert output.count('30 FILES, 0S TOTAL')==1,output
        assert '^C' in output
        for f in (report/'disks').glob('*.dsk'):assert before[f.name]==f.read_bytes(),f
    else:
        disk=report/'a.dmk'
        original=medium([('DIR.COM',binary),('CPX.COM',(ROOT/'build/utilities/CPX.COM').read_bytes()),*fixtures])
        disk.write_bytes(original)
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
        invocation+=keys('CPX UNLOAD RCP\r')+['-id','3000','-it']+keys('A7:\r')+['-id','3000','-it']
        for i,command in enumerate(commands):
            invocation+=keys(command+'\r')
            if i<3:
                invocation+=['-iw',prompt,'-it']+keys(['X ','\r','\x03'][i])
                if i<2:invocation+=['-iw','30 FILES, 0'+('K' if i==0 else 'S')+' TOTAL']
            else:invocation+=['-iw','30 FILES, 0K TOTAL']
            invocation+=['-id','8000','-it']
        invocation+=['-ix']
        (report/'invocation.json').write_text(json.dumps(invocation,indent=2))
        run(invocation,cwd=report,timeout=600,check=True)
        for i in range(3):
            text=screen(report/f'trs80-text-{3+2*i}.bin')
            assert prompt in text and 'PG020' in text and 'PG021' not in text,text
        for index,summary in [(4,'30 FILES, 0K TOTAL'),(6,'30 FILES, 0S TOTAL'),(9,'30 FILES, 0K TOTAL')]:
            text=screen(report/f'trs80-text-{index}.bin')
            assert summary in text and text.rstrip().endswith('A7>'),text
        text=screen(report/'trs80-text-8.bin')
        assert '^C' in text and '30 FILES' not in text and text.rstrip().endswith('A7>'),text
        from test_model4_copy import files
        from add_cpm_file_to_dmk import extract_raw
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
        offset=FILESYSTEM_FIRST_SECTOR*512
        assert files(extract_raw(original)[offset:])==files(extract_raw(disk.read_bytes())[offset:])
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'cases':commands},indent=2))
    print('DIR public paging, Space/Enter, Ctrl-C DU restoration and next-invocation reset PASS')
if __name__=='__main__':main()
