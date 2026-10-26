#!/usr/bin/env python3
"""Verify SQ-to-ARC method-4 body adaptation on the full Z80 core."""
import random
import shutil
from pathlib import Path
import subprocess

from noah_overlays import assemble
from test_ark import crc16, member
from test_sq import BASE, ENTRIES, EXTRA, Encoder, host_decode

ROOT = Path(__file__).resolve().parents[1]
class ArkSqEncoder(Encoder):
    def __init__(self, library, image):
        super().__init__(library, image)
        self.symbols['NASQ_RUN'] = self.word(BASE + (len(ENTRIES) + len(EXTRA)) * 2)
        self.symbols['NASQ_DISPATCH'] = self.word(BASE + (len(ENTRIES) + len(EXTRA) + 1) * 2)
        self.arc_mode = 0xF000

    def encode_body(self, raw):
        self.configure(raw, name=b'')
        assert self.call('SQ_INIT', budget=500_000_000) == 0
        assert self.call('SQ_SCAN', budget=500_000_000) == 0
        self.mem[self.arc_mode] = 1
        assert self.call('NASQ_DISPATCH', budget=500_000_000) == 0
        self.mem[self.arc_mode] = 0
        assert self.mem[self.ctx + 52] == 0
        return bytes(self.output)


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    names = ('codec.inc', 'codec.mac', 'usq.inc', 'usq.mac', 'sq.inc')
    text = ' ORG 100H\n' + ''.join((ROOT / 'src/codec' / n).read_text() + '\n' for n in names)
    sq = (ROOT / 'src/codec/sq.mac').read_text()
    text += sq + '\n'
    text += ''.join(f' DW {name}\n' for name in ENTRIES + EXTRA + ('NASQ_RUN', 'NASQ_DISPATCH'))
    text += 'NR_ARC_MODE EQU 0F000H\n'
    text += ' CODEC_CODE\n USQ_CODE\n SQ_CODE\n'
    text += (ROOT / 'src/utilities/common/noahark-sq-bridge.inc').read_text() + '\n'
    text += 'READ_CB: RET\nWRITE_CB: RET\nREWIND_CB: RET\n END\n'
    raw, _ = assemble(Path.home() / 'bin/z80asm', out, 'ARKSQ', text)
    core = Path.home() / 'projects/git/z80pack/z80core'
    (out / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for n in ('simmem.h', 'simport.h'):
        shutil.copy2(core.parent / 'z80sim/srcsim' / n, out / n)
    from test_usq import SHIM
    shim = SHIM.replace('static WORD readpc, writepc;', 'static WORD readpc, writepc, rewindpc;\n'
                        'void set_rewindpc(WORD p) { rewindpc=p; }')
    shim = shim.replace('if(hook && PC==writepc) hook(1);',
                        'if(hook && PC==writepc) hook(1);\n  if(hook && PC==rewindpc) hook(2);')
    (out / 'shim.c').write_text(shim)
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-I' + str(out), '-I' + str(core),
                    str(out / 'shim.c'), str(core / 'simglb.c'),
                    *map(str, sorted(core.glob('simz80*.c'))), '-o', str(out / 'core.so')], check=True)
    return ArkSqEncoder(__import__('ctypes').CDLL(str(out / 'core.so')), raw)


def main():
    import tempfile
    with tempfile.TemporaryDirectory(prefix='ark-sq-bridge-') as d:
        m = build(Path(d))
        rng = random.Random(454)
        samples = [b'', b'A', b'\x90', b'\x1a', bytes(range(256)), b'Z' * 4096,
                   b'\x90' * 600, bytes(rng.randrange(256) for _ in range(4096))]
        for data in samples:
            body = m.encode_body(data)
            # Reconstituting SQ's five-byte empty-name prefix lets the existing
            # independent Squeeze parser validate the unchanged tree and bits.
            standalone = b'\x76\xff' + (sum(data) & 0xffff).to_bytes(2, 'little') + b'\0' + body
            assert host_decode(standalone) == (b'', data)
        assert m.encode_body(b'') == b'\0\0'

        # The ordinary SQ entry retains its complete standalone framing.
        ordinary_data = b'unchanged standalone path'
        m.configure(ordinary_data, name=b'')
        assert m.call('SQ_INIT', budget=500_000_000) == 0
        assert m.call('SQ_SCAN', budget=500_000_000) == 0
        assert m.call('NASQ_DISPATCH', budget=500_000_000) == 0
        ordinary = bytes(m.output)
        assert host_decode(ordinary) == (b'', b'unchanged standalone path')

        # Wrong-state and sink failures leave the context mode cleared.
        m.configure(b'abc', name=b'')
        assert m.call('SQ_INIT') == 0
        assert m.call('NASQ_RUN') == 0x0C and m.mem[m.ctx + 52] == 0
        m.configure(b'abc', name=b'')
        assert m.call('SQ_INIT') == m.call('SQ_SCAN') == 0
        m.write_error = (0, 0xE7)
        assert m.call('NASQ_RUN') == 8 and m.mem[m.ctx + 52] == 0

        # Feed an actual assembled encoder body through production NOAH's
        # method-4 TEST path at each previously measured platform ceiling.
        from test_noah_write import machine as noah_machine
        from test_usq_com import diskkey
        payload = b'ARC method-4 encoder bridge'
        body = m.encode_body(payload)
        arc = member(body, 4, b'BRIDGE.BIN', logical=len(payload), crc=crc16(payload)) + b'\x1a\0'
        noah = noah_machine()
        for ceiling in (0xC501, 0xCA01):
            transcript = noah.run('/TEST BRIDGE.ARC',
                                  {diskkey(1, 'BRIDGE.ARC'): arc}, tpa=ceiling)
            assert 'Outcome: success.' in transcript and 'verified 00000001' in transcript, transcript
        print(f'PASS: {len(samples)} assembled SQ streams adapt to ARC method-4 bodies; '
              'production method-4 TEST accepts output at both TPA ceilings; '
              'standalone SQ unchanged and failure mode reset')


if __name__ == '__main__':
    main()
