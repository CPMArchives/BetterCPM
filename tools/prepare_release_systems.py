#!/usr/bin/env python3
"""Prepare fresh System candidates; execute cpmsim only, never launch Model 4."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_distribution import (ROOT, MANIFEST, source_identity, current_build,
    selected_files, geometry, capacity, construct, validate_config_fingerprint,
    validate_config_cold_patch, validate_files, digest, boot)
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT, disk_definition
from convert_fdf_image import raw_to_dmk
from test_utilities_inventory import inspect


def prepare(output, simulator):
    output=output.resolve();simulator=simulator.resolve()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT).strip():
        raise ValueError('System candidate preparation requires clean tracked source')
    output.mkdir(parents=True,exist_ok=False)
    identity=source_identity();manifest=json.loads(MANIFEST.read_text())
    # This existing build path emits both common Model 4 and target cpmsim
    # artifacts, without starting trs80gp. Images have private filesystems.
    root=current_build(output/'work','z80pack',identity,False)
    for target in ('z80pack','trs80gp'):
        out=output/target;out.mkdir()
        files,omitted=selected_files(manifest,target,root)
        g=geometry(target,root);totals=capacity(files,g)
        raw=construct(target,root,out,files,g,manifest.get('cold_start_command',''))
        validate_config_fingerprint(target,raw,files,root)
        validate_config_cold_patch(target,raw,files,root)
        included=validate_files(raw,out,files,g)
        name='BetterCPM-Distribution-'+target+('-332K.dsk' if target=='z80pack' else '-80T-DS-System.dmk')
        if target=='z80pack':
            image=raw.read_bytes()
        else:
            from build_montezuma_extended_790k import build,verify
            image=build(raw.read_bytes());verify(image,require_blank=False)
        path=out/name;path.write_bytes(image)
        result='PENDING manual execution; no automated Model 4 launch attempted'
        if target=='z80pack':
            result=boot(target,path,out,root,simulator,Path('/unused-no-model4-launch'))
        native=target=='trs80gp'
        fmt=select_fdf(ROOT/'third_party/montezuma'/('DISK-INT.FDF' if native else 'DISK.FDF'),
            'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
        blank=bytes([0xe5])*fmt.image_bytes
        inspect(blank,fmt,{})
        (out/'work-image').write_bytes(raw_to_dmk(blank,fmt) if native else blank)
        report={'target':target,'image':name,'format':g['format'],'sha256':digest(image),
                'source':identity,'manifest_sha256':digest(MANIFEST.read_bytes()),
                'cold_start_command':manifest.get('cold_start_command',''),
                'included':included,'omitted':omitted,**totals,
                'status':'CANDIDATE; NOT ACCEPTED',
                'validation':{'filesystem':'PASS','file_integrity':'PASS',
                              'config_fingerprint':'PASS','boot':result},
                'work_image_sha256':digest((out/'work-image').read_bytes()),
                'work_image_inventory':'PASS empty directory/allocation independent inspection'}
        if target=='z80pack':report['emulator_sha256']=digest(simulator.read_bytes())
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(target,result,flush=True)
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    a=p.parse_args();prepare(a.output,a.simulator)
