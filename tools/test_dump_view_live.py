#!/usr/bin/env python3
"""Verify enhanced DUMP on real cpmsim BDOS/RSXs with independent pyte screens."""
import argparse,hashlib,json,os,pty,select,shutil,signal,subprocess,tempfile,time
from pathlib import Path
import pyte
from test_dump_enhanced import row
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve();disks=w/'disks';disks.mkdir()
    report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256']
    image=disks/'drivea.dsk';shutil.copy2(original,image);shutil.copy2(a.baseline/'diskdefs',w/'diskdefs')
    def command(*args):return subprocess.run(args,cwd=w,check=True,capture_output=True)
    payload=bytes(range(256))*8;(w/'DHEX.BIN').write_bytes(payload)
    for source,target in [(ROOT/'build/utilities/DUMP.COM','0:DUMP.COM'),(w/'DHEX.BIN','0:DHEX.BIN')]:command('cpmcp','-f','bettercpm-default',str(image),str(source),target)
    before=sha(image)
    env=dict(os.environ);env['PATH']=str(a.simulator.parent/'srctools')+os.pathsep+env['PATH']
    pid,fd=pty.fork()
    if pid==0:
        os.chdir(w);os.execve(str(a.simulator),[str(a.simulator),'-z','-d',str(disks)],env)
    transcript=bytearray();pending=bytearray();screens={};screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
    def expect(marker):
        deadline=time.monotonic()+30
        while marker not in pending:
            left=deadline-time.monotonic()
            if left<=0:raise AssertionError(('timeout',marker,bytes(transcript[-2000:])))
            ready,_,_=select.select([fd],[],[],left)
            if not ready:continue
            data=os.read(fd,65536)
            if not data:raise AssertionError('emulator exited early')
            transcript.extend(data);pending.extend(data);stream.feed(data.decode('ascii',errors='replace'))
            (w/'transcript.bin').write_bytes(transcript)
        end=pending.index(marker)+len(marker);del pending[:end]
    def step(label,keys,marker):
        os.write(fd,keys);expect(marker);screens[label]=list(screen.display)
    try:
        expect(b'A0>_ ')
        step('backend',b'RSX LOAD ANSISCRN\r',b'A0>_ ')
        step('monitor',b'RSX LOAD ANSI\r',b'A0>_ ')
        hints=b'^R Up ^C Down F Find G Go Q Quit'
        step('wide',b'DUMP DHEX.BIN /P\r',hints)
        step('down',b'\x03',hints)
        step('goto',b'G0\r',hints)
        step('match',b'F7F8081\rH',b'Match at 0000007F')
        step('next',b'.',b'Match at 0000017F')
        step('previous',b',',b'Match at 0000007F')
        step('cancel',b'FABC\x1b',b'., Match')
        step('returned',b'Q',b'A0>_ ')
        step('compact',b'DUMP DHEX.BIN /40 /P\r',hints)
        step('done',b'Q',b'A0>_ ')
    finally:
        os.kill(pid,signal.SIGTERM)
        deadline=time.monotonic()+1
        while not os.waitpid(pid,os.WNOHANG)[0]:
            if time.monotonic()>=deadline:
                os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);break
            time.sleep(.02)
        os.close(fd)
        (w/'screens.json').write_text(json.dumps(screens,indent=2)+'\n')
    for label,pos in [('wide',0),('down',368),('goto',0),('match',112),('next',368),('previous',112),('cancel',112)]:
        assert screens[label][0].startswith(row(payload,pos)),(label,screens[label][0])
    assert screens['compact'][0].startswith(row(payload,0,True))
    extracted=w/'readback.bin';command('cpmcp','-f','bettercpm-default',str(image),'0:DHEX.BIN',str(extracted));assert extracted.read_bytes()==payload
    command('fsck.cpm','-f','bettercpm-default','-n',str(image));assert sha(original)==report['sha256']
    # Loading RSXs can change access metadata; independently assert file payload
    # and fsck rather than claiming the entire session is disk-byte-identical.
    result={'status':'PASS','program_sha256':sha(ROOT/'build/utilities/DUMP.COM'),'baseline_sha256':sha(original),'initial_private_image_sha256':before,'stages':list(screens),'scope':'Actual cpmsim with shipped ANSISCRN and ANSI, independent pyte cell screens: both layouts, paging, Go To, record-crossing forward/backward Find, ESC cancellation, CCP return; fixture data preserved and filesystem clean.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(w)
if __name__=='__main__':main()
