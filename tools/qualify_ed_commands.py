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
    parent=ROOT/'build/ed-development/commands';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    cases=[b'iHello world\x1aB2C2DiXX\x1a',b'IHello\x1aiWorld\x1a',
           b'UiMixed\x1a-UiCase\x1a',b'iabc',b'iA\x0cB\x1a',
           b'iabc\x1aB#C',b'iabc\x1a-#D',b'iabc\x1aB65536C',
           b'iabc\x1a0B',b'iabc\x1aB2C-1D',
           *[b'ione\x0ctwo\x0cthree\x1a'+tail for tail in
             [b'BL',b'B2L2C0L',b'B2L2C-L',b'B2L2C0K',b'B2L2C-K',b'B2K',b'B#L-#K']],
           b'iabc\x1aB#L',b'iabc\x1aB#K']
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
        assert not bad,(line,flag)
        expected=text[:cursor]+b'|'+text[cursor:]
        actual=saved.read_bytes().rstrip(b'\x1a')
        assert actual==expected,(line,actual,expected)
        results.append({'command_hex':line.hex(),'text_hex':text.hex(),'cursor':cursor})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED command/case/count workflows match text and cursor; {work}')


if __name__=='__main__':main()
