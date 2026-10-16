#!/usr/bin/env python3
"""Build/run isolated universal-personality and unloadable-backend prototypes.

CPU execution tests real assembled core/backend instructions. Profile binding
below is a host model, not production RSX dependency/lifecycle integration.
"""
import hashlib
import json
import tempfile
import struct
import test_rsx_stage3 as stage
from pathlib import Path
import pyte
from audit_vt52_screen_backend import SOURCE as M4_SOURCE
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80
from test_vt52_foundation import symbols

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/audit/unloadable-monitor-backend'
ASM=Path.home()/'bin/z80asm'
PROTOTYPES=ROOT/'src/prototypes/monitor-backend'


def build(name,text,entry,capabilities,identity):
    code=assemble(ASM,text,OUT/(name+'.bin'),OUT/(name+'.lst'),0x8000)
    alt=assemble(ASM,text.replace('ORG 08000H','ORG 08101H'),OUT/(name+'-alt.bin'),OUT/(name+'-alt.lst'),0x8101)
    relocs=relocation_offsets(code,alt,0x101)
    syms=symbols(OUT/(name+'.lst'))
    carrier=make_module(name=name,version=(0,1),services=[],linked_base=0x8000,
        code=code,relocations=relocs,reconstruction_class='STATEFUL',
        callable_services=[(identity,1,0,syms[entry]-0x8000,capabilities)])
    (OUT/(name+'.RSX')).write_bytes(carrier)
    return dict(name=name,code=code,relocs=relocs,syms=syms,entry=syms[entry]-0x8000,
                allocation=int.from_bytes(carrier[14:16],'little'),
                carrier_bytes=len(carrier),sha256=hashlib.sha256(carrier).hexdigest())


def relocate(cpu,module,base):
    data=bytearray(module['code'])
    for slot in module['relocs']:
        value=int.from_bytes(data[slot:slot+2],'little')+base-0x8000
        data[slot:slot+2]=value.to_bytes(2,'little')
    cpu.mem[base:base+len(data)]=data


