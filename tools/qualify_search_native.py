#!/usr/bin/env python3
"""Measure SEARCH directory timings and stack watermarks on disposable CP/M media.

Instrumented launcher restores the exact SEARCH entry bytes before calling it.
It only fills the existing stack/guard and observes them after normal return.
Timings are host emulator elapsed times, never physical-machine benchmarks.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from build_ccp import assemble
from build_native_search import DEFAULT_CPMSIM, DEFAULT_SYSTEM, DEFAULT_TEMPLATE
from build_native_trs80 import blank
from search_source import ROOT


def probe(image, listing, work, tpa_bytes=None):
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    guard, top = addr('DGUARD'), addr('DSTACK')
    # SEARCH begins with a three-byte JP. Preserve the entire original image;
    # patch only that entry during loader startup, then restore it before CALL.
    assert image[0] == 0xC3
    source = '        ORG 0100H\n        JP LOAD\n'
    for start in range(3,len(image),16):
        source += '        DB '+','.join(f'0{x:02X}H' for x in image[start:start+16])+'\n'
    fence_setup = fence_restore = ''
    if tpa_bytes is not None:
        boundary = 0x100+tpa_bytes
        if tpa_bytes < len(image)+2 or boundary+3 >= 0x8000:
            raise ValueError('TPA fence must fit image plus return and remain below resident observer')
        source += f'        DS {0x8000-0x100-len(image)}\n'
        fence_setup = f'''
        LD HL,(6)
        LD (OLDBDOS),HL
        LD ({boundary+1}),HL
        LD A,0C3H
        LD ({boundary}),A
        LD HL,{boundary}
        LD (6),HL
'''
        fence_restore = '''
        LD SP,PSTACK
        LD HL,(OLDBDOS)
        LD (6),HL
'''
    source += f'''
LOAD:
        LD (OLDSP),SP
        LD HL,{guard}
        LD BC,{top-guard}
FILL:
        LD (HL),05AH
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,FILL
        LD A,0{image[0]:02X}H
        LD (0100H),A
        LD HL,0{int.from_bytes(image[1:3],'little'):04X}H
        LD (0101H),HL
{fence_setup}
        LD SP,{boundary if tpa_bytes is not None else 'PSTACK'}
        CALL 0100H
{fence_restore}
        LD HL,{guard}
        LD B,16
CHECK:
        LD A,(HL)
        CP 05AH
        JP NZ,BAD
        INC HL
        DJNZ CHECK
        LD BC,512
FIND:
        LD A,(HL)
        CP 05AH
        JR NZ,FOUND
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,FIND
FOUND:
        LD (USED),BC
        LD DE,MSG
        LD C,9
        CALL 5
        LD HL,(USED)
        LD A,H
        CALL HEX
        LD HL,(USED)
        LD A,L
        CALL HEX
        LD DE,OK
        JR FINISH
BAD:
        LD DE,FAIL
FINISH:
        LD C,9
        CALL 5
        LD SP,(OLDSP)
        RET
HEX:
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIBBLE
        POP AF
NIBBLE:
        AND 15
        ADD A,48
        CP 58
        JR C,DIGIT
        ADD A,7
DIGIT:
        LD E,A
        LD C,2
        JP 5
MSG: DB 13,10,'PROBE STACK USED HEX: $'
OK: DB ' GUARD OK',13,10,'$'
FAIL: DB 13,10,'PROBE GUARD FAILED',13,10,'$'
OLDSP: DW 0
OLDBDOS: DW 0
USED: DW 0
        DS 256
PSTACK:
        END
'''
    return assemble(Path.home()/'bin/z80asm',source,work/'probe.com',work/'probe.lst',0x100)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--cpmsim',type=Path,default=DEFAULT_CPMSIM)
    parser.add_argument('--mhz',type=int,default=4,help='Emulated CPU frequency; elapsed time includes host overhead')
    parser.add_argument('--tpa-bytes',type=int,default=8192,help='Lower advertised TPA using a resident BDOS relay and low caller SP')
    args = parser.parse_args()
    out = args.report.resolve()
    out.mkdir(parents=True,exist_ok=False)
    image = (ROOT/'build/utilities/SEARCH.COM').read_bytes()
    listing = (ROOT/'build/utilities/search.lst').read_text()
    instrumented = probe(image,listing,out,args.tpa_bytes)
    env = dict(os.environ)
    env['PATH'] = str(args.cpmsim.parent/'srctools')+os.pathsep+env['PATH']
    def run(*command):
        return subprocess.run(list(map(str,command)),env=env,check=True,capture_output=True,text=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='search-native-qualification-') as tmp:
        work = Path(tmp)
        disks = work/'disks'
        disks.mkdir()
        shutil.copy2(DEFAULT_SYSTEM,disks/'drivea.dsk')
        blank(DEFAULT_TEMPLATE,disks/'driveb.dsk')
        for name,content in [('SEARCH.COM',image),('PROBE.COM',instrumented)]:
            file = work/name
            file.write_bytes(content)
            run('cpmcp','-f','ibm-3740',disks/'drivea.dsk',file,'0:'+name)
        fixture = work/'FIX.TXT'
        fixture.write_bytes(b'X\r\n'*40+b'\x1a'*8)
        for count in (8,32,64):
            blank(DEFAULT_TEMPLATE,disks/'driveb.dsk')
            for i in range(count):
                run('cpmcp','-f','ibm-3740',disks/'driveb.dsk',fixture,f'0:F{i:07}.TXT')
            before = (disks/'driveb.dsk').read_bytes()
            extra = ''
            if count == 64:
                for tail in ('/HELP','/VER','bad-command','"58" B0:F0000000.TXT /NOTEXT',
                             '"x" B0:F0000000.TXT /NOHEX /NOCASE'):
                    escaped = tail.replace('"','\\"')
                    extra += f'''send -- "PROBE {escaped}\\r"
expect -re {{PROBE STACK USED HEX: ([0-9A-F]+) GUARD OK}}
puts "STACK_HEX=$expect_out(1,string)"
expect "A>"
'''
            commands = f'''set timeout 60
spawn {args.cpmsim} -z -f {args.mhz} -d {disks}
expect_before timeout {{exit 2}}
expect "A>"
set begin [clock milliseconds]
send -- "SEARCH \\\"Z\\\" B0:*.TXT /NOHEX\\r"
expect "Files searched: {count}"
expect "Total matches: 0"
expect "A>"
puts "ELAPSED_MS=[expr {{[clock milliseconds]-$begin}}]"
send -- "PROBE \\\"X\\\" B0:F0000000.TXT /NOHEX /P\\r"
expect "Space/Enter:"
send -- "\\003"
expect "Total matches: 40"
expect -re {{PROBE STACK USED HEX: ([0-9A-F]+) GUARD OK}}
puts "STACK_HEX=$expect_out(1,string)"
expect "A>"
{extra}
send -- "\\034"
expect eof
'''
            result = run('expect','-c',commands)
            text = result.stdout+result.stderr
            (out/f'directory-{count}.txt').write_text(text)
            assert 'Search incomplete' not in text and (disks/'driveb.dsk').read_bytes() == before
            elapsed = int(re.search(r'ELAPSED_MS=(\d+)',text)[1])
            stack = max(int(item,16) for item in re.findall(r'STACK_HEX=([0-9A-F]+)',text))
            results.append({'directory_entries':count,'elapsed_ms':elapsed,'stack_watermark_bytes':stack,'data_disk_unchanged':True})
            print(results[-1],flush=True)
        # Invalid allocation points beyond this physical image. Exercise the
        # real BIOS/BDOS error interaction, rather than an adapter return code.
        damaged = bytearray((disks/'driveb.dsk').read_bytes())
        marker = b'F0000000TXT'
        position = damaged.index(marker)-1
        assert damaged[position] == 0 and damaged[position+15] != 0
        damaged[position+16] = 255
        (disks/'driveb.dsk').write_bytes(damaged)
        commands = f'''set timeout 15
spawn {args.cpmsim} -z -d {disks}
expect_before timeout {{exit 2}}
expect "A>"
send -- "SEARCH \\\"X\\\" B0:F0000000.TXT /NOHEX\\r"
expect "Bad Sector"
send -- "\\003"
expect "A>"
send -- "\\034"
expect eof
'''
        result = run('expect','-c',commands)
        fault_text = result.stdout+result.stderr
        (out/'bad-sector.txt').write_text(fault_text)
        assert 'Bad Sector' in fault_text and 'Total matches:' not in fault_text
        assert (disks/'driveb.dsk').read_bytes() == damaged
    evidence = {'sha256':hashlib.sha256(image).hexdigest(),'platform':'stock CP/M 2.2 cpmsim', 'configured_mhz':args.mhz,
                'system_input_sha256':hashlib.sha256(DEFAULT_SYSTEM.read_bytes()).hexdigest(),
                'emulator_sha256':hashlib.sha256(args.cpmsim.read_bytes()).hexdigest(),
                'probe_sha256':hashlib.sha256(instrumented).hexdigest(),
                'advertised_tpa_payload_bytes':args.tpa_bytes,
                'tpa_method':'Resident observer at 8000h installs BDOS relay at TPA end and lowers caller SP; original BDOS/BIOS remain resident at their original addresses.',
                'bad_sector':'Real out-of-image allocation triggers BDOS prompt; Ctrl-C warm boots without SEARCH totals; data image unchanged.',
                'results':results,'limits':'Host elapsed time; stack watermark of exercised paths only, not a worst-case BIOS or interrupt proof.'}
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')


if __name__ == '__main__':
    main()
