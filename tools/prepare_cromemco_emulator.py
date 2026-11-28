#!/usr/bin/env python3
"""Build a private serial Cromemco emulator from pinned, committed z80pack sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
REVISION = '91fd28eb04e675c2127df88ed3f40675e15282e2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs=parser.add_mutually_exclusive_group()
    inputs.add_argument('--source', type=Path, help='exact pinned local Git checkout')
    inputs.add_argument('--archive', type=Path, help='verified offline archive; bundled sources are the default')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    revision = REVISION
    if out.exists():
        parser.error('output exists; choose a fresh directory')
    out.mkdir(parents=True)
    if args.source:
        source=args.source.resolve()
        revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
        if revision!=REVISION:
            parser.error(f'expected {REVISION}, found {revision}')
        archive=subprocess.Popen(['git','-C',str(source),'archive',REVISION],stdout=subprocess.PIPE)
        result=subprocess.run(['tar','-xf','-','-C',str(out)],stdin=archive.stdout)
        archive.stdout.close()
        if archive.wait() or result.returncode:
            raise SystemExit('could not stage committed emulator sources')
    else:
        manifest=json.loads((ROOT/'third_party/z80pack/cromemco-offline.json').read_text())
        archive=args.archive or ROOT/'third_party/z80pack/cromemco-offline.tar.gz'
        if manifest['revision']!=REVISION or hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['sha256']:
            parser.error('offline sources do not match the pinned manifest')
        with tarfile.open(archive,'r:gz') as bundle:
            for member in bundle.getmembers():
                name=Path(member.name)
                if name.is_absolute() or '..' in name.parts or not (member.isfile() or member.isdir()):
                    parser.error('unsafe offline archive member: '+member.name)
            bundle.extractall(out)
    sim = out / 'cromemcosim/srcsim'
    # Exclude optional host services; preserve CPU, MMU, ROM, UART and FDC code.
    config = sim / 'sim.h'
    text = config.read_text()
    for name in ('HAS_NETSERVER', 'HAS_MODEM'):
        before = '#define ' + name
        if text.count(before) != 1:
            raise ValueError('pinned emulator configuration changed: ' + name)
        text = text.replace(before, '// ' + before)
    config.write_text(text)
    io = sim / 'simio.c'
    text = io.read_text()
    before = 'init_tcp_server_socket(&ncons[i]);'
    if text.count(before) != 1:
        raise ValueError('pinned socket initialization changed')
    io.write_text(text.replace(before, 'ncons[i].ss = -1; ncons[i].ssc = 0;'))
    # A one-byte read into an uninitialized int leaves the upper bytes
    # indeterminate. HAL treats negative ints as "no character", dropping
    # valid keystrokes depending on the host stack contents and launch path.
    hal = out / 'iodevices/cromemco-hal.c'
    text = hal.read_text()
    before = 'static int stdio_in(int dev)\n{\n\tint data;'
    if text.count(before) != 1:
        raise ValueError('pinned UART stdio input changed')
    hal.write_text(text.replace(before, 'static int stdio_in(int dev)\n{\n\tBYTE data;'))
    shim = ROOT / 'tools/cromemco/no-video.c'
    shutil.copy2(shim, sim / 'bettercpm-no-video.c')
    command = ['make', '-C', str(sim), '-j4', 'FRONTPANEL=NO', 'INFOPANEL=NO',
               'CIV_LIB=', 'CIV_LDLIBS=', 'PLAT_INCS=', 'PLAT_LDFLAGS=', 'PLAT_LDLIBS=',
               'IO_SRCS=bettercpm-no-video.c cromemco-wdi.c cromemco-d+7a.c '
               'cromemco-fdc.c cromemco-tu-art.c cromemco-hal.c unix_terminal.c '
               'unix_network.c simbdos.c diskmanager.c']
    with (out / 'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    binary = out / 'cromemcosim/cromemcosim'
    receipt = {'revision': revision, 'build': command,
               'scope': 'serial console, banked ROM and floppy controller; no network or graphics',
               'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'modified_sources': {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in (config, io, hal, sim / 'bettercpm-no-video.c')}}
    (out / 'bettercpm-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(binary)


if __name__ == '__main__':
    main()
