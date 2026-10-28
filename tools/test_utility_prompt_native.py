#!/usr/bin/env python3
"""Require native/cross byte parity for NOAH's changed resident and CLI modules."""
from pathlib import Path
import sys,shutil,tempfile,subprocess,json,hashlib,os
sys.path.insert(0,str(Path.cwd()/'tools'))
from build_native_trs80 import blank,run
from qualify_noah_codecs import native_match

def main():
    root=Path(__file__).resolve().parents[1];out=root/'build/prompt-help-development';out.mkdir(exist_ok=True)
    z=Path.home()/'projects/git/z80pack/cpmsim';tools=Path.home()/'projects/git/cpm-compatibility/suite/build-tools'
    os.environ['PATH']=str(z/'srctools')+os.pathsep+os.environ['PATH']
    with tempfile.TemporaryDirectory(prefix='noah-prompt-native-') as tmp:
     w=Path(tmp);disks=w/'disks';disks.mkdir();shutil.copy2(z/'disks/library/cpm22-62khd.dsk',disks/'drivea.dsk')
     for letter in 'bcd':blank(z/'disks/library/cpm22-1.dsk',disks/f'drive{letter}.dsk')
     for name in ('NOAH','NHCLI'):run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(root/f'build/utilities/{name}.MAC'),'0:'+name+'.MAC')
     for name in ('ZSM4.COM','LINK.COM'):run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(tools/name),'0:'+name)
     script=f'''set timeout 90
    spawn {z/'cpmsim'} -z -d {disks}
    expect_before timeout {{exit 2}}
    expect "A>"
    send -- "B:\\r"
    expect "B>"
    '''
     for name in ('NOAH','NHCLI'):
      script+=f'''send -- "D:ZSM4 {name}=C:{name}\\r"
    expect -re {{Errors: +0}}
    expect "B>"
    send -- "D:LINK {name}\\[A\\]\\r"
    expect "CODE SIZE"
    expect "B>"
    '''
     script+='send -- "\\034"\nexpect eof\n'
     r=run('expect','-c',script,check=False);(out/'NOAH-NATIVE-PROMPT.LOG').write_text(r.stdout+r.stderr)
     assert r.returncode==0,r.stdout+r.stderr
     records={}
     for name in ('NOAH','NHCLI'):
      path=out/(name+'-native.COM');run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:'+name+'.COM',str(path))
      expected=(root/f'build/utilities/{name}.bin').read_bytes();native_match(path.read_bytes(),expected)
      records[name]={'bytes':len(expected),'sha256':hashlib.sha256(expected).hexdigest(),'native_parity':'PASS'}
     (out/'NOAH-NATIVE-PROMPT.json').write_text(json.dumps(records,indent=2)+'\n')
     print('NOAH changed resident/CLI modules: native parity PASS')


if __name__=='__main__':main()
