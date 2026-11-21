"""Build the private transient PDS worker; no resident allocation."""
from pathlib import Path
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]


def build(assembler=None):
    assembler = assembler or Path.home()/'bin/z80asm'
    out = ROOT/'build/pds'
    out.mkdir(parents=True, exist_ok=True)
    import json
    from build_cpx_module import relocation_offsets
    from build_z80pack_image import symbols
    runtime=(ROOT/'src/system/mcl-worker.inc').read_text()
    images=[]
    for origin,stem in ((0x3000,'mcl-runtime'),(0x3101,'mcl-runtime-alt')):
        source='        INCLUDE layout.inc\n        ASEG\n        ORG 0'+format(origin,'04X')+'H\n'+runtime+'\n        END\n'
        images.append(assemble(assembler,source,out/(stem+'.bin'),out/(stem+'.lst'),origin))
    # Only trailing write-before-read cache fields are omitted from the carrier.
    if len(images[0])<=19 or any(images[0][-19:]):
        raise ValueError('MCL runtime cache is no longer trailing zero workspace')
    offsets=relocation_offsets(images[0],images[1],0x101)
    if any(offset+2>len(images[0])-19 for offset in offsets):
        raise ValueError('MCL fixup reaches omitted cache workspace')
    check_source='        INCLUDE layout.inc\n        ASEG\n        ORG 03237H\n'+runtime+'\n        END\n'
    check=assemble(assembler,check_source,out/'mcl-runtime-check.bin',out/'mcl-runtime-check.lst',0x3237)
    trial=bytearray(images[0])
    for offset in offsets:
        value=int.from_bytes(trial[offset:offset+2],'little')
        trial[offset:offset+2]=((value+0x237)&65535).to_bytes(2,'little')
    if trial!=check:raise ValueError('MCL private fixups fail independent carry check')
    if len(offsets)>255:raise ValueError('MCL private fixup count overflow')
    error=symbols(out/'mcl-runtime.lst')['MC_PDSMSG']-0x3000
    text='MC_SIZE EQU '+str(len(images[0])-19)+'\nMC_ERROR EQU '+str(error)+'\n'+(ROOT/'src/system/pds-worker.mac').read_text()
    def db(data):
        return '\n'.join('        DB '+','.join(map(str,data[i:i+16])) for i in range(0,len(data),16))
    assemble(assembler,text.replace('; @mcl-runtime@',db(bytes(len(images[0])-19))),
             out/'worker-probe.bin',out/'worker-probe.lst',0x1700)
    origin=symbols(out/'worker-probe.lst')['MC_SOURCE']
    data=bytearray(images[0]);delta=origin-0x3000
    for offset in offsets:
        value=int.from_bytes(data[offset:offset+2],'little')
        data[offset:offset+2]=((value+delta)&65535).to_bytes(2,'little')
    binary=assemble(assembler,text.replace('; @mcl-runtime@',db(data[:-19])),
                    out/'worker.bin',out/'worker.lst',0x1700)
    (out/'mcl-runtime.json').write_text(json.dumps(dict(size=len(data),source=origin,fixups=offsets),indent=2)+'\n')
    (out/'mcl-fixups.inc').write_text('        DB '+str(len(offsets))+'\n'+
        ''.join('        DW '+str(offset)+'\n' for offset in offsets))
    # Model II is the tightest checked stage pair; raw media has 2045 bytes.
    if not 0 < len(binary) <= 1598:
        raise ValueError(f'PDS worker exceeds its transient slot: {len(binary)}')
    return binary


if __name__ == '__main__':
    print('PDS worker bytes:', len(build()))
