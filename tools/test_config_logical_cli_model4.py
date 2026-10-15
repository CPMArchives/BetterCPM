#!/usr/bin/env python3
"""Model 4 logical binding/unbind via actual catalogue and public state snapshots."""
import json,re,struct,tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from test_disk_utilities import ROOT,medium
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    parent=ROOT/'build/test-results/config-logical-cli-model4';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));original=medium((('STATE.COM',state_probe(work)),))
    image=work/'a.dmk';image.write_bytes(original)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
    for command,capture in [('STATE\r',True),
        ('CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="MM 80T DS DATA"\r',False),
        ('STATE\r',True),('CONFIG /LOGICAL=C /UNBIND\r',False),('STATE\r',True)]:
        args+=key_args(command)+['-id','18000' if command.startswith('CONFIG') else '4000']
        if capture:args+=['-it']
    args+=['-ix'];run(args,cwd=work,check=True,timeout=100)
    states=[]
    for i in range(3):
        raw=(work/f'trs80-text-{i}.bin').read_bytes()[:1920]
        text='\n'.join(bytes(c&127 for c in raw[n:n+80]).decode('ascii').rstrip() for n in range(0,1920,80))
        (work/f'screen-{i}.txt').write_text(text)
        values=re.findall(r'STATE([0-9A-F]{560})',''.join(text.split()));assert values,text
        states.append(bytes.fromhex(values[-1]))
    definition=next(d for d in json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats']
                    if d['name']=='Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    v=definition['parameters']
    binding=b'\1'+struct.pack('<HBBBHHBBHH',*v[:10])+bytes((v[12],v[10],v[11],v[13]))+bytes(definition['sector_ids']).ljust(32,b'\0')+bytes(12)
    old,bound,unbound=states;expected=bytearray(old);at=24+2*64;expected[at:at+64]=binding
    assert bound==bytes(expected),(bound.hex(),bytes(expected).hex())
    expected[at]=255;assert unbound==bytes(expected),'unbind altered unrelated fields'
    assert image.read_bytes()==original,'logical CLI saved disk bytes'
    print('PASS: Model 4 named binding, unbind and unrelated state preserved; disk unchanged;',work)


if __name__=='__main__':main()
