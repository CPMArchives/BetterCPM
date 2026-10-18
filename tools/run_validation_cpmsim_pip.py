#!/usr/bin/env python3
"""Check shipped PIP against pinned DRI output on disposable release disks."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_stat_attributes import directory_offsets
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    report=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    for letter in 'ab':shutil.copy2(base/report['image'],w/'disks'/f'drive{letter}.dsk')
    shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    def cpm(tool,letter,*v):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(w/'disks'/f'drive{letter}.dsk'),*map(str,v)],cwd=w,check=True,capture_output=True)
    cpm('cpmrm','b','0:*.*');reference=ROOT/'third_party/dri-pip/PIP-1.5-reference.COM'
    cpm('cpmcp','a',reference,'0:PIPREF.COM')
    fixtures=[(1,'ONE.TXT',b'A'*16387+b'\xff\r\n\x1aIGNORE ONE'),(2,'TWO.TXT',b'B'*17003+b'\x80\r\n\x1aIGNORE TWO'),
              (1,'OBJECT.COM',bytes(range(256))*16),(1,'SMALL.TXT',b'alpha\r\nbeta\x1a')]
    for user,name,data in fixtures:
        f=w/f'{user}-{name}';f.write_bytes(data);cpm('cpmcp','b',f,f'{user}:{name}')
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';prompt=b'A0>_ '
    commands=[b':PIP B4:OURS.TXT=B1:ONE.TXT[V],B2:TWO.TXT[V]\r',b'B4:\r',
              b'A0:PIPREF REF.TXT=ONE.TXT[G1V],TWO.TXT[G2V]\r',
              b'A0:PIP UPPER.TXT=B1:SMALL.TXT[U]\r',b'A0:PIPREF REFUP.TXT=SMALL.TXT[G1U]\r',
              b'A0:PIP B5:=B1:*.COM[V]\r',b'A0:PIP CON:=B1:SMALL.TXT\r',b'A0:\r']
    steps=[]
    for i,command in enumerate(commands):steps.append((command,b'B4>_ ' if 1<=i<7 else prompt,120))
    trace=session(sim,w/'disks',steps,w/'transcript.bin')
    assert b'alpha' in trace and b'VERIFY ERROR' not in trace and b'ERROR:' not in trace
    # DRI S1 is unused-byte metadata. Clear it only in an inspection copy so
    # cpmtools exposes whole physical records rather than its S1 interpretation.
    image=w/'disks/driveb.dsk';data=bytearray(image.read_bytes());raw=directory(image,w/'diskdefs');offsets=directory_offsets(w/'diskdefs')
    for at in range(0,len(raw),32):
        if raw[at]<32:data[offsets[at+13]]=0
    inspect=w/'record-inspection.dsk';inspect.write_bytes(data)
    def get(user,name):
        out=w/f'out-{user}-{name}'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(inspect),f'{user}:{name}',str(out)],cwd=w,check=True,capture_output=True)
        return out.read_bytes()
    ours=get(4,'OURS.TXT');assert ours==get(4,'REF.TXT')
    content=fixtures[0][2].split(b'\x1a')[0]+fixtures[1][2].split(b'\x1a')[0]
    assert ours==content.ljust((len(content)+127)//128*128,b'\x1a')
    assert get(4,'UPPER.TXT')==get(4,'REFUP.TXT') and get(4,'UPPER.TXT').startswith(b'ALPHA\r\nBETA\x1a')
    assert get(5,'OBJECT.COM')==fixtures[2][2]
    for user,name,original in fixtures:assert get(user,name)[:len(original)]==original,(user,name)
    shipped=audit(base,report,w,w/'disks/drivea.dsk')
    r=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image)],cwd=w,capture_output=True,check=True)
    (w/'filesystem-b.txt').write_bytes(r.stdout+r.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','runner_sha256':sha(Path(__file__)),'baseline_sha256':report['sha256'],'reference_sha256':sha(reference),'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped,'scope':'multi-user multi-extent verified concatenation, uppercase transform, binary wildcard copy, console output and source preservation'},indent=2)+'\n')
    print('PASS shipped PIP disk/console workflows and pinned DRI parity',w)

if __name__=='__main__':main()
