#!/usr/bin/env python3
"""Export a named system package, restore it, and boot disposable cpmsim media."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_z80pack_image import DEFAULT_FORMAT
from fdf_format import select_fdf
from system_layout import LAYOUT
from startup_record import build as startup_record
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--simulator', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args = p.parse_args()
    report = ROOT/'build/test-results/sysgen-export-z80pack'
    report.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sysgen-export-') as t:
        w = Path(t)
        shutil.copytree(args.image_dir/'disks', w/'disks')
        shutil.copy2(args.image_dir/'diskdefs', w/'diskdefs')
        src = w/'disks/drivea.dsk'
        fmt = select_fdf(ROOT/'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
        mapping = fmt.raw_record_map()
        data = bytearray(src.read_bytes())
        saved = startup_record('VER /BANNER', system_base=LAYOUT['SYSTEM'])
        # VER /BANNER itself has no filesystem writes. Preserve a nonempty saved
        # startup record while avoiding SUBMIT's temporary-file side effects.
        for i in range(2):
            at = mapping[i+1]*128
            data[at:at+128] = saved[i*128:i*128+128]
        src.write_bytes(data)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(src),'0:SYSGEN.COM'],cwd=w,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(src),str(ROOT/'build/utilities/SYSGEN.COM'),'0:SYSGEN.COM'],cwd=w,check=True)
        original = src.read_bytes()
        b = w/'disks/driveb.dsk'
        c = w/'disks/drivec.dsk'
        b.write_bytes(b'\xe5'*len(b.read_bytes()))
        c.write_bytes(b'\xe5'*len(c.read_bytes()))
        old_c = c.read_bytes()
        transcript = session(args.simulator, w/'disks', [
            (b'SYSGEN A: B:BASE090.SYS\r', b'A0>_ ', 90),
            (b'SYSGEN A: B:BASE090.SYS\r', b'Replace existing package (Y/N)?', 30),
            (b'N', b'A0>_ ', 30),
            (b'SYSGEN A: B:BASE090.SYS\r', b'Replace existing package (Y/N)?', 30),
            (b'Y', b'A0>_ ', 90),
            (b'B:\r', b'B0>_ ', 30),
            (b'A:SYSGEN A:\r', b'B0>_ ', 90),
            (b'A:\r', b'A0>_ ', 30),
            (b'SYSGEN B:BASE090.SYS C:\r', b'Proceed (Y/N)?', 30),
            (b'N', b'A0>_ ', 30),
            (b'BYE /Y\r', b'System halted', 30)], report/'export.txt')
        assert src.read_bytes() == original
        assert c.read_bytes() == old_c
        package_path = w/'BASE090.SYS'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),'0:BASE090.SYS',str(package_path)],cwd=w,check=True)
        package = package_path.read_bytes()
        raw = bytearray()
        for record in range(160):
            track, within = divmod(record, fmt.spt)
            at = track*fmt.raw_track_bytes+mapping[within]*128
            raw.extend(original[at:at+128])
        assert len(package) == 20608 and package[:10] == b'BCSY\x01\x01\xa0\x00\xc4\xd5'
        assert package[128:] == raw
        assert package[256:512] == saved
        assert transcript.count(b'Package exported and verified.') == 3
        default_path = w/'SYSTEM.SYS'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),'0:SYSTEM.SYS',str(default_path)],cwd=w,check=True)
        assert default_path.read_bytes() == package
        directory = subprocess.run(['cpmls','-T','raw','-f','bettercpm-default',str(b)],cwd=w,check=True,capture_output=True).stdout.lower()
        assert b'sysgen.$$$' not in directory and b'sysgen.bak' not in directory
        assert b'Replace existing package' in transcript
        installed = session(args.simulator, w/'disks', [
            (b'SYSGEN B:BASE090.SYS C:\r', b'Proceed (Y/N)?', 30),
            (b'Y', b'A0>_ ', 90),
            (b'BYE /Y\r', b'System halted', 30)], report/'install.txt')
        assert b'System installed and verified.' in installed
        assert src.read_bytes() == original
        # All target bytes outside represented system records are unchanged.
        masked = bytearray(c.read_bytes())
        for record in range(160):
            track, within = divmod(record, fmt.spt)
            at = track*fmt.raw_track_bytes+mapping[within]*128
            masked[at:at+128] = old_c[at:at+128]
        assert masked == old_c
        # SYSGEN preserves files; it does not install the command environment.
        # Supply the known filesystem separately for the cold-boot exercise.
        bootable = bytearray(c.read_bytes())
        filesystem = fmt.reserved_records*128
        bootable[filesystem:] = original[filesystem:]
        src.write_bytes(bootable)
        session(args.simulator, w/'disks', [(b'BYE /Y\r',b'System halted',30)], report/'cold-boot.txt')
    print('PASS: named export exact bytes/saved startup, replacement decline, named reinstall, filesystem preservation and cold boot')


if __name__ == '__main__':
    main()
