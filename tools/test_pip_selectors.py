#!/usr/bin/env python3
"""Expanded PIP DU grammar, preflight safety and retained transfer semantics."""
from test_pip_parser import scan
from test_pip_transfer import execute, key

MUTATING = (19, 21, 22, 23, 30)

def unchanged(command, files, diagnostic, **kwargs):
    out, after, calls, writes = execute(command, files, **kwargs)
    assert diagnostic in out, (command, out)
    assert after == {k: list(v) for k, v in files.items()}, (command, out, after)
    assert not writes and not any(f in calls for f in MUTATING), (command, calls)
    return out

def main():
    source = {
        key(1, 0, 'ZERO.COM'): (b'zero', 0),
        key(1, 1, 'ONE.COM'): (b'one', 1),
        key(1, 3, 'THREE.COM'): (b'three', 4),
        key(1, 31, 'LAST.COM'): (b'last', 0),
        key(2, 7, 'SYS.COM'): (b'system', 6),
        key(1, 3, 'OTHER.TXT'): (b'unselected', 0),
    }
    cases = [
        ('B[-]:*.COM', [(1, 0), (1, 1), (1, 3), (1, 31)]),
        ('B[3-1]:*.COM', [(1, 1), (1, 3)]),
        ('B[-1,31-]:*.COM', [(1, 0), (1, 1), (1, 31)]),
        ('[B[0,3],C7]:*.COM[R]', [(1, 0), (1, 3), (2, 7)]),
        ('[B[0,3],B3,B0]:*.COM[V]', [(1, 0), (1, 3)]),
        ('[B0,1]:*.COM', [(1, 0)]), # user-only term inherits original A
        ('B[0]:ZERO.COM', [(1, 0)]),
    ]
    for operand, dus in cases:
        out, files, calls, _ = execute('A4:=' + operand, source)
        expected = [k for k in source if k[:2] in dus and k[2].endswith(b'COM')]
        for k in expected:
            payload, attr = source[k]
            assert files[(0, 4, k[2])] == [payload.ljust(128, b'\x1a'), attr], (operand, out, k)
        assert len(files) == len(source) + len(expected), (operand, out)
        assert all(files[k] == list(v) for k, v in source.items())
        assert bool(33 in calls) == ('V' in operand)
        assert out.count('COPYING -') == 1
        labels = [f'{chr(65+k[0])}{k[1]}:' + k[2][:8].decode().rstrip() + '.' + k[2][8:].decode().rstrip() for k in sorted(expected)]
        assert [out.index(label) for label in labels] == sorted(out.index(label) for label in labels)
    # Repeated DU terms are deduplicated, but distinct files sharing a name fail.
    duplicates = {key(1, 0, 'SAME.COM'): (b'first', 0),
                  key(1, 7, 'SAME.COM'): (b'second', 0),
                  key(1, 1, 'UNIQUE.COM'): (b'must not copy', 0),
                  key(0, 4, 'SAME.COM'): (b'old destination', 0),
                  key(0, 4, 'SAME.$$$'): (b'old staging', 0)}
    for option in ('', '[W]', '[V]'):
        out = unchanged('A4:=B[-]:*.COM' + option, duplicates, 'DUPLICATE DESTINATION NAME')
        assert 'B0:SAME.COM' in out and 'B7:SAME.COM' in out and 'No files copied.' in out
    # Attributes are filtered before checking duplicates.
    filtered = {key(1, 0, 'X.COM'): (b'normal', 0), key(1, 7, 'X.COM'): (b'system', 2)}
    out, files, _, _ = execute('A4:=B[-]:*.COM', filtered)
    assert files[key(0, 4, 'X.COM')][0].startswith(b'normal'), out
    unchanged('A4:=B[-]:*.COM[R]', filtered, 'DUPLICATE DESTINATION NAME')
    # Existing destination replacement remains the historical PIP transaction.
    existing = {key(1, 0, 'X.COM'): (b'new', 0), key(0, 4, 'X.COM'): (b'old', 0)}
    out, files, calls, _ = execute('A4:=B[-]:*.COM', existing)
    assert files[key(0, 4, 'X.COM')][0].startswith(b'new') and 1 not in calls
    existing[key(0, 4, 'X.COM')] = (b'old', 1)
    for answer, option, prefix in [('N', '', b'old'), ('Y', '', b'new'), ('N', '[W]', b'new')]:
        out, files, calls, _ = execute('A4:=B[-]:*.COM' + option, existing, answer=answer)
        assert files[key(0, 4, 'X.COM')][0].startswith(prefix), out
        assert (1 in calls) == (not option)
    # No mutation on selection overflow or late identity/staging/domain failures.
    many = {key(1, 0, f'F{i:03}.COM'): (b'x', 0) for i in range(65)}
    unchanged('A4:=B[-]:*.COM', many, 'TOO MANY SOURCE FILES')
    out, files, _, _ = execute('A4:=B[-]:*.COM', dict(list(many.items())[:64]))
    assert len(files) == 128, out
    unchanged('A4:=[B0,A4]:*.COM', {**source, key(0, 4, 'SELF.COM'): (b'self', 0)}, 'staging-name conflict')
    unchanged('A4:=B[-]:*.*', {**source, key(1, 7, 'RECOVER.$$$'): (b'keep', 0)}, 'staging-name conflict')
    unchanged('A4:=B[-]:*.COM', {**source, key(0, 4, 'LAST.$$$'): (b'keep', 1)}, 'CANNOT REMOVE TEMPORARY')
    unchanged('A4:=[B0,P7]:*.COM', source, 'INVALID DRIVE')
    unchanged('A4:=B[-]:*.COM', source, 'DRIVE IS R/O', readonly=1)
    unchanged('A4:=B[2]:*.COM', source, 'NOT FOUND')
    for command in ['A4:=B[-]:*.COM[X]', 'A4:=B[-]:*.COM[G0]', 'A4:=B[-]:*.COM[G7]',
                    'A[4]:=B0:*.COM', 'A[-]:=B0:*.COM', 'A4:X.COM=B[-]:X.COM',
                    'LST:=B[-]:*.COM', 'A4:X.COM=B[-]:X.COM,C0:X.COM',
                    'A4:=B[*]:*.COM', 'A4:=B[32]:*.COM', 'A4:=B[1,,3]:*.COM']:
        unchanged(command, source, 'INVALID FORMAT')
    # Nested selector brackets do not split source operands at internal commas.
    assert scan('A4:=[B[0,3],C7]:*.COM[RV]')[0] is False
    # Exact selector files keep PIP character transformations and S/Q punctuation.
    out, files, _, _ = execute('A4:=B[0]:X.TXT[U]', {key(1, 0, 'X.TXT'): (b'abc\x1aignored', 0)})
    assert files[key(0, 4, 'X.TXT')][0].startswith(b'ABC\x1a'), out
    # Selector brackets and S/Q literal punctuation coexist without query handling.
    out, files, _, _ = execute('A4:=[B[0,1]]:X.TXT[Sstart,[] /VER\x1aQend\x1a]',
                              {key(1, 0, 'X.TXT'): (b'prefixstart,[] /VERabcendtail\x1a', 0)})
    assert files[key(0, 4, 'X.TXT')][0].startswith(b'start,[] /VERabcend\r\n\x1a'), out
    # Failed verification preserves an existing destination and cleans staging.
    out, files, _, _ = execute('A4:=B[-]:*.COM[V]', existing, fail='verify')
    assert 'VERIFY ERROR' in out and files[key(0, 4, 'X.COM')] == [b'old', 1]
    assert key(0, 4, 'X.$$$') not in files
    # Multi-extent directory entries must produce one planned source each.
    big = {key(1, 31, 'BIG.COM'): (b'X' * 33001, 4)}
    out, files, _, _ = execute('A4:=B[-]:*.COM[V]', big, exm=1)
    assert out.count('B31:BIG.COM') == 1 and files[key(0, 4, 'BIG.COM')][0].startswith(b'X' * 33001)
    print('PASS: PIP shared DU selectors, canonical/deduplicated scopes, duplicate-name preflight, 64-file bound and retained V/W/R/transfer behavior')

if __name__ == '__main__':
    main()