def allocation_probe(core,backend):
    """Real manager memory test; deliberately demonstrates missing dependency gate."""
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 (backend['name'].ljust(8),str((OUT/(backend['name']+'.RSX')).relative_to(ROOT))),
                 (core['name'].ljust(8),str((OUT/(core['name']+'.RSX')).relative_to(ROOT))))
    biosdir=ROOT/('build/bios' if backend['name']=='PM4SCR' else 'build/audit/release-090-z80pack')
    cpu=Z80((biosdir/'bios.bin').read_bytes())
    for (_,path),address in zip(stage.FILES,(0x7800,0xB800,0xBC00)):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:
        stub=stage.file_stub(Path(temporary),(0x7800,0xB800,0xBC00))
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[LAYOUT['BIOS']+60:LAYOUT['BIOS']+63]=b'\xaf\xc9\0'
    cpu.run(LAYOUT['BIOS']+72)
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),
                          (stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    def change(op,name):
        stage.invoke(cpu,bootstrap,op,name.ljust(8).encode())
        assert cpu.a==0,(op,name,cpu.a)
    change(1,backend['name']);change(1,core['name'])
    loaded_tpa=cpu.word(6)-256
    change(2,backend['name'])
    # Current manager has no declared backend dependency and accepts this.
    missing_gate_confirmed=True
    change(2,core['name'])
    assert cpu.word(6)==LAYOUT['TPA'] and cpu.word(stage.TPA)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    return dict(core=core['name'],backend=backend['name'],loaded_tpa_bytes=loaded_tpa,
                unloaded_tpa_bytes=cpu.word(6)-256,
                dependency_removal_not_yet_blocked=missing_gate_confirmed)


def record(role,platform,base,length,offset,major=1,minor=0):
    return struct.pack('<BBBBHHH',role,platform,major,minor,base,length,offset)


def test_binder(code):
    f=record(1,0,0x6000,512,400)
    b=record(2,1,0x6500,256,12)
    tests=[([],True),([b],True),([f,b],True),([b,f],True),([f],False),
           ([f,f,b],False),([f,b,b],False),
           ([f,record(2,2,0x6500,256,12)],False),
           ([record(1,1,0x6000,512,400),b],False),
           ([record(1,0,0x6000,512,511),b],False),
           ([record(1,0,0x6000,512,7),b],False),
           ([f,record(2,1,0x6500,256,256)],False),
           ([f,record(2,1,0xFFF8,256,12)],False),
           ([f,record(2,1,0x6500,256,12,major=2)],False),
           ([f,record(2,1,0x6500,256,12,minor=1)],False)]
    for records,ok in tests:
        cpu=Z80(b'');cpu.mem[0x7000:0x7000+len(code)]=code
        data=b''.join(records);cpu.mem[0x7400:0x7400+len(data)]=data
        cpu.mem[0x6000:0x6900]=b'\xa5'*0x900
        before=bytes(cpu.mem[0x6000:0x6900])
        cpu.hl=0x7400;cpu.bc=len(records)*256+1
        cpu.run(0x7000,limit=20000)
        assert (cpu.a==0)==ok,(records,cpu.a)
        assert bytes(cpu.mem[0x6000:0x6900])==before,'preparation mutated live payload'
        if ok and f in records:assert (cpu.de,cpu.hl)==(0x6190,0x650c)
    return len(tests)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    binder=assemble(ASM,(PROTOTYPES/'bind-plan.mac').read_text(),OUT/'bind-plan.bin',OUT/'bind-plan.lst',0x7000)
    binder_cases=test_binder(binder)
    m4syms=symbols(ROOT/'build/bios/bios.lst')
    bindings=''.join(f'{name} EQU 0{m4syms[name]:04X}H\n' for name in ['MC_RAW','M4CURSOR','M4COLUMN'])
    header='''        ORG 08000H
B_NEXT: DW 5
B_DISP: DW B_CHAIN
        DW 0,0
B_CHAIN:
        LD HL,(B_NEXT)
        JP (HL)
'''
    m4text=bindings+M4_SOURCE.replace('        ORG 07000H',header)
    backends=[build('PM4SCR',m4text,'SB_ENTRY',1,b'SCRN'),
              build('PANSCR',(PROTOTYPES/'ansi-screen.mac').read_text(),'SB_ENTRY',2,b'SCRN')]
    cores=[build(name,f'MODE EQU {mode}\n'+(PROTOTYPES/'personality.mac').read_text(),
                 'P_ENTRY',0,b'PMON') for mode,name in enumerate(['PADM3A','PVT52','PANSI'])]
    cases=0
    transport_samples=[]
    for backend in backends:
        for core in cores:
            # Use the same exact core bytes for both targets, at two placements.
            for corebase,backbase in [(0x6000,0x6500),(0x8101,0x8701)]:
                cpu=Z80(b'')
                biosdir=ROOT/('build/bios' if backend['name']=='PM4SCR' else 'build/audit/release-090-z80pack')
                biossyms=symbols(biosdir/'bios.lst');biosbase=biossyms['MONRAW']-69
                data=(biosdir/'bios.bin').read_bytes()
                cpu.mem[biosbase:biosbase+len(data)]=data;cpu.setword(1,biosbase+3)
                relocate(cpu,backend,backbase);relocate(cpu,core,corebase)
                slot=corebase+core['syms']['P_BACKEND']-0x8000
                # Execute the candidate preparer; publication is host-modeled.
                cpu.mem[0x7000:0x7000+len(binder)]=binder
                records=(record(1,0,corebase,len(core['code']),slot-corebase)+
                         record(2,1 if backend['name']=='PM4SCR' else 2,backbase,len(backend['code']),backend['entry']))
                cpu.mem[0x7400:0x7400+len(records)]=records
                cpu.hl=0x7400;cpu.bc=0x200+(1 if backend['name']=='PM4SCR' else 2)
                cpu.run(0x7000,limit=20000)
                assert cpu.a==0 and cpu.de==slot and cpu.hl==backbase+backend['entry']
                cpu.setword(cpu.de,cpu.hl)
                screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
                emitted=[]
                def output(port,value):
                    assert port&255==1
                    emitted.append(value);stream.feed(chr(value))
                cpu.port_write=output
                def call(op,char=0):
                    sp=cpu.sp;cpu.a=op;cpu.c=char
                    cpu.run(corebase+core['entry'],limit=200000)
                    assert cpu.sp==sp
                def send(data):
                    for byte in data:call(0,byte)
                def address(row,col):
                    if core['name']=='PANSI':send(f'\x1b[{row+1};{col+1}H'.encode())
                    else:send(bytes([27,ord('=') if core['name']=='PADM3A' else ord('Y'),row+32,col+32]))
                def snapshot():
                    if backend['name']=='PM4SCR':return [''.join(chr(b&127) for b in cpu.mem[0xF800+r*80:0xF850+r*80]) for r in range(24)]
                    return screen.display
                def cursor():
                    if backend['name']=='PM4SCR':return divmod(cpu.word(m4syms['M4CURSOR'])-0xF800,80)
                    return screen.cursor.y,screen.cursor.x
                call(4)
                address(5,10);send(b'MARK')
                assert snapshot()[5][10:14]=='MARK' and cursor()==(5,14)
                address(7,79);send(b'AB')
                if core['name']=='PVT52':assert snapshot()[7][79]=='B' and cursor()==(7,79)
                else:assert snapshot()[7][79]=='A' and snapshot()[8][0]=='B' and cursor()==(8,1)
                # Erasure from a partial row and EOS on both targets.
                address(10,0);send(b'KEEP remove');address(10,4)
                send(b'\x15' if core['name']=='PADM3A' else (b'\x1bK' if core['name']=='PVT52' else b'\x1b[0K'))
                assert snapshot()[10]=='KEEP'+' '*76 and cursor()==(10,4)
                address(12,0);send(b'clear');address(12,0)
                send(b'\x17' if core['name']=='PADM3A' else (b'\x1bJ' if core['name']=='PVT52' else b'\x1b[0J'))
                assert all(line==' '*80 for line in snapshot()[12:])
                call(4)
                for row in range(24):address(row,0);send(bytes([65+row]))
                address(23,12);send(b'\n')
                assert snapshot()[0][0]=='B' and snapshot()[23]==' '*80 and cursor()==(23,12)
                if core['name']=='PVT52':
                    address(0,12);send(b'\x1bI')
                    assert snapshot()[0]==' '*80 and snapshot()[1][0]=='B' and cursor()==(0,12)
                if core['name']!='PVT52':
                    address(3,0);send(b'\x0f' if core['name']=='PADM3A' else b'\x1b[7m');send(b'R')
                    if backend['name']=='PM4SCR':assert cpu.mem[0xF800+3*80]==ord('R')|128
                    else:assert screen.buffer[3][0].reverse
                # Interrupted address reset does not consume returning text.
                address(4,5);send(b'\x1b[' if core['name']=='PANSI' else (b'\x1b=' if core['name']=='PADM3A' else b'\x1bY'))
                call(5);send(b'X');assert snapshot()[4][5]=='X'
                if core['name']=='PADM3A':send(b'\x0e')
                elif core['name']=='PANSI':send(b'\x1b[0m')
                call(4);emitted.clear();send(b'X'*80)
                transport_samples.append(dict(core=core['name'],backend=backend['name'],
                    placement=corebase,wire_bytes_for_80_char_line=len(emitted)))
                cases+=1
    rows=[{k:v for k,v in module.items() if k not in ['code','relocs','syms','entry']}|
          dict(payload=len(module['code']),relocations=len(module['relocs'])) for module in cores+backends]
    allocations=[allocation_probe(core,backend) for core in cores for backend in backends]
    report=dict(modules=rows,allocation_probes=allocations,binding_preparer_bytes=len(binder),binding_cases=binder_cases,transport_samples=transport_samples,cross_platform_runs=cases,permanent_prototype_growth=0,
                note='Z80 binding preparer tested; publication host-modeled. PMON deliberately differs from production MCON. No production integration claimed.')
    (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
