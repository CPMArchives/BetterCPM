#!/usr/bin/env python3
"""Compare shared executable bodies against the established flat-RAM target."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from build_distribution import prepare_profile,source_identity
from build_profiles import PROFILES,context_environment

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--altair-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    profile=PROFILES['cpmsim-fullram'];identity=source_identity(profile)
    root=prepare_profile(out/'comparison','z80pack',identity,profile)
    env=context_environment(root/'build/profile/context.json',root/'src/system/layout.inc')
    env['BETTERCPM_IDENTITY_STATE']='assigned'
    with (out/'build.log').open('w') as log:
        for name in ('bdos','ccp','rcp_cpx','fileloader'):
            subprocess.run([sys.executable,'-B',str(root/'tools'/f'build_{name}.py')],cwd=root,env=env,
                           stdout=log,stderr=subprocess.STDOUT,check=True)
    results=[]
    for relative in ('build/bdos/bdos.bin','build/ccp/ccp.bin','build/cpx/rcp.bin','build/system/fileloader.bin'):
        left=(root/relative).read_bytes();right=(a.altair_root/relative).read_bytes()
        assert left==right,'shared executable body differs: '+relative
        results.append({'artifact':relative,'bytes':len(left),'sha256':hashlib.sha256(left).hexdigest(),'status':'IDENTICAL'})
    baseline='55612e001027bce02978d1cd010ee56e63549402'
    sources={}
    for folder in ('src/bdos','src/ccp','src/cpx'):
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file():continue
            relative=str(path.relative_to(ROOT))
            expected=subprocess.check_output(['git','show',baseline+':'+relative],cwd=ROOT)
            assert expected==path.read_bytes(),'changed released core input: '+relative
            sources[relative]=hashlib.sha256(expected).hexdigest()
    report={'status':'PASS','mainline_base':baseline,'artifacts':results,'unchanged_core_sources':sources,
            'reuse_boundary':'Existing 1.3 shared BDOS/CCP/RCP behavior evidence applies to identical executable bodies. Altair BIOS, controller, boot and error paths require separate platform evidence; this is not 627 newly executed suite passes.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Altair BDOS, CCP, RCP and protected file-loader bodies are byte-identical to cpmsim-fullram')


if __name__=='__main__':main()
