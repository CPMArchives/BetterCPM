#!/usr/bin/env python3
"""Execute the packaged PATCH on disposable BetterCP/M media; export all results."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
    shutil.copytree(a.image_dir/'disks',w/'disks')
    shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
    volumes={letter:(a.utilities/name).read_bytes() for letter,name in (
        ('b','BetterCPM-Utilities-z80pack-332K.dsk'),('c','BetterCPM-NOAH-z80pack-332K.dsk'))}
    for letter,data in volumes.items():(w/f'disks/drive{letter}.dsk').write_bytes(data)
    companion=json.loads((a.utilities/'BetterCPM-NOAH-z80pack-332K.dsk.json').read_text())
    binary_digest=next(x['sha256'] for x in companion['included'] if x['name']=='PATCH.COM')
    assert binary_digest==sha((ROOT/'build/utilities/PATCH.COM').read_bytes())
    disk=w/'disks/drived.dsk'
    disk.write_bytes(bytes([0xe5])*len(volumes['b']))
    subprocess.run(['mkfs.cpm','-f','bettercpm-default',str(disk)],cwd=w,check=True,capture_output=True)
    def cpm(*args):
        return subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=w,check=True,capture_output=True)
    raw=bytes(range(256))*257
    short=bytes(range(128))
    manydata=bytes(range(256))*16
    changes=[(0xffff,bytes([255,0,1]),bytes([0x55,0x66])),(len(raw)-1,bytes([255]),bytes([0xaa]))]
    bigpatch='INPUT D0:BIG.DAT\r\nOUTPUT D0:BIG.NEW\r\n'+''.join(f'{o:X}: '+e.hex(' ')+' -> '+r.hex(' ')+'\r\n' for o,e,r in changes)
    expected=bytearray(raw)
    for o,e,r in changes:assert raw[o:o+len(e)]==e;expected[o:o+len(r)]=r
    manypatch='INPUT D0:MANY.DAT\r\nOUTPUT D0:MANY.NEW\r\n'+''.join(f'{o:X}: {manydata[o]:02X} -> {manydata[o]^255:02X} ; entry\r\n' for o in reversed(range(4000)))
    assert len(manypatch)>65536
    files={'BIG.DAT':raw,'BIG.PAT':bigpatch.encode()+b'\x1a','IN.DAT':short,
        'FIX.PAT':b'INPUT D0:IN.DAT\r\nOUTPUT D0:OUT.DAT\r\n00: 00 01 02 -> FF FE\r\n02: 02 -> FD\r\n\x1a',
        'OUT.DAT':b'old output'+bytes(118),'MANY.DAT':manydata,'MANY.PAT':manypatch.encode()+b'\x1a'}
    for name,data in files.items():
        (w/name).write_bytes(data);cpm(w/name,'0:'+name)
    commands=[(b'C0:PATCH /HELP /VER BAD\r',b'A0>_ ',20),
        (b'C0:PATCH D0:FIX.PAT\r',b'Overwrite? (y/N/r/?) ',20)]
    for _ in range(2):
        commands.extend([(b'?',b'Y Yes, N No (abort), R Rename, ? Help',10),
                         (b'',b'D0:OUT.DAT exists.',10),(b'',b'Overwrite? (y/N/r/?) ',10)])
    commands.extend([(b'Y',b'full verification passed.',30),(b'',b'A0>_ ',10),
        (b'C0:PATCH D0:BIG.PAT\r',b'full verification passed.',60),(b'',b'A0>_ ',10),
        (b'C0:PATCH D0:MANY.PAT\r',b'full verification passed.',60),(b'',b'A0>_ ',10)])
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',commands,w/'transcript.txt').decode('ascii',errors='replace')
    exports={}
    for name,original in files.items():
        dest=w/('READ-'+name);cpm('0:'+name,dest);data=dest.read_bytes()
        if name!='OUT.DAT':assert data[:len(original)]==original,(name,'source changed')
        exports[name]=sha(data)
    for name,wanted in (('OUT.DAT',bytes([255,254,253])+short[3:]),('BIG.NEW',expected),
                        ('MANY.NEW',bytes(b^255 if i<4000 else b for i,b in enumerate(manydata)))):
        dest=w/('RESULT-'+name);cpm('0:'+name,dest);actual=dest.read_bytes()
        assert actual==wanted,(name,len(actual),len(wanted))
        exports[name]=sha(actual)
    for letter,before in volumes.items():assert (w/f'disks/drive{letter}.dsk').read_bytes()==before
    record={'status':'PASS','scope':'Packaged PATCH under BetterCP/M: repeated help, staged replacement, 65792-byte input, unsorted 4000-instruction patch larger than 64 KiB (bounded memory), exact complete host byte comparison, unchanged sources and B/C disks',
        'binary_sha256':binary_digest,
        'volumes':{letter:sha(data) for letter,data in volumes.items()},'exported_sha256':exports,'large_patch_bytes':len(manypatch)}
    (w/'evidence.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Packaged PATCH BetterCP/M large-file, large-patch, help and replacement campaign: PASS')

if __name__=='__main__':main()
