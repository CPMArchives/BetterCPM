#!/usr/bin/env python3
"""Rebuild exported Cromemco sources and exercise the actual native package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from test_cromemco_system import Terminal


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();packages=args.packages.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    ledger=json.loads((packages/'CROMEMCO-RELEASE.json').read_text())
    for row in ledger['assets']:
        archive=packages/row['name'];assert sha(archive)==row['sha256']
        with zipfile.ZipFile(archive) as bundle:
            assert bundle.testzip() is None
            for member in bundle.infolist():
                path=Path(member.filename)
                assert not path.is_absolute() and '..' not in path.parts
            bundle.extractall(out)
            for member in bundle.infolist():
                mode=(member.external_attr>>16)&0o777
                if mode:(out/member.filename).chmod(mode)
    source=out/'BetterCPM-source';media=out/'BetterCPM-1.3-Cromemco'
    def run(command,log):
        with (out/log).open('w') as stream:
            subprocess.run(list(map(str,command)),cwd=source,stdout=stream,
                           stderr=subprocess.STDOUT,check=True)
    runtime=out/'offline-emulator'
    run([sys.executable,source/'tools/prepare_cromemco_emulator.py','--output',runtime], 'emulator-build.log')
    binary=runtime/'cromemcosim/cromemcosim'
    expected=ledger['acceptance']['emulator_sha256']
    assert sha(binary)==expected==sha(media/'Host/prebuilt/macos-arm64/cromemcosim')
    work=out/'rebuilt'
    run([sys.executable,source/'tools/build_cromemco.py','--release','--work',work], 'media-build.log')
    rebuilt=work/'profiles/cromemco-fullram/cromemco/build/cromemco/release'
    images=[]
    for row in ledger['collection']['volumes']:
        assert sha(rebuilt/row['image'])==row['sha256']==sha(media/'Media'/row['image'])
        images.append({'name':row['image'],'sha256':row['sha256'],'status':'IDENTICAL'})
    console=out/'native-console';console.mkdir()
    terminal=Terminal(media/'Host/prebuilt/macos-arm64/cromemcosim',console,
                      command=[str(media/'Run-Cromemco.command')],cwd=out)
    try:
        terminal.expect('BetterCP/M 1.3 - Cromemco');terminal.prompt()
        terminal.send(':VER /BANNER','BetterCP/M 1.3 - Cromemco')
        terminal.send('RSX LOAD C:ANSI')
        terminal.type_command('HELP PIP');terminal.expect('Q Exit',timeout=60)
        os.write(terminal.master,b'Q');terminal.prompt()
        terminal.send('RSX UNLOAD ANSI')
        terminal.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        terminal.type_command('BYE /Y');terminal.expect('System halted')
        terminal.process.wait(timeout=5);assert terminal.process.returncode==0
    finally:terminal.close()
    result={'status':'PASS','source':ledger['source'],'images':images,
            'emulator_sha256':expected,'checks':['offline exported-source emulator build',
            'exported-source complete media rebuild','all four release images byte-identical',
            'unpacked native launcher from unrelated working directory','cold and explicit banner',
            'packaged HELP/ANSI and full TPA restoration','BYE clean exit'],
            'transcript_sha256':sha(console/'transcript.txt')}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: offline source export rebuilds exact emulator/media; native package and HELP work')


if __name__=='__main__':main()
