"""Build the supported Model II System Disk and its distribution report."""
import json
import shutil
import sys
from pathlib import Path

from build_profiles import PROFILES, context_environment
from fdf_v1 import compile_file
from model2_media import geometry
from test_model2_release_media import decoded
from test_utilities_inventory import inspect

SYSTEM_NAME = 'BetterCPM-Distribution-trs80m2-77T-SS-System.imd'
LIFECYCLE = Path('docs/engineering/evidence/2026-11-07-model2-acceptance/lifecycle.json')


def build_system(work, out, identity, emulator, reuse, repo, *, pending_smoke=False):
    from build_distribution import digest, prepare_profile, profile_inputs, run
    from release_metadata import disk_record

    target = 'trs80m2'
    profile = PROFILES['model2-fullram']
    identity = dict(identity, profile=profile_inputs(profile,repo/'src/system/layout.inc')[0])
    staged = prepare_profile(work,target,identity,profile,reuse,source_root=repo)
    env = context_environment(staged/'build/profile/context.json',staged/'src/system/layout.inc')
    run([sys.executable,'-B',staged/'tools/build_model2.py'],staged,work/'model2-build.log',env=env)
    artifacts = staged/'build'
    media = artifacts/target
    manifest = json.loads((media/'candidate.json').read_text())
    system = media/'Model-II-System-candidate.imd'
    binary = system.read_bytes()
    system_hash = digest(binary)
    if manifest['files'][system.name]!=system_hash or manifest['profile']!=profile.name:
        raise ValueError('mismatched Model II System Disk or profile')
    from build_distribution import selected_files
    selection,omitted=selected_files(json.loads((staged/'metadata/distribution.json').read_text()),target,staged)
    files={row['name']:data for row,data in selection}
    origins={row['name']:row['artifact'] for row,data in selection}
    files['SYSTEM.SYS']=(media/'SYSTEM.SYS').read_bytes()
    origins['SYSTEM.SYS']='build/trs80m2/SYSTEM.SYS'
    fmt = geometry()
    raw = decoded(binary)[2]
    fm_length = fmt.boot_psectors*fmt.boot_secsize
    inventory = inspect(raw[:fm_length]+bytes(fmt.raw_track_bytes-fm_length)+raw[fm_length:],fmt,files)
    out.mkdir(parents=True)
    image = out/SYSTEM_NAME
    image.write_bytes(binary)
    shutil.copyfile(media/'SYSTEM.SYS',out/'SYSTEM.SYS')
    receipt = repo/LIFECYCLE
    prior = json.loads(receipt.read_text()) if receipt.is_file() else {}
    if (prior.get('status')=='PASS' and prior.get('system_sha256')==system_hash
            and prior.get('compatibility_id')==manifest['compatibility_id']):
        boot = {'status':'PASS','source':str(LIFECYCLE),'receipt_sha256':digest(receipt.read_bytes()),
                'emulator_sha256':prior['emulator_sha256']}
    elif pending_smoke:
        boot = {'status':'PENDING_SMOKE','source':'1.2 focused release policy'}
    else:
        # New executable bytes get a fresh native lifecycle test. Only exact
        # previously qualified media can take the receipt path on a headless host.
        trials = work/'model2-boot'
        before = set(trials.glob('run-*/result.json'))
        run([sys.executable,'-B',repo/'tools/run_model2_qualification.py','--media',media,
             '--output',trials,'--emulator',emulator],repo,work/'model2-boot.log',timeout=1300)
        result, = set(trials.glob('run-*/result.json'))-before
        proof = json.loads(result.read_text())
        if not proof['status'].startswith('PASS') or proof['candidate']['files'][system.name]!=system_hash:
            raise ValueError('Model II native lifecycle check did not qualify this System Disk')
        boot = {'status':'PASS','source':'native lifecycle','emulator_sha256':proof['emulator_sha256']}
    included = [{'name':name,'bytes':len(value),'sha256':digest(value),'user':0,
                 **({'artifact':origins[name]} if name in origins else {})} for name,value in files.items()]
    report = {'target':target,'profile':profile.name,'format':'BCM2SS','image':image.name,
              'sha256':system_hash,'source':identity,'included':included,'omitted':omitted,
              'free_bytes':inventory['free_blocks']*fmt.block_bytes,
              'package_sha256':digest(files['SYSTEM.SYS']),'compatibility_id':manifest['compatibility_id'],
              'validation':{'boot':boot,'inventory':inventory}}
    if pending_smoke:
        report['release_policy'] = '1.2-focused'
    report['release_record'] = disk_record(report,binary,root=staged)
    from package_release_candidates import write_package
    kit_name = 'BetterCPM-1.1-Model-II-System.zip'
    guide = (repo/'docs/platform/MODEL2-INSTALLATION.md').read_text()
    notes = "https://github.com/CPMArchives/BetterCPM/blob/main/docs/platform/MODEL2-PORT.md"
    install = guide.replace('(MODEL2-PORT.md#','('+notes+'#').encode()
    kit_files = {image.name:binary, 'INSTALL.md':install,
                 'LICENSE':(repo/'LICENSE').read_bytes(), 'NOTICE':(repo/'NOTICE').read_bytes(),
                 'COPYING':(repo/'COPYING').read_bytes()}
    kit_record = {'platform':'TRS-80 Model II','profile':profile.name,'format':'BCM2SS',
                  'source_revision':identity['revision'],'system_disk':image.name,'sha256':system_hash,
                  'compatibility_id':manifest['compatibility_id'],'boot':boot}
    write_package(out/kit_name,'BetterCPM-Model-II',kit_files,kit_record)
    report['system_archive'] = {'name':kit_name,'sha256':digest((out/kit_name).read_bytes())}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return out,image,report
