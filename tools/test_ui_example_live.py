#!/usr/bin/env python3
"""Qualify the shared UI example through real cpmsim and monitor output."""
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
    command('cpmcp','-f','bettercpm-default',str(image),str(ROOT/'build/shared-ui/UIEX.COM'),'0:UIEX.COM')
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
        for suffix,tag in [(b'', 'wide'),(b' /40','compact')]:
            step(tag+'-default',b'UIEX'+suffix+b'\r',b'Value: [DEFAULT] \x1b[24;18H\x1b[7m_')
            step(tag+'-invalid',b'BAD\r',b'BAD is rejected; edit or cancel.')
            step(tag+'-restored',b'\x19',b'Value: [DEFAULT] \x1b[24;18H\x1b[7m_')
            step(tag+'-choice',b'\r' if suffix else b'OK\r',b'Accept? (Y/N) [N]')
            error=b'Demo rejects Y; choo~' if suffix else b'Demo rejects Y; choose N or cancel.'
            step(tag+'-error',b'Y',error)
            step(tag+'-accepted',b'\r',b'Press a key to return.')
            step(tag+'-return',b'Q',b'A0>_ ')
        step('cancel-default',b'UIEX\r',b'Value: [DEFAULT] \x1b[24;18H\x1b[7m_')
        step('text-cancel',b'\x03',b'Accept? (Y/N) [N]')
        step('choice-cancel',b'\x1b',b'Press a key to return.')
        step('cancel-return',b'Q',b'A0>_ ')
    finally:
        os.kill(pid,signal.SIGTERM)
        deadline=time.monotonic()+1
        while not os.waitpid(pid,os.WNOHANG)[0]:
            if time.monotonic()>=deadline:
                os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);break
            time.sleep(.02)
        os.close(fd)
        (w/'screens.json').write_text(json.dumps(screens,indent=2)+'\n')
    for tag in ['wide','compact']:
        for stage in ['default','invalid','restored','choice','error','accepted']:
            frame=screens[tag+'-'+stage]
            assert frame[0].startswith('Shared UI developer example')
            assert frame[2].startswith('Body sentinel: unchanged by prompts.')
        assert screens[tag+'-default'][23].startswith('Value: [DEFAULT] _')
        assert screens[tag+'-restored'][23].startswith('Value: [DEFAULT] _')
        assert screens[tag+'-error'][23].startswith('Accept? (Y/N) [N] Demo rejects Y;')
        assert screens[tag+'-accepted'][1].startswith('DEFAULT' if tag=='compact' else 'OK')
        assert screens[tag+'-accepted'][3].startswith('Choice N accepted')
    assert screens['compact-error'][23][38]=='~'
    assert not screens['compact-error'][23][39:].strip()
    assert screens['choice-cancel'][1].startswith('Cancelled')
    assert screens['choice-cancel'][3].startswith('Cancelled')
    command('fsck.cpm','-f','bettercpm-default','-n',str(image));assert sha(original)==report['sha256']
    result={'status':'PASS','program_sha256':sha(ROOT/'build/shared-ui/UIEX.COM'),'baseline_sha256':sha(original),'initial_private_image_sha256':before,'stages':list(screens),'scope':'Real cpmsim ANSISCRN/ANSI: wide/compact separate defaults, rejection/correction, Ctrl-Y restoration, immediate choice errors, marked truncation, Enter default, Ctrl-C/ESC cancellation, untouched body rows, clean filesystem and unchanged reference image.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(w)
if __name__=='__main__':main()
