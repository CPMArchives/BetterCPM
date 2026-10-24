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
    parent=ROOT/'build/ed-development/juxtapose';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    cases=[b'iA old B A more B\x1aB'+tail for tail in [b'jA\x1aX\x1aB',b'2jA\x1aX\x1aB',b'3jA\x1aX\x1aB',b'jA\x1a\x1aB',b'jA\x1aX\x1aZ',b'jZ\x1aX\x1aB',b'0jA\x1aX\x1aB',b'j\x1aX\x1aB',b'jA\x1aX\x1a',b'jA\x1aX\x1aB\x1ai!\x1a']]
    cases.extend([b'iaa AA old BB\x1aBJaa\x1ax\x1abb',b'iaa AA old BB\x1aBUjaa\x1ax\x1abb',b'iA\x0cx\x0cB\x1aBjA\x1aNEW\x0c\x1aB'])
    for number,line in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDREF CASE.TXT\r',b'*',10),(line+b'\r',b'*',10),
            (b'i|\x1a\r',b'*',10),(b'E\r',b'A>',10),
            (b'BYE /Y\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
        saved=here/'saved.txt'
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        _,_,_,_,run=context(1024)
        (bad,flag),(text,cursor)=run(line)
        # Failed F preserves prior matches; still compare the resulting cursor.
        expected=text[:cursor]+b'|'+text[cursor:]
        actual=saved.read_bytes().rstrip(b'\x1a')
        # Preserve evidence of DRI's confirmed counted-J bug, not its output.
        dri_bugs={1:b'AXX|XB A more B',2:b'AXX|XXXXB A more B'}
        if number in dri_bugs:
            assert actual==dri_bugs[number],(line,actual)
            assert expected==b'AXB AX|B',(line,expected)
            assert bad==(number==2),(line,bad,flag)
        else:
            assert actual==expected,(line,actual,expected)
        results.append({'command_hex':line.hex(),'text_hex':text.hex(),'cursor':cursor,'dri_saved_hex':actual.hex(),'intentional_bug_correction':number in (1,2)})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} J workflows qualified: 11 DRI matches and two explicit counted-J bug corrections; {work}')


if __name__=='__main__':main()
