#!/usr/bin/env python3
"""Build and qualify one manifest-selected checked cpmsim distribution."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
from checked_carriers import selected_contract
from build_distribution import (digest,selected_files,stage_cpmsim_guest,geometry,capacity,construct,
    validate_config_fingerprint,validate_config_cold_patch,validate_files,boot)
from build_z80pack_image import DEFAULT_FORMAT,disk_definition
from fdf_format import select_fdf

ROOT=Path(__file__).resolve().parents[1]


def components(reuse):
    contract=selected_contract()
    if not contract:raise ValueError('select a prepared checked profile')
    source=json.loads((ROOT/'profile-state.json').read_text())['source']
    stamp=ROOT/'build-state.json'
    if reuse:
        state=json.loads(stamp.read_text())
        if state['source']!=source:raise ValueError('checked cache source differs')
        current={str(p.relative_to(ROOT)) for p in (ROOT/'build').rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        if current!=set(state['artifacts']):raise ValueError('checked cache artifact inventory differs')
        for path,expected in state['artifacts'].items():
            if digest((ROOT/path).read_bytes())!=expected:raise ValueError('changed checked artifact: '+path)
        return contract
    if stamp.exists():raise ValueError('checked products exist; select reuse or a fresh workspace')
    builders=('checked_resident_rsx','checked_carriers','checked_package','utilities',
              'fdf_catalog','ed','svctest','stattst','z80pack_bye')
    for name in builders:
        subprocess.run([sys.executable,str(ROOT/'tools'/f'build_{name}.py')],cwd=ROOT,check=True)
    out=ROOT/'build/z80pack';fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    payload=(out/'system-package/system-tracks.bin').read_bytes()
    raw=bytearray(b'\xe5'*fmt.image_bytes)
    for record in range(160):
        track,within=divmod(record,fmt.spt)
        at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
        raw[at:at+128]=payload[record*128:(record+1)*128]
    disks=out/'disks';disks.mkdir(exist_ok=True)
    for drive in 'abcd':(disks/f'drive{drive}.dsk').write_bytes(raw)
    (out/'diskdefs').write_text(disk_definition(fmt))
    if selected_contract()!=contract:raise ValueError('checked source changed during build')
    hashes={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sorted((ROOT/'build').rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    stamp.write_text(json.dumps({'source':source,'artifacts':hashes},indent=2)+'\n')
    return contract


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--reuse',action='store_true')
    a=p.parse_args();contract=components(a.reuse);out=a.output.resolve();out.mkdir(parents=True)
    manifest=json.loads((ROOT/'metadata/distribution.json').read_text())
    stage_cpmsim_guest(a.simulator, ROOT)
    files,omitted=selected_files(manifest,'z80pack',ROOT)
    if {'HELLO.RSX','HELLO.CPX','STATEFUL.RSX'} & {c['name'] for c,_ in files}:
        raise ValueError('development fixture in distribution')
    g=geometry('z80pack',ROOT);totals=capacity(files,g)
    raw=construct('z80pack',ROOT,out,files,g,manifest.get('cold_start_command',''))
    validate_config_fingerprint('z80pack',raw,files,ROOT)
    validate_config_cold_patch('z80pack',raw,files,ROOT)
    included=validate_files(raw,out,files,g)
    image=out/('BetterCPM-Distribution-'+contract['contract']['profile']+'-332K.dsk')
    shutil.copy2(raw,image)
    shutil.copy2(ROOT/'build/z80pack/system-package/SYSTEM.SYS',out/'SYSTEM.SYS')
    shutil.copy2(ROOT/'build/z80pack/checked-package.json',out/'checked-package.json')
    boot('z80pack',image,out,ROOT,a.simulator.resolve(),Path('/unused'))
    from qualify_checked_distribution import qualify
    acceptance=qualify(ROOT,image,out/'acceptance',a.simulator.resolve())
    report={'target':'z80pack','profile':contract['contract']['profile'],
       'compatibility_id':contract['compatibility_id'],'source':json.loads((ROOT/'profile-state.json').read_text())['source'],
       'image':image.name,'sha256':digest(image.read_bytes()),'format':g['format'],
       'included':included,'omitted':omitted,**totals,
       'package_sha256':digest((out/'SYSTEM.SYS').read_bytes()),
       'validation':{'filesystem':'PASS','file_integrity':'PASS','config_fingerprint':'PASS','boot':'PASS','acceptance':acceptance},
       'simulator_sha256':digest(a.simulator.read_bytes())}
    if selected_contract()!=contract:raise ValueError('source changed during qualification')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for pattern in ('artifact-*','extracted-*'):
        for path in out.glob(pattern):path.unlink()
    shutil.rmtree(out/'disks',ignore_errors=True)
    print('PASS checked distribution '+report['profile'])


if __name__=='__main__':main()
