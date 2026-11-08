"""Select the frozen integrated TCAP 2.0 personalities for release media."""
from pathlib import Path
import argparse
import json
from build_integrated_display import build

ROOT=Path(__file__).resolve().parents[1]


def release_modules(platform, assembler=None):
    reports={}
    destination=ROOT/'build/rsx'
    destination.mkdir(parents=True,exist_ok=True)
    for personality in ('ADM3A','VT52','ANSI'):
        carrier, report=build(ROOT,ROOT/'build/release-tcap'/personality,
                             platform,personality,assembler,inline_cache=True)
        (destination/(personality+'.RSX')).write_bytes(carrier)
        reports[personality]=report
    (destination/'TCAP-2.0.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--platform',choices=('cpmsim','model4','model2'),required=True)
    p.add_argument('--assembler',type=Path)
    a=p.parse_args();release_modules(a.platform,a.assembler)
