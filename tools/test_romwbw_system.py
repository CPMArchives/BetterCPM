#!/usr/bin/env python3
"""Prompt-paced RomWBW engineering acceptance; always tests private image copies."""
import argparse, hashlib, json, os, pty, re, select, shutil, subprocess, time
from pathlib import Path

class Terminal:
    def __init__(self, simulator, work, *, command=None, cwd=None):
        self.master, slave = pty.openpty()
        self.command = command or [str(simulator),'-z','-R','-M1','-f0','-r',str(simulator.parent/'roms'),'-c',str(work/'system.conf'),'-d',str(work/'disks')]
        environment = dict(os.environ, XDG_CONFIG_HOME=str(work/'config'))
        self.process = subprocess.Popen(self.command,cwd=cwd or work,stdin=slave,stdout=slave,stderr=slave,env=environment)
        os.close(slave)
        self.data = bytearray()
        self.cursor = 0
        self.work = work

    def expect(self, pattern, timeout=20):
        deadline = time.monotonic()+timeout
        while time.monotonic()<deadline:
            text = self.data.decode('latin1')
            match = re.search(pattern,text[self.cursor:])
            if match:
                self.cursor += match.end()
                return match.group()
            tail=text[self.cursor:]
            if '\x1b[' in tail:
                # Integrated host renderers position each glyph. Match their
                # textual content while retaining the raw transcript cursor.
                cleaned=[];positions=[];previous=0
                for escape in re.finditer(r'\x1b\[[0-9;?]*[A-Za-z]',tail):
                    for index in range(previous,escape.start()):
                        cleaned.append(tail[index]);positions.append(index+1)
                    previous=escape.end()
                for index in range(previous,len(tail)):
                    cleaned.append(tail[index]);positions.append(index+1)
                match=re.search(pattern,''.join(cleaned))
                if match:
                    self.cursor += positions[match.end()-1]
                    return match.group()
            if self.process.poll() is not None:
                raise AssertionError('emulator exited before '+pattern+'\n'+text[-2000:])
            if select.select([self.master],[],[],0.1)[0]:
                try:
                    chunk = os.read(self.master,65536)
                except OSError:
                    chunk = b''
                if not chunk:
                    raise AssertionError('console closed before '+pattern+'\n'+text[-2000:])
                self.data.extend(chunk)
        raise AssertionError('timeout waiting for '+pattern+'\n'+self.data.decode('latin1')[-2500:])

    def prompt(self, drive='A'):
        return self.expect(re.escape(drive)+'0> (?:'+re.escape(drive)+'0> )?_')

    def send(self, command, marker=None, drive='A'):
        self.type_command(command)
        if marker:
            self.expect(re.escape(marker))
        self.prompt(drive)

    def type_command(self, command):
        """Wait for each editor echo before queuing the next character.

        This respects the timed UART and finite CP/M typeahead buffer without
        guessing a fixed delay for progressively longer prompt redraws.
        """
        self.cursor = len(self.data)
        prefix = ''
        for byte in command.encode('ascii'):
            os.write(self.master, bytes([byte]))
            if 32 <= byte < 127:
                prefix += chr(byte)
                self.expect(re.escape(prefix))
            else:
                prefix = ''
        os.write(self.master,b'\r')

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        os.close(self.master)
        (self.work/'transcript.txt').write_bytes(self.data)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--simulator', type=Path, required=True)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    source,out=a.image_dir.resolve(),a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(source/'system.img',out/'system.img')
    shutil.copy2(source/'diskdefs',out/'diskdefs')
    simulator,rom=a.simulator.resolve(),a.rom.resolve()
    command=[str(simulator),'--romwbw='+str(rom),'--disk0='+str(out/'system.img'),
             '--boot=2','--no-config','--strict-io','--max-instructions=2000000000']
    results=[]
    t=Terminal(simulator,out,command=command)
    try:
        t.prompt()
        if b'Invalid PDS' in t.data:raise AssertionError('saved configuration was rejected')
        for cmd,marker in [('DIR','RCP'),('HELLO','ROMWBW TRANSIENT PASS'),
                ('AFILE','ROMWBW BDOS FILE IO PASS'),
                ('AIOTEST','ROMWBW BIOS BOUNDARIES PASS'),
                ('ATPA','ROMWBW 56K TPA OVERWRITE PASS'),
                ('RSX LOAD ECHO',None),('RSX LIST','ECHO : BDOS 199'),
                ('AECHO','Hello from ECHO.RSX'),('\x03',None),
                ('AECHO','Hello from ECHO.RSX'),('RSX UNLOAD ECHO',None),
                ('RSX LIST','TPA available: 56K')]:
            t.send(cmd,marker);results.append(cmd if cmd!='\x03' else 'warm boot')
    finally:
        t.close()
    # An independent host reader checks every generated record, not just DIR.
    subprocess.run(['cpmcp','-f','bettercpm-romwbw',str(out/'system.img'),
                    '0:ROMWBW.DAT',str(out/'guest.dat')],cwd=out,check=True)
    data=(out/'guest.dat').read_bytes()
    expected=bytes((record ^ (128-offset)) for record in range(140) for offset in range(128))
    if data!=expected:raise AssertionError('host/guest file contents differ')
    results.append('host extraction: 140 patterned records')
    before=(out/'system.img').read_bytes()
    original=(source/'system.img').read_bytes()
    if before[:131072]!=original[:131072]:raise AssertionError('guest changed reserved system area')
    (out/'transcript.txt').rename(out/'session-1.txt')
    t=Terminal(simulator,out,command=command)
    try:
        t.prompt();t.send('DIR ROMWBW.DAT','ROMWBW');t.send('HELLO','ROMWBW TRANSIENT PASS')
        results.append('cold restart: file persistence and transient execution')
    finally:
        t.close()
    (out/'transcript.txt').rename(out/'session-2.txt')
    # The bootstrap must reject a different capacity before loading the OS.
    wrong=out/'wrong-size.img';wrong.write_bytes(original[:8388608])
    wrong_command=[arg.replace(str(out/'system.img'),str(wrong)) for arg in command]
    t=Terminal(simulator,out,command=wrong_command)
    try:
        t.expect(r'entry @ 0x1000\]\.\.\.!')
        if b'A0>' in t.data:raise AssertionError('wrong geometry reached the OS')
        results.append('bootstrap rejects wrong physical capacity')
    finally:
        t.close()
    (out/'transcript.txt').rename(out/'rejected-geometry.txt')
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps({'status':'PASS','scope':'initial emulator engineering acceptance',
        'checks':results,'rom_sha256':sha(rom),'simulator_sha256':sha(simulator),
        'source_image_sha256':sha(source/'system.img'),'guest_file_sha256':sha(out/'guest.dat')},indent=2)+'\n')
    print('PASS:',out/'result.json')

if __name__=='__main__':main()
