#!/usr/bin/env python3
"""Exercise actual DUP copy/check code on private emulator disks."""
from pathlib import Path
import subprocess, tempfile, sys
from build_ccp import assemble
from test_disk_utilities import medium, keys
from run_trs80_command import DEFAULT_EMULATOR
from build_montezuma_extended_790k import crc16
ROOT=Path(__file__).resolve().parents[1]

def binding(physical,sides):
    # Two cylinders, one reserved surface track: copy must include it too.
    b=bytearray(64);b[0]=physical
    b[1:16]=bytes([40,0,3,7,0,14 if sides==2 else 4,0,31,0,128,0,0,0,1,0])
    b[16:20]=bytes([2,10,2,0xC0 if sides==2 else 0x80])
    b[20:30]=bytes(range(1,11));return bytes(b)

def probe(w, mode):
    src=binding(1,2);dst=binding(2,2 if mode=='same' else 1)
    if mode=='abort':
      src=bytearray(src);src[16]=80;src=bytes(src)
    if mode=='mixed':
      src=bytearray(src);src[1:3]=bytes([15,0]);src[6:8]=bytes([6,0]);src[14:16]=bytes(2)
      src[17:19]=bytes([4,3]);src[20:52]=bytes([3,7,9,12])+bytes(28)
      src[52:54]=bytes([1,0x9c]);src=bytes(src)
    def db(b):return ''.join('        DB '+','.join(map(str,b[i:i+16]))+'\n' for i in range(0,len(b),16))
    text='''        ASEG
        ORG 100H
        LD SP,4000H
        LD A,(80H)
        OR A
        JR NZ,CHECK
        LD DE,BREQ
        LD BC,04CFH
        CALL 5
        LD A,L
        OR A
        JR NZ,FAIL
        LD DE,CREQ
        LD BC,04CFH
        CALL 5
        LD A,L
        OR A
        JR NZ,FAIL
        JR OK
CHECK:  LD DE,READREQ
        LD BC,03CFH
        CALL 5
        LD A,L
        OR A
        JR NZ,FAIL
        LD HL,READREQ+1
        LD DE,CREQ+1
        LD B,64
CMP:    LD A,(DE)
        CP (HL)
        JR NZ,DIFF
        INC HL
        INC DE
        DJNZ CMP
        JR OK
DIFF:   LD A,64
        SUB B
        CALL HEX
        LD A,(HL)
        CALL HEX
        LD A,(DE)
        CALL HEX
        JR FAIL
HEX:    PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIB
        POP AF
        CALL NIB
        POP HL
        POP DE
        POP BC
        POP AF
        RET
NIB:    AND 15
        ADD A,'0'
        CP '9'+1
        JR C,EMIT
        ADD A,7
EMIT:   LD E,A
        LD C,2
        JP 5
OK:     LD DE,GOOD
        JR REPORT
FAIL:   LD DE,BAD
REPORT: LD C,9
        CALL 5
        JP 0
GOOD:   DB 'BINDING TEST PASS',13,10,'$'
BAD:    DB 'BINDING TEST FAIL',13,10,'$'
BREQ:
'''+db(bytes([1])+src+bytes(15))+'CREQ:\n'+db(bytes([2])+dst+bytes(15))+'READREQ:\n'+db(bytes([2])+bytes(79))
    return assemble(Path.home()/'bin/z80asm',text,w/'DSET.COM',w/'dset.lst',0x100)

def payloads(image):
    size=int.from_bytes(image[2:4],'little');out={}
    for cyl in range(2):
      for side in range(2):
        start=16+(cyl*2+side)*size;t=image[start:start+size]
        for j in range(0,128,2):
          ptr=int.from_bytes(t[j:j+2],'little')&0x3fff
          if not ptr:break
          mark=t.find(b'\xa1\xa1\xa1\xfb',ptr+7)
          n=128<<t[ptr+4]
          assert mark>=0
          data=t[mark+4:mark+4+n]
          assert t[mark+4+n:mark+6+n]==crc16(t[mark:mark+4+n]).to_bytes(2,'big')
          out[cyl,side,t[ptr+3]]=data
    return out

