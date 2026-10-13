#!/usr/bin/env python3
"""Exercise PIP's keyboard abort through real cpmsim and BDOS paths."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                          text=True).stdout


def install(disk, work, source, target):
    run('cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
        str(source), target, cwd=work)


def extract(disk, work, name, target):
    output = work / target
    run('cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
        name, str(output), cwd=work)
    return output.read_bytes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = ROOT / 'build/test-results/pip-interruption'
    report.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='pip-interrupt-',
                                     dir='/private/tmp') as temporary:
        work = Path(temporary)
        shutil.copytree(args.image_dir / 'disks', work / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
        disk = work / 'disks/drivea.dsk'
        install(disk, work, ROOT / 'build/pip-development/PIP.COM',
                '0:PIPDEV.COM')

        source = work / 'SOURCE.TXT'
        source.write_bytes(b'FIRST LINE\r\nSECOND LINE\r\n' + b'X' * 1024)
        install(disk, work, source, '2:SOURCE.TXT')
        previous = work / 'PREVIOUS.TXT'
        previous.write_bytes(b'OLD DESTINATION\r\n')
        install(disk, work, previous, '7:DEST.TXT')
        queue = work / 'A0QUEUE.SUB'
        queue.write_bytes(b'PENDING A0 BATCH\r\n')
        install(disk, work, queue, '0:$$$.SUB')
        unrelated = work / 'A7QUEUE.SUB'
        unrelated.write_bytes(b'UNRELATED A7 QUEUE\r\n')
        install(disk, work, unrelated, '7:$$$.SUB')

        transcript = session(args.simulator, work / 'disks', [
            (b':PIPDEV A7:DEST.TXT=A2:SOURCE.TXT[U]\rX',
             b'ABORTED', 30),
            (b'', b'A0>_ ', 30),
        ], report / 'transcript.txt')
        assert b'ABORTED' in transcript, transcript.decode(errors='replace')

        listing = run('cpmls', '-T', 'raw', '-f', 'bettercpm-default',
                      str(disk), cwd=work).lower()
        assert 'dest.$$$' not in listing, listing
        user7 = listing.split('7:', 1)[1]
        assert '$$$.sub' not in listing.split('2:', 1)[0]
        assert '$$$.sub' in user7, listing
        assert extract(disk, work, '7:DEST.TXT', 'DEST.OUT') == previous.read_bytes()
        assert extract(disk, work, '7:$$$.SUB', 'QUEUE.OUT') == unrelated.read_bytes()
        assert extract(disk, work, '2:SOURCE.TXT', 'SOURCE.OUT') == source.read_bytes()
        (report / 'listing.txt').write_text(listing)

    print('PASS: real cpmsim PIP abort preserves destination and source, removes staging and cancels only A0 SUBMIT')


if __name__ == '__main__':
    main()
