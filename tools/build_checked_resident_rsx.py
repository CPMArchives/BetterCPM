#!/usr/bin/env python3
"""Build checked resident/RSX components without constructing distribution media."""
from pathlib import Path
import argparse
import binascii
import hashlib
import json
import subprocess
import sys

from build_ccp import assemble
from build_profiles import selected_context
from build_rsx_runtime_overlays import source
from build_z80pack_image import symbols
from checked_build_contract import assembly_constants, load_contract
from checked_rsx_pack import bind_slot, pack_slots
from system_layout import LAYOUT as L

ROOT = Path(__file__).resolve().parents[1]


def build_rsx_components(contract: dict, assembler: Path, output: Path) -> dict:
    """Compile a supplied contract; qualification may supply an old reference ID."""
    if not selected_context(ROOT/'src/system/layout.inc'):
        raise ValueError('checked RSX components require a prepared profile context')
    output.mkdir(parents=True, exist_ok=True)
    identity = bytes.fromhex(contract['compatibility_id'])
    constants = assembly_constants(contract)
    def build(stem, filename, origin_symbol, address):
        return assemble(assembler, constants+source(filename, origin_symbol, address),
                        output/(stem+'.bin'), output/(stem+'.lst'), address)
    specs = [
        ('R3PLAN','r3plan','rsxplan.mac','RPBASE',L['CONFIG']),
        ('R3SLOTS','r3slots','rsxslots.mac','SUBASE',L['CONFIG']),
        ('R3SNAP','r3snapshot','r3snap.mac','RNBASE',L['CONFIG']),
        ('R3CARR','r3carrier','r3carr.mac','RXBASE',L['CONFIG']),
        ('R3META','r3metadata','r3meta.mac','RMBASE',L['CONFIG']),
        ('R3COORD','r3coord','r3coord.mac','RCBASE',L['RSX']),
        ('R3PROF','r3profile','r3prof.mac','PFBASE',L['RSX']),
        ('R3KCTX','r3kctx','r3kctx.mac','KCBASE',L['RSX']),
        ('R3KEEP','r3keep','r3keep.mac','KEBASE',L['RSX']),
        ('R3KPRE','r3kpre','r3kpre.mac','KPBASE',L['RSX']),
        ('R3FINAL','r3final','r3final.mac','RFBASE',L['RSX']),
        ('R3DROP','r3drop','r3drop.mac','RDBASE',L['RSX']),
        ('R3COMIT','r3commit','r3comit.mac','RCBASE',L['RSX']),
    ]
    gateway = bytes((0xC3, L['BDOS']&255, L['BDOS']>>8))
    images = {};sizes = {}
    for name, stem, filename, symbol, address in specs:
        code = build(stem, filename, symbol, address)
        limit = 1024 if address == L['CONFIG'] else 1012
        if not code or len(code) > limit:
            raise ValueError(f'{name}: code exceeds {limit} bytes')
        images[name+'.RSX'] = (code.ljust(1024,b'\0') if address == L['CONFIG']
                               else code.ljust(1021,b'\0')+gateway)
        sizes[name] = len(code)
    move = bytearray(1024);end = 0
    for stem, filename, symbol, offset in [
            ('r3mover','rsxmover.mac','RMBASE',0),
            ('r3sched','rsxsched.mac','RSBASE',0x120),
            ('r3ovload','r3ovload.mac','ROBASE',0x310),
            ('r3persist','r3pst.mac','RTBASE',0x38F)]:
        code = build(stem,filename,symbol,L['CONFIG']+offset)
        if offset < end or offset+len(code)>1024:
            raise ValueError(f'{stem}: move overlay overlap')
        move[offset:offset+len(code)] = code;end = offset+len(code)
    images['R3MOVE.RSX'] = bytes(move)
    resolver = (ROOT/'build/system/rsxresolver.bin').read_bytes()
    if not resolver or len(resolver)>1012:
        raise ValueError('resolver exceeds gateway-safe allocation')
    images['R3RESOL.RSX'] = resolver.ljust(1021,b'\0')+gateway
    package = pack_slots(images, identity)
    constants = assembly_constants(contract, binascii.crc_hqx(package[:512],0xFFFF))
    entry = build('r3entry','r3entry.mac','RVBASE',L['CONFIG'])
    text = (ROOT/'src/system/r3entry.mac').read_text(encoding='ascii')
    helper = text[text.index('RI_ENTRY:'):text.index('RI_END:')]
    reader = assemble(assembler, constants+'        INCLUDE layout.inc\n        INCLUDE profile.inc\n'
                      '        ASEG\n        ORG 0\n'+helper+'        END\n',
                      output/'rsxio.bin',output/'rsxio.lst',0)
    if len(entry)>1000 or len(reader)>512:
        raise ValueError('checked entry/reader overlaps private binding or scratch')
    images['R3ENTRY.RSX'] = bind_slot(entry.ljust(1021,b'\0')+gateway,identity)
    images['R3PACK.RSX'] = package
    (output/'rsxloader.bin').write_bytes(entry)
    for name,data in images.items():(output/name).write_bytes(data)
    return {'sizes':sizes,'entry_bytes':len(entry),'reader_bytes':len(reader),
            'pack_bytes':len(package),'pack_header_crc16':binascii.crc_hqx(package[:512],0xFFFF),
            'artifacts':{name:hashlib.sha256(data).hexdigest() for name,data in images.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    a = p.parse_args();assembler = a.assembler.expanduser().resolve()
    if not selected_context(ROOT/'src/system/layout.inc'):
        p.error('select a prepared checked profile with BETTERCPM_BUILD_CONTEXT')
    if any((ROOT/'build/z80pack'/name).exists() for name in ('command-loader','disks')):
        p.error('use a fresh prepared workspace for checked resident/RSX components')
    contract = load_contract(ROOT,assembler)
    def run(name,*args):
        subprocess.run([sys.executable,str(ROOT/'tools'/name),'--assembler',str(assembler),*args],
                       cwd=ROOT,check=True)
    run('build_rsxresolver.py')
    rsx = build_rsx_components(contract,assembler,ROOT/'build/system')
    run('build_checked_command_loader.py')
    run('build_z80pack_image.py','--resident-only','--ram-only','--system-tracks-only')
    out = ROOT/'build/z80pack';bs = symbols(out/'bios.lst');ds = symbols(out/'disk.lst')
    if not (bs['MP_MON_END']<=L['FILE']-32 and bs['Z_CRC']==L['FILE']-32 and
            bs['Z_CBACK']==L['FILE']-2 and ds['ZP_END']<=L['BIOS']-26 and
            ds['Z_CMP']==L['BIOS']-26 and ds['Z_ID']==L['BIOS']-16):
        raise ValueError('resident services overlap executable code or state')
    identity = bytes.fromhex(contract['compatibility_id'])
    control = (out/'config.bin').read_bytes()
    if len(control)>1000:raise ValueError('control overlay overlaps private binding')
    control = bind_slot(control.ljust(1024,b'\0'),identity)
    (out/'control.carrier').write_bytes(control)
    payloads = {'Z_EREL':(out/'command-loader/stage1.carrier').read_bytes(),
                'Z_ECTL':control,'Z_EENT':(ROOT/'build/system/R3ENTRY.RSX').read_bytes()}
    bios = bytearray((out/'bios.bin').read_bytes());checks = {}
    # Typed operand fixups: only the three labelled LD HL,checksum immediates.
    for label,payload in payloads.items():
        at = bs[label]+1-L['BIOS']
        if len(payload)!=1024 or bios[at-1]!=0x21:
            raise ValueError(f'{label}: checksum operand/carrier changed')
        checksum = binascii.crc_hqx(payload,0xFFFF)
        bios[at:at+2] = checksum.to_bytes(2,'little');checks[label] = checksum
    (out/'bios.bin').write_bytes(bios)
    metadata = {'checksums':checks,'symbols':bs,'bios_bytes':len(bios),
                'bios_capacity':L['FILE']-L['BIOS']}
    (out/'checked-load.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if load_contract(ROOT,assembler)!=contract:
        raise ValueError('checked build source changed while compiling')
    result = {'profile':contract['contract']['profile'],'compatibility_id':contract['compatibility_id'],
              'rsx':rsx,'resident':metadata,'native_identity_address':ds['Z_ID'],
              'native_compare_address':ds['Z_CMP'],'native_crc_address':bs['Z_CRC'],
              'component_hashes':{name:hashlib.sha256((out/name).read_bytes()).hexdigest()
                                  for name in ('bios.bin','disk.bin','extensions.bin','gateway.bin','tables.bin','control.carrier')},
              'status':'resident/RSX components only; no checked distribution image generated'}
    (out/'resident-rsx-results.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'resident-rsx-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
