"""Build/inspect 1.2 media without repeating engineering qualification campaigns.

Native smoke remains explicitly pending. All outputs retain source/image hashes.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from build_distribution import (ROOT, source_identity, prepare_profile, current_build,
    selected_files, geometry, capacity, construct, validate_config_fingerprint,
    validate_config_cold_patch, validate_files, digest, stage_cpmsim_guest, run)
from build_profiles import PROFILES, profile_inputs, context_environment
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from test_utilities_inventory import inspect
from convert_fdf_image import raw_to_dmk
from release_metadata import disk_record


def prepare(output, simulator, target, inner=False):
    output = output.resolve()
    work = output/'work'
    work.mkdir(parents=True, exist_ok=True)
    identity = (json.loads((ROOT/'profile-state.json').read_text())['source']
                if inner else source_identity())
    out = output/'systems'/target
    if out.exists():
        raise ValueError('refusing to overwrite prepared media')
    if target == 'trs80m2':
        from trs80m2_distribution import build_system
        build_system(work, out, identity, Path('/unused'), False, ROOT, pending_smoke=True)
        return
    if target == 'z80pack' and not inner:
        profile = PROFILES['cpmsim-fullram']
        identity = dict(identity, profile=profile_inputs(profile, ROOT/'src/system/layout.inc')[0])
        root = prepare_profile(work, target, identity, profile)
        environment = context_environment(root/'build/profile/context.json', root/'src/system/layout.inc')
        run([sys.executable, root/'tools/prepare_release_12.py', '--output', output,
             '--simulator', simulator, '--target', target, '--inner'], root,
            work/'cpmsim-prepare.log', timeout=1800, env=environment)
        return
    if inner:
        root = ROOT
        identity = json.loads((root/'profile-state.json').read_text())['source']
        stage_cpmsim_guest(simulator, root)
        from build_checked_distribution import components
        components(False)
    else:
        root = current_build(work, target, identity, False)
    manifest = json.loads((ROOT/'metadata/distribution.json').read_text())
    files, omitted = selected_files(manifest, target, root)
    g = geometry(target, root)
    totals = capacity(files, g)
    out.mkdir(parents=True)
    raw = construct(target, root, out, files, g, manifest.get('cold_start_command', ''))
    validate_config_fingerprint(target, raw, files, root)
    validate_config_cold_patch(target, raw, files, root)
    included = validate_files(raw, out, files, g)
    name = 'BetterCPM-Distribution-'+target+('-332K.dsk' if target == 'z80pack' else '-80T-DS-System.dmk')
    if target == 'z80pack':
        binary = raw.read_bytes()
    else:
        from build_montezuma_extended_790k import build, verify
        binary = build(raw.read_bytes())
        verify(binary, require_blank=False)
    (out/name).write_bytes(binary)
    fmt = select_fdf(ROOT/'metadata/DISK.FDF', DEFAULT_FORMAT if target == 'z80pack'
                    else 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    blank = bytes([0xe5])*fmt.image_bytes
    inspect(blank, fmt, {})
    work_image = blank if target == 'z80pack' else raw_to_dmk(blank, fmt)
    (out/'work-image').write_bytes(work_image)
    report = {'target':target, 'image':name, 'sha256':digest(binary), 'source':identity,
              'manifest_sha256':digest((ROOT/'metadata/distribution.json').read_bytes()),
              'included':included, 'omitted':omitted, **totals,
              'release_policy':'1.2-focused', 'build_root':str(root),
              'work_image_sha256':digest(work_image), 'work_image_inventory':'PASS',
              'validation':{'filesystem':'PASS', 'file_integrity':'PASS',
                            'config_fingerprint':'PASS', 'boot':'PENDING_SMOKE'}}
    report['release_record'] = disk_record(report, binary, root=root)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(target, digest(binary), 'construction PASS; smoke pending', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--simulator', type=Path, required=True)
    p.add_argument('--target', choices=('z80pack','trs80gp','trs80m2'), required=True)
    p.add_argument('--inner', action='store_true', help=argparse.SUPPRESS)
    a = p.parse_args()
    prepare(a.output, a.simulator.resolve(), a.target, a.inner)
