#!/usr/bin/env python3
"""Measure a compact checksum-only reloader against an existing Part 8 stage.

This is an experiment, not the complete carrier-migration solution.
"""
from pathlib import Path
import argparse,json,sys

def compact(source):
    first=source.index('        LD      HL,(MOD_LINK)',source.index('CRNCPX:'))
    last=source.index('\n; -------------------------------------------------------------------------------',first)
    source=source[:first]+'''        LD      HL,MOD_LINK
        LD      DE,CRMLINK
        LD      BC,20
        LDIR
        LD      HL,(MODBUF+44)
        LD      (CRMCHECK),HL
'''+source[last:]
    source=source.replace('        LD      DE,(CRMAGPTR)\n        CALL    CRLPUB','        LD      DE,(CRMINIT)\n        CALL    CRLPUB')
    source=source.replace('        LD      DE,(CRSLOT)\n        CALL    CRLPUB','        LD      DE,(CRMSHUT)\n        CALL    CRLPUB')
    source=source.replace('CRMRELOCS:     DW', 'CRMINIT:       DW      0\nCRMSHUT:       DW      0\nCRMRELOCS:     DW')
    # Keep the checksum outside the ten contiguous normalized header words.
    source=source.replace('CRFILE:        DB      0', 'CRMCHECK:      DW      0\nCRFILE:        DB      0')
    pos=source.index('\n        CALL    CRRESET',source.index('CRRELOC:'))
    gate='''
        LD      A,(CRFILE)
        OR      A
        JR      Z,CRSUMOK
        LD      HL,(CRBASE)
        LD      BC,(CRMSIZE)
        LD      DE,0
CRSUMLP:
        LD      A,(HL)
        ADD     A,E
        LD      E,A
        JR      NC,CRSUMNC
        INC     D
CRSUMNC:
        INC     HL
        DEC     BC
        LD      A,B
        OR      C
        JR      NZ,CRSUMLP
        LD      HL,(CRMCHECK)
        OR      A
        SBC     HL,DE
        JP      NZ,CRBAD
CRSUMOK:
'''
    return source[:pos]+gate+source[pos:]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.baseline.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'tools'))
    from build_ccp import assemble
    from build_z80pack_rom_boot import z80pack_reloader_source,normalized
    from build_z80pack_image import symbols
    from system_layout import LAYOUT as L
    from test_bios import Z80
    original=normalized(z80pack_reloader_source((root/'src/platform/trs80m4/ccprelod.mac').read_text()))
    source=compact(original);(out/'compact.mac').write_text(source)
    image=assemble(Path.home()/'bin/z80asm',source,out/'compact.bin',out/'compact.lst',L['RELOADER'])
    sy=symbols(out/'compact.lst')
    # Deterministic in-memory stream adapter. CRLOAD itself is real Z80 code.
    adapter=''' ASEG
 ORG 06000H
 JP NEXT
 JP RESET
NEXT:
 EX DE,HL
 LD HL,(PTR)
 LD BC,512
 LDIR
 LD (PTR),HL
 EX DE,HL
 XOR A
 RET
RESET:
 LD HL,02000H
 LD (PTR),HL
 XOR A
 RET
PTR: DW 02000H
 END
'''
    stub=assemble(Path.home()/'bin/z80asm',adapter,out/'stream.bin',out/'stream.lst',0x6000)
    passed=[]
    for name in ('HELLO','RCP'):
        raw=(root/f'build/cpx/{name}.CPX').read_bytes();size=int.from_bytes(raw[12:14],'little');header=int.from_bytes(raw[26:28],'little')
        for mutation in (None,header,header+size//2,header+size-1):
            data=bytearray(raw)
            if mutation is not None:data[mutation]^=1
            c=Z80(b'');c.mem[0x100:0x100+len(image)]=image;c.mem[0x2000:0x2000+len(data)]=data;c.mem[0x6000:0x6000+len(stub)]=stub
            c.mem[L['FILE']+3:L['FILE']+6]=bytes((0xc3,0,0x60));c.mem[L['FILE']+6:L['FILE']+9]=bytes((0xc3,3,0x60))
            c.mem[sy['CRFILE']]=1;c.setword(sy['CRBOUND'],L['TPA']);c.setword(sy['CRMAGPTR'],sy['CRCPXMAG']);c.sp=0x1000
            c.run(sy['CRLOAD'],limit=500000)
            assert (c.a==0)==(mutation is None),(name,mutation,c.a)
            if mutation is None:
                base=c.word(sy['CRBASE']);linked=int.from_bytes(raw[10:12],'little');expected=bytearray(raw[header:header+size])
                for i in range(int.from_bytes(raw[22:24],'little')):
                    off=int.from_bytes(raw[48+2*i:50+2*i],'little');value=int.from_bytes(expected[off:off+2],'little');expected[off:off+2]=((value+base-linked)&65535).to_bytes(2,'little')
                # Runtime descriptor publication overwrites entry/lifecycle words.
                for at in (16,18,20):
                    off=int.from_bytes(raw[at:at+2],'little');value=0 if off==65535 else base+off
                    dest=2+(at-16);expected[dest:dest+2]=value.to_bytes(2,'little')
                assert c.mem[base:base+size]==expected
            passed.append({'module':name,'payload_mutation':mutation,'accepted':c.a==0})
    result={'baseline_bytes':len((root/'build/z80pack/reloader.bin').read_bytes()),'compact_checksum_bytes':len(image),'existing_capacity':L['RELOADER_CAPACITY'],'fits_existing_capacity':len(image)<=L['RELOADER_CAPACITY'],'cases':passed,'scope':'checksum-only CRLOAD fixture; no binding, full-carrier integrity, or stream-consistency solution'}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
