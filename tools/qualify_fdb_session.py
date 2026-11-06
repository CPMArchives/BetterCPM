#!/usr/bin/env python3
"""Import into the stock catalogue and replace it on private platform media."""
from fdb_qualification_media import stage, startup, audit
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
    p.add_argument('--system-image', type=Path, help='complete shipped System image, with adjacent report.json')
    p.add_argument('--target', choices=('z80pack', 'trs80gp'), required=True)
    p.add_argument('--build-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--simulator', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--disk-full', action='store_true',
                   help='leave only one free allocation block and verify failed replacement')
    p.add_argument('--exchange', action='store_true',
                   help='inspect and export the pending entry before saving the session')
    p.add_argument('--details', action='store_true')
    p.add_argument('--config-read', action='store_true',
                   help='qualify entry 109 through CONFIG and a known file read')
    args = p.parse_args()
    if args.system_image and args.disk_full:
        p.error('disk-full uses its dedicated controlled allocation fixture')
    if args.config_read and (args.exchange or args.disk_full):
        p.error('CONFIG read is a separate acceptance case')
    if args.exchange and args.disk_full:
        p.error('exchange requires space for its output files')
    root = args.build_root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True)
    stock = catalogue_payload()
    entries = parse(decompile(stock))
    new = replace(entries[0], ident='TEST109', description='New test definition')
    if args.config_read:
        source_id = 'MMF017' if args.target == 'z80pack' else 'BCPM780'
        base = next(entry for entry in entries if entry.ident == source_id)
        new = replace(base, ident='TEST109', description='FDB Gate 109')
    single = serialize((new,))
    expected = serialize((*entries, new))
    names = [('FDB.COM', build(destination=out)), ('DISK.FDB', stock),
             ('ADD.FDB', single), ('RCP.CPX', (root/'build/cpx/RCP.CPX').read_bytes())]
    if args.target == 'z80pack':
        names.append(('BYE.COM', (root/'build/z80pack-tools/BYE.COM').read_bytes()))
    if args.exchange:
        names.append(('TARGET.FDB', serialize((entries[0],))))
    if args.details:
        names.append(('FDBVIEW.OVL',(out/'FDBVIEW.OVL').read_bytes()))
    if args.config_read:
        from build_config import expanded_source, validate_layout
        from build_ccp import assemble
        config = assemble(Path.home()/'bin/z80asm', expanded_source(root),
                          out/'CONFIG.COM',out/'config.lst',0x100)
        validate_layout(config,(out/'config.lst').read_text())
        names += [('CONFIG.COM',config),
                  ('TYPE.COM',(root/'build/utilities/TYPE.COM').read_bytes()),
                  ('KNOWN.TXT',b'FDB GATE FILE READ PASS\r\n\x1a')]
    files = [({'name': name, 'user': 0}, data) for name, data in names]
    g = geometry(args.target, root)
    if args.disk_full:
        free = capacity(files, g)['free_bytes']
        files.append(({'name':'FILL.BIN', 'user':0}, bytes(free - g['block'])))
    raw = construct(args.target, root, out, files, g, '')
    stage(args.target,raw,args.system_image,names,out)
    steps = [('FDB', 'Your choice: [ ]'), ('I', 'Source .FDB or .FDF: '),
             ('ADD.FDB', 'entire catalogue): '), ('TEST109', '1 added, 0 replaced.'),
             ('S', 'displayed default): '), ('', 'Replace entire file (Y/N)? '),
             ('Y', 'Catalogue saved and verified.'), ('Q', 'A0>')]
    if args.details:
        steps[4:4] = [('D','Source: catalogue ID,'), ('MMI012','Q or BREAK Return:'),
                      ('4','Q or BREAK Return:'), ('Q','Your choice: [ ]'),
                      ('P','Source: catalogue ID,'), ('MMI012','Source: catalogue ID,'),
                      ('MMI012','Q or BREAK Return:'), ('4','Q or BREAK Return:'),
                      ('A','Q or BREAK Return:'), ('Q','Your choice: [ ]'),
                      ('P','Source: catalogue ID,'), (':B','Source: catalogue ID,'),
                      (':C','Q or BREAK Return:'), ('4','Q or BREAK Return:'),
                      ('A','Q or BREAK Return:'), ('Q','Your choice: [ ]'),
                      ('B','Source filename'), ('','Catalogue ID:'), ('MMI012','Q Back:'),
                      ('Q','Your choice: [ ]'), ('D','Source: catalogue ID,'), ('@','Q or BREAK Return:'),
                      ('4','Q or BREAK Return:'), ('Q','Your choice: [ ]'),
                      ('D','Source: catalogue ID,'), ('/','Source .FDB filename:'),
                      ('DISK.FDB','Working catalogue ID:'), ('MMI012','Q or BREAK Return:'),
                      ('Q','Your choice: [ ]')]
    if args.details:
        # The loaded pristine editor remains available. Choose W at S.
        at = next(i for i,step in enumerate(steps) if step == ('S','displayed default): '))
        steps[at:at+1] = [('S','other Cancel:'),('W','displayed default): ')]
    if args.exchange:
        steps[4:4] = [('L', 'capacity in bytes): '), ('test109', 'Your choice: [ ]'),
                      ('O', 'working catalogue): '), ('TEST109', 'or .FDF: '),
                      ('TARGET.FDB', 'Replace entire file (Y/N)? '), ('Y','TARGET.FDB exported and verified.'),
                      ('O', 'working catalogue): '), ('', 'or .FDF: '),
                      ('ALL.FDF', 'Create new file (Y/N)? '), ('Y','ALL.FDF exported and verified.')]
    if args.config_read:
        steps += [('CONFIG /LOGICAL=B /PHYSICAL=0 /FORMAT="FDB Gate 109"', 'A0>'),
                  ('TYPE B:KNOWN.TXT', 'FDB GATE FILE READ PASS')]
    if args.disk_full:
        steps[-2:] = [('Y', 'file operation failed'), ('Q', 'C Cancel: '), ('D', 'A0>')]
    steps = startup(args.target,args.system_image) + steps
    if args.target == 'z80pack':
        disks = out/'disks'
        disks.mkdir()
        after = disks/'drivea.dsk'
        shutil.copy2(raw, after)
        session(args.simulator.resolve(), disks,
                [((k+'\r').encode(), (b'A0>_ ' if message=='A0>' else message.encode()), 45) for k, message in steps] +
                [(b'BYE /Y\r', b'System halted', 15)], out/'transcript.bin')
    else:
        disk = out/'session.dmk'
        disk.write_bytes(make_dmk(raw.read_bytes()))
        cmd = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo', '-d0', str(disk),
               '-id', '3000', '-itime', '0']
        if args.system_image:
            cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),
                 '-id','4000','-itime','15000','-iw','Type TYPE README.TXT for more','-id','4000']
        if args.disk_full:
            # Capture the failed save while the modified session is still live.
            # Inspect its directory after shutdown, before issuing another command.
            steps = steps[:-3] + [('Y', 'FDB: file operation failed.')]
        for keys, message in steps:
            cmd += key_args(keys+'\r') + ['-iw', ('A0> ' if message=='A0>' else message.rstrip()), '-id', '3000' if message=='A0>' else '200'] + (['-it'] if args.system_image else [])
        run(cmd + ['-id', '4000' if args.disk_full else '60', '-it', '-ix'], cwd=out, check=True, timeout=900 if args.system_image else 240)
        if args.disk_full:
            snapshot = screen(next(out.glob('trs80-text-*.bin')))
            assert 'FDB: file operation failed.' in snapshot
            current_menu = snapshot.rsplit('FDB: file operation failed.', 1)[1]
            assert '109   Modified' in current_menu and current_menu.rstrip().endswith('Your choice: [ ]')
        after = out/'after.raw'
        after.write_bytes(extract_raw(disk.read_bytes()))
    audit(args.target,args.system_image,after,out,('DISK.FDB',))
    if args.config_read:
        transcript = ((out/'transcript.bin').read_bytes().decode('ascii', 'replace')
                      if args.target == 'z80pack' else
                      '\n'.join(screen(p) for p in out.glob('trs80-text-*.bin')))
        assert 'Disk configuration changed (until cold boot).' in transcript
        assert 'FDB GATE FILE READ PASS' in transcript
        assert 'Nothing changed.' not in transcript
        # The cold-boot carrier and startup defaults occupy reserved tracks.
        assert after.read_bytes()[:g['reserved']] == raw.read_bytes()[:g['reserved']]
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
              'config_file_read':args.config_read, 'source_preserved':True, 'com_sha256':sha(names[0][1]), 'com_bytes':len(names[0][1])}
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', report)


if __name__ == '__main__':
    main()
