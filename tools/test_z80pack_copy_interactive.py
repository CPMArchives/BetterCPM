#!/usr/bin/env python3
"""Qualify COPY collision choices, session-local policy, abort and /B."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session

PROMPT = b' [Destination exists. Overwrite? Y/N/O/S/R/?] '


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / f'drive{x}.dsk' for x in 'ab']
    def cpm(tool, disk, *values):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, values)], cwd=report, check=True)
    cpm('cpmrm', a, '0:COPY.COM')
    cpm('cpmcp', a, ROOT / 'build/utilities/COPY.COM', '0:COPY.COM')
    b.write_bytes(bytes([229]) * len(b.read_bytes()))
    names = ['A.DAT', 'B.DAT', 'C.DAT']
    sources, old = {}, {}
    for name in names:
        sources[name] = name.encode().ljust(128, b'S')
        old[name] = name.encode().ljust(128, b'O')
        f, g = report / name, report / ('old-' + name)
        f.write_bytes(sources[name]); g.write_bytes(old[name])
        cpm('cpmcp', b, f, '1:' + name)
        for user in (3, 4, 5, 6, 7):
            if user != 7 or name != 'B.DAT':
                cpm('cpmcp', b, g, str(user) + ':' + name)
    cpm('cpmchattr', b, 'r', '7:C.DAT')
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    def execute(command, responses, label, followup=None):
        steps = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30),
                 (command.encode() + b'\r', PROMPT if responses else b'A0>_ ', 60)]
        steps.extend((outgoing, wanted, 60) for outgoing, wanted in responses)
        if followup is not None:
            next_command, next_responses = followup
            steps.append((next_command.encode() + b'\r', PROMPT, 60))
            steps.extend((outgoing, wanted, 60) for outgoing, wanted in next_responses)
        return session(simulator, report / 'disks', steps, report / (label + '.txt'))
    def check(user, expected, label):
        for name in names:
            f = report / (label + '-' + name)
            cpm('cpmcp', b, str(user) + ':' + name, f)
            assert f.read_bytes() == expected[name], (user, name)
    text = execute('COPY B1:*.DAT B3:', [(b'y', PROMPT), (b'N', PROMPT),
                   (b'?', PROMPT), (b'!', PROMPT), (b'Y', b'A0>_ ')], 'yes-no-help')
    assert b'B1:A.DAT -> B3:A.DAT' in text
    assert b'B1:B.DAT -> B3:B.DAT' in text
    assert b'Y - Yes  N - No' in text
    help_line=b'Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename'
    assert text.count(help_line)==2
    for remainder in text.split(help_line)[1:]:
        assert remainder.lstrip(b'\r\n').startswith(b'B1:C.DAT -> B3:C.DAT'+PROMPT),remainder
    check(3, {'A.DAT': sources['A.DAT'], 'B.DAT': old['B.DAT'], 'C.DAT': sources['C.DAT']}, 'mixed')
    text = execute('COPY B1:*.DAT B4:', [(b'O', b'A0>_ ')], 'overwrite-all',
                   ('COPY B1:*.DAT B4:', [(b'S', b'A0>_ ')]))
    assert text.count(PROMPT) == 2
    check(4, sources, 'all-yes')
    text = execute('COPY B1:*.DAT B5:', [(b'S', b'A0>_ ')], 'skip-all',
                   ('COPY B1:*.DAT B5:', [(b'\x03', b'A0>_ ')]))
    assert text.count(PROMPT) == 2
    check(5, old, 'all-no')
    text = execute('COPY B1:*.DAT B6:', [(b'Y', PROMPT), (b'\x03', b'A0>_ ')], 'abort')
    assert b'COPY ABORTED' in text
    check(6, {'A.DAT': sources['A.DAT'], 'B.DAT': old['B.DAT'], 'C.DAT': old['C.DAT']}, 'abort')
    text = execute('COPY B1:*.DAT B7: /B', [], 'batch')
    assert PROMPT not in text and b'FILE EXISTS' in text and b'READ ONLY' in text
    check(7, {'A.DAT': old['A.DAT'], 'B.DAT': sources['B.DAT'], 'C.DAT': old['C.DAT']}, 'batch')
    check(1, sources, 'sources')
    # SUBMIT alone must still allow the COPY collision prompt.
    cpm('cpmrm', a, '0:SUBMIT.COM')
    cpm('cpmcp', a, ROOT / 'build/utilities/SUBMIT.COM', '0:SUBMIT.COM')
    script = report / 'ASK.SUB'
    script.write_bytes(b'COPY B1:A.DAT B5:\r\n\x1a')
    cpm('cpmcp', a, script, '0:ASK.SUB')
    text = execute('SUBMIT ASK', [(b'N', b'A0>_ ')], 'submit-interactive')
    assert PROMPT in text
    # Rename rejects malformed names and future/past batch targets, then copies
    # under a new exact name. Editing, blank cancellation and Ctrl-C are explicit.
    text = execute('COPY B1:*.DAT B5:', [
        (b'R', b'New Name: '), (b'BAD*NAME.DAT\r', b'New Name: '),
        (b'B4:NEW.DAT\r', b'New Name: '), (b'B.DAT\r', b'New Name: '),
        (b'newx\x08.dat\r', PROMPT), (b'R', b'New Name: '),
        (b'NEW.DAT\r', b'New Name: '), (b'\r', PROMPT), (b'S', b'A0>_ ')], 'rename')
    assert b'Invalid filename.' in text and b'COPY DESTINATION CONFLICT' in text
    f = report / 'renamed.dat'
    cpm('cpmcp', b, '5:NEW.DAT', f)
    assert f.read_bytes() == sources['A.DAT']
    check(5, old, 'rename-originals')
    text = execute('COPY B1:A.DAT B5:', [(b'R', b'New Name: '),
        (b'NEW.DAT\r', PROMPT), (b'N', b'A0>_ ')], 'rename-existing')
    assert b'B5:NEW.DAT' in text
    text = execute('COPY B1:A.DAT B5:', [(b'R', b'New Name: '),
        (b'\x03', b'A0>_ ')], 'rename-abort')
    assert b'COPY ABORTED' in text
    text = execute('COPY B1:A.DAT B1:OTHER.DAT', [], 'prepare-same-du')
    text = execute('COPY B1:A.DAT B1:OTHER.DAT', [(b'R', b'New Name: '),
        (b'A.DAT\r', b'New Name: '), (b'\x03', b'A0>_ ')], 'rename-source-overlap')
    assert b'COPY DESTINATION CONFLICT' in text
    check(1, sources, 'rename-source-preserved')
    text = execute('COPY B1:A.DAT B7:', [(b'R', b'New Name: '),
        (b'C.DAT\r', b'A0>_ ')], 'rename-read-only')
    assert b'READ ONLY' in text
    check(7, {'A.DAT': old['A.DAT'], 'B.DAT': sources['B.DAT'],
              'C.DAT': old['C.DAT']}, 'rename-read-only-preserved')
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'choices': ['Y', 'N', 'O', 'S', 'R', '?'], 'invalid_response_reprompts': True,
        'policy_resets_between_invocations': True, 'ctrl_c_keeps_completed_files': True,
        'batch_no_prompt_and_continues': True, 'submit_remains_interactive': True,
        'rename_validation_and_editing': True, 'rename_blank_and_abort': True,
        'rename_batch_and_source_safety': True, 'rename_read_only_protected': True,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('COPY interactive choices, policy reset, Ctrl-C, /B and SUBMIT prompting pass')


if __name__ == '__main__':
    main()
