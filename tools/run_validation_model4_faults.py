#!/usr/bin/env python3
"""Native final-BIOS suspension/Ignore/abort with independent recovery checks."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from add_cpm_file_to_dmk import add_file, extract_raw, DIRECTORY_ENTRIES, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_model4 import sha, audit_files
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_sysgen_install import screen
from trs80gp_launch import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('baseline', 'output'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args()
    w = a.output.resolve()
    w.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    shutil.copy2(__file__, w / 'executed-runner.py')
    binaries = {}
    for source, name in [('faultmore.mac','FAULTIO'),('returnstate.mac','STATE')]:
        text = (root / 'tests/fixtures/conformance' / source).read_text()
        (w / source).write_text(text)
        binaries[name] = assemble(Path.home()/'bin/z80asm',text,w/(name+'.COM'),w/(name+'.lst'),0x100)
    healthy = b'HEALTHY READ AFTER ABORT\r\n\x1a'.ljust(128,b'\x1a')
    cases = {}
    for scenario in ('suspended','ignore','abort'):
        out = w / scenario
        out.mkdir()
        raw = extract_raw(original.read_bytes())
        for i in range(DIRECTORY_ENTRIES):
            at = FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE + i*32
            if raw[at] == 0 and raw[at+1:at+12] == b'STARTUP SUB':
                raw[at] = 229
        add_file(raw,'STARTUP.SUB',b':VER /BANNER\r\nFAULTIO\r\nTYPE BTONE.DAT\r\nSTATE\r\n\x1a')
        for name, code in binaries.items():
            add_file(raw,name+'.COM',code)
        add_file(raw,'BTONE.DAT',healthy)
        (out/'before.raw').write_bytes(raw)
        image = out/'a.dmk'
        image.write_bytes(build(bytes(raw)))
        command = [str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),
                   '-itime','15000','-iw','Healthy file read passed; inject final BIOS errors.',
                   '-iw','Bad Sector','-id','120','-it']
        if scenario == 'suspended':
            command += ['-id','1200','-it','-ix']
        elif scenario == 'ignore':
            command += key_args('I',delay=60)+['-iw','READ CALLER RESUMED after operator ignore.',
                        '-id','120','-it']+key_args('I',delay=60)
            command += ['-iw','FAULT PROVIDER COMPLETED BOTH CALLS','-id','120','-it',
                        '-iw','STATE D=00 U=00 TOP=D501','-id','120','-it','-ix']
        else:
            command += key_args('\x03',delay=60)+['-iw','HEALTHY READ AFTER ABORT',
                        '-iw','STATE D=00 U=00 TOP=D501','-id','120','-it','-ix']
        (out/'invocation.json').write_text(json.dumps(command,indent=2)+'\n')
        run(command,cwd=out,timeout=360)
        texts = [screen(p) for p in sorted(out.glob('trs80-text-*.bin'))]
        (out/'screens.txt').write_text('\n\n--- capture ---\n\n'.join(texts)+'\n')
        assert 'Bad Sector' in texts[0]
        assert not any('SETUP OR PROVIDER COUNT FAILED' in t for t in texts)
        if scenario == 'suspended':
            assert 'Bad Sector' in texts[-1]
            assert not any('READ CALLER RESUMED' in t or 'STATE D=' in t for t in texts)
        elif scenario == 'ignore':
            assert any('READ CALLER RESUMED' in t for t in texts)
            assert any('WRITE CALLER RESUMED' in t and 'FAULT PROVIDER COMPLETED BOTH CALLS' in t for t in texts)
            assert 'STATE D=00 U=00 TOP=D501' in texts[-1]
        else:
            assert not any('READ CALLER RESUMED' in t or 'WRITE CALLER RESUMED' in t for t in texts)
            assert 'HEALTHY READ AFTER ABORT' in texts[-1] and 'STATE D=00 U=00 TOP=D501' in texts[-1]
        after = extract_raw(image.read_bytes())
        (out/'after.raw').write_bytes(after)
        assert after[:20480] == raw[:20480]
        adjusted = dict(report,included=[f for f in report['included'] if f['name'] != 'STARTUP.SUB'])
        audit = audit_files(original,image,adjusted,out)
        folder = out/'file-audit'
        checked = subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',
                                  str(folder/'after.raw')],cwd=folder,capture_output=True)
        (folder/'filesystem.txt').write_bytes(checked.stdout+checked.stderr)
        assert checked.returncode == 0
        extracted = out/'healthy-after.bin'
        subprocess.run(['cpmcp','-T','raw,pcw800','-f','bettercpm-default',str(folder/'after.raw'),
                        '0:BTONE.DAT',str(extracted)],cwd=folder,check=True)
        assert extracted.read_bytes().startswith(healthy.split(b'\x1a')[0])
        cases[scenario] = {'status':'PASS','capture_sha256':[sha(p) for p in sorted(out.glob('trs80-text-*.bin'))],
                           'file_audit':audit,'filesystem_status':checked.returncode}
        print(scenario,'PASS',flush=True)
    assert sha(original) == report['sha256']
    result = {'status':'PASS','baseline_sha256':report['sha256'],'emulator_sha256':sha(DEFAULT_EMULATOR),
              'cases':cases,'runner_sha256':sha(w/'executed-runner.py'),
              'provider_sha256':sha(w/'FAULTIO.COM'),
              'cards':['0394','0395','0396','0397','0581','0586','0587'],
              'scope':'Native one-shot final-BIOS read/write failures: pending caller, Ignore, Control-C abandonment, healthy BDOS read and queried A0/53K recovery. Private startup queue and supplemental witnesses; no physical-controller retry or ignored-data guarantee.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS native physical-error operator boundary',w)


if __name__ == '__main__':
    main()
