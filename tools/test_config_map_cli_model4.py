#!/usr/bin/env python3
"""Model 4 sector-slot CLI and rejected maps using public state snapshots."""
import re,tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from test_disk_utilities import ROOT,medium
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    parent=ROOT/'build/test-results/config-map-cli-model4';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));original=medium((('STATE.COM',state_probe(work)),))
    image=work/'a.dmk';image.write_bytes(original)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
    for command,capture in [('STATE\r',True),
        ('CONFIG /EDIT=B /SLOT=1 /ID=200\r',False),
        ('STATE\r',True),('CONFIG /EDIT=B /SLOT=1 /ID=2\r',False),('STATE\r',True),('CONFIG /EDIT=B /SLOT=1 /CODE=0\r',False),('STATE\r',True)]:
        args+=key_args(command)+['-id','18000' if command.startswith('CONFIG') else '4000']
        if capture:args+=['-it']
    args+=['-ix'];run(args,cwd=work,check=True,timeout=125)
    states=[]
    for i in range(4):
        raw=(work/f'trs80-text-{i}.bin').read_bytes()[:1920]
        text='\n'.join(bytes(c&127 for c in raw[n:n+80]).decode('ascii').rstrip() for n in range(0,1920,80))
        (work/f'screen-{i}.txt').write_text(text)
        values=re.findall(r'STATE([0-9A-F]{560})',''.join(text.split()));assert values,text
        states.append(bytes.fromhex(values[-1]))
    old,changed,duplicate,mixed=states;expected=bytearray(old);at=24+64
    expected[at+20]=200
    assert changed==bytes(expected),(changed.hex(),bytes(expected).hex())
    assert duplicate==changed,'duplicate ID changed active binding'
    assert mixed==changed,'inconsistent size map changed active binding'
    assert image.read_bytes()==original,'slot CLI saved disk bytes'
    print('PASS: Model 4 sector ID, duplicate/inconsistent-map rejection, unrelated state preserved; disk unchanged;',work)


if __name__=='__main__':main()
