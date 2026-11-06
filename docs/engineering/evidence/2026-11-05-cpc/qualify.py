"""Check pinned Amstrad EDSKs against BetterCP/M on disposable media."""
from argparse import ArgumentParser
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE.parent / '2026-11-03-release-formats'))
from verify import diskdef
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as build_boot_dmk
from convert_fdf_image import raw_to_dmk, dmk_to_raw, _make_track, TRACK_LENGTH
from fdf_format import select_fdf
from fdf_v1 import parse, serialize, read_fdb
from test_z80pack_sysgen_install import session
from trs80gp_launch import run as run_trs80gp

SUPPLEMENT = ROOT / 'metadata/supplemental/SUPPDISK.FDF'
RELEASE = ROOT / 'metadata/release-formats.fdf'


@contextmanager
def watch_model4(disks, *, interval=30, idle_limit=600):
    """On this POSIX runner, interrupt a stalled guest inside the emulator cleanup scope."""
    stamps = [disk.stat().st_mtime_ns for disk in disks]
    started = last_write = time.monotonic()

    def report(signum, frame):
        nonlocal last_write
        now = time.monotonic()
        changed = []
        for i, disk in enumerate(disks):
            stamp = disk.stat().st_mtime_ns
            if stamp != stamps[i]:
                changed.append('ABC'[i])
                stamps[i] = stamp
        if changed:
            last_write = now
            detail = 'writes on ' + ', '.join(changed)
        else:
            detail = f'{now-last_write:.0f}s since last observed disk write'
        print(f'  {time.strftime("%Y-%m-%d %H:%M:%S %Z")} '
              f'{disks[0].parent.name}: {int(now-started)//60}m awake, {detail}', flush=True)
        if now - last_write >= idle_limit:
            raise TimeoutError(f'No disk writes for {idle_limit}s; private DMKs remain in {disks[0].parent}')

    old_handler = signal.signal(signal.SIGALRM, report)
    signal.setitimer(signal.ITIMER_REAL, interval, interval)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def digest(data):
    return sha256(data).hexdigest()


def cpm(work, tool, fmt, image, *args, driver='raw', flags=()):
    result = subprocess.run([tool, *flags, '-f', fmt, '-T', driver, image, *args],
                            cwd=work, stdout=subprocess.PIPE, check=True)
    return result.stdout.decode()


def files(work, fmt, image, driver='raw'):
    names = cpm(work, 'cpmls', fmt, image, driver=driver).split()
    assert names and names[0] == '0:' and not any(n.endswith(':') for n in names[1:]), names
    payloads = {}
    for name in names[1:]:
        exported = work / 'export'
        exported.unlink(missing_ok=True)
        cpm(work, 'cpmcp', fmt, image, '0:' + name, exported, driver=driver)
        payloads[name] = exported.read_bytes()
    return payloads


def decode(image, fmt, *, per_track=False):
    """Read CHRN metadata before discarding the EDSK wrapper."""
    assert image.startswith(b'EXTENDED CPC DSK File') and image[49] == 1
    count = image[48]
    sizes = [n * 256 for n in image[52:52+count]]
    assert len(sizes) == count and sum(sizes) + 256 == len(image)
    assert sizes[:fmt.cylinders] == [256 + fmt.raw_track_bytes] * fmt.cylinders
    assert not any(sizes[fmt.cylinders:]), 'formatted cylinders beyond the definition'
    pos, raw, orders = 256, bytearray(), []
    offsets = []
    for cyl in range(fmt.cylinders):
        track = image[pos:pos+sizes[cyl]]
        pos += sizes[cyl]
        assert track.startswith(b'Track-Info') and track[16:18] == bytes([cyl, 0])
        assert track[20:22] == bytes([fmt.size_code, fmt.physical_sectors])
        sectors = {}
        starts = {}
        for i in range(fmt.physical_sectors):
            start = 24 + 8*i
            c, h, r, n, st1, st2, lo, hi = track[start:start+8]
            assert (c, h, n, st1, st2, lo + 256*hi) == (cyl, 0, fmt.size_code, 0, 0, fmt.sector_bytes)
            assert r not in sectors
            data_at = 256 + i*fmt.sector_bytes
            sectors[r] = track[data_at:data_at+fmt.sector_bytes]
            starts[r] = pos - sizes[cyl] + data_at
        orders.append(tuple(sectors))
        assert sorted(sectors) == list(fmt.sector_ids)
        raw.extend(b''.join(sectors[r] for r in sorted(sectors)))
        offsets.extend(starts[r] for r in sorted(starts))
    if per_track:
        return bytes(raw), orders, offsets
    assert len(set(orders)) == 1, 'image has varying rotational order'
    return bytes(raw), orders[0], offsets


