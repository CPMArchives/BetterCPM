#!/usr/bin/env python3
"""Require native ZSM4/LINK parity for portable VT52 and both screen backends."""
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from build_native_trs80 import blank, run
from test_vt52_foundation import symbols

ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path.home()/'projects/git/cpm-compatibility/suite/build-tools'
SIM=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
SYSTEM=SIM.parent/'disks/library/cpm22-62khd.dsk'
TEMPLATE=TOOLS.parent/'disk-images/z80pack/ibm-3740/drivea.dsk'


def main():
    os.environ['PATH']=str(SIM.parent/'srctools')+os.pathsep+os.environ.get('PATH','')
    out=ROOT/'build/vt52-development/native';out.mkdir(parents=True,exist_ok=True)
    bios=symbols(ROOT/'build/bios/bios.lst')
    bindings='\n'.join(f'{name} EQU 0{bios[name]:04X}H' for name in ['M4CURSOR','M4COLUMN'])
    results=[]
    for stem,source,reference in [
        ('VT52','src/rsx/vt52.mac','build/vt52-development/vt52.bin'),
        ('ADM3A','src/rsx/adm3a.mac','build/monitor-development/adm3a.bin'),
        ('M4SCRN','src/rsx/screen/model4.mac','build/screen-backends/M4SCRN.bin'),
        ('ANSISCRN','src/rsx/screen/ansi-host.mac','build/screen-backends/ANSISCRN.bin'),
        ('R3KPRE','src/system/r3kpre.mac','build/system/r3kpre.bin'),
        ('R3FINAL','src/system/r3final.mac','build/system/r3final.bin'),
        ('R3SCHED','src/system/rsxsched.mac','build/system/r3sched.bin')]:
        work=Path(tempfile.mkdtemp(prefix=stem+'-',dir=out));disks=work/'disks';disks.mkdir()
        shutil.copy2(SYSTEM,disks/'drivea.dsk')
        for drive in 'bcd':blank(TEMPLATE,disks/f'drive{drive}.dsk')
        text=(ROOT/source).read_text().replace('        INCLUDE backend.inc',bindings)
        if stem.startswith('R3'):
            from build_rsx_runtime_overlays import source as overlay_source
            from system_layout import LAYOUT
            symbol,address={'R3KPRE':('KPBASE',LAYOUT['RSX']),
                'R3FINAL':('RFBASE',LAYOUT['RSX']),
                'R3SCHED':('RSBASE',LAYOUT['CONFIG']+0x120)}[stem]
            text=overlay_source(Path(source).name,symbol,address)
            # z80asm fills DS with FF, native ZSM4/LINK with zero. Make the
            # cross-assembler's padding explicit for byte-parity comparison.
            text=re.sub(r'\bDS\s+(\d+)',lambda m:'DB '+','.join(['0FFH']*int(m[1])),text)
        if '        ASEG' in text:
            text,count=re.subn(r'        ASEG\n        ORG\s+([^\n]+)',r'        CSEG\n        .PHASE \1',text,count=1)
            assert count==1
            text=re.sub(r'^\s*END\s*$', '        .DEPHASE\n        END',text,count=1,flags=re.M)
        unit=work/'UNIT.MAC';unit.write_bytes((text.rstrip()+'\n').replace('\n','\r\n').encode('ascii')+b'\x1a')
        run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(unit),'0:UNIT.MAC')
        for tool in ['ZSM4.COM','LINK.COM']:
            run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(TOOLS/tool),'0:'+tool)
        commands=rf'''set timeout 30
spawn {SIM} -z -d {disks}
send -- "\r"
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:UNIT=C:UNIT\r"
expect -re {{Errors: +[0-9]+}}
expect "B>"
send -- "D:LINK UNIT\[A\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
        result=run('expect','-c',commands,check=False)
        transcript=result.stdout+result.stderr;(work/'transcript.txt').write_text(transcript)
        assert result.returncode==0 and re.search(r'Errors: +0',transcript),transcript
        linked=work/'UNIT.COM';run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:UNIT.COM',str(linked))
        expected=(ROOT/reference).read_bytes()
        assert linked.read_bytes()[:len(expected)]==expected,(stem,'native/cross mismatch',work)
        results.append(dict(name=stem,bytes=len(expected),parity=True,evidence=str(work)))
        print(f'PASS {stem}: {len(expected)} native/cross identical bytes',flush=True)
    (out/'parity.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
