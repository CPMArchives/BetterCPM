#!/usr/bin/env python3
"""Compare real disk concatenation with the pinned stock DRI PIP binary."""
import argparse
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from test_z80pack_sysgen_install import session

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack')
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    report=ROOT/'build/test-results/pip-concat';report.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pip-concat-',dir='/private/tmp') as tmp:
        work=Path(tmp);shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
        disk=work/'disks/drivea.dsk'
        def install(path,target):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),target],cwd=work,check=True)
        install(ROOT/'build/pip-development/PIP.COM','0:PIPDEV.COM')
        install(ROOT/'third_party/dri-pip/PIP-1.5-reference.COM','0:PIPREF.COM')
        one=work/'ONE.TXT';one.write_bytes(b'A'*16387+b'\xff\r\n\x1aIGNORE ONE')
        two=work/'TWO.TXT';two.write_bytes(b'B'*17003+b'\x80\r\n\x1aIGNORE TWO')
        obj=work/'OBJ.COM';obj.write_bytes(b'\x00\x1a\xffOBJECT')
        install(one,'3:ONE.TXT');install(two,'7:TWO.TXT');install(obj,'3:OBJ.COM')
        session(args.simulator,work/'disks',[
            (b':PIPDEV A4:OURS.TXT=A3:ONE.TXT[V],A7:TWO.TXT[V]\r',b'A0>_ ',120),
            (b'A4:\r',b'A4>_ ',30),
            (b':PIPREF STOCK.TXT=ONE.TXT[G3V],TWO.TXT[G7V]\r',b'A4>_ ',120),
            (b':PIPDEV MIX.TXT=A3:OBJ.COM,A7:TWO.TXT\r',b'A4>_ ',120),
            (b':PIPREF REFMIX.TXT=OBJ.COM[G3],TWO.TXT[G7]\r',b'A4>_ ',120),
        ],report/'transcript.txt')
        def extract(name,user=4,image=None):
            out=work/name
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image or disk),str(user)+':'+name,str(out)],cwd=work,check=True)
            return out.read_bytes()
        ours=extract('OURS.TXT');stock=extract('STOCK.TXT')
        (report/'ours.bin').write_bytes(ours);(report/'stock.bin').write_bytes(stock)
        assert ours==stock
        assert extract('MIX.TXT')==extract('REFMIX.TXT')
        assert extract('ONE.TXT',3)==one.read_bytes() and extract('TWO.TXT',7)==two.read_bytes()
        # DRI S1 counts unused bytes; cpmtools treats S1 as used bytes. Compare
        # the ordinary extraction first, then clear S1 on a separate inspection
        # copy so cpmtools exposes every physical record without truncation.
        section=re.search(r'diskdef bettercpm-default\s+(.*?)\bend\b',(work/'diskdefs').read_text(),re.S)[1]
        fields=dict(line.split(None,1) for line in section.splitlines() if line.strip())
        size=int(fields['seclen']);sectors=int(fields['sectrk']);boot=int(fields['boottrk'])*size*sectors
        skew=[int(x) for x in fields['skewtab'].split(',')]
        data=bytearray(disk.read_bytes())
        for i in range(int(fields['maxdir'])):
            logical=i*32;offset=boot+skew[logical//size]*size+logical%size
            if data[offset]==4:data[offset+13]=0
        inspection=work/'records.dsk';inspection.write_bytes(data)
        content=one.read_bytes().split(b'\x1a')[0]+two.read_bytes().split(b'\x1a')[0]
        expected=content.ljust((len(content)+127)//128*128,b'\x1a')
        assert extract('OURS.TXT',image=inspection)==extract('STOCK.TXT',image=inspection)==expected
        assert extract('MIX.TXT',image=inspection)==extract('REFMIX.TXT',image=inspection)
    print('PASS: cpmsim mixed-user multi-extent text and COM/text concatenation matches stock DRI PIP')

if __name__=='__main__':main()
