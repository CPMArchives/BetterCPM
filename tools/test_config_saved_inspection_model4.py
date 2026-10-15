#!/usr/bin/env python3
"""Qualify saved-default inspection through the Model 4 disk backend."""
from pathlib import Path
import tempfile
from test_disk_utilities import ROOT,medium
from test_config_sysgen import probe
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run as run_emulator


def main():
    parent=ROOT/'build/test-results/config-saved-inspection-model4'
    parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    setup=probe(work)
    original=medium((('SETUP.COM',setup),))
    image=work/'a.dmk';image.write_bytes(original)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
    for action in ('SETUP\r','\r','CONFIG /SHOW\r'):
        args+=key_args(action)+['-id','20000' if action.startswith('CONFIG') else '3000']
    args+=['-it','-ix']
    run_emulator(args,cwd=work,check=True,timeout=60)
    raw=(work/'trs80-text-0.bin').read_bytes()[:1920]
    shown='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip()
                    for i in range(0,1920,80))
    (work/'screen.txt').write_text(shown)
    assert 'Saved logical-drive bindings:' in shown and 'B: 1:' in shown,shown
    assert 'A0>' in shown and 'Push ENTER' not in shown and '(Y/N)?' not in shown,shown
    assert (work/'a.dmk').read_bytes()==original,'inspection wrote disk'
    print('PASS: Model 4 saved bindings, immediate return and image unchanged;',work)


if __name__=='__main__':main()
