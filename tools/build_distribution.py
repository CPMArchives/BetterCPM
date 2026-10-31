#!/usr/bin/env python3
"""Build manifest-selected, independently boot-qualified distribution media."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from build_profiles import (CONTEXT_ENV, PROFILES, profile_inputs, read_context,
                            select_profile, workspace, write_context)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'metadata/distribution.json'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command, cwd, log=None, timeout=900, env=None):
    result = subprocess.run(list(map(str, command)), cwd=cwd, check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout, env=env)
    if log:
        Path(log).write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(f"build/tool failed: {command}; log: {log}\n"+result.stdout.decode(errors="replace")[-3000:])
    return result.stdout


def source_identity(profile=None):
    """Hash actual build inputs, not filesystem timestamps or prebuilt media."""
    files = {}
    for folder in ('src', 'tools', 'metadata', 'third_party'):
        for path in sorted((ROOT / folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                files[str(path.relative_to(ROOT))] = digest(path.read_bytes())
    revision = run(['git', 'rev-parse', 'HEAD'], ROOT).decode().strip()
    identity = {'revision': revision, 'inputs': files,
                'assembler_sha256': digest((Path.home() / 'bin/z80asm').read_bytes())}
    if profile:
        identity['profile'] = profile_inputs(profile, ROOT/'src/system/layout.inc')[0]
    return identity


def stage_sources(destination):
    for folder in ('src', 'tools', 'metadata', 'third_party'):
        shutil.copytree(ROOT / folder, destination / folder,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def prepare_profile(work, target, identity, profile, reuse=False):
    """Stage unchanged sources and generated inputs; never publish a disk."""
    root = workspace(work, target, profile)
    stamp = root/'profile-state.json'
    if identity.get('profile') != profile_inputs(profile, ROOT/'src/system/layout.inc')[0]:
        raise ValueError('profile preparation identity does not match requested profile')
    if reuse:
        state = json.loads(stamp.read_text())
        if state['source'] != identity:
            raise ValueError(f'{profile.name}: cached profile inputs differ; prepare without --reuse-work in a fresh --work')
        staged_inputs = {str(p.relative_to(root))
                         for folder in ('src', 'tools', 'metadata', 'third_party')
                         for p in (root/folder).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        if staged_inputs != set(identity['inputs']):
            raise ValueError(f'{profile.name}: cached source file set changed; prepare again')
        expected_artifacts = staged_inputs | {
            'build/profile/context.json', 'build/profile/layout.inc', 'build/profile/profile.inc'}
        if set(state['artifacts']) != expected_artifacts:
            raise ValueError(f'{profile.name}: incomplete cached profile input inventory')
        for name, expected in state['artifacts'].items():
            if digest((root/name).read_bytes()) != expected:
                raise ValueError(f'{profile.name}: cached profile input changed: {name}')
        read_context(root/'build/profile/context.json', root/'src/system/layout.inc')
        return root
    if root.exists():
        raise ValueError(f'{root} exists; select a fresh --work or use --reuse-work')
    root.mkdir(parents=True)
    stage_sources(root)
    write_context(profile, root/'src/system/layout.inc')
    artifacts = {str(p.relative_to(root)): digest(p.read_bytes())
                 for p in sorted(root.rglob('*')) if p.is_file()}
    stamp.write_text(json.dumps({'source': identity, 'artifacts': artifacts}, indent=2)+'\n')
    return root


def current_build(work, target, identity, reuse):
    if 'profile' in identity:
        raise ValueError('checked-profile disk generation awaits normal-build integration; use --prepare-profile')
    root = workspace(work, target)
    stamp = root / 'build-state.json'
    if reuse:
        state = json.loads(stamp.read_text())
        if state['source'] != identity:
            raise ValueError(f'{target}: cached build inputs differ; rebuild without --reuse-work')
        for name, expected in state['artifacts'].items():
            if digest((root / name).read_bytes()) != expected:
                raise ValueError(f'{target}: cached artifact changed: {name}')
        return root
    if root.exists():
        raise ValueError(f'{root} exists; select a fresh --work or use --reuse-work')
    root.mkdir(parents=True)
    stage_sources(root)
    # Break the existing clean-build metadata cycle without changing development builders.
    bootstrap = ("import sys;sys.path.insert(0,'tools');"
                 "from pathlib import Path;from build_trs80_boot import assemble,SOURCE,BUILD,BOOT_ADDRESS,STAGE1_ADDRESS;"
                 "a=Path.home()/'bin/z80asm';"
                 "assemble(a,SOURCE/'boot.mac',BUILD/'boot.bin',BOOT_ADDRESS);"
                 "assemble(a,SOURCE/'stage1.mac',BUILD/'stage1.bin',STAGE1_ADDRESS)")
    run([sys.executable, '-c', bootstrap], root, root/'bootstrap-build.log')
    run([sys.executable, 'tools/build_rsxselect.py'], root, root/'selector-build.log')
    # SYSBUILD utility metadata currently depends on the common system build.
    run([sys.executable, 'tools/build_complete_system.py'], root, root / 'common-build.log')
    if target == 'z80pack':
        run([sys.executable, 'tools/build_z80pack_image.py', '--system-tracks-only'], root, root / 'build.log')
    else:
        shutil.copy2(root / 'common-build.log', root / 'build.log')
    if target == 'z80pack':
        run([sys.executable, 'tools/build_z80pack_bye.py'], root, root/'exit-build.log')
    # Clock packages are explicit target components, not taken from disk files.
    builder = 'frehd_time_rsx' if target == 'trs80gp' else 'zprtc_rsx'
    run([sys.executable, f'tools/build_{builder}.py'], root, root / 'clock-build.log')
    artifacts = {str(p.relative_to(root)): digest(p.read_bytes())
                 for p in sorted((root / 'build').rglob('*')) if p.is_file()}
    stamp.write_text(json.dumps({'source': identity, 'artifacts': artifacts}, indent=2)+'\n')
    return root


def geometry(target, build_root):
    if target == 'z80pack':
        from fdf_format import select_fdf
        from build_z80pack_image import DEFAULT_FORMAT
        f = select_fdf(build_root / 'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
        return {'format': f.name, 'bytes': f.image_bytes,
                'reserved': f.reserved_records*128, 'block': f.block_bytes,
                'blocks': f.dsm+1, 'directory_blocks': f.directory_blocks,
                'entries': f.drm+1, 'definition': 'bettercpm-default'}
    from build_trs80_boot import (RAW_SIZE, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE,
                                 ALLOCATION_BLOCK_BYTES, BLOCK_COUNT,
                                 FIRST_DATA_BLOCK, DIRECTORY_ENTRIES)
    return {'format': 'MM Extended 80T DS SYSTEM (780K filesystem)',
            'bytes': RAW_SIZE, 'reserved': FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE,
            'block': ALLOCATION_BLOCK_BYTES, 'blocks': BLOCK_COUNT,
            'directory_blocks': FIRST_DATA_BLOCK, 'entries': DIRECTORY_ENTRIES,
            'definition': 'bettercpm-default'}


def stage_cpmsim_guest(simulator, root):
    """Stage the tool built alongside the selected emulator, outside OS caches."""
    source = Path(simulator).resolve().parent.parent/'cpmtools/mount.com'
    data = source.read_bytes()
    if not data:
        raise ValueError('empty cpmsim MOUNT.COM')
    destination = Path(root)/'staged-host-tools/MOUNT.COM'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def selected_files(manifest, target, root):
    selected, omitted = [], []
    for component in manifest['system_disk']:
        if target not in component['targets']:
            omitted.append({'name': component['name'], 'status': 'other target'})
        elif component['status'] == 'planned':
            omitted.append({'name': component['name'], 'status': 'planned',
                            'reason': component['reason']})
        elif component['status'] == 'implemented':
            path = root / component['artifact']
            content = path.read_bytes()  # Missing implemented artifacts fail.
            if not content:
                raise ValueError(f'empty implemented artifact: {path}')
            selected.append((component, content))
        else:
            raise ValueError(f'unknown status: {component}')
    keys = [(c['user'], c['name']) for c, _ in selected]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate manifest destination')
    if manifest.get('cold_start_command') == 'SUBMIT STARTUP':
        required = {(0, 'SUBMIT.COM'), (0, 'STARTUP.SUB')}
        if not required.issubset(set(keys)):
            raise ValueError('SUBMIT STARTUP requires SUBMIT.COM and STARTUP.SUB in user 0')
    return selected, omitted


def capacity(files, g):
    allocation = sum((len(data)+g['block']-1)//g['block'] for _, data in files)
    extents = sum(max(1, (len(data)+16383)//16384) for _, data in files)
    available = g['blocks']-g['directory_blocks']
    if allocation > available or extents > g['entries']:
        details = ', '.join(f"{c['name']}={len(data)}" for c, data in files)
        raise ValueError(f"distribution exceeds capacity: {allocation*g['block']} bytes required, "
                         f"{available*g['block']} available; {extents}/{g['entries']} directory entries; {details}")
    return {'allocated_bytes': allocation*g['block'],
            'available_bytes': available*g['block'],
            'free_bytes': (available-allocation)*g['block'], 'directory_entries': extents}


def construct(target, root, out, files, g, cold_start_command=""):
    """Reuse freshly assembled system tracks; recreate the filesystem from artifacts."""
    from startup_record import build as startup_record
    from system_layout import LAYOUT
    startup = startup_record(cold_start_command, system_base=LAYOUT['SYSTEM'])
    raw = out / 'system.raw'
    if target == 'z80pack':
        from fdf_format import select_fdf
        from build_z80pack_image import DEFAULT_FORMAT
        f = select_fdf(root / 'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
        source = (root / 'build/z80pack/disks/drivea.dsk').read_bytes()
        # Raw sector ordering is target-specific. Preserve only reserved records.
        image = bytearray(b'\xe5'*len(source))
        for record in range(f.reserved_records):
            track, within = divmod(record, f.spt)
            at = track*f.raw_track_bytes + f.raw_record_map()[within]*128
            image[at:at+128] = source[at:at+128]
        # BCST occupies logical records 1 and 2, which need not be adjacent
        # physical records in a skewed host image.
        for index in range(2):
            record = index + 1
            track, within = divmod(record, f.spt)
            at = track*f.raw_track_bytes + f.raw_record_map()[within]*128
            image[at:at+128] = startup[index*128:(index+1)*128]
        raw.write_bytes(image)
        shutil.copy2(root / 'build/z80pack/diskdefs', out / 'diskdefs')
    else:
        from add_cpm_file_to_dmk import extract_raw
        source = extract_raw((root / 'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk').read_bytes())
        image = bytearray(source[:g['reserved']]+b'\xe5'*(len(source)-g['reserved']))
        image[128:384] = startup
        raw.write_bytes(image)
        (out / 'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
    for i, (component, data) in enumerate(files):
        artifact = out / f'artifact-{i}'
        artifact.write_bytes(data)
        run(['cpmcp', '-f', g['definition'], raw, artifact,
             f"{component['user']}:{component['name']}"], out)
    return raw


def validate_config_fingerprint(target, raw, files, root):
    """CONFIG must contain the CRC/layout record for the installed resident carrier."""
    from config_validation import validation_record
    from system_layout import LAYOUT
    names = {c['name']: data for c, data in files if c['user'] == 0}
    if 'CONFIG.COM' not in names:
        return
    image = raw.read_bytes()
    if target == 'z80pack':
        from fdf_format import select_fdf
        from build_z80pack_image import DEFAULT_FORMAT
        f = select_fdf(root / 'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
        def record(n):
            track, within = divmod(n, f.spt)
            at = track*f.raw_track_bytes + f.raw_record_map()[within]*128
            return image[at:at+128]
        spt = f.spt
    else:
        def record(n):
            return image[n*128:(n+1)*128]
        spt = 80
    carrier = b''.join(record(n) for n in range(8, 60))
    expected = validation_record(carrier, LAYOUT['SYSTEM'], 52, 8, spt)
    if names['CONFIG.COM'].count(expected) != 1:
        raise ValueError('CONFIG.COM fingerprint does not match installed system carrier/geometry')


def validate_config_cold_patch(target, raw, files, root):
    """Independently bind CONFIG's cold operand metadata to installed bytes/symbols."""
    from iobyte_config import descriptor
    from system_layout import LAYOUT
    program=next((data for c,data in files if c['name']=='CONFIG.COM' and c['user']==0),None)
    if program is None:return
    image=raw.read_bytes()
    if target=='z80pack':
        from fdf_format import select_fdf
        from build_z80pack_image import DEFAULT_FORMAT
        fmt=select_fdf(root/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
        def record(n):
            t,i=divmod(n,fmt.spt);at=t*fmt.raw_track_bytes+fmt.raw_record_map()[i]*128
            return image[at:at+128]
        code=b''.join(record(n) for n in range(8,60))
        expected=descriptor(code,LAYOUT['SYSTEM'],(root/'build/z80pack/bios.lst').read_text(),fmt.spt,8)
    else:
        expected=descriptor(image[512:1024],0x5000,(root/'build/trs80/stage1.lst').read_text(),80,4)
    if program.count(expected)!=1:
        raise ValueError('CONFIG.COM cold IOBYTE patch descriptor does not match installed boot code')


def validate_files(raw, out, files, g):
    listing = run(['cpmls', '-f', g['definition'], raw], out).decode()
    tokens = listing.lower().split()
    headings = {t for t in tokens if t.endswith(':')}
    if headings != {'0:'}:
        raise ValueError(f'unexpected installed user areas: {headings}')
    actual = {t for t in tokens if not t.endswith(':')}
    expected = {c['name'].lower() for c, _ in files}
    if actual != expected:
        raise ValueError(f'namespace mismatch: {actual ^ expected}')
    run(['fsck.cpm', '-n', '-f', g['definition'], raw], out, out / 'filesystem-validation.txt')
    result = []
    for i, (component, data) in enumerate(files):
        extracted = out / f'extracted-{i}'
        run(['cpmcp', '-f', g['definition'], raw,
             f"{component['user']}:{component['name']}", extracted], out)
        installed = extracted.read_bytes()
        if installed[:len(data)] != data or len(installed) > (len(data)+127)//128*128 or len(installed)<len(data):
            raise ValueError(f"file integrity failure: {component['name']}")
        result.append({**component, 'bytes': len(data), 'sha256': digest(data)})
    (out / 'directory.txt').write_text(listing)
    return result


def development_identity():
    """Default builds identify current development separately from frozen core."""
    from version_metadata import rows
    core=next(row['implementation_version'] for row in rows()
              if row['component']=='BetterCP/M')
    return f'BetterCP/M development (after core {core})'


def boot(target, image, out, root, simulator, emulator):
    from utility_versions import banner as utility_banner
    ed_identity = utility_banner('ED')
    identity = development_identity()
    if target == 'z80pack':
        from test_z80pack_sysgen_install import session
        disks = out / 'disks'
        disks.mkdir()
        shutil.copy2(image, disks / 'drivea.dsk')
        for letter in 'bcd':
            shutil.copy2(root / f'build/z80pack/disks/drive{letter}.dsk', disks / f'drive{letter}.dsk')
        text = session(simulator, disks, [(b'CPX LIST\r', b'A0>_ ', 60),
                       (b'VER\r', b'A0>_ ', 60),
                       (b'ED /VER\r', b'A0>_ ', 60),
                       (b'RSX LOAD ZPRTC\r', b'A0>_ ', 60),
                       (b'RSX LIST\r', b'A0>_ ', 60)], out/'boot.txt').decode(errors='replace')
        if 'RCP' not in text or 'BetterCP/M' not in text or 'ZPRTC : BDOS' not in text:
            raise ValueError('cpmsim boot/system/provider identity missing')
        if ed_identity not in text:
            raise ValueError('installed ED identity missing; see boot.txt')
        # Styled cold banner separates product and release onto different lines.
        # Its unique operator hint must appear once; VER supplies the compact identity.
        if text.count('Type TYPE README.TXT for more') != 1 or text.count(identity) != 1:
            raise ValueError('cold banner missing or repeated on warm boot; see boot.txt')
        if 'Error' in text or 'NOT FOUND' in text:
            raise ValueError('cpmsim command failure; see boot.txt')
        # A second private boot proves BYE returns control to the host.
        script = out/'exit-test.exp'
        script.write_text(r"""set timeout 30
log_file -noappend [lindex $argv 2]
spawn -noecho [lindex $argv 0] -z -d [lindex $argv 1]
expect {
 -exact {A0>_ } {}
 timeout {exit 1}
 eof {exit 1}
}
send -- "BYE /Y\r"
expect {
 eof {}
 timeout {exit 1}
}
set status [wait]
exit [lindex $status 3]
""")
        environment = dict(os.environ)
        environment['PATH'] = str(simulator.parent/'srctools')+os.pathsep+environment['PATH']
        subprocess.run(['expect', str(script), str(simulator), str(disks),
                        str(out/'exit-test.txt')], cwd=out, env=environment,
                       check=True, timeout=60, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)

    else:
        from trs80gp_launch import run as launch
        from run_trs80_command import key_args
        from test_sysgen_install import screen
        private = out / 'boot-test.dmk'
        shutil.copy2(image, private)
        command = [str(emulator), '-m4', '-batch', '-turbo', '-ktx',
                   '-d0', str(private), '-itime', '15000',
                   '-iw', 'Type TYPE README.TXT for more', '-id', '6000', '-it']
        command += key_args('CPX LIST\r')+['-iw','RCP','-id','6000','-it']
        command += key_args('VER\r')+['-iw',identity,'-id','6000','-it']
        command += key_args('ED /VER\r')+['-iw',ed_identity,'-id','6000','-it','-ix']
        launch(command, cwd=out, timeout=300)
        initial = screen(out/'trs80-text-0.bin')
        cpx = screen(out/'trs80-text-1.bin')
        final = screen(out/'trs80-text-3.bin')
        (out/'boot.txt').write_text(initial+'\n'+cpx+'\n'+final)
        if ed_identity not in final:
            raise ValueError('Model 4 installed ED identity missing; see boot.txt')
        if 'BetterCP/M' not in initial:
            raise ValueError('Model 4 cold startup banner missing; see boot.txt')
        if 'A0>' not in initial or 'BetterCP/M' not in final or 'RCP' not in cpx:
            raise ValueError('Model 4 boot/system identity missing; see boot.txt')
    return 'PASS'



def publish_named(generation, reports, root=ROOT):
    """Prepare every named copy before atomically replacing each destination."""
    prepared = []
    try:
        for _, image, report in reports:
            target = report['target']
            folder = root / ('build/trs80' if target == 'trs80gp'
                             else 'build/z80pack/disks/library')
            if report.get('profile'):folder=folder/report['profile']
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / image.name
            source = generation / target / image.name
            with tempfile.NamedTemporaryFile(dir=folder, delete=False) as stream:
                temporary = Path(stream.name)
                prepared.append((temporary, destination))
                stream.write(source.read_bytes())
            if digest(temporary.read_bytes()) != report['sha256']:
                raise ValueError(f'named-image copy failed integrity check: {destination}')
        for temporary, destination in prepared:
            temporary.replace(destination)
    finally:
        for temporary, _ in prepared:
            temporary.unlink(missing_ok=True)
    return [destination for _, destination in prepared]


def publish_generation(publication, generation, reports):
    """Reuse an identical, intact immutable release on repeated builds."""
    if generation.exists():
        for _, image, report in reports:
            target = generation / report['target']
            try:
                existing = json.loads((target / 'report.json').read_text())
                image_hash = digest((target / image.name).read_bytes())
                package_hash = digest((target/'SYSTEM.SYS').read_bytes()) if 'package_sha256' in report else None
            except (OSError, ValueError) as error:
                raise ValueError(f'{generation}: existing release is incomplete or unreadable; previous release preserved') from error
            if existing != report or image_hash != report['sha256'] or package_hash != report.get('package_sha256'):
                raise ValueError(f'{generation}: existing release differs or failed integrity check; previous release preserved')
        return True
    with tempfile.TemporaryDirectory(prefix='.candidate-', dir=generation.parent) as publish_temp:
        staged = Path(publish_temp) / 'release'
        shutil.copytree(publication, staged)
        staged.rename(generation)
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=['all','z80pack','trs80gp'], default='all')
    p.add_argument('--profile', choices=['default', *PROFILES], default='default',
                   help='explicit checked cpmsim RAM distribution profile')
    p.add_argument('--prepare-profile', action='store_true',
                   help='stage profile inputs without assembling or publishing a distribution; requires --work')
    p.add_argument('--output', type=Path, default=ROOT/'build/distribution')
    p.add_argument('--work', type=Path, help='persistent isolated build cache (fresh directory)')
    p.add_argument('--reuse-work', action='store_true', help='reuse only hash-verified identical source/artifacts')
    p.add_argument('--simulator', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--emulator', type=Path, default=Path('/Users/nathanael/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp'))
    a = p.parse_args()
    if a.reuse_work and not a.work:
        p.error('--reuse-work requires --work')
    if os.environ.get(CONTEXT_ENV):
        p.error(f'run distribution selection without inherited {CONTEXT_ENV}; select --profile explicitly')
    profile = None
    if a.profile != 'default':
        try:
            profile = select_profile(a.profile, a.target)
        except ValueError as error:
            p.error(str(error))
    if a.prepare_profile:
        if not profile or not a.work:
            p.error('--prepare-profile requires an explicit --profile and --work')
        root = prepare_profile(a.work.resolve(), a.target, source_identity(profile),
                               profile, a.reuse_work)
        print(json.dumps({'status':'profile inputs prepared; no distribution generated',
                          'workspace':str(root), 'profile':profile.name,
                          'context':str(root/'build/profile/context.json')}, indent=2))
        return
    if profile:
        from build_profiles import context_environment
        identity=source_identity(profile)
        a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='bettercpm-checked-dist-') as temporary:
            work=a.work.resolve() if a.work else Path(temporary)/'work'
            root=prepare_profile(work,a.target,identity,profile,a.reuse_work)
            publication=work/('candidate-'+Path(temporary).name);publication.mkdir(parents=True)
            out=publication/'z80pack'
            command=[sys.executable,str(root/'tools/build_checked_distribution.py'),
                     '--output',str(out),'--simulator',str(a.simulator.resolve())]
            if a.reuse_work:command.append('--reuse')
            environment=context_environment(root/'build/profile/context.json',root/'src/system/layout.inc')
            run(command,root,work/('checked-'+profile.name+'.log'),timeout=1800,env=environment)
            report=json.loads((out/'report.json').read_text());image=out/report['image']
            if source_identity(profile)!=identity:raise ValueError('source changed; checked candidate not published')
            from release_metadata import disk_record
            report['source']=identity
            from component_tracking import record_collection
            record_collection(root,report['target'],report['source'])
            report['release_record']=disk_record(report,image.read_bytes(),root=root)
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            reports=[(out,image,report)]
            generation=a.output/('release-'+profile.name+'-'+identity['revision'][:12]+'-'+digest(json.dumps(report,sort_keys=True).encode())[:12])
            publish_generation(publication,generation,reports)
            named=publish_named(generation,reports)
            print('PASS '+str(named[0])+': checked boot and live acceptance')
        return
    manifest = json.loads(MANIFEST.read_text())
    identity = source_identity()
    a.output = a.output.resolve()
    a.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bettercpm-dist-') as temporary:
        work = a.work.resolve() if a.work else Path(temporary)/'work'
        work.mkdir(parents=True, exist_ok=True)
        publication = work/('candidate-'+Path(temporary).name)
        publication.mkdir()
        reports = []
        for target in (['z80pack','trs80gp'] if a.target=='all' else [a.target]):
            print(f'{target}: building and qualifying isolated System Disk', flush=True)
            root = current_build(work, target, identity, a.reuse_work)
            out = publication/target
            out.mkdir()
            if target == 'z80pack':
                stage_cpmsim_guest(a.simulator, root)
            files, omitted = selected_files(manifest, target, root)
            g = geometry(target, root)
            totals = capacity(files, g)
            raw = construct(target, root, out, files, g, manifest.get('cold_start_command', ''))
            validate_config_fingerprint(target, raw, files, root)
            validate_config_cold_patch(target, raw, files, root)
            included = validate_files(raw, out, files, g)
            name = f'BetterCPM-Distribution-{target}-'+('332K.dsk' if target=='z80pack' else '80T-DS-System.dmk')
            image = out/name
            if target=='z80pack':
                shutil.copy2(raw,image)
            else:
                from build_montezuma_extended_790k import build, verify
                image.write_bytes(build(raw.read_bytes()))
                verify(image.read_bytes(), require_blank=False)
            boot_result = boot(target,image,out,root,a.simulator.resolve(),a.emulator.resolve())
            report = {'target':target, 'format':g['format'], 'image':name,
                      'cold_start_command':manifest.get('cold_start_command', ''),
                      'sha256':digest(image.read_bytes()), 'source':identity,
                      'manifest_sha256':digest(MANIFEST.read_bytes()),
                      'tools':{n:digest(Path(shutil.which(n)).read_bytes()) for n in ['cpmcp','cpmls','fsck.cpm']},
                      'emulator_sha256':digest((a.simulator if target=='z80pack' else a.emulator).read_bytes()),
                      'included':included, 'omitted':omitted, **totals,
                      'validation':{'filesystem':'PASS','file_integrity':'PASS','config_fingerprint':'PASS','boot':boot_result},
                      'issues':['Utilities/CPM Tools media and additional on-disk documentation deferred']}
            from release_metadata import disk_record
            from component_tracking import record_collection
            record_collection(root,report['target'],report['source'])
            report['release_record']=disk_record(report,image.read_bytes(),root=root)
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            shutil.copy2(root/'build.log',out/'build.log')
            reports.append((out,image,report))
        # Publish one immutable generation only after every requested target passes.
        generation = a.output / ('release-'+identity['revision'][:12]+'-'+digest(json.dumps([r for _,_,r in reports],sort_keys=True).encode())[:12])
        if source_identity() != identity:
            raise ValueError('source inputs changed during the build; candidate not published')
        # Keep construction inputs/private emulator media out of delivered evidence.
        for out, _, _ in reports:
            for pattern in ('artifact-*', 'extracted-*', 'boot-test.dmk'):
                for path in out.glob(pattern):
                    path.unlink()
            shutil.rmtree(out/'disks', ignore_errors=True)
        if publish_generation(publication, generation, reports):
            print(f'Reusing verified release: {generation}', flush=True)
        named_images = publish_named(generation, reports)
        for destination, (_, image, report) in zip(named_images, reports):
            print(f"PASS {destination}: {len(report['included'])} files, {report['free_bytes']//1024}K free; planned: "+', '.join(c['name'] for c in report['omitted'] if c['status']=='planned'))


if __name__=='__main__':
    main()
