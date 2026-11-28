#!/usr/bin/env python3
"""Bundle the verified Cromemco engineering image for macOS Apple Silicon."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--emulator-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--system-result', type=Path,
                        help='retained passing system receipt for this candidate')
    parser.add_argument('--hardware-result', type=Path,
                        help='retained passing hardware receipt for this emulator')
    args = parser.parse_args()
    image, emulator = args.image_dir.resolve(), args.emulator_root.resolve()
    output = args.output.resolve()
    evidence = ROOT / 'docs/engineering/evidence/cromemco'
    system_result = args.system_result or evidence / 'system-result.json'
    report = json.loads(system_result.read_text())
    hardware_result = args.hardware_result or evidence / 'hardware-result.json'
    hardware = json.loads(hardware_result.read_text())
    candidate = json.loads((image / 'candidate.json').read_text())
    binary = emulator / 'cromemcosim/cromemcosim'
    if (report['status'] != 'PASS' or hardware['status'] != 'PASS' or
            report['candidate'] != candidate or
            sha(binary) != report['emulator_sha256'] or
            sha(binary) != hardware['emulator_sha256']):
        parser.error('inputs do not match the retained passing engineering evidence')
    if 'arm64' not in subprocess.check_output(['file', str(binary)], text=True):
        parser.error('this package requires the tested macOS arm64 emulator')
    output.mkdir(parents=True, exist_ok=False)
    bundle = output / 'BetterCPM-Cromemco-Engineering-macOS-arm64'
    (bundle / 'Host/roms').mkdir(parents=True)
    (bundle / 'Source').mkdir()
    shutil.copytree(image / 'disks', bundle / 'Media')
    shutil.copy2(binary, bundle / 'Host/cromemcosim')
    for name in ('rdos252.hex', 'rdos252.asm'):
        shutil.copy2(emulator / 'cromemcosim/roms' / name, bundle / 'Host/roms' / name)
    for name in ('system.conf', 'diskdefs', 'candidate.json'):
        shutil.copy2(image / name, bundle / name)
    shutil.copy2(ROOT / 'LICENSE', bundle / 'Source/BetterCPM-LICENSE.txt')
    shutil.copy2(emulator / 'LICENSE', bundle / 'Source/z80pack-LICENSE.txt')
    shutil.copytree(evidence, bundle / 'Evidence')
    shutil.copy2(system_result, bundle / 'Evidence/system-result.json')
    shutil.copy2(hardware_result, bundle / 'Evidence/hardware-result.json')
    shutil.copy2(emulator / 'bettercpm-build.json', bundle / 'Evidence/emulator-build.json')
    with (bundle / 'Source/BetterCPM-source.tar.gz').open('wb') as stream:
        subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar.gz', 'HEAD',
                        'src', 'tools', 'metadata', 'third_party', 'LICENSE', 'LICENSES',
                        'README.md', 'docs/LICENSING.md', 'docs/SOURCE-BUILD.md'],
                       stdout=stream, check=True)
    # Preserve the exact modified host source used to build the emulator.
    def source_only(member):
        return None if Path(member.name).suffix in ('.o', '.d', '.a') else member
    with tarfile.open(bundle / 'Source/Emulator-sources.tar.gz', 'w:gz') as archive:
        for name in ('cromemcosim/srcsim', 'cromemcosim/roms/rdos252.asm',
                     'cromemcosim/roms/rdos252.hex', 'z80core', 'iodevices',
                     'frontpanel', 'LICENSE', 'README.md', 'HISTORY',
                     'bettercpm-build.json', 'build.log'):
            archive.add(emulator / name, arcname=name, filter=source_only)
    launcher = bundle / 'Run-Cromemco.command'
    launcher.write_text('''#!/bin/zsh
set -eu
bundle_root="$(cd "$(dirname "$0")" && pwd)"
cd "$bundle_root"
exec "$bundle_root/Host/cromemcosim" -z -R -M1 -f0 \\
  -r "$bundle_root/Host/roms" -c "$bundle_root/system.conf" -d "$bundle_root/Media"
''')
    launcher.chmod(0o755)
    (bundle / 'README.txt').write_text('''BetterCP/M Cromemco engineering package — macOS Apple Silicon

1. Unzip the entire package anywhere you like.
2. Open that folder and double-click Run-Cromemco.command.
   It finds its own files; no Terminal working directory or Python is required.
3. Wait for RDOS to boot and the A0> prompt to appear.

Try VER, DIR, or STAT MEM. Enter BYE to close the emulator.
The launcher also works from Terminal using its full path, from any directory.

This is the tested initial engineering collection, not the full System and
Utilities release. It includes four writable 8-inch single-density disks,
the emulator, RDOS boot ROM, source/licensing material, and acceptance evidence.
The host serial reader includes the correction for discarded keystrokes.
The verified unloaded COM capacity is 57,344 bytes. The serial console is timed;
wait for redraws when entering commands. Keep Host, Media and system.conf with
the launcher. Disk changes persist in Media; unzip a fresh copy to reset them.

Complete release utilities, display personalities, installation qualification,
broader compatibility testing and publication are still pending.

Evidence/system-result.json, hardware-result.json and emulator-build.json
describe this bundle. Nested evidence archives retain earlier checkpoints.

Emulator source rebuild (after extracting Source/Emulator-sources.tar.gz):
make -C cromemcosim/srcsim -j4 FRONTPANEL=NO INFOPANEL=NO CIV_LIB= CIV_LDLIBS= \\
  PLAT_INCS= PLAT_LDFLAGS= PLAT_LDLIBS= \\
  'IO_SRCS=bettercpm-no-video.c cromemco-wdi.c cromemco-d+7a.c cromemco-fdc.c cromemco-tu-art.c cromemco-hal.c unix_terminal.c unix_network.c simbdos.c diskmanager.c'
''')
    files = {str(p.relative_to(bundle)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(bundle.rglob('*')) if p.is_file()}
    (bundle / 'PACKAGE.json').write_text(json.dumps({
        'status': 'engineering collection; not a qualified full release',
        'host': 'macOS arm64', 'source_commit': subprocess.check_output(
            ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'files': files}, indent=2) + '\n')
    destination = output / (bundle.name + '.zip')
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(output))
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
    print(destination)


if __name__ == '__main__':
    main()
