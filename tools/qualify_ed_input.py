#!/usr/bin/env python3
"""Compare interactive insertion text with stock ED, pacing retype/backspace."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_ed_input import insert
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    source=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    oracle=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
    assert hashlib.sha256(oracle.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    parent=ROOT/'build/ed-development/input';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    bs=b'\x08 \x08'
    cases=[('line',False,[(b'abc\rdef',b'def')]),
           ('lf',False,[(b'abc\ndef',b'def')]),
           ('wipe',False,[(b'abc',b'abc'),(b'\x15',b'    1:  '),(b'def',b'def')]),
           ('clear',False,[(b'abc',b'abc'),(b'\x18',bs),(b'def',b'def')]),
           ('rubout',False,[(b'abc',b'abc'),(b'\x7f',b'c'),(b'd',b'd')]),
           ('backspace',False,[(b'abc',b'abc'),(b'\x08',bs),(b'd',b'd')]),
           ('retype',False,[(b'abc',b'abc'),(b'\x12',b'    1:  abc'),(b'd',b'd')]),
           ('tab',False,[(b'A\tB',b'B')]),
           ('formfeed',False,[(b'A\x0cB',b'B')]),
           ('upper',True,[(b'Mixed',b'Mixed')]),
           ('wipe-second',False,[(b'abc\rdef',b'def'),(b'\x15',b'    2:  '),(b'gh',b'gh')]),
           ('backspace-tab',False,[(b'ab\tX',b'X'),(b'\x08',bs),(b'\x08',bs),(b'Q',b'Q')]),
           ('backspace-start',False,[(b'\x08a',b'a')]),
           ('nul',False,[(b'\x00abc',b'abc')]),
           ('control-e',False,[(b'A\x05B',b'B')]),
           ('rubout-lf',False,[(b'abc\r\x7fX',b'X')])]
    for name,upper,steps in cases:
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        commands=[(b'EDREF CASE.TXT\r',b'*',10),((b'I' if upper else b'i')+b'\r',b'    1:  ',10)]
        commands += [(data,wanted,10) for data,wanted in steps]
        commands += [(b'\x1a',b'     : *',10),(b'E\r',b'A>',10),(b'BYE /Y\r',b'System halted',10)]
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin',initial_prompt=b'A>')
        saved=here/'saved.txt';subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        keys=b''.join(data for data,_ in steps)+b'\x1a'
        result,(text,cursor),_=insert(keys,upper=upper)
        assert result==(False,1)
        actual=saved.read_bytes().rstrip(b'\x1a')
        assert actual==text and cursor==len(text),(name,actual,text,cursor)
        results.append({'case':name,'keys_hex':keys.hex(),'text_hex':text.hex()})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} interactive insert workflows match stock ED saved text; {work}')


if __name__=='__main__':main()
