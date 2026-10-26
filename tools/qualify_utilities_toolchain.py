#!/usr/bin/env python3
"""Exercise the packaged native toolchain from Utilities B: on both targets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as system_dmk
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from fdf_format import select_fdf
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run as launch
from qualify_codec_native import native_text, verify_native
from codec_version import prepare_version

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()
CODECS = ('SQ', 'USQ', 'CR', 'UNCR', 'LZH', 'UNLZH')


def probe_sources():
    return {
        'MAIN.MAC': b''' CSEG
 EXTRN SAY
 LD IX,BUFFER
 LD (IX+0),42H
 LD A,(IX+0)
 CP 42H
 JR NZ,BAD
 CALL SAY
 LD DE,DONE
 LD C,9
 CALL 5
 JP 0
BAD: LD DE,FAIL
 LD C,9
 CALL 5
 JP 0
DONE: DB 'TOOLCHAIN OK',13,10,'$'
FAIL: DB 'TOOLCHAIN FAILED',13,10,'$'
 DSEG
BUFFER: DS 1
 END
''',
        'PART.MAC': b''' CSEG
 PUBLIC SAY
 INCLUDE PRINT.INC
SAY: PRINT MESSAGE
 RET
MESSAGE: DB 'MODULE OK',13,10,'$'
 END
''',
        'PRINT.INC': b'''PRINT MACRO TARGET
 LD DE,TARGET
 LD C,9
 CALL 5
 ENDM
''',
        'BAD.MAC': b' CSEG\n LD NOREGISTER,42H\n END\n',
    }


def codec_sources(command, work):
    prepared = work / 'prepared'
    prepared.mkdir()
    prepare_version(command, prepared)
    paths = {n: ROOT / 'src/codec' / n for n in
             ('codec.inc', 'codec.mac', command.lower()+'.inc', command.lower()+'.mac')}
    paths.update({'cfio.mac': ROOT / 'src/utilities/common/codecfile.mac',
                  'command.mac': ROOT / 'src/utilities' / (command.lower()+'.mac')})
    for name, path in paths.items():
        (prepared / name).write_text(path.read_text())
    return {p.name.upper(): native_text(p.read_text()) for p in prepared.iterdir()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('system', 'utilities', 'artifacts', 'output', 'simulator'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--platforms', nargs='+', choices=('z80pack', 'trs80gp'), default=('z80pack', 'trs80gp'))
    p.add_argument('--cases', nargs='+', choices=('PROBE',)+CODECS, default=('PROBE',)+CODECS)
    a = p.parse_args()
    for name in ('system', 'utilities', 'artifacts', 'output', 'simulator'):
        setattr(a, name, getattr(a, name).expanduser().resolve())
    a.output.mkdir(parents=True, exist_ok=False)
    executed_runner = Path(__file__).read_bytes()
    (a.output / 'runner-executed.py').write_bytes(executed_runner)
    result = {'status': 'IN_PROGRESS', 'runner_sha256': sha(executed_runner),
              'simulator_sha256': sha(a.simulator.read_bytes()),
              'trs80gp_sha256': sha(DEFAULT_EMULATOR.read_bytes()), 'platforms': {}}
    for platform in a.platforms:
        native = platform == 'trs80gp'
        r = json.loads((a.system / platform / 'report.json').read_text())
        system = a.system / platform / r['image']
        source = system.read_bytes()
        utilities = a.utilities/('BetterCPM-Utilities-'+platform+('-80T-DS-800K.dmk' if native else '-332K.dsk'))
        ub = utilities.read_bytes()
        pr = {'status': 'IN_PROGRESS', 'system_sha256': sha(source), 'utilities_sha256': sha(ub), 'cases': {}}
        result['platforms'][platform] = pr
        for case in a.cases:
            w = a.output / platform / case
            w.mkdir(parents=True)
            files = probe_sources() if case == 'PROBE' else codec_sources(case, w)
            if case == 'PROBE':
                files = {n: t.replace(b'\n', b'\r\n')+b'\x1a' for n,t in files.items()}
                commands = ['B:ZSM4 MAIN=MAIN', 'B:ZSM4 PART=PART', 'B:LINK CHECK=MAIN,PART[A]',
                            'CHECK', 'B:ZSM4 BAD=BAD', 'B:LINK UNRES=MAIN[A]']
            else:
                commands = ['B:ZSM4 COMMAND=COMMAND', 'B:LINK COMMAND[A]']
            # A marker after each command proves a return to the batch environment.
            script = []
            for i, cmd in enumerate(commands):
                marker = f'TOOL {case} STEP {i} DONE'
                program = f'TM{i}'
                # Native markers wait for physical Enter before the next CLS.
                stub = '1110010e09cd05000e01cd0500c30000' if native else '110b010e09cd0500c30000'
                files[program+'.COM'] = bytes.fromhex(stub)+(marker+'\r\n$').encode()
                script += ['CLS', cmd, program]
            files['QUALIFY.SUB'] = ('\r\n'.join(script)+'\r\n\x1a').encode()
            defs = disk_definition(select_fdf(ROOT / 'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT))
            defs += '''diskdef toolchain-system
 libdsk:format pcw800
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
'''
            (w / 'diskdefs').write_text(defs)
            definition = 'toolchain-system' if native else 'bettercpm-default'
            raw = w / 'system.raw'
            raw.write_bytes(extract_raw(source) if native else source)
            def tool(*args):
                return subprocess.run(list(map(str,args)), cwd=w, check=True, capture_output=True)
            for name,data in files.items():
                host = w / name
                host.write_bytes(data)
                tool('cpmcp', '-T', 'raw', '-f', definition, raw, host, '0:'+name)
            if native:
                data = bytearray(raw.read_bytes())
                for i in range(DIRECTORY_ENTRIES):
                    at = FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
                    if data[at] == 0 and data[at+1:at+12] == b'STARTUP SUB':
                        data[at] = 0xe5
                add_file(data, 'STARTUP.SUB', b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nSUBMIT QUALIFY\r\n\x1a')
                disk = w / 'a.dmk'
                disk.write_bytes(system_dmk(data))
                (w / 'b.dmk').write_bytes(ub)
                args = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-ktx',
                        '-d0', str(disk), '-d1', str(w/'b.dmk'), '-itime', '60000']
                for i in range(len(commands)):
                    args += ['-iw', f'TOOL {case} STEP {i} DONE', '-it']
                    args += key_args('\r', 250) + ['-id', '1000']
                args += ['-ix']
                (w / 'invocation.json').write_text(json.dumps(args, indent=2)+'\n')
                launch(args, cwd=w, timeout=600)
                captures = sorted(w.glob('trs80-text-*'), key=lambda p: int(p.stem.rsplit('-',1)[1]))
                logs = [bytes(x&127 for x in p.read_bytes()[:1920]) for p in captures]
                assert len(logs) == len(commands), (case, 'missing native captures')
                assert (w / 'b.dmk').read_bytes() == ub
                raw.write_bytes(extract_raw(disk.read_bytes()))
            else:
                disks = w / 'disks'
                disks.mkdir()
                shutil.copy2(raw, disks / 'drivea.dsk')
                for letter in 'bcd':
                    (disks / f'drive{letter}.dsk').write_bytes(ub)
                steps = [(b'SUBMIT QUALIFY\r', f'TOOL {case} STEP {len(commands)-1} DONE'.encode(), 240),
                         (b'', b'A0>_ ', 30)]
                transcript = session(a.simulator, disks, steps, w / 'transcript.bin')
                logs = [transcript]
                assert (disks / 'driveb.dsk').read_bytes() == ub
                shutil.copy2(disks / 'drivea.dsk', raw)
            log = b'\n'.join(logs)
            (w / 'console.bin').write_bytes(log)
            # Native screens have fixed-width padding between output lines.
            errors = re.findall(rb'Errors: +([0-9]+)', log)
            assert b'ZSM' in log and b'4.7' in log and b'LINK 1.3' in log, 'tool identities missing'
            if case == 'PROBE':
                assert errors == [b'0', b'0', b'1'], errors
                assert b'MODULE OK' in log and b'TOOLCHAIN OK' in log and b'TOOLCHAIN FAILED' not in log
                assert b'UNDEFINED' in log.upper(), 'missing unresolved-symbol diagnostic'
                assert b'SAY' in log
            else:
                assert errors == [b'0'], errors
                output = w / 'COMMAND.COM'
                tool('cpmcp','-T','raw','-f',definition,raw,'0:COMMAND.COM',output)
                expected = (a.artifacts / 'build/utilities' / (case+'.COM')).read_bytes()
                verify_native(output.read_bytes(), expected, log)
            for name,data in files.items():
                output = w / ('after-'+name)
                tool('cpmcp','-T','raw','-f',definition,raw,'0:'+name,output)
                assert output.read_bytes()[:len(data)] == data, ('input changed',name)
            check = tool('fsck.cpm','-T','raw','-f',definition,'-n',raw)
            (w / 'filesystem.txt').write_bytes(check.stdout+check.stderr)
            assert utilities.read_bytes() == ub and system.read_bytes() == source
            pr['cases'][case] = {'status': 'PASS', 'commands': commands, 'console_sha256': sha(log),
                'inputs_sha256': {n:sha(d) for n,d in files.items()},
                'parity': 'macro/include, multi-module relocation, code/data and execution; invalid operand and unresolved external rejected' if case == 'PROBE' else 'exact qualified COM bytes and CP/M padding',
                'utilities_unchanged': True, 'inputs_unchanged': True, 'filesystem': 'PASS'}
            (a.output / 'report.json').write_text(json.dumps(result,indent=2)+'\n')
            print(f'PASS {platform} {case}', flush=True)
        pr['status'] = 'PASS'
    result['status'] = 'PASS'
    (a.output / 'report.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
