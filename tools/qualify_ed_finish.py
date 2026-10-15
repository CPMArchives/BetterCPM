#!/usr/bin/env python3
"""Compare in-memory command results/cursor with pinned stock ED on stock CP/M."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_ed_finish import setup
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    source=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    oracle=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
    assert hashlib.sha256(oracle.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    parent=ROOT/'build/ed-development/finish';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    body=b'One\r\ntwo\r\nlast'
    cases=[b'a',b'aW',b'Ua',b'#aB2CiX\x1a',b'2aBW',b'a2Cai!\x1a']
    for number,line in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        seed=here/'seed.txt';seed.write_bytes(body+b'\x1a')
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(seed),'0:CASE.TXT'],cwd=here,check=True)
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDREF CASE.TXT\r',b'*',10),(line+b'\r',b'*',10),
            (b'E\r',b'A>',10),
            (b'BYE\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
        saved=here/'saved.txt'
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        cpu,sym,call,state,run,writes,calls=setup(body)
        (bad,flag),_=run(line)
        assert not bad,(line,flag)
        assert call('EF_DRAIN')==(False,0)
        expected=b''.join(writes)
        actual=saved.read_bytes()
        assert actual==expected,(line,actual,expected)
        results.append({'command_hex':line.hex(),'output_hex':expected.hex()})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED completion data workflows match exact output records; {work}')


if __name__=='__main__':main()
