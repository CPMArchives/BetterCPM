"""Build a labelled diagnostic fixture; this is not an original Ampro disk."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '2026-11-05-cpc'))
from qualify import decode, select_fdf


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new fixture directory')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True)
    shutil.copyfile(HERE / 'diskdefs', out / 'diskdefs')
    image = out / 'synthetic-ampro400s.dsk'
    result = subprocess.run(['dskform', '-type', 'edsk', '-format', 'ampro400s', image],
                            check=True, capture_output=True)
    (out / 'dskform.log').write_bytes(result.stdout + result.stderr)
    for name, length in [('SMALL.BIN', 128), ('SECTOR.BIN', 1152), ('EXTENT.BIN', 32896)]:
        payload = b''.join(sha256((name + ':' + str(i)).encode()).digest()
                           for i in range((length + 31) // 32))[:length]
        source = out / name
        source.write_bytes(payload)
        subprocess.run(['cpmcp', '-f', 'amp3', '-T', 'edsk', image, source, '0:' + name],
                       cwd=out, check=True)
    # Reorder the generated EDSK to the vendor formatter's SKW2 order.
    # This is a reconstruction from source, not observed physical media.
    fmt = select_fdf(HERE / 'CANDIDATE.FDF', 'AMP3')
    before = image.read_bytes()
    raw, orders, _ = decode(before, fmt, per_track=True)
    after = bytearray(before)
    for cylinder, order in enumerate(orders):
        start = 256 + cylinder * (256 + fmt.raw_track_bytes)
        for slot, sector in enumerate((1, 4, 2, 5, 3)):
            old = order.index(sector)
            after[start+24+8*slot:start+32+8*slot] = before[start+24+8*old:start+32+8*old]
            dest = start + 256 + slot * 1024
            src = start + 256 + old * 1024
            after[dest:dest+1024] = before[src:src+1024]
    assert decode(after, fmt)[0] == raw
    image.write_bytes(after)
    manifest = [dict(filename=image.name, format='AMP3', files=3,
                     sha256=sha256(after).hexdigest(),
                     fixture_origin='synthetic: libdsk ampro400s, deterministic payloads, vendor SKW2 order')]
    (out / 'samples.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(out / 'samples.json')


if __name__ == '__main__':
    main()
