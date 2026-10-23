#!/usr/bin/env python3
"""Exercise checked utility entry gates and cross-profile public operations."""
from pathlib import Path
import argparse,json,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path);p.add_argument('foreign',type=Path)
p.add_argument('--output',type=Path,required=True);p.add_argument('--live',action='store_true')
a=p.parse_args();root=a.root.resolve();other=a.foreign.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'tools'))
from test_bios import Z80
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
g=symbols(root/'build/z80pack/gateway.lst')
profile=json.loads((root/'assessment-profile.json').read_text());ident=bytes.fromhex(profile['compatibility_id']);cid=L['BIOS']-16
results={}
def save(): (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
class Memory(bytearray):
    private_reads=0
    def __getitem__(self,k):
        if isinstance(k,int) and cid<=k<cid+16:self.private_reads+=1
        return super().__getitem__(k)
for name,tail in [('CONFIG',b'/SHOW'),('SYSGEN',b'X'),('STAT',b'MEM')]:
    data=(root/f'build/utilities/{name}.COM').read_bytes();sy=symbols(root/f'build/utilities/{name.lower()}.lst')
    target=sy['P12CHECK'];call=bytes((0xcd,target&255,target>>8));offset=data.index(call)
    rows=[]
    for mode in ['matching','wrong-bios','wrong-opcode']+['id-'+str(i) for i in range(16)]:
        c=Z80(b'');c.mem=Memory(65536);c.mem[256:256+len(data)]=data
        # Stop immediately after the actual entry gate returns successfully.
        c.mem[256+offset+3:256+offset+6]=b'\xc3\xff\xff'
        c.mem[0]=0xc3;c.setword(1,L['BIOS']+3);c.mem[cid:cid+16]=ident
        if mode=='wrong-bios':c.setword(1,L['BIOS']+3-0xC00)
        if mode=='wrong-opcode':c.mem[0]=0
        if mode.startswith('id-'):c.mem[cid+int(mode[3:])]^=1
        c.mem[5:8]=bytes((0xdb,254,0xc9));c.mem[128]=len(tail);c.mem[129:129+len(tail)]=tail
        # Intercept failure's JP 0 without altering the WBOOT identity under test.
        source=__import__('inspect').getsource(Z80.run)
        import textwrap
        source=textwrap.dedent(source).replace('if self.pc == SENTINEL:', 'if self.pc in (0, SENTINEL):')
        ns=dict(Z80.run.__globals__);exec(source,ns);c.run=ns['run'].__get__(c,Z80)
        calls=[];output=[];before=bytes(c.mem[cid:cid+16]);c.mem.private_reads=0
        def io(port):
            assert port&255==254
            calls.append(c.c)
            if c.c==9:
                end=c.mem.index(36,c.de);output.append(bytes(c.mem[c.de:end]));return 0
            if name=='CONFIG' and c.c==2:
                output.append(bytes((c.e,)));return 0
            assert name=='STAT' and c.c in (25,32),(name,mode,c.c)
            return 0
        c.port_read=io;c.sp=g['SYS_STKTOP'];low=[c.sp];push=c.push
        def watch(v):
            push(v)
            if c.sp>g['SYS_STACK']-256:low[0]=min(low[0],c.sp)
        c.push=watch;c.run(256,limit=200000)
        assert low[0]>=g['SYS_STACK'],(name,mode,'pre-private stack overflow',low[0])
        good=mode=='matching'
        assert bool(output)==(not good),(name,mode,output)
        if not good:assert b''.join(output)==(b'Requires matching BetterCP/M private build.\r\n' if name=='CONFIG' else b'Private utility build mismatch.\r\n')
        reads=c.mem.private_reads
        if mode in ('wrong-bios','wrong-opcode'):assert reads==0
        assert bytes(c.mem[cid:cid+16])==before
        rows.append({'case':mode,'accepted':good,'private_reads':reads,'bdos_calls':calls,'entry_stack_bytes':g['SYS_STKTOP']-low[0]})
    results[name]=rows;save()
# CONFIG parses once before adopting its private stack, to distinguish /VER
# from quoted data. Exercise actual entry bytes with legal 127-byte tails.
name='CONFIG';data=(root/'build/utilities/CONFIG.COM').read_bytes();sy=symbols(root/'build/utilities/config.lst')
pre=[]
for tail in ('','/VER','/SHOW X','/STARTUP="Mixed /VER /B"','/STARTUP="'+'x'*116+'"','/STARTUP="X" /VER','/PHYSICAL=0,TRACKS=80'):
    c=Z80(b'');c.mem[256:256+len(data)]=data;c.mem[:3]=b'\xc3\xff\xff'
    c.mem[5:8]=bytes((0xdb,254,0xc9));c.mem[sy['P12CHECK']:sy['P12CHECK']+3]=b'\xc3\xff\xff'
    raw=tail.encode();c.mem[128]=len(raw);c.mem[129:129+len(raw)]=raw
    c.sp=g['SYS_STKTOP'];low=[c.sp];push=c.push
    def watch(v):
        push(v)
        if c.sp>g['SYS_STACK']-256:low[0]=min(low[0],c.sp)
    def io(port):
        assert c.c in (2,9),c.c
        return 0
    c.push=watch;c.port_read=io;c.run(256,limit=200000)
    used=g['SYS_STKTOP']-low[0];assert used<=32,(tail,used)
    pre.append({'tail':tail,'entry_stack_bytes':used})
results['CONFIG-preflight']=pre;save()
for name in ('SYSBUILD','RESPACK','RLMBUILD'):
    data=(root/f'build/utilities/{name}.COM').read_bytes();c=Z80(b'');c.mem[256:256+len(data)]=data
    c.mem[:3]=b'\xc3\xff\xff';c.mem[5:8]=bytes((0xdb,254,0xc9));calls=[];output=[]
    def io(port):
        calls.append(c.c);assert c.c==9,(name,c.c)
        end=c.mem.index(36,c.de);output.append(bytes(c.mem[c.de:end]));return 0
    c.port_read=io;c.run(256,limit=100000)
    assert output==[b'Native packaging tool unavailable in checked cpmsim build.\r\n']
    results[name]={'disabled':True,'bdos_calls':calls};save()
if a.live:
    import part7_probe_support as h
    h.out=out/'live';h.out.mkdir(exist_ok=True)
    w=h.case('cross-profile')
    for name in ('CONFIG','SYSGEN','STAT','RSX','CPX','CLS'):
        h.put(w,'F'+name+'.COM',(other/f'build/utilities/{name}.COM').read_bytes())
    for name in ('SYSBUILD','RESPACK','RLMBUILD'):
        h.put(w,name+'.COM',(root/f'build/utilities/{name}.COM').read_bytes())
    h.put(w,'HELLO.CPX',(root/'build/cpx/HELLO.CPX').read_bytes())
    t=h.run(w,['FCONFIG /SHOW','FSYSGEN A: B:','FSTAT MEM','FSTAT VAL:',
               'FRSX LIST','FCPX LIST','FRSX LOAD ZPRTC','FRSX LIST','TIME','FRSX UNLOAD ZPRTC',
               'FCPX LOAD HELLO','HELLO','FCPX UNLOAD HELLO','FCLS',
               'SYSBUILD','RESPACK','RLMBUILD','CONFIG /SHOW','STAT MEM'])
    assert t.count('Private utility build mismatch.')==2 and t.count('Requires matching BetterCP/M private build.')==1,t
    assert t.count('Native packaging tool unavailable in checked cpmsim build.')==3,t
    assert 'RSX module or profile error' not in t and 'Hello from HELLO.CPX' in t and 'ZPRTC' in t,t
    assert 'File Status:' in t or '$R/O $R/W' in t,t
    assert h.maps(t)[-1]['maximum']==(L['TPA']-256)//128*128
    results['live-cross-profile']={'private_rejections':3,'native_disabled':3,'tpa':h.maps(t)[-1]['maximum'],'public_STAT_RSX_CPX_CLS':True};save()
print('PASS Part 12 utility gates',flush=True)
