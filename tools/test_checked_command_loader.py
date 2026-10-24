#!/usr/bin/env python3
"""Execute emitted command stages with controlled record/CRC/identity services.

Fixtures construct carriers independently; services are intercepted. This is
component qualification, not a live OS or native-stack qualification.
"""
from pathlib import Path
import argparse
import binascii
import json
import struct
import types

from build_checked_command_loader import build_stages
from build_z80pack_image import symbols
from checked_build_contract import load_contract
from system_layout import LAYOUT as L
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def bind(data, identity, public=False):
    data = bytearray(data)
    if data[:4] == b'BCPX':
        data[4] = 2
    else:
        data[:5] = b'BCM2\2'
    data += b'BP' + bytes((2, 0 if public else 1)) + (bytes(16) if public else identity)
    data += struct.pack('<H', binascii.crc_hqx(data, 0xFFFF))
    return bytes(data)


def repair_crc(data):
    data[-2:] = struct.pack('<H', binascii.crc_hqx(data[:-2], 0xFFFF))
    return bytes(data)


def install_services(cpu, read_record, identity):
    # OR A supplies the resident routines' documented zero/nonzero result.
    for address, port in [(L['DISK']+15, 200), (L['BIOS']-26, 201),
                          (L['FILE']-32, 202), (L['EXTENSIONS']+9, 203)]:
        cpu.mem[address:address+4] = bytes((0xDB, port, 0xB7, 0xC9))
    cpu.mem[L['BIOS']-16:L['BIOS']] = identity
    def io(port):
        port &= 255
        if port in (200, 203):
            return read_record(port)
        if port == 201:
            return int(cpu.mem[cpu.hl:cpu.hl+16] != cpu.mem[cpu.de:cpu.de+16])
        if port == 202:
            cpu.hl = binascii.crc_hqx(cpu.mem[cpu.de:cpu.de+cpu.bc], 0xFFFF)
            return 0
        raise AssertionError(port)
    cpu.port_read = io


def first_stage_cases(directory, identity):
    first = (directory/'stage1.bin').read_bytes()
    second = (directory/'stage2.carrier').read_bytes()
    listing = symbols(directory/'stage1.lst')
    cases = [('good', None, True), ('read-error', None, False),
             ('payload-corruption', 100, False), ('tail-corruption', 2047, False),
             ('wrong-expected-crc', None, False)]
    cases += [('foreign-id-'+str(i), 2024+i, False) for i in range(16)]
    results = []
    for name, mutation, accepted in cases:
        cpu = Z80(b'');cpu.mem[0x100:0x100+len(first)] = first
        carrier = bytearray(second)
        if mutation is not None:
            carrier[mutation] ^= 1
        if name == 'wrong-expected-crc':
            cpu.mem[listing['P9_EXPECT']+1] ^= 1
        reads = []
        def read(port):
            assert port == 200 and (cpu.hl, cpu.de, cpu.b) == (0x500, 84, 16)
            reads.append([cpu.hl, cpu.de, cpu.b])
            if name == 'read-error':
                return 1
            cpu.mem[0x500:0xD00] = carrier
            return 0
        install_services(cpu, read, identity)
        output = [];cpu.port_write = lambda port, value:output.append(value)
        # Stop at the genuine second-stage entry without executing that stage.
        run = types.FunctionType(Z80.run.__code__, dict(Z80.run.__globals__, SENTINEL=0x500))
        try:
            run(cpu, 0x100, 10000)
            reached = cpu.pc == 0x500
        except AssertionError:
            assert cpu.mem[cpu.pc-1] == 0x76 and output == [ord('!')], name
            reached = False
        assert reached == accepted, name
        assert len(reads) == 1, name
        results.append({'case':name, 'entered_stage2':reached, 'expected_accept':accepted})
    return results


def module_fixture(cpx, identity, public):
    payload = bytearray(32);payload[8] = 0xC9
    payload[10:12] = (0x8010).to_bytes(2, 'little')
    if cpx:
        # Independent BCPX1 fixture: do not call the selected-profile builder.
        header = bytearray(512)
        struct.pack_into('<4sBBBBHHHHHHHHHHHH8sBBBBH', header, 0,
                         b'BCPX', 1, 1, 1, 0, 0, 0x8000, 32, 256,
                         8, 0xFFFF, 0xFFFF, 1, 512, 512, 48, 544,
                         b'PROBE   ', 1, 0, 1, 0, sum(payload)&0xFFFF)
        header[48:50] = (10).to_bytes(2, 'little')
        old = bytes(header) + payload + b'PROBE   '
    else:
        header = bytearray(1024)
        header[:16] = struct.pack('<4sBBHHHHH', b'BCM1', 1, 2, 0x8000, 32, 256, 0, 1)
        header[16:18] = (10).to_bytes(2, 'little')
        old = bytes(header) + payload
    return bind(old, identity, public), payload


