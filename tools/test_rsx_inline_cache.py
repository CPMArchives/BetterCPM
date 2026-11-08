"""Exercise explicit in-allocation cache ownership with the production manager."""
import json
import struct
from pathlib import Path

from build_rsx_module import make_module
from test_rsx_disk_cache import setup,state,L

ROOT=Path(__file__).resolve().parents[1]


def inline(carrier):
    result=bytearray(carrier);result[8]|=4
    return bytes(result)


def main():
    old=setup();original=old.files[1,3,'STATEFUL.RSX']
    assert old.change(1,b'STATEFUL',(1,3))==0
    old_boundary=old.word(6)
    m=setup();baseline=m.word(6)
    m.files[1,3,'STATEFUL.RSX']=inline(original)
    assert m.change(1,b'STATEFUL',(1,3))==0
    assert m.word(6)==old_boundary+256
    allocation=struct.unpack_from('<H',original,14)[0]
    base=m.word(L['SYSTEM']+0x84)
    descriptors=m.word(base+6)
    prefix=allocation-10-m.mem[base+4]*10
    assert descriptors==allocation-m.mem[base+4]*10
    assert m.word(base+descriptors-8)==prefix
    state(m,0)
    size=struct.unpack_from('<H',original,12)[0]
    padding=bytes((i*7)&255 for i in range(prefix-size))
    m.mem[base+size:base+prefix]=padding
    for _ in range(3):state(m,1)
    expected=state(m,2)
    del m.files[1,3,'STATEFUL.RSX']
    assert m.change(1,b'HELLO',(1,0))==0
    assert state(m,2)==expected
    assert m.change(2,b'HELLO',(0,0))==0
    assert state(m,2)==expected
    base=m.word(L['SYSTEM']+0x84)
    assert bytes(m.mem[base+size:base+prefix])==padding
    assert m.change(2,b'STATEFUL',(0,0))==0
    assert m.word(6)==baseline
    # Both reconstruction classes and mixed old/new modules must compose.
    mixed=setup();mixed.files[1,0,'HELLO.RSX']=inline(mixed.files[1,0,'HELLO.RSX'])
    mixed.files[1,3,'STATEFUL.RSX']=inline(original)
    for name,du in ((b'HELLO',(1,0)),(b'STATEFUL',(1,3))):assert mixed.change(1,name,du)==0
    assert mixed.change(2,b'HELLO',(0,0))==0
    assert mixed.change(2,b'STATEFUL',(0,0))==0 and mixed.word(6)==baseline
    # Exact fit, and a word starting one byte too late, exercise the footer
    # boundary rather than merely checking the builder's arithmetic.
    code=bytearray(236);code[8]=0xc9
    exact=make_module(name='TEST',version=(0,1),services=[],linked_base=0x8000,
        code=bytes(code),relocations=[],reconstruction_class='STATEFUL',
        callable_services=[(b'TEST',1,0,8,0)],runtime_pointers=[234],cache_footer_inline=True)
    assert exact[8]==5 and struct.unpack_from('<H',exact,14)[0]==256
    x=setup();x.files[1,0,'TEST.RSX']=exact
    assert x.change(1,b'TEST',(1,0))==0
    assert x.change(2,b'TEST',(0,0))==0
    bad=bytearray(exact)
    meta=struct.unpack_from('<H',bad,30)[0]
    pointer=meta+12+12+2
    assert bad[pointer-2:pointer]==b'\x03\x02'
    bad[pointer:pointer+2]=struct.pack('<H',235)
    cases=[]
    crowded=bytearray(make_module(name='TEST',version=(0,1),services=[],linked_base=0x8000,
        code=bytes(code)+b'\0',relocations=[],reconstruction_class='STATEFUL',
        callable_services=[(b'TEST',1,0,8,0)]));crowded[8]|=4
    reserved=bytearray(exact);reserved[8]|=8
    for label,carrier in [('word-overlaps-footer',bad),('payload-overlaps-footer',crowded),('reserved-flags',reserved)]:
        x=setup();before=x.chain();context=x.context();x.files[1,0,'TEST.RSX']=bytes(carrier)
        assert x.change(1,b'TEST',(1,0))==255,label
        assert x.chain()==before and x.context()==context,label
        cases.append(label)
    for fn in (22,21,16):
        x=setup();x.files[1,3,'STATEFUL.RSX']=inline(original)
        before=x.chain();context=x.context();x.fault=(fn,1)
        assert x.change(1,b'STATEFUL',(1,3))==255,fn
        assert x.chain()==before and x.context()==context,fn
        cases.append('rollback-'+str(fn))
    try:
        make_module(name='TEST',version=(0,1),services=[],linked_base=0x8000,
            code=bytes(code)+b'\0',relocations=[],allocation=256,
            callable_services=[(b'TEST',1,0,8,0)],cache_footer_inline=True)
    except SystemExit:pass
    else:raise AssertionError('builder allowed footer overlap')
    report={'status':'PASS inline cache ownership, relocation, reconstruction, rollback and unload',
        'saved_bytes_per_opted_in_allocation':256,'footer_bytes_charged_in_allocation':10,
        'provider_padding_preserved':True,'source_removed_reconstruction':True,
        'stateful_runtime_pointers_preserved':True,'mixed_stateless_stateful':True,
        'exact_boundary_restored':True,'rejections':cases}
    (ROOT/'build/rsx-inline-cache-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
