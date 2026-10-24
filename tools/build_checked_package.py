#!/usr/bin/env python3
"""Compose checked RAM system tracks and SYSTEM.SYS without distribution media."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from build_ccp import assemble
from checked_carriers import selected_contract
from checked_system_package import prepare, make, validate
from build_z80pack_image import DEFAULT_FORMAT, symbols
from fdf_format import select_fdf
from system_layout import LAYOUT as L
from startup_record import build as startup_record

ROOT=Path(__file__).resolve().parents[1]


def compose(assembler):
    contract=selected_contract(assembler)
    if not contract:raise ValueError('select a prepared checked profile')
    out=ROOT/'build/z80pack'
    if json.loads((out/'resident-rsx-contract.json').read_text())!=contract:
        raise ValueError('resident/RSX artifacts belong to another build')
    carriers=json.loads((ROOT/'build/carriers-results.json').read_text())
    if carriers['compatibility_id']!=contract['compatibility_id']:
        raise ValueError('module carriers belong to another build')
    for path,digest in carriers['artifacts'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('changed module carrier: '+path)
    resident_meta=json.loads((out/'resident-rsx-results.json').read_text())
    for path,digest in resident_meta['upstream_hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('changed upstream component: '+path)
    for path,digest in resident_meta['component_hashes'].items():
        if hashlib.sha256((out/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('changed resident component: '+path)
    for path,digest in resident_meta['rsx']['artifacts'].items():
        if hashlib.sha256((ROOT/'build/system'/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('changed RSX component: '+path)
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    boot_source=(ROOT/'src/platform/z80pack/boot.mac').read_text().replace(
        '        INCLUDE bootfmt.inc',f'ZB_TRACKS EQU {fmt.raw_tracks}\nZB_SLOTS EQU {fmt.raw_track_bytes//128}\n')
    boot_source=boot_source.replace('        DB ZB_MAP_BYTES','        DB '+','.join(map(str,fmt.raw_record_map())))
    boot=assemble(assembler,boot_source,out/'boot.bin',out/'boot.lst',0)
    if len(boot)>128:raise ValueError('bootstrap exceeds one record')
    resident=bytearray(L['DIRBUF']-L['SYSTEM'])
    parts=[(L['SYSTEM'],out/'gateway.bin'),(L['BDOS'],ROOT/'build/bdos/bdos.bin'),
           (L['EXTENSIONS'],out/'extensions.bin'),(L['DISK'],out/'disk.bin'),
           (L['BIOS'],out/'bios.bin'),(L['FILE'],ROOT/'build/system/fileloader.bin'),
           (L['TABLES'],out/'tables.bin')]
    for address,path in parts:
        data=path.read_bytes();offset=address-L['SYSTEM']
        if offset<0 or offset+len(data)>len(resident):raise ValueError('resident overflow')
        resident[offset:offset+len(data)]=data
    payload=bytearray(b'\xe5'*(160*128))
    def put(record,data,capacity):
        if not data or len(data)>capacity:raise ValueError(f'raw carrier overflow at record {record}')
        payload[record*128:record*128+capacity]=data.ljust(capacity,b'\0')
    put(0,boot,128);put(1,startup_record(system_base=L['SYSTEM']),256)
    put(8,resident,52*128);put(60,(out/'command-loader/stage1.carrier').read_bytes(),1024)
    put(68,(out/'control.carrier').read_bytes(),1024)
    put(76,(ROOT/'build/system/R3ENTRY.RSX').read_bytes(),1024)
    put(84,(out/'command-loader/stage2.carrier').read_bytes(),2048)
    put(100,(ROOT/'build/system/R3RESOL.RSX').read_bytes(),1024)
    put(108,(ROOT/'build/ccp/ccp.rlm').read_bytes(),13*512)
    (out/'resident.bin').write_bytes(resident)
    prepare(ROOT,out,bytes(payload),symbols(out/'bios.lst'))
    package_contract=json.loads((out/'checked-package.json').read_text())
    package=make(bytes(payload),package_contract);validate(package,package_contract)
    if selected_contract(assembler)!=contract:raise ValueError('source changed while composing package')
    return bytes(payload),package


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--output',type=Path,default=ROOT/'build/z80pack/system-package')
    a=p.parse_args();payload,package=compose(a.assembler)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'system-tracks.bin').write_bytes(payload)
    (a.output/'SYSTEM.SYS').write_bytes(package)
    contract=selected_contract(a.assembler)
    for name in ('disk_utilities','stat','rcp_transients'):
        subprocess.run([sys.executable,str(ROOT/'tools'/f'build_{name}.py'),
                        '--assembler',str(a.assembler)],cwd=ROOT,check=True)
    if selected_contract(a.assembler)!=contract:raise ValueError('source changed while building utilities')
    result={'profile':contract['contract']['profile'],'compatibility_id':contract['compatibility_id'],
            'payload_sha256':hashlib.sha256(payload).hexdigest(),'package_sha256':hashlib.sha256(package).hexdigest(),
            'payload_bytes':len(payload),'package_bytes':len(package),
            'utilities':{name:hashlib.sha256((ROOT/'build/utilities'/name).read_bytes()).hexdigest()
                         for name in ('CONFIG.COM','SYSGEN.COM','STAT.COM','DUP.COM','SYSBUILD.COM','RESPACK.COM','RLMBUILD.COM','CLS.COM')},
            'status':'checked package and utilities only; distribution acceptance pending'}
    (ROOT/'build/package-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
