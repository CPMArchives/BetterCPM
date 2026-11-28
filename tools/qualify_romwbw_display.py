#!/usr/bin/env python3
"""Run the shared integrated-display lifecycle on private RomWBW media."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import time
import shutil
import subprocess
import sys
import pyte
from build_integrated_display import build
from integrated_display_qualification import collection, audit
from test_romwbw_system import Terminal


class Console(Terminal):
    monitored=False

    def prompt(self, drive='A'):
        if not self.monitored: return super().prompt(drive)
        screen=pyte.Screen(80,24);stream=pyte.Stream(screen);fed=0
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            stream.feed(self.data[fed:].decode('latin1'));fed=len(self.data)
            prefix=screen.display[screen.cursor.y][:screen.cursor.x]
            if prefix in (drive+'0>',drive+'0> '):
                # A redraw briefly emits the prefix before its command text.
                if not select.select([self.master],[],[],.02)[0]:
                    self.cursor=len(self.data);return prefix
            if select.select([self.master],[],[],.1)[0]:
                block=os.read(self.master,65536)
                if not block: raise AssertionError('console closed')
                self.data.extend(block)
        raise AssertionError('display prompt timeout: '+self.data[-2000:].decode('latin1'))



def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('workspace','simulator','rom','output'): p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();workspace=a.workspace.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    image=workspace/'build/romwbw';candidate=json.loads((image/'candidate.json').read_text())
    maximum=candidate['profile']['capacities']['maximum_com_bytes']
    baseline=candidate['layout']['TPA']
    files,budgets,sequence=collection(workspace,out,'romwbw',maximum,('ADM3A','VT52','ANSI'),True)
    env=dict(os.environ,BETTERCPM_BUILD_CONTEXT=str(workspace/'build/profile/context.json'),
             BETTERCPM_IDENTITY_TARGET='romwbw',BETTERCPM_IDENTITY_STATE='development')
    subprocess.run([sys.executable,'-B',str(workspace/'tools/build_hello_rsx.py'),
                    '--assembler',str(Path.home()/'bin/z80asm')],cwd=workspace,env=env,check=True)
    files['HELLO.RSX']=(workspace/'build/rsx/HELLO.RSX').read_bytes()
    # A structurally valid public carrier with this platform's native code
    # must not acquire access to absolute protected BIOS call addresses.
    public=bytearray(files['ANSI.RSX']);public[32:40]=b'PUBANSI '
    offset=int.from_bytes(public[30:32],'little')
    assert public[offset:offset+4]==b'BMET' and public[offset+12:offset+15]==bytes((4,18,1))
    public[offset+15]=0;public[offset+16:offset+32]=bytes(16)
    files['PUBANSI.RSX']=bytes(public)
    disk=out/'system.img';shutil.copy2(image/'system.img',disk);shutil.copy2(image/'diskdefs',out/'diskdefs')
    for name,data in files.items():
        (out/name).write_bytes(data)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-romwbw',str(disk),'0:'+name],cwd=out,capture_output=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(disk),str(out/name),'0:'+name],cwd=out,check=True)
    from romwbw_media import SIZE
    wrong=out/'wrong-platform.img';wrong.write_bytes(b'\xe5'*SIZE)
    foreign,foreign_report=build(workspace,out/'foreign','cpmsim','ANSI',inline_cache=True)
    assert foreign_report['compatibility_id']==budgets['ANSI']['compatibility_id']
    (out/'foreign/ANSI.RSX').write_bytes(foreign)
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(wrong),str(out/'foreign/ANSI.RSX'),'0:ANSI.RSX'],cwd=out,check=True)
    report={'status':'RUNNING','platform':'romwbw','service':'TCAP 2.0','budgets':budgets,
            'system_sha256':hashlib.sha256((image/'system.img').read_bytes()).hexdigest(),
            'checks':[]}
    def save(): (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    command=[str(a.simulator.resolve()),'--romwbw='+str(a.rom.resolve()),'--disk0='+str(disk),
             '--disk1='+str(wrong),'--boot=2','--no-config','--strict-io','--escape=none',
             '--max-instructions=40000000000']
    t=Console(a.simulator.resolve(),out,command=command)
    frames=[];records=[];screen=pyte.Screen(80,24);stream=pyte.Stream(screen);fed=0
    try:
        t.prompt()
        t.send('CONFIG /LOGICAL=B /UNIT=3','B: binding updated.')
        t.send('RSX LOAD B:ANSI','RSX module or profile error')
        report['checks'].append('same-private-binding cpmsim transport refused by platform bit')
        t.send('RSX LOAD PUBANSI','RSX module or profile error')
        report['checks'].append('public native carrier refused despite correct platform capability')
        active=None
        for cmd in sequence:
            if cmd.startswith('RSX LOAD ') and cmd.split()[-1] in budgets:
                active=cmd.split()[-1];t.monitored=True
            if cmd.startswith('RSX UNLOAD ') and cmd.split()[-1] in budgets: t.monitored=False
            before=len(t.data)
            if cmd.startswith('DEMO '):
                t.type_command(cmd);t.expect('INTEGRATED READY '+cmd[-1])
                stream.feed(t.data[fed:].decode('latin1'));fed=len(t.data)
                cells=[screen.buffer[4][col] for col in range(9,18)]
                assert ''.join(c.data for c in cells)=='TCAP TEXT',(active,cells)
                assert all(c.reverse==(active!='VT52') for c in cells),(active,cells)
                os.write(t.master,cmd[-1].encode());t.expect('INTEGRATED DEMO PASS');t.prompt()
            else: t.send(cmd)
            text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',t.data[before:].decode('latin1'))
            frames.append(text);records.append(cmd)
            print('PASS',cmd,flush=True)
            if cmd.startswith('RSX UNLOAD ') and cmd.split()[-1] in budgets: active=None
        audit(sequence,frames,budgets,baseline)
        report['checks'].append('all three shared lifecycle sequences, exact bounds, relocation and unload')
        for personality in budgets:
            t.monitored=True;t.send('RSX LOAD '+personality)
            t.type_command('HELP PIP');t.expect('Q Exit')
            os.write(t.master,b'Q');t.prompt()
            t.monitored=False;t.send('RSX UNLOAD '+personality)
        t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        report['checks']+=['HELP PIP through each personality','default 56 KiB COM capacity restored']
        report.update(status='PASS',commands=records,permanent_memory_loss_bytes=0)
    except Exception as error:
        report.update(status='FAIL',error=str(error));raise
    finally:
        t.close();report['transcript_sha256']=hashlib.sha256(t.data).hexdigest();save()
    print('PASS:',out/'result.json')


if __name__=='__main__': main()
