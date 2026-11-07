#!/usr/bin/env python3
"""Build/run isolated XTCP 0.1 feasibility slice; never publish production outputs.

Run with the pinned monitor-test environment. This deliberately does not implement
or advertise the proposed public TCAP 1.0 request ABI or modify shipped sources.
"""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from system_layout import LAYOUT as L
from test_bios import Z80
from test_vt52_foundation import symbols
import pyte

HERE = Path(__file__).resolve().parent
OUT = ROOT / 'build/tcap-feasibility'


def normalized(text):
    return re.sub(r'        CSEG\n        \.PHASE\s+', '        ASEG\n        ORG ', text).replace('        .DEPHASE\n', '')


def build(assembler):
    OUT.mkdir(parents=True, exist_ok=True)
    images = {}
    def emit(name, text, origin):
        data = assemble(assembler, text, OUT / (name + '.bin'), OUT / (name + '.lst'), origin)
        images[name] = (data, symbols(OUT / (name + '.lst')))
        return images[name]
    # Existing BIOS build has platform includes: use its independent builder.
    import subprocess
    subprocess.run([sys.executable, str(ROOT/'tools/build_bios.py'), '--assembler', str(assembler)], check=True)
    images['bios'] = ((ROOT/'build/bios/bios.bin').read_bytes(), symbols(ROOT/'build/bios/bios.lst'))
    emit('bdos', normalized((ROOT/'src/bdos/unified.mac').read_text()), L['BDOS'])
    for name, source, base in [('mover','rsxmover.mac',0x7000), ('scheduler','rsxsched.mac',0x7800), ('commit','r3comit.mac',0x7c00)]:
        emit(name, normalized((ROOT/'src/system'/source).read_text()), base)
    ansi = normalized((ROOT/'src/rsx/ansi.mac').read_text())
    ansi = ansi.replace('        INCLUDE ansi-dispatch.inc', (ROOT/'src/rsx/ansi-dispatch.inc').read_text())
    ansi = ansi.replace('        INCLUDE screen/rendition.inc', (ROOT/'src/rsx/screen/rendition.inc').read_text())
    baseline, syms = emit('ansi-base', ansi, 0x8000)
    extended = ansi.replace('        END\n', (HERE/'owner.inc').read_text() + '\n        END\n')
    code, owner = emit('owner', extended, 0x8000)
    alt, _ = emit('owner-alt', extended.replace('08000H', '08101H'), 0x8101)
    slots = relocation_offsets(code, alt, 0x101)
    print(f'Owner payload {len(code)} bytes, relocation words {len(slots)}')
    carrier_error = None
    try:
        carrier = make_module(name='XTCAP',version=(0,1),services=[],linked_base=0x8000,
                              code=code,relocations=slots,reconstruction_class='STATEFUL',
                              callable_services=[(b'MCON',1,2,owner['AN_ENTRY']-0x8000,4),
                                                 (b'XTCP',0,1,owner['TX_ENTRY']-0x8000,0)])
    except SystemExit as error:
        if str(error) != 'RSX relocation directory exceeds its header':
            raise
        carrier_error = str(error)
        carrier = None
    if carrier is not None:
        (OUT/'XTCAP.RSX').write_bytes(carrier)
    else:
        (OUT/'XTCAP.RSX').unlink(missing_ok=True)
    (OUT/'owner-relocations.json').write_text(json.dumps(slots)+'\n')
    baseline_alt, _ = emit('ansi-base-alt', ansi.replace('08000H','08101H'),0x8101)
    baseline_slots = relocation_offsets(baseline,baseline_alt,0x101)
    baseline_carrier = make_module(name='ANSI',version=(0,1),services=[],linked_base=0x8000,
                                   code=baseline,relocations=baseline_slots,reconstruction_class='STATEFUL',
                                   callable_services=[(b'MCON',1,2,syms['AN_ENTRY']-0x8000,4)])
    backends = {}
    for name, source, entry in [('M4SCRN','model4.mac','S_ENTRY'), ('ANSISCRN','ansi-host.mac','SB_ENTRY')]:
        text = (ROOT/'src/rsx/screen'/source).read_text()
        bindings = '\n'.join(f'{key} EQU 0{images["bios"][1][key]:04X}H' for key in ('M4CURSOR','M4COLUMN'))
        text = text.replace('        INCLUDE backend.inc', bindings)
        data, labels = emit(name, text, 0x8000)
        other, _ = emit(name+'-alt', text.replace('08000H','08101H'), 0x8101)
        backends[name] = (data, labels, relocation_offsets(data,other,0x101), entry)
    return images, slots, backends, {
        'baseline_ansi_payload_bytes': len(baseline), 'experimental_ansi_payload_bytes': len(code),
        'owner_code_and_data_delta_bytes': len(code)-len(baseline),
        'owner_data_bytes': owner['TX_IMAGE']-owner['TX_STATE'],
        'baseline_ansi_allocation_bytes': int.from_bytes(baseline_carrier[14:16],'little'),
        'experimental_ansi_allocation_bytes': None if carrier is None else int.from_bytes(carrier[14:16],'little'),
        'experimental_payload_rounded_with_descriptors_bytes': (len(code)+20+255)&~255,
        'carrier_packaging_error': carrier_error,
        'experimental_relocation_words': len(slots),
        'bios_bytes': len(images['bios'][0]), 'bios_region_bytes': L['FILE']-L['BIOS'],
        'bdos_bytes': len(images['bdos'][0]), 'bdos_region_bytes': L['EXTENSIONS']-L['BDOS'],
    }


