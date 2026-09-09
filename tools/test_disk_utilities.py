#!/usr/bin/env python3
"""Run the transient utilities against disposable trs80gp disks."""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from build_ccp import assemble
from build_disk_utilities import builtin_source
import json
from build_trs80_boot import install
from build_montezuma_extended_790k import crc16
from run_trs80_command import DEFAULT_EMULATOR, key_args
ROOT=Path(__file__).resolve().parents[1]
FDF=ROOT/'third_party/montezuma/DISK.FDF'

def records():
    lines=FDF.read_text().split(chr(26))[0].splitlines()
    result=[]
    for i in range(0,len(lines),3):
        name=lines[i][1:]
        p=list(map(int,lines[i+1].split(',')))
        skew=bytes(map(int,lines[i+2].split(',')))
        # Independent encoding from the documented ABI, not assembly offsets.
        dpb=struct.pack('<HBBBHHBBHH',*p[:10])
        binding=b'\0'+dpb+bytes((p[12],p[10],p[11],p[13]))+skew.ljust(32,b'\0')+bytes(12)
        assert len(binding)==64
        result.append((name,binding))
    return result

def db(data):
    return '\n'.join('        DB '+','.join(map(str,data[i:i+16])) for i in range(0,len(data),16))

def make_probe(work):
    rows=[]
    for f in json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats']:
        p=f['parameters']
        binding=b'\0'+struct.pack('<HBBBHHBBHH',*p[:10])+bytes((p[12],p[10],p[11],p[13]))+bytes(f['sector_ids']).ljust(32,b'\0')+bytes(12)
        rows.append((f['name'],binding))
    rows+=records()
    text='''        ASEG
        ORG 100H
        LD SP,4000H
        CALL INIT
        CALL FLOAD
        LD A,(FCOUNT)
        CP 112
        JP NZ,TFAIL
        LD HL,EXPECTED
        LD (EXPECT),HL
        XOR A
        LD (INDEX),A
TLOOP:  LD A,(INDEX)
        CALL FPARSE
        JP C,TFAIL
        LD HL,BIND
        LD DE,(EXPECT)
        LD B,64
TCMP:   LD A,(DE)
        CP (HL)
        JP NZ,TFAIL
        INC DE
        INC HL
        DJNZ TCMP
        LD (EXPECT),DE
        LD A,(INDEX)
        INC A
        LD (INDEX),A
        CP 112
        JR NZ,TLOOP
        LD HL,BROKEN
        LD (FINDEX),HL
        XOR A
        CALL FPARSE
        JP NC,TFAIL
        LD HL,PASSMSG
        CALL PUTS
TWAIT:  CALL KEY
        JP 0
TFAIL:  LD HL,FAILMSG
        CALL PUTS
        LD A,(INDEX)
        CALL DECOUT
        JP TWAIT
PASSMSG:DB 'ALL 112 FORMAT RECORDS PASS; OVERFLOW REJECTED',13,10,0
FAILMSG:DB 'FDF PARSER FAIL at ',0
INDEX:  DB 0
EXPECT: DW 0
BROKEN: DB 'Bad',13,10,'65536,3,7,0,170,63,192,0,16,2,9,2,40,128',13,10
        DB '1,4,7,2,5,8,3,6,9',13,10,26
EXPECTED:
'''+db(b''.join(b for _,b in rows))+'\n'+(ROOT/'src/utilities/disk/common.inc').read_text().replace('        INCLUDE disk/builtins.inc',builtin_source())+'\n        END\n'
    path=work/'FDFTEST.COM'
    assemble(Path.home()/'bin/z80asm',text,path,work/'probe.lst',0x100)
    return path

def medium(extras=()):
    b=ROOT/'build'
    files=[('RCP.CPX',(b/'cpx/RCP.CPX').read_bytes()),
           ('CONFIG.COM',(b/'utilities/CONFIG.COM').read_bytes()),
           ('DUP.COM',(b/'utilities/DUP.COM').read_bytes()),
           ('SYSGEN.COM',(b/'utilities/SYSGEN.COM').read_bytes()),
           ('DISK.FDF',FDF.read_bytes()),*extras]
    return install((b/'trs80/boot.bin').read_bytes(),(b/'trs80/stage1.bin').read_bytes(),
        (b/'system/resident.bin').read_bytes(),(b/'ccp/ccp.rlm').read_bytes(),files)

def keys(text):
    args=[]
    for char in text:
        if char=='\x03':
            args+=['-ik','6','4','-id','4','-ik','6','0','-id','4']
        else: args+=key_args(char)
    return args

