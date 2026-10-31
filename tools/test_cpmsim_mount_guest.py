#!/usr/bin/env python3
"""Run the assembled MOUNT.COM in real cpmsim with a minimal BDOS adapter."""
import argparse, os, pty, select, signal, subprocess, tempfile, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
a=p.parse_args();source=a.source.resolve();sim=source/'cpmsim/cpmsim'
stub="        org 5000h\n        lxi sp,7000h\n        call 100h\n        mvi a,1\n        out 10\n        xra a\n        out 11\n        out 15\n        mvi a,80h\n        out 16\n        mvi a,1\n        out 12\n        xra a\n        out 13\n        mvi a,'['\n        out 1\n        in 14\n        adi '0'\n        out 1\n        lda 8000h\n        out 1\n        mvi a,']'\n        out 1\n        mvi a,'!'\n        out 1\n        mvi a,0aah\n        out 0a0h\n        mvi a,80h\n        out 0a0h\n        org 6000h\nbdos:   mov a,c\n        cpi 2\n        jz char\n        cpi 9\n        jz string\n        cpi 1\n        jz input\n        ret\nchar:   mov a,e\n        out 1\n        ret\nstring: ldax d\n        cpi '$'\n        rz\n        out 1\n        inx d\n        jmp string\ninput:  in 0\n        ora a\n        jz input\n        in 1\n        ret\n        end\n"
with tempfile.TemporaryDirectory() as tmp:
    w=Path(tmp);(w/'disks').mkdir();(w/'Image.dsk').write_bytes(b'A'*128)
    (w/'stub.asm').write_text(stub)
    subprocess.run([str(source/'z80asm/z80asm'),'-8','-fb','-o'+str(w/'stub.bin'),str(w/'stub.asm')],check=True,capture_output=True)
    for tail,answer,expected in [('/VER',None,b'001-dev'),('/U',None,b'Invalid syntax'),
                                ('/U [A,B,C]:',b'n',b'Operation cancelled. No changes made.'),
                                ('/U [A,B,C]:',b'Y',b'C: unmounted'),
                                ('B: Image.dsk',None,b'Image.dsk'),
                                ('/HELP',None,b'working directory')]:
        mem=bytearray(0x6100);mem[5:8]=bytes.fromhex('c30060')
        guest=(source/'cpmtools/mount.com').read_bytes();mem[0x100:0x100+len(guest)]=guest
        code=(w/'stub.bin').read_bytes();mem[0x5000:0x5000+len(code)]=code
        data=tail.encode();mem[0x80]=len(data);mem[0x81:0x81+len(data)]=data
        (w/'probe.bin').write_bytes(bytes.fromhex('ff0000')+mem)
        # -x loads at zero. Execute entry via a jump at zero.
        mem[:3]=bytes.fromhex('c30050');(w/'probe.bin').write_bytes(bytes.fromhex('ff0000')+mem)
        pid,terminal=pty.fork()
        if pid==0:
            os.chdir(w);env=dict(os.environ);env['PATH']=str(sim.parent/'srctools')+os.pathsep+env.get('PATH','')
            os.execve(sim,[str(sim),'-z','-d',str(w/'disks'),'-x',str(w/'probe.bin')],env)
        output=bytearray();sent=False;deadline=time.monotonic()+10
        try:
            while b'!' not in output:
                assert time.monotonic()<deadline,bytes(output)
                if select.select([terminal],[],[],0.2)[0]:
                    try:chunk=os.read(terminal,65536)
                    except OSError:break
                    if not chunk:break
                    output.extend(chunk)
                    if answer and b'[y/N]' in output and not sent:
                        os.write(terminal,answer);sent=True
            assert expected in output,(tail,bytes(output))
            assert b'!' in output,(tail,bytes(output))
            if tail == 'B: Image.dsk': assert b'[0A]' in output,bytes(output)
            if tail == '/U [A,B,C]:' and answer == b'Y': assert b'[5' in output,bytes(output)
            os.waitpid(pid,0)
        finally:
            try:os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:pass
            os.close(terminal)
print('PASS: real guest execution, help/version, syntax errors, A: accept/cancel and command return')
