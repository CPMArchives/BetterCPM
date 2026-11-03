"""Read the candidate ZIP disks using only the independently authored definitions."""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from convert_fdf_image import dmk_to_raw
from fdf_format import FDFFormat
from fdf_v1 import parse, serialize, read_fdb


def digest(data):
    return sha256(data).hexdigest()


def surface(f):
    # The DMK decoder operates on one surface at a time, even for a
    # filesystem whose logical track spans both heads.
    return FDFFormat(f.ident, f.psectors*f.secsize//128, f.bsh, f.blm,
                     f.exm, f.dsm, f.drm, f.al0, f.al1, f.cks, f.off,
                     f.psectors, {256: 1, 512: 2}[f.secsize], f.cylinders,
                     0xC0, f.sector_ids)


def diskdef(f):
    reserved_bytes = f.off * f.spt * 128
    skip, remainder = divmod(reserved_bytes, f.psectors * f.secsize)
    assert remainder == 0
    raw_hint = ' libdsk:format pcw800\n' if f.secsize == 512 else ''
    return (f'diskdef {f.ident}\n{raw_hint} seclen {f.secsize}\n tracks {f.cylinders*f.sides}\n'
            f' sectrk {f.psectors}\n blocksize {128 << f.bsh}\n maxdir {f.drm+1}\n'
            ' skewtab ' + ','.join(str(i-1) for i in f.sector_ids)
            + f'\n boottrk {skip}\n os 2.2\nend\n')


def cpm(folder, command, ident, *args, check=True):
    return subprocess.run([command, '-f', ident, '-T', 'raw', *args], cwd=folder,
                          check=check, capture_output=True)


def verify(folder, candidates):
    defs = (HERE/'review.fdf').read_text()
    formats = {f.ident: f for f in parse(defs)}
    fdb = serialize(tuple(formats.values()))
    assert [d.format for d in read_fdb(fdb).descriptors] == list(formats.values())
    (folder/'diskdefs').write_text(''.join(map(diskdef, formats.values())))
    out = {'definitions_sha256': digest(defs.encode()), 'review_fdb_sha256': digest(fdb),
           'media': [], 'catalogue_comparison': {}, 'full_volume_probes': {}}
    index = json.loads((candidates/'BetterCPM-1.0-CANDIDATE.json').read_text())
    out['tested_source_commit'] = index['source_commit']
    for asset in index['assets']:
        name = asset['filename']
        if 'System-' not in name and 'Utilities-' not in name:
            continue
        path = candidates/name
        assert digest(path.read_bytes()) == asset['sha256']
        with zipfile.ZipFile(path) as archive:
            release = json.loads(archive.read(next(n for n in archive.namelist()
                                 if n.count('/') == 1 and n.endswith('/RELEASE.json'))))
            assert release['source_commit'] == index['source_commit']
            evidence = release['evidence']
            for member in archive.namelist():
                if '/images/' not in member or not member.endswith(('.dmk', '.dsk')):
                    continue
                filename = Path(member).name
                data = archive.read(member)
                system = evidence.get('system', {})
                report = system if filename == system.get('image') else evidence.get('images', {}).get(filename)
                expected = report['included'] if report else []
                want = report['sha256'] if report else system['work_image_sha256']
                assert digest(data) == want
                model4 = member.endswith('.dmk')
                ident = ('BCPM780' if filename == system.get('image') else 'MMI008') if model4 else 'MMF017'
                f = formats[ident]
                raw = dmk_to_raw(data, surface(f)) if model4 else data
                assert len(raw) == f.cylinders * f.sides * f.psectors * f.secsize
                (folder/'disk').write_bytes(raw)
                filelist = cpm(folder, 'cpmls', ident, 'disk').stdout.decode().split()
                assert set(filelist) == ({'0:'} if expected else set()) | {r['name'].lower() for r in expected}, filename
                for r in expected:
                    (folder/'payload').unlink(missing_ok=True)
                    cpm(folder, 'cpmcp', ident, 'disk', '0:'+r['name'], 'payload')
                    actual = (folder/'payload').read_bytes()
                    assert len(actual) in (r['bytes'], (r['bytes']+127)//128*128), (filename,r['name'],len(actual),r['bytes'])
                    assert set(actual[r['bytes']:]) <= {0, 26}
                    assert digest(actual[:r['bytes']]) == r['sha256'], (filename, r['name'],digest(actual[:r['bytes']]))
                    if r['name'] == 'DISK.FDB':
                        # Post-check only. The historical FDB is never a constructor input.
                        stored = {d.ident: d.format for d in read_fdb(actual[:r['bytes']]).descriptors}
                        compared = []
                        for key in ('MMF017', 'MMI012', 'MMI008'):
                            proposed = formats[key]
                            assert replace(proposed, description=stored[key].description) == stored[key]
                            compared.append(key)
                        out['catalogue_comparison'][filename] = compared
                check = cpm(folder, 'fsck.cpm', ident, '-n', 'disk').stdout.decode().splitlines()[-1]
                row = dict(image=filename, sha256=want, definition=ident,
                           files_verified=len(expected), filesystem=check)
                if ident == 'BCPM780':
                    control = cpm(folder, 'cpmls', 'MMI012', 'disk', check=False)
                    assert b'readme.txt' not in control.stdout.lower().split()
                    row['historical_MMI012_recovers_expected_directory'] = False
                out['media'].append(row)
    assert len(out['media']) == 8
    for f in formats.values():
        size = f.cylinders * f.sides * f.secsize * f.psectors
        blank = b'\xe5'*size
        reserved = f.off*f.spt*128
        blocksize = 128 << f.bsh
        available = (f.dsm+1)*blocksize - (f.drm+1)*32
        # Distinct records expose aliasing at extent, track and final-block boundaries.
        probe = b''.join(sha256(i.to_bytes(4, 'little')).digest()*4 for i in range(available//128))
        (folder/'probe').write_bytes(probe)
        (folder/'disk').write_bytes(blank)
        cpm(folder, 'cpmcp', f.ident, 'disk', 'probe', '0:PROBE.BIN')
        (folder/'export').unlink(missing_ok=True)
        cpm(folder, 'cpmcp', f.ident, 'disk', '0:PROBE.BIN', 'export')
        assert (folder/'export').read_bytes() == probe
        assert (folder/'disk').read_bytes()[:reserved] == blank[:reserved]
        line = cpm(folder, 'fsck.cpm', f.ident, '-n', 'disk').stdout.decode().splitlines()[-1]
        assert f'{f.dsm+1}/{f.dsm+1} blocks' in line, line
        out['full_volume_probes'][f.ident] = dict(file_bytes=len(probe), sha256=digest(probe), fsck=line)
    return out


if __name__ == '__main__':
    if not __debug__:
        sys.exit('Run without -O so verification assertions are active.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as work:
        print(json.dumps(verify(Path(work), args.candidates.resolve()), indent=2))
