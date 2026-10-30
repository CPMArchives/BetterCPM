#!/usr/bin/env python3
"""Exercise media insertion, link swaps, removal and writes in one cpmsim process.
Only temporary media is modified. No full-size-image assumption is made.
"""
import argparse
import os
from pathlib import Path
import pty
import select
import signal
import time
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulator', type=Path, required=True)
    args = parser.parse_args()
    simulator = args.simulator.resolve()
    with tempfile.TemporaryDirectory(prefix='cpmsim-live-media-') as directory:
        work = Path(directory)
        disks = work/'disks'; disks.mkdir()
        first = work/'first.dsk'; first.write_bytes(b'A'*128)
        second = work/'second.dsk'; second.write_bytes(b'B'*128)
        readonly = work/'readonly.dsk'; readonly.write_bytes(b'R'*128); readonly.chmod(0o444)
        link = disks/'drived.dsk'
        code = bytearray()
        def out(port, value): code.extend((0x3e,value,0xd3,port))
        def text(value):
            for b in value.encode(): out(1,b)
        # D:, track zero, sector one, DMA buffer at 8000h.
        for port,value in ((10,3),(11,0),(12,1),(15,0),(16,0x80)): out(port,value)
        # Host changes media only after the guest reports it is idle.
        for command in (0,0,0,0,0,1,1,0):
            text('READY')
            code.extend(bytes.fromhex('db00b728fbdb01'))
            if command == 1: code.extend(bytes.fromhex('3e57320080'))
            out(13,command)
            text('[')
            code.extend(bytes.fromhex('db0ec630d301'))
            if command == 0: code.extend(bytes.fromhex('3a0080d301'))
            text(']')
        out(0xa0,0xaa);out(0xa0,0x80)
        image=work/'probe.bin';image.write_bytes(b'\xff\x00\xd6'+code)
        env=dict(os.environ);env['PATH']=str(simulator.parent/'srctools')+os.pathsep+env.get('PATH','')
        env.pop('CPMSIM_ROM_START',None)
        pid,terminal=pty.fork()
        if pid==0:
            os.chdir(work)
            os.execve(simulator,[str(simulator),'-z','-d',str(disks),'-x',str(image)],env)
        pending=bytearray();transcript=bytearray()
        def expect(token):
            deadline=time.monotonic()+10
            while token not in pending:
                remaining=deadline-time.monotonic()
                if remaining<=0: raise AssertionError((token,bytes(transcript)))
                if select.select([terminal],[],[],remaining)[0]:
                    data=os.read(terminal,65536)
                    if not data: raise AssertionError(bytes(transcript))
                    pending.extend(data);transcript.extend(data)
            end=pending.index(token)+len(token);del pending[:end]
        def mount(target):
            replacement=disks/'next';replacement.symlink_to(target);replacement.replace(link)
        actions=(lambda:mount(first),lambda:mount(second),lambda:link.unlink(),
                 lambda:mount(first),lambda:mount(readonly),lambda:None,
                 lambda:mount(second),lambda:None)
        expected=(b'[0A]',b'[0B]',b'[5',b'[0A]',b'[0R]',b'[6]',b'[0]',b'[0W]')
        try:
            for action,result in zip(actions,expected):
                expect(b'READY');action();os.write(terminal,b'x');expect(result)
            _,status=os.waitpid(pid,0)
            assert os.waitstatus_to_exitcode(status)==0
            assert first.read_bytes()==b'A'*128
            assert readonly.read_bytes()==b'R'*128
            assert second.read_bytes()==b'W'+b'R'*127
            print('PASS: insertion, swap, removal, reinsertion, read-only read/write, writable write/read; one process; shortened images')
        finally:
            try:os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:pass
            os.close(terminal)
            readonly.chmod(0o644)

if __name__=='__main__':main()
