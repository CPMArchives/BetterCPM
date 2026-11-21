"""Build a bounded self-unpacking CCP using unchanged ordinary carrier readers."""
import json
from pathlib import Path
from command_packing import pack, unpack

ROOT = Path(__file__).resolve().parents[1]


def build(assembler, image, payload_size, offsets, assemble, relocation_offsets):
    out = ROOT / 'build/ccp'
    table = bytearray()
    previous = 0
    for offset in offsets:
        delta = offset-previous
        if delta < 2:
            raise ValueError('overlapping internal CCP fixups')
        table.extend(bytes((delta,)) if delta<=255 else b'\0'+delta.to_bytes(2,'little'))
        previous = offset
    bundle = image[:payload_size] + table
    packed = pack(bundle)
    if unpack(packed,len(bundle)) != bundle:
        raise ValueError('private CCP packing round trip failed')
    inner_allocation = (len(image)+255)&~255
    if len(bundle)>inner_allocation:
        raise ValueError('decoded fixups exceed the inner CCP workspace')
    # A sizing assembly determines the destination immediately above the whole
    # packed executable. Decoder length is independent of these addresses.
    destination = 0x1800
    def db(data):
        return '\n'.join('        DB '+','.join(map(str, data[i:i+16])) for i in range(0,len(data),16))
    bodies = []
    for origin, stem in ((0xBB00,'packed'), (0xBC01,'packed-alt'), (0xBD37,'packed-check')):
        def source(destination):
            constants = ('        INCLUDE layout.inc\n'
                     f'PK_REAL EQU {origin+destination}\nPK_RUNTIME EQU {origin+3}\n'
                     f'PK_PAYLOAD EQU {payload_size}\nPK_DECODED EQU {len(bundle)}\n'
                     f'PK_RELOCS EQU {len(offsets)}\nPK_INNERALLOC EQU {inner_allocation}\n')
            return constants + (ROOT/'src/ccp/unpack-body.mac').read_text().replace(
                '; @packed-command-data@', db(packed))
        body = assemble(assembler,source(destination),out/(stem+'-body.bin'),out/(stem+'-body.lst'),origin+3)
        destination = (len(body)+3+255)&~255
        body = assemble(assembler,source(destination),out/(stem+'-body.bin'),out/(stem+'-body.lst'),origin+3)
        text = (f'PK_ORIGIN EQU {origin}\nPK_RUNTIME EQU {origin+3}\n'+
                (ROOT/'src/ccp/unpack.mac').read_text().replace('; @packed-bootstrap-body@',db(body)))
        bodies.append(assemble(assembler,text,out/(stem+'.bin'),out/(stem+'.lst'),origin))
    outer_offsets = relocation_offsets(bodies[0],[(bodies[1],0xBC01),(bodies[2],0xBD37)])
    # Only decoder operands vary: compressed canonical code/table never relocates.
    if any(x >= len(bodies[0])-len(packed) for x in outer_offsets):
        raise ValueError('outer relocation reaches packed data')
    prefix = len(bodies[0]) - len((out/'packed-body.bin').read_bytes())
    if prefix != 3 or len(bodies[0]) > destination:
        raise ValueError('CCP packed source overlaps decoded destination')
    allocation = destination+inner_allocation
    if 0xBD37+allocation>65536:
        raise ValueError('private CCP alternate assembly would wrap address space')
    (out/'packing.json').write_text(json.dumps(dict(inner_payload=payload_size,
        inner_image=len(image),inner_relocations=len(offsets),bundle=len(bundle),
        packed=len(packed),outer_payload=len(bodies[0]),outer_relocations=len(outer_offsets),
        output_offset=destination,inner_allocation=inner_allocation,
        allocation=allocation,prefix=prefix),indent=2)+'\n')
    return bodies[0], outer_offsets, allocation
