#!/usr/bin/env python3
"""Verify Altair physical-error DMA preservation, media changes and BIOS routing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from altair_media import image,DISKDEFS
from build_ccp import assemble
from build_z80pack_image import symbols
from test_altair_system import Terminal
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]
PROBE='''        ASEG
        ORG 0100H
        LD SP,01F00H
        LD HL,(1)
        DEC HL
        DEC HL
        DEC HL
        LD (MPBASE),HL
        CALL FILL
        LD BC,1
        LD E,0
        LD A,27
        CALL RAW
        LD BC,0
        LD A,30
        CALL RAW
        LD BC,0
        LD A,33
        CALL RAW
        LD BC,02000H
        LD A,36
        CALL RAW
        LD A,39
        CALL RAW
        OR A
        JP @READ_CONDITION@,FAIL
@READ_CHECK@
        CALL FILL
        LD BC,0
        LD A,42
        CALL RAW
        OR A
        JP Z,FAIL
        CALL CHECK
        LD DE,OK
        JR REPORT
FAIL:   LD DE,BAD
REPORT: LD C,9
        CALL 5
        JP 0
FILL:   LD HL,02000H
        LD DE,02001H
        LD BC,127
        LD (HL),0A5H
        LDIR
        RET
CHECK:  LD HL,02000H
        LD B,128
CKLOOP: LD A,(HL)
        CP 0A5H
        JP NZ,FAIL
        INC HL
        DJNZ CKLOOP
        RET
RAW:    LD HL,(MPBASE)
        LD E,A
        LD D,0
        ADD HL,DE
        JP (HL)
MPBASE: DW 0
OK: DB 'ALTAIR PHYSICAL ERROR DMA PASS',13,10,'$'
BAD: DB 'ALTAIR PHYSICAL ERROR DMA FAIL',13,10,'$'
        END
'''


def routes(build):
    data=(build/'bios.bin').read_bytes();sy=symbols(build/'bios.lst');base=sy['BIOS']
    cpu=Z80(b'');cpu.mem[base:base+len(data)]=data;cpu.sp=0xb000
    wire=[];keys=[]
    def read(port):
        if port&255==16:return 2+bool(keys)
        assert port&255==17 and keys
        return keys.pop(0)
    def write(port,value):
        assert port&255==17
        wire.append(value)
    cpu.port_read=read;cpu.port_write=write;cpu.run(base+72)
    for byte in range(256):
        cpu.mem[3]=byte;console=byte&3;listing=byte>>6
        for offset,emits in ((12,console==1 or (console==2 and listing==1)),(15,listing==1),(18,False)):
            for value in (65,9,16):
                wire.clear();cpu.c=value;cpu.run(base+offset)
                assert wire==([value] if emits else []),(byte,offset,wire)
        keys[:]=[0xe1]
        for offset,expected in ((6,255 if console==1 else 0),(6,255 if console==1 else 0),(21,26),(45,255 if listing==1 else 0)):
            cpu.run(base+offset);assert cpu.a==expected and keys==[0xe1]
        cpu.run(base+9);assert cpu.a==(0x61 if console==1 else 26)
        keys.clear();cpu.run(base+6);assert cpu.a==0
    return {'status':'PASS','iobyte_values':256,'scope':'unaltered emitted BIOS with simulated 88-2SIO status/data ports'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    src=a.image_dir.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    master=(src/'disks/drivea.dsk').read_bytes();results=[]
    def work(name):
        w=out/name;w.mkdir();shutil.copytree(src/'disks',w/'disks')
        for n in ('system.conf','diskdefs'):shutil.copy2(src/n,w/n)
        return w
    for case in ('missing','wrong-size','read-only'):
        w=work(case)
        text=PROBE.replace('@READ_CONDITION@','NZ' if case=='read-only' else 'Z').replace('@READ_CHECK@','' if case=='read-only' else '        CALL CHECK')
        data=assemble(Path.home()/'bin/z80asm',text,w/'IOERR.COM',w/'ioerr.lst',0x100)
        (w/'disks/drivec.dsk').write_bytes(image(bytes(20480),[('IOERR.COM',data)]))
        target=w/'disks/driveb.dsk'
        if case=='missing':target.unlink()
        elif case=='wrong-size':target.write_bytes(b'bad disk')
        else:target.chmod(0o444)
        before=target.read_bytes() if target.exists() else None
        t=Terminal(a.simulator.resolve(),w)
        try:
            t.prompt();t.send('C0:IOERR','ALTAIR PHYSICAL ERROR DMA PASS')
        finally:
            t.close()
            if target.exists():target.chmod(0o644)
        assert (target.read_bytes() if target.exists() else None)==before
        results.append({'case':case,'status':'PASS','media_unchanged':True})
    for reset in (False,True):
        w=work('media-reset' if reset else 'media-protect')
        code=(ROOT/'tests/fixtures/conformance/media-change-probe.mac').read_text().replace("ANCHOR: DB 1,'ANCHOR  DAT'","ANCHOR: DB 3,'ANCHOR  DAT'")
        data=assemble(Path.home()/'bin/z80asm',code,w/'MEDIA.COM',w/'media.lst',0x100)
        (w/'disks/drivec.dsk').write_bytes(image(bytes(20480),[('MEDIA.COM',data),('ANCHOR.DAT',b'anchor')]))
        (w/'disks/driveb.dsk').write_bytes(image(bytes(20480),[('OLD.TXT',b'OLD MEDIA')]))
        replacement=image(bytes(20480),[('NEW.TXT',b'REPLACEMENT MEDIA')])
        t=Terminal(a.simulator.resolve(),w)
        try:
            t.prompt();t.cursor=len(t.data);os.write(t.master,b'C0:MEDIA'+(b' R' if reset else b'')+b'\r')
            t.expect('OR-0143 SWAP LOGGED B NOW')
            (w/'disks/driveb.dsk').write_bytes(replacement)
            os.write(t.master,b'Y')
            t.expect('OR-0143 RESET AND CREATE PASS' if reset else 'Disk R/O');t.prompt('B')
            assert b'OR-0143 FIXTURE OR PROTECTION FAIL' not in t.data
        finally:t.close()
        if not reset:assert (w/'disks/driveb.dsk').read_bytes()==replacement
        results.append({'case':'media-reset' if reset else 'media-protect','status':'PASS'})
    assert (src/'disks/drivea.dsk').read_bytes()==master
    report={'status':'PASS','system_sha256':hashlib.sha256(master).hexdigest(),'cases':results,'character_routes':routes(src)}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: failed-read DMA preservation, failed writes, media change/reset and all 256 IOBYTE routes')


if __name__=='__main__':main()
