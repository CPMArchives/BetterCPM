#!/usr/bin/env python3
"""Exercise the isolated native ARC method-8 encoder entry on a full Z80 core."""
import ctypes as C
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from test_cr import Codec, ENTRIES as CR_ENTRIES, ROOT, SHIM, SIZE
from test_ark import crc16, member
from test_noah_ark_lzw import dynamic_codes, rle
from test_noah_write import machine as noah_machine
from test_usq_com import diskkey, padded

class ArcCodec(Codec):
    def __init__(self, library, image):
        super().__init__(library, image, encode=True)
        self.symbols['N8_RUN'] = self.word(0x100 + len(CR_ENTRIES) * 2)

    def compress_arc(self, data):
        self.configure(data)
        assert self.call('CR_INIT') == 0
        status = self.call('N8_RUN')
        assert status == 0, (status, self.mem[self.ctx+2], self.mem[self.ctx+3], self.mem[self.ctx+4], self.position, hex(self.regs['PC'].value), len(self.output))
        assert self.position == len(data) and self.reads == len(data) + 1
        assert self.call('N8_RUN') == 0
        return bytes(self.output)

def build(assembler, z80pack, cc):
    with tempfile.TemporaryDirectory(prefix='bettercpm-ark8-') as temp:
        work = Path(temp)
        for name in ('codec.inc', 'codec.mac', 'cr.inc', 'cr.mac', 'uncr.inc', 'uncr.mac'):
            shutil.copy2(ROOT / 'src/codec' / name, work / name)
        shutil.copy2(ROOT / 'src/utilities/common/noahark-crencode.inc', work)
        text = '        ORG 100H\n'
        text += ''.join(f'        INCLUDE {n}\n' for n in ('codec.inc', 'codec.mac', 'cr.inc', 'cr.mac', 'uncr.inc', 'uncr.mac'))
        text += '        DW ' + ','.join(CR_ENTRIES) + ',0\n'
        text += 'READ_CB: RET\nWRITE_CB: RET\n        CODEC_CODE\n        CR_CODE\n        UNCR_CODE\n'
        text += (work / 'noahark-crencode.inc').read_text() + '\n        END\n'
        (work / 'test.mac').write_text(text)
        result = subprocess.run([str(assembler), '-e32', '-fb', '-otest.bin', '-ltest.lst', 'test.mac'], cwd=work, capture_output=True)
        if result.returncode:
            listing = (work / 'test.lst').read_text(errors='replace') if (work / 'test.lst').exists() else ''
            Path('/tmp/noah-ark8-assembler.lst').write_text(listing)
            rows = listing.splitlines()
            suspicious = []
            for i, line in enumerate(rows):
                if 'undefined' in line.lower() or '????' in line:
                    suspicious.extend(rows[max(0, i-2):i+2])
            suspicious.extend(line for line in rows if 'N8_RUN' in line)
            raise RuntimeError(result.stdout.decode(errors='replace') + '\n' + '\n'.join(suspicious))
        image = bytearray((work / 'test.bin').read_bytes())
        import re
        match = re.search(r'(?m)^([0-9a-f]{4})\s+.*\bN8_RUN:', (work / 'test.lst').read_text(errors='replace'), re.I)
        if not match:
            raise RuntimeError('assembler listing omitted N8_RUN address')
        entry = int(match.group(1), 16)
        offset = 2 * len(CR_ENTRIES)
        image[offset:offset+2] = entry.to_bytes(2, 'little')
        image = bytes(image)
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(z80pack / 'z80sim/srcsim' / name, work / name)
        (work / 'shim.c').write_text(SHIM)
        core = z80pack / 'z80core'
        subprocess.run([cc, '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work / 'shim.c'), str(core / 'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work / 'core.so')], check=True)
        # Keep the image and shared library alive after the temporary directory closes.
        return image, C.CDLL(str(work / 'core.so'))