def run(work,name,steps,extras=(),blank=False,timeout=360):
    w=work/name;w.mkdir()
    image=medium(extras)
    (w/'a.dmk').write_bytes(image)
    (w/'b.dmk').write_bytes(image[:16]+bytes(len(image)-16) if blank else image)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),
          '-d1',str(w/'b.dmk'),'-id','3000']
    for text,delay in steps:
        args+=keys(text)+(['-itime','0','-iw',delay] if isinstance(delay,str) else ['-id',str(delay)])+['-it']
    args+=['-ix']
    subprocess.run(args,cwd=w,check=True,timeout=timeout)
    captures=[]
    for p in sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1])):
        raw=p.read_bytes()[:1920]
        screen='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
        captures.append((screen,raw))
    report=ROOT/'build/test-results/disk-utilities'/name
    report.mkdir(parents=True,exist_ok=True)
    for i,(text,raw) in enumerate(captures):
        (report/f'{i:02d}.txt').write_text(text)
        (report/f'{i:02d}.bin').write_bytes(raw)
    assert len(captures)==len(steps),(name,len(captures),len(steps))
    if name=='format':
        shutil.copy2(w/'b.dmk',report/'formatted.dmk')
        (report/'original.dmk').write_bytes(image)
    assert (w/'a.dmk').read_bytes()==image,'utility modified system disk'
    return captures,w,image

def check_image(path, original, cylinders=40):
    data=path.read_bytes()
    size=int.from_bytes(data[2:4],'little')
    # Only side zero of the first 40 cylinders was requested. Side one and
    # all later cylinders must remain byte-for-byte unchanged.
    for cyl in range(80):
        for side in range(2):
            start=16+(cyl*2+side)*size
            track=data[start:start+size]
            if cyl>=cylinders or side:
                assert track==original[start:start+size],(cyl,side,'untargeted track changed')
                continue
            ids=[]
            for j in range(0,128,2):
                ptr=int.from_bytes(track[j:j+2],'little')
                if not ptr: break
                off=ptr&0x3fff
                assert track[off:off+3]==bytes((0xfe,cyl,0)),(cyl,off)
                ids.append(track[off+3])
                assert track[off+4]==2,'wrong sector length'
                assert track[off+5:off+7]==crc16(b'\xa1'*3+track[off:off+5]).to_bytes(2,'big'),'bad ID CRC'
                mark=track.find(b'\xa1\xa1\xa1\xfb',off+7)
                assert mark>=0,'missing MFM data mark'
                assert track[mark+4:mark+516]==bytes([0xe5])*512,(cyl,ids[-1],'not erased')
                assert track[mark+516:mark+518]==crc16(track[mark:mark+516]).to_bytes(2,'big'),'bad data CRC'
            assert ids==[1,4,7,2,5,8,3,6,9],(cyl,ids)


def format_test(work):
    steps=[('CONFIG\r',6000),('G',700),('B',700),('.',700),('\r',700),('1',1200),
           ('\r',700),('\x03',700),('\x03',4000),('DUP\r',6000),('A',700),
           ('B',1000),('N',700),('A',700),('B',1000),('Y',40000),
           ('\r',700),('\x03',4000)]
    screens,w,image=run(work,'format',steps)
    assert 'Disk configuration changed' in screens[5][0],screens[5][0]
    assert 'Access Matrix' in screens[11][0],screens[11][0]
    assert 'Format complete.' in screens[15][0],screens[15][0]
    assert 'A0>' in screens[-1][0],screens[-1][0]
    check_image(w/'b.dmk',image)
    print('PASS: configured FDF format, confirmation, all 40 tracks erased, other tracks and system disk unchanged, exit',flush=True)


def settings_probe(work):
    code=['        ASEG','        ORG 100H','        LD SP,4000H']
    expected=[(1,1,bytes([5,40,1,1,3,20])),(3,1,bytes([1])+records()[0][1][1:]),
              (3,2,bytes([1])+records()[5][1][1:])]
    for i,(op,index,data) in enumerate(expected):
        code += [f'        LD A,{index}','        LD (REQ),A',f'        LD B,{op}',
            '        LD DE,REQ','        CALL API','        JP NZ,TFAIL',
            '        LD HL,REQ+1',f'        LD DE,EXP{i}',f'        LD B,{len(data)}',
            f'CMP{i}: LD A,(DE)','        CP (HL)','        JP NZ,TFAIL',
            '        INC HL','        INC DE',f'        DJNZ CMP{i}']
    code += ['        LD HL,OK','        JR REPORT','TFAIL: LD HL,BAD',
        'REPORT: CALL PUTS','        CALL KEY','        JP 0',
        "OK: DB 'DRIVE SETTINGS AND ALIASES PASS',13,10,0",
        "BAD: DB 'DRIVE SETTINGS OR ALIASES FAIL',13,10,0"]
    for i,(_,_,data) in enumerate(expected): code += [f'EXP{i}:',db(data)]
    code += [(ROOT/'src/utilities/disk/common.inc').read_text().replace('        INCLUDE disk/builtins.inc',builtin_source()),'        END']
    path=work/'CFGTEST.COM'
    assemble(Path.home()/'bin/z80asm','\n'.join(code),path,work/'settings.lst',0x100)
    return path


