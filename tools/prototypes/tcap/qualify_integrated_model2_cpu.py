"""Qualify compact native ADM3A admission and mapped-stack safety on Model II."""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_z80pack_image import symbols
from checked_build_contract import load_contract
from checked_carriers import rsx_metadata
from test_model2_screen import Core,variant
from tcap_test_support import sha
from integrated_source import display_source


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--personality',choices=('ADM3A','VT52','ANSI'),default='ADM3A')
    p.add_argument('--inline-cache',action='store_true')
    a=p.parse_args()
    workspace,out=a.workspace.resolve(),a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    bios=symbols(workspace/'build/trs80m2/bios.lst')
    context=json.loads((workspace/'build/profile/context.json').read_text())
    contract=load_contract(workspace,Path.home()/'bin/z80asm')
    source=display_source(a.personality.lower())
    source=('M2BANK EQU 1\nCRT_POS EQU 0%04XH\nCRT_COL EQU 0%04XH\n'%(bios['M2_POS'],bios['M2_COL']))+source
    assembler=Path.home()/'bin/z80asm'
    code=assemble(assembler,source,out/'native.bin',out/'native.lst',0x8000)
    alt=assemble(assembler,source.replace('08000H','08101H'),out/'alt.bin',out/'alt.lst',0x8101)
    table=symbols(out/'native.lst')
    carrier=bytearray(make_module(name=a.personality,version=(0,1),services=[],linked_base=0x8000,
        code=code,relocations=relocation_offsets(code,alt,0x101),reconstruction_class='STATEFUL',
        init_offset=table['D_HOME']-0x8000 if a.personality in ('VT52','ANSI') else 0xffff,
        cache_footer_inline=a.inline_cache,
        callable_services=[(b'MCON',1,0,table['D_ENTRY']-0x8000,4),
                           (b'TCAP',2,0,table['D_TCAP']-0x8000,0)]))
    at=int.from_bytes(carrier[30:32],'little')
    carrier[4]=3
    carrier=bytes(carrier[:at])+rsx_metadata(a.personality,bytes(carrier[at:]),contract)
    (out/(a.personality+'.RSX')).write_bytes(carrier)
    allocation=int.from_bytes(carrier[14:16],'little')+(0 if a.inline_cache else 256)
    assert allocation+159+67<=(1792 if a.personality=='ANSI' else 1280)
    cpu_dir=out/'cpu'
    cpu_dir.mkdir(exist_ok=True)
    cpu=Core(cpu_dir,Path.home()/'projects/git/z80pack')
    layout=context['symbols']
    cpu.put(layout['LY_SYS'],(workspace/'build/trs80m2/resident.bin').read_bytes())
    cpu.put(1,struct.pack('<H',layout['LY_BIOS']+3))
    assert cpu.admit(workspace/'build/system',layout['LY_CFG'],carrier)==0
    assert cpu.admit(workspace/'build/system',layout['LY_CFG'],variant(carrier,public=True))==2
    assert cpu.admit(workspace/'build/system',layout['LY_CFG'],variant(carrier,foreign=True))==1
    for capability in (0,1,2,3,5,6,7,0x104):
        bad=bytearray(carrier);at=bad.index(b'MCON',int.from_bytes(bad[30:32],'little'))
        bad[at+8:at+10]=capability.to_bytes(2,'little')
        assert cpu.admit(workspace/'build/system',layout['LY_CFG'],bytes(bad))==2,capability
    checks=0
    for base in (0x6100,0x9200):
        for enabled in (0,3):
            cpu.load_module(carrier,base)
            entry=table['D_ENTRY']+base-0x8000
            tcap=table['D_TCAP']+base-0x8000
            cpu.put(bios['M2_POS'],struct.pack('<H',0xf800))
            cpu.put(bios['M2_COL'],b'\0')
            cpu.video[:]=b' '*2048
            protected=bytearray(i%253 for i in range(2048))
            cpu.put(0xf800,protected)
            for sp in (0x7800,0xfef0):
                def invoke(op,c=0,b=0,portable=False):
                    nonlocal checks
                    cpu.r['IFF'].value=enabled
                    result=cpu.run(tcap if portable else entry,sp=sp,A=op,B=b,C=c)
                    assert cpu.r['IFF'].value==enabled and cpu.mapped.value==0 and cpu.faults.value==0
                    assert bytes(cpu.mem[table['D_SP']+base-0x8000:table['D_SP']+base-0x8000+2])==b'\0\0'
                    assert cpu.mem[table['D_GUARD']+base-0x8000]==0xa5
                    # Only the caller's return and saved-IFF words may change
                    # upper RAM. VRAM operations must not touch its other bytes.
                    for i,v in enumerate(protected):
                        if not sp-4<=0xf800+i<sp:
                            assert cpu.mem[0xf800+i]==v,(base,sp,i)
                    checks+=1
                    return result
                invoke(4)
                assert invoke(0,b=86,c=120,portable=True)==0
                assert cpu.r['B'].value==86 and cpu.r['C'].value==120
                facts=cpu.r['H'].value*256+cpu.r['L'].value
                vt=a.personality=='VT52'
                assert bytes(cpu.mem[facts:facts+8])==b'TC'+bytes((2,8,24,80,7 if vt else 15,0 if vt else 2))
                protocol=b'\x1bY\x24\x29TCAP TEXT' if vt else b'\x1b=\x24\x29\x0fTCAP TEXT\x0e'
                if a.personality=='ANSI':protocol=b'\x1b[5;10H\x1b[7mTCAP TEXT\x1b[0m'
                for c in protocol:invoke(0,c)
                assert bytes(cpu.video[329:338])==bytes(c|(0 if vt else 128) for c in b'TCAP TEXT')
                if a.personality=='ANSI':
                    cpu.r['D'].value,cpu.r['E'].value=0x53,0x79
                    assert invoke(3)==1 and invoke(3,ord('K'))==1
                    assert cpu.video[338]==(ord('K')|128)
                    assert (cpu.r['D'].value,cpu.r['E'].value)==(0x53,0x79)
                assert invoke(2,b=23,c=79,portable=True)==0
                invoke(0,ord('X'))
                if vt:
                    for c in b'\x1bZ':invoke(0,c)
                    assert invoke(1)==255
                    assert bytes(invoke(2) for _ in range(3))==b'\x1b/K'
                    for op in (4,5):assert invoke(op,portable=True)==2
                else:
                    if a.personality=='ANSI':
                        for c in b'\x1b[3;8r\x1b[8;1H\x1bD\x1b[3;1H\x1bM\x1b[1J\x1b[2K':invoke(0,c)
                    else:invoke(0,28);invoke(0,29)
                    for op in (4,5):assert invoke(op,portable=True)==0
                for op in (1,3,6,7):assert invoke(op,portable=True)==0
                before=bytes(cpu.video)
                assert invoke(2,b=24,c=0,portable=True)==3
                assert invoke(2,b=0,c=80,portable=True)==3
                assert invoke(8,portable=True)==255
                assert bytes(cpu.video)==before
    report={'status':'PASS private integrated Model II admission, overlay, stack and interrupt checks',
            'checks':checks,'load_addresses':[0x6100,0x9200],'entry_stack_addresses':[0x7800,0xfef0],
            'interrupt_states':[0,3],'payload_bytes':len(code),'resident_profile_bytes':allocation,
            'helper_bytes':159,'full_budgeted_path_bytes':allocation+159+67,
            'personality':a.personality,'private_stack_bytes':table['D_TOP']-table['D_STACK'],
            'stack_guard_intact':True,'inline_cache_ownership':a.inline_cache,
            'carrier_sha256':sha(out/(a.personality+'.RSX')),
            'compatibility_id':contract['compatibility_id'],
            'scope':'CPU and actual carrier/metadata validators; full-machine load/unload and installation remain unqualified'}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
