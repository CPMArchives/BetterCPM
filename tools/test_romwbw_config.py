#!/usr/bin/env python3
"""Exercise shared CONFIG menus and cold-only settings on RomWBW."""
import argparse,hashlib,json,os
from pathlib import Path
from test_romwbw_system import Terminal
from romwbw_media import SIZE,configuration
from startup_record import parse,choices

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('image-dir','simulator','rom','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    image=a.image_dir.resolve();source=out/'source.img';source.write_bytes((image/'system.img').read_bytes())
    target=out/'target.img';target.write_bytes(b'\xe5'*SIZE)
    checks=[];sim=a.simulator.resolve();rom=a.rom.resolve()
    def start(name,boot='2'):
        work=out/name;work.mkdir()
        cmd=[str(sim),'--romwbw='+str(rom),'--disk0='+str(source),'--disk1='+str(target),
             '--boot='+boot,'--no-config','--strict-io','--max-instructions=40000000000']
        return Terminal(sim,work,command=cmd)
    def accept(t,cmd,prompt,marker):
        t.type_command(cmd);t.expect(prompt);os.write(t.master,b'Y');t.expect(marker);t.prompt()
    t=start('edit')
    try:
        t.prompt();t.send('CONFIG /HELP','CONFIG: /SHOW')
        accept(t,'CONFIG /STARTUP="HELLO"','Save pending cold-boot changes on system disk A:',
               'Pending cold-boot changes saved and verified.')
        accept(t,'CONFIG /IOBYTE=85','Save disk-boot IOBYTE', 'Disk-boot IOBYTE saved; live unchanged.')
        t.type_command('CONFIG /SHOW');t.expect('Live IOBYTE [(]decimal[)]: 149')
        t.expect('Saved disk-boot IOBYTE [(]decimal[)]: 85');t.expect('Saved cold-start command: HELLO');t.prompt()
        t.send('CONFIG /LOGICAL=B /UNIT=3 /SAVE','Block configuration saved and verified.')
        # The shared PDS menu edits pending state. It must not move live owners.
        t.type_command('CONFIG');t.expect('Select A/B/C/F/S')
        os.write(t.master,b'F');t.expect('Pending choices H/M/V: 2 0 0')
        os.write(t.master,b'A');t.expect('Pending choices H/M/V: 3 0 0')
        os.write(t.master,b'A');t.expect('Pending choices H/M/V: 0 0 0')
        os.write(t.master,b'B');t.expect('Pending choices H/M/V: 0 1 0')
        os.write(t.master,b'C');t.expect('Active H/M/V bytes: 192 0 0')
        t.expect('Pending choices H/M/V: 0 1 1')
        t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'\x03');t.expect('Select A/B/C/F/S')
        os.write(t.master,b'S');t.expect('Save pending cold-boot changes only')
        t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'A');t.expect('Save pending cold-boot changes on system disk A:')
        os.write(t.master,b'Y');t.expect('Pending cold-boot changes saved and verified.')
        t.expect('Push ENTER for menu.');os.write(t.master,b'\r')
        t.expect('Save pending cold-boot changes only');t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'\x03')
        t.expect('Select A/B/C/F/S');t.expect(r'Your choice: \[ \]\x08\x08');os.write(t.master,b'\x03');t.prompt()
        checks+=['shared HELP/CONFIG menus','startup save through shared BCST/PDS validator',
                 'IOBYTE save leaves live routes unchanged','block save preserves saved IOBYTE',
                 'PDS menu preserves live owners while editing and saves pending choices']
    finally:t.close()
    raw=source.read_bytes();base=json.loads((image/'candidate.json').read_text())['layout']['SYSTEM']
    if raw[128:384]!=raw[32896:33152]:raise AssertionError('BCST mirror differs')
    if parse(raw[128:384],system_base=base)!='HELLO':raise AssertionError('startup differs')
    if choices(raw[128:384],system_base=base)!=(0,1,1):raise AssertionError('PDS choices differ')
    if raw[2048:2560]!=configuration(3,85):raise AssertionError('saved IOBYTE/binding record differs')
    t=start('cold-settings')
    try:
        t.expect('ROMWBW TRANSIENT PASS');t.prompt()
        t.type_command('CONFIG /SHOW');t.expect('Live IOBYTE [(]decimal[)]: 85')
        t.expect('Saved cold-start command: HELLO');t.expect('Saved H/M/V choices: 0 1 1');t.prompt()
        t.type_command('HELLO;HELLO');t.expect('ROMWBW TRANSIENT PASS');t.expect('ROMWBW TRANSIENT PASS');t.prompt()
        t.type_command('SYSGEN B:');t.expect('ROMWBW SYSGEN INSTALL PASS',timeout=1200);t.prompt()
        checks+=['cold boot activates saved startup, IOBYTE and PDS choices',
                 'MCL survives transient execution','SYSgen accepts edited settings and mirrored BCST']
    finally:t.close()
    t=start('installed-settings',boot='3')
    try:
        t.expect('ROMWBW TRANSIENT PASS');t.prompt()
        t.type_command('CONFIG /SHOW');t.expect('Live IOBYTE [(]decimal[)]: 85')
        t.expect('B: unbound');t.expect('Saved H/M/V choices: 0 1 1');t.prompt()
        checks.append('installed disk preserves startup/PDS/IOBYTE and unbinds B')
    finally:t.close()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps({'status':'PASS','checks':checks,
        'system_sha256':sha(image/'system.img'),'rom_sha256':sha(rom),
        'simulator_sha256':sha(sim)},indent=2)+'\n')
    print('PASS:',out/'result.json')

if __name__=='__main__':main()