def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    p.add_argument('--z80pack', type=Path, default=Path.home() / 'projects/git/z80pack')
    p.add_argument('--cc', default='cc')
    a = p.parse_args()
    image, lib = build(a.assembler, a.z80pack, a.cc)
    m = ArcCodec(lib, image)
    rng = random.Random(80517)
    samples = [b'', b'A', b'\0', b'\x1a', b'\x90', b'\xff', b'ABABABA',
               b'A'*2, b'B'*3, b'Z'*255, b'Z'*256, b'\x90'*512,
               b'CP/M\r\n'*500, bytes(range(256))*4,
               bytes(rng.randrange(256) for _ in range(20000))]
    samples += [bytes(rng.randrange(128) for _ in range(n)) for n in (250, 255, 760, 800, 1800, 2000, 3900, 4100)]
    for raw in samples:
        encoded = m.compress_arc(raw)
        expected = b'\x0c' + dynamic_codes(rle(raw), 12)
        assert encoded == expected, (len(raw), len(encoded), len(expected), encoded[:40].hex(), expected[:40].hex())
    fault_data = bytes(range(256))
    for offset, reason in ((0, 0), (1, 0x41), (2, 0x73), (17, 0)):
        m.configure(fault_data)
        assert m.call('CR_INIT') == 0
        m.write_error = (offset, reason)
        assert m.call('N8_RUN') == 8
        assert m.mem[m.ctx+2] == 4 and m.mem[m.ctx+4] == reason
        events = (m.reads, m.writes, len(m.output))
        assert m.call('N8_RUN') == 8 and events == (m.reads, m.writes, len(m.output))
    for offset in (0, 1, 127):
        m.configure(fault_data)
        assert m.call('CR_INIT') == 0
        m.read_error = (offset, 0x37)
        assert m.call('N8_RUN') == 7
        assert m.mem[m.ctx+2] == 4 and m.mem[m.ctx+4] == 0x37
        events = (m.reads, m.writes, len(m.output))
        assert m.call('N8_RUN') == 7 and events == (m.reads, m.writes, len(m.output))
    qualify_production(m, samples[0:6] + [samples[12], samples[-1]])
    print(f'PASS: {len(samples)} ARC method-8 streams match the independent model; NOAH production TEST/EXTRACT and Deark/ARC oracles agree; {m.calls} Z80 entry calls; context {SIZE} bytes.')

def qualify_production(encoder, samples):
    arc = ROOT / 'build/noah-proof/references/arc-325047b2dc60fad5f6c8238d8cb5294b9a5ada38/arc'
    deark = ROOT / 'build/noah-proof/references/deark-c19b47c80a5ff8a7b41eb4f578e1afdda99202a2/deark'
    native = noah_machine()
    native.instruction_budget = 450000000
    for index, raw in enumerate(samples):
        body = encoder.compress_arc(raw)
        wire = member(body, 8, b'CR8.BIN', logical=len(raw), crc=crc16(raw)) + b'\x1a\0'
        report = native.run('/TEST CHECK.ARC', {diskkey(1, 'CHECK.ARC'): wire}, tpa=0xc501)
        assert 'Outcome: success.' in report, (index, report)
        report = native.run('/X /Y CHECK.ARC', {diskkey(1, 'CHECK.ARC'): wire}, tpa=0xca01)
        assert 'Outcome: success.' in report, (index, report)
        assert native.files[diskkey(1, 'CR8.BIN')] == padded(raw), (index, report)
        for exe, args, glob in ((arc, ['x', 'input.arc'], 'CR8.BIN'),
                                (deark, ['-od', 'out', 'input.arc'], '*CR8.BIN')):
            with tempfile.TemporaryDirectory(prefix='bettercpm-ark8-oracle-') as temp:
                root = Path(temp)
                (root / 'input.arc').write_bytes(wire)
                (root / 'out').mkdir()
                result = subprocess.run([str(exe), *args], cwd=root, capture_output=True)
                assert result.returncode == 0, (exe, result.stdout, result.stderr)
                folder = root / 'out' if exe == deark else root
                outputs = list(folder.glob(glob))
                assert len(outputs) == 1 and outputs[0].read_bytes() == raw, (exe, index, result.stdout, result.stderr)

if __name__ == '__main__':
    main()
