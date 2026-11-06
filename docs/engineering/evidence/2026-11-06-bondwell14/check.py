"""Check BW14 provenance, bounded decoding, physical conversion and native FDB."""
from pathlib import Path
from argparse import ArgumentParser
from dataclasses import replace
import json
import sys
import xml.etree.ElementTree as ET
from hashlib import sha1
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from media import decode,logical,physical,repack,read_files,digest,RESERVED,END
from fdf_v1 import parse,serialize
from fdfdecomp import decompile
from fdf_format import select_fdf
from convert_fdf_image import raw_to_dmk,dmk_to_raw
from test_fdb_roundtrip import machine,diskkey


def reject(fn,*args):
    try:fn(*args)
    except ValueError:return
    raise AssertionError('bad input accepted')


def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--images',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not __debug__:p.error('run without -O')
    specs=json.loads((HERE/'sources.json').read_text())
    archive=a.images/'bw14dsks.zip';assert digest(archive.read_bytes())==specs['archive_sha256']
    mame={r.attrib['sha1']:r.attrib['name'] for r in ET.parse(HERE/'mame-bw14.xml').iter('rom')}
    fmt=select_fdf(HERE/'CANDIDATE.FDF','BW14')
    # Only the filesystem visits heads in side-major order. DMK tracks remain
    # physical C/H order, with ordinary C,H,R,N fields and ascending IDs.
    surface=replace(fmt,flags=0xc0)
    dpb=bytes.fromhex('2400040f01ae007f00c00020000200');inspection={}
    for spec in specs['images']:
        image=(a.images/spec['filename']).read_bytes();assert digest(image)==spec['sha256'] and mame[sha1(image).hexdigest()]==spec['mame_filename']
        raw,head=decode(image);assert physical(logical(raw))==raw
        assert decode(repack(image,raw))[0]==raw
        dmk=raw_to_dmk(raw,surface);assert dmk_to_raw(dmk,surface)==raw
        files,used,count=read_files(raw)
        offsets=[i for i in range(len(raw)) if raw.startswith(dpb,i)]
        assert set(n.split(':')[0] for n in files)=={'0'}
        if spec['filename']=='SYSTEM1.IMG':assert offsets==[3263,68995]
        reject(decode,image[:-1]);reject(decode,bytes([image[0]^1])+image[1:])
        bad=bytearray(image);bad[-1]^=1;reject(decode,bad)
        bad=bytearray(image);bad[18]=1;bad[132]=0;bad[132]=(-sum(bad[:133]))&255;reject(decode,bad)
        for at in (0,END):
            changed=bytearray(logical(raw));changed[at]^=1;reject(repack,image,physical(changed))
        inspection[spec['filename']]=dict(original_sha256=digest(image),raw_sha256=digest(raw),original_files={n:digest(v) for n,v in files.items()},used_blocks=len(used),free_blocks=175-len(used),directory_extents=count,embedded_dpb_canonical_offsets=offsets,dmk_roundtrip=True)
    work=ROOT/'build/bw14-native';work.mkdir(parents=True,exist_ok=True)
    m=machine(work)
    key=lambda n:diskkey(1,n)
    for catalogue in (HERE/'qualification-catalogue.FDF',ROOT/'metadata/supplemental/SUPPDISK.FDF'):
        payload=serialize(parse(catalogue.read_text()))
        console=m.run('IN.FDF OUT.FDB',{key('IN.FDF'):decompile(payload).encode()});assert m.files.get(key('OUT.FDB'))==payload,console
        console=m.run('IN.FDB OUT.FDF',{key('IN.FDB'):payload});assert serialize(parse(m.files[key('OUT.FDF')].split(b'\x1a')[0].decode()))==payload,console
    a.output.write_text(json.dumps(dict(status='pass',images=inspection,native_compile_export='pass',negative_cases='header, CRC, truncation, geometry, reserved bytes, unused tail'),indent=2)+'\n')
    print('PASS nine originals: provenance, decoding, DMK roundtrip, rejection, native FDB compile/export')
if __name__=='__main__':main()
