"""Qualify original Model II IMDs through the explicit cpmsim boot-slot adapter.

Each process owns four disposable images. Originals are never write targets.
"""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
import json
import re
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from inspect_images import decode, raw_image, read_extents, sequential_files, logical_data, PREFIX, digest
from adapt import canonical,historical,to_raw,to_imd
from random_records import build_verifier
from fdf_v1 import parse, serialize
from fdfdecomp import decompile
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from test_z80pack_sysgen_install import session


def diskdef(f):
    ids=sorted(f.sector_ids)
    return (f'diskdef {f.ident}\n seclen {f.secsize}\n tracks {f.cylinders*f.sides}\n'
            f' sectrk {f.psectors}\n blocksize {128<<f.bsh}\n maxdir {f.drm+1}\n'
            ' skewtab '+','.join(str(ids.index(i)) for i in f.sector_ids)+
            f'\n boottrk {f.off}\n os 2.2\nend\n')


def run_one(spec,args):
    started=time.monotonic()
    source=args.images/spec['filename'];original=source.read_bytes()
    assert digest(original)==spec['sha256']
    comment,tracks,errors=decode(original)
    if errors:
        return dict(status='rejected before guest I/O',problems=errors,original_sha256=digest(original))
    double=len(tracks)==154
    assert [(t['cylinder'],t['head']) for t in sorted(tracks,key=lambda t:(t['cylinder'],t['head']))]==[(c,h) for c in range(77) for h in range(2 if double else 1)]
    formats=parse(args.catalogue.read_text());byid={f.ident:f for f in formats}
    data_size=next(t['size'] for t in tracks if t['cylinder'] or t['head'])
    ident='PT2SS' if data_size==512 and not double else ('ATONDS' if double else 'ATONSS')
    fmt=byid[ident];scratch=byid['M2WORK']
    for t in tracks:
        boot=t['cylinder']==t['head']==0
        assert (t['mode'],t['size'],sorted(t['ids']))==((0,128,list(range(1,27))) if boot else (3,fmt.secsize,sorted(fmt.sector_ids)))
    host_format='pt2ss' if ident=='PT2SS' else ('m2ds' if double else 'm2ss')
    raw=raw_image(tracks);before=to_raw(original)
    assert historical(before)==raw
    original_extents,used,extents=read_extents(raw,fmt.dsm,fmt.drm+1,fmt.sector_ids,fmt.secsize)
    expected=sequential_files(original_extents)
    random_records=[(name,extent*128+offset//128,data[offset:offset+128])
                    for name,parts in original_extents.items() for extent,data in parts.items()
                    for offset in range(0,len(data),128) if extent*16384+offset>=len(expected[name])]
    assert all(name.startswith('0:') for name in expected)
    free=set(range(fmt.dsm+1))-used
    assert fmt.dsm in free and (len(free)+7)//8 <= fmt.drm+1-extents
    probe=b''.join(sha256(b'Model II guest probe'+i.to_bytes(4,'little')).digest() for i in range(len(free)*2048//32))
    work=args.output/source.stem;work.mkdir();disks=work/'disks';disks.mkdir()
    (work/'diskdefs').write_text(''.join(diskdef(f) for f in formats)+(HERE/'diskdefs').read_text())
    def tool(name,ident,image,*rest):
        result=subprocess.run([str(args.cpmtools/name),'-f',ident,str(image),*map(str,rest)],cwd=work,capture_output=True,text=True)
        assert result.returncode==0,(name,result.stdout,result.stderr)
        return result.stdout
    a,b,c,d=[disks/f'drive{x}.dsk' for x in 'abcd']
    shutil.copyfile(args.system,a);b.write_bytes(before)
    for path in (c,d):path.write_bytes(bytes([0xe5])*(scratch.cylinders*scratch.sides*scratch.psectors*scratch.secsize))
    (work/'probe.bin').write_bytes(probe)
    tool('cpmcp','M2WORK',c,work/'probe.bin','0:PROBE.BIN')
    (work/'DISK.FDB').write_bytes(serialize(formats));tool('cpmcp','M2WORK',c,work/'DISK.FDB','0:DISK.FDB')
    if random_records:
        for name,negative in [('RVERIFY.COM',False),('RVBAD.COM',True)]:
            path=work/name;build_verifier(random_records,path,negative)
            tool('cpmcp','M2WORK',c,path,'0:'+name)
    commands=[f'CONFIG /PHYSICAL=1 /TRACKS=77 /SIDES={fmt.sides} /STEP=6']
    for letter,physical in [('C',2),('D',3)]:
        commands += [f'CONFIG /PHYSICAL={physical} /TRACKS=80 /SIDES=2 /STEP=6',
                     f'CONFIG /LOGICAL={letter} /PHYSICAL={physical} /FORMAT="{scratch.description}"']
    commands += ['C:',f'A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="{fmt.description}"','A:',
                 'DIR B:','COPY B:*.* C:','COPY C:PROBE.BIN B:FILL.BIN','COPY B:FILL.BIN D:RETURN.BIN']
    if random_records:
        at=commands.index('COPY B:*.* C:')
        commands[at:at]=['C:RVERIFY','C:RVBAD']
        commands.append('C:RVERIFY')
    steps=[];current='A'
    for cmd in commands:
        if len(cmd)==2 and cmd[1]==':':current=cmd[0]
        steps.append((cmd.encode()+b'\r',current.encode()+b'0>_ ',120))
    trace=session(args.simulator,disks,steps+[(b'BYE /Y\r',b'System halted',20)],work/'console.bin')
    assert trace.count(b'Disk configuration changed')==6,trace.decode(errors='replace')
    if random_records:
        assert re.findall(rb'Random records (PASS|FAIL)',trace)==[b'PASS',b'FAIL',b'PASS']
    after=historical(b.read_bytes())
    assert b.read_bytes()[:16384]==before[:16384]
    assert len(after)==len(raw) and after[:PREFIX]==raw[:PREFIX]
    written_extents,allocated,_=read_extents(after,fmt.dsm,fmt.drm+1,fmt.sector_ids,fmt.secsize)
    found=sequential_files(written_extents)
    assert {n:p for n,p in written_extents.items() if n!='0:fill.bin'}==original_extents
    assert allocated==set(range(fmt.dsm+1))
    assert found==dict(expected,**{'0:fill.bin':probe})
    olddir,newdir=logical_data(raw,fmt.sector_ids,fmt.secsize),logical_data(after,fmt.sector_ids,fmt.secsize)
    for offset in range(0,(fmt.drm+1)*32,32):
        if olddir[offset]!=0xe5:assert newdir[offset:offset+32]==olddir[offset:offset+32]
    def extract(path,ident,name,want):
        dest=work/'extract.bin';dest.unlink(missing_ok=True)
        tool('cpmcp',ident,path,name,dest)
        assert dest.read_bytes()==want,(path,name)
    for name,data in expected.items():extract(c,'M2WORK',name,data)
    extract(d,'M2WORK','0:return.bin',probe)
    packed=to_imd(original,b.read_bytes());(work/'written.imd').write_bytes(packed)
    comment2,tracks2,errors2=decode(packed)
    assert not errors2 and comment2==comment
    assert [t['header'] for t in tracks2]==[t['header'] for t in tracks]
    restored=raw_image(tracks2);assert restored==after
    historical_path=work/'written.raw';historical_path.write_bytes(restored)
    for name,parts in written_extents.items():
        dest=work/'extract.bin';dest.unlink(missing_ok=True)
        tool('cpmcp',host_format,historical_path,name,dest)
        data=dest.read_bytes()
        assert len(data)==max(n*16384+len(v) for n,v in parts.items())
        for extent,payload in parts.items():
            assert data[extent*16384:extent*16384+len(payload)]==payload,(name,extent)
    # Bytes in unallocated holes have no defined file value; compare only
    # recorded extents. Sequential COPY and BDOS random reads are distinct.
    # Independent directory/allocation check on the original variable-length layout.
    check=subprocess.run([str(args.cpmtools/'fsck.cpm'),'-f',host_format,'-n',str(historical_path)],cwd=work,text=True,capture_output=True)
    assert check.returncode==0,(check.stdout,check.stderr)
    assert digest(source.read_bytes())==spec['sha256']
    result=dict(status='pass',format=fmt.ident,original_sha256=spec['sha256'],original_files={n:digest(v) for n,v in expected.items()},
                probe_bytes=len(probe),probe_sha256=digest(probe),highest_block_written_and_read=fmt.dsm,
                original_recorded_extents_preserved=True,
                random_records_beyond_sequential_eof=[dict(file=n,record=r,sha256=digest(v)) for n,r,v in random_records],
                random_read_negative_control='pass' if random_records else 'not needed',
                original_directory_entries_preserved=True,reserved_bytes_preserved=PREFIX,canonical_reserved_bytes_preserved=16384,
                original_image_unchanged=True,image_length_preserved=True,imd_headers_and_sector_order_preserved=True,
                written_imd_sha256=digest(packed),written_raw_sha256=digest(after),fsck=check.stdout,
                guest_commands=commands,seconds=round(time.monotonic()-started,3))
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(spec['filename'],'pass',result['seconds'],'seconds',flush=True)
    return result


def main():
    p=ArgumentParser(description=__doc__)
    for name in ('images','system','simulator','cpmtools','catalogue','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sources',type=Path,default=HERE/'sources.json')
    p.add_argument('--jobs',type=int,default=5);args=p.parse_args()
    for name in ('images','system','simulator','cpmtools','catalogue'):setattr(args,name,getattr(args,name).resolve(strict=True))
    args.output=args.output.resolve();args.output.mkdir(parents=True)
    specs=json.loads(args.sources.read_text())['images']
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(run_one,s,args) for s in specs]
        samples={s['filename']:f.result() for s,f in zip(specs,futures)}
    result=dict(scope='cpmsim RAM file interchange through canonical reserved-first-surface adapter',jobs=args.jobs,
                system_sha256=digest(args.system.read_bytes()),emulator_sha256=digest(args.simulator.read_bytes()),
                catalogue_sha256=digest(args.catalogue.read_bytes()),samples=samples)
    (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
