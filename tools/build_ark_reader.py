#!/usr/bin/env python3
"""Build the isolated ARC reader/CP-M adapter proof, not production NOAH."""
import argparse
import hashlib
import json
from pathlib import Path
from noah_overlays import assemble,native_export

ROOT=Path(__file__).resolve().parents[1]


def build(out):
    out.mkdir(parents=True,exist_ok=True)
    files={n:(ROOT/'src/archive'/n).read_text() for n in ('archive.inc','ark.inc','ark.mac','cpmfile.inc','cpmfile.mac')}
    ark=files['ark.mac'].replace('ARK_CODE MACRO\n','').replace('        ENDM\n','')
    adapter=files['cpmfile.mac'].replace('ARCHIVE_CPM_CODE MACRO\n','').replace('        ENDM\n','')
    # Local symbol binding only; the maintained CP/M adapter is unchanged.
    aliases='LBR_OPEN EQU ARK_OPEN\nLBR_CLOSE EQU ARK_CLOSE\nLB_STORE32 EQU AR_STORE32\n'
    source=(ROOT/'tools/ark_reader/proof.mac').read_text()
    source=source.replace('; @definitions@','\n'.join(files[n] for n in ('archive.inc','ark.inc','cpmfile.inc')))
    source=source.replace('; @code@',ark+'\n'+aliases+adapter)
    raw,sy=assemble(Path.home()/'bin/z80asm',out,'ARKPRF',source)
    (out/'ARKPRF.MAC').write_bytes(native_export(source))
    (out/'ARKPRF.COM').write_bytes(raw)
    report={'scope':'isolated ARK reader/stored-CRC proof; not production CLI/codec/writer integration',
        'image_bytes':len(raw),'required_ceiling':sy['IMAGE_END'],
        'context_bytes':138,'adapter_bytes':178,'private_stack_bytes':512,
        'library_bytes':sy['AC_OPEN']-sy['ARK_OPEN'],
        'image_sha256':hashlib.sha256(raw).hexdigest()}
    (out/'layout.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'build/ark-reader/proof')
    print(json.dumps(build(p.parse_args().output),indent=2))
