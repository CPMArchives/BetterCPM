"""Typed relocation metadata for the boot-fixed private RSX execution window."""
import re
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from system_layout import LAYOUT, expand_layout

PREFIX = 96
HELPERS = (
    (5,'r3coord','r3coord.mac','RCBASE'),
    (6,'r3profile','r3prof.mac','PFBASE'),
    (7,'r3kctx','r3kctx.mac','KCBASE'),
    (8,'r3keep','r3keep.mac','KEBASE'),
    (9,'r3kpre','r3kpre.mac','KPBASE'),
    (10,'r3final','r3final.mac','RFBASE'),
    (11,'r3drop','r3drop.mac','RDBASE'),
    (13,'r3commit','r3comit.mac','RCBASE'),
    (14,'rsxresolver-plain','rsxresol.mac','RRBASE'),
)
PROLOGUE = '''
        PUSH DE
        PUSH IX
        LD DE,(RX_BASE)
        PUSH DE
        LD HL,-LY_RSX
        ADD HL,DE
        LD B,H
        LD C,L
        LD HL,PZ_MAP-LY_RSX
        ADD HL,DE
        PUSH HL
        POP IX
        EX DE,HL
        LD D,128
PZ_BYTE:
        LD A,(IX+0)
        INC IX
        LD E,8
PZ_BIT:
        RRCA
        JR NC,PZ_SKIP
        PUSH AF
        PUSH DE
        PUSH HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        POP HL
        LD (HL),E
        INC HL
        LD (HL),D
        DEC HL
        POP DE
        POP AF
PZ_SKIP:
        INC HL
        DEC E
        JR NZ,PZ_BIT
        LD A,D
        DEC A
        LD D,A
        JR NZ,PZ_BYTE
        POP HL
        LD (HL),0C3H
        INC HL
        PUSH HL
        LD DE,95
        ADD HL,DE
        EX DE,HL
        POP HL
        LD (HL),E
        INC HL
        LD (HL),D
        EX DE,HL
        POP IX
        POP DE
        JP (HL)
        REPT LY_RSX+96-$
        DB 0
        ENDM
'''


def shifted(text, origin_symbol, base):
    text = re.sub(r'^(LY_RSX[ \t]+EQU[ \t]+)0[0-9A-F]+H',
                  lambda m: m[1]+f'0{base:04X}H', text, flags=re.M)
    return re.sub(r'^'+re.escape(origin_symbol)+r'[ \t]+EQU[^\n]*',
                  f'{origin_symbol} EQU 0{base:04X}H', text, flags=re.M)


def bitmap(offsets):
    bits = bytearray(128)
    for offset in offsets:
        if not 0 <= offset < 1011:
            raise ValueError('private relocation touches protected manager frame')
        bits[offset//8] |= 1 << (offset%8)
    return bytes(bits)


def relocation_map(assembler, text, symbol, image, output, stem):
    base = LAYOUT['RSX']
    alternate = assemble(assembler, shifted(text, symbol, base+0x101),
                         output/(stem+'-rebase.bin'), output/(stem+'-rebase.lst'), base+0x101)
    offsets=relocation_offsets(image, alternate, 0x101)
    check=assemble(assembler,shifted(text,symbol,base+0x237),
                   output/(stem+'-rebase-check.bin'),output/(stem+'-rebase-check.lst'),base+0x237)
    trial=bytearray(image)
    for n in offsets:
        trial[n:n+2]=((int.from_bytes(trial[n:n+2],'little')+0x237)&65535).to_bytes(2,'little')
    if trial!=check:
        raise ValueError('private helper relocation fails independent carry check')
    return bitmap(offsets)


def boot_image(assembler, text, symbol, output, stem):
    """Raw entry/resolver self-rebases once, then becomes a direct entry JP."""
    base = LAYOUT['RSX']
    text = expand_layout(text)
    text = re.sub(r'(\bORG[ \t]+[^\n]+\n)', lambda m:m[0]+PROLOGUE, text, count=1)
    text = re.sub(r'^[ \t]*END[ \t]*$', 'PZ_MAP:\n        END', text, flags=re.M)
    first = assemble(assembler, text, output/(stem+'-pre.bin'), output/(stem+'-pre.lst'), base)
    alternate = assemble(assembler, shifted(text, symbol, base+0x101),
                         output/(stem+'-alt.bin'), output/(stem+'-alt.lst'), base+0x101)
    offsets = relocation_offsets(first[PREFIX:], alternate[PREFIX:], 0x101)
    bits = bitmap([n+PREFIX for n in offsets])
    body = '\n'.join('        DB '+','.join(map(str,bits[i:i+16])) for i in range(0,128,16))
    text = text.replace('PZ_MAP:\n', 'PZ_MAP:\n'+body+'\n')
    (output/(stem+'.mac')).write_text(text)
    data = assemble(assembler,text,output/(stem+'.bin'),output/(stem+'.lst'),base)
    if len(data)>1000:
        raise ValueError(f'{stem}: boot rebasing overlaps private frame/binding: {len(data)}')
    return data


def helper_tables(assembler, output, constants, images):
    """Maps are authenticated with the existing private scratch-worker binding."""
    import binascii
    from build_rsx_runtime_overlays import source
    from rsx_container import NAMES
    maps={}
    for slot,stem,filename,symbol in HELPERS:
        image=(output/(stem+'.bin')).read_bytes()
        maps[slot]=relocation_map(assembler,constants+source(filename,symbol,LAYOUT['RSX']),
                                  symbol,image,output,stem)
    lines=['RB_DIR:']
    for slot,name in enumerate(NAMES):
        pointer=f'RB_MAP{slot}-CBBASE' if slot in maps else '0'
        crc=binascii.crc_hqx(images[name+'.RSX'],0xffff)
        lines.append(f'        DW {pointer},{crc}')
    for slot,bits in maps.items():
        lines.append(f'RB_MAP{slot}:')
        lines += ['        DB '+','.join(map(str,bits[i:i+16])) for i in range(0,128,16)]
    return '\n'.join(lines)
