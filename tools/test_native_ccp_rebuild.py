#!/usr/bin/env python3
"""Execute production RLMBUILD with controlled CP/M record services."""
from pathlib import Path
from test_bios import Z80
from native_ccp import metadata
import struct
import tempfile
from build_ccp import assemble
from system_layout import expand_layout

ROOT = Path(__file__).resolve().parents[1]


def execute(inputs, image=None, ceiling=0xE100, fail=None):
    image = image or (ROOT/'build/utilities/RLMBUILD.COM').read_bytes()
    c = Z80(b'')
    c.mem[:] = b'\xa5'*65536
    c.mem[0:3] = b'\xc3\xff\xff'
    c.mem[5:8] = b'\xc3\x00\xf0'
    c.mem[0xf000:0xf003] = b'\xd3\x00\xc9'
    c.setword(6, ceiling)
    c.mem[ceiling:ceiling+3] = b'\xc3\x00\xf0'
    c.mem[0x100:0x100+len(image)] = image
    c.mem[0x80] = 0
    c.sp = 0x3000
    dma = 0x80
    cursors, out, messages, calls = {}, bytearray(), [], []
    protected = bytes(c.mem[ceiling:0xf000])
    def bdos(port, value):
        nonlocal dma
        fn, ptr = c.c, c.de
        calls.append(fn)
        c.a = 0
        if fn == 9:
            end = c.mem.index(36, ptr)
            messages.append(bytes(c.mem[ptr:end]).decode('ascii'))
        elif fn == 2:
            messages.append(chr(c.e))
        elif fn == 26:
            dma = ptr
        else:
            name = bytes(c.mem[ptr+1:ptr+12])
            if fail == fn:
                c.a = 255 if fn != 21 else 1
            elif fn == 15:
                if name not in inputs: c.a = 255
                cursors[name] = 0
            elif fn == 20:
                pos = cursors[name]
                block = inputs[name][pos:pos+128]
                if not block: c.a = 1
                else:
                    c.mem[dma:dma+128] = block.ljust(128,b'\x1a')
                    cursors[name] += 128
            elif fn == 21:
                out.extend(c.mem[dma:dma+128])
            elif fn not in (16,19,22):
                raise AssertionError(('unexpected BDOS',fn))
    c.port_write = bdos
    c.run(0x100, limit=4000000)
    assert bytes(c.mem[ceiling:0xf000]) == protected, 'protected memory changed'
    return bytes(out), ''.join(messages), calls


def main():
    root = ROOT/'build/ccp'
    module = (root/'ccp.rlm').read_bytes()
    metadata(module)
    relocations = int.from_bytes(module[14:16], 'little')
    inputs = {name: (root/file).read_bytes() for name,file in (
        (b'CCPBASE BIN','packed.bin'),(b'CCPALT  BIN','packed-alt.bin'),
        (b'CCPCHK  BIN','packed-check.bin'))}
    output, text, calls = execute(inputs)
    assert output[:len(module)] == module and not any(output[len(module):]), text
    assert len(output) == (len(module)+127)//128*128
    assert 'created and verified' in text
    count = 1
    for mode in ('missing','short','extra','wrong-constant','wrong-fixup'):
        changed = dict(inputs)
        data = bytearray(changed[b'CCPALT  BIN'])
        if mode == 'missing': del changed[b'CCPALT  BIN']
        elif mode == 'short': changed[b'CCPALT  BIN'] = data[:-128]
        elif mode == 'extra': changed[b'CCPALT  BIN'] = data.ljust((len(data)+127)//128*128,b'\x1a')+bytes(128)
        else:
            # First opcode is JP; operand at offset one is a relocation.
            data[0 if mode == 'wrong-constant' else 1] ^= 1
            changed[b'CCPALT  BIN'] = data
        output, text, calls = execute(changed)
        assert 'failed' in text and 22 not in calls, (mode,text)
        count += 1
    for fn in (15,20,22,21,16):
        output, text, calls = execute(inputs, fail=fn)
        assert 'failed' in text, (fn,text)
        count += 1
    for ceiling in (0x8bff,0x8c00,0x8c01):
        output, text, calls = execute(inputs, ceiling=ceiling)
        assert (15 in calls) == (ceiling >= 0x8c00), text
        count += 1
    # Exercise actual emitted builder variants at padding/slot/header edges.
    with tempfile.TemporaryDirectory(prefix='native-rlm-edges-') as tmp:
        work = Path(tmp)
        for headers, size in ((1,1),(1,127),(1,128),(1,6144),(2,128)):
            payload = bytes((i*7 & 255 for i in range(size)))
            head = bytearray(headers*512)
            head[:16] = struct.pack('<4sBBHHHHH',b'BCM1',1,headers,0xbb00,
                                    size,(size+255)&~255,0,0)
            expected = bytes(head)+payload
            source = (ROOT/'src/utilities/rlmbuild.mac').read_text().replace(
                '        INCLUDE ccpmeta.inc',metadata(expected))
            image = assemble(Path.home()/'bin/z80asm',expand_layout(source),
                             work/'edge.com',work/'edge.lst',0x100)
            records = {name: payload for name in inputs}
            output, text, calls = execute(records,image=image)
            assert output[:len(expected)] == expected and not any(output[len(expected):]), text
            count += 1
        # Real relocation-rich inputs with an undersized declared table.
        source = (ROOT/'src/utilities/rlmbuild.mac').read_text().replace(
            '        INCLUDE ccpmeta.inc',metadata(module).replace(f'CCP_RELOCS EQU {relocations}', 'CCP_RELOCS EQU 0'))
        image = assemble(Path.home()/'bin/z80asm',expand_layout(source),
                         work/'overflow.com',work/'overflow.lst',0x100)
        output, text, calls = execute(inputs,image=image)
        assert 'status 03' in text and 22 not in calls, text
        count += 1
    for offset, value in ((5,3),(8,0),(9,25),(14,255)):
        bad = bytearray(module); bad[offset] = value
        try: metadata(bad)
        except ValueError: pass
        else: raise AssertionError(('accepted invalid metadata',offset,value))
    print(f'PASS: {count} production RLMBUILD parity/error/TPA/header/padding cases; protected canaries intact')



if __name__ == '__main__': main()
