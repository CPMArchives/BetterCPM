"""Prepare/run parallel BW14 Model 4 trials using private media and FDF.RSX.

Preparation and DMK round trips are host checks, not guest qualification.
"""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(HERE.parent/'2026-11-05-cpc')]
from media import decode,logical,repack,read_files,digest,RESERVED,END
from fdf_v1 import parse,serialize
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as build_boot_dmk
from convert_fdf_image import raw_to_dmk,dmk_to_raw
from trs80gp_launch import run as run_trs80gp,require_launch_services
# Load only the existing progress watcher; this module is named model4.py.
from qualify import watch_model4


def cpm(args,work,tool,fmt,image,*rest):
    r=subprocess.run([str(args.cpmtools/tool),'-f',fmt,*(['-n'] if tool=='fsck.cpm' else []),str(image),*map(str,rest)],cwd=work,capture_output=True,text=True)
    assert r.returncode==0,(tool,r.stdout,r.stderr)
    return r.stdout


def one(spec,args):
    source=args.images/spec['filename'];image=source.read_bytes();assert digest(image)==spec['sha256']
    raw,_=decode(image);expected,used,_=read_files(raw)
    fmt=select_fdf(HERE/'CANDIDATE.FDF','BW14')
    surface=replace(fmt,flags=0xc0) # physical C/H/R/N is ordinary; guest keeps SIDE_MAJOR.
    scratch=select_fdf(ROOT/'metadata/release-formats.fdf','MMI008')
    probe=b''.join(sha256(b'BW14 guest probe'+i.to_bytes(4,'little')).digest() for i in range((175-len(used))*2048//32))
    work=args.output/source.stem
    if args.prepare:
        work.mkdir()
        (work/'diskdefs').write_text(disk_definition(scratch)+(HERE/'diskdefs').read_text()+'''\ndiskdef boot
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
''')
        boot=work/'boot.raw';boot.write_bytes(extract_raw(args.system.read_bytes()))
        dest=work/'scratch.raw';dest.write_bytes(bytes([0xe5])*scratch.image_bytes)
        (work/'probe.bin').write_bytes(probe)
        (work/'DISK.FDB').write_bytes(serialize(parse((HERE/'CANDIDATE.FDF').read_text())))
        for local,name in [('probe.bin','PROBE.BIN'),('DISK.FDB','DISK.FDB')]:cpm(args,work,'cpmcp','bettercpm-default',dest,work/local,'0:'+name)
        cpm(args,work,'cpmcp','boot',boot,args.mapper,'0:FDF.RSX')
        # FDF's private mapper input uses HL, which preceding chaining RSXs
        # overwrite. Keep FDF first until that existing ABI limitation is fixed.
        commands=['RSX LOAD FDF','RSX LOAD M4SCRN','RSX LOAD ADM3A','CLS','B:',
                  'A:CONFIG /LOGICAL=C /PHYSICAL=2 /FORMAT="Bondwell 14 40T DS"','A:',
                  'DIR C:','COPY C:*.* B:','COPY B:PROBE.BIN C:FILL.BIN','COPY C:FILL.BIN B:RETURN.BIN','TYPE BWEND.TXT']
        (work/'startup').write_bytes(('\r\n'.join(commands)+'\r\n\x1a').encode());(work/'marker').write_bytes(b'BW14 batch ended\r\n\x1a')
        cpm(args,work,'cpmrm','boot',boot,'0:STARTUP.SUB')
        for local,name in [('startup','STARTUP.SUB'),('marker','BWEND.TXT')]:cpm(args,work,'cpmcp','boot',boot,work/local,'0:'+name)
        d0,d1,d2=[work/f'drive{i}.dmk' for i in range(3)]
        d0.write_bytes(build_boot_dmk(boot.read_bytes()));assert extract_raw(d0.read_bytes())==boot.read_bytes()
        d1.write_bytes(raw_to_dmk(dest.read_bytes(),scratch));assert dmk_to_raw(d1.read_bytes(),scratch)==dest.read_bytes()
        d2.write_bytes(raw_to_dmk(raw,surface));assert dmk_to_raw(d2.read_bytes(),surface)==raw
        result=dict(status='prepared, guest not run',original_sha256=digest(image),files=len(expected),probe_bytes=len(probe),guest_commands=commands,
                    system_sha256=digest(args.system.read_bytes()),mapper_sha256=digest(args.mapper.read_bytes()),
                    dmks_sha256={p.name:digest(p.read_bytes()) for p in (d0,d1,d2)},
                    physical_layout='synthetic ascending-ID DMK tracks; historical angular order is not recorded by CopyQM')
        (work/'prepared.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    prepared=json.loads((work/'prepared.json').read_text())
    assert prepared['original_sha256']==digest(image)
    disks=[work/f'drive{i}.dmk' for i in range(3)]
    assert all(digest(p.read_bytes())==prepared['dmks_sha256'][p.name] for p in disks),'prepare fresh media before another trial'
    print('Running',source.name,flush=True)
    with watch_model4(disks):
        run_trs80gp([args.simulator,'-m4','-batch','-turbo','-na','-d0',disks[0],'-d1',disks[1],'-d2',disks[2],'-itime','0','-iw','BW14 batch ended','-id','500','-it','-ix'],cwd=work,timeout=24*60*60)
    after=dmk_to_raw(disks[2].read_bytes(),surface);found,allocated,_=read_files(after)
    assert found==dict(expected,**{'0:fill.bin':probe}) and allocated==set(range(175))
    old,new=logical(raw),logical(after)
    assert old[:RESERVED]==new[:RESERVED] and old[END:]==new[END:]
    for at in range(RESERVED,RESERVED+4096,32):
        if old[at]!=0xe5:assert old[at:at+32]==new[at:at+32]
    dest=work/'scratch.raw';dest.write_bytes(dmk_to_raw(disks[1].read_bytes(),scratch))
    for name,want in dict(expected,**{'0:return.bin':probe}).items():
        out=work/'extract.bin';out.unlink(missing_ok=True);cpm(args,work,'cpmcp','bettercpm-default',dest,name,out);assert out.read_bytes()==want
    written=work/'written.logical';written.write_bytes(new);check=cpm(args,work,'fsck.cpm','bw14',written)
    packed=repack(image,after);(work/'written.cqm').write_bytes(packed)
    assert digest(source.read_bytes())==spec['sha256']
    result=dict(status='pass',original_sha256=spec['sha256'],original_files={n:digest(v) for n,v in expected.items()},probe_bytes=len(probe),probe_sha256=digest(probe),highest_block_written_and_read=174,written_raw_sha256=digest(after),written_cqm_sha256=digest(packed),reserved_bytes_preserved=RESERVED,unused_tail_preserved=True,original_directory_entries_preserved=True,fsck=check,preparation=prepared,emulator_sha256=digest(args.simulator.read_bytes()))
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(source.name,'pass',flush=True)
    return result


def main():
    p=ArgumentParser(description=__doc__)
    for name in ('images','output','cpmtools'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('system','mapper','simulator'):p.add_argument('--'+name,type=Path)
    p.add_argument('--prepare',action='store_true');p.add_argument('--jobs',type=int,default=9);args=p.parse_args()
    if not __debug__ or args.jobs<1:p.error('run without -O and with positive --jobs')
    if args.prepare and not(args.system and args.mapper):p.error('--prepare requires --system and --mapper')
    if not args.prepare and not args.simulator:p.error('execution requires --simulator')
    for name in ('images','output','cpmtools','system','mapper','simulator'):
        if getattr(args,name):setattr(args,name,getattr(args,name).resolve())
    if args.prepare:args.output.mkdir(parents=True)
    elif sys.platform=='darwin':require_launch_services()
    specs=json.loads((HERE/'sources.json').read_text())['images']
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(one,s,args) for s in specs]
        results={s['filename']:f.result() for s,f in zip(specs,futures)}
    (args.output/('prepared.json' if args.prepare else 'results.json')).write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
