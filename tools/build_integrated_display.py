"""Build one unloadable personality plus renderer for an existing system.

No resident core reservation, release profile or utility migration is introduced.
Checked systems receive their existing exact private carrier binding.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_z80pack_image import symbols
from checked_build_contract import load_contract
from checked_carriers import rsx_metadata
from component_registry import module_version

ROOT=Path(__file__).resolve().parents[1]


def source(personality,backend):
    folder=ROOT/'src/rsx/compact'
    text=(folder/(personality.lower()+'.mac')).read_text()
    marker='        INCLUDE display-renderer.inc'
    assert text.count(marker)==1
    renderer=('ansi-' if personality.upper()=='ANSI' else '')+backend
    text=text.replace(marker,(folder/(renderer+'.inc')).read_text())
    return ('HOSTTERM EQU %d\n'%(backend=='host') if personality.upper()=='ANSI' else '')+text


def build(workspace,out,platform,personality='ADM3A',assembler=None,inline_cache=False):
    assembler=assembler or Path.home()/'bin/z80asm'
    workspace,out=Path(workspace).resolve(),Path(out).resolve()
    if inline_cache and 'CACHE_INLINE_1' not in (workspace/'src/system/r3cache.mac').read_text():
        raise ValueError('the selected system does not support explicit inline cache ownership')
    out.mkdir(parents=True,exist_ok=True)
    host=platform=='cpmsim';m2=platform=='model2'
    preamble='M2BANK EQU %d\n'%m2
    if not host:
        bios=symbols(workspace/('build/trs80m2/bios.lst' if m2 else 'build/bios/bios.lst'))
        pos,col=('M2_POS','M2_COL') if m2 else ('M4CURSOR','M4COLUMN')
        assert not m2 or max(bios[pos]+1,bios[col])<0xf800
        preamble+='CRT_POS EQU 0%04XH\nCRT_COL EQU 0%04XH\n'%(bios[pos],bios[col])
    text=preamble+source(personality,'host' if host else 'crt')
    code=assemble(assembler,text,out/'native.bin',out/'native.lst',0x8000)
    alternate=assemble(assembler,text.replace('08000H','08101H'),out/'alternate.bin',out/'alternate.lst',0x8101)
    labels=symbols(out/'native.lst')
    carrier=make_module(name=personality,version=module_version(personality),services=[],linked_base=0x8000,code=code,
        relocations=relocation_offsets(code,alternate,0x101),reconstruction_class='STATEFUL',
        init_offset=labels['D_ACTIVATE']-0x8000,
        cache_footer_inline=inline_cache,
        callable_services=[(b'MCON',1,0,labels['D_ENTRY']-0x8000,2 if host else 4 if m2 else 1),
                           (b'TCAP',2,0,labels['D_TCAP']-0x8000,0)])
    context=workspace/'build/profile/context.json'
    contract=None
    if context.exists():
        contract=load_contract(workspace,assembler)
        # This builder can run outside the prepared workspace. Avoid adding a
        # second binding if make_module already inherited that exact context.
        if carrier[4]==2:
            item=bytearray(carrier);at=int.from_bytes(item[30:32],'little');item[4]=3
            carrier=bytes(item[:at])+rsx_metadata(personality,bytes(item[at:]),contract)
    (out/(personality+'.RSX')).write_bytes(carrier)
    helpertext=(ROOT/'src/utilities/common/tcap2.inc').read_text()
    helper=assemble(assembler,'        ASEG\n        ORG 0100H\n'+helpertext+'\n        END\n',
        out/'client.bin',out/'client.lst',0x100)
    table=symbols(out/'client.lst')
    resident=int.from_bytes(carrier[14:16],'little')+(0 if inline_cache else 256)
    report={'personality':personality,'platform':platform,'service':'TCAP 2.0',
        'payload_bytes':len(code),'resident_profile_bytes':resident,
        'helper_code_bytes':table['T2_CODE_END']-table['T2_OPEN'],
        'helper_data_bytes':table['T2_END']-table['T2_CODE_END'],
        'helper_bytes':len(helper),'shared_bios_state_bytes':0 if host else 3,
        'call_site_allowance_bytes':32,'stack_allowance_bytes':32,
        'full_path_limit_bytes':1792 if personality=='ANSI' else 1280,
        'full_budgeted_path_bytes':resident+len(helper)+(0 if host else 3)+64,
        'generic_rsx_bytes_excluded':1024,'permanent_display_reservation_bytes':0,
        'cache_footer_bytes':10,'inline_cache_ownership':inline_cache,
        'compatibility_id':None if contract is None else contract['compatibility_id'],
        'payload_sha256':hashlib.sha256(code).hexdigest(),
        'carrier_sha256':hashlib.sha256(carrier).hexdigest(),
        'expanded_source_sha256':hashlib.sha256(text.encode()).hexdigest()}
    assert report['full_budgeted_path_bytes']<=report['full_path_limit_bytes'],report
    (out/'footprint.json').write_text(json.dumps(report,indent=2)+'\n')
    return carrier,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace',type=Path)
    p.add_argument('--platform',choices=('cpmsim','model4','model2'),required=True)
    p.add_argument('--personality',choices=('ADM3A','VT52','ANSI'),default='ADM3A')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--inline-cache',action='store_true')
    a=p.parse_args();_,report=build(a.workspace,a.output,a.platform,a.personality,inline_cache=a.inline_cache)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
