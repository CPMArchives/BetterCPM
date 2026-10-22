#!/usr/bin/env python3
"""Native Model 4 CONFIG inline editor, CLEAR cancellation and no-save checks."""
import argparse,hashlib,json
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from startup_record import build as startup
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve()
    source=a.image.read_bytes();raw=extract_raw(source);directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    for i in range(DIRECTORY_ENTRIES):
        at=directory+i*32
        if raw[at]==0 and bytes(v&127 for v in raw[at+1:at+12])==b'CONFIG  COM':raw[at]=0xe5
    program=(ROOT/'build/utilities/CONFIG.COM').read_bytes();add_file(raw,'CONFIG.COM',program)
    raw[128:384]=startup('',system_base=LAYOUT['SYSTEM'])
    image=w/'private.dmk';initial=build(raw);image.write_bytes(initial)
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-id','5000']
    stages=[]
    def step(keys,label=None):
        cmd.extend(key_args(keys,delay=25));cmd.extend(['-id','18000' if keys.startswith('CONFIG') else '2500'])
        if label:cmd.append('-it');stages.append(label)
    step('CONFIG /DEFAULT\r')
    step('\r')
    step('E')
    step('Abc\x13\x07\x08Z\x04Q\r','edited')
    step('E')
    step('Cancel','caret')
    # Native physical CLEAR supplies ESC rather than a host Ctrl-[ assumption.
    cmd.extend(['-ik','6','2','-id','25','-ik','6','0'])
    cmd.extend(['-id','2500','-it']);stages.append('cancelled')
    step('\x03')
    step('B')
    step('12X\r','numeric-error')
    step('\x08\x03','numeric-cancel')
    step('\x03','returned');cmd.append('-ix')
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
    run(cmd,cwd=w,timeout=600)
    files=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(files)==len(stages)
    screens={}
    for label,p in zip(stages,files):
        data=p.read_bytes()[:1920];text='\n'.join(bytes(v&127 for v in data[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
        screens[label]=text;(w/(label+'.txt')).write_text(text+'\n')
        if label=='caret':assert (ord('_')|128) in data,'software cursor not visible'
    assert 'Pending startup command: AZQ' in screens['edited']
    assert 'Pending startup command: AZQ' in screens['cancelled']
    assert 'Invalid decimal value.' in screens['numeric-error']
    assert 'Configuration options:' in screens['numeric-cancel']
    assert 'A0>' in screens['returned']
    assert image.read_bytes()==initial,'editing/cancellation modified disk'
    assert a.image.read_bytes()==source,'modified source image'
    report={'status':'PASS','stages':stages,'program_sha256':hashlib.sha256(program).hexdigest(),
            'source_sha256':hashlib.sha256(source).hexdigest(),'bytes':len(program),'disk_unchanged':True}
    (w/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: native Model 4 CONFIG shared editing/CLEAR/numeric recovery/return;',w)


if __name__=='__main__':main()
