#!/usr/bin/env python3
"""Import into the stock catalogue and replace it on private platform media."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess

from add_cpm_file_to_dmk import extract_raw
from build_distribution import capacity, construct, geometry
from build_fdb import build
from build_fdf_catalog import catalogue_payload
from build_montezuma_extended_790k import build as make_dmk
from fdfdecomp import decompile
from fdf_v1 import parse, serialize
from qualify_fdb_roundtrip import sha
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_z80pack_sysgen_install import session
from trs80gp_launch import run
from test_sysgen_install import screen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=('z80pack', 'trs80gp'), required=True)
    p.add_argument('--build-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--simulator', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--disk-full', action='store_true',
                   help='leave only one free allocation block and verify failed replacement')
    p.add_argument('--exchange', action='store_true',
                   help='inspect and export the pending entry before saving the session')
    args = p.parse_args()
    if args.exchange and args.disk_full:
        p.error('exchange requires space for its output files')
    root = args.build_root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True)
    stock = catalogue_payload()
    entries = parse(decompile(stock))
    new = replace(entries[0], ident='TEST109', description='New test definition')
    single = serialize((new,))
    expected = serialize((*entries, new))
    names = [('FDB.COM', build(destination=out)), ('DISK.FDB', stock),
             ('ADD.FDB', single), ('RCP.CPX', (root/'build/cpx/RCP.CPX').read_bytes())]
    if args.target == 'z80pack':
        names.append(('BYE.COM', (root/'build/z80pack-tools/BYE.COM').read_bytes()))
    if args.exchange:
        names.append(('TARGET.FDB', serialize((entries[0],))))
    files = [({'name': name, 'user': 0}, data) for name, data in names]
    g = geometry(args.target, root)
    if args.disk_full:
        free = capacity(files, g)['free_bytes']
        files.append(({'name':'FILL.BIN', 'user':0}, bytes(free - g['block'])))
    raw = construct(args.target, root, out, files, g, '')
    steps = [('FDB', 'Choice: '), ('I', 'Source .FDB or .FDF: '),
             ('ADD.FDB', 'entire catalogue): '), ('TEST109', '1 added, 0 replaced.'),
             ('S', 'displayed default): '), ('', 'Replace entire file (Y/N)? '),
             ('Y', 'Catalogue saved and verified.'), ('Q', 'A0>')]
    if args.exchange:
        steps[4:4] = [('L', 'capacity in bytes): '), ('test109', 'Choice: '),
                      ('O', 'working catalogue): '), ('TEST109', 'or .FDF: '),
                      ('TARGET.FDB', 'Replace entire file (Y/N)? '), ('Y','TARGET.FDB exported and verified.'),
                      ('O', 'working catalogue): '), ('', 'or .FDF: '),
                      ('ALL.FDF', 'Create new file (Y/N)? '), ('Y','ALL.FDF exported and verified.')]
    if args.disk_full:
        steps[-2:] = [('Y', 'file operation failed'), ('Q', 'C Cancel: '), ('D', 'A0>')]
    if args.target == 'z80pack':
        disks = out/'disks'
        disks.mkdir()
        after = disks/'drivea.dsk'
        shutil.copy2(raw, after)
        session(args.simulator.resolve(), disks,
                [((k+'\r').encode(), message.encode(), 45) for k, message in steps] +
                [(b'BYE /Y\r', b'System halted', 15)], out/'transcript.bin')
    else:
        disk = out/'session.dmk'
        disk.write_bytes(make_dmk(raw.read_bytes()))
        cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk),
               '-id', '3000', '-itime', '0']
        if args.disk_full:
            # Capture the failed save while the modified session is still live.
            # Inspect its directory after shutdown, before issuing another command.
            steps = steps[:-3] + [('Y', 'FDB: file operation failed.')]
        for keys, message in steps:
            cmd += key_args(keys+'\r') + ['-iw', message.rstrip(), '-id', '60']
        run(cmd + ['-id', '4000' if args.disk_full else '60', '-it', '-ix'], cwd=out, check=True, timeout=240)
        if args.disk_full:
            snapshot = screen(next(out.glob('trs80-text-*.bin')))
            assert 'FDB: file operation failed.' in snapshot
            current_menu = snapshot.rsplit('FDB: file operation failed.', 1)[1]
            assert '109   Modified' in current_menu and current_menu.rstrip().endswith('Choice:')
        after = out/'after.raw'
        after.write_bytes(extract_raw(disk.read_bytes()))
    for name, wanted in [('DISK.FDB', stock if args.disk_full else expected), ('ADD.FDB', single)]:
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(after),
                        '0:'+name, str(out/name)], check=True, cwd=out)
        assert (out/name).read_bytes() == wanted, name
    if args.exchange:
        for name in ('TARGET.FDB','ALL.FDF'):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(after),
                            '0:'+name,str(out/name)],cwd=out,check=True)
        assert (out/'TARGET.FDB').read_bytes() == serialize((entries[0],new))
        assert serialize(parse((out/'ALL.FDF').read_bytes().split(b'\x1a')[0].decode())) == expected
    listing = subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(after)], cwd=out).upper()
    assert b'DISK.BAK' not in listing and b'DISK.$$$' not in listing
    report = {'target':args.target, 'entries':108 if args.disk_full else 109, 'disk_full':args.disk_full,
              'catalogue_sha256':sha((out/'DISK.FDB').read_bytes()),
              'source_preserved':True, 'com_sha256':sha(names[0][1]), 'com_bytes':len(names[0][1])}
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', report)


if __name__ == '__main__':
    main()
