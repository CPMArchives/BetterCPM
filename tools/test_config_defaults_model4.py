#!/usr/bin/env python3
"""Model 4 pending startup default and unchanged active/disk state."""
import re,tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from test_disk_utilities import ROOT,medium
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    parent=ROOT/'build/test-results/config-default-model4';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));original=medium((('STATE.COM',state_probe(work)),))
    image=work/'a.dmk';image.write_bytes(original)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
    for command,capture in [('STATE\r',True),('CONFIG /DEFAULT\r',False),
                            ('\r',True),('\x03',False),('\x03',False),('STATE\r',True)]:
        args+=key_args(command)+['-id','18000' if command.startswith('CONFIG') else '4000']
        if capture:args+=['-it']
    args+=['-ix'];run(args,cwd=work,check=True,timeout=125)
    states=[]
    for i in range(3):
        raw=(work/f'trs80-text-{i}.bin').read_bytes()[:1920]
        text='\n'.join(bytes(c&127 for c in raw[n:n+80]).decode('ascii').rstrip() for n in range(0,1920,80))
        (work/f'screen-{i}.txt').write_text(text)
        if i==1:
            assert 'SUBMIT STARTUP' in text and 'has not been saved' in text,text
            continue
        values=re.findall(r'STATE([0-9A-F]{560})',''.join(text.split()));assert values,text
        states.append(bytes.fromhex(values[-1]))
    assert len(states)==2 and states[0]==states[1],'default changed active drives'
    assert image.read_bytes()==original,'default saved disk bytes'
    print('PASS: Model 4 pending default visible, active drives preserved, exit without saving; disk unchanged;',work)


if __name__=='__main__':main()
