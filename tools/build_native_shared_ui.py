#!/usr/bin/env python3
"""Require native ZSM4/LINK parity for non-distributed shared UI CPU fixtures."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from build_native_trs80 import blank,cpm_text,run
from build_shared_ui_fixtures import ROOT,BUILD,PROFILES,fixture_source


def main():
    p=argparse.ArgumentParser()
    base=Path.home()/'projects/git'
    p.add_argument('--cpmsim',type=Path,default=base/'z80pack/cpmsim/cpmsim')
    p.add_argument('--system',type=Path,default=base/'z80pack/cpmsim/disks/library/cpm22-62khd.dsk')
    p.add_argument('--template',type=Path,default=base/'z80pack/cpmsim/disks/library/cpm22-1.dsk')
    p.add_argument('--tools',type=Path,default=base/'cpm-compatibility/suite/build-tools')
    p.add_argument('--extra-fixture',type=Path,action='append',default=[],
                   help='Previously cross-built .mac fixture, with matching .bin in build/shared-ui')
    a=p.parse_args();os.environ['PATH']=str(a.cpmsim.parent/'srctools')+os.pathsep+os.environ.get('PATH','')
    BUILD.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bcpm-native-ui-') as temporary:
        w=Path(temporary);disks=w/'disks';disks.mkdir();shutil.copy2(a.system,disks/'drivea.dsk')
        for drive in 'bcd':blank(a.template,disks/f'drive{drive}.dsk')
        for tool in ['ZSM4.COM','LINK.COM']:
            run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(a.tools/tool),'0:'+tool)
        sources={profile:fixture_source(profile) for profile in PROFILES}
        for extra in a.extra_fixture:
            assert extra.stem not in sources,'duplicate fixture name'
            sources[extra.stem]=extra.read_text(encoding='ascii')
        names={profile:'UI'+str(i) for i,profile in enumerate(sources)}
        commands=f'set timeout 60\nspawn {a.cpmsim} -z -d {disks}\nexpect "A>"\nsend -- "B:\\r"\nexpect "B>"\n'
        for profile,name in names.items():
            text=sources[profile].replace('        ASEG\n        ORG 0100H','        CSEG\n        .PHASE 0100H',1)
            text=text.replace('        END\n','        .DEPHASE\n        END\n')
            source=w/(name+'.MAC');plain=w/(name+'.txt');plain.write_text(text,encoding='ascii');source.write_bytes(cpm_text(plain))
            run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(source),'0:'+source.name)
            commands+=f'send -- "D:ZSM4 B:{name}=C:{name}\\r"\nexpect -re {{Errors: +0}}\nexpect "B>"\nsend -- "D:LINK {name}\\[A\\]\\r"\nexpect "CODE SIZE"\nexpect "B>"\n'
        commands+='send "\\034"\nexpect eof\n'
        result=run('expect','-c',commands,check=False)
        log=result.stdout+result.stderr;(BUILD/'NATIVE-UI-BUILD.LOG').write_text(log)
        assert result.returncode==0,log
        assert log.count('Errors: 0')==len(sources),log
        reports={}
        for profile,name in names.items():
            target=w/(name+'.COM');run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:'+target.name,str(target))
            cross=(BUILD/(profile+'.bin')).read_bytes();native=target.read_bytes()
            assert native[:len(cross)]==cross,(profile,'native/cross mismatch')
            assert len(cross)<=len(native)<len(cross)+128,(profile,'unexpected native size')
            (BUILD/(profile+'-native.bin')).write_bytes(native[:len(cross)])
            reports[profile]={'status':'PASS','bytes':len(cross)}
        (BUILD/'native-results.json').write_text(json.dumps(reports,indent=2)+'\n')
        print(f'PASS: native ZSM4/LINK parity for {len(sources)} shared UI fixtures')


if __name__=='__main__':main()
