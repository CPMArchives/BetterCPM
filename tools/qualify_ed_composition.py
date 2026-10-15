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
    parent=ROOT/'build/ed-development/composition';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    cases=[b'iabcdef\x1aB'+tail for tail in (b'0V2C',b'0VB0V#C',b'2m0VC',b'0V2DiX\x1a',b'0V?')]
    cases += [b'ione\x0ctwo\x0cthree\x1aB'+tail for tail in (b'3:',b'3:1:',b'2:2C2:',b'2:2C:2K',b':3K',b'3::1K',b'0:',b'99:',b'-2:',b'2m2:1:',b'2:0V3:')]
    for number,line in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        setup,separator,command=line.partition(b'\x1aB')
        assert separator
        setup+=separator
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDREF CASE.TXT\r',b'*',10),(setup+b'\r',b'*',10),
            (b'B\r',b'    1: *',10),(command+b'\r',b'*',10),
            (b'i|\x1a\r',b'*',10),(b'E\r',b'A>',10),
            (b'BYE\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
        saved=here/'saved.txt'
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        cpu,_,_,_,run=context(1024)
        cpu.mem[5:8]=bytes((0xdb,254,0xc9))
        def io(port):
            assert cpu.c in (2,11),cpu.c
            return 0
        cpu.port_read=io
        (bad,flag),(text,cursor)=run(line)
        # Capacity depends on allocation; compare subsequent edits and cursor,
        # including state retained before a later command error.
        expected=text[:cursor]+b'|'+text[cursor:]
        actual=saved.read_bytes().rstrip(b'\x1a')
        assert actual==expected,(line,actual,expected)
        results.append({'command_hex':line.hex(),'text_hex':text.hex(),'cursor':cursor})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED command compositions match text and cursor; {work}')


if __name__=='__main__':main()
