"""Bind destructive guest fixtures to the exact unmodified release input image."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def bind(image, platform, expected):
    image=Path(image).resolve()
    report_path=image.parent/'report.json'
    report=json.loads(report_path.read_text())
    digest=hashlib.sha256(image.read_bytes()).hexdigest()
    if report['image']!=image.name or report['sha256']!=digest:
        raise ValueError('release image differs from its construction report')
    target={'cpmsim':'z80pack','model4':'trs80gp','model2':'trs80m2'}[platform]
    if report['target']!=target:raise ValueError('wrong release target')
    if platform=='cpmsim':
        observed={}
        with tempfile.TemporaryDirectory() as td:
            for name in expected:
                dest=Path(td)/name
                subprocess.run(['cpmcp','-f','bettercpm-default',str(image),'0:'+name,str(dest)],
                               cwd=image.parent,check=True,capture_output=True)
                if not dest.exists():raise ValueError('missing on-media input: '+name)
                observed[name]=dest.read_bytes()
    else:
        from package_integrated_tcap import native_files
        observed=native_files(image,platform)
    hashes={}
    for name,data in expected.items():
        actual=observed[name]
        if actual[:len(data)]!=data or len(actual)!=(len(data)+127)//128*128 or set(actual[len(data):])-{0,26}:
            raise ValueError('on-media executable differs from qualification input: '+name)
        hashes[name]=hashlib.sha256(data).hexdigest()
    return {'source_commit':report['source']['revision'],'image':image.name,
            'image_sha256':digest,'construction_report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
            'verified_executables':hashes,
            'fixture_boundary':'Unmodified release image checked first. Guest fixtures use disposable media; test scripts and fixtures are added, without substituting the verified executable cohort.'}
