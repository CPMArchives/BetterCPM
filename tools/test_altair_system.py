#!/usr/bin/env python3
"""Exercise a private Altair OS candidate through the serial console and cpmtools."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import subprocess
import time


class Terminal:
    def __init__(self, simulator, work):
        self.master, slave = pty.openpty()
        self.command = [str(simulator),'-z','-R','-M1','-f0','-c',str(work/'system.conf'),'-d',str(work/'disks')]
        self.process = subprocess.Popen(self.command,cwd=work,stdin=slave,stdout=slave,stderr=slave)
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
        # Submitted commands also print "A0> command". Wait for the editable
        # cursor, otherwise early host input can race cold STARTUP processing.
        escape=r'(?:\x1b\[[0-9;?]*[A-Za-z])*'
        cursor=r'(?:_|\x1b\[7m'+escape+' | '+escape+' )'
        return self.expect(r'(?:\r|\n|\x1b\[[0-9]+;1H)'+escape+drive+escape+'0'+escape+'>'+escape+' '+escape+cursor)

    def send(self, command, marker=None, drive='A'):
        self.cursor = len(self.data)
        os.write(self.master, command.encode('ascii')+b'\r')
        if marker:
            self.expect(re.escape(marker))
        self.prompt(drive)

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        os.close(self.master)
        (self.work/'transcript.txt').write_bytes(self.data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    image, out = a.image_dir.resolve(), a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(image/'disks',out/'disks')
    for name in ('diskdefs','system.conf'):
        shutil.copy2(image/name,out/name)
    before = (out/'disks/drivea.dsk').read_bytes()
    candidate = json.loads((image/'candidate.json').read_text())
    terminal = Terminal(a.simulator.resolve(),out)
    try:
        terminal.prompt()
        terminal.send('VER', 'BetterCP/M')
        terminal.send('DIR', 'RCP')
        terminal.send('STAT MEM', 'Maximum loadable COM: 57344 bytes')
        terminal.send('AAPI', 'ALTAIR GEOMETRY API PASS')
        terminal.send('AFILE', 'ALTAIR BDOS FILE IO PASS')
        terminal.send('ATPA', 'ALTAIR 56K TPA OVERWRITE PASS')
        terminal.send('VER', 'BetterCP/M')
        terminal.send('RSX LOAD ECHO')
        terminal.send('RSX LIST', 'ECHO : BDOS 199')
        terminal.send('AECHO', 'Hello from ECHO.RSX')
        terminal.send('RSX UNLOAD ECHO')
        terminal.send('RSX LIST', 'TPA available: 56K')
        terminal.send('B:', drive='B')
        terminal.send('\x03', drive='B')
        terminal.send('A:')
        terminal.send('VER', 'BetterCP/M')
        terminal.cursor = len(terminal.data)
        os.write(terminal.master,b'BYE\r')
        terminal.expect('System halted')
        terminal.process.wait(timeout=5)
        if terminal.process.returncode:
            raise AssertionError('nonzero emulator exit')
    finally:
        terminal.close()
    text = terminal.data.decode('latin1')
    if 'FAIL' in text or 'CPX?' in text:
        raise AssertionError('guest reported a failure')
    # The common RSX manager creates and deletes its scratch file on A.
    # Deleted directory slots/free allocation blocks may retain those bytes.
    # Require identical active files and reserved tracks instead of declaring
    # legitimate scratch-file cleanup to be controller corruption.
    after = (out/'disks/drivea.dsk').read_bytes()
    if after[:8*26*128] != before[:8*26*128]:
        raise AssertionError('system tracks changed')
    def listing(folder):
        return subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-altair',str(folder/'disks/drivea.dsk')],cwd=out,text=True)
    original_listing = listing(image)
    if listing(out) != original_listing:
        raise AssertionError('active A filesystem membership changed')
    system_files = []
    for name in original_listing.splitlines():
        if '.' not in name:
            continue
        paths = []
        for label,folder in [('before',image),('after',out)]:
            target = out/(label+'-'+name)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-altair',str(folder/'disks/drivea.dsk'),
                            '0:'+name,str(target)],cwd=out,check=True)
            paths.append(target)
        if paths[0].read_bytes() != paths[1].read_bytes():
            raise AssertionError('active system file changed: '+name)
        if hashlib.sha256(paths[1].read_bytes()).hexdigest() != candidate['files'][name.upper()]['cpm_sha256']:
            raise AssertionError('filesystem extraction differs from assembled artifact: '+name)
        system_files.append({'name':name,'sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest()})
    expected = bytes(record ^ column for record in range(140) for column in range(128,0,-1))
    results = []
    for drive in 'bcd':
        path = out/(drive+'-ALTAIR.DAT')
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-altair',str(out/f'disks/drive{drive}.dsk'),
                        '0:ALTAIR.DAT',str(path)],cwd=out,check=True)
        if path.read_bytes() != expected:
            raise AssertionError('host extraction differs from expected 140-record data on '+drive)
        results.append({'drive':drive,'records':140,'bytes':len(expected),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    guard_results = []
    for name,offset in [('stage1-corruption',60*128+200),
                        ('stage2-corruption',84*128+200),
                        ('foreign-stage1-identity',60*128+1000)]:
        work = out/name
        work.mkdir()
        shutil.copytree(image/'disks',work/'disks')
        shutil.copy2(image/'system.conf',work/'system.conf')
        path = work/'disks/drivea.dsk'
        damaged = bytearray(path.read_bytes())
        damaged[offset] ^= 1
        path.write_bytes(damaged)
        guest = Terminal(a.simulator.resolve(),work)
        try:
            guest.expect('!')
            guest.process.wait(timeout=5)
        finally:
            guest.close()
        if b'\nA0> ' in guest.data:
            raise AssertionError(name+': corrupted carrier reached the CCP')
        if path.read_bytes() != damaged:
            raise AssertionError(name+': failed admission modified system media')
        guard_results.append({'case':name,'entered_ccp':False,'status':'PASS'})
    report = {'status':'PASS','scope':'bounded OS integration, not release qualification',
              'command':terminal.command,'candidate':candidate,
              'emulator_sha256':hashlib.sha256(a.simulator.read_bytes()).hexdigest(),
              'checks':['cold boot','shared version/directory commands','STAT MEM',
                        'B-D create/write/close/reopen/read/EOF across file extents',
                        'independent cpmtools extraction','56K TPA overwrite and warm boot',
                        'ECHO RSX load/call/unload','56K after RSX unload',
                        'warm boot preserves drive B','geometry discovery and unsupported setter refusal',
                        'system tracks and active system files unchanged'],
              'files':results,'system_files':system_files,'guard_cases':guard_results,
              'transcript_sha256':hashlib.sha256(terminal.data).hexdigest(),
              'images':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'disks').iterdir())}}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Altair cold/warm boot, 56K TPA, multi-extent B-D file I/O, RSX lifecycle')


if __name__ == '__main__':
    main()