def relocated(data, slots, base):
    result = bytearray(data)
    for slot in slots:
        struct.pack_into('<H',result,slot,struct.unpack_from('<H',result,slot)[0]+base-0x8000)
    return result


class DepthCPU(Z80):
    """Observe every SP assignment; fail if any fixture stack exceeds its bound."""
    def __setattr__(self, name, value):
        bounds = self.__dict__.get('_stack_bounds') if name == 'sp' else None
        if bounds:
            for label, (low, high) in bounds.items():
                if low <= value <= high:
                    self._min_sp[label] = min(value, self._min_sp.get(label, high))
                    break
            else:
                raise AssertionError(f'stack pointer outside qualified fixture bounds: {value:04X}')
        super().__setattr__(name, value)


class WatchedMemory(bytearray):
    def __init__(self, cpu, data, bdos):
        super().__init__(data); self.cpu=cpu; self.bdos=bdos
        self.list_bytes=[]; self.console_bytes=[]
    def __getitem__(self,key):
        if isinstance(key,int) and key == self.cpu.pc:
            if key == L['BIOS']+15: self.list_bytes.append(self.cpu.c)
            if key == L['BIOS']+12: self.console_bytes.append(self.cpu.c)
        return super().__getitem__(key)



class Fixture:
    def __init__(self, assembler, images, slots, backends, name, base):
        self.cpu=cpu=DepthCPU(b''); self.name=name; self.base=base
        self.labels={k:v+base-0x8000 for k,v in images['owner'][1].items()}
        self.bdos=images['bdos'][1];self.bios=images['bios'][1]
        cpu.mem[L['BIOS']:L['BIOS']+len(images['bios'][0])]=images['bios'][0]
        cpu.mem[L['BDOS']:L['BDOS']+len(images['bdos'][0])]=images['bdos'][0]
        cpu.mem[base:base+len(images['owner'][0])]=relocated(images['owner'][0],slots,base)
        data,labels,repairs,entry=backends[name]
        cpu.mem[0x5000:0x5000+len(data)]=relocated(data,repairs,0x5000)
        cpu.setword(self.labels['AN_BACKEND'],labels[entry]-0x8000+0x5000)
        cpu.setword(images['bios'][1]['MP_MON'],self.labels['AN_ENTRY'])
        self.backend_labels={k:v-0x8000+0x5000 for k,v in labels.items()}
        cpu.mem[3]=1; cpu.sp=0x5f00; cpu.setword(1,L['BIOS']+3)
        bridge=(HERE/'coordinator.mac').read_text()
        prefix='\n'.join(f'{key} EQU 0{value:04X}H' for key,value in {
            'TX_FIX':self.labels['TX_FIX'],'TX_STATE':self.labels['TX_STATE'],
            'TX_ROUTE':self.labels['TX_ROUTE'],'BDOSCALL':L['BDOS'],
            'RCOMMIT':0x7c00,'RCONOUT':images['bios'][1]['BIOCONOT']}.items())+'\n'
        stem=f'bridge-{name}-{base:04x}'
        self.bridge=assemble(assembler,prefix+bridge,OUT/(stem+'.bin'),OUT/(stem+'.lst'),0x4000)
        self.gx=symbols(OUT/(stem+'.lst'))
        cpu.mem[0x4000:0x4000+len(self.bridge)]=self.bridge
        cpu.mem[L['BIOS']+12:L['BIOS']+15]=bytes([0xc3])+struct.pack('<H',self.gx['GX_ROUTE'])
        io='''        ASEG
        ORG 04800H
IO_STAT: LD A,(IO_KEY)
        OR A
        RET
IO_INPUT: LD A,(IO_KEY)
        LD B,A
        XOR A
        LD (IO_KEY),A
        LD A,B
        RET
IO_KEY: DB 0
IO_EMIT: LD A,C
        OUT (1),A
        RET
IO_WARM: LD SP,05D00H
        CALL 04000H
        JP 0FFFFH
'''
        io_data=assemble(assembler,io,OUT/'io.bin',OUT/'io.lst',0x4800)
        self.io=symbols(OUT/'io.lst');cpu.mem[0x4800:0x4800+len(io_data)]=io_data
        if name=='ANSISCRN':
            # Substitute only the fixture's basic hardware leaf with the host
            # OUT convention; keep the real shared BIOS router/Monitor dispatch.
            leaf=images['bios'][1]['M4_SCROLL_OUT']
            cpu.mem[leaf:leaf+3]=bytes([0xc3])+struct.pack('<H',self.io['IO_EMIT'])
        for off,label in [(3,'IO_WARM'),(6,'IO_STAT'),(9,'IO_INPUT')]:
            cpu.mem[L['BIOS']+off:L['BIOS']+off+3]=bytes([0xc3])+struct.pack('<H',self.io[label])
        self.screen=pyte.Screen(80,24); self.stream=pyte.Stream(self.screen);self.wire=[]
        def write(port,value):
            if name=='ANSISCRN':
                assert port&255==1;self.wire.append(value);self.stream.feed(chr(value))
        cpu.port_write=write;cpu.port_read=lambda port:0
        cpu.mem=WatchedMemory(cpu,cpu.mem,self.bdos)
        cpu._min_sp={}
        cpu._stack_bounds={'client':(0x5e00,0x5f00),'warm':(0x5c00,0x5d00),'bdos':(self.bdos['UB_STACK'],self.bdos['UB_STKTOP'])}
    def state(self): return self.cpu.mem[self.labels['TX_STATE']]
    def run(self,address,a=0):
        self.cpu.a=a;sp=self.cpu.sp;ix=self.cpu.ix
        self.cpu.run(address,limit=500000)
        assert self.cpu.sp==sp and self.cpu.ix==ix,(hex(address),self.cpu.sp,sp)
        return self.cpu.a
    def owner(self,op,token=None):
        if token is not None:self.cpu.mem[0x3000:0x3010]=token
        self.cpu.de=0x3000
        result=self.run(self.labels['TX_ENTRY'],op)
        assert self.cpu.de==0x3000 and self.cpu.word(self.labels['TX_PTR'])==0
        return result,bytes(self.cpu.mem[0x3000:0x3010])
    def text(self,data):
        for byte in data:
            self.cpu.c=2;self.cpu.de=byte
            self.run(L['BDOS'])
    def style(self,record):
        self.cpu.mem[0x3100:0x3109]=bytes(record)
        self.cpu.hl=0x3100
        assert self.run(self.labels['AN_RAW'],20)==0
        self.cpu.mem[self.labels['AP_VALUE']:self.labels['AP_VALUE']+9]=bytes(record)
    def saved(self):
        p=self.labels['AP_VALUE'];return bytes(self.cpu.mem[p:p+9])


