"""Run existing FDB campaigns on copies of complete System media."""
from pathlib import Path
import hashlib
import json
import subprocess
from add_cpm_file_to_dmk import extract_raw


def stage(target, raw, system_image, fixtures, out):
    if not system_image:
        return
    image = system_image.resolve()
    payload = image.read_bytes()
    raw.write_bytes(extract_raw(payload) if target == 'trs80gp' else payload)
    (out/'media-origin.json').write_text(json.dumps({
        'image': str(image), 'sha256': hashlib.sha256(payload).hexdigest()}, indent=2)+'\n')
    for index, (name, data) in enumerate(fixtures):
        path = out/f'fixture-{index}'
        path.write_bytes(data)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(raw),
                        str(path),'0:'+name],cwd=out,check=True,capture_output=True)


def startup(target, system_image):
    # The interactive workbench requires the standard 53 KiB TPA. Model 4
    # normally loads screen personalities; release them explicitly on this
    # disposable test boot rather than changing the shipped startup defaults.
    if target == 'trs80gp' and system_image:
        return [('RSX UNLOAD ADM3A','A0>'), ('RSX UNLOAD M4SCRN','A0>')]
    return []


def audit(target, system_image, after, out, changed=()):
    if not system_image:
        return
    receipt = json.loads((system_image.resolve().parent/'report.json').read_text())
    original = system_image.read_bytes()
    original = extract_raw(original) if target == 'trs80gp' else original
    # All reserved records precede the filesystem in these two System layouts.
    reserved = 20480 if target == 'trs80gp' else 27648
    assert after.read_bytes()[:reserved] == original[:reserved], 'cold defaults changed'
    verified = []
    for item in receipt['included']:
        if item['name'] in changed:
            continue
        path = out/'audit-file'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(after),
                        f"{item.get('user',0)}:{item['name']}",str(path)],
                       cwd=out,check=True,capture_output=True)
        assert hashlib.sha256(path.read_bytes()[:item['bytes']]).hexdigest() == item['sha256'], item['name']
        verified.append(item['name'])
    subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(after)],
                   cwd=out,check=True,capture_output=True)
    (out/'preservation.json').write_text(json.dumps({
        'status':'PASS','reserved_bytes':reserved,'original_files_preserved':verified,
        'expected_changed_files':list(changed)},indent=2)+'\n')
