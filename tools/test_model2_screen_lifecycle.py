#!/usr/bin/env python3
"""Execute Model II profile mutations with the real overlay pack and a fixture filesystem."""
import json
import struct
from pathlib import Path
from build_z80pack_image import symbols
from build_ccp import assemble
import tempfile
from system_layout import CONTEXT, LAYOUT as L
from test_rsx_disk_cache import DiskMachine
from test_model2_screen import variant

ROOT=Path(__file__).resolve().parents[1]


def main():
    if not CONTEXT or CONTEXT[0]['target']!='trs80m2':
        raise SystemExit('run from the staged Model II build with BETTERCPM_BUILD_CONTEXT set')
    m=DiskMachine()
    out=ROOT/'build'
    for name,addr in [('bios',L['BIOS']),('disk',L['DISK']),('extensions',L['EXTENSIONS'])]:
        data=(out/'trs80m2'/(name+'.bin')).read_bytes()
        m.mem[addr:addr+len(data)]=data
    m.run(L['BIOS']+72)
    binding=symbols(out/'trs80m2/bios.lst')['MP_MON']
    # Function 177 loads checked package records 76..83 via BIOS+60. Only
    # the physical read is replaced; execute the production CRC, private-ID
    # check, stack change, transaction and resolver-recovery epilogue.
    m.mem[0x8200:0x8600]=(out/'system/R3ENTRY.RSX').read_bytes()
    m.mem[L['DISK']+15:L['DISK']+18]=bytes.fromhex('c30093')
    source="""        ORG 9300H
        LD A,D
        OR A
        JR NZ,BAD
        LD A,E
        CP 76
        JR NZ,BAD
        LD A,B
        CP 8
        JR NZ,BAD
        EX DE,HL
        LD HL,8200H
        LD BC,1024
        LDIR
        XOR A
        RET
BAD:    LD A,1
        OR A
        RET
        END
"""
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)
        raw=assemble(Path.home()/'bin/z80asm',source,path/'raw.bin',path/'raw.lst',0x9300)
    m.mem[0x9300:0x9300+len(raw)]=raw
    for name in ('M2SCRN','ADM3A','VT52','ANSI','HELLO'):
        m.files[0,0,name+'.RSX']=(out/'rsx'/(name+'.RSX')).read_bytes()
    def change(op,name):
        at=0x300
        request=bytes((3,op,0,0))+name.encode().ljust(8,b' ')+bytes(2)+struct.pack('<HHBB',0x405,0x7000,0,0)
        m.mem[at:at+len(request)]=request
        m.pair('DE',at);m.reg['C'].value=177
        return m.run(L['EXTENSIONS'])
    resolver_size=(out/'system/rsxresolver.bin').stat().st_size
    def state():
        # Compare published state, module bytes, the callable binding, the
        # entire linked resolver and the gateway. The rest is stack/padding.
        return (m.chain(),m.word(binding),bytes(m.mem[L['RSX']:L['RSX']+resolver_size]),
                bytes(m.mem[L['RSX']+0x3fd:L['RSX']+0x400]))
    base=m.word(6)
    assert base==0xe101
    assert change(1,'HELLO')==0
    tops={'unloaded':base,'HELLO':m.word(6)}
    assert change(2,'HELLO')==0 and m.word(6)==base
    assert change(1,'M2SCRN')==0
    top=m.word(6);tops['M2SCRN']=top
    for name in ('ADM3A','VT52','ANSI'):
        assert change(1,name)==0
        tops['M2SCRN+'+name]=m.word(6)
        before=state()
        for args in ({'cap':1},{'foreign':True},{'public':True}):
            bad=bytearray(variant(m.files[0,0,'M2SCRN.RSX'],**args))
            bad[32:40]=b'BADSCRN '
            m.files[0,0,'BADSCRN.RSX']=bytes(bad)
            assert change(1,'BADSCRN')!=0 and state()==before,(name,args)
        assert change(2,name)==0 and m.word(6)==top
    assert change(2,'M2SCRN')==0 and m.mem[L['RSX_STATE']]==0 and m.word(6)==base
    print(json.dumps({name:{'top':f'{addr:04X}','record_aligned_bytes':(addr-256)//128*128}
                      for name,addr in tops.items()},indent=2))


if __name__=='__main__':
    main()
