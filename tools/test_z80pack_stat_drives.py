#!/usr/bin/env python3
"""Qualify STAT drive status and temporary read-only state on private media."""
import argparse
import re
import subprocess
from pathlib import Path

from build_ccp import assemble
from test_z80pack_submit_xsub import ROOT, run_case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    stat = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    listing = (ROOT / 'build/utilities/stat.lst').read_text()

    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)

    def files(work):
        a = work / 'disks/drivea.dsk'
        subprocess.run(['cpmrm', '-f', 'bettercpm-default', str(a), '0:stat.com'], cwd=work, check=True)
        b = work / 'disks/driveb.dsk'
        size = len(b.read_bytes())
        b.unlink()
        b.write_bytes(bytes([0xe5]) * size)
        # 2K directory + 2K small + 22K medium + 66K large = 92K allocated.
        for name, records in [('SMALL.DAT', 1), ('MEDIUM.DAT', 161), ('LARGE.DAT', 513)]:
            source = work / name
            source.write_bytes(bytes(records * 128))
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(b), str(source), '0:' + name], cwd=work, check=True)
        source = work / 'STAT3.COM'
        source.write_bytes(stat)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(a), str(source), '3:STAT.COM'], cwd=work, check=True)

        trampoline = (len(stat) + 0x100 + 255) & ~255

        def patched(entry, count, source, stem):
            binary = bytearray(stat)
            original = binary[entry - 0x100:entry - 0x100 + count]
            binary[entry - 0x100:entry - 0x100 + count] = bytes((0xc3, trampoline & 255, trampoline >> 8)) + bytes(count - 3)
            tail = assemble(Path.home() / 'bin/z80asm', source, work / (stem + '.bin'), work / (stem + '.lst'), trampoline)
            binary += bytes(trampoline - 0x100 - len(binary)) + tail + original + bytes((0xc3, (entry + count) & 255, (entry + count) >> 8))
            return binary

        # Populate logged drives within this invocation; WBOOT resets the vector.
        def status_source(readonly):
            return f'''        ORG {trampoline}
        LD E,1
        LD C,14
        CALL 5
{('        LD C,28' + chr(10) + '        CALL 5') if readonly else ''}
        LD E,0
        LD C,14
        CALL 5
        END
'''
        ds = patched(address('DISKSTATUS'), 5, status_source(False), 'status')
        ro = patched(address('DISKSTATUS'), 5, status_source(True), 'readonly')
        # Observe the public R/O vector before STAT's normal FINISH reaches WBOOT.
        check_source = f'''        ORG {trampoline}
        LD C,29
        CALL 5
        LD A,H
        OR A
        JR NZ,BAD
        LD A,L
        CP 2
        JR NZ,BAD
        LD DE,GOOD
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JR DONE
GOOD:   DB 'B ONLY READ-ONLY',13,10,'$'
FAIL:   DB 'READ-ONLY VECTOR WRONG',13,10,'$'
DONE:
        END
'''
        checked = patched(address('FINISH'), 3, check_source, 'assign')
        return {'STAT.COM': stat, 'DSSTAT.COM': ds, 'RODS.COM': ro, 'ASSIGNCK.COM': checked}

    body = r'''
send -s "stat b:\r"
expect -exact "Bytes Remaining On B: 240K"
prompt
send -s "stat\r"
expect -re {A: R/W, Space: +[0-9]+K}
expect {
 -exact "B: R/" {puts "UNLOGGED B REPORTED"; exit 1}
 -exact "A0>_ " {}
 timeout {exit 1}
}
send -s "dsstat\r"
expect -re {A: R/W, Space: +[0-9]+K}
expect -exact "B: R/W, Space: 240K"
prompt
send -s "rods\r"
expect -re {A: R/W, Space: +[0-9]+K}
expect -exact "B: R/O, Space: 240K"
prompt
send -s "assignck b:=r/o\r"
expect -exact "B ONLY READ-ONLY"
prompt
send -s "dsstat\r"
expect -re {A: R/W, Space: +[0-9]+K}
expect -exact "B: R/W, Space: 240K"
prompt
send -s "stat b:=r/w\r"
expect -exact "Invalid STAT command"
prompt
send -s "b:\r"
expect -exact "B0>_ "
send -s "user 3\r"
expect -exact "B3>_ "
send -s "a:stat a:\r"
expect -re {Bytes Remaining On A: +[0-9]+K}
expect -exact "B3>_ "
send -s "a:stat b:\r"
expect -exact "Bytes Remaining On B: 240K"
expect -exact "B3>_ "
send -s "bye\r"
expect eof
'''
    guards = r'''proc mustexact {pattern} {
 expect {
  -exact $pattern {}
  timeout {puts "MISSING TEXT: $pattern"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
proc mustre {pattern} {
 expect {
  -re $pattern {}
  timeout {puts "MISSING REGEX: $pattern"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
'''
    body = guards + body.replace('expect -exact ', 'mustexact ').replace('expect -re ', 'mustre ')
    run_case(args.image_dir.resolve(), args.simulator.resolve(), 'stat-drives', files, body)
    print('STAT logged-drive status, exact free space, temporary R/O, WBOOT clearing and B3 restoration passed')


if __name__ == '__main__':
    main()
