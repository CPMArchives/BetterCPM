#!/usr/bin/env python3
"""Accept packaged DDT from Utilities B: on disposable release media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from build_ddt import ROOT, version_text
from build_utilities_disk import build as utilities
from build_z80pack_image import disk_definition,DEFAULT_FORMAT
from fdf_format import select_fdf
from convert_fdf_image import dmk_to_raw
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build as dmk
from test_z80pack_sysgen_install import session
from trs80gp_launch import run as launch
from run_trs80_command import DEFAULT_EMULATOR,key_args
SHA=None
TINY=bytes.fromhex('3e05320003c9')
sha=lambda b:hashlib.sha256(b).hexdigest()


def command(w,*args):
    r=subprocess.run([str(x) for x in args],cwd=w,capture_output=True)
    if r.returncode:raise RuntimeError(f'{args}: {r.stdout!r} {r.stderr!r}')
    return r.stdout


def cpmsim(w,system,utility,artifacts,simulator):
    disks=w/'disks';disks.mkdir();a=disks/'drivea.dsk';b=disks/'driveb.dsk'
    shutil.copyfile(system,a);shutil.copyfile(utility,b)
    for letter in 'cd':shutil.copyfile(artifacts/f'build/z80pack/disks/drive{letter}.dsk',disks/f'drive{letter}.dsk')
    tiny=w/'TINY.COM';tiny.write_bytes(TINY)
    command(w,'cpmcp','-f','bettercpm-default',a,tiny,'0:TINY.COM')
    before=b.read_bytes();prompt=b'A0>_ ';ready=b'\r\n-'
    steps=[(b'B:DDT /VER\r',prompt,30),(b'B:DDT /VER X\r',prompt,30),
           (b'B:DDT TINY.COM\r',ready,30),(b'L100,105\r',b'0105  RET',30),(b'',ready,30),
           (b'H100,2X\x7f0\r',b'0120 00E0',30),(b'',ready,30),
           (b'F300,300,41\r',ready,30),(b'S300\r',b'0300 41 ',30),
           (b'99\x1b',ready,30),(b'D300,300\r',b'0300 41',30),(b'',ready,30),
           (b'A400\rMVI A,5\rRET\r.\r',ready,30),(b'L400,402\r',b'0402  RET',30),(b'',ready,30),
           (b'G100,102\r',b'*0102',30),(b'',ready,30),(b'T1\r',ready,30),
           (b'D300,300\r',b'0300 05',30),(b'',ready,30),(b'XP\r',b'P=0105 ',30),
           (b'100\r',ready,30),(b'U1\r',ready,30),(b'G0\r',prompt,30),
           (b'B:DDT\r',ready,30),(b'\x03',prompt,30)]
    text=session(simulator,disks,steps,w/'transcript.bin')
    assert b'Invalid /VER usage.' not in text and version_text().encode() in text
    assert b.read_bytes()==before,'Utilities changed'
    command(w,'cpmcp','-f','bettercpm-default',a,'0:TINY.COM',w/'TINY-after.COM')
    assert (w/'TINY-after.COM').read_bytes()[:len(TINY)]==TINY
    for image in [a,b]:command(w,'fsck.cpm','-n','-f','bettercpm-default',image)
    return {'status':'PASS','interactions':len(steps),'utilities_unchanged':True,'debuggee_unchanged':True,'filesystem':'PASS','caller_drive':'A0','transcript_sha256':sha(text)}


def model4(w,system,utility):
    a=w/'a.dmk';b=w/'b.dmk';raw=extract_raw(system.read_bytes());add_file(raw,'TINY.COM',TINY);a.write_bytes(dmk(raw));shutil.copyfile(utility,b)
    before=b.read_bytes();cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(a),'-d1',str(b),'-itime','60000','-iw','Type TYPE README.TXT for more','-id','6000'];stages=[]
    def snap(name,delay=1500):stages.append(name);cmd.extend(['-id',str(delay),'-it'])
    def keys(s):cmd.extend(key_args(s,delay=25))
    snap('boot');keys('RSX LIST\r');snap('providers',5000)
    keys('B:DDT /VER\r');snap('version',5000)
    keys('B:DDT TINY.COM\r');snap('loaded',5000)
    keys('L100,105\r');snap('debuggee')
    keys('H100,2X\x7f0\r');snap('editing')
    keys('F300,300,41\rS300\r99');snap('provisional')
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25'];snap('cancel')
    keys('D300,300\r');snap('uncommitted')
    keys('G100,102\r');snap('breakpoint')
    keys('T1\rD300,300\r');snap('stepped')
    keys('XP\r100\rU1\rG0\r');snap('return',3000)
    keys('B:DDT\r');snap('restart',3000)
    keys('\x03');snap('break',3000);cmd+=['-ix']
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');launch(cmd,cwd=w,timeout=600)
    captures=sorted(w.glob('trs80-text*'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==len(stages)
    screens={n:bytes(c&127 for c in p.read_bytes()[:1920]) for n,p in zip(stages,captures)}
    for n,t in screens.items():(w/(n+'.txt')).write_text('\n'.join(t[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    expected={'boot':b'A0>','providers':b'ADM3A','version':version_text().splitlines()[0].encode(),'loaded':b'-_',
              'debuggee':b'0105  RET','editing':b'0120 00E0','provisional':b'0300 41 99_',
              'cancel':b'-_','uncommitted':b'0300 41 A','breakpoint':b'*0102',
              'stepped':b'0300 05','return':b'A0>','restart':b'-_','break':b'A0>'}
    for n,v in expected.items():assert v in screens[n],(n,v,screens[n])
    assert b'M4SCRN' in screens['providers'] and b'0300 41 99' not in screens['cancel']
    assert b.read_bytes()==before,'Utilities changed'
    # Convert only private images for independent cpmtools readback/checking.
    araw=w/'a.raw';araw.write_bytes(extract_raw(a.read_bytes()))
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK-INT.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
    braw=w/'b.raw';braw.write_bytes(dmk_to_raw(b.read_bytes(),fmt))
    command(w,'cpmcp','-f','ddt-system',araw,'0:TINY.COM',w/'TINY-after.COM')
    assert (w/'TINY-after.COM').read_bytes()[:len(TINY)]==TINY
    command(w,'fsck.cpm','-n','-f','ddt-system',araw);command(w,'fsck.cpm','-n','-f','bettercpm-mm-80t-ds-data',braw)
    return {'status':'PASS','stages':stages,'utilities_unchanged':True,'debuggee_unchanged':True,'filesystem':'PASS','caller_drive':'A0','providers':['M4SCRN','ADM3A']}


def main():
    global SHA
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--system',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp']);args=p.parse_args()
    w=args.output.resolve();w.mkdir(parents=True,exist_ok=False)
    defs=disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT))+'''diskdef ddt-system
 libdsk:format pcw800
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
'''
    SHA=sha((args.artifacts/'build/utilities/DDT.COM').read_bytes())
    packaged=utilities(w/'packaged',args.artifacts)
    sources={p:p.read_bytes() for p in args.system.glob('*/*') if p.suffix in ('.dsk','.dmk')}
    result={}
    try:
        for target,image,report in packaged:
            platform=report['target']
            if platform not in args.platforms or not any(row['name']=='DDT.COM' for row in report['included']):
                continue
            dest=w/platform;dest.mkdir();(dest/'diskdefs').write_text(defs)
            system=args.system/platform/json.loads((args.system/platform/'report.json').read_text())['image']
            utility=w/'packaged'/target
            assert next(x for x in report['included'] if x['name']=='DDT.COM')['sha256']==SHA
            result[platform]=cpmsim(dest,system,utility,args.artifacts,args.simulator) if platform=='z80pack' else model4(dest,system,utility)
            result[platform]['utilities_image']=target
            result[platform]['utilities_sha256']=sha(image)
            result[platform]['ddt_sha256']=SHA
            result[platform]['system_sha256']=sha(system.read_bytes())
            assert utility.read_bytes()==image
    finally:
        for p,data in sources.items():assert p.read_bytes()==data,('source image changed',p)
    result={'ddt_utilities_acceptance':'PASS','whole_utilities_disk':'PROVISIONAL','ddt_sha256':SHA,'sources_unchanged':True,'platforms':result,'source_images':{str(p):sha(data) for p,data in sources.items()}}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
