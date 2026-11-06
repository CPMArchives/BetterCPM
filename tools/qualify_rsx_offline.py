#!/usr/bin/env python3
"""Qualify explicit-source RSXs and XSUB on disposable released-media copies."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from build_trs80_boot import SYSTEM_FIRST_LOGICAL_INDEX, SYSTEM_SECTORS
from fdf_format import select_fdf
from convert_fdf_image import dmk_to_raw, raw_to_dmk
from build_z80pack_image import DEFAULT_FORMAT, disk_definition
from run_trs80_command import DEFAULT_EMULATOR
from test_z80pack_sysgen_install import session
from test_z80pack_submit_xsub import input_probe
from test_submit_xsub import marker
from trs80gp_launch import run
from system_layout import LAYOUT

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def audit_outputs(w, native):
    """Prove source removal and reject diagnostics, independently of prompts."""
    definition='offline-data' if native else 'bettercpm-default'
    positive=w/'audit-XSUB.COM'
    subprocess.run(['cpmcp','-T','raw','-f',definition,str(w/'utilities.raw'),'0:XSUB.COM',str(positive)],cwd=w,check=True,capture_output=True)
    expected=(ROOT/'build/utilities/XSUB.COM').read_bytes()
    assert positive.read_bytes()[:len(expected)]==expected
    for user,name in ((0,'HELLO.RSX'),(3,'STATEFUL.RSX'),(0,'BATCHIO.RSX')):
        destination=w/('absent-'+str(user)+'-'+name)
        result=subprocess.run(['cpmcp','-T','raw','-f',definition,str(w/'utilities.raw'),
            f'{user}:{name}',str(destination)],cwd=w,capture_output=True)
        # cpmtools may return zero when a source wildcard matches no file.
        assert not destination.exists(),('carrier still present',user,name,result.stderr)
    if native:
        text=b'\n'.join(bytes(c&127 for c in f.read_bytes()[:1920]) for f in sorted(w.glob('trs80-text*')))
    else:
        text=(w/'transcript.bin').read_bytes()
    assert b'CACHE ERROR CHAIN PASS' in text,'missing native error-probe pass marker'
    for error in (b'RSX module or profile error',b'STATEFUL LOOKUP FAILED',b'INPUT FAILED',b'CACHE ERROR CHAIN FAILED',b'Invalid usage.'):
        assert error not in text,error
    return {'carrier_removal':'PASS: B0 HELLO/BATCHIO and B3 STATEFUL absent',
            'unexpected_diagnostics':'none'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=('z80pack','trs80gp'),required=True)
    for n in ('system','utilities','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--companion',type=Path)
    p.add_argument('--work-disk',type=Path)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    tracked=[ROOT/p for p in ('build/system/R3PACK.RSX','build/system/R3CACHE.RSX','build/system/rsxloader.bin','build/system/fileloader.bin','build/utilities/RSX.COM','build/utilities/XSUB.COM')]
    artifacts={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in tracked}
    original=a.system.resolve().read_bytes();utilities=a.utilities.resolve().read_bytes()
    native=a.target=='trs80gp'
    if native and (not a.companion or not a.work_disk):p.error('Model 4 requires --companion and --work-disk for the bcpm A-D layout')
    raw=w/'system.raw';raw.write_bytes(extract_raw(original) if native else original)
    data_fmt=select_fdf(ROOT/'metadata/DISK.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    data=w/'utilities.raw';data.write_bytes(dmk_to_raw(utilities,data_fmt) if native else utilities)
    # Only the Function-177 raw selector changes in the reserved System area.
    entry=(ROOT/'build/system/rsxloader.bin').read_bytes()
    block=entry.ljust(1021,b'\0')+bytes((0xc3,LAYOUT['BDOS']&255,LAYOUT['BDOS']>>8))
    payload=bytearray(raw.read_bytes())
    if native:
        start=(SYSTEM_FIRST_LOGICAL_INDEX+SYSTEM_SECTORS)*512+2048
        payload[start:start+1024]=block
    else:
        fmt=select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT)
        mapping=fmt.raw_record_map()
        for i in range(8):
            track,within=divmod(76+i,fmt.spt)
            at=track*fmt.raw_track_bytes+mapping[within]*128
            payload[at:at+128]=block[i*128:(i+1)*128]
    # Matched stream reset preserves the sequential FCB's random-record bytes,
    # which carry the transient worker trampoline. Patch this resident component
    # as well as the raw selector; never qualify a mixed old/new System.
    stream=(ROOT/'build/system/fileloader.bin').read_bytes()
    resident_offset=LAYOUT['FILE']-LAYOUT['SYSTEM']
    if native:
        start=SYSTEM_FIRST_LOGICAL_INDEX*512+resident_offset
        old=bytes(payload[start:start+len(stream)])
        assert sum(a!=b for a,b in zip(old,stream))<=1,'unexpected resident stream baseline'
        payload[start:start+len(stream)]=stream
    else:
        old=bytearray()
        for i,value in enumerate(stream):
            logical=8*128+resident_offset+i
            record,byte=divmod(logical,128);track,within=divmod(record,fmt.spt)
            at=track*fmt.raw_track_bytes+mapping[within]*128+byte
            old.append(payload[at]);payload[at]=value
        assert sum(a!=b for a,b in zip(old,stream))<=1,'unexpected resident stream baseline'
    raw.write_bytes(payload)
    defs=('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n' if native else disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT)))
    (w/'diskdefs').write_text(defs)
    with (w/'diskdefs').open('a') as f:
        f.write('\ndiskdef offline-data\n libdsk:format pcw800\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 2\n boottrk 0\n os 2.2\nend\n')
    definition=lambda disk:'offline-data' if native and disk==data else 'bettercpm-default'
    def cmd(*args):
        return subprocess.run(list(map(str,args)),cwd=w,check=True,capture_output=True)
    def remove(disk,user,name):
        subprocess.run(['cpmrm','-T','raw','-f',definition(disk),str(disk),f'{user}:{name}'],cwd=w,capture_output=True)
    def put(disk,user,name,content):
        remove(disk,user,name)
        path=w/f'{user}-{name}';path.write_bytes(content)
        cmd('cpmcp','-T','raw','-f',definition(disk),disk,path,f'{user}:{name}')
    for name in ('DDT.COM','DUMP.COM','UNCR.COM'):
        remove(data,0,name)
    steps=['RSX LOAD B0:HELLO','RSX UNLOAD HELLO']*(1 if native else 6)+['RSX LOAD B0:HELLO','RSX LOAD B3:STATEFUL','STATTST I','STATTST M','CACHERR',
           'ERA B0:HELLO.RSX','ERA B3:STATEFUL.RSX','RSX UNLOAD HELLO','STATTST C',
           'RSX UNLOAD STATEFUL','SUBMIT UBATCH']
    batch=b'B:XSUB B0:\r\nA:INPUT\r\nBATCHFULL\r\nERA B:BATCHIO.RSX\r\nA:MARK RSXOFFLINE\r\nRSX UNLOAD BATCHIO\r\nRSX LIST\r\n\x1a'
    for n,path in [('R3PACK.RSX','build/system/R3PACK.RSX'),('R3CACHE.RSX','build/system/R3CACHE.RSX'),
                   ('RSX.COM','build/utilities/RSX.COM'),('STATTST.COM','build/utilities/STATTST.COM')]:
        put(raw,0,n,(ROOT/path).read_bytes())
    for n,path,user in [('XSUB.COM','build/utilities/XSUB.COM',0),('BATCHIO.RSX','build/rsx/BATCHIO.RSX',0),
                        ('HELLO.RSX','build/rsx/HELLO.RSX',0),('STATEFUL.RSX','build/rsx/STATEFUL.RSX',3)]:
        put(data,user,n,(ROOT/path).read_bytes())
    for n in ('HELLO.RSX','STATEFUL.RSX','BATCHIO.RSX'):remove(raw,0,n)
    from build_ccp import assemble
    probe=assemble(Path.home()/'bin/z80asm',(ROOT/'tools/rsx_cache_error_probe.mac').read_text(),
        w/'CACHERR.COM',w/'CACHERR.lst',0x100)
    put(raw,0,'CACHERR.COM',probe)
    put(raw,0,'UBATCH.SUB',batch);put(raw,0,'INPUT.COM',input_probe(w));put(raw,0,'MARK.COM',marker(w))
    if not native:
        disks=w/'disks';disks.mkdir();shutil.copy2(raw,disks/'drivea.dsk');shutil.copy2(data,disks/'driveb.dsk')
        commands=[]
        for s in steps:
            expected=b'CACHE ERROR CHAIN PASS' if s=='CACHERR' else b'STATEFUL CHECK PASS' if s=='STATTST C' else b'No RSXs loaded' if s=='SUBMIT UBATCH' else b'A0>_ '
            commands.append(((s+'\r').encode(),expected,15))
        text=session(a.simulator.resolve(),disks,commands,w/'transcript.bin')
        assert b'INPUT OK' in text and b'INPUT FAILED' not in text
        assert b'RSX module or profile error' not in text and b'STATEFUL LOOKUP FAILED' not in text
        shutil.copy2(disks/'drivea.dsk',raw);shutil.copy2(disks/'driveb.dsk',data)
    else:
        put(raw,0,'STARTUP.SUB',('\r\n'.join(steps)+'\r\n\x1a').encode())
        disk=w/'system.dmk';disk.write_bytes(make_dmk(raw.read_bytes()))
        other=w/'utilities.dmk';other.write_bytes(raw_to_dmk(data.read_bytes(),data_fmt))
        extra=[]
        for n,source in enumerate((a.companion,a.work_disk),2):
            copy=w/f'drive{n}.dmk';shutil.copy2(source.resolve(),copy);extra+=['-d'+str(n),str(copy)]
        args=[str(DEFAULT_EMULATOR),'-m4','-frehd','-batch','-turbo','-na','-ktx','-d0',str(disk),'-d1',str(other),
              *extra,'-itime','60000','-id','4000','-it','-iw','CACHE ERROR CHAIN PASS','-id','200','-it','-iw','STATEFUL CHECK PASS','-id','200','-it',
              '-iw','INPUT OK','-id','200','-it','-iw','MARK: RSXOFFLINE','-iw','No RSXs loaded','-id','500','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
        run(args,cwd=w,timeout=600)
        screens=b'\n'.join(bytes(c&127 for c in f.read_bytes()[:1920]) for f in sorted(w.glob('trs80-text*')))
        assert b'STATEFUL CHECK PASS' in screens and b'INPUT OK' in screens and b'MARK: RSXOFFLINE' in screens
        raw.write_bytes(extract_raw(disk.read_bytes()));data.write_bytes(dmk_to_raw(other.read_bytes(),data_fmt))
    listing=cmd('cpmls','-f',definition(raw),raw).stdout.decode()
    import re
    cache_names=re.findall(r'\$\$RSX0[0-4]\.RSC',listing,re.I)
    assert len(cache_names)==0,listing
    audit=audit_outputs(w,native)
    audit['bounded_cache_files']=cache_names
    audit['cache_reuse_cycles']=1 if native else 6
    audit['native_returning_error_probe']='PASS: removed STATEFUL cache, set change rejected, live service intact, cache restored'
    assert artifacts=={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in tracked},'artifacts changed during qualification'
    assert b'$$$' not in cmd('cpmls','-f',definition(raw),raw).stdout
    for disk in (raw,data):cmd('fsck.cpm','-T','raw','-f',definition(disk),'-n',disk)
    assert a.system.resolve().read_bytes()==original and a.utilities.resolve().read_bytes()==utilities
    result={'status':'PASS','target':a.target,'system_sha256':sha(original),'utilities_sha256':sha(utilities),
            'steps':steps,'batch':batch.decode(),'originals_unchanged':True,'audit':audit,'artifacts':artifacts}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',a.target,'offline stateful relocation and XSUB Function-10 batch input')


if __name__=='__main__':main()
