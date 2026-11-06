"""Bounded CopyQM adapter and independent reader for the observed BW14 set.

CopyQM layout cross-checked with MAME cqm_dsk.cpp and LibDsk drvqm.c.
CopyQM's historical CRC uses only six bits of the reflected table index.
"""
from hashlib import sha256

TRACK=18*256
SIZE=80*TRACK
RESERVED=2*TRACK
END=RESERVED+175*2048


def digest(data):return sha256(data).hexdigest()


def crc(data):
    table=[]
    for value in range(64):
        for _ in range(8):value=(value>>1)^(0xedb88320 if value&1 else 0)
        table.append(value)
    result=0
    for byte in data:result=table[(byte^result)&63]^(result>>8)
    return result


def decode(image):
    if len(image)<133 or image[:3]!=b'CQ\x14' or sum(image[:133])%256:
        raise ValueError('invalid CopyQM header/checksum')
    word=lambda n:int.from_bytes(image[n:n+2],'little')
    if (word(3),word(16),word(18),image[89],image[90],image[91],image[113])!=(256,18,2,0,40,40,255):
        raise ValueError('not the observed BW14 geometry')
    pos=133+word(111);start=pos;raw=bytearray()
    if pos>len(image):raise ValueError('truncated CopyQM comment')
    while pos<len(image):
        if pos+2>len(image):raise ValueError('truncated RLE length')
        n=int.from_bytes(image[pos:pos+2],'little',signed=True);pos+=2
        count=1 if n<0 else n
        if n==0 or pos+count>len(image) or len(raw)+abs(n)>SIZE:
            raise ValueError('invalid CopyQM RLE bounds')
        raw.extend(image[pos:pos+count]*(-n) if n<0 else image[pos:pos+count]);pos+=count
    if len(raw)!=SIZE or crc(raw)!=int.from_bytes(image[92:96],'little'):
        raise ValueError('CopyQM payload size/CRC mismatch')
    return bytes(raw),image[:start]


def logical(raw):
    if len(raw)!=SIZE:raise ValueError('wrong raw size')
    return b''.join(raw[(c*2+h)*TRACK:(c*2+h+1)*TRACK] for h in range(2) for c in range(40))


def physical(data):
    if len(data)!=SIZE:raise ValueError('wrong logical size')
    return b''.join(data[(h*40+c)*TRACK:(h*40+c+1)*TRACK] for c in range(40) for h in range(2))


def repack(original,raw):
    before,header=decode(original)
    old,new=logical(before),logical(raw)
    if old[:RESERVED]!=new[:RESERVED] or old[END:]!=new[END:]:
        raise ValueError('reserved tracks or unused tail changed')
    head=bytearray(header);head[92:96]=crc(raw).to_bytes(4,'little')
    head[132]=0;head[132]=(-sum(head[:133]))&255
    result=bytes(head)+b''.join(TRACK.to_bytes(2,'little')+raw[i:i+TRACK] for i in range(0,SIZE,TRACK))
    if decode(result)[0]!=raw:raise ValueError('CopyQM round-trip failure')
    return result


def read_files(raw):
    data=logical(raw)[RESERVED:END]
    entries,used,count={},set(range(2)),0
    for at in range(0,128*32,32):
        entry=data[at:at+32]
        if entry[0]==229:continue
        if entry[0]>15:raise ValueError('unsupported CP/M directory metadata')
        name=str(entry[0])+':'+bytes(c&127 for c in entry[1:9]).decode('ascii').rstrip()
        ext=bytes(c&127 for c in entry[9:12]).decode('ascii').rstrip()
        name=(name+('.'+ext if ext else '')).lower()
        extent=(entry[12]&31)+(entry[14]<<5)
        if entry[15]>128:raise ValueError('invalid record count')
        blocks=[b for b in entry[16:] if b]
        if any(b>=175 or b in used for b in blocks) or len(set(blocks))!=len(blocks):
            raise ValueError('invalid/cross-linked allocation')
        used.update(blocks)
        size=(extent&1)*16384+entry[15]*128
        payload=b''.join(data[b*2048:(b+1)*2048] for b in blocks)[:size]
        if len(payload)!=size:raise ValueError('short allocation')
        parts=entries.setdefault(name,{})
        if extent//2 in parts:raise ValueError('duplicate extent')
        parts[extent//2]=payload;count+=1
    files={}
    for name,parts in entries.items():
        if sorted(parts)!=list(range(len(parts))) or any(len(parts[i])!=32768 for i in range(len(parts)-1)):
            raise ValueError('sparse file requires a separate random-record test')
        files[name]=b''.join(parts[i] for i in range(len(parts)))
    return files,used,count


def main():
    from argparse import ArgumentParser
    from pathlib import Path
    p=ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    read=sub.add_parser('to-raw');read.add_argument('source',type=Path);read.add_argument('output',type=Path)
    write=sub.add_parser('to-cqm');write.add_argument('source',type=Path);write.add_argument('raw',type=Path);write.add_argument('output',type=Path)
    a=p.parse_args();original=a.source.read_bytes()
    payload=decode(original)[0] if a.mode=='to-raw' else repack(original,a.raw.read_bytes())
    with a.output.open('xb') as out:out.write(payload)
if __name__=='__main__':main()
