#!/usr/bin/env python3
"""Compare in-memory command results/cursor with pinned stock ED on stock CP/M."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_ed_buffer import context
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    source=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    oracle=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
    assert hashlib.sha256(oracle.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    parent=ROOT/'build/ed-development/substitute';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    cases=[b'ione one\x1aB'+tail for tail in [b'sone\x1atwo',b'2sone\x1aX',b'3sone\x1aX',b'sone\x1a',b'smissing\x1aX',b'0sone\x1aX',b's\x1aX',b'sone\x1aX\x1asone\x1aY']]
    cases.extend([b'iMixed MIXED\x1aBSmixed\x1anew',b'iMixed MIXED\x1aBUsmixed\x1anew',b'iA\x0cB\x1aBsA\x0cB\x1aX\x0cY'])
    cases.extend([b'ix\x1aB0s'+b'a'*50+b'\x1a'+b'b'*n for n in (49,50)])
    for number,line in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDREF CASE.TXT\r',b'*',10),(line+b'\r',b'*',10),
            (b'i|\x1a\r',b'*',10),(b'E\r',b'A>',10),
            (b'BYE\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
        saved=here/'saved.txt'
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        _,_,_,_,run=context(1024)
        (bad,flag),(text,cursor)=run(line)
        # Failed F preserves prior matches; still compare the resulting cursor.
        expected=text[:cursor]+b'|'+text[cursor:]
        actual=saved.read_bytes().rstrip(b'\x1a')
        assert actual==expected,(line,actual,expected)
        results.append({'command_hex':line.hex(),'text_hex':text.hex(),'cursor':cursor})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED S substitution workflows match text and cursor; {work}')


if __name__=='__main__':main()
