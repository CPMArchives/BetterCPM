#!/usr/bin/env python3
"""Model 4 named package export with exact payload/source preservation."""
from pathlib import Path
import tempfile
from add_cpm_file_to_dmk import extract_raw
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_disk_utilities import medium
from test_model4_copy import files
from test_sysgen_install import setup_program, screen
from trs80gp_launch import run

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = ROOT/'build/test-results/sysgen-export-model4'
    report.mkdir(parents=True, exist_ok=True)
    import test_sysgen_install as installer
    installer.OUT = report
    source = medium([('SETBSYS.COM', setup_program())])
    target = medium([('KEEP.TXT', b'KEEP THIS FILE\r\n')])
    with tempfile.TemporaryDirectory(prefix='sysgen-export-m4-') as t:
        w = Path(t)
        (w/'a.dmk').write_bytes(source)
        (w/'b.dmk').write_bytes(target)
        args = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
                '-d0', str(w/'a.dmk'), '-d1', str(w/'b.dmk'), '-id', '2500']
        args += key_args('SETBSYS\r')+['-id','7000','-it']
        args += key_args('SYSGEN A: B:BASE090.SYS\r', delay=25)+['-itime','0','-iw','Package exported and verified.','-it','-ix']
        run(args, cwd=w, timeout=180)
        texts = [screen(p) for p in sorted(w.glob('trs80-text-*.bin'))]
        (report/'screens.txt').write_text('\n\n'.join(texts))
        assert any('B SYSTEM READY' in s for s in texts), texts
        assert any('Package exported and verified.' in s for s in texts), texts
        assert (w/'a.dmk').read_bytes() == source
        raw = extract_raw((w/'b.dmk').read_bytes())
        old = extract_raw(target)
        assert raw[:20480] == old[:20480], 'export modified protected records'
        all_files = files(raw[20480:])
        package = all_files[0, b'BASE090 SYS'][0]
        assert len(package) == 20608
        assert package[:10] == b'BCSY\x01\x01\xa0\x00\xc4\xd5'
        assert package[128:] == extract_raw(source)[:20480]
        before = files(old[20480:])
        for key, (data, _) in before.items():
            assert all_files[key][0] == data, key
        (report/'BASE090.SYS').write_bytes(package)
    print('PASS: Model 4 named export exact package, source/protected tracks and existing files preserved')


if __name__ == '__main__':
    main()
