"""Canonical identity of the BIOS executable, bootstrap and configuration pieces."""
import argparse
import hashlib
import json
from pathlib import Path

PIECES={
    'z80pack':{'bios':'build/z80pack/bios.bin','disk':'build/z80pack/disk.bin',
               'config':'build/z80pack/config.bin','tables':'build/z80pack/tables.bin',
               'boot':'build/z80pack/boot.bin'},
    'trs80gp':{'bios':'build/bios/bios.bin','disk':'build/system/disk.bin',
               'config':'build/system/config.bin','tables':'build/system/tables.bin',
               'boot':'build/trs80/boot.bin','stage1':'build/trs80/stage1.bin'}}


def bundle(root,target):
    root=Path(root);pieces=dict(PIECES[target]);limit=32
    if target=='z80pack':
        layout=root/'build/z80pack/checksum-layout.json'
        if layout.is_file():limit=json.loads(layout.read_text())['cks_limit']
        if limit not in (32,48):raise ValueError('unsupported checksum-vector layout')
        if limit==48:pieces['checksum-extra']='build/z80pack/checksum-extra.bin'
    files={}
    for name,path in pieces.items():
        data=(root/path).read_bytes()
        if not data:raise ValueError('empty BIOS implementation piece: '+path)
        files[name]={'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    value={'schema':1,'component':'subsystem:BIOS','target':target,'checksum_limit':limit,'pieces':files}
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--target',choices=tuple(PIECES),required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_bytes(bundle(a.root,a.target))
