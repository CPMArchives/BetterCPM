#!/usr/bin/env python3
"""Check six compact /VER identities and complete /HELP screens under stock CP/M 2.2 on disposable disks."""
import argparse
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from codec_version import DESCRIPTIONS, version_text, help_text
from test_usq_com_cpm import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    args=parser.parse_args()
    simulator=args.z80pack/'cpmsim/cpmsim'
    template=simulator.parent/'disks/library/cpm22-62khd.dsk'
    with tempfile.TemporaryDirectory(prefix='bettercpm-codec-version-cpm-') as temp:
        work=Path(temp);disks=work/'disks';disks.mkdir()
        shutil.copy2(template,disks/'drivea.dsk')
        def put(name,data):
            host=work/'import.bin';host.write_bytes(data)
            run('cpmcp','-f','ibm-3740',disks/'drivea.dsk',host,'0:'+name)
        def get(name):
            host=work/'export.bin';host.unlink(missing_ok=True)
            run('cpmcp','-f','ibm-3740',disks/'drivea.dsk','0:'+name,host)
            return host.read_bytes()
        images={c:importlib.import_module('build_'+c.lower()).build(args.assembler,work) for c in DESCRIPTIONS}
        for c,image in images.items():
            put(c+'.COM',image)
        put('KEEP.BIN',bytes(range(256)))
        before={c+'.COM':get(c+'.COM') for c in images}
        before['KEEP.BIN']=get('KEEP.BIN')
        commands=[]
        for c in images:
            title=version_text(c).split('\r\n')[0]
            commands += [(c+' /VER',title),(c+' /ver',title),
                         (c+' /VER KEEP.BIN','Invalid /VER usage.'),
                         (c+' KEEP.BIN /VER','Invalid /VER usage.'),
                         (c+' /VER /VER','Invalid /VER usage.'),
                         (c+' /VERIFY','Usage: '+c),
                         (c+' /HELP',title),(c+' /help',title),
                         (c+' /HELP KEEP.BIN','Invalid /HELP usage.'),
                         (c+' KEEP.BIN /HELP','Invalid /HELP usage.'),
                         (c+' /HELP /HELP','Invalid /HELP usage.'),
                         (c+' /HELP /VER','Invalid /VER usage.'),
                         (c+' /VER /HELP','Invalid /VER usage.'),
                         (c+' /HELPER','Usage: '+c),(c,'Use '+c+' /HELP for help.')]
        script='''set timeout 30
proc await {text} {
 expect {
  -exact $text {return}
  timeout {puts "TIMEOUT waiting for $text"; exit 1}
  eof {puts "unexpected EOF"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
await "A>"
'''
        for cmd,message in commands:
            script+=f'send -- "{cmd}\\r"\nawait "{message}"\nawait "A>"\n'
        script+='send -- "\\034"\nexpect eof\n'
        (work/'test.exp').write_text(script)
        env=dict(os.environ);env['PATH']=str(simulator.parent/'srctools')+os.pathsep+env['PATH']
        result=subprocess.run(['expect',str(work/'test.exp'),str(simulator),str(disks)],cwd=work,
                              env=env,capture_output=True,text=True,timeout=180)
        assert result.returncode==0,result.stdout+result.stderr
        lines=[line for line in result.stdout.splitlines() if line.strip()]
        for c in images:
            expected=version_text(c).splitlines()
            count=sum(lines[i:i+4]==expected for i in range(len(lines)-3))
            assert count==2,(c,count,result.stdout)
        for c in images:
            expected=help_text(c).splitlines()
            output=result.stdout.splitlines()
            assert sum(output[i:i+len(expected)]==expected for i in range(len(output)))==2,(c,result.stdout)
        for name,data in before.items():
            assert get(name)==data,(name,'file changed')
        listing=run('cpmls','-f','ibm-3740',disks/'drivea.dsk').stdout.upper()
        assert '.$$$' not in listing
        print(f'PASS: {len(commands)} stock CP/M 2.2 version/help/invalid-token commands;')
        print('all six identities and complete help screens, return to prompt, unchanged files and no temporary output checked.')


if __name__=='__main__':
    main()
