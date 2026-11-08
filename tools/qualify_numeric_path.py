#!/usr/bin/env python3
"""Exercise numeric PATH through the public cpmsim prompt on disposable media."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from build_ccp import assemble
from test_z80pack_submit_xsub import input_probe
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-dir', type=Path, required=True,
                        help='cpmsim diskdefs and disks/ for this build')
    parser.add_argument('--build', type=Path, default=ROOT / 'build')
    parser.add_argument('--simulator', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-com', type=int, required=True)
    args = parser.parse_args()
    work = args.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    disks = work / 'disks'
    shutil.copytree(args.image_dir / 'disks', disks)
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    # B is a scratch fixture volume, not the nearly full Utilities disk.
    scratch=disks/'driveb.dsk'
    scratch.write_bytes(bytes([0xe5])*scratch.stat().st_size)
    simulator = args.simulator.resolve()
    build = args.build.resolve()

    def install(drive, user, filename, data):
        existing=work/'readback.tmp'
        result=subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',
                               str(disks/f'drive{drive}.dsk'),f'{user}:{filename}',str(existing)],
                              cwd=work,capture_output=True)
        if result.returncode==0 and existing.exists():
            observed=existing.read_bytes();existing.unlink()
            if observed[:len(data)]==data and set(observed[len(data):]) <= {0,26}:
                return  # Exercise the packaged bytes without replacing them.
            raise ValueError('packaged input differs from qualification build: '+filename)
        source = work / filename
        source.write_bytes(data)
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disks / f'drive{drive}.dsk'), str(source),
                        f'{user}:{filename}'], cwd=work, check=True)

    def program(message):
        source = f"""        ORG 0100H
        LD DE,MSG
        LD C,9
        CALL 5
        RET
MSG:    DB 13,10,'{message}',13,10,'$'
        END
"""
        return assemble(Path.home() / 'bin/z80asm', source, work/'probe.bin',
                        work/'probe.lst', 0x100)

    for name in ('PATH', 'SUBMIT', 'XSUB'):
        install('a', 0, name+'.COM', (build/'utilities'/(name+'.COM')).read_bytes())
    install('a', 0, 'RCP.CPX', (build/'cpx/RCP.CPX').read_bytes())
    for path in (build/'rsx/BATCHIO.RSX', build/'system/R3PACK.RSX',
                 build/'system/R3CACHE.RSX'):
        install('a', 0, path.name, path.read_bytes())
    # Use a probe that independently checks BDOS drive/user, page zero, raw
    # case/length and both default FCBs after a cross-drive, cross-user load.
    abi = """        ORG 0100H
        LD C,25
        CALL 5
        CP 2
        JR NZ,BAD
        LD A,(4)
        CP 2
        JR NZ,BAD
        LD C,32
        LD E,0FFH
        CALL 5
        CP 4
        JR NZ,BAD
        LD HL,0080H
        LD DE,TAIL
        LD B,18
        CALL MATCH
        JR NZ,BAD
        LD HL,005CH
        LD DE,FCB1
        LD B,12
        CALL MATCH
        JR NZ,BAD
        LD HL,006CH
        LD DE,FCB2
        LD B,12
        CALL MATCH
        JR NZ,BAD
        LD DE,GOOD
        JR SHOW
BAD:    LD DE,FAIL
SHOW:   LD C,9
        CALL 5
        JP 0
MATCH:  LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DJNZ MATCH
        RET
TAIL:   DB 16,' One.txt tWo.Dat',0
FCB1:   DB 0,'ONE     TXT'
FCB2:   DB 0,'TWO     DAT'
GOOD:   DB 'INVOCATION OK',13,10,'$'
FAIL:   DB 'INVOCATION FAILED',13,10,'$'
        END
