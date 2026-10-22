#!/usr/bin/env python3
"""Test residue provenance, clean-build identity and comparison-only reference use."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from build_ddt_seed import build_seed

ROOT=Path(__file__).resolve().parents[1]
EXPECTED='d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/ddt-reproduction')
    p.add_argument('--inputs',type=Path,default=ROOT/'third_party/dri-ddt')
    p.add_argument('--cpmsim',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=p.parse_args()
    out=args.build.resolve()
    candidate=(out/'DDT-reproduced.COM').read_bytes()
    assert hashlib.sha256(candidate).hexdigest()==EXPECTED
    provenance=json.loads((out/'residue-provenance.json').read_text())
    assert len(provenance)==245
    seed=(out/'seed/pip.com').read_bytes()
    code=set(json.loads((out/'seed/initialized-code-offsets.json').read_text()))
    for item in provenance:
        assert item['seed_file_offset'] in code
        assert item['seed_file_offset']==item['file_offset']+0x700
        assert candidate[item['file_offset']]==seed[item['seed_file_offset']]
    wrong_stack=build_seed(args.inputs.resolve()/'reproduction',out/'negative-stack100',args.cpmsim,100)
    controls={}
    for name, image, bias in [('stack_100',wrong_stack,0x700),
                             ('work_origin_0600',seed,0x500)]:
        altered=bytearray(candidate)
        for item in provenance:
            i=item['file_offset']
            altered[i]=image[i+bias]
        count=sum(a!=b for a,b in zip(altered,candidate))
        assert count>0
        controls[name]=count
    assert controls['stack_100']==37
    # The comparison file is absent. A complete byte-identical candidate must
    # still be produced before the final verifier attempts to open that path.
    with tempfile.TemporaryDirectory(prefix='ddt-no-reference-',dir=out) as temp:
        temp=Path(temp)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_ddt_reproduction.py'),
                               '--inputs',str(args.inputs.resolve()),'--output',str(temp/'build'),
                               '--reference',str(temp/'ABSENT-DDT.COM'),
                               '--cpmsim',str(args.cpmsim.resolve())],capture_output=True)
        assert result.returncode!=0 and b'FileNotFoundError' in result.stderr
        independent=(temp/'build/DDT-reproduced.COM').read_bytes()
        assert independent==candidate
        (out/'generated-without-reference.COM').write_bytes(independent)
        (out/'missing-reference-control.log').write_bytes(result.stdout+result.stderr)
    report={'all_245_residue_bytes_from_compiler_initialized_code':True,
            'complete_build_identical_without_comparison_file':True,
            'candidate_sha256':EXPECTED,'negative_control_differing_bytes':controls,
            'historical_limit':'Memory state reconstructed; original DRI chronological command sequence not established.'}
    (out/'residue-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
