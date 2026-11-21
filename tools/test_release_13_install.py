#!/usr/bin/env python3
"""One SYSGEN install, populated-filesystem comparison and cold boot per System.

Use prepared final-media receipts. Operate only on newly created private copies;
this is a focused release gate, not the wider DUP/configuration campaign.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulator',type=Path)
    args = parser.parse_args()
    folder = args.system.resolve(); out = args.output.resolve()
    receipt = json.loads((folder/'report.json').read_text())
    original = folder/receipt['image']; master = original.read_bytes()
    assert digest(master) == receipt['sha256']
    target = receipt['target']
    assert target in ('z80pack','trs80gp','trs80m2'), 'unsupported System target'
    root = Path(receipt.get('build_root',folder))
    out.mkdir(parents=True,exist_ok=False)
    result = {'status':'RUNNING','source_commit':receipt['source']['revision'],
              'target':target,'system_sha256':digest(master),
              'scope':'one package install, entire populated filesystem preservation, independent cold boot, identity/memory/ordinary COM'}
    def save(): (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        if target == 'z80pack':
            from test_z80pack_sysgen_install import session
            assert args.simulator
            disks = out/'disks'; disks.mkdir()
            for letter in 'acd':
                data = master if letter == 'a' else (root/f'build/z80pack/disks/drive{letter}.dsk').read_bytes()
                (disks/f'drive{letter}.dsk').write_bytes(data)
            from fdf_format import select_fdf
            from build_z80pack_image import DEFAULT_FORMAT
            fmt = select_fdf(root/'metadata/DISK.FDF',DEFAULT_FORMAT)
            assert len(master) == fmt.image_bytes
            reserved = fmt.reserved_records*128
            before = b'\xe5'*reserved+master[reserved:]
            dest = disks/'driveb.dsk'; dest.write_bytes(before)
            steps = [(b'SYSGEN SYSTEM.SYS B:\r',b'Proceed (Y/N)?',60),
                     (b'Y',b'System installed and verified.',90),
                     (b'\r',b'A0> _ ',60)]
            install = session(args.simulator.resolve(),disks,steps,out/'install-transcript.txt')
            actual = dest.read_bytes()
            normalized = [(i,a,b) for i,(a,b) in enumerate(zip(master[:reserved],actual[:reserved])) if a!=b]
            # Established surface-track -> cylinder-track bootstrap binding.
            assert normalized == [(4952,36,72),(4965,6,3),(4970,0xc0,0xa0)], normalized
            assert actual[reserved:] == before[reserved:], 'filesystem modified'
            # Cold startup may create/delete $$$.SUB on this private boot copy.
            assert (disks/'drivea.dsk').read_bytes()[:reserved] == master[:reserved], 'source protected area modified'
            (disks/'drivea.dsk').write_bytes(actual)
            cold = session(args.simulator.resolve(),disks,
                           [(b'VER\r',b'A0> _ ',60),(b'STAT MEM\r',b'A0> _ ',60),
                            (b'STAT /VER\r',b'A0> _ ',60)],out/'cold-transcript.txt').decode(errors='replace')
            assert all(x in cold for x in ('1.3','57344 bytes','STAT 1.0')),cold[-3000:]
            # Cold startup may create/delete $$$.SUB on this private boot copy.
            assert (disks/'drivea.dsk').read_bytes()[:reserved] == actual[:reserved]
        else:
            from trs80gp_launch import run
            from run_trs80_command import DEFAULT_EMULATOR, key_args
            from test_sysgen_install import screen
            if target == 'trs80m2':
                from run_model2_qualification import EMU, EMU_SHA
                from test_model2_release_media import decoded, repack
                assert digest(EMU.read_bytes()) == EMU_SHA
                emulator = EMU; suffix = 'imd'; reserved = 26*128+3*16*512
                comment, tracks, reference = decoded(master)
                before = b'\xe5'*reserved+reference[reserved:]
                destination = repack(comment,tracks,before)
                source_bytes = master
                def raw(data): return decoded(data)[2]
            else:
                from add_cpm_file_to_dmk import extract_raw, add_file
                from build_montezuma_extended_790k import build
                import test_sysgen_install
                emulator = DEFAULT_EMULATOR; suffix = 'dmk'; reserved = 20480
                reference = bytes(extract_raw(master))
                before = b'\xe5'*reserved+reference[reserved:]
                destination = build(before)
                # An ephemeral helper selects a SYSTEM B: binding using the
                # existing Function 181 contract; no saved configuration change.
                test_sysgen_install.OUT = out
                source_raw = bytearray(reference)
                add_file(source_raw,'SETBSYS.COM',test_sysgen_install.setup_program())
                source_bytes = build(bytes(source_raw))
                def raw(data): return bytes(extract_raw(data))
            source = out/('source.'+suffix); source.write_bytes(source_bytes)
            dest = out/('installed.'+suffix); dest.write_bytes(destination)
            (out/('target-before.'+suffix)).write_bytes(destination)
            result['emulator_sha256'] = digest(emulator.read_bytes()); save()
            def phase(name,disk,second,actions):
                case = out/name; case.mkdir()
                command = [str(emulator),'-m2' if target=='trs80m2' else '-m4']
                if target == 'trs80m2': command += ['-mem','64']
                command += ['-batch','-turbo','-itime','0','-d0',str(disk)]
                if second: command += ['-d1',str(second)]
                command += ['-iw','A0>' if target=='trs80m2' else 'Type TYPE README.TXT','-id','3000','-it']
                for text, marker, delay in actions:
                    command += ['-i',text] if target=='trs80m2' else key_args(text,delay=25)
                    if marker: command += ['-it','-iw',marker]
                    command += ['-id',str(delay),'-it']
                command += ['-ix']
                (case/'arguments.json').write_text(json.dumps(command,indent=2)+'\n')
                run(command,cwd=case,timeout=240,check=True)
                captures = sorted(case.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
                texts = [screen(p) for p in captures]
                for p,text in zip(captures,texts): p.with_suffix('.txt').write_text(text+'\n')
                return '\n'.join(texts)
            actions = [] if target=='trs80m2' else [('SETBSYS\r','B SYSTEM READY',7000)]
            actions += [('SYSGEN SYSTEM.SYS B:\r','Proceed (Y/N)?',6500),
                        ('Y','System installed and verified',18000)]
            install = phase('install',source,dest,actions)
            assert 'System installed and verified' in install
            assert raw(source.read_bytes())[:reserved] == raw(source_bytes)[:reserved], 'source protected area modified'
            actual = raw(dest.read_bytes())
            assert actual[reserved:] == before[reserved:], 'filesystem modified'
            normalized = [(i,a,b) for i,(a,b) in enumerate(zip(reference[:reserved],actual[:reserved])) if a!=b]
            expected = [] if target=='trs80m2' else [(7018,0xe0,0xa0)]
            assert normalized == expected, ('unexpected protected-record difference',normalized)
            saved = dest.read_bytes()
            actions = [('VER\r','A0>',8000)]
            if target=='trs80gp': actions += [('RSX UNLOAD ADM3A\r','A0>',25000)]
            actions += [('STAT MEM\r',None,8000),('STAT /VER\r',None,8000)]
            cold = phase('cold',dest,None,actions)
            floor = '57344 bytes' if target=='trs80m2' else '54272 bytes'
            assert all(x in cold for x in ('1.3',floor,'STAT 1.0')), cold[-5000:]
            assert raw(dest.read_bytes())[:reserved] == raw(saved)[:reserved], 'cold boot modified protected records'
        assert original.read_bytes() == master, 'release master changed'
        result.update(status='PASS_FOCUSED_INSTALL',filesystem_unchanged=True,
                      populated_filesystem_sha256=digest(before[reserved:]),
                      installed_protected_sha256=digest(actual[:reserved]),
                      installed_raw_sha256=digest(actual),source_master_unchanged=True,
                      protected_normalization=normalized,
                      maximum_com=54272 if target=='trs80gp' else 57344,
                      cold_boot_identity_and_ordinary_com='PASS',maintainer_release_acceptance='PENDING')
        save(); print(target,result['status'])
    except Exception as error:
        result.update(status='FAIL',error=str(error));save();raise


if __name__ == '__main__': main()
