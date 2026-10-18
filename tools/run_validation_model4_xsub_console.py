#!/usr/bin/env python3
"""Native zero-length Function-10 fallback and safe Function-0 retirement."""
import argparse,json,shutil
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_sysgen_install import screen
SOURCE='''        ORG 100H
        LD DE,BUFFER
        LD C,10
        CALL 5
        LD A,(BUFFER+1)
        OR A
        LD DE,GOOD
        JR Z,SHOW
        LD DE,BAD
SHOW:   LD C,9
        CALL 5
        LD C,0
        JP 5
BUFFER: DB 0,255
GOOD:   DB 'CONSOLE FALLBACK RETURNED',13,10,'$'
BAD:    DB 'CONSOLE FALLBACK FAILED',13,10,'$'
        END
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('baseline','build-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    r=json.loads((a.baseline/'report.json').read_text());original=a.baseline/r['image'];raw=extract_raw(original.read_bytes())
    for i in range(DIRECTORY_ENTRIES):
        off=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
        if raw[off]==0 and raw[off+1:off+12]==b'STARTUP SUB':raw[off]=0xe5
    add_file(raw,'STARTUP.SUB',b'XSUB\r\nZERO\r\n\x1a')
    added={}
    for name,part in [('XSUB.COM','utilities'),('BATCHIO.RSX','rsx')]:
        source=a.build_root/'build'/part/name;add_file(raw,name,source.read_bytes());added[name]=sha(source)
    (w/'zero.mac').write_text(SOURCE)
    code=assemble(Path.home()/'bin/z80asm',SOURCE,w/'ZERO.COM',w/'zero.lst',0x100);add_file(raw,'ZERO.COM',code)
    image=w/'a.dmk';image.write_bytes(build(bytes(raw)));shutil.copy2(__file__,w/'executed-runner.py')
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000',
         '-iw','CONSOLE FALLBACK RETURNED','-id','6000','-it']
    cmd+=key_args('RSX LIST\r')+['-id','2000','-it','-ix']
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=480,check=True)
    captures=sorted(w.glob('trs80-text-*.bin'));assert len(captures)==2
    texts=[screen(f) for f in captures]
    for i,t in enumerate(texts):(w/f'screen-{i}.txt').write_text(t+'\n')
    assert '(xsub active)' in texts[0]
    assert 'CONSOLE FALLBACK RETURNED' in texts[0] and 'CONSOLE FALLBACK FAILED' not in texts[0]
    assert 'No RSXs loaded' in texts[1] and 'TPA available: 53K' in texts[1]
    audit=audit_files(original,image,dict(r,included=[f for f in r['included'] if f['name']!='STARTUP.SUB']),w)
    (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':sha(original),'supplemental_files':added,'file_audit':audit,
        'runner_sha256':sha(Path(__file__)),'emulator_sha256':sha(DEFAULT_EMULATOR),'scope':'native empty-buffer console fallback returns to caller, Function-0 retirement and 53K; declared STARTUP.SUB fixture'},indent=2)+'\n')
    print('PASS native XSUB console fallback',w)

if __name__=='__main__':main()
