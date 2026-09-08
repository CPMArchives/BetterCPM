#!/usr/bin/env python3
"""Exercise final BIOS failures in every assembled BDOS disk-I/O path."""
from pathlib import Path
import test_unified_bdos as foundation
from test_bios import Z80, BASE as BIOS, require
from system_layout import LAYOUT

S = foundation.symbols()


def wrapper_checks():
    """Check normal completion, ignore, and warm-boot abort at each wrapper."""
    for name in ('UB_IOREAD', 'UB_IOWR'):
        for status in (0, 1, 2, 255):
            for key in (13, ord('I'), 3):
                cpu = Z80(b'')
                data = foundation.IMAGE.read_bytes()
                cpu.mem[LAYOUT['BDOS']:LAYOUT['BDOS'] + len(data)] = data
                # Both BIOS vectors report their final status without changing
                # any caller registers.  The BDOS must protect those registers
                # while it talks with the operator.
                for offset in (39, 42):
                    cpu.mem[BIOS + offset:BIOS + offset + 3] = bytes((0x3e, status, 0xc9))
                cpu.mem[BIOS + 12] = 0xc9
                cpu.mem[BIOS + 9:BIOS + 12] = bytes((0x3e, key, 0xc9))
                cpu.mem[BIOS + 3:BIOS + 6] = bytes((0xc3, 0xff, 0xff))
                cpu.sp = 0x9000
                cpu.bc = 0x1234
                cpu.de = 0x5678
                cpu.hl = 0x9abc
                cpu.ix = 0xabcd
                cpu.mem[S['UB_DIRTY']] = 1
                cpu.run(S[name], limit=5000)
                abort = bool(status and key == 3)
                if abort:
                    require(cpu.mem[S['UB_DIRTY']] == 0,
                            'abort retained a dirty directory buffer')
                    require(cpu.sp < 0x9000,
                            'abort returned to the interrupted caller')
                else:
                    require(cpu.a == 0 and cpu.z,
                            'ignore/success did not return success')
                    require((cpu.bc, cpu.de, cpu.hl, cpu.ix) ==
                            (0x1234, 0x5678, 0x9abc, 0xabcd),
                            'operator recovery damaged caller registers')
                    require(cpu.sp == 0x9000, 'operator recovery unbalanced the stack')
    print('24 success/ignore/abort combinations passed')


def all_paths():
    """Run the filesystem foundation with failures after every physical I/O."""
    source = Path(foundation.__file__).read_text()
    inject = '''
    def put(address, data):
        cpu.mem[address:address+len(data)] = bytes(data)
    for name, vector, hook in (('UB_IOREAD',39,0x9000), ('UB_IOWR',42,0x9020)):
        cpu.setword(state[name]+1,hook)
        put(hook,[0xcd,(BIOS_BASE+vector)&255,(BIOS_BASE+vector)>>8,
                  0xe5,0x21,0x90,0x90,0x34,0xe1,0x3e,1,0xc9])
    # ENTER ignores the reported error.  Keep this input separate from the
    # scripted console tests in the foundation.
    cpu.setword(state['UB_SECKEY']+1,0x9040)
    put(0x9040,[0x3e,13,0xc9])
    start=state['UB_SECOUT']
    console_call=next(a for a in range(start,start+24) if cpu.mem[a]==0xcd)
    cpu.setword(console_call+1,0x9043)
    put(0x9043,[0xc9])
'''
    source = source.replace('    state = symbols()\n', '    state = symbols()\n' + inject)
    source = source.replace(
        '    print(f"BDOS private stack high-water:',
        '    require(cpu.mem[0x9090] != 0, "no faults injected")\n'
        '    print(f"BDOS private stack high-water:')
    env = dict(foundation.__dict__, __name__='recovery_foundation')
    exec(compile(source, foundation.__file__, 'exec'), env)
    env['main']()


if __name__ == '__main__':
    wrapper_checks()
    all_paths()
