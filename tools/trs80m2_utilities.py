"""Package the ordinary Utilities inventory on native BCM2SS media."""
import hashlib
import json

from model2_media import geometry, image
from test_model2_release_media import decoded
from test_utilities_inventory import inspect


def system_digest(directory, compatibility_id):
    standard = directory/'report.json'
    if standard.is_file():
        manifest = json.loads(standard.read_text())
        from trs80m2_distribution import SYSTEM_NAME
        name = SYSTEM_NAME
        if manifest.get('image')!=name:
            raise ValueError('unexpected Model II distribution image')
        expected = manifest['sha256']
    else:
        manifest = json.loads((directory/'candidate.json').read_text())
        name = 'Model-II-System-candidate.imd'
        expected = manifest['files'][name]
    actual = hashlib.sha256((directory/name).read_bytes()).hexdigest()
    if (manifest['target'] != 'trs80m2' or manifest['profile'] != 'model2-fullram'
            or manifest['compatibility_id'] != compatibility_id or expected != actual):
        raise ValueError('Model II System Disk and Utilities profile do not match')
    return actual


def volume(label, files, *, compatibility_id, system_sha256):
    fmt = geometry()
    disk = image(bytes(160*128), list(files.items()), bootable=False)
    # Expand only the short FM boot surface for the common logical record auditor.
    raw = decoded(disk)[2]
    boot_bytes = fmt.boot_psectors * fmt.boot_secsize
    normalized = raw[:boot_bytes] + bytes(fmt.raw_track_bytes-boot_bytes) + raw[boot_bytes:]
    audit = inspect(normalized, fmt, files)
    name = f'BetterCPM-{label}-trs80m2-77T-SS-584K.imd'
    report = {
        'target': 'trs80m2', 'profile': 'model2-fullram', 'format': 'BCM2SS',
        'compatibility_id': compatibility_id, 'paired_system_sha256': system_sha256,
        'image': name, 'sha256': hashlib.sha256(disk).hexdigest(),
        'status': 'PROVISIONAL', 'validation': audit,
        'included': [{'name': n, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                     for n, data in files.items()],
        'pending': ['Model II paired-media guest qualification'],
    }
    return name, disk, report


def bind_qualified_pair(reports, artifacts):
    """Attach the native pairing receipt only to the three tested image hashes."""
    folder = artifacts/'docs/engineering/evidence/2026-11-07-model2-acceptance'
    path = folder/'guest.json'
    lifecycle = folder/'lifecycle.json'
    if not path.is_file() or not lifecycle.is_file():
        return
    proof = json.loads(path.read_text())
    gate = json.loads(lifecycle.read_text())
    if proof.get('status')!='PASS' or gate.get('status')!='PASS':
        return
    for (_, _, report), key in zip(reports,('primary_sha256','companion_sha256')):
        if (report['sha256']!=proof[key] or report['paired_system_sha256']!=proof['system_sha256']
                or report['compatibility_id']!=gate['compatibility_id'] or gate['system_sha256']!=proof['system_sha256']):
            return
    if len(reports)!=2 or proof['release_phases']!={key:'PASS' for key in ('utilities','batch','lifecycle','install')}:
        return
    for _,_,report in reports:
        report['status'] = 'QUALIFIED_PLATFORM_MEDIA'
        report['pending'].remove('Model II paired-media guest qualification')
        report['paired_media_evidence'] = {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                           'path':str(path.relative_to(artifacts)),
                                           'scope':'Native paired-media release checks; individual utility campaigns are recorded separately.'}
