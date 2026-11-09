#!/usr/bin/env python3
"""Check full-screen HELP with the packaged Model 4 and Model II System disks."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from run_trs80_command import key_args
from test_sysgen_install import screen
from trs80gp_launch import run


def qualify(model, image, emulator, folder):
    folder.mkdir()
    disk = folder/image.name
    shutil.copyfile(image,disk)
    command = [str(emulator), '-m'+model, '-batch', '-turbo', '-d0', str(disk),
               '-itime', '60000']
    if model == '4':
        command += ['-ktx', '-iw', 'Type TYPE README.TXT for more']
    else:
        command += ['-mem', '64', '-iw', 'A0>']
    def type_keys(keys):
        command.extend(key_args(keys) if model == '4' else ['-i',keys])
    def wait_for(text):
        command.extend(['-iw',text,'-id','300'])
    captures = []
    def capture(*lines):
        wait_for(lines[-1])
        command.append('-it')
        captures.append(lines)

    command += ['-id','6000']
    if model == '2':
        type_keys('RSX LOAD ADM3A\r')
        command += ['-id','6000']
    type_keys('HELP PIP\r')
    capture('PIP - File and device transfer','0  Syntax','0-2 Select  Q Exit')
    type_keys('1')
    capture('PIP - Selectors','Q Back')
    type_keys('Q')
    capture('PIP - File and device transfer','0-2 Select  Q Exit')
    type_keys('Q')
    wait_for('A0>')
    type_keys('HELP PIP /R\r')
    capture('A0:HELP.LBR (PIP.HLP)')
    command += ['-ix']
    run(command, cwd=folder, timeout=240)
    for index, expected in enumerate(captures):
        rows = screen(folder/f'trs80-text-{index}.bin').splitlines()
        if not all(any(text in row for row in rows) for text in expected):
            raise ValueError(f'Model {model}, capture {index}: expected {expected}, got {rows}')
        if len(expected) > 1 and (rows[0] != expected[0] or rows[-1] != expected[-1]):
            raise ValueError(f'Model {model}, capture {index}: misplaced title or navigation row')
    return {'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(), 'status':'PASS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model4', type=Path, required=True)
    parser.add_argument('--model2', type=Path, required=True)
    parser.add_argument('--emulator', type=Path,
                        default=Path.home()/'Applications/trs80gp.app/Contents/MacOS/trs80gp')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='run-',dir=args.output)).resolve()
    result = {}
    for model, image in [('4',args.model4),('2',args.model2)]:
        result[model] = qualify(model,image.resolve(),args.emulator.resolve(),folder/model)
        (folder/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'Model {model} full-screen HELP: PASS',flush=True)
    print(folder/'results.json')


if __name__ == '__main__':
    main()
