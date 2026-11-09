#!/usr/bin/env python3
"""Run production NOAH on the Z80 core with the established PATH memory ABI.

BDOS remains an exact-DU file provider: only NOAH can perform PATH searches.
The separate guest test exercises launch through the real CCP.
"""
from pathlib import Path
from test_noah_write import machine
from test_usq_com import diskkey, padded
from test_lbr import archive, entry, with_crcs
from test_sq import host_decode
from test_ark import member as arc_member

# Independent published v1.1 memory layouts: WBOOT vector, BM descriptor, PATH.
LAYOUTS = ((0xe994, 0xd644, 0xe42a),       # Model 4 / conventional
           (0xf594, 0xe244, 0xf02a),       # cpmsim full RAM
           (0xf5ec, 0xe244, 0xf02a))       # Model II full RAM


def tests(m):
    # The inherited literal fixtures must still match current 1.2's contract,
    # including all platform profiles used by PATH.COM and the NOAH builder.
    from build_profiles import PROFILES, profile_inputs, symbols
    from noah_overlays import path_layouts
    source = Path(__file__).resolve().parents[1] / 'src/system/layout.inc'
    text = source.read_text()
    assert 'LY_LERR         EQU     LY_EXT-17' in text
    assert 'LY_PATH         EQU     LY_LERR+1' in text
    layouts = [symbols(text)]
    layouts += [profile_inputs(p, source)[0]['symbols'] for p in PROFILES.values()]
    current = {(v['LY_BIOS'] + 3, v['LY_SYS'] + 0x80, v['LY_EXT'] - 16) for v in layouts}
    assert current == set(LAYOUTS) == set(path_layouts()), current
    provider = m.bdos
    attempts = []
    fault = {"read": False}

    def bdos(fn, de):
        if fn == 15 and de == m.symbols['NR_FCB']:
            assert not any(m.mem[de+12:de+36]), 'Open scratch not reset'
            attempts.append(m.fcbkey(de))
            result = provider(fn, de)
            if result == 255:
                m.mem[de+12:de+36] = bytes([0xcc])*24
            return result
        if fn == 20 and de == m.symbols['NR_FCB'] and fault['read']:
            m.events.append((fn, de))
            return 2
        return provider(fn, de)

    m.bdos = bdos
    good = with_crcs(archive([entry(b'README  TXT')], b'X'*128))
    ovl = m.overlay
    local, first, last = (diskkey(2, 'NOAH.OVL', 7),
                          diskkey(3, 'NOAH.OVL', 4), diskkey(1, 'NOAH.OVL'))

    def run(files, path=b'\x02\x03\x04\x01\x00', layout=LAYOUTS[1],
            header=b'BM\x01\x05', tail='/L TEST.LBR'):
        memory = {}
        if layout:
            wboot, descriptor, path_address = layout
            memory = {1: wboot.to_bytes(2, 'little'), descriptor: header, path_address: path}
        attempts.clear()
        files = {diskkey(2, 'TEST.LBR', 7): good, **files}
        text = m.run(tail, files, drive=2, user=7, supply_overlay=False, system_memory=memory)
        assert (m.drive, m.user, m.dma) == (2, 7, 0x80), text
        assert not m.opened, text
        m.intact()
        return text

    # Before the fix this first cross-DU case fails, even with a matching PATH.
    for layout in LAYOUTS:
        text = run({first: ovl}, layout=layout)
        assert 'README.TXT' in text and 'operation stopped' not in text, text
        assert attempts == [local, first], attempts
        text = run({local: ovl, first: b'bad'}, layout=layout)
        assert 'README.TXT' in text and attempts == [local], (text, attempts)

    text = run({last: ovl})
    assert 'README.TXT' in text and attempts == [local, first, last], (text, attempts)
    text = run({})
    assert 'NOAH.OVL not found' in text and attempts == [local, first, last], (text, attempts)

    # First found wins, even if a later directory contains the correct build.
    # Header/ABI/build mismatches, truncated, trailing, and CRC-bad bodies.
    for offset in (0, 8, 24):
        bad = bytearray(ovl); bad[offset] ^= 1
        text = run({first: bytes(bad), last: ovl})
        assert 'invalid or incompatible' in text and attempts == [local, first], (text, attempts)
    for bad in (b'', ovl[:-128], ovl+bytes(128), ovl[:-1]+bytes([ovl[-1]^1])):
        text = run({first: bad, last: ovl})
        assert 'invalid or incompatible' in text and attempts == [local, first], (text, attempts)
    text = run({local: b'bad', first: ovl})
    assert 'invalid or incompatible' in text and attempts == [local], (text, attempts)

    fault['read'] = True
    text = run({first: ovl, last: ovl})
    fault['read'] = False
    assert 'invalid or incompatible' in text and attempts == [local, first], (text, attempts)

    # Maximum six-entry list: no candidate is omitted or reordered.
    path = bytes([6, 0, 255, 3, 1, 3, 2, 3, 3, 3, 4, 3, 5])
    end = diskkey(3, 'NOAH.OVL', 5)
    text = run({end: ovl}, path=path)
    assert 'README.TXT' in text and attempts == [local] + [diskkey(3, 'NOAH.OVL', u) for u in range(1, 6)], (text, attempts)

    # Resolve dynamic fields against the invocation DU, not a prior candidate.
    dynamic = diskkey(3, 'NOAH.OVL', 7)
    text = run({dynamic: ovl}, path=bytes([3, 0, 255, 1, 4, 3, 255]))
    assert 'README.TXT' in text and attempts == [local, diskkey(1, 'NOAH.OVL', 4), dynamic], (text, attempts)
    text = run({diskkey(2, 'NOAH.OVL', 5): ovl}, path=bytes([2, 3, 4, 0, 5]))
    assert 'README.TXT' in text and attempts[-1] == diskkey(2, 'NOAH.OVL', 5), text

    # Count zero is the default current-DU/A0 policy. No hardcoded A0 appended
    # to an explicit list. Unsupported systems retain the original fallback.
    for layout, header in ((LAYOUTS[1], b'BM\x01\x05'), (None, b'xxxx'),
                           (LAYOUTS[1], b'BM\x01\x03'),
                           (LAYOUTS[1], b'BM\x02\x05'),
                           (LAYOUTS[1], b'XX\x01\x05')):
        text = run({last: ovl}, path=b'\x00', layout=layout, header=header)
        assert 'README.TXT' in text and attempts == [local, last], (text, attempts)
    text = run({last: ovl}, path=bytes([1, 3, 4]))
    assert 'not found' in text and attempts == [local, first], (text, attempts)
    for bad_path in (bytes([7]), bytes([1, 17, 0]), bytes([1, 1, 32])):
        text = run({last: ovl}, path=bad_path)
        assert 'not found' in text and attempts == [local], (text, attempts)

    # Codec phases reopen the selected overlay; restoration and output placement
    # must continue working when the overlay lives in another drive/user area.
    source = diskkey(2, 'TEXT.DAT', 7)
    text = run({first: ovl, source: b'hello'*30}, tail='/SQ TEXT.DAT B7:')
    assert 'published' in text and attempts.count(first) > 1, (text, attempts)
    assert host_decode(m.files[diskkey(2, 'TEXT.DQT', 7)], record_padding=True)[1] == padded(b'hello'*30)
    # Archive readers retain their context register across a PATH-based phase
    # reload. Exercise both formats, including extraction to another DU.
    arc = arc_member(b'archive bytes', name=b'README.TXT') + b'\x1a\0'
    arc_key = diskkey(2, 'TEST.ARC', 7)
    text = run({first: ovl, arc_key: arc}, tail='/L TEST.ARC')
    assert 'README.TXT' in text and attempts.count(first) > 1, text
    text = run({first: ovl}, tail='/X TEST.LBR D4:')
    assert m.files[diskkey(4, 'README.TXT', 4)] == b'X'*128, text
    text = run({first: ovl, arc_key: arc}, tail='/X TEST.ARC D4:')
    assert m.files[diskkey(4, 'README.TXT', 4)] == padded(b'archive bytes'), text
    text = run({first: ovl, source: b'hello'*30}, tail='/ADD /Y NEW.ARC TEXT.DAT')
    assert 'published' in text and attempts.count(first) > 1, text
    # Query paths need neither overlay nor PATH support.
    for tail in ('/HELP', '/VER'):
        text = run({}, tail=tail)
        assert 'NOAH' in text and not attempts, text
    m.bdos = provider
    print(f'PASS: {m.cases} NOAH overlay PATH cases; all three v1.1 layouts; drive/user/DMA restored')


if __name__ == '__main__':
    tests(machine())
