#!/usr/bin/env python3
"""Independently verify exact Utilities membership, allocation and record bytes."""
import argparse,hashlib,json
from pathlib import Path
from build_utilities_disk import COMPONENTS
from convert_fdf_image import dmk_to_raw,raw_to_dmk
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def inspect(raw,fmt,files):
    mapping=fmt.raw_record_map()
    def record(n):
        track,slot=divmod(n,fmt.spt);at=(track*fmt.spt+mapping[slot])*128
        return raw[at:at+128]
    def data(n):return record(fmt.reserved_records+n)
    directory=b''.join(data(n) for n in range((fmt.drm+1)*32//128))
    entries={};used=set(range(fmt.directory_blocks))
    for at in range(0,len(directory),32):
        e=directory[at:at+32]
        if e[0]==0xe5:continue
        assert e[0]==0,('unexpected user/label entry',e[0])
        assert all(x<128 for x in e[1:12]),'unexpected file attributes'
        name=e[1:9].decode().rstrip()+'.'+e[9:12].decode().rstrip()
        assert name in files,('unexpected file',name)
        extent=(e[12]&31)+(e[14]&63)*32
        logical_extent=extent & ~fmt.exm
        records=(extent&fmt.exm)*128+e[15]
        assert e[15]<=128
        slots=[int.from_bytes(e[i:i+2],'little') for i in range(16,32,2)] if fmt.dsm>255 else list(e[16:32])
        count=(records*128+fmt.block_bytes-1)//fmt.block_bytes
        blocks=slots[:count]
        assert len(blocks)==count and not any(slots[count:])
        for b in blocks:
            assert fmt.directory_blocks<=b<=fmt.dsm and b not in used,('cross-linked/out-of-range allocation',name,b)
            used.add(b)
        payload=b''.join(data(b*(1<<fmt.bsh)+n) for b in blocks for n in range(1<<fmt.bsh))[:records*128]
        parts=entries.setdefault(name,{})
        assert logical_extent not in parts
        parts[logical_extent]=payload
    assert set(entries)==set(files),(set(entries),set(files))
    for name,parts in entries.items():
        assert sorted(parts)==list(range(0,len(parts)*(fmt.exm+1),fmt.exm+1))
        actual=b''.join(parts[k] for k in sorted(parts));expected=files[name]
        assert len(actual)==(len(expected)+127)//128*128
        assert actual[:len(expected)]==expected,name
        assert set(actual[len(expected):]) <= {0,0x1a},('unexpected record padding',name)
    return {'files':len(entries),'user':0,'allocated_blocks':len(used),'free_blocks':fmt.dsm+1-len(used),'exact_membership':'PASS','independent_record_readback':'PASS','allocation':'PASS'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--images',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    files={n:(a.artifacts/path).read_bytes() for n,path in COMPONENTS.items()};result={'status':'PASS','platforms':{}}
    for native,target in ((False,'z80pack'),(True,'trs80gp')):
        fmt=select_fdf(ROOT/'third_party/montezuma'/('DISK-INT.FDF' if native else 'DISK.FDF'),'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
        path=next(a.images.glob('*'+target+'*.dmk' if native else '*'+target+'*.dsk'));image=path.read_bytes();raw=dmk_to_raw(image,fmt) if native else image
        if native:assert raw_to_dmk(raw,fmt)==image
        r=inspect(raw,fmt,files);r.update(image=path.name,image_sha256=sha(image),raw_bytes=len(raw),files_sha256={n:sha(b) for n,b in files.items()});result['platforms'][target]=r
    a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS exact Utilities inventory, user placement, independent file bytes, allocations and native conversion')


if __name__=='__main__':main()
