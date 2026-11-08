"""Build/cost the integrated ADM3A experiment and compare its actual CPU output.

Uses the qualified portable ADM3A+M4SCRN implementation as the independent
behavioral reference. This CPU fixture is not boot or installation qualification.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from build_ccp import assemble
from build_z80pack_image import symbols
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
import test_adm3a_foundation as foundation
from test_adm3a_foundation import bind_backend
from test_bios import Z80
from system_layout import LAYOUT
from test_usq import SHIM
from integrated_source import display_source


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'build/integrated-adm3a')
    p.add_argument('--coordinates', action='store_true', help='also compare all 65,536 coordinate pairs')
    p.add_argument('--reference-workspace',type=Path,default=ROOT)
    a = p.parse_args()
    reference = a.reference_workspace.resolve()
    foundation.ROOT = reference
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bios = symbols(reference/'build/bios/bios.lst')
    source = ROOT/'src/rsx/compact/adm3a.mac'
    text = ('M2BANK EQU 0\nCRT_POS EQU 0%04XH\nCRT_COL EQU 0%04XH\n' % (bios['M4CURSOR'], bios['M4COLUMN']))+display_source()
    assembler = Path.home()/'bin/z80asm'
    code = assemble(assembler, text, out/'native.bin', out/'native.lst', 0x8000)
    alternate = assemble(assembler, text.replace('08000H','08101H'), out/'alternate.bin', out/'alternate.lst', 0x8101)
    table = symbols(out/'native.lst')
    fixes = relocation_offsets(code, alternate, 0x101)
    carrier = make_module(name='XTADM', version=(0,1), services=[], linked_base=0x8000,
                          code=code, relocations=fixes, reconstruction_class='STATEFUL',
                          callable_services=[(b'MCON',1,0,table['D_ENTRY']-0x8000,1),
                                             (b'TCAP',2,0,table['D_TCAP']-0x8000,0)])
    (out/'XTADM.RSX').write_bytes(carrier)
    client_source = ROOT/'src/utilities/common/tcap2.inc'
    client = assemble(assembler, '        ASEG\n        ORG 0100H\n'+client_source.read_text()+'\n        END\n',
                      out/'client.bin', out/'client.lst', 0x100)
    allocation = int.from_bytes(carrier[14:16], 'little')+256
    footprint = allocation+len(client)+3+32+32
    assert footprint <= 1280, footprint
    core = Path.home()/'projects/git/z80pack/z80core'
    cpu = out/'cpu'
    cpu.mkdir(exist_ok=True)
    (cpu/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):
        shutil.copy2(core.parent/'z80sim/srcsim'/name,cpu/name)
    shim = SHIM.replace('static WORD readpc, writepc;', 'static WORD readpc, writepc;\nunsigned low_sp;')
    shim = shim.replace('cpu_error=0; tmax=100000000;', 'cpu_error=0; tmax=100000000; low_sp=SP;')
    shim = shim.replace('if(PC==65535) return i;', 'if(SP<low_sp) low_sp=SP;\n  if(PC==65535) return i;')
    (cpu/'shim.c').write_text(shim)
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{cpu}',f'-I{core}',str(cpu/'shim.c'),
                    str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(cpu/'core.so')],check=True)
    lib = C.CDLL(str(cpu/'core.so'))
    mem = (C.c_ubyte*65536).in_dll(lib,'memory')
    regs = {n:C.c_ubyte.in_dll(lib,n) for n in 'AFBCDEHL'}
    sp = C.c_ushort.in_dll(lib,'SP')
    low = C.c_uint.in_dll(lib,'low_sp')
    old_table = symbols(reference/'build/monitor-development/adm3a.lst')
    old_code = (reference/'build/monitor-development/adm3a.bin').read_bytes()
    old_carrier = (reference/'build/monitor-development/ADM3A.RSX').read_bytes()
    old_fixes = [int.from_bytes(old_carrier[48+i*2:50+i*2],'little')
                 for i in range(int.from_bytes(old_carrier[22:24],'little'))]
    base = 0x6000
    def image(binary, relocations, legacy=False):
        machine = Z80((reference/'build/bios/bios.bin').read_bytes())
        patch = bytearray(binary)
        for offset in relocations:
            value = int.from_bytes(patch[offset:offset+2],'little')+base-0x8000
            patch[offset:offset+2] = value.to_bytes(2,'little')
        machine.mem[base:base+len(patch)] = patch
        machine.setword(1,LAYOUT['BIOS']+3)
        machine.setword(bios['M4CURSOR'],0xf800)
        machine.mem[bios['M4COLUMN']] = 0
        if legacy:
            bind_backend(machine,base,old_table)
        return machine.mem
    images = [image(old_code,old_fixes,True),image(code,fixes)]
    entries = [old_table['AM_ENTRY']+base-0x8000,table['D_ENTRY']+base-0x8000]
    maximum_stack = [0,0]
    def invoke(which, op, char=0, *, address=None, row=0):
        C.memmove(C.addressof(mem), (C.c_ubyte*65536).from_buffer(images[which]), 65536)
        for r in regs.values(): r.value = 0
        regs['A'].value,regs['B'].value,regs['C'].value = op,row,char
        sp.value = 0x4000
        result = lib.test_run(entries[which] if address is None else address,2000000)
        assert result >= 0, (which,op,char,result)
        assert sp.value == 0x4000
        maximum_stack[which] = max(maximum_stack[which],0x4000-low.value)
        images[which][:] = bytes(mem)
        return regs['A'].value
    count = 0
    def equal(context):
        for first,last in ((0xf7ff,0xff81),(bios['M4CURSOR'],bios['M4CURSOR']+2),
                           (bios['M4COLUMN'],bios['M4COLUMN']+1)):
            assert images[0][first:last] == images[1][first:last], (context,hex(first),
                [(hex(first+i),x,y) for i,(x,y) in enumerate(zip(images[0][first:last],images[1][first:last])) if x!=y][:8])
    def command(op,char=0):
        nonlocal count
        results = [invoke(i,op,char) for i in (0,1)]
        equal((op,char))
        if op == 3:
            assert results[0] == results[1]
        count += 1
    def send(data):
        for char in data: command(0,char)
    command(4)
    for where in ((0,0),(0,79),(23,0),(23,79),(11,39)):
        for reverse in (14,15):
            for char in range(256):
                send(bytes((27,61,where[0]+32,where[1]+32,reverse,char)))
                command(5)
    for hidden in (48,49):
        send(bytes((27,hidden)))
        command(3)
        command(3,ord('X'))
    for row in range(24):
        for col in (0,39,79):
            for reverse in (14,15):
                for operation in (21,23,26,28,29):
                    pattern=bytes(33+(i//80)%90 for i in range(1920))
                    for image_data in images:
                        image_data[0xf800:0xff80]=pattern
                    send(bytes((27,61,row+32,col+32,reverse,operation)))
    if a.coordinates:
        for row in range(256):
            for col in range(256):
                send(bytes((27,61,row,col)))
    rng=random.Random(20261108)
    send(bytes(rng.randrange(256) for _ in range(5000)))
    # The private portable entry must produce the same display effects as the
    # old protocol path, using the native implementation alone.
    tcap = table['D_TCAP']+base-0x8000
    for op,protocol in ((6,b'\x0e'),(1,b'\x1a'),(4,b'\x0f'),(3,b'\x15'),(5,b'\x0e'),(7,b'\x0e')):
        command(5)
        for c in protocol: invoke(0,0,c)
        assert invoke(1,op,address=tcap) == 0
        equal(('portable',op))
        count += 1
    # Exercise the application library against the actual Function-182 resolver,
    # not a permissive registry mock. Its identifier and ownership checks matter.
    C.memmove(C.addressof(mem),(C.c_ubyte*65536).from_buffer(images[1]),65536)
    resolver=(reference/'build/system/rsxresolver.bin').read_bytes()
    mem[LAYOUT['RSX']:LAYOUT['RSX']+len(resolver)]=resolver
    mem[5:8]=bytes((0xc3,LAYOUT['RSX']&255,LAYOUT['RSX']>>8))
    mem[3]=1
    mem[256:256+len(client)]=client
    def put(address,data):mem[address:address+len(data)]=data
    def runtime(next_dispatch,services):
        put(base,struct.pack('<HHBBH',next_dispatch,base+8,len(services),0,0x300-len(services)*10))
        for i,item in enumerate(services):
            put(base+0x300-len(services)*10+i*10,struct.pack('<4sBBHH',*item))
        put(LAYOUT['SYSTEM']+0x84,struct.pack('<H',base))
    descriptors=[(b'MCON',1,0,table['D_ENTRY']-0x8000,1),
                 (b'TCAP',2,0,table['D_TCAP']-0x8000,0)]
    runtime(LAYOUT['BDOS'],descriptors)
    caller=symbols(out/'client.lst')
    def helper(name,a=0,b=0,c=0,status=0):
        regs['A'].value,regs['B'].value,regs['C'].value=a,b,c
        sp.value=0x4000
        result=lib.test_run(caller[name],100000)
        assert result>=0 and sp.value==0x4000 and regs['A'].value==status,(name,result,regs['A'].value,status)
    helper('T2_OPEN')
    facts=regs['H'].value*256+regs['L'].value
    assert bytes(mem[facts:facts+8])==b'TC'+bytes((2,8,24,80,15,2))
    helper('T2_EMIT',2,4,9)
    assert int.from_bytes(bytes(mem[bios['M4CURSOR']:bios['M4CURSOR']+2]),'little')==0xf800+329
    helper('T2_EMIT',2,24,0,status=3)
    for route in (0,2,3):
        mem[3]=route
        helper('T2_OPEN',status=1)
        helper('T2_EMIT',4,status=1)
    mem[3]=1
    put(caller['T2_LOOK']+4,b'XTN2')
    helper('T2_OPEN',status=1)
    assert mem[caller['T2_LOOK']+19]==8
    put(caller['T2_LOOK']+4,b'TCAP')
    helper('T2_OPEN')
    runtime(0x5008,[descriptors[1]])
    put(0x5000,struct.pack('<HHBBH',LAYOUT['BDOS'],0x5008,1,0,0x80))
    put(0x5080,struct.pack('<4sBBHH',*descriptors[0]))
    mem[table['D_TCAP']+base-0x8000]=0x76
    helper('T2_OPEN',status=1)  # foreign-owner HALT query must not be invoked
    try:
        make_module(name='BADID',version=(0,1),services=[],linked_base=0x8000,
                    code=b'\0'*8+b'\xc9',relocations=[],
                    callable_services=[(b'XTN2',0,1,8,0)])
    except SystemExit:
        pass
    else:
        raise AssertionError('builder admitted an identifier the resolver rejects')
    report={'status':'PASS private integrated ADM3A CPU differential checks',
            'checks':count,'all_coordinate_pairs':a.coordinates,'payload_bytes':len(code),
            'relocations':len(fixes),'resident_including_descriptor_bytes':allocation,
            'application_helper_bytes':len(client),'shared_bios_state_bytes':3,
            'call_site_allowance_bytes':32,'stack_allowance_bytes':32,
            'full_budgeted_path_bytes':footprint,'limit_bytes':1280,
            'maximum_observed_stack_bytes':maximum_stack,
            'prototype_source_sha256':sha(text.encode()),'client_source_sha256':sha(client_source.read_bytes()),
            'actual_resolver_client_checks':'PASS discovery, facts, operations, route refusal, invalid identifier, foreign-owner uncalled HALT',
            'reference_payload_sha256':sha(old_code),'reference_backend_sha256':sha((ROOT/'build/screen-backends/M4SCRN.bin').read_bytes()),
            'scope':'Model 4 CPU output experiment; public ABI, real loader, installation, cpmsim and Model II not yet qualified'}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
