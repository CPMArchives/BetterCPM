"""Inventory pinned Ampro downloads without treating other geometries as AMP3."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent


def inspect(name, data):
    pos = data.index(b'\x1a') + 1
    tracks, payloads, marks = [], {}, Counter()
    while pos < len(data):
        mode, cyl, head, count, size = data[pos:pos+5]
        pos += 5
        assert mode <= 5 and size <= 6 and 0 < count <= 64
        ids = list(data[pos:pos+count])
        pos += count
        cylinders = list(data[pos:pos+count]) if head & 128 else [cyl] * count
        if head & 128:
            pos += count
        heads = list(data[pos:pos+count]) if head & 64 else [head & 1] * count
        if head & 64:
            pos += count
        assert cylinders == [cyl] * count and heads == [head & 1] * count
        assert len(set(ids)) == count
        for sector in ids:
            mark = data[pos]
            pos += 1
            marks[mark] += 1
            assert mark in (1, 2), 'unavailable, deleted, or error-marked sector'
            length = 128 << size
            payload = data[pos:pos+length] if mark == 1 else data[pos:pos+1] * length
            pos += length if mark == 1 else 1
            assert len(payload) == length
            key = (cyl, head & 1, sector)
            assert key not in payloads
            payloads[key] = payload
        tracks.append((cyl, head & 1, mode, 128 << size, tuple(ids)))
    assert pos == len(data)
    record = dict(name=name, bytes=len(data), sha256=sha256(data).hexdigest(),
                  standard_imd_signature=data.startswith(b'IMD '),
                  cylinders=len({t[0] for t in tracks}), heads=sorted({t[1] for t in tracks}),
                  track_count=len(tracks), modes=sorted({t[2] for t in tracks}),
                  sector_sizes=sorted({t[3] for t in tracks}),
                  sector_counts=sorted({len(t[4]) for t in tracks}),
                  sector_orders=sorted({t[4] for t in tracks}), record_types=dict(marks))
    return record, b''.join(payloads[k] for k in sorted(payloads))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new report directory')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    for source in json.loads((HERE / 'sources.json').read_text()):
        assert sha256((args.images / source['filename']).read_bytes()).hexdigest() == source['sha256']
    inventory, source_checks = [], []
    with zipfile.ZipFile(args.images / 'Ampro_LBZ80-CPM.ZIP') as archive:
        for outer in archive.namelist():
            if not outer.lower().endswith('.zip'):
                continue
            with zipfile.ZipFile(io.BytesIO(archive.read(outer))) as sub:
                for name in sub.namelist():
                    if not name.endswith('.IMD'):
                        continue
                    record, raw = inspect(outer + '/' + name, sub.read(name))
                    assert raw == sub.read(name[:-4] + '.RAW')
                    record['decoded_raw_matches_archived_imdu_conversion'] = True
                    inventory.append(record)
                    (args.output / 'source.raw').write_bytes(raw)
                for name in ('bios-1-6.asm', 'bios-3-8.asm', 'ad-3-3.asm'):
                    if name not in sub.namelist():
                        continue
                    exported = args.output / name
                    subprocess.run(['cpmcp', '-f', 'amp2', '-T', 'raw',
                                    args.output / 'source.raw', '0:' + name, exported],
                                   cwd=args.output, check=True)
                    assert exported.read_bytes() == sub.read(name)
                    source_checks.append(dict(member=outer + '/' + name,
                        sha256=sha256(exported.read_bytes()).hexdigest(),
                        cpmtools_extraction_matches_archive_file=True))
    for name in ('LBSYS-F.IMD', 'DM718.IMD'):
        inventory.append(inspect(name, (args.images / name).read_bytes())[0])
    for name, value in [('image-survey.json', inventory), ('source-checks.json', source_checks)]:
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n')
    print('All seven image geometries inspected; five archived IMDU conversions match; three source files verified.')


if __name__ == '__main__':
    main()
