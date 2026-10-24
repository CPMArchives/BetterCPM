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
    p.add_argument('--from-utilities',action='store_true',help='execute and hash-check the packaged B: tool set')
    p.add_argument('--scripted-input',action='store_true',help='also use the native line-input harness on z80pack')
    p.add_argument('--capacity-only',action='store_true',help='8 KiB input and source output across multiple extents')
    p.add_argument('--utility-only',action='store_true',help='round-trip the complete maintained DLINK executable as representative input')
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    binary=build(Path.home()/'bin/z80asm',a.output/'cross')
    if a.utility_only and a.capacity_only:p.error('choose one input selection')
    fixtures={'TOOL':(Path(__file__).resolve().parents[1]/'build/utilities/DLINK.COM').read_bytes()} if a.utility_only else {'MAX':bytes(8192)} if a.capacity_only else corpus()
    files={'DASM.COM':binary}
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
        scripted_input=platform=='trs80gp' or a.scripted_input
        if scripted_input:
            interactive=[]
            lines=[]
            for name,payload in fixtures.items():
                end=256+len(payload)
                lines += ['RIN'+name+'.COM',f'N{len(payload):X}','S'+name+'.ASM',
                          f'P100,{end:X}',f'QL100,{end:X}','Z']
            selected_files['QALL.COM']=scripted(binary,lines+['G'])
            commands += ['QALL']
            for name in fixtures:
                commands += [f'B:ZSM4 {name}={name}.ASM',f'B:LINK {name}[A]']
        if a.from_utilities:
            commands=[('B:'+c if c.startswith('DASM ') else c) for c in commands]
            interactive=[(b'B:DASM\r' if c==b'DASM\r' else c,w,t) for c,w,t in interactive]
        log,outputs=campaign(platform,selected_files,commands,a.output/platform,
                             system=a.system,utilities=a.utilities,interactive=interactive,
                             utility_files={'DASM.COM':binary} if a.from_utilities else None,
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
        report['platforms'][platform]={'status':'PASS','scripted_line_input':scripted_input,'keyboard_qualified':False,'cases':cases}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,len(cases),'native opcode/data reconstruction corpora',flush=True)


if __name__=='__main__':main()
