#!/usr/bin/env python3
"""Qualify CONFIG CLI against protected startup records on private cpmsim media."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
import re
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import build,parse
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);args=p.parse_args()
    parent=ROOT/'build/config-defaults';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(record):
        track,within=divmod(record,fmt.spt)
        return track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
    offsets=[offset(1),offset(2)]
    probe=state_probe(work)
    for name in ('exit','decline','save'):
        old='';want='SUBMIT STARTUP' if name=='save' else ''
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(args.diskdefs,here/'diskdefs');image=disks/'drivea.dsk';shutil.copy2(template,image)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM'],cwd=here,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(ROOT/'build/utilities/CONFIG.COM'),'0:CONFIG.COM'],cwd=here,check=True)
        state=here/'STATE.COM';state.write_bytes(probe)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(state),'0:STATE.COM'],cwd=here,check=True)
        data=bytearray(image.read_bytes());record=build(old,system_base=LAYOUT['SYSTEM'])
        for i,at in enumerate(offsets):data[at:at+128]=record[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        commands=[(b'STATE\r',b'A0>_ ',20),
                  (b'CONFIG /DEFAULT\r',b'Push ENTER for menu.',20),
                  (b'\r',b'Your choice: [',20),(b'\x03',b'Your choice: [',20)]
        if name!='exit':
            commands += [(b'H',b'Your choice: [',20),(b'A',b'(Y/N)? ',20),
                         (b'Y' if name=='save' else b'N',b'Push ENTER for menu.' if name=='save' else b'Your choice: [',20)]
            if name=='save':commands.append((b'\r',b'Your choice: [',20))
            commands.append((b'\x03',b'Your choice: [',20))
        commands += [(b'\x03',b'A0>_ ',20),(b'STATE\r',b'A0>_ ',20),(b'BYE\r',b'System halted',10)]
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        after=image.read_bytes();actual=b''.join(after[at:at+128] for at in offsets)
        assert parse(actual,system_base=LAYOUT['SYSTEM'])==want,(name,trace)
        masked=bytearray(after)
        for at in offsets:masked[at:at+128]=before[at:at+128]
        assert bytes(masked)==before,(name,'changed bytes outside BCST')
        if name!='save':assert after==before,name
        states=re.findall(rb'STATE ([0-9A-F]{560})',trace)
        assert len(states)==2 and states[0]==states[1],(name,'active drive changes')
        assert b'Startup default pending; drives unchanged.' in trace
        assert b'Pending startup command: SUBMIT STARTUP' in trace
        if name=='save':assert b'saved and verified.' in trace
        results.append({'case':name,'saved_command':want,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: CONFIG pending startup default, exit/decline preservation, explicit save and unchanged active drives; {work}')


if __name__=='__main__':main()
