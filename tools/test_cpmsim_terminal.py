"""Exercise real PTY dimensions and the generated RAM/ROM launchers."""
import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time
from unittest.mock import patch
import cpmsim_terminal
from build_z80pack_image import write_launchers

ROOT=Path(__file__).resolve().parents[1]


def resize(fd,columns,rows):
    fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))


def execute(args,work,env,size=None,terminal=None):
    if size is None:
        p=subprocess.run(args,cwd=work,env=env,capture_output=True,timeout=5)
        return p.returncode,p.stdout+p.stderr
    own=terminal is None
    master,slave=pty.openpty() if own else terminal
    resize(slave,*size)
    p=subprocess.Popen(args,stdin=slave,stdout=slave,stderr=slave,cwd=work,env=env)
    data=bytearray();deadline=time.monotonic()+5
    try:
        while p.poll() is None:
            if time.monotonic()>deadline:raise TimeoutError('guard/fixture did not finish')
            ready,_,_=select.select([master],[],[],.05)
            if ready:data.extend(os.read(master,65536))
        while select.select([master],[],[],.05)[0]:
            try:data.extend(os.read(master,65536))
            except OSError as error:
                if error.errno!=errno.EIO:raise
                break
        return p.returncode,bytes(data)
    finally:
        if p.poll() is None:p.kill();p.wait()
        if own:os.close(master);os.close(slave)


def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix='cpmsim-terminal-') as tmp:
        w=Path(tmp);runtime=w/"runtime with 'quotes'";runtime.mkdir()
        simulator=runtime/'cpmsim';log=w/'execution.json'
        simulator.write_text('#!'+sys.executable+'\nimport os,sys,json\nfrom pathlib import Path\nPath(os.environ["FAKE_LOG"]).write_text(json.dumps({"argv":sys.argv[1:],"cwd":os.getcwd(),"path":os.environ["PATH"]}))\nprint("EMULATOR STARTED")\nsys.exit(7)\n')
        simulator.chmod(0o755)
        env=dict(os.environ,FAKE_LOG=str(log),COLUMNS='999',LINES='999')
        command=[sys.executable,str(ROOT/'tools/cpmsim_terminal.py'),'--',str(simulator),'argument with spaces','*.com']
        for size in ((77,20),(79,24),(80,23),(100,20),(40,24),(0,0)):
            rc,out=execute(command,w,env,size)
            assert rc==1 and not log.exists(),(size,rc,out)
            assert b'BetterCP/M requires at least 80x24' in out and b'then launch again' in out,out
            results.append({'size':size,'result':'REFUSED; emulator not executed'})
        for size in ((80,24),(100,40)):
            rc,out=execute(command,w,env,size)
            assert rc==7 and b'EMULATOR STARTED' in out,(size,rc,out)
            record=json.loads(log.read_text());assert record['argv']==command[-2:] and Path(record['cwd']).resolve()==w.resolve()
            log.unlink();results.append({'size':size,'result':'LAUNCHED; arguments/cwd/exit status preserved'})
        # Reuse one terminal to prove retry measures the enlarged window afresh.
        master,slave=pty.openpty()
        try:
            assert execute(command,w,env,(77,20),(master,slave))[0]==1 and not log.exists()
            assert execute(command,w,env,(80,24),(master,slave))[0]==7 and log.exists()
            log.unlink()
        finally:os.close(master);os.close(slave)
        rc,out=execute(command,w,env)
        assert rc==7 and log.exists();log.unlink() # redirected automation stays usable
        with patch.object(cpmsim_terminal.os,'isatty',return_value=True),patch.object(cpmsim_terminal.os,'get_terminal_size',side_effect=OSError('unknown')):
            assert not cpmsim_terminal.check_terminal()
        output=w/'generated launchers';output.mkdir()
        write_launchers(output,simulator)
        assert (output/'cpmsim_terminal.py').read_bytes()==(ROOT/'tools/cpmsim_terminal.py').read_bytes()
        for name,flags in (('launch-z80pack.command',['-z','-d',str(output/'disks')]),
                           ('launch-z80pack-rom.command',['-z','-x',str(output/'rom/rom-boot.hex'),'-d',str(output/'rom-disks')])):
            args=[str(output/name),'extra argument']
            assert execute(args,w,env,(77,20))[0]==1 and not log.exists()
            assert execute(args,w,env,(80,24))[0]==7
            record=json.loads(log.read_text());assert record['argv']==flags+['extra argument'],record
            assert Path(record['cwd']).resolve()==output.resolve() and record['path'].startswith(str(runtime/'srctools')+':'),record
            log.unlink()
    out=ROOT/'build/ansi-size';out.mkdir(parents=True,exist_ok=True)
    (out/'host-tests.json').write_text(json.dumps({'status':'PASS','sizes':results,'resize_retry':'PASS','redirected_output':'PASS','unavailable_size':'REFUSED','generated_ram_and_rom_launchers':'PASS','environment_dimensions_ignored':True},indent=2)+'\n')
    print('PASS real PTY size/refusal, resize/retry, automation, argv/cwd/status and both generated launchers')


if __name__=='__main__':main()
