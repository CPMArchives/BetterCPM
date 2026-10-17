#!/usr/bin/env python3
"""Broader shipped TYPE, ED and CONFIG regressions on private cpmsim media."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
import pyte
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import parse
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]
MORE=b'MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--group',choices=('all','type','lifecycle'),default='all')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image'];assert report['target']=='z80pack' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True)
    results=[]
    def prepare(label):
        w=Path(tempfile.mkdtemp(prefix=label+'-',dir=a.output.resolve()));d=w/'disks';d.mkdir()
        shutil.copy2(a.baseline/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
        for drive in 'abc':
            image=d/f'drive{drive}.dsk';shutil.copy2(original,image)
            if drive!='a':subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:*.*'],cwd=w,check=True,capture_output=True)
        return w,d
    def put(w,d,drive,user,name,data):
        f=w/name;f.write_bytes(data)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(d/f'drive{drive}.dsk'),str(f),f'{user}:{name}'],cwd=w,check=True,capture_output=True)
    def get(w,d,drive,user,name):
        f=w/f'after-{user}-{name}'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(d/f'drive{drive}.dsk'),f'{user}:{name}',str(f)],cwd=w,check=True,capture_output=True)
        return f.read_bytes()
    def finish(w,d,label,detail):
        shipped=audit(a.baseline,report,w,d/'drivea.dsk')
        for letter in 'bc':
            c=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(d/f'drive{letter}.dsk')],cwd=w,capture_output=True,text=True)
            (w/(letter+'-filesystem.txt')).write_text(c.stdout+c.stderr);assert c.returncode==0
        r={'status':'PASS','case':label,'baseline_sha256':report['sha256'],'simulator_sha256':sha(a.simulator),'detail':detail,'unchanged_shipped_files':shipped}
        (w/'result.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(label,'PASS',w,flush=True)
    if a.group in ('all','type'):
        w,d=prepare('type-paging')
        payload=b''.join(f'PAGE ROW {i:02d}\r\n'.encode() for i in range(55))+b'\x1aHIDDEN'
        put(w,d,'a',3,'LONG.TXT',payload)
        steps=[(b'RSX LOAD ANSISCRN\r',b'A0>',30),(b'RSX LOAD ANSI\r',b'A0>',30),
               (b':TYPE A3:LONG.TXT /P\r',MORE,30)]
        steps += [(key,MORE,30) for key in (b'\x03',b',',b' ',b'.')]
        steps += [(b'.',b'\x07',30),(b'\x12',MORE,30),(b'\x11',b'A0>',30),
                  (b'RSX UNLOAD ANSI\r',b'A0>',30),(b'RSX UNLOAD ANSISCRN\r',b'A0>',30),(b'BYE\r',b'System halted',30)]
        t=session(a.simulator,d,steps,w/'transcript.bin')
        assert t.count(b'PAGE ROW 00')==2 and t.count(b'PAGE ROW 54')==1 and b'HIDDEN' not in t
        assert get(w,d,'a',3,'LONG.TXT')[:len(payload)]==payload
        finish(w,d,'type-paging','ANSI pair loaded; Ctrl-C next, backward, Space, EOF, EOF bell, Ctrl-R replay, Ctrl-Q; source unchanged')
        w,d=prepare('type-boundaries')
        for name,data in [('ONE.DOC',b'FIRST\r\n\x1a'),('TWO.DOC',b'SECOND\r\n\x1a')]:put(w,d,'a',3,name,data)
        t=session(a.simulator,d,[(b'RSX LOAD ANSISCRN\r',b'A0>',30),(b'RSX LOAD ANSI\r',b'A0>',30),
            (b':TYPE A3:*.DOC /P\r',MORE,30),(b'>',MORE,30),(b'<',MORE,30),(b'\x11',b'A0>',30),
            (b'RSX UNLOAD ANSI\r',b'A0>',30),(b'RSX UNLOAD ANSISCRN\r',b'A0>',30),(b'BYE\r',b'System halted',30)],w/'transcript.bin')
        positions=[];start=0
        while (at:=t.find(MORE,start))>=0:positions.append(at);start=at+len(MORE)
        assert len(positions)==3
        for index,want in enumerate(('ONE.DOC','TWO.DOC','ONE.DOC')):
            s=pyte.Screen(80,24);pyte.Stream(s).feed(t[:positions[index]].decode('ascii',errors='replace'))
            (w/f'page-{index}.txt').write_text('\n'.join(s.display)+'\n')
            top=next(line for line in s.display if line.strip()) if index==0 else s.display[0]
            assert want in top,(index,s.display[:3])
        assert b'FIRST' in t[:positions[0]] and b'SECOND' in t[:positions[0]]
        for name,data in [('ONE.DOC',b'FIRST\r\n\x1a'),('TWO.DOC',b'SECOND\r\n\x1a')]:assert get(w,d,'a',3,name)[:len(data)]==data
        finish(w,d,'type-boundaries','Continuous final page; > brings second banner to row 0, < restores first banner to row 0; sources unchanged')
    if a.group in ('all','lifecycle'):
        for mode in ('save','quit','head'):
            w,d=prepare('ed-'+mode);old=b'OLD\r\n\x1a';sentinel=b'USER ZERO\r\n\x1a'
            put(w,d,'b',7,'CASE.TXT',old);put(w,d,'b',0,'CASE.TXT',sentinel)
            steps=[(b':ED B7:CASE.TXT\r',b'*',30),(b'INEW\x1a\r',b'*',30)]
            if mode=='quit':steps += [(b'Q\r',b'-(Y/N)?',30),(b'Y',b'A0>',30)]
            elif mode=='head':steps += [(b'H\r',b'*',30),(b'IAGAIN\x1a\r',b'*',30),(b'E\r',b'B7>',30)]
            else:steps += [(b'E\r',b'B7>',30)]
            if mode!='quit':steps += [(b'A0:\r',b'A0>',30)]
            steps += [(b'BYE\r',b'System halted',30)];session(a.simulator,d,steps,w/'transcript.bin')
            expected=old[:-1] if mode=='quit' else (b'AGAINNEW'+old[:-1] if mode=='head' else b'NEW'+old[:-1])
            assert get(w,d,'b',7,'CASE.TXT').split(b'\x1a')[0]==expected
            assert get(w,d,'b',0,'CASE.TXT').split(b'\x1a')[0]==sentinel[:-1]
            listing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(d/'driveb.dsk'),'7:*.*'],cwd=w).lower()
            assert b'case.$$$' not in listing
            if mode=='quit':assert b'case.bak' not in listing
            else:assert get(w,d,'b',7,'CASE.BAK').split(b'\x1a')[0]==(b'NEW'+old[:-1] if mode=='head' else old[:-1])
            finish(w,d,'ed-'+mode,'Real editor entry; user-7 text, backup/work-file lifecycle and user-0 sentinel independently verified')
        fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
        def offset(record):
            track,within=divmod(record,fmt.spt);return track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
        offsets=[offset(1),offset(2)]
        for answer in (b'N',b'Y'):
            label='config-startup-'+answer.decode();w,d=prepare(label);image=d/'drivea.dsk'
            before=image.read_bytes();old=b''.join(before[at:at+128] for at in offsets)
            t=session(a.simulator,d,[(b'CONFIG /STARTUP="VER /VER"\r',b'(Y/N)? ',30),(answer,b'A0>',30),(b'BYE\r',b'System halted',30)],w/'transcript.bin')
            after=image.read_bytes();actual=b''.join(after[at:at+128] for at in offsets)
            assert parse(actual,system_base=LAYOUT['SYSTEM'])==('VER /VER' if answer==b'Y' else parse(old,system_base=LAYOUT['SYSTEM']))
            if answer==b'N':assert actual==old
            else:
                assert b'saved and verified' in t
                boot=session(a.simulator,d,[(b'BYE\r',b'System halted',30)],w/'cold-boot.bin')
                assert b'BetterCP/M VER 1.0 (Resident, RCP Build ' in boot
            finish(w,d,label,'Declined/confirmed protected startup record; confirmed command executes on next cold boot; shipped files unchanged')
    (a.output/'application-summary.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
