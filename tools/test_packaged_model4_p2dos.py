#!/usr/bin/env python3
"""Run the optional A0 clock carriers on a disposable copy of a prepared Model 4 image."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_z80pack_image import disk_definition
from convert_fdf_image import dmk_to_raw, raw_to_dmk
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_z80pack_clock_lifecycle import PROBE
from trs80gp_launch import run


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_lifecycle(screens):
    """Check each transition using the output for that stage only."""
    assert 'No TIME provider is loaded' in screens[1]
    assert 'FREHDCLK' not in screens[1] and 'P2DOS' not in screens[1]
    assert 'Provider: FREHDCLK' in screens[2]
    assert re.search(r'(?m)^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', screens[2])
    assert 'B:WBOOT' in screens[3]
    after_removal = screens[4].rsplit('A0>RSX UNLOAD FREHDCLK', 1)[-1]
    assert 'No TIME provider is loaded' in after_removal
    listing = after_removal.split('A0>RSX LIST', 1)[1].split('A0>B:CK4', 1)[0]
    assert 'P2DOS' in listing and 'FREHDCLK' not in listing
    assert 'Provider: FREHDCLK' in screens[5].rsplit('A0>RSX LOAD FREHDCLK', 1)[-1]
    assert 'Provider: FREHDCLK' in screens[6].rsplit('A0>RSX UNLOAD P2DOS', 1)[-1]


def qualify(image_dir, work, emulator):
    work.mkdir(parents=True, exist_ok=False)
    report = json.loads((image_dir/'report.json').read_text())
    image = image_dir/report['image']
    original = image.read_bytes()
    assert report['target'] == 'trs80gp' and sha(original) == report['sha256']
    (work/'a.dmk').write_bytes(original)
    (work/'system.raw').write_bytes(extract_raw(original))
    shutil.copyfile(image_dir/'diskdefs', work/'diskdefs')
    carriers = {}
    for name in ('P2DOS.RSX', 'FREHDCLK.RSX', 'TIME.COM', 'STARTUP.SUB'):
        row = next(r for r in report['included'] if r['name'] == name and r['user'] == 0)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default','system.raw','0:'+name,name],
                       cwd=work, check=True)
        body = (work/name).read_bytes()[:row['bytes']]
        assert sha(body) == row['sha256']
        carriers[name] = sha(body)
        if name == 'STARTUP.SUB':
            assert b'P2DOS' not in body.upper() and b'FREHDCLK' not in body.upper()

    root = Path(__file__).resolve().parents[1]
    fmt = select_fdf(root/'metadata/DISK.FDF', 'MMI008')
    (work/'diskdefs').write_text(disk_definition(fmt))
    work_image = (image_dir/'work-image').read_bytes()
    assert sha(work_image) == report['work_image_sha256']
    (work/'work.raw').write_bytes(dmk_to_raw(work_image, fmt))
    commands = ['RSX LIST','TIME /PROVIDER']
    stages = []
    probes = {}
    def stage(label, mode):
        # Give each invocation a unique result string so old screen text cannot pass.
        name = 'CK' + str(len(stages)+1)
        marker = name + ' ABI PASS'
        binary = work/(name+'.COM')
        source = PROBE.replace('CLOCK ABI PASS', marker)
        assemble(Path.home()/'bin/z80asm', source, binary, work/(name+'.lst'), 0x100)
        probes[name] = sha(binary.read_bytes())
        commands.append(f'B:{name} {mode}')
        stages.append((label, marker))
    stage('cold frontend absent', 2)
    commands.extend(['RSX LOAD FREHDCLK','RSX LOAD P2DOS','TIME /PROVIDER','TIME'])
    stage('loaded', 0)
    # Release A: omits the development WARM.COM. Request BDOS function 0
    # explicitly from a diagnostic on B: without adding anything to A:.
    warm = work/'WBOOT.COM'
    assemble(Path.home()/'bin/z80asm', '        ASEG\n        ORG 100H\n        LD C,0\n        JP 5\n        END\n',
             warm, work/'WBOOT.lst', 0x100)
    commands.append('B:WBOOT')
    stage('after explicit warm boot', 0)
    commands.extend(['RSX UNLOAD FREHDCLK','TIME /PROVIDER','RSX LIST'])
    stage('provider absent, frontend resident', 1)
    commands.extend(['RSX LOAD FREHDCLK','TIME /PROVIDER'])
    stage('provider reloaded, same frontend', 0)
    commands.extend(['RSX UNLOAD P2DOS','TIME /PROVIDER'])
    stage('frontend removed, provider resident', 2)
    (work/'P2QUAL.SUB').write_bytes(('\r\n'.join(commands)+'\r\n\x1a').encode())
    for path in [work/(name+'.COM') for name in probes]+[warm, work/'P2QUAL.SUB']:
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-mm-80t-ds-data','work.raw',
                        path,'0:'+path.name],cwd=work,check=True)
    disk = work/'b.dmk'
    disk.write_bytes(raw_to_dmk((work/'work.raw').read_bytes(),fmt))
    probe_disk_sha = sha(disk.read_bytes())
    (work/'frehd').mkdir()
    cmd = [str(emulator),'-m4','-batch','-turbo','-ktx','-frehd_dir',str(work/'frehd'),
           '-d0',str(work/'a.dmk'),'-d1',str(disk),'-itime','40000',
           '-iw','Type TYPE README.TXT for more','-id','6000','-it']
    cmd += key_args('SUBMIT B:P2QUAL\r',delay=40)
    for _, marker in stages:
        cmd += ['-iw',marker,'-it']
    run(cmd+['-id','2000','-it','-ix'],cwd=work,timeout=900)
    screens = []
    captures = {}
    for i in range(len(stages)+2):
        capture = work/f'trs80-text-{i}.bin'
        data = capture.read_bytes()
        captures[capture.name] = sha(data)
        raw = data[:1920]
        screens.append('\n'.join(bytes(c&127 for c in raw[j:j+80]).decode('ascii').rstrip()
                                  for j in range(0,1920,80)).strip())
    for i, (_, marker) in enumerate(stages,1):
        assert marker in screens[i].splitlines(), marker
    verify_lifecycle(screens)
    assert original == image.read_bytes() and sha(disk.read_bytes()) == probe_disk_sha
    result=dict(status='PASS', source_commit=report['source']['revision'], image=image.name,
                system_sha256=sha(original), carriers=carriers, probe_sha256=probes,
                emulator_sha256=sha(emulator.read_bytes()), commands=commands, stages=stages,
                screens=screens, capture_sha256=captures, work_disk_sha256=probe_disk_sha,
                warm_probe_sha256=sha(warm.read_bytes()), script_sha256=sha((work/'P2QUAL.SUB').read_bytes()))
    (work/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: six Model 4 P2DOS lifecycle stages')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    args=parser.parse_args()
    qualify(args.image_dir.resolve(),args.output.resolve(),args.emulator.resolve())
