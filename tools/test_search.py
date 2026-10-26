#!/usr/bin/env python3
"""Execute the complete SEARCH.COM with independent fixtures and hostile BDOS."""
from pathlib import Path
import re
from search_source import ROOT
from test_search_scan import execute, entry


def main():
    image = (ROOT/'build/utilities/SEARCH.COM').read_bytes()
    listing = (ROOT/'build/utilities/search.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':', listing, re.M | re.I)[1], 16)
    a = (0,0,b'ONE     TXT')
    b = (1,3,b'TWO     TXT')
    directories = {(0,0): [entry('ONE.TXT'), entry('ONE.TXT',1)], (1,3): [entry('TWO.TXT')]}
    data = {a:b'4142 AB 4142\r\n'+b'\x1a'*114, b:b'4142\r\n'+b'.'*122}
    maximum_stack = 0
    def run(tail, dirs=directories, files=data, **kwargs):
        nonlocal maximum_stack
        result = execute(image, address, tail, dirs, files, command=True, **kwargs)
        maximum_stack = max(maximum_stack, result['stack_bytes'])
        return result
    r = run('"4142" [A0,B3]:*.TXT')
    assert r['totals'] == [2,2,3,1,4], r
    assert r['output'].count('[TEXT]') == 2
    assert 'A0:ONE.TXT [TEXT] line 1: 4142 AB 4142' in r['output']
    assert 'A0:ONE.TXT [HEX] offset 00000005' in r['output']
    for label, count in [('Files searched',2), ('Files matched',2), ('Text matches',3), ('Hex matches',1), ('Total matches',4)]:
        assert f'{label}: {count}\r\n' in r['output'], r['output']
    for tail in ['/HELP /VER garbage', '"/VER" A0:*.TXT /HELP', '/VER /BOGUS']:
        q = run(tail)
        assert set(q['services']) == {6}, q
        assert not q['opens'] and not q['reads']
        from utility_versions import display_development
        expected = 'SEARCH 1.0 (001-dev)' if display_development('utility:SEARCH') else 'SEARCH 1.0 (001)'
        assert expected in q['output']
        if '/HELP' in tail:
            assert 'Usage:' in q['output']
        assert all(len(line) <= 79 for line in q['output'].splitlines())
        assert len(q['output'].splitlines()) <= 23
    for tail in ['', 'A0:*.TXT "x"', '"x" A0:*.TXT /NOTEXT', '"x" A0:*.TXT /NOHEX /NOTEXT']:
        q = run(tail)
        assert 'Invalid command' in q['output'] and not q['opens'] and not q['reads']
        assert not set(q['services']) & {14,15,17,18,25,26,32,33,35}
    # First matching occurrence chooses the single line excerpt, counts include
    # every later occurrence. Terminal controls are escaped, not executed.
    payload = b'X\0\x1b\t\x1a\xffX\r\n'+b'.'*119
    assert len(payload) == 128
    q = run('"X" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT')]}, {a:payload})
    assert q['totals'] == [1,1,2,0,2]
    assert q['output'].count('[TEXT]') == 1
    assert 'X<00><1B><09><1A><FF>X' in q['output']
    assert '\x1b' not in q['output']
    # Very long line, distant matches, bounded memory/display; all count.
    payload = b'.'*65535+b'AB'+b'.'*127
    payload += b'.'*(-len(payload)%128)
    q = run('"AB" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT'),entry('ONE.TXT',1)]}, {a:payload})
    assert q['totals'] == [1,1,1,0,1]
    assert '[...]' in q['output'] and 'AB' in q['output']
    assert len(q['output']) < 1000
    last_detail = run('"AB" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT')]}, {a:payload}, cancel_after=120)
    assert last_detail['totals'] == q['totals'] and 'DISPLAY INTERRUPTED' in last_detail['output']
    # Mixed line boundaries and a matched terminator spanning CRLF.
    payload = b'X\r\nX\rX\nX'
    payload += b'.'*(-len(payload)%128)
    q = run('"X" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT')]}, {a:payload})
    for line in (1,2,3,4):
        assert f'[TEXT] line {line}:' in q['output']
    q = run('"\n" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT')]}, {a:payload})
    assert '[TEXT] line 1: X<0D><0A>X' not in q['output']
    assert '[TEXT] line 1: X<0D><0A>' in q['output']
    assert q['totals'] == [1,1,2,0,2]
    payload = b'X'*64+b'\r\n'+b'.'*62
    q = run('"\n" A0:*.TXT /NOHEX', {(0,0):[entry('ONE.TXT')]}, {a:payload})
    assert '[...]' not in q['output'] and '<0D><0A>' in q['output']
    # Enough lines to exercise real rendered-row paging and complete scan after
    # an early display stop. Space and Enter both continue by full pages.
    payload = b'X\r\n'*80
    payload += b'\x1a'*(-len(payload)%128)
    dirs = {(0,0):[entry('ONE.TXT')]}
    files = {a:payload}
    plain = run('"X" A0:*.TXT /NOHEX', dirs, files)
    for key in (b' ', b'\r'):
        paged = run('"X" A0:*.TXT /NOHEX /P', dirs, files, keys=key)
        assert paged['totals'] == plain['totals'] == [1,1,80,0,80]
        assert paged['output'].count('Space/Enter:') == 3
        assert paged['output'].count('[TEXT]') == 80
    stopped = run('"X" A0:*.TXT /NOHEX /P', dirs, files, keys=b'\x03')
    assert stopped['totals'] == plain['totals']
    assert stopped['output'].count('[TEXT]') == 23
    assert stopped['output'].count('Space/Enter:') == 1
    assert 'DISPLAY INTERRUPTED\r\nSEARCH CONTINUING...' in stopped['output']
    assert 'Total matches: 80' in stopped['output'] and not stopped['incomplete']
    unpaged = run('"X" A0:*.TXT /NOHEX', dirs, files, cancel_after=120)
    assert unpaged['totals'] == plain['totals'] and 'DISPLAY INTERRUPTED' in unpaged['output']
    # A failure after display suppression is still visible and qualifies totals.
    faulted = run('"X" A0:*.TXT /NOHEX /P', dirs, files, keys=b'\x03', read_error=(a,1))
    assert faulted['incomplete'] and 'Search incomplete' in faulted['output']
    assert 'SEARCH: A0:ONE.TXT' in faulted['output']
    reread = run('"X" A0:*.TXT /NOHEX', dirs, files, render_error=(a,0))
    assert reread['incomplete'] and reread['totals'] == plain['totals']
    assert 'Search incomplete' in reread['output']
    # Essential errors occupy rendered rows too. After display suppression,
    # they remain visible and cannot create another prompt.
    errors = run('"X" [A[16-31],B[16-31]]:*.TXT /NOHEX /P', {}, {},
                 max_user=15, keys=b'\x03')
    assert errors['output'].count('Location unavailable') == 32
    assert errors['output'].count('Space/Enter:') == 1
    assert 'DISPLAY INTERRUPTED' in errors['output'] and errors['incomplete']
    assert errors['totals'] == [0]*5
    # Decimal summaries retain full uint64 precision, including saturation.
    c = reread['c']
    for number in (0, 0x100000000, 0xFFFFFFFFFFFFFFFF):
        where = address('DLINEVAL')
        c.mem[where:where+8] = number.to_bytes(8, 'little')
        c.hl = where
        start = len(reread['rawoutput'])
        c.run(address('DDECIMAL'), limit=1000000)
        assert reread['rawoutput'][start:].decode() == str(number)
    print('SEARCH.COM: queries, validation, dual results, excerpts, safe rendering, paging/suppression, totals and errors pass; '
          f'maximum observed private stack {maximum_stack}/512 bytes')


if __name__ == '__main__':
    main()
