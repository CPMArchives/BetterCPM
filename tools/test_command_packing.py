#!/usr/bin/env python3
"""Check host packing and execute the emitted bounded CCP bootstrap/fixups."""
import json
import random
import types
from pathlib import Path
from command_packing import pack,unpack
from test_bios import Z80
from build_z80pack_image import symbols

ROOT=Path(__file__).resolve().parents[1]


def main():
    rng=random.Random(1300)
    for data in (b'',b'x',b'x'*512,bytes(range(256))*20,
                 bytes(rng.randrange(256) for _ in range(4097))):
        assert unpack(pack(data),len(data))==data
    for raw,n in ((b'\0\0',2),(b'\0\x80',3),(b'\1',1),
                  (b'\1x\0',1),(b'\x81x',1),(b'\1x\0',2)):
        try:unpack(raw,n)
        except ValueError:pass
        else:raise AssertionError(('malformed stream accepted',raw,n))
    carrier=(ROOT/'build/ccp/ccp.rlm').read_bytes()
    inner=(ROOT/'build/ccp/ccp-inner.rlm').read_bytes()
    original=(ROOT/'build/ccp/ccp.bin').read_bytes()
    info=json.loads((ROOT/'build/ccp/packing.json').read_text())
    labels=symbols(ROOT/'build/ccp/packed-body.lst')
    size=int.from_bytes(inner[8:10],'little')
    def load(base):
        c=Z80(b'');c.sp=0x1000
        header=carrier[5]*512
        payload=carrier[header:header+int.from_bytes(carrier[8:10],'little')]
        c.mem[base:base+len(payload)]=payload
        for i in range(int.from_bytes(carrier[14:16],'little')):
            off=int.from_bytes(carrier[16+2*i:18+2*i],'little')
            c.setword(base+off,(c.word(base+off)+base-0xbb00)&65535)
        return c
    for base in (0x3000,0x5001,0x7137):
        c=load(base)
        c.mem[base-8:base]=b'L'*8
        end=base+info['allocation'];c.mem[end:end+8]=b'R'*8
        types.FunctionType(Z80.run.__code__,dict(Z80.run.__globals__,SENTINEL=base+info['output_offset']))(c,base,500000)
        expected=bytearray(original[:size])
        for i in range(int.from_bytes(inner[14:16],'little')):
            off=int.from_bytes(inner[16+2*i:18+2*i],'little')
            value=int.from_bytes(expected[off:off+2],'little')
            expected[off:off+2]=((value+base+info['output_offset']-0xbb00)&65535).to_bytes(2,'little')
        assert c.mem[base+info['output_offset']:base+info['output_offset']+size]==expected
        from system_layout import LAYOUT
        assert c.word(LAYOUT['SYSTEM']+0x8c)==base+info['output_offset']
        assert c.word(LAYOUT['SYSTEM']+0x8e)==info['inner_allocation']
        assert c.mem[base-8:base]==b'L'*8 and c.mem[end:end+8]==b'R'*8
    # Bypass authentication only to exercise the decoder's own fail-closed bounds.
    for mutation in ('backreference','truncated','output-overrun','relocation-bound'):
        base=0x5001;c=load(base);out=[]
        from test_ccp import install_bdos
        install_bdos(c,b'\xd3\xff\xc9')
        def write(port,value):
            if c.c==9:out.append(bytes(c.mem[c.de:c.mem.index(36,c.de)]))
        c.port_write=write
        data_at=base+info['prefix']+(labels['PDATA']-(0xbb00+info['prefix']))
        if mutation=='backreference':c.mem[data_at:data_at+2]=b'\0\0'
        elif mutation=='truncated':
            off=base+info['prefix']+labels['PSOURCE']-(0xbb00+info['prefix'])
            c.setword(off,base+labels['PEND']-0xbb00)
        elif mutation=='output-overrun':
            # LD BC,decoded size at bootstrap-body +3.
            c.setword(base+info['prefix']+4,1)
        else:
            off=base+info['prefix']+labels['PPREV']-(0xbb00+info['prefix'])
            c.setword(off,0xffff)
        try:types.FunctionType(Z80.run.__code__,dict(Z80.run.__globals__,SENTINEL=base+info['output_offset']))(c,base,500000)
        except AssertionError as error:assert 'execution limit reached' in str(error),error
        else:raise AssertionError(('corruption reached command entry',mutation))
        assert out and b'cold boot required' in out[-1],(mutation,out)
    print('PASS host short/long/overlap streams, emitted bootstrap at three bases, exact inner fixups, canaries and malformed bounds')


if __name__=='__main__':main()
