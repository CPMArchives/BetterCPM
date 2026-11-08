"""Execute private compact helpers with independent registry/BDOS fixtures."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from zsystem_model import ROOT, description, symbols
from test_usq import SHIM


def qualify(out):
    cpu = out/'cpu'
    cpu.mkdir(exist_ok=True)
    core = Path.home()/'projects/git/z80pack/z80core'
    (cpu/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h', 'simport.h'):
        shutil.copy2(core.parent/'z80sim/srcsim'/name, cpu/name)
    shim = SHIM.replace('static WORD readpc, writepc;', 'static WORD readpc, writepc;\nunsigned low_sp;')
    shim = shim.replace('cpu_error=0; tmax=100000000;', 'cpu_error=0; tmax=100000000; low_sp=SP;')
    shim = shim.replace('if(PC==65535) return i;', 'if(SP<low_sp) low_sp=SP;\n  if(PC==65535) return i;')
    (cpu/'shim.c').write_text(shim)
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', f'-I{cpu}', f'-I{core}', str(cpu/'shim.c'),
                    str(core/'simglb.c'), *map(str, sorted(core.glob('simz80*.c'))),
                    '-o', str(cpu/'core.so')], check=True)
    lib = C.CDLL(str(cpu/'core.so'))
    memory = (C.c_ubyte*65536).in_dll(lib, 'memory')
    registers = {n: C.c_ubyte.in_dll(lib, n) for n in 'AFBCDEHL'}
    sp = C.c_ushort.in_dll(lib, 'SP')
    ix = C.c_ushort.in_dll(lib, 'IX')
    iy = C.c_ushort.in_dll(lib, 'IY')
    low_sp = C.c_uint.in_dll(lib, 'low_sp')
    captured = bytearray()
    errors = []
    mode = 'normal'
    def callback(kind):
        operation = registers['C'].value
        if kind or operation not in (2, 182):
            errors.append(('unexpected BDOS call', kind, operation))
            return
        if operation == 2:
            captured.append(registers['E'].value)
            # The helper must tolerate ordinary scratch-register clobbering.
            for n in 'ABCDEFHL': registers[n].value = 0x55
            return
        request = registers['D'].value*256+registers['E'].value
        service = bytes(memory[request+4:request+8])
        if service not in (b'MCON', b'XTAB'):
            errors.append(('unexpected service', service))
        address = 0x8000 if service == b'XTAB' else 0x8100
        status = 1 if mode == 'absent' and service == b'XTAB' else 0
        memory[request+18] = 2 if mode == 'mismatch' and service == b'XTAB' else 1
        memory[request+19] = status
        registers['A'].value = status
        registers['H'].value, registers['L'].value = address >> 8, address & 255
    hook = C.CFUNCTYPE(None, C.c_int)(callback)
    lib.set_hooks(5, 0xfff0, hook)
    labels = symbols(out/'client.lst')
    checks = []
    def invoke(name, a=0, row=0, col=0, status=0, output=b''):
        captured.clear()
        registers['A'].value = a
        registers['B'].value = row
        registers['C'].value = col
        sp.value = 0x7000
        ix.value, iy.value = 0x1234, 0x5678
        steps = lib.test_run(labels[name], 100000)
        actual = (registers['A'].value, bytes(captured))
        assert steps >= 0 and not errors and actual == (status, output), (name, actual, status, output, errors)
        assert sp.value == 0x7000 and ix.value == 0x1234 and iy.value == 0x5678
        checks.append(dict(routine=name, argument=a, row=row, column=col, status=status,
                           output_hex=captured.hex(), stack_bytes_including_entry_return=0x7000-low_sp.value))
    def setup(name, record=None):
        memory[:] = bytes(65536)
        code = (out/'client.bin').read_bytes()
        memory[0x4000:0x4000+len(code)] = code
        memory[3] = 1
        memory[5] = 0xc9
        # Relocate the original generated query alone to the fixture entry.
        table = description(name) if record is None else record
        memory[0x8000:0x800a] = bytes.fromhex('b72004210a80c93effc9')
        memory[0x800a:0x800a+len(table)] = table
    for name in ('ANSI', 'ADM3A', 'VT52'):
        setup(name)
        invoke('TC_OPEN')
        assert bytes(memory[labels['TC_TABLE']:labels['TC_TABLE']+len(description(name))]) == description(name)
        if name == 'ANSI':
            for row, col in ((0, 0), (23, 79), (99, 100), (254, 254)):
                invoke('TC_EMIT', 1, row, col, output=f'\x1b[{row+1};{col+1}H'.encode())
            invoke('TC_EMIT', 1, 255, 0, status=3)
            invoke('TC_EMIT', 3, output=b'\x1b[1m')
            invoke('TC_EMIT', 4, output=b'\x1b[22m')
        else:
            prefix = b'\x1b=' if name == 'ADM3A' else b'\x1bY'
            invoke('TC_EMIT', 1, 23, 79, output=prefix+bytes((55, 111)))
            invoke('TC_EMIT', 1, 24, 0, status=3)
            invoke('TC_EMIT', 1, 0, 80, status=3)
            invoke('TC_EMIT', 3, output=b'\x0f' if name == 'ADM3A' else b'')
            invoke('TC_EMIT', 4, output=b'\x0e' if name == 'ADM3A' else b'')
        invoke('TC_EMIT', 7, status=3)
        for route in (0, 2, 3):
            memory[3] = route
            invoke('TC_EMIT', 3, status=1)
            invoke('TC_OPEN', status=1)
    for field, value in ((0, 0), (2, 1), (3, 15), (3, 129), (8, 15), (8, 128)):
        record = bytearray(description('ANSI'))
        record[field] = value
        setup('ANSI', record)
        invoke('TC_OPEN', status=2)
        invoke('TC_EMIT', 3, status=1)
    record = bytearray(description('ANSI'))
    record[-1] = 65
    setup('ANSI', record)
    invoke('TC_OPEN', status=2)
    for mode in ('absent', 'mismatch'):
        setup('ANSI')
        invoke('TC_OPEN', status=1)
        invoke('TC_EMIT', 3, status=1)
    report = dict(status='PASS private compact helper CPU fixtures', checks=checks,
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  maximum_observed_stack_bytes=max(c['stack_bytes_including_entry_return'] for c in checks),
                  scope='library and mocked BDOS leaf; platform BDOS/BIOS stack excluded',
                  helper_image_sha256=hashlib.sha256((out/'client.bin').read_bytes()).hexdigest())
    built = json.loads((out/'build.json').read_text())
    extra = max(p['extra_allocated_bytes'] for p in built['profiles'].values())
    report['maximum_comparable_static_bytes'] = extra+built['helper']['total_bytes']
    report['diagnostic_plus_resident_and_observed_stack_bytes'] = (
        extra+built['probe_com_bytes']+report['maximum_observed_stack_bytes'])
    assert report['diagnostic_plus_resident_and_observed_stack_bytes'] <= 1280
    (out/'cpu.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', len(checks), 'compact helper cases; observed stack', report['maximum_observed_stack_bytes'])
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    qualify(args.output.resolve())
