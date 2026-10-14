#!/usr/bin/env python3
"""Prove production mode-one rebinding precedes generation publication.

The target is synthetic; selecting/validating MCON metadata remains separate.
"""
from pathlib import Path
import re
from system_layout import LAYOUT
import test_rsxcommit as commit

ROOT = Path(__file__).resolve().parents[1]


def main():
    cpu, _ = commit.setup()
    listing = (ROOT / 'build/bios/bios.lst').read_text(errors='replace')
    binding = int(re.search(r'^([0-9a-f]{4})\s+.*\bMP_MON:', listing, re.M)[1], 16)
    provider, prospective, live, public = 0x9000, 0x6500, 0x6540, 0x6700
    publisher = LAYOUT['CONFIG'] + 0x38F
    image = (ROOT / 'build/system/r3persist.bin').read_bytes()
    cpu.mem[publisher:publisher + len(image)] = image
    cpu.mem[prospective:prospective + 41] = bytes(range(41))
    cpu.mem[commit.REQUEST + 7] = 1
    cpu.mem[commit.REQUEST + 24] = 1  # LOAD, not self-retirement
    for offset, value in [(25, publisher), (27, prospective), (29, live),
                           (31, public), (33, 0xFFFF), (35, provider)]:
        cpu.setword(commit.REQUEST + offset, value)
    cpu.setword(binding, 0x9100)
    generation = cpu.word(commit.GEN)

    class ObservedMemory(bytearray):
        stores = 0

        def __setitem__(self, key, value):
            if key == commit.GEN:
                assert cpu.word(binding) == provider, 'generation preceded rebinding'
                assert self[live:live + 41] == bytes(range(41))
                self.stores += 1
            super().__setitem__(key, value)

    cpu.mem = ObservedMemory(cpu.mem)
    cpu.de = commit.REQUEST
    cpu.sp = 0x5F00
    cpu.run(commit.COMMIT, limit=100000)
    assert cpu.a == 0 and cpu.sp == 0x5F00
    assert cpu.word(binding) == provider
    assert cpu.word(public + 12) == 0xFFFF
    assert cpu.word(commit.GEN) == generation + 1 and cpu.mem.stores == 1
    # The request word must not overwrite the fixed continuation's first byte.
    continuation=publisher+0x50
    expected_code=image[0x50:0x67]
    assert bytes(cpu.mem[continuation:continuation+len(expected_code)])==expected_code
    source=0x7000
    restored=bytes((i%251 for i in range(0x3F4)))
    cpu.mem[source:source+len(restored)]=restored
    cpu.setword(publisher+0x67,source)
    cpu.a=0
    cpu.run(continuation,limit=100000)
    assert bytes(cpu.mem[LAYOUT['RSX']:LAYOUT['RSX']+len(restored)])==restored
    assert cpu.sp==0x5F00
    # A rejected scheduler plan must not detach the original binding.
    rejected, _ = commit.setup(bad_snapshot_size=True)
    rejected.setword(binding, 0x9100)
    before = bytes(rejected.mem[commit.OLD_STATEFUL:commit.OLD_STATEFUL + commit.ALLOCATION])
    rejected.de = commit.REQUEST
    rejected.run(commit.COMMIT, limit=100000)
    assert rejected.a != 0 and rejected.word(binding) == 0x9100
    assert bytes(rejected.mem[commit.OLD_STATEFUL:commit.OLD_STATEFUL + commit.ALLOCATION]) == before
    # Legacy mode zero must never read the two new request bytes.
    legacy, _ = commit.setup()
    class LegacyMemory(bytearray):
        def __getitem__(self, key):
            if isinstance(key, int):
                assert key not in (commit.REQUEST + 35, commit.REQUEST + 36)
            return super().__getitem__(key)
    legacy.mem = LegacyMemory(legacy.mem)
    legacy.setword(binding, 0x9100)
    legacy.de = commit.REQUEST
    legacy.run(commit.COMMIT, limit=100000)
    assert legacy.a == 0
    assert legacy.word(binding) == legacy.word(LAYOUT['BIOS'] + 70)
    print('PASS: production prepared rebinding precedes generation; failure retains old binding')


if __name__ == '__main__':
    main()
