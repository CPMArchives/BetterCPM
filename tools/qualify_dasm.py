#!/usr/bin/env python3
"""Native build, symbol conversion and small round-trip integration gate.

This gate is deliberately separate from the full release acceptance campaign.
It does not assert completion of every requirement in DASM Specification.md.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_dasm import source, build
from build_dsym import source as dsym_source, build as build_dsym
from dasm_native import campaign, cpm_text, compact_source, DEFAULT_SYSTEM

ROOT=Path(__file__).resolve().parents[1]


def native_source(text):
    text=re.sub(r'(?mi)^(\s*(?:\w+:)?)[ \t]+(?:DEFS|DS)[ \t]+([^;\n]+)(?:;[^\n]*)?$',
                r'\1\n REPT \2\n DB 0FFH\n ENDM',text)
    return cpm_text(compact_source(text))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    cross=build(Path.home()/'bin/z80asm',a.output/'cross')
    converter=build_dsym(Path.home()/'bin/z80asm',a.output/'cross')
    files={'DASM.MAC':native_source(source()),'DSYM.MAC':native_source(dsym_source()),
           'SYMTEST.MAC':cpm_text(' CSEG\n PUBLIC START,HELLO\nSTART: LD DE,HELLO\n RET\n DSEG\nHELLO: DB 0\n END\n')}
    commands=['B:ZSM4 DASM=DASM','B:LINK DASM[A]','B:ZSM4 DSYM=DSYM','B:LINK DSYM[A]',
              'B:ZSM4 SYMTEST=SYMTEST','B:LINK SYMTEST[A]','DSYM SYMTEST.SYM','DASM /VER']
    report={'status':'IN_PROGRESS','scope':'native integration gate; full release acceptance pending',
            'cross_sha256':hashlib.sha256(cross).hexdigest(),'converter_sha256':hashlib.sha256(converter).hexdigest(),
            'platforms':{}}
    for platform in a.platforms:
        prompt=b'A0>_ ' if platform=='trs80gp' else b'C0>_ '
        interactive=[(b'DASM\r',b'\r\n*',30),(b'RSYMTEST.COM\r',b'\r\n*',30),
                     (b'N5\r',b'\r\n*',30),(b'RSYMTEST.DSY\r',b'\r\n*',30),
                     (b'C104,H\r',b'\r\n*',30),(b'SROUND.ASM\r',b'\r\n*',30),
                     (b'P100,105\r',b'\r\n*',30),(b'QL100,105\r',b'\r\n*',30),
                     (b'Z\r',b'\r\n*',30),(b'G\r',prompt,30),
                     (b'B:ZSM4 ROUND=ROUND.ASM\r',prompt,30),
                     (b'B:LINK ROUND[A]\r',prompt,30)]
        log,out=campaign(platform,files,commands,a.output/platform,system=a.system,
                         utilities=a.utilities,interactive=interactive,
                         extract=['DASM.COM','DSYM.COM','SYMTEST.COM','SYMTEST.DSY','ROUND.ASM','ROUND.COM'])
        errors=re.findall(rb'Errors: +([0-9]+)',log)
        # A native screenshot retains earlier lines; assess final build screen
        # separately instead of counting duplicated screen contents as builds.
        if platform=='z80pack':assert errors==[b'0']*4,errors
        else:assert errors and set(errors)=={b'0'},errors
        assert b'UNDEFINED SYMBOLS' not in log.upper()
        for name,expected in [('DASM.COM',cross),('DSYM.COM',converter)]:
            raw=out[name]
            assert raw[:len(expected)]==expected,(platform,name,'native/cross mismatch')
            assert len(raw)==(len(expected)+127)//128*128
            assert set(raw[len(expected):]) <= {26}
        assert out['SYMTEST.DSY'].split(b'\x1a',1)[0]==b'0104 HELLO\r\n0100 START\r\n'
        expected=bytes.fromhex('110401c900')
        assert out['SYMTEST.COM'][:5]==expected
        assert out['ROUND.COM'][:5]==expected,(platform,out['ROUND.ASM'],out['ROUND.COM'])
        assert len(out['ROUND.COM'])==128
        assert set(out['ROUND.COM'][5:]) <= {26}
        assert b'ASEG' in out['ROUND.ASM'] and b'HELLO' in out['ROUND.ASM']
        report['platforms'][platform]={'status':'PASS','native_cross_parity':True,
            'symbol_conversion':True,'round_trip_bytes':5,'logical_bytes':expected.hex(),
            'execution_report':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'native build, symbol conversion and 5-byte round trip',flush=True)
    report['status']='PASS'
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
