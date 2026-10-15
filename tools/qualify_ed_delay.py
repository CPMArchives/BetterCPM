#!/usr/bin/env python3
"""Compare Z/0Z/macro-delay command outcomes and diagnostics with pinned ED."""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_ed_page_delay import machine
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    template=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(template.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    oracle=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
    assert hashlib.sha256(oracle.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    parent=ROOT/'build/ed-development/delay';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    results=[]
    cases=[(b'Z',None,False),(b'2Z',None,False),(b'-Z',None,False),
           (b'0Z',ord('x'),False),(b'0Z',26,False),(b'2mZ',None,False),(b'Z',ord('x'),True)]
    for number,(line,key,interrupt) in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(template,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        commands=[(b'EDREF CASE.TXT\r',b'*',10)]
        if line==b'0Z':commands.extend([(line+b'\r',b'0Z\r\n',10),(bytes([key]),b'*',10)])
        else:commands.append((line+b'\r'+(bytes([key]) if interrupt else b''),b'*',10))
        commands.extend([(b'Q\r',b'(Y/N)?',10),(b'Y',b'A>',10),(b'BYE\r',b'System halted',10)])
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin',initial_prompt=b'A>')
        c,s,call,state,run,out,polls=machine(ready_after=0 if interrupt else None,key=key if key is not None else ord('x'))
        (bad,flag),_=run(line)
        if bad:
            shown=b'^'+bytes([flag+64]) if flag<32 else bytes([flag])
            match=re.search(rb'BREAK "(.*?)" AT Z',trace)
            assert match,(line,trace)
            if flag:assert match.group(1)==shown,(line,trace)
            # DRI FLAG is uninitialized until a prior error assigns it.
            # BetterCP/M initializes it; do not freeze stale TPA bytes as UI.
            results.append({'command_hex':line.hex(),'key':key,'new_flag':flag,'oracle_flag_hex':match.group(1).hex()})
        else:assert b'BREAK' not in trace,(line,trace)
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED Z count/key/interruption/macro outcomes; {work}')


if __name__=='__main__':main()
