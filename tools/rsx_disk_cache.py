"""Build the relocatable scratch-only RSX disk-cache worker."""
import struct
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_runtime_overlays import source

def build_worker(assembler, output, constants=""):
    output.mkdir(parents=True,exist_ok=True)
    images=[]
    for base,stem in ((0x1000,'r3cache'),(0x1101,'r3cache-alt')):
        images.append(assemble(assembler,constants+source('r3cache.mac','CBBASE',base),
            output/(stem+'.bin'),output/(stem+'.lst'),base))
    payload=images[0]
    if len(payload)<=33 or len(payload)>1536:
        raise ValueError(f'cache worker exceeds staged bounds: {len(payload)}')
    if any(payload[i]!=0xC3 for i in range(0,33,3)) or payload[33]!=0xF5:
        raise ValueError('cache dispatcher vector ABI changed')
    offsets=relocation_offsets(payload,images[1],0x101)
    if len(offsets)>240:raise ValueError('cache relocation header overflow')
    header=bytearray(512);header[:4]=b'R3DC';header[4]=len(offsets)
    struct.pack_into('<H',header,6,len(payload))
    for i,offset in enumerate(offsets):struct.pack_into('<H',header,32+i*2,offset)
    text=(Path(__file__).resolve().parents[1]/'src/system/r3entry.mac').read_text()
    reader=text[text.index('RI_ENTRY:'):text.index('RI_END:')]
    io=assemble(assembler,constants+'        INCLUDE layout.inc\n        INCLUDE profile.inc\n        ASEG\n        ORG 0\n'+reader+'        END\n',output/'rsxio.bin',output/'rsxio.lst',0)
    if len(io)>512:raise ValueError('overlay reader exceeds staged slot')
    image=bytes(header)+payload.ljust(1536,b'\0')+io.ljust(512,b'\0')
    (output/'R3CACHE.RSX').write_bytes(image)
    return image,len(payload),len(offsets)
