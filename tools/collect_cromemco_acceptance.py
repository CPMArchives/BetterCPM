#!/usr/bin/env python3
"""Retain focused acceptance only when a frozen rebuild reproduces every volume."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,required=True)
    p.add_argument('--accepted-build-root',type=Path,required=True)
    p.add_argument('--gate-prefix',type=Path,required=True)
    p.add_argument('--hardware',type=Path,required=True)
    p.add_argument('--display-transport',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.build_root.resolve();accepted=a.accepted_build_root.resolve()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    collection=json.loads((root/'build/cromemco/release/collection.json').read_text())
    previous=json.loads((accepted/'build/cromemco/release/collection.json').read_text())
    assert collection['volumes']==previous['volumes'], 'frozen collection differs from executed acceptance'
    for row in collection['volumes']:
        assert sha(root/'build/cromemco/release'/row['image'])==row['sha256']
    system=collection['volumes'][0]['sha256']
    gates={name:Path(str(a.gate_prefix)+'-'+name.replace('-','_')) for name in
           ('loader','install','media','utilities','compatibility','shared-core')}
    gates.update(hardware=a.hardware,**{'display-transport':a.display_transport})
    rows={}
    for name,folder in gates.items():
        result=json.loads((folder/'result.json').read_text());assert result['status']=='PASS',name
        if name in ('loader','install','media','utilities','compatibility'):
            assert result['system_sha256']==system,name
        if name=='shared-core':
            for row in result['artifacts']:assert sha(root/row['artifact'])==row['sha256']
        if name=='display-transport':
            for row in result['modules']:
                assert sha(root/'build/release-tcap'/row['personality']/'native.bin')==row['native_sha256']
        destination=out/name;destination.mkdir()
        for path in folder.rglob('*'):
            if not path.is_file() or 'comparison' in path.relative_to(folder).parts:continue
            if path.name not in ('result.json','transcript.txt') and path.suffix not in ('.log','.asm','.lst'):continue
            target=destination/path.relative_to(folder);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
        rows[name]={'status':'PASS','result':name+'/result.json','executed_evidence':str(folder.resolve()),
                    'result_sha256':sha(folder/'result.json')}
    result={'status':'PASS','system_sha256':system,
            'emulator_sha256':json.loads((a.hardware/'result.json').read_text())['emulator_sha256'],
            'gates':rows,'collection':collection,
            'evidence_reuse':'All four frozen media volumes equal those used in the executed gates; shared executable and display bodies are also checked directly.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: frozen four-volume rebuild matches every executed acceptance gate')


if __name__=='__main__':main()