def second_stage_cases(directory, identity):
    image = (directory/'stage2.bin').read_bytes();sy = symbols(directory/'stage2.lst')
    results = []
    for cpx, public in [(True, False), (True, True), (False, False)]:
        original, payload = module_fixture(cpx, identity, public)
        header = 512 if cpx else 1024
        scenarios = ['good', 'payload-corruption', 'late-crc', 'old-format', 'wrong-class',
                     'wrong-id', 'bad-relocation', 'oversized-header', 'truncated',
                     'read-error', 'padding-ignored', 'exact-floor', 'below-floor']
        if cpx:
            scenarios.append('bad-lifecycle')
        else:
            scenarios.append('public-ccp')
        for name in scenarios:
            data = bytearray(original)
            if name == 'payload-corruption':data[header+16] ^= 1
            elif name == 'late-crc':data[-1] ^= 1
            elif name == 'old-format':data[4] = 1
            elif name == 'wrong-class':data[-19] = 2;data = bytearray(repair_crc(data))
            elif name == 'wrong-id':data[-18] ^= 1;data = bytearray(repair_crc(data))
            elif name == 'bad-relocation':
                at = 48 if cpx else 16;data[at:at+2] = (31).to_bytes(2, 'little');data = bytearray(repair_crc(data))
            elif name == 'oversized-header':
                if cpx:data[24:28] = (2048).to_bytes(2, 'little')*2
                else:data[14:16] = (0xFFFF).to_bytes(2, 'little')
                data = bytearray(repair_crc(data))
            elif name == 'bad-lifecycle':data[18:20] = (32).to_bytes(2, 'little');data = bytearray(repair_crc(data))
            elif name == 'public-ccp':data[-19:-2] = bytes(17);data = bytearray(repair_crc(data))
            elif name == 'truncated':data = data[:header]
            expected = name in ('good', 'padding-ignored', 'exact-floor')
            padded = data + bytes([0xA5 if name == 'padding-ignored' else 0x1A])*((-len(data))%128)
            cpu = Z80(b'');cpu.mem[0x500:0x500+len(image)] = image
            cursor = [0];requests = []
            def read(port):
                assert port == (203 if cpx else 200)
                destination = cpu.bc if cpx else cpu.hl
                if not cpx:assert (cpu.de, cpu.b) == (108+cursor[0], 1)
                start = cursor[0]*128;cursor[0] += 1;requests.append(destination)
                if start+128 > len(padded) or (name == 'read-error' and start >= header):
                    return 1
                cpu.mem[destination:destination+128] = padded[start:start+128]
                if not cpx:cpu.hl = destination+128
                return 0
            install_services(cpu, read, identity)
            cpu.mem[sy['CRFILE']] = int(cpx)
            cpu.mem[sy['CRSLOT']] = 108
            cpu.setword(sy['CRMAGPTR'], sy['CRCPXMAG' if cpx else 'CRCCPMAG'])
            bound = 0x1780 if name == 'exact-floor' else 0x177F if name == 'below-floor' else L['TPA']
            cpu.setword(sy['CRBOUND'], bound);cpu.sp = 0x1000
            cpu.mem[bound:bound+16] = bytes([0xA5])*16
            cpu.run(sy['CRLOAD'], limit=1000000)
            accepted = cpu.a == 0
            assert accepted == expected, (cpx, public, name, cpu.a)
            assert cpu.word(sy['CRBOUND']) == (bound-256 if expected else bound)
            assert cpu.mem[bound:bound+16] == bytes([0xA5])*16
            if expected:
                base = bound-256;wanted = bytearray(payload)
                wanted[10:12] = (base+16).to_bytes(2, 'little')
                if cpx:wanted[2:8] = (base+8).to_bytes(2, 'little')+bytes(4)
                assert cpu.mem[base:base+32] == wanted, (cpx, public, name)
            results.append({'module':'public-CPX' if public else 'private-CPX' if cpx else 'private-CCP',
                            'case':name, 'accepted':accepted, 'expected_accept':expected,
                            'record_reads':len(requests), 'allocation_boundary_preserved_on_failure':True})
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loader', type=Path, default=ROOT/'build/z80pack/command-loader')
    p.add_argument('--reference', type=Path, required=True, help='qualified prototype profile for byte comparison')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args();assembler = Path.home()/'bin/z80asm'
    contract = load_contract(ROOT, assembler);identity = bytes.fromhex(contract['compatibility_id'])
    assert json.loads((a.loader/'contract.json').read_text()) == contract
    reference_id = bytes.fromhex(json.loads((a.reference/'assessment-profile.json').read_text())['compatibility_id'])
    refout = a.output.parent/'reference-id-stages'
    build_stages(refout, reference_id, assembler)
    identical = []
    for name in ('stage1.bin', 'stage2.bin', 'stage1.carrier', 'stage2.carrier'):
        assert (refout/name).read_bytes() == (a.reference/'build/z80pack/command-loader'/name).read_bytes(), name
        identical.append(name)
    first = first_stage_cases(a.loader, identity);second = second_stage_cases(a.loader, identity)
    assert load_contract(ROOT, assembler) == contract
    result = {'profile':contract['contract']['profile'], 'compatibility_id':identity.hex(),
              'reference_id_artifacts_identical':identical, 'stage1_cases':first, 'stage2_cases':second,
              'status':'PASS', 'scope':'emitted stages with controlled resident services; no live OS or native stack qualification'}
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(f'PASS {len(first)} first-stage and {len(second)} streaming admission cases; four reference artifacts identical')


if __name__ == '__main__':main()