def settings_test(work):
    probe=settings_probe(work)
    steps=[('CONFIG\r',6000),('G',700),('B',700),('.',700),('A',700),('1',1200),
        ('\r',700),('\x03',700),('F',700),('B',700),('B',700),('B',1000),
        ('C',700),('1\r',1000),('D',700),('B',1000),('E',700),('3\r',1000),
        ('F',700),('20\r',1000),('\x03',700),('\x03',700),('G',700),('C',700),('.',700),
        ('F',700),('1',1200),('\r',700),('\x03',700),('\x03',4000),('CFGTEST\r',5000)]
    screens,w,image=run(work,'settings',steps,[(probe.name,probe.read_bytes())])
    assert 'DRIVE SETTINGS AND ALIASES PASS' in screens[-1][0],screens[-1][0]
    assert (w/'b.dmk').read_bytes()==image,'configuration wrote disk data'
    print('PASS: tracks, sides, step rate, spin-up, settle time, distinct B/C formats on physical 1, warm-boot persistence',flush=True)


def reject_test(work):
    steps=[('CONFIG\r',6000),('G',700),('A',700),('\r',700),('B',700),('M',700),
        ('1',1000),('\r',700),('\x03',700),('\x03',4000),
        ('DUP\r',6000),('A',700),('A',700),('\r',700),('A',700),('B',1000),
        ('N',700),('\x03',4000)]
    screens,w,image=run(work,'reject',steps)
    assert 'binding is protected' in screens[2][0],screens[2][0]
    assert 'Invalid or unsupported setting' in screens[6][0],screens[6][0]
    assert 'protected system disk' in screens[12][0],screens[12][0]
    assert 'Format this disk?' in screens[15][0],screens[15][0]
    assert 'A0>' in screens[-1][0],screens[-1][0]
    assert (w/'b.dmk').read_bytes()==image,'rejection/cancel modified target disk'
    print('PASS: protected system drive, unsupported FDF, cancelled format leave both disks untouched',flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix='bettercpm-disk-utils-') as tmp:
        work=Path(tmp)
        probe=make_probe(work)
        screens,_,_=run(work,'parser',[('FDFTEST\r',6000)],[(probe.name,probe.read_bytes())])
        assert 'ALL 112 FORMAT RECORDS PASS' in screens[0][0],screens[0][0]
        print('PASS: assembly parser matches 16 built-ins plus 96 FDF definitions and rejects overflow',flush=True)
        screens,_,_=run(work,'menus',[('CONFIG\r',6000),('G',1000),('B',1000),
            ('.',1000),(',',1000),('>',1000),('<',1000),('\x03',1000),
            ('\x03',1000),('\x03',4000),('DUP\r',6000),('B',1000),
            ('\x03',1000),('C',1000),('\x03',1000),('\x03',4000)])
        page=screens[2][0]
        for i in range(16): assert '[ '+chr(65+i)+' ]' in page,page
        assert 'Montezuma Micro Standard SYSTEM' in page,page
        assert 'Access Matrix' in screens[3][0],screens[3][0]
        assert screens[2]==screens[4]==screens[6],'paging failed to restore first page'
        assert screens[3]==screens[5],'shifted next-page key differs from period'
        assert all(c&128 for c in screens[2][1][:79]),'heading is not reverse video'
        assert 'A0>' in screens[9][0],screens[9][0]
        assert 'Source logical drive' in screens[11][0],screens[11][0]
        assert 'Check a disk for errors' in screens[13][0],screens[13][0]
        assert 'A0>' in screens[15][0],screens[15][0]
        print('PASS: 16-row menus, both paging key pairs, copy/check menus and CONFIG/DUP exit',flush=True)
if __name__=='__main__':
    import sys
    if len(sys.argv)==1: main()
    else:
        with tempfile.TemporaryDirectory(prefix='bettercpm-disk-utils-') as tmp:
            {'format':format_test,'settings':settings_test,'reject':reject_test}[sys.argv[1]](Path(tmp))