def exercise(f):
    c=f.cpu; cases=[]; zero=bytes(16)
    def check(label,condition):
        assert condition,(f.name,hex(f.base),label);cases.append(label)
    c.mem[f.labels['AN_STATE']]=2
    check('takeover parser refusal',f.owner(3,zero)[0]==11 and f.state()==0)
    c.mem[f.labels['AN_STATE']]=0
    c.mem[f.labels['TX_MAP']]=0
    check('plain scope creates no token',f.owner(2,zero)==(1,zero) and f.state()==0)
    c.mem[f.labels['TX_MAP']]=32
    original=bytes([1,1,3,0,0,0,0,0,0]);f.style(original)
    # Actual SCX reusable slot must survive portable emphasis untouched.
    c.b=0;assert f.run(f.labels['AN_RAW'],23)==0
    result,token=f.owner(2,zero);check('begin',result==0 and f.state()==1)
    f.text(b'X');check('ordinary cooked text',c.mem[f.bdos['UB_COLUMN']]==1)
    if f.name=='ANSISCRN':check('rendered reverse',f.screen.buffer[0][0].reverse)
    else:check('rendered reverse',c.mem[0xf800]&128!=0)
    before=f.saved();result,_=f.owner(2,zero);check('nested refusal',result==12 and f.saved()==before)
    bad=bytearray(token);bad[0]^=1
    check('wrong identity refusal',f.owner(4,bad)[0]==13 and f.state()==1)
    c.mem[f.labels['AN_STATE']]=2
    check('incomplete parser refusal',f.owner(4,token)[0]==11 and f.state()==1)
    c.mem[f.labels['AN_STATE']]=0
    check('end restores prior rendition',f.owner(4,token)[0]==0 and f.saved()==original and f.state()==0)
    c.b=1;check('SCX save slot remains valid',f.run(f.labels['AN_RAW'],23)==0)
    f.text(b'S')
    if f.name=='ANSISCRN':
        check('SCX saved rendition and cursor preserved',f.screen.buffer[0][0].data=='S' and not f.screen.buffer[0][0].reverse and f.screen.buffer[0][0].bold)
    else:
        check('SCX saved rendition and cursor preserved',c.mem[0xf800]==ord('S'))
    check('retired scope refusal',f.owner(4,token)[0]==12)
    c.hl=4;c.de=80;assert f.run(f.labels['AN_RAW'],18)==0
    f.text(b'A');_,edge_token=f.owner(2,zero);f.owner(4,edge_token)
    if f.name=='ANSISCRN':
        check('scope preserves delayed wrap',(f.screen.cursor.x,f.screen.cursor.y)==(80,3))
    else:
        check('scope preserves delayed wrap',c.mem[f.backend_labels['SX_PEND']]==1)
    f.text(b'B')
    if f.name=='ANSISCRN':
        check('post-scope wrap continuation',f.screen.buffer[4][0].data=='B' and not f.screen.buffer[4][0].reverse)
    else:
        check('post-scope wrap continuation',c.mem[0xf800+4*80]==ord('B'))
    result,take=f.owner(3,zero);check('takeover',result==0 and f.state()==2)
    result,span=f.owner(2,take);check('takeover emphasis',result==0 and f.state()==3)
    check('end preserves takeover',f.owner(4,span)[0]==0 and f.state()==2)
    c.mem[f.labels['TX_MAP']]=0
    check('plain inside takeover preserves token',f.owner(2,take)==(1,take) and f.state()==2)
    c.mem[f.labels['TX_MAP']]=32
    # True safe-stack recovery through actual BDOS: CR resets cooked column.
    c.hl=3;c.de=10;assert f.run(f.labels['AN_RAW'],22)==0
    c.mem[f.labels['AN_VISIBLE']]=0;c.c=0;f.run(f.labels['AN_RAW'],15)
    c.mem[f.bdos['UB_COLUMN']]=77
    wire=len(f.wire);check('safe coordinator recovery',f.run(f.gx['GX_RECV'])==0 and f.state()==0)
    check('cooked column synchronized by real CR',c.mem[f.bdos['UB_COLUMN']]==0)
    check('personality visibility restored',c.mem[f.labels['AN_VISIBLE']]==1 and f.saved()==bytes(9))
    if f.name=='ANSISCRN':
        check('independent host prompt baseline',(f.screen.cursor.x,f.screen.cursor.y)==(0,1) and not f.screen.cursor.hidden and not f.screen.cursor.attrs.reverse and not f.screen.cursor.attrs.bold and f.screen.margins is None)
    else:
        check('Model 4 memory prompt baseline',c.word(f.bios['M4CURSOR'])==0xf850 and c.mem[f.bios['M4COLUMN']]==0 and c.mem[f.backend_labels['SM_TOPROW']]==0 and c.mem[f.backend_labels['SM_BOTTOM']]==23 and c.mem[f.backend_labels['SX_PEND']]==0)
    wire=len(f.wire);check('repeat recovery emits nothing',f.run(f.gx['GX_RECV'])==2 and len(f.wire)==wire)
    # Saturating 32-bit serial, carry and no-wrap.
    c.mem[f.labels['TX_SESS']:f.labels['TX_SESS']+4]=b'\xff\xff\xff\xff'
    check('session exhaustion atomic',f.owner(2,zero)[0]==20 and f.state()==0)
    c.mem[f.labels['TX_SESS']:f.labels['TX_SESS']+4]=b'\xff\0\0\0'
    result,token=f.owner(2,zero)
    check('32-bit session carry',result==0 and token[4:8]==b'\0\1\0\0')
    f.run(f.gx['GX_RECV'])
    c.mem[f.labels['TX_SSEQ']:f.labels['TX_SSEQ']+4]=b'\xff\xff\xff\xff'
    check('scope exhaustion atomic',f.owner(2,zero)[0]==20 and f.state()==0)
    c.mem[f.labels['TX_SSEQ']:f.labels['TX_SSEQ']+4]=b'\x05\0\0\0'
    # Real BDOS consumes ^P and mirrors only ordinary text to the real LIST route.
    c.mem[3]=0x41;c.mem[f.labels['TX_ROUTE']]=0x41
    c.mem[f.bdos['UB_LISTE']]=1
    before=len(c.mem.list_bytes)
    _,token=f.owner(2,zero)
    check('begin emits no LIST controls',len(c.mem.list_bytes)==before)
    c.mem[f.bdos['UB_LISTE']]=0
    c.mem[f.io['IO_KEY']]=16
    before=len(c.mem.list_bytes);f.text(b'P')
    check('printer echo sees text not style controls',c.mem.list_bytes[before:]==[ord('P')])
    before=len(c.mem.list_bytes);f.owner(4,token)
    check('end emits no LIST controls',len(c.mem.list_bytes)==before)
    f.owner(3,zero);before=len(c.mem.list_bytes);f.run(f.gx['GX_RECV'])
    check('recovery LIST receives only CR LF',c.mem.list_bytes[before:]==[13,10])
    c.mem[f.bdos['UB_LISTE']]=0;c.mem[3]=1;c.mem[f.labels['TX_ROUTE']]=1
    # Guard detects a route-to-sink change before real BIOS dispatch.
    _,token=f.owner(2,zero);c.mem[3]=0
    f.text(b'Q');check('route mismatch retains recovery obligation',f.state()==5 and f.saved()==bytes(9))
    c.mem[3]=1;f.run(f.gx['GX_RECV'])
    # Inject failure during Begin: token/recovery ownership must already exist.
    target=c.word(f.labels['AN_BACKEND']);saved=bytes(c.mem[target:target+3])
    c.mem[target:target+3]=b'\x3e\xff\xc9'
    result,failed_token=f.owner(2,zero)
    check('failed Begin returns owned token',result==18 and failed_token!=zero and f.state()==5)
    c.mem[target:target+3]=saved
    check('failed Begin can recover',f.run(f.gx['GX_RECV'])==0 and f.state()==0)
    # Inject a backend failure at its entry; persistent owner must survive it.
    _,token=f.owner(2,zero)
    target=c.word(f.labels['AN_BACKEND']);saved=bytes(c.mem[target:target+3])
    c.mem[target:target+3]=b'\x3e\xff\xc9'
    check('restore failure retains ownership',f.owner(4,token)[0]==18 and f.state()==5)
    check('recovery failure is explicit',f.run(f.gx['GX_RECV'])==19 and f.state()==5)
    c.mem[target:target+3]=saved;check('retry recovery',f.run(f.gx['GX_RECV'])==0 and f.state()==0)
    # A failed route repair must halt instead of silently forwarding output.
    _,token=f.owner(2,zero)
    target=c.word(f.labels['AN_BACKEND']);saved=bytes(c.mem[target:target+3])
    c.mem[target:target+3]=b'\x3e\xff\xc9';c.mem[3]=0
    before=len(f.wire);c.c=2;c.de=ord('Q')
    try:
        c.run(L['BDOS'],limit=500000)
    except AssertionError as error:
        assert str(error)==f"unsupported opcode 76 at {f.gx['GX_HALT']:04X}",error
    else:
        raise AssertionError('expected the fixture fatal HALT')
    check('failed route repair halts without forwarding',f.state()==5 and len(f.wire)==before)
    c.mem[target:target+3]=saved;c.mem[3]=1;c.sp=0x5f00
    check('safe retry after fatal fixture reset',f.run(f.gx['GX_RECV'])==0)
    # Abandon actual BDOS private frame with cooked ^C; injected warm boundary
    # selects a separate stack and calls coordinator (not a live reloader claim).
    _,token=f.owner(2,zero);c.mem[f.io['IO_KEY']]=3;c.c=2;c.de=ord('Z');c.sp=0x5f00
    c.run(L['BDOS'],limit=500000)
    check('cooked Ctrl-C safe-stack recovery',f.state()==0 and c.sp==0x5d00 and c.mem[f.bdos['UB_COLUMN']]==0)
    c.sp=0x5f00
    return cases


