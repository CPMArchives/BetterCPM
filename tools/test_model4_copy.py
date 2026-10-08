#!/usr/bin/env python3
"""Qualify shared COPY on Model 4 SYSTEM-to-DATA media in both profiles."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from trs80gp_launch import run


def digest(data):
    return hashlib.sha256(data).hexdigest()


def files(raw):
    result = {}
    for at in range(0, 4096, 32):
        entry = raw[at:at + 32]
        if entry[0] > 31:
            continue
        name = bytes(x & 127 for x in entry[1:12])
        key = (entry[0], name)
        payload = b''.join(raw[block * 2048:(block + 1) * 2048]
                           for slot in range(8)
                           if (block := int.from_bytes(entry[16 + 2 * slot:18 + 2 * slot], 'little')))
        result.setdefault(key, []).append((entry[12] + 32 * (entry[14] & 63),
                                           payload[:entry[15] * 128], entry))
    return {key: (b''.join(p[1] for p in sorted(parts)), [p[2] for p in sorted(parts)])
            for key, parts in result.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--profile', choices=('cpx', 'transient'))
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    observations = []
    sources = []
    for mask in range(8):
        records = 0 if mask == 0 else 1
        payload = bytes((index * 29 + mask) & 255 for index in range(records * 128))
        sources.append((f'S{mask:03}.DAT', payload, 1, mask))
    for profile in ((args.profile,) if args.profile else ('cpx', 'transient')):
        work = report / profile; work.mkdir()
        extras = [('CPX.COM', (ROOT / 'build/utilities/CPX.COM').read_bytes()), *sources]
        if profile == 'transient':
            extras.append(('COPY.COM', (ROOT / 'build/utilities/COPY.COM').read_bytes()))
        large = bytes((index * 17 + 9) & 255 for index in range(17 * 128))
        extras.append(('LARGE.DAT', large, 1, 7))
        original_a = medium(extras)
        old = [(4, name, bytes(257 * 128 if name == 'S003.DAT' else 128)) for name, *_ in sources]
        original_b = build(install_files([(0, 'KEEP.DAT', b'KEEP'.ljust(128, b'!')), *old]))
        a, b = work / 'a.dmk', work / 'b.dmk'
        a.write_bytes(original_a); b.write_bytes(original_b)
        (work / 'before-a.dmk').write_bytes(original_a)
        (work / 'before-b.dmk').write_bytes(original_b)
        def invoke(label, commands):
            case = work / label; case.mkdir()
            invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(a), '-d1', str(b), '-id', '3000']
            setup = [('CPX UNLOAD RCP', 'A0')]
            if profile == 'cpx':
                setup.append(('CPX LOAD RCP', 'A0'))
            for command, caller in setup + commands:
                invocation += keys(command + '\r') + ['-itime', '0', '-iw', caller + '> ', '-id', '500', '-it']
            invocation += ['-ix']
            (case / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
            run(invocation, cwd=case, check=True, timeout=600)
            captures = sorted(case.glob('trs80-text-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
            assert len(captures) == len(setup + commands), (label, len(captures))
            texts = []
            for capture, (command, caller) in zip(captures, setup + commands):
                text = screen(capture); capture.with_suffix('.txt').write_text(text)
                assert command in text and re.search(caller + r'>\s*$', text.rstrip()), (command, text)
                assert not any(error in text for error in ('CPX load failed', 'CPX module or profile error')), text
                texts.append(text)
            return texts[len(setup):]
        commands = [('COPY A1:S*.DAT B3:', 'A0'), ('COPY A1:S*.DAT B4: /O', 'A0'),
                    ('COPY B5:=A1:S?*.DAT', 'A0'), ('COPY A1:LARGE.DAT B31:', 'A0')]
        texts = invoke('success', commands)
        for text in texts:
            assert not any(error in text for error in ('FILE EXISTS', 'NO FILE', 'NO SPACE', 'READ ONLY', 'COPY source destination')), text
        recovered = files(extract_raw(b.read_bytes()))
        for user in (3, 4, 5):
            for name, payload, _, mask in sources:
                key = (user, name.partition('.')[0].ljust(8).encode() + b'DAT')
                content, entries = recovered[key]
                assert content == payload, (profile, user, name, len(content), len(payload))
                assert len(entries) == max(1, (len(payload) + 16383) // 16384)
                for entry in entries:
                    assert sum((entry[9 + bit] >> 7) << bit for bit in range(3)) == mask, (user, name, entry.hex())
        assert recovered[(31, b'LARGE   DAT')][0] == large
        assert recovered[(0, b'KEEP    DAT')][0] == b'KEEP'.ljust(128, b'!')
        assert a.read_bytes() == original_a, 'source/system media changed'
        for letter, image in [('a', a), ('b', b)]:
            (work / f'success-{letter}.dmk').write_bytes(image.read_bytes())
        rejects = [('COPY A1:S003.DAT B3:', 'FILE EXISTS'),
                   ('COPY A1:S003.DAT B4: /O', 'READ ONLY'),
                   ('COPY A1:S003.DAT A1: /O', 'FILE EXISTS'),
                   ('COPY A1:Z*.DAT B7:', 'NO FILE'),
                   ('COPY A1:S*X.DAT B7:', 'COPY source destination'),
                   ('COPY A1:S003.DAT B:*.DAT', 'COPY source destination'),
                   ('COPY A1:S003.DAT B32:', 'COPY source destination'),
                   ('COPY A1:S003.DAT B7: /O /O', 'COPY source destination')]
        before = (a.read_bytes(), b.read_bytes())
        texts = invoke('rejections', [(command, 'A0') for command, _ in rejects])
        for text, (command, expected) in zip(texts, rejects):
            assert expected in text.rsplit(command, 1)[1], (command, text)
        assert (a.read_bytes(), b.read_bytes()) == before, 'rejected operations modified media'
        for resource in ('directory', 'allocation'):
            fixture = ([(0, f'X{index:07}.DAT', b'') for index in range(128)]
                       if resource == 'directory' else [(0, 'FULL.DAT', bytes(398 * 2048))])
            full = build(install_files(fixture)); b.write_bytes(full)
            (work / f'full-{resource}-before.dmk').write_bytes(full)
            expected_files = files(extract_raw(full))
            text = invoke('full-' + resource, [('COPY A1:S001.DAT B:TARGET.DAT', 'A0')])[0]
            assert 'NO SPACE' in text.rsplit('COPY A1:S001.DAT B:TARGET.DAT', 1)[1], text
            assert a.read_bytes() == original_a
            assert files(extract_raw(b.read_bytes())) == expected_files, resource
            (work / f'full-{resource}-after.dmk').write_bytes(b.read_bytes())
            if resource == 'directory':
                assert b.read_bytes() == full
        observations.append({'profile': profile, 'success_commands': commands,
                             'rejections': rejects, 'attribute_masks': list(range(8)),
                             'largest_source_records': 17, 'overwritten_records': 257,
                             'caller_restored': True, 'full_directory_and_allocation_cleanup': True, 'source_and_unrelated_file_preserved': True})
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'observations': observations,
        'copy_sha256': digest((ROOT / 'build/utilities/COPY.COM').read_bytes()),
        'rcp_sha256': digest((ROOT / 'build/cpx/RCP.CPX').read_bytes()),
        'bdos_sha256': digest((ROOT / 'build/bdos/bdos.bin').read_bytes()),
        'emulator_sha256': digest(DEFAULT_EMULATOR.read_bytes()),
        'cpx_has_no_copy_com': True}, indent=2) + '\n')
    print('Model 4 COPY CPX/transient wildcard, overwrite, eight attributes, user 31 and rejection qualification PASS')


if __name__ == '__main__':
    main()
