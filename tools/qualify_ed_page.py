#!/usr/bin/env python3
"""Compare T display and unchanged cursor with stock ED on stock CP/M."""
import hashlib
import json
import re
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
    parent=ROOT/'build/ed-development/page';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    body=b''.join(f'{i:02}\r\n'.encode() for i in range(70))
    cases=[(body,line) for line in [b'0P',b'P',b'2P',b'-V#P',b'50L-P',b'50L-2P',b'-P',b'#L-P',b'-V0P',b'2C0P',b'65536P']]
    for number,(body,line) in enumerate(cases):
        here=work/str(number);here.mkdir();disks=here/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(source,image)
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(oracle),'0:EDREF.COM'],cwd=here,check=True)
        seed=here/'seed.bin';seed.write_bytes(body+b'\x1a')
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),str(seed),'0:CASE.TXT'],cwd=here,check=True)
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDREF CASE.TXT\r',b'*',10),(b'#a\r',b'*',10),
            # Inline Ctrl-L emits intermediate * prompts. A separate B is a
            # barrier before T's keyboard-interruption polls can see new input.
            (b'B\r',b'    1: *',10),
            (line+b'\r',b'*',10),(b'i|\x1a\r',b'*',10),
            (b'E\r',b'A>',10),(b'BYE\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
        start=trace.index(b'*'+line+b'\r');start=trace.index(b'\n',start)+1
        finish=trace.index(b'*',start)
        actual=re.sub(rb' {0,4}[0-9]*: $',b'',trace[start:finish]).replace(b'\r\r\n',b'\r\n')
        c,_,call,_,run=context(1024,execution_limit=2000000);out=[];c.mem[5:8]=bytes((0xdb,254,0xc9))
        def io(port):
            if c.c==2:out.append(c.e);return 0
            assert c.c==11;return 0
        c.port_read=io
        for byte in body:c.c=byte;assert not call('EB_PUT')[0]
        call('EB_TOP');out.clear()
        (bad,flag),(text,cursor)=run(line);assert not bad,(line,flag)
        assert bytes(out)==actual,(line,bytes(out),actual)
        saved=here/'saved.txt'
        subprocess.run(['cpmcp','-f','ibm-3740',str(image),'0:case.txt',str(saved)],cwd=here,check=True)
        assert saved.read_bytes().rstrip(b'\x1a')==text[:cursor]+b'|'+text[cursor:]
        results.append({'body_hex':body.hex(),'command':line.decode(),'output_hex':actual.hex(),'cursor':cursor})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: {len(cases)} stock ED P displays and cursor positions match; {work}')


if __name__=='__main__':main()
