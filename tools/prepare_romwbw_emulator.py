#!/usr/bin/env python3
"""Verify pinned source snapshots, stage and build a private native RomWBW emulator."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='romwbw_emu source directory')
    p.add_argument('--cpu-source',type=Path,required=True,help='cpmemu source directory')
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); pin=json.loads((ROOT/'metadata/romwbw-emulator.json').read_text())
    rom=a.rom.read_bytes()
    if len(rom)!=524288 or hashlib.sha256(rom).hexdigest()!=pin['rom']['sha256']:
        p.error('ROM differs from the pinned RomWBW 3.5.1 image')
    # Verify before producing a build. Git metadata is unnecessary: each byte
    # is checked against its blob in the pinned upstream commit tree.
    snapshots={}
    for name,directory in [('romwbw_emu',a.source),('cpmemu',a.cpu_source)]:
        snapshots[name]={}
        for relative,expected in pin['sources'][name]['files'].items():
            data=(directory/relative).read_bytes()
            if blob(data)!=expected:p.error('source differs from pin: '+name+'/'+relative)
            snapshots[name][relative]=data
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name,files in snapshots.items():
        for relative,data in files.items():
            target=out/name/relative;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            if relative.startswith('tools/'):target.chmod(0o755)
    (out/'emu_avw.rom').write_bytes(rom)
    commands=[['make','-C','cpmemu/src','libqkz80.a'],
              ['make','-C','romwbw_emu/src','-j4','QKZ80_CFLAGS=-I../../cpmemu/src',
               'QKZ80_LIBS=../../cpmemu/src/libqkz80.a']]
    with (out/'build.log').open('w') as log:
        for command in commands:subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True)
    executable=out/'romwbw_emu/src/romwbw_emu'
    (out/'provenance.json').write_text(json.dumps({'pins':pin,'build_commands':commands,
        'simulator_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
        'compiler':subprocess.check_output(['c++','--version'],text=True)},indent=2)+'\n')
    print(executable)

if __name__=='__main__':main()