"""
    install('b', 3, 'CALLER.COM', assemble(Path.home()/'bin/z80asm', abi,
            work/'caller.bin', work/'caller.lst', 0x100))
    first, last = program('B3 IMAGE'), program('A0 IMAGE')
    install('b', 3, 'WHICH.COM', first)
    install('a', 0, 'WHICH.COM', last)
    install('b', 3, 'INPUT.COM', input_probe(work))
    install('b', 3, 'DIR.COM', program('TRANSIENT DIR'))
    install('b', 3, 'EMPTY.COM', b'')
    wrong = program('WRONG FALLBACK EXECUTED')
    install('a', 0, 'EMPTY.COM', wrong)
    install('b', 3, 'BIG.COM', first.ljust(args.max_com+128, b'X'))
    install('a', 0, 'BIG.COM', wrong)
    install('b', 3, 'FIT.COM', program('FULL TPA EXECUTED').ljust(args.max_com, b'X'))
    install('a', 0, 'PTEST.SUB',
            b'A0:PATH B3: A0:\r\nWHICH\r\nA0:XSUB\r\nINPUT\r\nBATCHFULL\r\nWHICH\r\n\x1a')

    commands = []
    def check(command, expected, prompt=b'A0>_ '):
        commands.append((command.encode()+b'\r', expected, 30))
        if expected != prompt:
            commands.append((b'', prompt, 30))

    check('PATH /HELP', b'Usage: PATH')
    check('PATH /VER', b'Numeric Command Search Path')
    check('PATH', b'PATH: . A0:')
    check('PATH D0:', b'PATH: D0:')
    check('PATH', b'PATH: D0:')  # local PATH.COM remains reachable
    check('WHICH', b'A0 IMAGE')
    check('PATH B3: . A0:', b'PATH: B3: . A0:')
    check('WHICH', b'A0 IMAGE')
    check('A0:WHICH', b'A0 IMAGE')
    check('B3:WHICH', b'B3 IMAGE')
    check('B3:WHI?H', b'B3 IMAGE')  # preserve the existing qualified FCB Open
    check('C2:WHICH', b'\n?')
    check('C4:', b'C4>_ ', b'C4>_ ')
    check('WHICH', b'B3 IMAGE', b'C4>_ ')
    check('CALLER One.txt tWo.Dat', b'INVOCATION OK', b'C4>_ ')
    check('P:WHICH', b'\n?', b'C4>_ ')
    check('A0:', b'A0>_ ')
    check('PATH B3: B03:', b'Duplicate PATH entry')
    check('PATH C32:', b'Invalid PATH user')
    check('PATH TOOLS:', b'Invalid PATH')
    check('PATH . A0: A1: B1: B2: B3: B4:', b'up to six')
    check('PATH', b'PATH: B3: . A0:')
    check('C4:', b'C4>_ ', b'C4>_ ')
    check('EMPTY', b'EMPTY PROGRAM', b'C4>_ ')
    check('BIG', b'FILE WILL NOT FIT', b'C4>_ ')
    check('FIT', b'FULL TPA EXECUTED', b'C4>_ ')
    check('A0:', b'A0>_ ')
    check('PATH', b'PATH: B3: . A0:')
    check('DIR', b'PATH     COM')
    check(':DIR', b'TRANSIENT DIR')
    check('PATH P31: A0:', b'PATH: P31: A0:')
    check('ABSENT', b'DRIVE UNAVAILABLE')
    check('A0:PATH /DEFAULT', b'PATH: . A0:')
    check('B3:', b'B3>_ ', b'B3>_ ')
    check('WHICH', b'B3 IMAGE', b'B3>_ ')
    check('A2:', b'A2>_ ', b'A2>_ ')
    check('WHICH', b'A0 IMAGE', b'A2>_ ')
    check('A0:', b'A0>_ ')
    commands += [(b'SUBMIT PTEST\r', b'INPUT OK', 60),
                 (b'', b'A0 IMAGE', 30), (b'', b'A0>_ ', 30)]
    log = session(simulator, disks, commands, work/'prompt.log')
    # Read the emitted help rows so a formatter change cannot move only one group.
    help_rows = log.split(b'   Options:\r\n', 1)[1].splitlines()
    for index, label in enumerate((b'location', b'/DEFAULT', b'', b'/H /HELP', b'/VER')):
        row = help_rows[index]
        if label:
            assert row.startswith(b'     ' + label.ljust(15)) and row[20:21].isalpha(), row
        else:
            assert not row, row
    assert b'INPUT FAILED' not in log and b'WRONG FALLBACK EXECUTED' not in log
    # Separate process and same disks prove cold defaults after a custom list.
    check_cold = [(b'PATH\r', b'PATH: . A0:', 30)]
    session(simulator, disks, check_cold, work/'cold.log')
    # An absent supported drive reaches the real media-error prompt. Ctrl-C
    # abandons Open, before the ordinary restoration code could run.
    (disks/'drived.dsk').unlink()
    session(simulator, disks, [(b'3:\r', b'A3>_ ', 30),
        (b'A0:PATH D7: A0:\r', b'A3>_ ', 30), (b'WHICH\r', b'Bad Sector', 30),
        (b'\x03', b'A3>_ ', 30), (b'A0:PATH\r', b'PATH: D7: A0:', 30)],
        work/'unready.log')
    print(json.dumps({'result': 'PASS', 'command_count': sum(bool(c) for c, _, _ in commands),
                      'largest_executed': args.max_com, 'size_rejected': args.max_com+128}))


if __name__ == '__main__':
    main()