def transactions(f,images):
    c=f.cpu
    for name,base in [('mover',0x7000),('scheduler',0x7800),('commit',0x7c00)]:
        data=images[name][0];c.mem[base:base+len(data)]=data
    # Empty-profile commit using the actual unmodified commit engine.
    descriptor=0x6460
    c.mem[descriptor:descriptor+10]=struct.pack('<HHHHH',0x6600,0x6602,0x6604,0x6606,0x6608)
    c.setword(0x6600,0x8200);c.setword(0x6602,0x8100);c.setword(0x6606,7)
    request=struct.pack('<HHHBBHHHHHHHHB',0x6100,0x6200,0x6240,0,0,0x6400,0x7800,0x6420,32,0x7000,0x8400,L['BDOS'],descriptor,0xcc)
    c.mem[0x6000:0x6000+len(request)]=request
    c.mem[f.labels['TX_STATE']]=1
    before=bytes(c.mem[0x6000:0x8400]);c.de=0x6000
    assert f.run(f.gx['GX_COMIT'])==16
    assert bytes(c.mem[0x6000:0x8400])==before and c.word(0x6606)==7
    c.mem[f.labels['TX_STATE']]=0;c.de=0x6000
    assert f.run(f.gx['GX_COMIT'])==0 and c.word(0x6606)==8 and c.word(0x6600)==0
    c.mem[0x6006]=5;c.de=0x6000
    before=bytes(c.mem[0x6600:0x660a])
    assert f.run(f.gx['GX_COMIT'])!=0 and bytes(c.mem[0x6600:0x660a])==before
    return ['active guard preserves request/publication','idle invokes actual commit','invalid commit does not publish']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args()
    (OUT/'report.json').unlink(missing_ok=True)
    images,slots,backends,metrics=build(args.assembler)
    results=[]
    for backend in ('M4SCRN','ANSISCRN'):
        for base in (0x9000,0xa101):
            f=Fixture(args.assembler,images,slots,backends,backend,base)
            cases=exercise(f)+transactions(f,images)
            stack={name:high-f.cpu._min_sp.get(name,high) for name,high in [('client',0x5f00),('warm',0x5d00),('bdos',f.bdos['UB_STKTOP'])]}
            assert stack['bdos']<=f.bdos['UB_STKTOP']-f.bdos['UB_STACK']
            results.append({'backend':backend,'owner_origin':hex(base),'cases':cases,'stack_observed_bytes':stack,'bridge_bytes':len(f.bridge)})
            print(f'PASS {backend} at {base:04X}: {len(cases)} cases; stack {stack}')
    # Run the existing full commit/mover/scheduler regression in a private root.
    import test_rsxcommit as regression
    root=OUT/'commit-regression'
    for relative,name in [('build/bios/bios.bin','bios'),('build/system/rsxmover.bin','mover'),('build/system/rsxschedule.bin','scheduler'),('build/system/rsxcommit.bin','commit')]:
        target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(images[name][0])
    prior_root=regression.ROOT
    try:
        regression.ROOT=root
        regression.main()
    finally:
        regression.ROOT=prior_root
    metrics['projected_allocation_delta_bytes']=metrics['experimental_payload_rounded_with_descriptors_bytes']-metrics['baseline_ansi_allocation_bytes']
    metrics['bios_free_bytes']=metrics['bios_region_bytes']-metrics['bios_bytes']
    metrics['bdos_free_bytes']=metrics['bdos_region_bytes']-metrics['bdos_bytes']
    metrics['bridge_bytes']=results[0]['bridge_bytes']
    from importlib.metadata import version
    report={'python_version':sys.version.split()[0],'test_dependencies':{name:version(name) for name in ('pyte','wcwidth')},'status':'PASS', 'feasibility_disposition':'BLOCKED_FOR_PRODUCTION_PLACEMENT_AND_CARRIER_PACKAGING','experimental_interface':'XTCP 0.1 subset, not TCAP candidate ABI',
            'metrics':metrics,'runs':results,'existing_commit_regression':'PASS','source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (HERE/'owner.inc',HERE/'coordinator.mac',HERE/'campaign.py',ROOT/'src/bdos/unified.mac',ROOT/'src/bios/bios.mac',ROOT/'src/rsx/ansi.mac',ROOT/'src/rsx/ansi-dispatch.inc',ROOT/'src/rsx/screen/rendition.inc',ROOT/'src/rsx/screen/model4.mac',ROOT/'src/rsx/screen/ansi-host.mac',ROOT/'src/system/r3comit.mac',ROOT/'src/system/rsxsched.mac',ROOT/'src/system/rsxmover.mac')},
            'assembler_sha256':hashlib.sha256(args.assembler.read_bytes()).hexdigest(),
            'image_sha256':{name:hashlib.sha256(pair[0]).hexdigest() for name,pair in images.items()},
            'limits':['CPU/model evidence only; no live/native/ROM qualification',
                      'injected safe-stack return and routing/commit bridges, not production manager/reloader wiring',
                      'host fixture uses shared Model 4 BIOS router with host-output hardware leaf substitution, not a complete cpmsim BIOS',
                      'actual BRSX packaging rejected; raw rebased images are CPU-test inputs only',
                      'fixture-issued validity identity; global allocator, full request ABI and admission not implemented',
                      'bridge has no placement in current packed resident image; no production TPA claim',
                      'no TYPE/TED/HELP migration or distribution changes']}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
