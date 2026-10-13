#!/usr/bin/env python3
"""Qualify TYPE page keys and replay on disposable Model 4 media."""
import argparse,hashlib,json
from pathlib import Path
from test_disk_utilities import ROOT,medium,keys
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
PROMPT='MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    binary=(ROOT/'build/utilities/TYPE.COM').read_bytes()
    source=b''.join(f'PAGE ROW {i:02d}\r\n'.encode() for i in range(55))+b'\x1aHIDDEN'
    disk=work/'a.dmk';original=medium([('TYPE.COM',binary),('LONG.TXT',source,3,3)]);disk.write_bytes(original)
    invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
    invocation+=keys(':TYPE A3:LONG.TXT /P\r')+['-itime','0','-iw',PROMPT,'-it']
    for key,marker in [('\x03','PAGE ROW 23'),(',','PAGE ROW 00'),(' ','PAGE ROW 23'),('.','PAGE ROW 54')]:
        invocation+=keys(key)+['-iw',marker,'-iw',PROMPT,'-it']
    invocation+=keys('.')+['-id','1000','-it']
    invocation+=keys('\x12')+['-iw','PAGE ROW 23','-iw',PROMPT,'-it']
    invocation+=keys('\x11')+['-iw','A0>','-it','-ix']
    (work/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
    run(invocation,cwd=work,timeout=300,check=True)
    captures=sorted(work.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))
    texts=[screen(f) for f in captures]
    for f,text in zip(captures,texts):f.with_suffix('.txt').write_text(text)
    assert len(texts)==9,len(texts)
    for i,marker in [(1,'PAGE ROW 00'),(2,'PAGE ROW 23'),(3,'PAGE ROW 00'),(4,'PAGE ROW 23'),(5,'PAGE ROW 54'),(6,'PAGE ROW 54'),(7,'PAGE ROW 23'),(8,'A0>')]:
        assert marker in texts[i] and 'HIDDEN' not in texts[i],(i,texts[i])
    assert 'PAGE ROW 23' not in texts[1] and 'PAGE ROW 46' not in texts[2]
    assert disk.read_bytes()==original,'paging changed Model 4 source disk'
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','type_sha256':hashlib.sha256(binary).hexdigest(),'keys':['Ctrl-C',',','Space','.','.','Ctrl-R','Ctrl-Q'],'whole_disk_unchanged':True},indent=2)+'\n')
    print('PASS: Model 4 TYPE forward/backward page keys, EOF, quit and whole-disk immutability')
if __name__=='__main__':main()
