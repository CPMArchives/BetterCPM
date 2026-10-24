#!/usr/bin/env python3
"""Native checked-LINK report and multi-module conversion qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from build_dlink import build as build_link, source as link_source
from build_dsym import build as build_sym, source as sym_source
from dasm_native import campaign,cpm_text,DEFAULT_SYSTEM
from qualify_dasm import native_source
from dsym_reference import convert_log

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    launcher=build_link(Path.home()/'bin/z80asm',a.output/'cross')
    converter=build_sym(Path.home()/'bin/z80asm',a.output/'cross')
    files={'DLINK.MAC':native_source(link_source()),'DSYM.MAC':native_source(sym_source()),
        'ONE.MAC':cpm_text(' CSEG\n PUBLIC START,ZERO,ALIAS,LONGSYMBOLAA\n EXTRN HELLO\nZERO EQU 0\nSTART: LD DE,HELLO\n RET\nALIAS EQU START\nLONGSYMBOLAA EQU START\n END\n'),
        'TWO.MAC':cpm_text(' CSEG\n PUBLIC TARGET,LAST,HELLO\nTARGET: RET\nLAST EQU 0FFFFH\n DSEG\nHELLO: DB 0A5H\n END\n'),
        'BAD.MAC':cpm_text(' CSEG\n PUBLIC START\n EXTRN MISSIN\nSTART: JP MISSIN\n END\n'),
        'LONG.MAC':cpm_text(' CSEG\n PUBLIC LONGSYMBOLAA,LONGSYMBOLBB\nLONGSYMBOLAA: NOP\nLONGSYMBOLBB: RET\n END\n')}
    commands=['B:ZSM4 DLINK=DLINK','B:LINK DLINK[A]','B:ZSM4 DSYM=DSYM','B:LINK DSYM[A]',
        'B:ZSM4 ONE=ONE','B:ZSM4 TWO=TWO','DLINK PASS ONE TWO','DSYM PASS.LOG',
        'B:ZSM4 BAD=BAD','DLINK BAD','DSYM BAD.LOG',
        'B:ZSM4 LONG=LONG','DLINK LONG','DSYM LONG.LOG']
    report={'scope':'checked native link/map conversion; full Utilities acceptance pending','platforms':{}}
    names=['DLINK.COM','DSYM.COM','PASS.COM','PASS.LOG','PASS.DSY','ONE.REL','TWO.REL','BAD.REL','BAD.LOG','LONG.REL','LONG.LOG']
    expected=b'0100 ALIAS\r\n0105 HELLO\r\nFFFF LAST\r\n0100 LONGSY\r\n0100 START\r\n0104 TARGET\r\n0000 ZERO\r\n\x1a'
    for platform in a.platforms:
        log,outputs=campaign(platform,files,commands,a.output/platform,system=a.system,utilities=a.utilities,extract=names)
        errors=re.findall(rb'Errors: +([0-9]+)',log)
        assert errors and set(errors)=={b'0'},errors
        for name,binary in [('DLINK.COM',launcher),('DSYM.COM',converter)]:
            raw=outputs[name]
            assert raw[:len(binary)]==binary,(platform,name,'native/cross mismatch')
            assert len(raw)==(len(binary)+127)//128*128 and set(raw[len(binary):])<={26}
        assert convert_log(outputs['PASS.LOG'])==expected,outputs['PASS.LOG']
        assert outputs['PASS.DSY'].split(b'\x1a',1)[0]==expected[:-1]
        logical=bytes.fromhex('110501c9c9a5')
        assert outputs['PASS.COM'][:6]==logical and set(outputs['PASS.COM'][6:])<={26}
        for name in ('BAD','LONG'):
            try:convert_log(outputs[name+'.LOG'])
            except ValueError:pass
            else:raise AssertionError(('failed link accepted',name))
        w=a.output/platform
        definition='dasm-system' if platform=='trs80gp' else 'bettercpm-default'
        listing=subprocess.run(['cpmls','-T','raw','-f',definition,'system.raw'],cwd=w,check=True,capture_output=True).stdout.upper()
        assert b'BAD.DSY' not in listing and b'LONG.DSY' not in listing,listing
        report['platforms'][platform]={'status':'PASS','native_cross_parity':True,'multi_module_logical_bytes':logical.hex(),
            'final_symbols':expected.decode('ascii'),'unresolved_rejected':True,'significance_collision_rejected':True,
            'launcher_sha256':hashlib.sha256(launcher).hexdigest(),'converter_sha256':hashlib.sha256(converter).hexdigest(),
            'execution_report':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'native checked LINK, final-address report conversion and failed-link rejection',flush=True)
if __name__=='__main__':main()
