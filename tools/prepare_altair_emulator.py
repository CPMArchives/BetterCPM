#!/usr/bin/env python3
"""Build an isolated, serial-only Altair from a pinned local z80pack checkout."""
import argparse
import tarfile
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVISION = '91fd28eb04e675c2127df88ed3f40675e15282e2'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    inputs=p.add_mutually_exclusive_group()
    inputs.add_argument('--source', type=Path, help='pinned local Git checkout')
    inputs.add_argument('--archive', type=Path, help='verified offline archive; bundled archive is the default')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists():
        p.error('output exists; choose a fresh directory')
    revision=REVISION
    if a.source:
        source=a.source.resolve()
        revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
        if revision!=REVISION:p.error(f'expected z80pack {REVISION}, found {revision}')
        out.mkdir(parents=True)
        archive=subprocess.Popen(['git','-C',str(source),'archive',REVISION],stdout=subprocess.PIPE)
        result=subprocess.run(['tar','-xf','-','-C',str(out)],stdin=archive.stdout)
        archive.stdout.close()
        if archive.wait() or result.returncode:raise SystemExit('could not stage pinned emulator sources')
    else:
        manifest=json.loads((ROOT/'third_party/z80pack/altair-offline.json').read_text())
        archive=a.archive or ROOT/'third_party/z80pack/altair-offline.tar.gz'
        if manifest['revision']!=REVISION or hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['sha256']:
            p.error('offline archive does not match the pinned Altair source manifest')
        with tarfile.open(archive,'r:gz') as bundle:
            for member in bundle.getmembers():
                name=Path(member.name)
                if name.is_absolute() or '..' in name.parts or not (member.isfile() or member.isdir()):
                    p.error('unsafe offline archive member: '+member.name)
            out.mkdir(parents=True)
            bundle.extractall(out)
    shim = ROOT / 'tools/altair/no-video.c'
    shutil.copy2(shim, out / 'altairsim/srcsim/bettercpm-no-video.c')
    # Auxiliary socket endpoints are outside this serial-console target.
    # Removing their startup also keeps parallel tests from sharing sockets.
    io_path = out / 'altairsim/srcsim/simio.c'
    io = io_path.read_text()
    for index, name in enumerate(('altairsim.tape', 'altairsim.sio2')):
        before = f'init_unix_server_socket(&ucons[{index}], "{name}");'
        if io.count(before) != 1:
            raise ValueError('pinned auxiliary initialization changed')
        io = io.replace(before, f'ucons[{index}].ss = -1; ucons[{index}].ssc = 0;')
    for name in ('altair_sio3_status_in', 'altair_sio3_data_in',
                 'altair_sio2_status_in', 'altair_sio2_data_in'):
        io = io.replace('= ' + name + ',', '= bettercpm_absent_in,')
    for name in ('altair_sio3_status_out', 'altair_sio3_data_out',
                 'altair_sio2_status_out', 'altair_sio2_data_out'):
        io = io.replace('= ' + name + ',', '= bettercpm_absent_out,')
    io = io.replace('in_func_t *const port_in[256]',
                    'extern BYTE bettercpm_absent_in(void);\n'
                    'extern void bettercpm_absent_out(BYTE);\n'
                    'in_func_t *const port_in[256]')
    io_path.write_text(io)
    command = ['make', '-C', str(out / 'altairsim/srcsim'), '-j4',
               'FRONTPANEL=NO', 'INFOPANEL=NO', 'PLAT_LDLIBS=',
               'PLAT_LDFLAGS=', 'PLAT_INCS=',
               'IO_SRCS=bettercpm-no-video.c tarbell_fdc.c altair-88-dcdd.c '
               'altair-88-sio.c altair-88-2sio.c unix_terminal.c unix_network.c simbdos.c']
    with (out / 'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    binary = out / 'altairsim/altairsim'
    receipt = {'revision': revision, 'build': command, 'graphics': 'absent; access fails',
               'auxiliary_sockets': 'absent; access fails',
               'simio_sha256': hashlib.sha256(io_path.read_bytes()).hexdigest(),
               'shim_sha256': hashlib.sha256(shim.read_bytes()).hexdigest(),
               'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    (out / 'bettercpm-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(binary)


if __name__ == '__main__':
    main()
