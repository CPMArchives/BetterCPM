#!/usr/bin/env python3
"""Automate two-disk configuration, persistence and installation acceptance."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from romwbw_media import SIZE,configuration
from test_romwbw_system import Terminal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('image-dir','simulator','rom','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/'source.img';target=out/'target.img'
    image=a.image_dir.resolve();source.write_bytes((image/'system.img').read_bytes())
    target.write_bytes(b'\xe5'*SIZE);shutil.copy2(image/'diskdefs',out/'diskdefs')
    simulator,rom=a.simulator.resolve(),a.rom.resolve();checks=[]
    def terminal(name,boot='2',disk=source,second=target):
        work=out/name;work.mkdir()
        command=[str(simulator),'--romwbw='+str(rom),'--disk0='+str(disk),
                 '--boot='+boot,'--no-config','--strict-io','--max-instructions=4000000000']
        if second is not None:command+=['--disk1='+str(second)]
        return Terminal(simulator,work,command=command)
    t=terminal('install')
    try:
        t.prompt()
        t.send('CONFIG /SHOW','B: unbound')
        t.send('CONFIG /LOGICAL=B /UNIT=2','CONFIG failed')
        t.send('CONFIG /SHOW','B: unbound')
        t.send('CONFIG /LOGICAL=B /UNIT=3 /SAVE','Block configuration saved and verified.')
        t.send('CONFIG /SHOW','B: HBIOS unit 3')
        t.send('CONFIG /LOGICAL=B /UNIT=0','CONFIG failed')
        t.send('CONFIG /SHOW','B: HBIOS unit 3')
        t.type_command('SYSGEN B:');t.expect('ROMWBW SYSGEN INSTALL PASS',timeout=60);t.prompt()
        checks+=['protected A alias rejected without changing B','B mapped to HBIOS unit 3',
                 'configuration saved and read-back verified','empty B installed and sector/file verified']
    finally:t.close()
    if source.read_bytes()[2048:2560]!=configuration(3):raise AssertionError('saved block record differs')
    installed=target.read_bytes()
    t=terminal('repeat-refusal')
    try:
        t.prompt();t.send('CONFIG /SHOW','B: HBIOS unit 3')
        t.send('SYSGEN B:','SYSGEN refused: destination B: is not empty.')
        checks+=['saved B restored after cold boot','nonempty destination refused']
    finally:t.close()
    if target.read_bytes()!=installed:raise AssertionError('refused installation changed destination')
    candidate=json.loads((image/'candidate.json').read_text())
    exported=out/'extracted';exported.mkdir()
    for name,entry in candidate['files'].items():
        if name in ('AFILE.COM','ATPA.COM','AIOTEST.COM','AFAILIO.COM'):continue
        path=exported/name
        subprocess.run(['cpmcp','-f','bettercpm-romwbw',str(target),'0:'+name,str(path)],cwd=out,check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['cpm_sha256']:
            raise AssertionError('installed file differs: '+name)
    checks.append('independent host extraction matches every installed file')
    t=terminal('destination-boot',boot='3')
    try:
        t.prompt();t.send('CONFIG /SHOW','A: HBIOS unit 3')
        t.send('CONFIG /SHOW','B: unbound')
        t.send('HELLO','ROMWBW TRANSIENT PASS')
        t.send('RSX LOAD ECHO');t.send('AECHO','Hello from ECHO.RSX')
        t.send('RSX UNLOAD ECHO');t.send('RSX LIST','TPA available: 56K')
        checks+=['cold boot from installed destination','boot unit rediscovered as A',
                 'installed transient and RSX lifecycle pass with 56 KiB unloaded TPA']
    finally:t.close()
    t=terminal('absent-saved-device',second=None)
    try:
        t.prompt();t.send('CONFIG /SHOW','B: unbound')
        checks.append('unavailable saved B does not prevent A boot')
    finally:t.close()
    pristine=(image/'system.img').read_bytes()
    for label,damage in [('source-kernel',60000),('source-file',None)]:
        broken=out/(label+'.img');data=bytearray(pristine)
        if damage is None:
            for at in range(131072,131072+16384,32):
                entry=data[at:at+32]
                if entry[0]==0 and entry[1:12]==b'README  TXT':
                    damage=131072+struct.unpack_from('<H',entry,16)[0]*4096
                    break
            if damage is None:raise AssertionError('README not found in source image')
        data[damage]^=1;broken.write_bytes(data)
        blank=out/(label+'-target.img');blank.write_bytes(b'\xe5'*SIZE)
        before=blank.read_bytes();t=terminal(label,disk=broken,second=blank)
        try:
            t.prompt();t.send('CONFIG /LOGICAL=B /UNIT=3','B: binding updated.')
            t.send('SYSGEN B:','SYSGEN failed; destination is not an installed system.')
            checks.append(label+' corruption rejected before target writes')
        finally:t.close()
        if blank.read_bytes()!=before:raise AssertionError(label+' preflight changed target')
    occupied=out/'other-user.img';occupied.write_bytes(b'\xe5'*SIZE)
    keep=out/'keep.txt';keep.write_bytes(b'Keep this user-seven file.\r\n')
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(occupied),str(keep),'7:KEEP.TXT'],cwd=out,check=True)
    before=occupied.read_bytes();t=terminal('other-user-refusal',second=occupied)
    try:
        t.prompt();t.send('CONFIG /LOGICAL=B /UNIT=3','B: binding updated.')
        t.send('SYSGEN B:','SYSGEN refused: destination B: is not empty.')
        checks.append('nonzero-user files also protect destination from installation')
    finally:t.close()
    if occupied.read_bytes()!=before:raise AssertionError('nonzero-user data changed')
    bad=out/'invalid-config.img';data=bytearray(pristine);data[2048+100]^=1;bad.write_bytes(data)
    t=terminal('invalid-saved-config',disk=bad)
    try:
        t.expect(r'entry @ 0x1000\]\.\.\.!')
        if b'A0>' in t.data:raise AssertionError('bad configuration reached OS')
        checks.append('corrupt saved configuration rejected before OS entry')
    finally:t.close()
    faulty=out/'io-fault.img';faulty.write_bytes(pristine)
    t=terminal('injected-io-error',disk=faulty,second=None)
    try:
        t.prompt();t.type_command('AFAILIO');t.expect('ROMWBW IO FAULT READY')
        with faulty.open('r+b') as f:f.truncate(2048)
        os.write(t.master,b'X')
        t.expect('ROMWBW IO FAULT PASS')
        checks.append('HBIOS read failure preserves DMA; failed write pre-read propagates error')
    finally:t.close()
    t=terminal('unbind-and-save')
    try:
        t.prompt();t.send('CONFIG /LOGICAL=B /UNBIND /SAVE','Block configuration saved and verified.')
    finally:t.close()
    if source.read_bytes()[2048:2560]!=configuration():raise AssertionError('unbound map not saved')
    t=terminal('unbound-cold-boot')
    try:
        t.prompt();t.send('CONFIG /SHOW','B: unbound')
        checks.append('explicit unbind persists across cold boot')
    finally:t.close()
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps({'status':'PASS','checks':checks,
        'source_image_sha256':sha(image/'system.img'),'rom_sha256':sha(rom),
        'simulator_sha256':sha(simulator),'installed_image_sha256':sha(target)},indent=2)+'\n')
    print('PASS:',out/'result.json')

if __name__=='__main__':main()