def source_dmk(raw, fmt, orders):
    """Preserve the independently sourced sector order on every track."""
    image = bytearray(raw_to_dmk(raw, fmt))
    for cylinder, order in enumerate(orders):
        start = cylinder * fmt.raw_track_bytes
        track = _make_track(replace(fmt, sector_ids=order), cylinder, 0,
                            raw[start:start + fmt.raw_track_bytes])
        at = 16 + cylinder * TRACK_LENGTH
        image[at:at + TRACK_LENGTH] = track
    assert dmk_to_raw(image, fmt) == raw
    return bytes(image)


def run_sample(args, spec, work, formats):
    work.mkdir()
    stock = work / 'stock'
    stock.mkdir()  # cpmtools reads its installed diskdefs here
    if args.diskdefs:
        shutil.copyfile(args.diskdefs, stock / 'diskdefs')
    ident = spec['format']
    fmt = select_fdf(args.catalogue, ident)
    desc = formats[ident].description
    path = args.images / spec['filename']
    if path.exists():
        image = path.read_bytes()
    else:
        image = urlopen(spec['url'], timeout=60).read()
        if 'archive_member' in spec:
            assert digest(image) == spec['archive_sha256'], 'downloaded archive hash'
            image = subprocess.run(
                ['tar', '-xOf', '-', spec['archive_member']], input=image,
                stdout=subprocess.PIPE, check=True).stdout
    assert digest(image) == spec['sha256'], path
    if not path.exists():
        path.write_bytes(image)
    original, orders, offsets = decode(image, fmt, per_track=True)
    expected = files(stock, ident.lower(), path, 'edsk')
    assert len(expected) == spec['files']
    used, total = map(int, re.search(r'(\d+)/(\d+) blocks',
        cpm(stock, 'fsck.cpm', ident.lower(), path, driver='edsk', flags=['-n'])).groups())
    assert total == fmt.dsm + 1
    probe = b''.join(sha256(i.to_bytes(4, 'little')).digest()*4
                     for i in range((total-used)*fmt.block_bytes//128))
    (work / 'probe').write_bytes(probe)
    scratch_id = args.work_format if args.target == 'cpmsim' else 'MMI008'
    release = {f.ident: f for f in parse(RELEASE.read_text())}
    (work / 'diskdefs').write_text(diskdef(release[scratch_id]))
    scratch_fmt = select_fdf(RELEASE, scratch_id)
    scratch = work / 'scratch.raw'
    scratch.write_bytes(bytes([0xe5]) * scratch_fmt.image_bytes)
    cpm(work, 'cpmcp', scratch_id, scratch, work/'probe', '0:PROBE.BIN')
    candidate = work / 'cpc.raw'
    candidate.write_bytes(original)
    # Check the host view again after normalizing by ID.
    assert files(stock, ident.lower(), candidate) == expected

    boot = work / 'boot.raw'
    model4 = args.target != 'cpmsim'
    if model4:
        boot.write_bytes(extract_raw(args.system.read_bytes()))
        # extract_raw returns logical sector order for this boot layout.
        with (work/'diskdefs').open('a') as defs:
            defs.write('diskdef boot\n libdsk:format pcw800\n seclen 512\n tracks 160\n'
                       ' sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
        boot_fmt = 'boot'
    else:
        shutil.copyfile(args.system, boot)
        boot_fmt = 'MMF017'
    # CONFIG searches the current drive first. Keep the production catalogue on A:.
    cpm(work, 'cpmcp', scratch_id, scratch, args.catalogue.with_suffix('.FDB'), '0:DISK.FDB')
    src, dst, back = ('C', 'B', 'B') if model4 else ('B', 'C', 'D')
    commands = [f'{dst}:', f'A:CONFIG /LOGICAL={src} /PHYSICAL={2 if model4 else 1} /FORMAT="{desc}"', 'A:',
                f'DIR {src}:', f'COPY {src}:*.* {dst}:',
                f'COPY {dst}:PROBE.BIN {src}:FILL.BIN', f'COPY {src}:FILL.BIN {back}:RETURN.BIN']
    setup = []
    if not model4 and fmt.cylinders > 40:
        setup.append(f'A:CONFIG /PHYSICAL=1 /TRACKS={fmt.cylinders} /SIDES={fmt.sides} /STEP=6')
    if not model4 and scratch_id != 'MMF017':
        for letter, physical in [('C', 2), ('D', 3)]:
            setup.extend([
                f'A:CONFIG /PHYSICAL={physical} /TRACKS={scratch_fmt.cylinders} /SIDES={scratch_fmt.sides} /STEP=6',
                f'A:CONFIG /LOGICAL={letter} /PHYSICAL={physical} /FORMAT="{release[scratch_id].description}"'])
    if setup:
        commands = setup + commands
    if model4:
        commands = ['RSX LOAD M4SCRN', 'RSX LOAD ADM3A', 'CLS', *commands, 'TYPE CPCEND.TXT']
        (work/'startup').write_bytes(('\r\n'.join(commands)+'\r\n\x1a').encode())
        (work/'marker').write_bytes(b'CPC batch ended\r\n\x1a')
        cpm(work, 'cpmrm', boot_fmt, boot, '0:STARTUP.SUB')
        for name, local in [('STARTUP.SUB', 'startup'), ('CPCEND.TXT', 'marker')]:
            cpm(work, 'cpmcp', boot_fmt, boot, work/local, '0:'+name)
        drive0, drive1, drive2 = [work/f'drive{i}.dmk' for i in range(3)]
        drive0.write_bytes(build_boot_dmk(boot.read_bytes()))
        assert extract_raw(drive0.read_bytes()) == boot.read_bytes()
        drive1.write_bytes(raw_to_dmk(scratch.read_bytes(), scratch_fmt))
        drive2.write_bytes(source_dmk(original, fmt, orders))
        assert dmk_to_raw(drive2.read_bytes(), fmt) == original
        if args.target == 'prepare-model4':
            return {'status': 'prepared', 'guest_commands': commands}
        print(f"Running {spec['filename']}: {len(expected)} original files, "
              f"{len(probe)//1024} KiB to write and read back.", flush=True)
        with watch_model4((drive0, drive1, drive2)):
            run_trs80gp([args.simulator, '-m4', '-batch', '-turbo', '-na', '-d0', drive0,
                         '-d1', drive1, '-d2', drive2, '-itime', '0',
                         '-iw', 'CPC batch ended', '-id', '500', '-it', '-ix'],
                        cwd=work, timeout=24*60*60)
        candidate.write_bytes(dmk_to_raw(drive2.read_bytes(), fmt))
        scratch.write_bytes(dmk_to_raw(drive1.read_bytes(), scratch_fmt))
        returned = scratch
    else:
        disks = work / 'disks'
        disks.mkdir()
        returned = disks/'drived.dsk'
        returned.write_bytes(bytes([0xe5])*scratch_fmt.image_bytes)
        for letter, disk in zip('abc', (boot, candidate, scratch)):
            disk.rename(disks/f'drive{letter}.dsk')
        candidate, scratch = disks/'driveb.dsk', disks/'drivec.dsk'
        steps = [(s.encode()+b'\r', (dst if len(setup) <= i < len(setup)+2 else 'A').encode()+b'0>_ ', 60)
                 for i, s in enumerate(commands)]
        trace = session(args.simulator, disks, steps
                        + [(b'BYE /Y\r', b'System halted', 20)], work/'console.bin')
        assert trace.count(b'Disk configuration changed') == len(setup) + 1
    copied = files(work, scratch_id, scratch)
    roundtrip = copied if model4 else files(work, scratch_id, returned)
    for name, data in expected.items():
        assert copied[name] == data, name
    assert roundtrip['return.bin'] == probe
    assert files(stock, ident.lower(), candidate) == {**expected, 'fill.bin': probe}
    after = candidate.read_bytes()
    start = fmt.off * fmt.spt * 128
    assert len(after) == len(original) and after[:start] == original[:start]
    allocation_end = start + (fmt.dsm + 1) * fmt.block_bytes
    assert after[allocation_end:] == original[allocation_end:]
    entries = [after[i:i+32] for i in range(start, start + 32*(fmt.drm+1), 32)]
    assert any(e[:12] == b'\0FILL    BIN' and fmt.dsm in e[16:32] for e in entries)
    assert f'{total}/{total} blocks' in cpm(stock, 'fsck.cpm', ident.lower(), candidate, flags=['-n'])
    # Reinsert guest-written sectors into a copy with the original headers and interleave.
    repacked = bytearray(image)
    for i, dest in enumerate(offsets):
        start_in_raw = i * fmt.sector_bytes
        repacked[dest:dest+fmt.sector_bytes] = after[start_in_raw:start_in_raw+fmt.sector_bytes]
    edsk = work / 'written.dsk'
    edsk.write_bytes(repacked)
    assert files(stock, ident.lower(), edsk, 'edsk') == {**expected, 'fill.bin': probe}
    assert digest(path.read_bytes()) == spec['sha256']
    rotation = ({'rotation': list(orders[0])} if len(set(orders)) == 1
                else {'rotation_by_track': [list(order) for order in orders]})
    return dict(status='pass', raw_sha256=digest(original), formatted_cylinders=fmt.cylinders,
                **rotation, original_files={n:digest(v) for n,v in expected.items()},
                fill_bytes=len(probe), fill_sha256=digest(probe), highest_block_written=fmt.dsm,
                written_edsk_sha256=digest(repacked),
                reserved_bytes_preserved=start, guest_commands=commands)


def qualify_sample(args, spec, formats):
    work = args.output / Path(spec['filename']).stem
    result = run_sample(args, spec, work, formats)
    if 'fixture_origin' in spec:
        result['fixture_origin'] = spec['fixture_origin']
    (work/'sample-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(spec['filename'], result['status'], flush=True)
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['cpmsim','trs80gp','prepare-model4'], required=True)
    parser.add_argument('--system', type=Path, required=True, help='BetterCP/M System image for this target')
    parser.add_argument('--simulator', type=Path, help='patched cpmsim or trs80gp executable')
    parser.add_argument('--images', type=Path, required=True, help='cache for SHA-pinned image fixtures')
    parser.add_argument('--output', type=Path, required=True, help='new directory for disposable media and results')
    parser.add_argument('--manifest', type=Path, default=HERE/'samples.json',
                        help='pinned image manifest, defaults to the original CPC set')
    parser.add_argument('--catalogue', type=Path, default=SUPPLEMENT,
                        help='FDF catalogue with a matching compiled .FDB')
    parser.add_argument('--diskdefs', type=Path,
                        help='independent cpmtools diskdefs for source-image reads')
    parser.add_argument('--work-format', default='MMF017',
                        help='release-catalogue format for cpmsim work and return disks')
    parser.add_argument('--jobs', type=int, default=1,
                        help='independent guest processes to run concurrently')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if not __debug__ or (args.target != 'prepare-model4' and not args.simulator):
        parser.error('run without -O and supply --simulator for guest execution')
    args.system = args.system.resolve(strict=True)
    if args.simulator:
        args.simulator = args.simulator.resolve(strict=True)
    args.images = args.images.resolve()
    args.images.mkdir(parents=True, exist_ok=True)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    args.catalogue = args.catalogue.resolve(strict=True)
    if args.diskdefs:
        args.diskdefs = args.diskdefs.resolve(strict=True)
    database = args.catalogue.with_suffix('.FDB')
    formats = parse(args.catalogue.read_text())
    assert serialize(formats) == database.read_bytes()
    assert tuple(d.format for d in read_fdb(database.read_bytes()).descriptors) == formats
    report = dict(target=args.target, fdb_sha256=digest(database.read_bytes()),
                  system_sha256=digest(args.system.read_bytes()), samples={})
    if args.diskdefs:
        report['diskdefs_sha256'] = digest(args.diskdefs.read_bytes())
    if args.simulator:
        report['emulator_sha256'] = digest(args.simulator.read_bytes())
    by_id = {f.ident:f for f in formats}
    samples = json.loads(args.manifest.read_text())
    stems = [Path(spec['filename']).stem for spec in samples]
    if not samples or len(set(stems)) != len(stems):
        parser.error('manifest must contain images with distinct filename stems')
    for spec in samples:
        if Path(spec['filename']).name != spec['filename']:
            parser.error('image filenames must be plain basenames')
    with ProcessPoolExecutor(max_workers=args.jobs) as workers:
        futures = [workers.submit(qualify_sample, args, spec, by_id) for spec in samples]
        for spec, future in zip(samples, futures):
            report['samples'][spec['filename']] = future.result()
    (args.output/'results.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
