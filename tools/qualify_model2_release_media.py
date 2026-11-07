#!/usr/bin/env python3
"""Run packaged Utilities, system lifecycle and install checks on private Model II disks."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from model2_media import image, geometry
from qualify_numeric_path_trs80 import marker
from run_model2_conformance import OFFSET, write_json, validate
from run_model2_qualification import EMU, EMU_SHA, ROOT, sha, screen
from test_ark import member
from test_model2_release_media import decoded
from test_z80pack_submit_xsub import input_probe
from trs80gp_launch import launch_services_lookup, run
from trs80m2_utilities import system_digest

PHASES = ('utilities', 'batch', 'lifecycle', 'install')
VOLUMES = ('BetterCPM-Utilities-trs80m2-77T-SS-584K.imd', 'BetterCPM-NOAH-trs80m2-77T-SS-584K.imd')


def inventory(raw):
    """Retain the live directory and allocated data, ignoring deleted scratch files."""
    fmt = geometry()
    contents = {}
    for i in range(fmt.drm + 1):
        pos = OFFSET + 32*i
        entry = raw[pos:pos+32]
        if entry[0] == 0xe5:
            continue
        blocks = []
        for j in range(16, 32, 2):
            block = int.from_bytes(entry[j:j+2], 'little')
            if block:
                validate(fmt.directory_blocks <= block <= fmt.dsm, 'invalid allocation')
                start = OFFSET + block*fmt.block_bytes
                blocks.append(raw[start:start+fmt.block_bytes])
        contents[i] = (entry, blocks)
    return contents


def inputs(system, utilities):
    manifest = json.loads((system/'candidate.json').read_text())
    digest = system_digest(system, manifest['compatibility_id'])
    paths = [system/'Model-II-System-candidate.imd']
    for filename in VOLUMES:
        path = utilities/filename
        report = json.loads(path.with_suffix('.imd.json').read_text())
        validate(report['target']=='trs80m2' and report['format']=='BCM2SS' and
                 report['profile']==manifest['profile'] and report['compatibility_id']==manifest['compatibility_id']
                 and report['paired_system_sha256']==digest and report['sha256']==sha(path),
                 'incorrect paired Utilities volume: '+filename)
        paths.append(path)
    return paths


def exercise(phase, system, paths, work, previous_install=None):
    if phase in ('lifecycle', 'install'):
        runner = 'run_model2_qualification.py' if phase=='lifecycle' else 'run_model2_install.py'
        command = [sys.executable, '-B', str(ROOT/'tools'/runner), '--media',str(system),'--output',str(work)]
        if previous_install:
            command.extend(['--resume',str(previous_install)])
        subprocess.run(command, check=True)
        receipt, = work.glob('run-*/result.json')
        data = json.loads(receipt.read_text())
        validate(data['status'].startswith('PASS'), 'nested qualification incomplete')
        return {'report':str(receipt.relative_to(work))}
    batch = b'B0:XSUB B0:\r\nD0:INPUT\r\nBATCHFULL\r\nA0:RSX UNLOAD BATCHIO\r\nA0:RSX LIST\r\nD0:DONE\r\n\x1a'
    fixtures = [('PAIR.SUB',batch),('INPUT.COM',input_probe(work)),('DONE.COM',marker('PAIRED BATCH FINISHED'))] if phase=='batch' else [
        ('TEST.ARK',member(b'proof record',name=b'PROOF.BIN')+b'\x1a\0')]
    d = work/'d.imd'
    d.write_bytes(image(bytes(20480),fixtures,bootable=False))
    arguments = [str(EMU),'-m2','-mem','64','-batch','-turbo','-itime','45000']
    originals = []
    for index, path in enumerate(paths):
        mount = work/('abc'[index]+'.imd')
        shutil.copyfile(path, mount)
        originals.append(decoded(path.read_bytes())[2])
        arguments.extend(['-d'+str(index),str(mount)])
    arguments.extend(['-d3',str(d),'-iw','A0>','-id','500','-it'])
    if phase=='batch':
        steps = [('B0:SUBMIT D:PAIR',['INPUT OK','No RSXs loaded','PAIRED BATCH FINISHED']),
                 ('STAT MEM',['Maximum loadable COM: 57344 bytes'])]
    else:
        steps = [('B0:SQ B:DUMP.COM D:', ['SQ: complete.']),
                 ('B0:USQ D:DUMP.CQM D:', ['USQ: complete.']),
                 ('C0:COMPARE B:DUMP.COM D:DUMP.COM /SUMMARY', ['FILES IDENTICAL']),
                 ('C:', ['C0>']), ('NOAH /LIST D:TEST.ARK', ['PROOF.BIN'])]
    witnesses = ['A0>']
    for command, expected in steps:
        arguments.extend(['-id','4000','-i',command+'\r'])
        for witness in expected:
            arguments.extend(['-iw',witness,'-id','300','-it'])
            witnesses.append(witness)
    arguments.append('-ix')
    write_json(work/'arguments.json',arguments)
    run(arguments,cwd=work,timeout=480)
    captures = {}
    for idx,witness in enumerate(witnesses):
        path = work/f'trs80-text-{idx}.bin'
        value = screen(path)
        (work/f'screen-{idx}.txt').write_text(value+'\n')
        validate(witness in value, 'missing witness: '+witness)
        captures[path.name] = sha(path)
    for letter, before in zip('abc',originals):
        after = decoded((work/(letter+'.imd')).read_bytes())[2]
        if phase=='batch' and letter=='a':
            validate(before[:OFFSET]==after[:OFFSET] and inventory(before)==inventory(after),
                     'SUBMIT changed system tracks or a live System file')
        else:
            validate(after==before,'changed mounted disk '+letter.upper())
    return {'witnesses':witnesses,'capture_sha256':captures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,default=ROOT/'build/conformance11-candidate')
    parser.add_argument('--utilities',type=Path,default=ROOT/'build/model2-native-utilities')
    parser.add_argument('--output',type=Path,default=ROOT/'build/model2-release-guest')
    parser.add_argument('--only',choices=PHASES,action='append')
    parser.add_argument('--resume-install',type=Path,metavar='PREVIOUS_RUN',
                        help='finish an interrupted install on the same verified release images')
    args = parser.parse_args()
    if args.resume_install and args.only:
        parser.error('--resume-install already selects the install phase')
    system = args.system.resolve()
    paths = inputs(system,args.utilities.resolve())
    validate(sha(EMU)==EMU_SHA, 'unexpected emulator binary')
    if sys.platform=='darwin' and (code:=launch_services_lookup()):
        sys.exit(f'macOS LaunchServices {code}: start Run-Model-II-Release-Checks.command in Terminal')
    previous_install = None
    if args.resume_install:
        previous = args.resume_install.resolve()
        old = json.loads((previous/'result.json').read_text())
        validate([old[k] for k in ('system','primary','companion')]==[sha(p) for p in paths]
                 and old['emulator_sha256']==EMU_SHA and old['phases']['install']['status']=='INCOMPLETE',
                 'previous run does not have an interrupted installation on this media set')
        previous_install, = (previous/'install').glob('run-*/result.json')
        previous_install = previous_install.parent
    args.output.mkdir(parents=True,exist_ok=True)
    trial = Path(tempfile.mkdtemp(prefix='run-',dir=args.output.resolve()))
    result = {'status':'RUNNING','system':sha(paths[0]),'primary':sha(paths[1]),'companion':sha(paths[2]),
              'emulator_sha256':EMU_SHA,'phases':{}}
    receipt = trial/'result.json'
    print('Model II release-media checks:',receipt,flush=True)
    if previous_install:
        result['resumed_from'] = str(args.resume_install.resolve())
    for phase in (('install',) if previous_install else (args.only or PHASES)):
        work = trial/phase
        work.mkdir()
        result['phases'][phase] = {'status':'RUNNING'}
        write_json(receipt,result)
        print('Running',phase,flush=True)
        try:
            details = exercise(phase,system,paths,work,previous_install)
            result['phases'][phase] = {'status':'PASS',**details}
        except (OSError,ValueError,AssertionError,subprocess.SubprocessError) as error:
            result['phases'][phase] = {'status':'INCOMPLETE','detail':str(error)}
        row = result['phases'][phase]
        write_json(receipt,result)
        print(row['status'],phase,row.get('detail',''),flush=True)
    passed = all(x['status']=='PASS' for x in result['phases'].values())
    result['status'] = 'PASS (selected phases)' if passed else 'INCOMPLETE'
    write_json(receipt,result)
    print(result['status'],receipt,flush=True)
    return 0 if passed else 1


if __name__=='__main__':
    sys.exit(main())
