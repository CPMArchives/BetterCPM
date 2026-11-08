"""Console guest and formatting support for direct TCAP qualification."""
import hashlib
import os
import pty
import select
import signal
import time
import re
from pathlib import Path
import pyte

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


PRINTER = """HEX:    PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIB
        POP AF
NIB:    AND 15
        ADD A,48
        CP 58
        JR C,CHAR
        ADD A,7
CHAR:   PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL 5
        POP BC
        POP HL
        RET
"""


class Guest:
    def __init__(self,simulator,disks,out):
        self.out=out;self.transcript=bytearray();self.pending=bytearray()
        self.screen=pyte.Screen(80,24);self.stream=pyte.Stream(self.screen)
        self.child,self.terminal=pty.fork()
        if self.child==0:
            os.chdir(out)
            env=dict(os.environ);env.pop('CPMSIM_ROM_START',None)
            env['PATH']=str(simulator.parent/'srctools')+os.pathsep+env.get('PATH','')
            os.execve(str(simulator),[str(simulator),'-z','-s','-d',str(disks)],env)
    def expect(self,wanted,timeout=30,rendered=False):
        deadline=time.monotonic()+timeout
        def found():return wanted.decode() in '\n'.join(self.screen.display) if rendered else wanted in self.pending
        while not found():
            remain=deadline-time.monotonic()
            assert remain>0,('timeout',wanted,bytes(self.transcript[-2000:]))
            if select.select([self.terminal],[],[],remain)[0]:
                data=os.read(self.terminal,65536)
                assert data,('emulator exited',wanted,bytes(self.transcript[-2000:]))
                self.pending.extend(data);self.transcript.extend(data)
                self.stream.feed(data.decode('ascii',errors='replace'))
                (self.out/'transcript.bin').write_bytes(self.transcript)
                assert len(self.pending)<65536,('unbounded output',bytes(self.pending[-2000:]))
        end=len(self.pending) if rendered else self.pending.index(wanted)+len(wanted)
        data=bytes(self.pending[:end]);del self.pending[:end]
        return data
    def command(self,command,wanted=b'A0>_ '):
        os.write(self.terminal,command.encode()+b'\r')
        return self.expect(wanted)
    def prompt(self,command=None,timeout=30):
        """Await the current empty editor row after echoing the sent command.

        The editor redraws the prompt on each keystroke. A raw prompt substring
        alone would therefore return before the command has even executed.
        """
        start=len(self.transcript);deadline=time.monotonic()+timeout
        if command is not None:os.write(self.terminal,command.encode()+b'\r')
        while True:
            data=bytes(self.transcript[start:])
            row=self.screen.display[self.screen.cursor.y].strip()
            echoed=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',data)
            if self.screen.cursor.x==3 and row.startswith('A0>') and (command is None or command.encode() in echoed):
                # A redraw can briefly stop after printing only the prefix.
                # Drain further output before accepting an idle editor.
                if not select.select([self.terminal],[],[],.02)[0]:return data
            remain=deadline-time.monotonic()
            assert remain>0,('prompt timeout',command,data[-2000:],row)
            if select.select([self.terminal],[],[],min(remain,.1))[0]:
                block=os.read(self.terminal,65536);assert block,('emulator exited',command)
                self.transcript.extend(block);self.stream.feed(block.decode('ascii',errors='replace'))
                (self.out/'transcript.bin').write_bytes(self.transcript)
    def close(self):
        # Interrupt the CPU through its host handler. Wake a blocked host read
        # as well; teardown must never wait indefinitely for a console thread.
        try:
            os.kill(self.child,signal.SIGINT);os.write(self.terminal,b'\r')
        except (ProcessLookupError,OSError):pass
        deadline=time.monotonic()+2;sent_term=False
        while True:
            try:pid,status=os.waitpid(self.child,os.WNOHANG)
            except ChildProcessError:break
            if pid:break
            if select.select([self.terminal],[],[],.02)[0]:
                try:data=os.read(self.terminal,65536)
                except OSError:data=b''
                self.transcript.extend(data)
            if time.monotonic()>=deadline:
                try:os.kill(self.child,signal.SIGKILL if sent_term else signal.SIGTERM)
                except ProcessLookupError:pass
                if sent_term:
                    try:os.waitpid(self.child,0)
                    except ChildProcessError:pass
                    break
                sent_term=True;deadline=time.monotonic()+1
        os.close(self.terminal)
        (self.out/'transcript.bin').write_bytes(self.transcript)
        core=self.out/'core.z80'
        if core.exists():
            data=core.read_bytes();assert len(data)>65536
            (self.out/'ram.bin').write_bytes(data[-65536:])
