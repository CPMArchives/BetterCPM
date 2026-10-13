#!/usr/bin/env python3
"""Compare disk wildcard copies and attributes with pinned DRI PIP."""
import argparse,re,shutil,subprocess,tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack')
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--reference',action='store_true',help='Also run the pinned DRI binary (currently exposes a BetterCP/M compatibility timeout).')
    parser.add_argument('--clear-source-arc',action='store_true',help='Diagnostic control: keep RO/SYS but clear ARC on seeded sources.')
    args=parser.parse_args();report=ROOT/'build/test-results/pip-wildcard';report.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pip-wild-',dir='/private/tmp') as tmp:
        work=Path(tmp);shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
        disk=work/'disks/drivea.dsk'
        def install(path,target):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),target],cwd=work,check=True)
        install(ROOT/'build/pip-development/PIP.COM','0:PIPDEV.COM')
        install(ROOT/'third_party/dri-pip/PIP-1.5-reference.COM','0:PIPREF.COM')
        expected={}
        for name,payload,attrs in [('PWONE.DAT',b'one\x1aafter', ''),('PWTWO.DAT',bytes(range(256))*4+b'tail','a'),('PWSYS.DAT',b'system\x1apadding','rsa'),('PWMULTI.DAT',bytes(range(256))*129+b'multi','')]:
            if args.clear_source_arc:attrs=attrs.replace('a','')
            path=work/name;path.write_bytes(payload);install(path,'3:'+name);expected[name]=payload
            if attrs:subprocess.run(['cpmchattr','-T','raw','-f','bettercpm-default',str(disk),attrs,'3:'+name],cwd=work,check=True)
        commands=[
            (b':PIPDEV A4:=A3:PW*.DAT[RV]\r',b'A0>_ ',120),
        ]
        if args.reference:commands += [
            (b'A6:\r',b'A6>_ ',30),
            (b':PIPREF A:=A:PW???.DAT[G3R]\r',b'A6>_ ',120),
        ]
        session(args.simulator,work/'disks',commands,report/'transcript.txt')
        for name,payload in expected.items():
            copies=[]
            for user in ((3,4,6) if args.reference and name!='PWMULTI.DAT' else (3,4)):
                out=work/(str(user)+'-'+name)
                subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(user)+':'+name,str(out)],cwd=work,check=True)
                copies.append(out.read_bytes())
            assert copies==[payload]*len(copies),(name,[len(v) for v in copies])
        section=re.search(r'diskdef bettercpm-default\s+(.*?)\bend\b',(work/'diskdefs').read_text(),re.S)[1]
        fields=dict(line.split(None,1) for line in section.splitlines() if line.strip())
        size=int(fields['seclen']);boot=int(fields['boottrk'])*size*int(fields['sectrk']);skew=[int(x) for x in fields['skewtab'].split(',')]
        data=disk.read_bytes();attrs={}
        for i in range(int(fields['maxdir'])):
            logical=i*32;offset=boot+skew[logical//size]*size+logical%size;e=data[offset:offset+32]
            if e[0] in (3,4,6):
                name=bytes(v&127 for v in e[1:12]);attrs[(e[0],name)]=sum((e[9+j]>>7)<<j for j in range(3))
        for name in expected:
            if name=='PWMULTI.DAT':continue
            stem,ext=name.split('.');packed=(stem.ljust(8)+ext).encode()
            if args.reference:assert attrs[(4,packed)]==attrs[(6,packed)],(name,attrs[(4,packed)],attrs[(6,packed)])
            assert attrs[(4,packed)]==attrs[(3,packed)]&4
        (report/'attributes.txt').write_text(str(attrs))
    print('PASS: cpmsim wildcard complete record data and development RO/SYS/ARC assertions')

if __name__=='__main__':main()
