#!/usr/bin/env python3
"""Smoke-test the expanded RCP carrier with resident DIR and reconstruction."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser();p.add_argument('--platform',choices=('z80pack','model4'),required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--image-dir',type=Path);a=p.parse_args()
    report=a.report.resolve();report.mkdir(parents=True,exist_ok=False)
    module=(ROOT/'build/cpx/RCP.CPX').read_bytes();(report/'RCP.CPX').write_bytes(module)
    commands=['CPX UNLOAD RCP','CPX LOAD RCP','DIR SELMARK.TXT','CPX LIST','DIR SELMARK.TXT']
    if a.platform=='z80pack':
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',report/'disks');shutil.copy2(a.image_dir/'diskdefs',report/'diskdefs')
        disk=report/'disks/drivea.dsk'
        for name in ('RCP.CPX','DIR.COM'):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disk),'0:'+name],cwd=report,check=True)
        marker=report/'SELMARK.TXT';marker.write_bytes(b'SELECTOR LIFECYCLE\r\n')
        for path in (report/'RCP.CPX',marker):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),'0:'+path.name],cwd=report,check=True)
        text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',
                     [(c.encode()+b'\r',b'A0>_ ',60) for c in commands],report/'transcript.txt').decode(errors='replace')
        assert text.count('SELMARK  TXT')>=2,text
    else:
        finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00\r\nSELECTOR FINISH\r\n$'
        extras=[('CPX.COM',(ROOT/'build/utilities/CPX.COM').read_bytes()),
                ('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),
                ('SELMARK.TXT',b'SELECTOR LIFECYCLE\r\n'),('FINISH.COM',finish),
                ('CASE.SUB',('\r\n'.join(commands+['FINISH'])+'\r\n').encode()+b'\x1a')]
        disk=report/'a.dmk';disk.write_bytes(medium(extras))
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
        invocation+=keys('SUBMIT CASE\r')+['-itime','0','-iw','SELECTOR FINISH','-id','3000','-it','-ix']
        (report/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
        run(invocation,cwd=report,timeout=900,check=True)
        text=screen(report/'trs80-text-1.bin');(report/'transcript.txt').write_text(text)
        assert 'SELECTOR FINISH' in text and text.rstrip().endswith('A0>'),text
        assert text.count('SELMARK  TXT')>=2,text
    assert 'RCP.CPX' in text,text
    (report/'harness.py').write_bytes(Path(__file__).read_bytes())
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,
        'carrier_sha256':hashlib.sha256(module).hexdigest(),'no_DIR_transient':True,
        'coverage':['unload/reload','resident DIR','WBOOT after CPX LIST']},indent=2)+'\n')
    print('Expanded RCP loading, resident dispatch and WBOOT: PASS')


if __name__=='__main__':main()
