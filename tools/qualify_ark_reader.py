#!/usr/bin/env python3
"""Qualify the isolated ARC reader with pinned historical inputs on both targets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_ark_reader import build,ROOT
from qualify_noah_proof import verify_system
from dasm_native import campaign
from test_ark import member
from qualify_noah_codecs import native_match


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,default=ROOT/'build/ted-qualified-utilities')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output=a.output.resolve();a.system=a.system.resolve()
    a.output.mkdir(parents=True,exist_ok=False)
    systems=verify_system(a.system,('z80pack','trs80gp'))
    layout=build(a.output/'cross');cross=a.output/'cross';expected=(cross/'ARKPRF.COM').read_bytes()
    good=member(b'old stored',method=1,name=b'OLD.DAT')+member(bytes(range(256))+b'\0\x1a\xff',name=b'ALL.BIN')+b'\x1a\0'
    files={'ARKPRF.MAC':(cross/'ARKPRF.MAC').read_bytes(),
           'STORED.ARC':good,'TAIL.ARC':good+b'opaque trailer',
           'CRC.ARC':member(b'abc',crc=0)+b'\x1a\0','UNKNOWN.ARC':member(b'abc',method=10)+b'\x1a\0'}
    pins=json.loads((ROOT/'tests/fixtures/noah/references.json').read_text())['artifacts']
    historical={}
    for i,name in enumerate(('crc32a.arc','de-lbr.arc','nulu15.arc'),1):
        raw=(ROOT/'build/noah-proof/references'/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pins[name]['sha256']
        files[f'HIST{i}.ARC']=raw;historical[f'HIST{i}.ARC']=pins[name]
    report={'scope':'isolated ARC framing/stored CRC; compressed entries enumerated, not decoded',
            'layout':layout,'verified_systems':systems,'historical_inputs':historical,'platforms':{}}
    for platform in ('z80pack','trs80gp'):
        prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
        commands=['B:ZSM4 ARKPRF=ARKPRF','B:LINK ARKPRF[A]']+prefix+[
            'ARKPRF STORED.ARC','ARKPRF HIST1.ARC','ARKPRF HIST2.ARC','ARKPRF HIST3.ARC',
            'ARKPRF TAIL.ARC','ARKPRF CRC.ARC','ARKPRF UNKNOWN.ARC']
        log,outputs=campaign(platform,files,commands,a.output/platform,system=a.system,utilities=a.utilities,
                              extract=['ARKPRF.COM'],timeout=600)
        assert re.findall(rb'Errors: +([0-9]+)',log)==[b'0']
        native_match(outputs['ARKPRF.COM'],expected)
        results=re.findall(rb'ARK READER (?:PASS V=[0-9A-F]+ O=[0-9A-F]+ T=[0-9A-F]+|FAIL [0-9A-F]+)',log)
        wanted=[b'ARK READER PASS V=0002 O=0000 T=01',b'ARK READER PASS V=0000 O=0003 T=01',
                b'ARK READER PASS V=0000 O=0002 T=02',b'ARK READER PASS V=0000 O=0002 T=01',
                b'ARK READER PASS V=0002 O=0000 T=02',b'ARK READER FAIL 08',b'ARK READER FAIL 0D']
        assert results==wanted,(platform,results)
        ceiling='C501' if platform=='z80pack' else 'CA01'
        assert f'ARK READER TPA {ceiling} NEED {layout["required_ceiling"]:04X}'.encode() in log
        assert b'ARK READER STACK ERROR' not in log and b'ARK READER LOW TPA' not in log
        report['platforms'][platform]={'status':'PASS','native_cross_parity':True,'loaded_tpa_ceiling_hex':ceiling,
            'results':[x.decode() for x in results],'console_sha256':hashlib.sha256(log).hexdigest()}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'native reader/stored CRC, historical framing and explicit refusals',flush=True)

if __name__=='__main__':main()
