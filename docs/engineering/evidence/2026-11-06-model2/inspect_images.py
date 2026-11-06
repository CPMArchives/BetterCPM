"""Inspect original Model II IMDs and test host writes on bounded private copies.

This is a host layout experiment, not BetterCP/M guest qualification.
Requires the POSIX (not libdsk) cpmtools backend because offset 11520 is not
divisible by 1024. All file data are checked by a separate Python CP/M reader.
"""
from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ORDER = (1, 4, 7, 2, 5, 8, 3, 6)
PREFIX = 11520


def digest(data):
    return sha256(data).hexdigest()


def decode(data):
    assert data.startswith(b'IMD ')
    pos = data.index(b'\x1a') + 1
    comment = data[:pos]
    tracks, problems = [], []
    while pos < len(data):
        start = pos
        mode, cyl, head, count, size = data[pos:pos+5]
        pos += 5
        assert mode <= 5 and size <= 6 and 0 < count <= 64
        ids = list(data[pos:pos+count]); pos += count
        cylinders = list(data[pos:pos+count]) if head & 128 else [cyl] * count
        if head & 128:
            pos += count
        heads = list(data[pos:pos+count]) if head & 64 else [head & 1] * count
        if head & 64:
            pos += count
        header = data[start:pos]
        sectors = []
        for ident, recorded_c, recorded_h in zip(ids, cylinders, heads):
            mark = data[pos]; pos += 1
            assert 0 <= mark <= 8
            length = 128 << size
            payload = None if mark == 0 else (data[pos:pos+length] if mark & 1 else data[pos:pos+1] * length)
            pos += 0 if mark == 0 else (length if mark & 1 else 1)
            if payload is not None:
                assert len(payload) == length
            if mark not in (1, 2) or recorded_c != cyl or recorded_h != (head & 1):
                problems.append(dict(cylinder=cyl, head=head & 1, sector=ident,
                                     recorded_cylinder=recorded_c, recorded_head=recorded_h, record_type=mark))
            sectors.append(dict(id=ident, mark=mark, payload=payload))
        if len(set(ids)) != count:
            problems.append(dict(cylinder=cyl, head=head & 1, duplicate_sector_ids=ids))
        tracks.append(dict(cylinder=cyl, head=head & 1, mode=mode, size=128 << size,
                           ids=ids, header=header, sectors=sectors))
    assert pos == len(data)
    return comment, tracks, problems


def raw_image(tracks):
    return b''.join(s['payload'] for t in sorted(tracks, key=lambda t: (t['cylinder'], t['head']))
                    for s in sorted(t['sectors'], key=lambda s: s['id']))


def repack(comment, tracks, raw):
    payloads, offset = {}, 0
    for t in sorted(tracks, key=lambda t: (t['cylinder'], t['head'])):
        for s in sorted(t['sectors'], key=lambda s: s['id']):
            payloads[t['cylinder'], t['head'], s['id']] = raw[offset:offset+t['size']]
            offset += t['size']
    assert offset == len(raw)
    output = bytearray(comment)
    for t in tracks:
        output.extend(t['header'])
        for s in t['sectors']:
            payload = payloads[t['cylinder'], t['head'], s['id']]
            output.extend(b'\x02' + payload[:1] if len(set(payload)) == 1 else b'\x01' + payload)
    return bytes(output)


def logical_data(raw):
    data = raw[PREFIX:]
    assert len(data) % 8192 == 0
    return b''.join(data[t+i*1024:t+(i+1)*1024]
                    for t in range(0, len(data), 8192) for i in (r-1 for r in ORDER))


