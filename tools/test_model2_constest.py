#!/usr/bin/env python3
"""Run the pinned CONSTEST output cards through the assembled Model II resident system."""
import argparse
import ctypes
import hashlib
import json
import struct
import tempfile
from pathlib import Path

from build_z80pack_image import symbols
from run_model2_conformance import SUITE, SUITE_REV, suite_blob
from test_model2_screen import Core

OUTPUTS = {52:b'[A]', 53:b'[$]', 54:b'[F9ADDR]', 55:b'[LEFT]', 56:b'[X]', 57:b'[]'}
CONFIRM = b'Do OBSERVED and EXPECTED match? (Y/N; no Enter) '


def console_fixture(out, suite, z80pack, folder):
    program = suite_blob(suite,'build/CONSTEST.COM')
    hashes = dict(line.split()[::-1] for line in suite_blob(suite,'build/SHA256SUMS.txt').decode().splitlines())
    digest = hashlib.sha256(program).hexdigest()
    assert hashes['CONSTEST.COM'] == digest
    resident = (out/'resident.bin').read_bytes()
    base = json.loads((out/'checked-package.json').read_text())['system_base']
    bios = symbols(out/'bios.lst')
    gateway = symbols(out/'gateway.lst')
    # The unloaded movable vector and its target are supplied by the image.
    limit = gateway['ECB_TPATOP'] - base
    top = int.from_bytes(resident[limit:limit+2],'little')
    bdos = json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_BDOS']
    assert base-256 < top < base < bdos < bios['BIOS']
    core = Core(folder,z80pack)
    hook_type = ctypes.CFUNCTYPE(None, ctypes.c_int)
    core.lib.set_hooks.argtypes = [ctypes.c_ushort,ctypes.c_ushort,hook_type]
    pending = ctypes.c_ubyte.in_dll(core.lib,'key_pending')
    key = ctypes.c_ubyte.in_dll(core.lib,'key_value')
    def jump(address):
        return b'\xc3'+struct.pack('<H',address)

    def run_card(case, on_output, on_poll=None):
        # Output is observed at the renderer entry. Status polls supply ready
        # keys through the Model II hardware ports. Both guest routines execute.
        error = []
        @hook_type
        def observe(which):
            try:
                if which == 0:
                    on_output(core.r['C'].value)
                elif on_poll and not pending.value:
                    value = on_poll()
                    if value is not None:
                        key.value = value
                        pending.value = 1
            except Exception as exc:
                if not error:
                    error.append(exc)
        core.lib.set_hooks(bios['PL_CONOT'],bios['PL_CONST'],observe)
        core.put(0,bytes(65536))
        core.put(base,resident)
        core.put(5,jump(top))
        core.put(top,jump(bdos))
        core.put(0,jump(bios['BIOS']+3))
        core.put(bios['BIOS']+3,jump(0xffff))  # stop at WBOOT after each independent COM
        core.run(bios['BIOS']+72)               # initialize the ordinary monitor
        core.mem[3] = 0x95
        core.put(0x100,program)
        tail = f' /{case:04d}'.encode()
        core.put(0x80,bytes([len(tail)])+tail+b'\r')
        pending.value = 0
        core.sp.value = 0x9f00
        steps = core.lib.test_run(0x100,3000000)
        if error:
            raise error[0]
        assert steps >= 0, (case, steps)
    return run_card, digest, hashlib.sha256(resident).hexdigest()


def check(out, suite, z80pack, folder):
    run_card, digest, resident_digest = console_fixture(out,suite,z80pack,folder)
    results = []
    for case in range(52,59):
        value = OUTPUTS.get(case)
        expected = b'OBSERVED: '+value+b'\r\nEXPECTED: '+value if value else b'OBSERVED:\r\nA\r\nB\r\nEXPECTED:\r\nA\r\nB'
        if case==53:
            expected += b' (one dollar-sign character)'
        output = bytearray()
        confirmed = []
        keys = []
        def observe(byte):
            output.append(byte)
            if output.endswith(expected+b'\r\n'+CONFIRM):
                keys.append(ord('Y'))
                confirmed.append(True)
        run_card(case, observe, lambda: keys.pop() if keys else None)
        assert confirmed==[True] and f'{case:04d}  P  R'.encode() in output, (case,bytes(output[-420:]))
        results.append({'card':f'{case:04d}','transcript':output.decode('ascii'),'status':'PASS'})
    return {'status':'PASS','suite_revision':SUITE_REV,'constest_sha256':digest,
            'resident_sha256':resident_digest,'cards':results,
            'scope':'Output cards 0052-0058. The actual Model II BDOS, BIOS, monitor and CRT routine execute in the Z80 CPU harness. Confirmation is offered through synthetic Model II keyboard ports only after the independent literal output matches. Guest filesystems, timing and physical peripherals are outside this check.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts',type=Path)
    parser.add_argument('--suite',type=Path,default=SUITE)
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        print(json.dumps(check(args.artifacts,args.suite,args.z80pack,Path(temp)),indent=2))
