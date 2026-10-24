#!/usr/bin/env python3
"""Round-trip byte-enumerated DASM corpora with native ZSM4/LINK.

Uses disposable media. This is byte reconstruction qualification, distinct from
full release acceptance, physical hardware, or exhaustive decoder correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_dasm import build
from dasm_native import campaign, DEFAULT_SYSTEM
from test_dasm import corpus
from dasm_script_harness import scripted


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    binary=build(Path.home()/'bin/z80asm',a.output/'cross')
    fixtures=corpus();files={'DASM.COM':binary}
    files.update({'IN'+name+'.COM':payload for name,payload in fixtures.items()})
    report={'scope':'byte-enumerated native reconstruction; release acceptance pending',
            'dasm_sha256':hashlib.sha256(binary).hexdigest(),'platforms':{}}
    for platform in a.platforms:
        prompt=b'A0>_ ' if platform=='trs80gp' else b'C0>_ '
        interactive=[]
        for name,payload in fixtures.items():
            end=256+len(payload)
            for command in ['DASM','RIN'+name+'.COM',f'N{len(payload):X}',
                            'S'+name+'.ASM',f'P100,{end:X}',f'QL100,{end:X}','Z','G',
                            f'B:ZSM4 {name}={name}.ASM',f'B:LINK {name}[A]']:
                wanted=prompt if command=='G' or command.startswith('B:') else b'\r\n*'
                interactive.append(((command+'\r').encode(),wanted,120))
        selected_files=dict(files)
        commands=['DASM /VER']
        if platform=='trs80gp':
            interactive=[]
            for index,(name,payload) in enumerate(fixtures.items()):
                end=256+len(payload)
                selected_files[f'Q{index}.COM']=scripted(binary,[
                    'RIN'+name+'.COM',f'N{len(payload):X}','S'+name+'.ASM',
                    f'P100,{end:X}',f'QL100,{end:X}','Z','G'])
                commands += [f'Q{index}',f'B:ZSM4 {name}={name}.ASM',f'B:LINK {name}[A]']
        log,outputs=campaign(platform,selected_files,commands,a.output/platform,
                             system=a.system,utilities=a.utilities,interactive=interactive,
                             extract=[name+ext for name in fixtures for ext in ('.ASM','.COM')])
        errors=re.findall(rb'Errors: +([0-9]+)',log)
        assert errors and set(errors)=={b'0'},errors
        assert b'UNDEFINED SYMBOLS' not in log.upper()
        cases={}
        for name,payload in fixtures.items():
            actual=outputs[name+'.COM']
            assert actual[:len(payload)]==payload,(platform,name)
            assert len(actual)==(len(payload)+127)//128*128
            assert set(actual[len(payload):]) <= {26}
            cases[name]={'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
        report['platforms'][platform]={'status':'PASS','scripted_line_input':platform=='trs80gp','keyboard_qualified':False,'cases':cases}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,len(cases),'native opcode/data reconstruction corpora',flush=True)


if __name__=='__main__':main()