def read_files(raw, dsm, maxdir):
    data = logical_data(raw)
    assert len(data) == (dsm+1)*2048
    files, blocks, extent_count = {}, set(range(maxdir*32//2048)), 0
    for pos in range(0, maxdir*32, 32):
        e = data[pos:pos+32]
        if e[0] == 0xe5:
            continue
        assert e[0] < 16, ('unsupported directory entry', e.hex())
        stem = bytes(c & 127 for c in e[1:9]).decode('ascii').rstrip()
        suffix = bytes(c & 127 for c in e[9:12]).decode('ascii').rstrip()
        name = str(e[0]) + ':' + (stem + ('.' + suffix if suffix else '')).lower()
        extent = (e[12] & 31) + (e[14] << 5)
        assert e[15] <= 128
        allocation = [int.from_bytes(e[i:i+2], 'little') for i in range(16, 32, 2)]
        used = [b for b in allocation if b]
        assert all(b <= dsm and b not in blocks for b in used)
        blocks.update(used)
        payload = b''.join(data[b*2048:(b+1)*2048] for b in used)[:e[15]*128]
        assert len(payload) == e[15]*128
        parts = files.setdefault(name, {})
        assert extent not in parts
        parts[extent] = payload
        extent_count += 1
    for name, parts in list(files.items()):
        assert sorted(parts) == list(range(len(parts)))
        files[name] = b''.join(parts[i] for i in range(len(parts)))
    return files, blocks, extent_count


def run_one(spec, images, output, cpmtools):
    original = (images / spec['filename']).read_bytes()
    assert digest(original) == spec['sha256']
    comment, tracks, problems = decode(original)
    record = dict(filename=spec['filename'], sha256=digest(original),
                  track_count=len(tracks), problems=problems,
                  track_layouts=[dict(cylinder=t['cylinder'], head=t['head'], mode=t['mode'],
                      sector_bytes=t['size'], sector_ids=t['ids']) for t in tracks],
                  record_types=dict(Counter(s['mark'] for t in tracks for s in t['sectors'])))
    if problems:
        record['status'] = 'rejected before host I/O; original retained unchanged'
        return record
    raw = raw_image(tracks)
    double = len(tracks) == 154
    assert sorted((t['cylinder'], t['head']) for t in tracks) == [
        (c, h) for c in range(77) for h in range(2 if double else 1)]
    dsm, maxdir = (607, 192) if double else (299, 128)
    assert len(raw) == PREFIX + (dsm+1)*2048
    assert tracks[0]['mode'] == 0 and tracks[0]['size'] == 128 and set(tracks[0]['ids']) == set(range(1,27))
    for t in tracks[1:]:
        assert t['mode'] == 3 and t['size'] == 1024 and set(t['ids']) == set(range(1,9))
    dpb = bytes((64,0,4,15,0)) + dsm.to_bytes(2,'little') + (maxdir-1).to_bytes(2,'little')
    dpb += bytes((0xe0 if double else 0xc0,0)) + (maxdir//4).to_bytes(2,'little') + b'\x02\x00'
    positions = [i for i in range(len(raw)) if raw.startswith(dpb, i)]
    assert positions, 'expected OEM DPB absent'
    files, used, extents = read_files(raw, dsm, maxdir)
    work = output / Path(spec['filename']).stem
    work.mkdir()
    shutil.copyfile(HERE / 'diskdefs', work / 'diskdefs')
    target = work / 'working.raw'
    target.write_bytes(raw)
    fmt = 'm2ds' if double else 'm2ss'
    def tool(name, args):
        result = subprocess.run([str(cpmtools/name)] + args, cwd=work, text=True, capture_output=True)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        return result.stdout
    before_check = tool('fsck.cpm', ['-f', fmt, '-n', str(target)])
    def independent_extract(expected):
        for name, payload in expected.items():
            dest = work / 'extracted.bin'
            tool('cpmcp', ['-f', fmt, str(target), name, str(dest)])
            assert dest.read_bytes() == payload, name
    independent_extract(files)
    free = set(range(dsm+1)) - used
    assert dsm in free and (len(free)+7)//8 <= maxdir-extents
    # Position-varying bytes catch displaced/reordered blocks and sectors.
    probe = b''.join(sha256(b'Model II host probe' + i.to_bytes(4,'little')).digest()
                     for i in range(len(free)*2048//32))
    (work / 'probe.bin').write_bytes(probe)
    tool('cpmcp', ['-f', fmt, str(target), str(work/'probe.bin'), '0:m2probe.bin'])
    written = target.read_bytes()
    assert len(written) == len(raw) and written[:PREFIX] == raw[:PREFIX]
    old_directory, new_directory = logical_data(raw), logical_data(written)
    for pos in range(0, maxdir*32, 32):
        if old_directory[pos] != 0xe5:
            assert new_directory[pos:pos+32] == old_directory[pos:pos+32]
    after, allocated, _ = read_files(written, dsm, maxdir)
    assert allocated == set(range(dsm+1))
    assert after.pop('0:m2probe.bin') == probe and after == files
    independent_extract(dict(files, **{'0:m2probe.bin': probe}))
    after_check = tool('fsck.cpm', ['-f', fmt, '-n', str(target)])
    packed = repack(comment, tracks, written)
    new_comment, new_tracks, errors = decode(packed)
    assert not errors and new_comment == comment
    assert [t['header'] for t in new_tracks] == [t['header'] for t in tracks]
    assert raw_image(new_tracks) == written
    (work / 'written.imd').write_bytes(packed)
    assert digest((images/spec['filename']).read_bytes()) == spec['sha256']
    record.update(status='host-only pass; BetterCP/M guest untested', raw_bytes=len(raw),
                  original_files=len(files), original_file_bytes=sum(map(len,files.values())),
                  original_files_sha256={n:digest(v) for n,v in sorted(files.items())},
                  dpb_hex=dpb.hex(), dpb_raw_offsets=positions, dsm=dsm, maxdir=maxdir,
                  logical_sector_order=list(ORDER), probe_bytes=len(probe),
                  highest_block_written=dsm, reserved_bytes_preserved=PREFIX,
                  image_length_preserved=True, imd_headers_and_sector_order_preserved=True,
                  original_directory_entries_preserved=True,
                  original_image_unchanged=True, original_raw_sha256=digest(raw),
                  written_raw_sha256=digest(written), written_imd_sha256=digest(packed),
                  probe_sha256=digest(probe), fsck_before=before_check, fsck_after=after_check)
    return record


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpmtools', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    args.output = args.output.resolve(); args.output.mkdir(parents=True)
    sources = json.loads((HERE/'sources.json').read_text())
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(lambda s: run_one(s, args.images.resolve(), args.output,
                                                args.cpmtools.resolve()), sources['images']))
    result = dict(scope='host tools only; no BetterCP/M guest or physical-media qualification',
                  tools=sources['cpmtools'], jobs=args.jobs, samples=records)
    (args.output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    for r in records:
        print(r['filename'], r['status'], r.get('highest_block_written', ''))


if __name__ == '__main__':
    main()
