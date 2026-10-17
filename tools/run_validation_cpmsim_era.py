#!/usr/bin/env python3
"""Validate shipped ERA selection/protection without replacing release utilities."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    baseline = args.image_dir.resolve()
    manifest = json.loads((baseline / 'report.json').read_text())
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    (report / 'disks').mkdir()
    for letter in 'ab':
        shutil.copy2(baseline / manifest['image'], report / 'disks' / ('drive' + letter + '.dsk'))
    shutil.copy2(__file__, report / 'executed-runner.py')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / ('drive' + n + '.dsk') for n in 'ab']
    def cpm(tool, disk, *values):
        return subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, values)], cwd=report, check=True, capture_output=True)
    cpm('cpmrm', b, '0:*.*')
    original = {}
    def add(user, name, attrs='', size=128):
        path = report / ('fixture-' + str(user) + '-' + name)
        data = name.encode().ljust(size, b'X')
        path.write_bytes(data)
        cpm('cpmcp', b, path, str(user) + ':' + name)
        if attrs:
            cpm('cpmchattr', b, attrs, str(user) + ':' + name)
        original[(user,name)] = data
    for user in range(1, 10):
        add(user, 'NORMAL.DAT', size=33024 if user == 1 else 128)
        add(user, 'READONLY.DAT', 'r')
        add(user, 'SYSTEM.DAT', 's')
        add(user, 'BOTH.DAT', 'rs')
    for user in (12, 13):
        for name, attrs in [('NORMAL.DAT',''), ('READONLY.DAT','r'), ('SYSTEM.DAT','s'), ('BOTH.DAT','rs')]:
            add(user, name, attrs)
    add(10, 'N.DAT'); add(10, 'Y.DAT'); add(11,'EXACT.DAT')
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    prompt = b'A0>_ '
    results = []
    def execute(command, responses=(), label='case'):
        wanted = responses[0][0] if responses else prompt
        steps = [(command.encode() + b'\r', wanted, 60)]
        for i, (_, outgoing) in enumerate(responses):
            next_prompt = responses[i+1][0] if i+1 < len(responses) else prompt
            steps.append((outgoing, next_prompt, 60))
        text = session(simulator, report/'disks', steps, report/(label+'.txt'))
        results.append(label)
        return text
    def remains(user, expected):
        # Inspect physical directory sectors; cpmls aborts on empty glob results.
        image = b.read_bytes()
        skew = [0,4,8,12,16,2,6,10]
        directory = b''.join(image[6*18*256+n*256:6*18*256+(n+1)*256] for n in skew)
        actual = set()
        for offset in range(0, len(directory), 32):
            entry = directory[offset:offset+32]
            if entry[0] == user:
                name = bytes(v & 127 for v in entry[1:12])
                actual.add(name[:8].decode().rstrip()+'.'+name[8:].decode().rstrip())
        assert actual == set(expected), (user, actual, expected)
        for name in expected:
            dest = report / ('remaining-' + str(user) + '-' + name)
            cpm('cpmcp', b, str(user)+':'+name, dest)
            assert dest.read_bytes() == original[(user,name)]
    all_names = {'NORMAL.DAT','READONLY.DAT','SYSTEM.DAT','BOTH.DAT'}
    execute('ERA B[12,13]:*.DAT[$RW]', label='resident-multi-du')
    remains(12, all_names-{'NORMAL.DAT'}); remains(13, all_names-{'NORMAL.DAT'})
    execute('ERA B12:*.DAT[$SYS+$RO]', label='resident-protected-explicit')
    remains(12, all_names-{'NORMAL.DAT'})
    text = execute('ERA B13:*.DAT /R', label='resident-use-transient')
    assert b'Use :ERA' in text
    remains(13, all_names-{'NORMAL.DAT'})
    text = execute(':ERA /VER', label='version')
    assert b'BetterCP/M ERA 1.0 (Build ' in text
    text = execute(':ERA /Y B1:*.DAT', label='safe-broad')
    assert b'1 FILES ERASED, 3 SKIPPED, 34K FREED' in text, text[-500:]
    remains(1, all_names-{'NORMAL.DAT'})
    execute(':ERA /Y /R B2:*.DAT[$SYS+$RO,$RW]', label='matching-branch')
    remains(2, {'SYSTEM.DAT','READONLY.DAT'})
    execute(':ERA /Y /R B3:*.DAT[$SYS,$RO]', label='separate-branches')
    remains(3, {'NORMAL.DAT','BOTH.DAT'})
    execute(':ERA /Y /R B4:*.DAT[!$DIR+!$RW]', label='negated-aliases')
    remains(4, all_names-{'BOTH.DAT'})
    execute(':ERA /Y B5:*.DAT[$RO]', label='unattended-ro-skip')
    remains(5, all_names)
    text = execute(':ERA /C B5:READONLY.DAT[$RO]', [(b'Read only. Erase? Y/N ', b'Y')], 'one-ro-prompt')
    assert text.count(b'Erase? Y/N ') == 1
    remains(5, all_names-{'READONLY.DAT'})
    execute(':ERA /Q B6:*.DAT', [(b'ERASE THESE FILES? Y/N ', b'N')], 'quiet-still-confirms')
    remains(6, all_names)
    execute(':ERA B6:NORMAL.DAT', [(b'Erase? Y/N ', b'\x03')], 'abort-exact')
    remains(6, all_names)
    for i, operand in enumerate(('B6:F*A.DAT','B6:*.DAT /Z','B6:*.DAT /QQ','[B6,E0]:*.DAT','B6:*.DAT[$RO,]')):
        text = execute(':ERA /Y '+operand, label='invalid-'+str(i))
        assert b'Invalid filespec or option.' in text or b'INVALID DRIVE' in text
        remains(6, all_names)
    execute(':ERA /Y /C [B7,B8,B7]:*.DAT', label='multi-du-deduplicated')
    remains(7, all_names-{'NORMAL.DAT'}); remains(8, all_names-{'NORMAL.DAT'})
    execute(':ERA /Y /R B9:*.DAT[$RO+$SYS,$RO+$DIR,$RW+$SYS,$RW+$DIR]', label='all-admitted')
    remains(9, set())
    execute(':ERA /C B10:*.DAT', [(b'ERASE THESE FILES? Y/N ', b'Y'),
            (b'Erase? Y/N ', b'N'), (b'Erase? Y/N ', b'Y')], 'per-file-confirmation')
    remains(10, {'N.DAT'})
    text=execute(':ERA /C B11:EXACT.DAT', [(b'Erase? Y/N ',b'Y')], 'one-exact-prompt')
    assert text.count(b'Erase? Y/N ')==1
    remains(11,set())
    shipped = audit(baseline, manifest, report, a)
    check = subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(b)],cwd=report,check=True,capture_output=True)
    (report/'secondary-filesystem.txt').write_bytes(check.stdout + check.stderr)
    (report/'result.json').write_text(json.dumps({'status':'PASS','sessions':results,'unchanged_shipped_files':shipped,'baseline_sha256':manifest['sha256'],'simulator_sha256':sha(simulator),'runner_sha256':sha(Path(__file__))},indent=2)+'\n')
    print('PASS shipped resident/transient ERA:', len(results), 'sessions')


if __name__ == '__main__':
    main()
