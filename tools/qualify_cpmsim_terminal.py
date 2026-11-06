"""Run the guarded launcher, ANSI lifecycle and resize/redraw on private media."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import signal
import struct
import subprocess
import termios
import time
from build_z80pack_image import write_launchers, disk_definition, DEFAULT_FORMAT
from fdf_format import select_fdf

ROOT=Path(__file__).resolve().parents[1]
sha=lambda data:hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--image',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    simulator=a.simulator.resolve();original=a.image.read_bytes();disks=w/'disks';disks.mkdir()
    image=disks/'drivea.dsk';image.write_bytes(original)
    (w/'diskdefs').write_text(disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT)))
    write_launchers(w,simulator)
    def cpm(tool,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',*map(str,args)],cwd=w,check=True,capture_output=True)
    names=re.findall(r'^[a-z0-9$][a-z0-9_$.-]*\.[a-z0-9$]+$',cpm('cpmls',image).stdout.decode(),re.M|re.I)
    def content(name):
        f=w/'readback';cpm('cpmcp',image,'0:'+name,f);return f.read_bytes()
    before={n:sha(content(n)) for n in names};assert len(before)>20
    pid,fd=pty.fork()
    if pid==0:
        fcntl.ioctl(1,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0))
        os.chdir(w);launcher=w/'launch-z80pack.command';os.execve(launcher,[str(launcher)],dict(os.environ))
    trace=bytearray();pending=bytearray();phases=[]
    def expect(wanted):
        deadline=time.monotonic()+30
        while wanted not in pending:
            assert time.monotonic()<deadline,(wanted,trace[-1500:])
            if select.select([fd],[],[],.1)[0]:
                data=os.read(fd,65536);assert data,'emulator exited early'
                trace.extend(data);pending.extend(data)
        del pending[:pending.index(wanted)+len(wanted)]
    def send(data,wanted):os.write(fd,data);expect(wanted)
    try:
        expect(b'A0>_ ')
        assert b'Booting...' in trace and b'cpmsim was not started' not in trace
        send(b'RSX LOAD ANSISCRN\r',b'A0>_ ');send(b'RSX LOAD ANSI\r',b'A0>_ ')
        assert b'Load Error' not in trace and b'profile error' not in trace
        for columns,rows in ((80,24),(100,40),(77,20),(80,24)):
            fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))
            start=len(trace);send(b'CONFIG\r',b'BREAK (^C) to exit.')
            send(b'\x03',b'A0>_ ')
            fragment=bytes(trace[start:]);assert b'Configuration options:' in fragment and b'\x1b[' in fragment
            (w/f'phase-{len(phases)}.bin').write_bytes(fragment)
            phases.append({'columns':columns,'rows':rows,'menu_and_exit':'PASS',
                           'supported_size':columns>=80 and rows>=24})
        send(b'RSX UNLOAD ANSI\r',b'A0>_ ');send(b'RSX UNLOAD ANSISCRN\r',b'A0>_ ')
        send(b'RSX LIST\r',b'A0>_ ');assert b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
        send(b'TYPE README.TXT\r',b'A0>_ ')
    finally:
        (w/'transcript.bin').write_bytes(trace)
        try:os.kill(pid,signal.SIGTERM)
        except ProcessLookupError:pass
        deadline=time.monotonic()+1
        while True:
            result,_=os.waitpid(pid,os.WNOHANG)
            if result:break
            if time.monotonic()>deadline:
                os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);break
            time.sleep(.02)
        os.close(fd)
    for n,h in before.items():assert sha(content(n))==h,n
    assert image.read_bytes()[:27648]==original[:27648]
    cpm('fsck.cpm','-n',image);assert a.image.read_bytes()==original
    result={'status':'PASS','system_sha256':sha(original),'simulator_sha256':sha(simulator.read_bytes()),
            'launcher_and_guard':'generated RAM launcher; real cpmsim','phases':phases,
            'ansi_load_unload':'PASS','post_exit_file_read':'PASS','unloaded_tpa':'53K',
            'preserved_files':list(before),'reserved_tracks_unchanged':True,'filesystem':'PASS',
            'original_image_unchanged':True,'limit':'Host launch check only. Resize/redraw checks guest lifecycle and emitted menu, not graphical rendering or smaller-screen support.'}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS guarded real cpmsim, ANSI load/unload, CONFIG redraw, resize/recovery and disk audit')


if __name__=='__main__':main()
