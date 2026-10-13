#!/usr/bin/env python3
"""PIP's console break behavior during character and reader transfers."""
from test_pip_transfer import execute, key


def main():
    source = key(0, 2, 'SRC.TXT')
    dest = key(1, 7, 'DEST.TXT')
    queue = key(0, 0, '$$$.SUB')
    unrelated_queue = key(0, 7, '$$$.SUB')
    files = {
        source: (b'one\ntwo\x1a', 0), dest: (b'old', 0),
        queue: (b'BATCH', 0), unrelated_queue: (b'OTHER', 0),
    }

    # DRI checks the console after a text line-feed. Ctrl-Z acts as EOF;
    # another queued character aborts the staged transfer.
    out, result, _, _ = execute(
        'B7:DEST.TXT=A2:SRC.TXT[U]', files,
        break_keys=[0x1A], break_at=1,
    )
    assert result[dest][0].startswith(b'ONE')
    assert b'old' not in result[dest][0]
    assert result[source][0] == files[source][0]
    assert result[queue] == list(files[queue])
    assert result[unrelated_queue] == list(files[unrelated_queue])
    assert not any(name[2].endswith(b'$$$') for name in result)

    out, result, _, _ = execute(
        'B7:DEST.TXT=A2:SRC.TXT[U]', files,
        break_keys=[3], break_at=1,
    )
    assert 'ABORTED' in out, out
    assert result[dest] == list(files[dest])
    assert result[source] == list(files[source])
    assert queue not in result
    assert result[unrelated_queue] == list(files[unrelated_queue])
    assert not any(name[2].endswith(b'$$$') for name in result)

    # Object transfers use the historical 256-character console polling
    # interval rather than the text line-feed check.
    obj = key(0, 2, 'CODE.COM')
    obj_dest = key(1, 7, 'CODE.COM')
    obj_files = {obj: (bytes(range(256)), 0), obj_dest: (b'old', 0)}
    out, result, _, _ = execute(
        'B7:CODE.COM=A2:CODE.COM[B]', obj_files,
        break_keys=[3], break_at=1,
    )
    assert 'ABORTED' in out, out
    assert result[obj_dest] == list(obj_files[obj_dest])
    assert result[obj] == list(obj_files[obj])

    # A following text device source must not inherit the preceding COM
    # source's 256-byte polling mode.
    one_record = key(0, 2, 'ONE.COM')
    mixed_files = {one_record: (bytes(range(128)), 0), dest: (b'old', 0)}
    out, result, _, _ = execute(
        'B7:DEST.TXT=A2:ONE.COM,INP:[U]', mixed_files,
        input_bytes=b'a\nb\x1a', patch_in=True,
        break_keys=[3], break_at=1,
    )
    assert 'ABORTED' in out, out
    assert result[dest] == list(mixed_files[dest])

    # DRI checks INP before each BLOCK/HEX read. Ctrl-Z stops; any other
    # queued character requests a reader stop and is treated as XOFF.
    out, result, _, _ = execute(
        'B7:DEST.TXT=INP:[B]', {}, input_bytes=b'data\x1a',
        patch_in=True, break_keys=[ord('X')], break_at=1,
    )
    assert 'READER STOPPING' in out, out
    assert result[key(1, 7, 'DEST.TXT')][0].startswith(b'data')

    out, result, _, _ = execute(
        'B7:DEST.TXT=INP:[B]', {}, input_bytes=b'data\x1a',
        patch_in=True, break_keys=[0x1A], break_at=1,
    )
    assert 'READER STOPPING' not in out, out
    assert result[key(1, 7, 'DEST.TXT')][0] in (b'', b'\x1a' * 128)

    out, result, _, _ = execute(
        'B7:DEST.TXT=RDR:[B]', {}, input_bytes=b'data\x1a',
        break_keys=[ord('X')], break_at=1,
    )
    assert 'READER STOPPING' in out, out
    assert result[key(1, 7, 'DEST.TXT')][0].startswith(b'data')
    print('PASS: PIP text/object interrupts and INP/RDR block reader-stop handling')


if __name__ == '__main__':
    main()
