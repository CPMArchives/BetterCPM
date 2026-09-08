#!/usr/bin/env python3
"""Exercise CONFIG H against private media, including a failed second write."""
from pathlib import Path
import subprocess, shutil
from test_disk_utilities import ROOT, medium, keys, DEFAULT_EMULATOR
from build_ccp import assemble
from build_montezuma_extended_790k import crc16

OUT=ROOT/'build/test-results/config-sysgen'

def probe(work,check=False,fault=False):
    body='''        ASEG
        ORG 100H
        LD SP,4000H
        LD DE,REQ
        LD B,1
        LD C,207
        CALL 5
        LD A,L
        OR A
        JP NZ,FAIL
'''
    if check:
        body+='''        LD A,(REQ+6)
        CP 20
        JP NZ,FAIL
'''
    else:
        body+='''        LD A,20
        LD (REQ+6),A
        LD DE,REQ
        LD B,2
        LD C,207
        CALL 5
        LD A,L
        OR A
        JP NZ,FAIL
'''
    body+='''        LD DE,REQ
        LD B,3
        LD C,207
        CALL 5
        LD A,L
        OR A
        JP NZ,FAIL
'''
    if check:
        body+='''        LD A,(REQ+1)
        CP 2
        JP NZ,FAIL
'''
    else:
        body+='''        LD A,2
        LD (REQ+1),A
        LD DE,REQ
        LD B,4
        LD C,207
        CALL 5
        LD A,L
        OR A
        JP NZ,FAIL
'''
    if fault:
        body+='''        LD HL,HOOK
        LD DE,9000H
        LD BC,HOOKEND-HOOK
        LDIR
        LD HL,(1)
        LD DE,40
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD (9015H),DE
        LD (HL),90H
        DEC HL
        LD (HL),0
'''
    body+='''        LD DE,GOOD
        JR REPORT
FAIL:   LD DE,BAD
REPORT: LD C,9
        CALL 5
        LD C,1
        CALL 5
        JP 0
GOOD:   DB 'SYSGEN PROBE PASS',13,10,'$'
BAD:    DB 'SYSGEN PROBE FAIL',13,10,'$'
REQ:    DB 1
        DS 79
'''
    if fault:
        # Hook assembled at 9000 by hand: fail exactly the second write;
        # all subsequent writes, including rollback, reach the real BIOS.
        body+='''HOOK: DB 03AH,018H,090H,03CH,032H,018H,090H,0FEH,2
        DB 020H,4,03EH,1,0B7H,0C9H
        DB 0C3H,014H,090H,0,0,0C3H,0,0,0,0
HOOKEND:
'''
    body+='        END\n'
    name='CHECK' if check else 'SETUP'
    return assemble(Path.home()/'bin/z80asm',body,work/(name+'.COM'),work/(name+'.lst'),0x100)

def run(work,image,steps,protected=False):
    work.mkdir(parents=True,exist_ok=True)
    if image is not None:(work/'a.dmk').write_bytes(image)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(work/'a.dmk'),'-id','2000']
    for text,wait in steps:
        args+=keys(text)
        args+=['-itime','0','-iw',wait] if isinstance(wait,str) else ['-id',str(wait)]
        args+=['-it']
    args+=['-ix']
    subprocess.run(args,cwd=work,check=True,timeout=180,stdout=subprocess.DEVNULL)
    captures=[]
    for p in sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1])):
        r=p.read_bytes()[:1920]
        s='\n'.join(bytes(c&127 for c in r[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
        p.with_suffix('.txt').write_text(s);captures.append(s)
    return captures

def logical(image):
    size=int.from_bytes(image[2:4],'little');raw=bytearray()
    for t in range(160):
        track=image[16+t*size:16+(t+1)*size];sectors={}
        for j in range(0,128,2):
            p=int.from_bytes(track[j:j+2],'little')&0x3fff
            if not p:break
            mark=track.find(b'\xa1\xa1\xa1\xfb',p+7)
            assert mark>=0
            data=track[mark+4:mark+516]
            assert int.from_bytes(track[mark+516:mark+518],'big')==crc16(track[mark:mark+516])
            sectors[track[p+3]]=data
        for sid in (1,3,5,7,9,2,4,6,8,10):raw+=sectors[sid]
    return bytes(raw)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name in ('save','cold','decline','rollback'):
        if (OUT/name).exists():shutil.rmtree(OUT/name)
    setup=probe(OUT);check=probe(OUT,check=True)
    image=medium([('SETUP.COM',setup),('CHECK.COM',check)])
    start=[('SETUP\r','SYSGEN PROBE PASS'),('\r','A0>'),('CONFIG\r','Your choice:'),('H','Save current drive settings')]
    s=run(OUT/'save',image,start+[('Y','Configuration saved and verified.'),('\r','Your choice:'),('\x03','A0>')])
    assert 'Configuration saved and verified.' in s[-3],s
    saved=(OUT/'save/a.dmk').read_bytes()
    before=logical(image);after=logical(saved)
    assert before!=after,'no settings written'
    resident=(ROOT/'build/system/resident.bin').read_bytes()
    import struct
    from system_layout import LAYOUT
    p=resident.index(b'BDCF'+bytes((5,4,4,64)))
    physical,table=struct.unpack_from('<HH',resident,p+8)
    base=8*128-LAYOUT['SYSTEM']
    allowed=set(range(base+physical,base+physical+24))
    for n in range(4):allowed.update(range(base+table+n*80+16,base+table+n*80+80))
    changed={i for i,(a,b) in enumerate(zip(before,after)) if a!=b}
    assert changed<=allowed,changed-allowed
    cold=run(OUT/'cold',saved,[('CHECK\r','SYSGEN PROBE PASS'),('\r','A0>'),('CONFIG\r','Your choice:'),('H','Save current drive settings'),('Y','Configuration saved and verified.')])
    assert 'SYSGEN PROBE PASS' in cold[0],cold
    assert logical((OUT/'cold/a.dmk').read_bytes())==after,'repeat save changed disk'
    run(OUT/'decline',image,start+[('N','Your choice:')])
    assert (OUT/'decline/a.dmk').read_bytes()==image
    faultsetup=probe(OUT,fault=True)
    faultimage=medium([('SETUP.COM',faultsetup)])
    s=run(OUT/'rollback',faultimage,start+[('Y','Original configuration restored.')])
    assert 'Original configuration restored.' in s[-1],s
    assert logical((OUT/'rollback/a.dmk').read_bytes())==logical(faultimage),'rollback did not restore all bytes'
    print('CONFIG H: cold boot, repeat save, decline, unrelated-byte preservation and write-failure rollback PASS')
if __name__=='__main__':main()