def main():
  mode=sys.argv[1] if len(sys.argv)>1 else 'copy'
  with tempfile.TemporaryDirectory(prefix='bettercpm-dup-') as tmp:
    w=Path(tmp);code=probe(w,mode);system=medium([('DSET.COM',code),('RSX.COM',(ROOT/'build/utilities/RSX.COM').read_bytes()),('FDF.RSX',(ROOT/'build/rsx/FDF.RSX').read_bytes())])
    source=bytearray(system);size=int.from_bytes(source[2:4],'little')
    badpos=None
    for cyl in range(2):
      for side in range(2):
        start=16+(cyl*2+side)*size;t=source[start:start+size]
        if mode=='mixed':
          t=bytearray(b'\x4e'*size);t[:128]=bytes(128);ptr=175
          for slot,(sid,sz) in enumerate(zip([3,7,9,12],[0,3,1,2])):
            t[2*slot:2*slot+2]=(ptr|0x8000).to_bytes(2,'little')
            t[ptr-15:ptr-3]=bytes(12);t[ptr-3:ptr]=b'\xa1'*3
            ident=bytes([254,cyl,side,sid,sz]);t[ptr:ptr+5]=ident
            t[ptr+5:ptr+7]=crc16(b'\xa1'*3+ident).to_bytes(2,'big')
            t[ptr+29:ptr+41]=bytes(12);t[ptr+41:ptr+45]=b'\xa1'*3+b'\xfb'
            ptr+=98+(128<<sz)
        for j in range(0,128,2):
          ptr=int.from_bytes(t[j:j+2],'little')&0x3fff
          if not ptr:break
          mark=t.find(b'\xa1\xa1\xa1\xfb',ptr+7)
          assert mark>=0
          n=128<<t[ptr+4]
          # Distinct 128-byte portions catch stale or misindexed cache hits;
          # a simple byte ramp repeats after 256 bytes and misses that fault.
          data=bytes((cyl*41+side*17+t[ptr+3]*3+k+19*(k//128))%256 for k in range(n))
          t[mark+4:mark+4+n]=data
          t[mark+4+n:mark+6+n]=crc16(t[mark:mark+4+n]).to_bytes(2,'big')
          if badpos is None and j==4:badpos=start+mark+4+n
        source[start:start+size]=t
    if mode=='bad':source[badpos]^=1
    target=bytearray(system)
    if mode=='protected':target[0]=255
    for l,b in [('a',system),('b',source),('c',target)]: (w/f'{l}.dmk').write_bytes(b)
    # First decline: temporary reconfiguration must be restored with no writes.
    steps=[('DSET\r',2500),('DUP\r',5000),('B',500),('B',500),('C',1000),('N',1000),
      ('\x03',2000),('DSET CHECK\r',2500),('DUP\r',5000),('B',500),('B',500),('C',1000),('Y',25000),
      ('\r',1000),('\x03',2500),('DSET CHECK\r',2500)]
    if mode in ('copy','bad','mixed','same'):
      steps += [('DUP\r',5000),('C',500),('B',10000),('\r',1000),('\x03',2500)]
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo']
    for i,l in enumerate('abc'):args += [f'-d{i}',str(w/f'{l}.dmk')]
    args+=['-id','3000']
    if mode=='mixed':args+=keys('RSX LOAD FDF\r')+['-id','5000']
    for i,(text,delay) in enumerate(steps):
      args+=keys(text)
      if mode=='abort' and i==12:args+=['-id','200','-ik','6','4','-id','1000','-ik','6','0']
      args+=['-id',str(delay),'-it']
    args+=['-ix'];subprocess.run(args,cwd=w,check=True,timeout=360)
    screens=[];report=ROOT/'build/test-results/dup'/mode;report.mkdir(parents=True,exist_ok=True)
    for i,p in enumerate(sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))):
      raw=p.read_bytes()[:1920];text='\n'.join(bytes(c&127 for c in raw[x:x+80]).decode('ascii').rstrip() for x in range(0,1920,80))
      screens.append(text);(report/f'{i:02d}.txt').write_text(text)
    assert 'BINDING TEST PASS' in screens[0],screens[0]
    assert 'BINDING TEST PASS' in screens[7],screens[7]
    assert 'BINDING TEST PASS' in screens[15],screens[15]
    assert (w/'a.dmk').read_bytes()==system
    assert (w/'b.dmk').read_bytes()==source
    result=(w/'c.dmk').read_bytes()
    if mode in ('copy','mixed','same'):
      assert 'Copy complete; destination verified.' in screens[12],screens[12]
      assert payloads(result)==payloads(source)
      assert result[16+4*size:]==target[16+4*size:]
      assert 'Unreadable sectors: 00000' in screens[18],screens[18]
    else:
      assert 'Copy complete' not in screens[12]
      if mode!='abort':assert result==target,'failed operation changed destination'
      if mode=='bad':
        assert 'Unreadable sectors: 00001' in screens[18],screens[18]
        assert 'CRC error' in screens[12] and 'sector ID 3' in screens[12],screens[12]
      if mode=='protected':assert 'Disk is write protected.' in screens[12],screens[12]
    assert 'A0>' in screens[-1],screens[-1]
    print(f'PASS: DUP {mode}; source/system preserved, destination restored, menu and warm exit')
if __name__=='__main__':main()
