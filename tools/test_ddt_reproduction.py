#!/usr/bin/env python3
"""Differential CP/M smoke test of reference and source-only DDT candidate.

Uses stock BDOS Function 10 line editing through DDT's unchanged GETBUFF.
Does not replace full byte qualification or the engineering behavior matrix.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/ddt-reproduction')
    parser.add_argument('--reference', type=Path, default=ROOT/'third_party/dri-ddt/DDT.COM')
    base = Path.home()/'projects/git/z80pack/cpmsim'
    parser.add_argument('--cpmsim', type=Path, default=base/'cpmsim')
    parser.add_argument('--system-disk', type=Path, default=base/'disks/library/cpm22-62khd.dsk')
    parser.add_argument('--disk-template', type=Path, default=base/'disks/library/cpm22-1.dsk')
    args = parser.parse_args()
    build = args.build.resolve()
    env = dict(os.environ)
    env['PATH'] = str(args.cpmsim.resolve().parent/'srctools')+os.pathsep+env.get('PATH','')
    # Include rubout and Ctrl-U edits before a reproducible hex arithmetic query.
    commands = ['H100,20', 'F300,30F,41', 'D300,30F', 'M300,30F,320',
                'D320,32F', 'X', 'L100,10B', 'Z', 'H100,2X\\1770',
                'bad\\025H100,20']
    transcripts = {}
    for label, binary in [('reference', args.reference),
                          ('candidate', build/'DDT-source-candidate.COM')]:
        with tempfile.TemporaryDirectory(prefix='ddt-smoke-', dir=build) as temp:
            work = Path(temp)
            disks = work/'disks'
            disks.mkdir()
            shutil.copyfile(args.system_disk, disks/'drivea.dsk')
            shutil.copyfile(args.disk_template, disks/'driveb.dsk')
            for cmd in [['mkfs.cpm', '-f', 'ibm-3740', disks/'driveb.dsk'],
                        ['cpmcp', '-f', 'ibm-3740', disks/'driveb.dsk', binary, '0:DDT.COM']]:
                subprocess.run([str(x) for x in cmd], check=True, capture_output=True)
            transcript = build/(label+'-smoke.txt')
            script = ['set timeout 10', f'spawn {{{args.cpmsim.resolve()}}} -z -d {{{disks}}}',
                      'expect "A>"', 'send -- "B:\\r"', 'expect "B>"',
                      f'set f [open {{{transcript}}} w]', 'fconfigure $f -translation binary',
                      'send -- "DDT\\r"', 'expect -re {\\r\\n-}',
                      'puts -nonewline $f $expect_out(buffer)']
            for command in commands:
                script += [f'send -- "{command}\\r"', 'expect -re {\\r\\n-}',
                           'puts -nonewline $f $expect_out(buffer)']
            script += ['send -- "G0\\r"', 'expect "B>"',
                       'puts -nonewline $f $expect_out(buffer)', 'close $f',
                       'send "\\034"', 'expect eof']
            result = subprocess.run(['expect', '-c', '\n'.join(script)], env=env,
                                    cwd=work, capture_output=True, timeout=30)
            (build/(label+'-smoke.log')).write_bytes(result.stdout+result.stderr)
            assert result.returncode == 0, result.stderr
            transcripts[label] = transcript.read_bytes()
            assert transcripts[label].count(b'B>') == 1
            assert b'DDT VERS 2.2' in transcripts[label]
            assert b'0120 00E0' in transcripts[label]
            assert b'G0' in transcripts[label]
            assert transcripts[label].count(b'0120 00E0') == 3
            assert transcripts[label].count(b'\n-') == len(commands)+1
    equal = transcripts['reference'] == transcripts['candidate']
    report = {'identical': equal, 'commands': commands, 'line_editing':
              'Original DDT GETBUFF -> preserved BDOS Function 10; rubout and Ctrl-U tested.',
              'limit': 'CP/M smoke test only. Does not establish full-file reproduction or exhaustive behavior parity.'}
    (build/'smoke-qualification.json').write_text(json.dumps(report, indent=2)+'\n')
    assert equal, 'DDT console transcripts differ'
    print('Reference/candidate CP/M smoke transcripts identical, including rubout and Ctrl-U.')


if __name__ == '__main__':
    main()
