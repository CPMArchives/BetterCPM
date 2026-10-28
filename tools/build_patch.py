#!/usr/bin/env python3
"""Build PATCH's bounded-memory verified binary replacement utility."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
from build_ccp import assemble
from component_build import recorded_build
from component_identity import identification, title
from utility_versions import identities, display_development
ROOT=Path(__file__).resolve().parents[1]


def expanded_source():
    text=(ROOT/'src/utilities/patch.mac').read_text()
    for name in ('command','scan','engine','transaction'):
        text=text.replace('; @'+name+'@',(ROOT/f'src/utilities/patch/{name}.inc').read_text())
    common=ROOT/'src/utilities/common'
    parser=(common/'compareparse.inc').read_text()
    parser=parser[:parser.index('PARSE:\n')]
    helpers=(ROOT/'src/utilities/compare.mac').read_text()
    helpers=helpers[helpers.index('COPY32:\n'):helpers.index('STAT:\n')]
    io=(common/'compareio.inc').read_text()
    get=io[io.index('GETBYTE:\n'):]
    selector=(common/'duselect.inc').read_text()+'\n'+(common/'filespec.inc').read_text()
    text=text.replace('; @shared@',parser+'\n'+helpers+'\n'+get)
    md=(ROOT/'src/utilities/md5sum/algorithms.inc').read_text()
    rows=['MDSCHEDULE:']
    shifts=((7,12,17,22),(5,9,14,20),(4,11,16,23),(6,10,15,21))
    for i in range(64):
        k=i if i<16 else ((5*i+1)%16 if i<32 else ((3*i+5)%16 if i<48 else (7*i)%16))
        vals=[4*k,shifts[i//16][i%4],*int(abs(math.sin(i+1))*(1<<32)).to_bytes(4,'little')]
        rows.append('        DB '+','.join(f'0{x:02X}H' for x in vals))
    md=md.replace('; @md5-schedule@','\n'.join(rows))
    text=text.replace('; @fingerprint@',md).replace('; @selectors@',selector)
    version,rev=identities()['PATCH']
    dev=display_development('utility:PATCH')
    identity=identification('PATCH',version,rev,'Verified Binary Patching',development=dev)
    helptext=(title('PATCH',version,rev,development=dev)+'\n  - - -\n | Verified binary file replacements\n |\n'
        ' |   Usage: PATCH patchfile [options]\n\n   Options:\n'
        '     /INPUT=file  Override original input.\n'
        '     /OUTPUT=file Override separate output.\n'
        '     /VERBOSE     Show instruction validation details.\n\n'
        '     /HELP        Display this help.\n'
        '     /VER         Display utility identification.\n')
    def string(label,value):
        return label+':\n'+''.join("        DB '"+line.replace("'","''")+"',13,10\n" if line else '        DB 13,10\n' for line in value.splitlines())+'        DB 0\n'
    return text.replace('; @identity@',string('VERSIONTEXT',identity)+string('HELPTEXT',helptext))


@recorded_build('utility:PATCH')
def build(assembler,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    text=expanded_source()
    cross=text.replace('        CSEG\n','        ASEG\n').replace('        .PHASE 0103H\n','        ORG 0103H\n').replace('        .DEPHASE\n','')
    data=b'\xc3\x03\x01'+assemble(assembler,cross,destination/'patch.bin',destination/'patch.lst',0x103)
    (destination/'PATCH.COM').write_bytes(data)
    native=re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',r'\1\n        REPT \2\n        DB 0FFH\n        ENDM',text)
    prepared=native.replace('\n','\r\n').encode('ascii')+b'\x1a'
    (destination/'PATCH-NATIVE.MAC').write_bytes(prepared)
    (destination/'PATCH-native.json').write_text(json.dumps({'binary_sha256':hashlib.sha256(data).hexdigest(),'native_source_sha256':hashlib.sha256(prepared).hexdigest()},indent=2)+'\n')
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm');a=p.parse_args()
    data=build(a.assembler,ROOT/'build/utilities')
    print(f'PATCH.COM: {len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')
