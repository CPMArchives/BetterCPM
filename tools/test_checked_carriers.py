#!/usr/bin/env python3
"""Qualify real ordinary-builder carriers against native RSX and streaming gates."""
from pathlib import Path
import argparse
import binascii
import json
import struct

from checked_carriers import selected_contract, binding
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
from test_bios import Z80
from test_checked_command_loader import install_services

ROOT = Path(__file__).resolve().parents[1]


def command_cases(paths, identity):
    directory = ROOT/'build/z80pack/command-loader'
    image = (directory/'stage2.bin').read_bytes();sy = symbols(directory/'stage2.lst')
    results = []
    for path, foreign in paths:
        original = path.read_bytes();cpx = original[:4] == b'BCPX'
        public = original[-19] == 0
        for damaged in (False, True):
            data = bytearray(original)
            if damaged:data[-1] ^= 1
            expected = not damaged and (not foreign or public)
            padded = data + b'\x1a'*((-len(data))%128)
            c = Z80(b'');c.mem[0x500:0x500+len(image)] = image
            cursor = [0]
            def read(port):
                assert port == (203 if cpx else 200)
                dest = c.bc if cpx else c.hl
                if not cpx:assert (c.de,c.b)==(108+cursor[0],1)
                start = cursor[0]*128;cursor[0]+=1
                if start+128 > len(padded):return 1
                c.mem[dest:dest+128] = padded[start:start+128]
                if not cpx:c.hl = dest+128
                return 0
            install_services(c, read, identity)
            c.mem[sy['CRFILE']] = int(cpx);c.mem[sy['CRSLOT']] = 108
            c.setword(sy['CRMAGPTR'],sy['CRCPXMAG' if cpx else 'CRCCPMAG'])
            c.setword(sy['CRBOUND'],L['TPA']);c.sp = 0x1000
            c.run(sy['CRLOAD'],limit=10000000)
            assert (c.a == 0) == expected, (path, foreign, damaged, c.a)
            allocation = int.from_bytes(data[14:16] if cpx else data[10:12],'little')
            assert c.word(sy['CRBOUND']) == L['TPA']-(allocation if expected else 0)
            if expected:
                header = int.from_bytes(data[24:26],'little') if cpx else 1024
                length = int.from_bytes(data[12:14] if cpx else data[8:10],'little')
                linked = int.from_bytes(data[10:12] if cpx else data[6:8],'little')
                count = int.from_bytes(data[22:24] if cpx else data[14:16],'little')
                reloc = 48 if cpx else 16;base = L['TPA']-allocation
                wanted = bytearray(data[header:header+length])
                for i in range(count):
                    off = int.from_bytes(data[reloc+2*i:reloc+2*i+2],'little')
                    value = int.from_bytes(wanted[off:off+2],'little')
                    wanted[off:off+2] = ((value+base-linked)&65535).to_bytes(2,'little')
                if cpx:
                    entry = int.from_bytes(data[16:18],'little')
                    wanted[2:8] = (base+entry).to_bytes(2,'little')+bytes(4)
                assert c.mem[base:base+length] == wanted, path
            results.append({'module':path.name,'foreign_profile':foreign,
                            'crc_damaged':damaged,'accepted':expected})
    return results


def rsx_cases(paths):
    import test_rsxcarrier as fixture
    original_cpu = fixture.Z80
    class NativeCPU(Z80):
        def __init__(self,_):
            super().__init__((ROOT/'build/z80pack/bios.bin').read_bytes())
            data = (ROOT/'build/z80pack/disk.bin').read_bytes()
            self.mem[L['DISK']:L['DISK']+len(data)] = data
        def run(self,address,limit=1000):super().run(address,max(limit,1000000))
    results = [];fixture.Z80 = NativeCPU
    try:
        for path,foreign in paths:
            data = path.read_bytes();off = int.from_bytes(data[30:32],'little')
            public = data[off+15] == 0;expected = not foreign or public
            c,before = fixture.phase_one(data,name=data[32:40])
            if c.a == 0:fixture.phase_two(c,len(data))
            assert (c.a == 0) == expected,(path,foreign,c.a)
            if not expected:assert c.mem[fixture.FACTS:fixture.FACTS+26] == before
            results.append({'module':path.name,'foreign_profile':foreign,'accepted':expected})
    finally:fixture.Z80 = original_cpu
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--foreign',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args();contract = selected_contract();identity = bytes.fromhex(contract['compatibility_id'])
    files = [ROOT/'build/ccp/ccp.rlm',*sorted((ROOT/'build/cpx').glob('*.CPX')),
             *sorted((ROOT/'build/rsx').glob('*.RSX'))]
    identical = []
    old_id = bytes.fromhex(json.loads((a.reference/'assessment-profile.json').read_text())['compatibility_id'])
    for path in files:
        data = bytearray(path.read_bytes());old = (a.reference/path.relative_to(ROOT)).read_bytes()
        if data[:4] == b'BRSX':
            assert data[4] == 3
            off = int.from_bytes(data[30:32],'little');assert data[off:off+5] == b'BMET\x02'
            assert data[off+12:off+15] == bytes((4,18,1))
            if data[off+15]:data[off+16:off+32] = old_id
            else:assert data[off+16:off+32] == bytes(16)
        else:
            assert binascii.crc_hqx(data[:-2],0xFFFF) == int.from_bytes(data[-2:],'little')
            assert data[-22:-19] == b'BP\x02'
            if data[-19]:data[-18:-2] = old_id
            else:assert data[-18:-2] == bytes(16)
            data[-2:] = struct.pack('<H',binascii.crc_hqx(data[:-2],0xFFFF))
        assert data == old, path
        identical.append(str(path.relative_to(ROOT)))
    commands = [p for p in files if p.suffix != '.RSX']
    rsx = [p for p in files if p.suffix == '.RSX']
    paired = lambda paths:[(p,False) for p in paths]+[(a.foreign/p.relative_to(ROOT),True) for p in paths]
    command = command_cases(paired(commands),identity);resident = rsx_cases(paired(rsx))
    denied = []
    for kind,name in [('rsx','M4SCRN'),('rsx','FREHDCLK'),('rsx','UNKNOWN'),('cpx','UNKNOWN')]:
        try:binding(name,contract,kind)
        except ValueError:denied.append([kind,name])
        else:raise AssertionError((kind,name))
    assert not any((ROOT/'build/rsx'/name).exists() for name in ('M4SCRN.RSX','FREHDCLK.RSX'))
    assert selected_contract() == contract
    result = {'profile':contract['contract']['profile'],'compatibility_id':identity.hex(),
              'reference_id_artifacts_identical':identical,'command_cases':command,
              'native_rsx_cases':resident,'policy_denials':denied,'status':'PASS',
              'scope':'component admission and relocated payloads; no media, live OS or stack qualification'}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS {len(identical)} reference artifacts, {len(command)} streaming cases, {len(resident)} native RSX cases, {len(denied)} policy denials')


if __name__ == '__main__':main()
