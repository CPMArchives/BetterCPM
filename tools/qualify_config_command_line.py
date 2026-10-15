#!/usr/bin/env python3
"""Qualify CONFIG CLI against protected startup records on private cpmsim media."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import build,parse
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);args=p.parse_args()
    parent=ROOT/'build/config-command-line';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(record):
        track,within=divmod(record,fmt.spt)
        return track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
    offsets=[offset(1),offset(2)]
    cases=[('show',b'CONFIG /SHOW\r',None,'',''),
           ('invalid',b'CONFIG /STARTUP="X" EXTRA\r',None,'',''),
           ('decline',b'CONFIG /STARTUP="SUBMIT STARTUP"\r',b'N','',''),
           ('save',b'CONFIG /STARTUP="SUBMIT STARTUP"\r',b'Y','','SUBMIT STARTUP'),
           ('quoted-ver',b'CONFIG /STARTUP=":VER /VER /B"\r',b'Y','',':VER /VER /B'),
           ('clear',b'CONFIG /STARTUP=""\r',b'Y',':VER /VER','')]
    for name,command,answer,old,want in cases:
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(args.diskdefs,here/'diskdefs');image=disks/'drivea.dsk';shutil.copy2(template,image)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM'],cwd=here,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(ROOT/'build/utilities/CONFIG.COM'),'0:CONFIG.COM'],cwd=here,check=True)
        data=bytearray(image.read_bytes());record=build(old,system_base=LAYOUT['SYSTEM'])
        for i,at in enumerate(offsets):data[at:at+128]=record[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        commands=[(command,b'(Y/N)? ' if answer else b'A0>_ ',20)]
        if answer:commands.append((answer,b'A0>_ ',20))
        commands.append((b'BYE\r',b'System halted',10))
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        after=image.read_bytes();actual=b''.join(after[at:at+128] for at in offsets)
        assert parse(actual,system_base=LAYOUT['SYSTEM'])==want,(name,trace)
        masked=bytearray(after)
        for at in offsets:masked[at:at+128]=before[at:at+128]
        assert bytes(masked)==before,(name,'changed bytes outside BCST')
        if name in ('show','invalid','decline'):assert after==before,name
        if name=='show':
            assert b'Active physical-drive profiles:' in trace and b'Active logical-drive bindings:' in trace
            assert b'Saved cold-start command: disabled' in trace and b'Pending changes: none' in trace
            assert b'Push ENTER' not in trace
        if name=='invalid':assert b'Invalid CONFIG usage.' in trace
        if answer==b'Y':assert b'saved and verified.' in trace and b'Invalid /VER usage' not in trace
        results.append({'case':name,'saved_command':want,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: CONFIG /SHOW, full validation, declined/confirmed startup saves, quoted /VER and clear; {work}')


if __name__=='__main__':main()
