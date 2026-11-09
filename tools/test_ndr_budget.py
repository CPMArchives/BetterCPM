#!/usr/bin/env python3
"""Measure NDR's complete allocation increase against the released 1.1.1 CCP."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-source', type=Path)
    args = parser.parse_args()
    source = (args.baseline_source.read_bytes() if args.baseline_source else
              subprocess.check_output(['git','show','v1.1.1:src/ccp/ccp.mac'], cwd=ROOT))
    output = ROOT/'build/ndr-budget'
    output.mkdir(parents=True, exist_ok=True)
    text = source.decode('ascii').replace('        CSEG\n        .PHASE  ',
          '        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
    baseline = assemble(Path.home()/'bin/z80asm', text, output/'baseline.bin',
                        output/'baseline.lst', 0xbb00)
    current = (ROOT/'build/ccp/ccp.bin').read_bytes()
    carrier = (ROOT/'build/rsx/NDR.RSX').read_bytes()
    allocated = lambda n: (n+255)&~255
    provider = int.from_bytes(carrier[14:16], 'little')
    increase = allocated(len(current))-allocated(len(baseline))
    total = provider+increase
    assert increase >= 0 and provider <= 768, (provider, increase, total)
    from system_layout import CONTEXT
    result = dict(profile=CONTEXT[0]['profile'] if CONTEXT else 'model4-default',
        baseline='v1.1.1', baseline_source_sha256=hashlib.sha256(source).hexdigest(),
        baseline_ccp_bytes=len(baseline), baseline_ccp_allocation=allocated(len(baseline)),
        ccp_bytes=len(current), ccp_allocation=allocated(len(current)),
        ccp_increase=increase, ndr_allocation=provider, total_increase=total,
        ndr_target=512, ndr_ceiling=768, status='PASS')
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))

if __name__ == '__main__': main()
