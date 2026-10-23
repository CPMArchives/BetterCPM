#!/usr/bin/env python3
"""Reject LibDsk boot-probe geometry inferred from CP/M directory data.

Read allocation blocks independently through the FDF sector map; a second
cpmcp read alone can repeat the same incorrect mapping and mask a bad seed.
"""
from pathlib import Path
import subprocess
import tempfile

from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from fdf_format import select_fdf

ROOT = Path(__file__).resolve().parents[1]
NAME = 'bettercpm-mm-80t-ds-data'
FORMAT = 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)'


def read_file(raw, fmt, user, name):
    """Read an EXM=0 16-bit allocation file without cpmtools or LibDsk."""
    assert fmt.exm == 0 and fmt.dsm > 255
    mapping = fmt.raw_record_map()

    def record(number):
        track, slot = divmod(number, fmt.spt)
        offset = (track * fmt.spt + mapping[slot]) * 128
        return raw[offset:offset+128]

    def data_record(number):
        return record(fmt.reserved_records + number)

    stem, _, ext = name.upper().partition('.')
    key = stem.ljust(8).encode() + ext.ljust(3).encode()
    directory = b''.join(data_record(i) for i in range((fmt.drm+1)*32//128))
    extents = {}
    for offset in range(0, len(directory), 32):
        entry = directory[offset:offset+32]
        if entry[0] != user or bytes(x & 127 for x in entry[1:12]) != key:
            continue
        extent = (entry[14] & 63)*32 + (entry[12] & 31)
        assert extent not in extents and entry[15] <= 128
        blocks = [int.from_bytes(entry[i:i+2], 'little') for i in range(16,32,2)]
        chunks = []
        for index in range(entry[15]):
            block = blocks[index >> fmt.bsh]
            assert 0 < block <= fmt.dsm
            chunks.append(data_record((block << fmt.bsh) + (index & fmt.blm)))
        extents[extent] = b''.join(chunks)
    assert extents and sorted(extents) == list(range(len(extents))), name
    return b''.join(extents[i] for i in sorted(extents))


def main():
    fmt = select_fdf(ROOT/'third_party/montezuma/DISK-INT.FDF', FORMAT)
    definitions = disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT))
    # This first file fills the directory allocation words which LibDsk's
    # boot probe wrongly interprets as geometry. Each later open probes again.
    values = {'BIG.BIN': (bytes(range(256))*274)[:70001].ljust(70016, b'\x1a'),
              'DEFAULT.TXT': b'logged drive defaults'.ljust(128, b'\x1a'),
              'SQU00000.$$$': b'preexisting SQ sentinel'.ljust(128, b'\x1a'),
              'USQ00000.$$$': b'preexisting USQ sentinel'.ljust(128, b'\x1a')}
    with tempfile.TemporaryDirectory(prefix='model4-raw-geometry-') as temp:
        for pinned in [False, True]:
            work = Path(temp)/str(pinned);work.mkdir()
            definition = definitions if pinned else definitions.replace(' libdsk:format pcw800\n', '')
            (work/'diskdefs').write_text(definition)
            image = work/'data.raw';image.write_bytes(b'\xe5'*fmt.image_bytes)
            def run(*args):
                subprocess.run(args, cwd=work, check=True, capture_output=True)
            run('mkfs.cpm', '-f', NAME, str(image))
            for name, value in values.items():
                host = work/'input.bin';host.write_bytes(value)
                run('cpmcp', '-T', 'raw', '-f', NAME, str(image), str(host), '0:'+name)
                host = work/'readback.bin'
                run('cpmcp', '-T', 'raw', '-f', NAME, str(image), '0:'+name, str(host))
                if pinned or name != 'BIG.BIN':
                    assert host.read_bytes() == value, (pinned, name, 'circular host readback')
            matches = {name: read_file(image.read_bytes(),fmt,0,name)==value for name,value in values.items()}
            if pinned:
                assert all(matches.values()), matches
            else:
                # This is the regression trigger on the installed LibDsk 1.4.2.
                # An upstream fix may remove it; the pinned positive case must
                # still pass. Record whether the old path reproduced the defect.
                print('Unpinned physical readback:', matches)
            print('PASS: pinned independent FDF readback' if pinned else 'Unpinned circular readback alone was insufficient.')


if __name__ == '__main__':
    main()
