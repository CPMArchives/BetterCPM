#!/usr/bin/env python3
"""Build declared public-boundary conformance probes into a private test image."""
from pathlib import Path
import argparse,json,hashlib
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--image',type=Path,default=R/'build/compatibility/BetterCPM-Compatibility-Campaign.dmk');a=p.parse_args()
b=R/'build/compatibility/probes';b.mkdir(exist_ok=True)
raw=extract_raw(a.image.read_bytes());manifest={'seed':str(a.image),'seed_sha256':hashlib.sha256(a.image.read_bytes()).hexdigest(),'probes':{}}
for src,name in [('coremore','COREMORE'),('morechar','MORECHAR'),('setsys','SETSYS'),('faultmore','FAULTIO'),('bootmore','BOOTMORE'),('readerr','READERR')]:
 source=R/f'tests/fixtures/conformance/{src}.mac'
 data=assemble(Path('/Users/nathanael/bin/z80asm'),source.read_text(),b/(name+'.COM'),b/(src+'.lst'),0x100)
 add_file(raw,name+'.COM',data)
 manifest['probes'][name]={'source':str(source.relative_to(R)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'com_sha256':hashlib.sha256(data).hexdigest()}
output=b/'BetterCPM-Conformance-Probes.dmk';output.write_bytes(build(raw));manifest['image_sha256']=hashlib.sha256(output.read_bytes()).hexdigest();(b/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(output)
