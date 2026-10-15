#!/usr/bin/env python3
"""Physical CONFIG CLI and protected boot geometry on actual Model 4 backend."""
import re
import tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from test_disk_utilities import ROOT,medium
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    parent=ROOT/'build/test-results/config-physical-cli-model4'
    parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    original=medium((('STATE.COM',state_probe(work)),))
    image=work/'a.dmk';image.write_bytes(original)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
    for command,capture in [('STATE\r',True),
                            ('CONFIG /PHYSICAL=1 /TRACKS=35 /SIDES=1 /SETTLE=20\r',False),
                            ('STATE\r',True),
                            ('CONFIG /PHYSICAL=0 /TRACKS=35\r',False),('STATE\r',True)]:
        args+=key_args(command)+['-id','12000' if command.startswith('CONFIG') else '4000']
        if capture:args+=['-it']
    args+=['-ix'];run(args,cwd=work,check=True,timeout=90)
    states=[];screens=[]
    for i in range(3):
        raw=(work/f'trs80-text-{i}.bin').read_bytes()[:1920]
        text='\n'.join(bytes(c&127 for c in raw[n:n+80]).decode('ascii').rstrip() for n in range(0,1920,80))
        (work/f'screen-{i}.txt').write_text(text);screens.append(text)
        rows=re.findall(r'STATE([0-9A-F]{560})',''.join(text.split()))
        assert rows,text
        states.append(bytes.fromhex(rows[-1]))
    before,after,protected=states;expected=bytearray(before)
    expected[7]=35;expected[8]=1;expected[11]=20
    for i in range(1,4):
        at=24+i*64
        if before[at]==1 and (before[at+16]>35 or before[at+19]&0x60):expected[at]=255
    assert after==bytes(expected),(before.hex(),after.hex())
    assert protected==after,'boot-geometry request changed state'
    assert 'Nothing changed.' in screens[-1],screens[-1]
    assert image.read_bytes()==original,'live CLI changed disk'
    print('PASS: Model 4 physical CLI state, incompatible detach, boot protection and image unchanged;',work)


if __name__=='__main__':main()
