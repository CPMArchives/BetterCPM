#!/usr/bin/env python3
"""Assemble provisional Utilities media from implemented owned components only.

No third-party candidate is silently selected. The report lists remaining
manifest entries; these development images are not a completed release disk.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT=Path(os.environ.get("BCPM_REPO",Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0,str(ROOT/"tools"))
from fdf_format import select_fdf
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from convert_fdf_image import raw_to_dmk, dmk_to_raw
COMPONENTS={'DDT.COM':'build/utilities/DDT.COM','DUMP.COM':'build/utilities/DUMP.COM','XSUB.COM':'build/utilities/XSUB.COM','BATCHIO.RSX':'build/rsx/BATCHIO.RSX','SQ.COM':'build/utilities/SQ.COM','USQ.COM':'build/utilities/USQ.COM','UNCR.COM':'build/utilities/UNCR.COM'}
PENDING=['Full-screen editor (selection pending)','ZSM4 (release packaging pending)','LINK (release packaging pending)','Z80 disassembler (selection pending)','Archive utility (selection pending)','CR and CrLZH utilities (implementation pending)']
sha=lambda data:hashlib.sha256(data).hexdigest()


def build(output, artifacts=ROOT, ddt_acceptance=None):
    files={name:(artifacts/path).read_bytes() for name,path in COMPONENTS.items()}
    if not all(files.values()):raise ValueError('empty Utilities artifact')
    accepted=json.loads(ddt_acceptance.read_text()) if ddt_acceptance else None
    if accepted is not None:
        if accepted.get('ddt_utilities_acceptance')!='PASS' or accepted.get('ddt_sha256')!=sha(files['DDT.COM']):
            raise ValueError('DDT acceptance does not match current artifact')
    reports=[]
    output.mkdir(parents=True,exist_ok=True)
    for target in ['z80pack','trs80gp']:
        native=target=='trs80gp'
        fmt=select_fdf(ROOT/'third_party/montezuma'/('DISK-INT.FDF' if native else 'DISK.FDF'), 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
        definition='bettercpm-mm-80t-ds-data' if native else 'bettercpm-default'
        with tempfile.TemporaryDirectory(prefix='bettercpm-utilities-',dir='/private/tmp') as temp:
            work=Path(temp);(work/'diskdefs').write_text(disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)))
            raw=work/'utilities.dsk';raw.write_bytes(bytes([0xE5])*fmt.image_bytes)
            def run(*args):
                result=subprocess.run(args,cwd=work,capture_output=True)
                if result.returncode:raise RuntimeError(f'{args}: {result.stdout!r} {result.stderr!r}')
                return result
            run('mkfs.cpm','-f',definition,str(raw))
            for name,data in files.items():
                source=work/name;source.write_bytes(data);run('cpmcp','-T','raw','-f',definition,str(raw),str(source),'0:'+name)
                extracted=work/('readback-'+name);run('cpmcp','-T','raw','-f',definition,str(raw),'0:'+name,str(extracted))
                actual=extracted.read_bytes();assert actual[:len(data)]==data and len(actual)<=((len(data)+127)//128)*128,name
            run('fsck.cpm','-T','raw','-f',definition,'-n',str(raw))
            data=raw.read_bytes()
            if native:
                image=raw_to_dmk(data,fmt);assert dmk_to_raw(image,fmt)==data
            else:image=data
            name=f'BetterCPM-Utilities-{target}-'+('80T-DS-800K.dmk' if native else '332K.dsk')
            reports.append((name,image,{'target':target,'image':name,'sha256':sha(image),'format':fmt.name,'status':'PROVISIONAL','included':[{'name':n,'sha256':sha(d),'bytes':len(d)} for n,d in files.items()],'pending':PENDING,'validation':'file readback and filesystem PASS; native DMK/raw round trip PASS; no whole Utilities release acceptance claimed'}))
    # Component evidence is valid only for these exact packaged images.
    for name,data,report in reports:
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['DDT.COM'])}
        if accepted:
            proof=accepted['platforms'][report['target']]
            if proof['status']!='PASS' or proof['utilities_sha256']!=sha(data) or proof['ddt_sha256']!=sha(files['DDT.COM']):
                raise ValueError('DDT acceptance does not match packaged '+name)
            verdict={'status':'PASS','sha256':sha(files['DDT.COM']),'evidence_sha256':sha(ddt_acceptance.read_bytes())}
        report['component_acceptance']={'DDT.COM':verdict}
    # Construct and validate both before publishing either named image.
    for name,data,report in reports:
        staged=output/(name+'.tmp');staged.write_bytes(data);staged.replace(output/name)
        (output/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(f'{output/name}: PROVISIONAL, {len(files)} files; {len(PENDING)} pending selections/implementations')
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/utilities-disks')
    p.add_argument('--artifacts',type=Path,default=ROOT)
    p.add_argument('--build',action='store_true',help='freshly build owned Utilities components first')
    p.add_argument('--ddt-acceptance',type=Path,help='bind a passing DDT campaign to these exact image hashes')
    a=p.parse_args()
    if a.build:
        for name in ['dump','ddt','batch','sq','usq','uncr']:subprocess.run([sys.executable,str(ROOT/'tools'/f'build_{name}.py')],cwd=ROOT,check=True)
    build(a.output.resolve(),a.artifacts.resolve(),a.ddt_acceptance)


if __name__=='__main__':main()
