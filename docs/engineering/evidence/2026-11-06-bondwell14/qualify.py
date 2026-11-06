"""Parallel BW14 cpmsim RAM interchange on private, canonical raw copies."""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from media import decode,logical,repack,read_files,digest,RESERVED,END
from fdf_v1 import parse,serialize
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from test_z80pack_sysgen_install import session


def run_one(spec,args):
    started=time.monotonic()
    source=args.images/spec['filename'];original=source.read_bytes()
    assert digest(original)==spec['sha256']
    before,header=decode(original)
    expected,used,extents=read_files(before)
    formats=parse(args.catalogue.read_text());fmt,scratch=formats
    assert fmt.ident=='BW14' and scratch.ident=='M2WORK'
    free=set(range(fmt.dsm+1))-used
    assert 174 in free and (len(free)+15)//16<=128-extents
    probe=b''.join(sha256(b'BW14 guest probe'+i.to_bytes(4,'little')).digest() for i in range(len(free)*2048//32))
    work=args.output/source.stem;work.mkdir();disks=work/'disks';disks.mkdir()
    (work/'diskdefs').write_text((HERE/'diskdefs').read_text()+disk_definition(select_fdf(ROOT/'metadata/release-formats.fdf','MMF017'))+'''\ndiskdef M2WORK
 seclen 1024
 tracks 160
 sectrk 8
 blocksize 2048
 maxdir 192
 skew 0
 boottrk 0
 os 2.2
end
''')
    def tool(name,ident,image,*rest):
        result=subprocess.run([str(args.cpmtools/name),'-f',ident,*(['-n'] if name=='fsck.cpm' else []),str(image),*map(str,rest)],cwd=work,capture_output=True,text=True)
        assert result.returncode==0,(name,result.stdout,result.stderr)
        return result.stdout
    def extract(path,ident,name,want):
        dest=work/'extract.bin';dest.unlink(missing_ok=True)
        tool('cpmcp',ident,path,name,dest)
        assert dest.read_bytes()==want,(path,name)
    logical_path=work/'original.logical';logical_path.write_bytes(logical(before))
    for name,data in expected.items():extract(logical_path,'bw14',name,data)
    libdsk_source=work/'libdsk-source.cqm';libdsk_source.write_bytes(original)
    independent=work/'libdsk-original.raw'
    subprocess.run([str(args.dsktrans),'-itype','qm','-otype','raw',str(libdsk_source),str(independent)],check=True,capture_output=True)
    assert independent.read_bytes()==before
    a,b,c,d=[disks/f'drive{x}.dsk' for x in 'abcd']
    shutil.copyfile(args.system,a);b.write_bytes(before)
    tool('cpmcp','bettercpm-default',a,args.mapper,'0:FDF.RSX')
    for path in (c,d):path.write_bytes(bytes([0xe5])*(160*8*1024))
    (work/'probe.bin').write_bytes(probe)
    tool('cpmcp','M2WORK',c,work/'probe.bin','0:PROBE.BIN')
    (work/'DISK.FDB').write_bytes(serialize(formats));tool('cpmcp','M2WORK',c,work/'DISK.FDB','0:DISK.FDB')
    commands=['RSX LOAD FDF','CONFIG /PHYSICAL=1 /TRACKS=40 /SIDES=2 /STEP=6']
    for letter,physical in [('C',2),('D',3)]:
        commands += [f'CONFIG /PHYSICAL={physical} /TRACKS=80 /SIDES=2 /STEP=6',
                     f'CONFIG /LOGICAL={letter} /PHYSICAL={physical} /FORMAT="{scratch.description}"']
    commands += ['C:',f'A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="{fmt.description}"','A:',
                 'DIR B:','COPY B:*.* C:','COPY C:PROBE.BIN B:FILL.BIN','COPY B:FILL.BIN D:RETURN.BIN']
    steps=[];current='A'
    for cmd in commands:
        if len(cmd)==2 and cmd[1]==':':current=cmd[0]
        steps.append((cmd.encode()+b'\r',current.encode()+b'0>_ ',120))
    trace=session(args.simulator,disks,steps+[(b'BYE /Y\r',b'System halted',20)],work/'console.bin')
    assert trace.count(b'Disk configuration changed')==6,trace.decode(errors='replace')
    after=b.read_bytes();found,allocated,_=read_files(after)
    assert len(after)==len(before) and allocated==set(range(175))
    assert found==dict(expected,**{'0:fill.bin':probe})
    old,new=logical(before),logical(after)
    assert old[:RESERVED]==new[:RESERVED] and old[END:]==new[END:]
    for at in range(RESERVED,RESERVED+128*32,32):
        if old[at]!=0xe5:assert new[at:at+32]==old[at:at+32]
    for name,data in expected.items():extract(c,'M2WORK',name,data)
    extract(d,'M2WORK','0:return.bin',probe)
    packed=repack(original,after);written=work/'written.cqm';written.write_bytes(packed)
    restored,head=decode(packed);assert restored==after
    assert all(x==y for i,(x,y) in enumerate(zip(header,head)) if i not in [92,93,94,95,132])
    libdsk_source.write_bytes(packed)
    independent=work/'libdsk-written.raw'
    subprocess.run([str(args.dsktrans),'-itype','qm','-otype','raw',str(libdsk_source),str(independent)],check=True,capture_output=True)
    assert independent.read_bytes()==after
    logical_path=work/'written.logical';logical_path.write_bytes(logical(independent.read_bytes()))
    for name,data in found.items():extract(logical_path,'bw14',name,data)
    check=tool('fsck.cpm','bw14',logical_path)
    assert digest(source.read_bytes())==spec['sha256']
    result=dict(status='pass',format='BW14',original_sha256=spec['sha256'],original_files={n:digest(v) for n,v in expected.items()},
                probe_bytes=len(probe),probe_sha256=digest(probe),highest_block_written_and_read=174,
                original_directory_entries_preserved=True,reserved_logical_bytes_preserved=RESERVED,unused_tail_bytes_preserved=len(old)-END,
                original_image_unchanged=True,image_length_preserved=True,copyqm_header_and_comment_preserved_except_checksums=True,
                libdsk_original_and_written_raw_match=True,written_cqm_sha256=digest(packed),written_raw_sha256=digest(after),fsck=check,
                guest_commands=commands,seconds=round(time.monotonic()-started,3))
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(spec['filename'],'pass',result['seconds'],'seconds',flush=True)
    return result


def main():
    p=ArgumentParser(description=__doc__)
    for name in ('images','system','simulator','cpmtools','dsktrans','mapper','catalogue','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--jobs',type=int,default=9);args=p.parse_args()
    if not __debug__ or args.jobs<1:p.error('run without -O and with positive --jobs')
    for name in ('images','system','simulator','cpmtools','dsktrans','mapper','catalogue'):setattr(args,name,getattr(args,name).resolve(strict=True))
    args.output=args.output.resolve();args.output.mkdir(parents=True)
    specs=json.loads((HERE/'sources.json').read_text())['images']
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(run_one,s,args) for s in specs]
        samples={s['filename']:f.result() for s,f in zip(specs,futures)}
    result=dict(scope='cpmsim RAM file interchange on canonical C/H/ascending-ID raw media',jobs=args.jobs,
                system_sha256=digest(args.system.read_bytes()),emulator_sha256=digest(args.simulator.read_bytes()),
                catalogue_sha256=digest(args.catalogue.read_bytes()),mapper_sha256=digest(args.mapper.read_bytes()),samples=samples)
    (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
