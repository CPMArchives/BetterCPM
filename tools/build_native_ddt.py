#!/usr/bin/env python3
"""Require ZSM4/LINK parity for DDT's adaptation payloads and bootstrap."""
from pathlib import Path
import argparse,json,os,re,shutil,subprocess,tempfile
from build_ddt import ROOT,BUILD,payload_source,startup_source


def run(command,**kw):
    r=subprocess.run([str(x) for x in command],capture_output=True,**kw)
    if r.returncode:raise RuntimeError(f'{command}: {r.stdout!r} {r.stderr!r}')
    return r


def main():
    p=argparse.ArgumentParser(description=__doc__);base=Path.home()/'projects/git'
    p.add_argument('--output',type=Path,default=BUILD)
    p.add_argument('--cpmsim',type=Path,default=base/'z80pack/cpmsim/cpmsim')
    p.add_argument('--tools',type=Path,default=base/'cpm-compatibility/suite/build-tools')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    library=a.cpmsim.parent/'disks/library';env=dict(os.environ);env['PATH']=str(a.cpmsim.parent/'srctools')+os.pathsep+env['PATH']
    length=len((out/'payload-0000.bin').read_bytes())
    sources=[(f'PAY{i}',payload_source(origin),f'payload-{origin:04x}.bin',origin) for i,origin in enumerate([0,0x100,0x3100])]
    sources.append(('BOOT',startup_source(length),'startup.bin',0x100))
    report={}
    for name,text,filename,origin in sources:
        with tempfile.TemporaryDirectory(prefix='ddt-native-',dir=out) as temp:
            work=Path(temp);disks=work/'disks';disks.mkdir()
            shutil.copyfile(library/'cpm22-62khd.dsk',disks/'drivea.dsk')
            for d in 'bcd':shutil.copyfile(library/'cpm22-1.dsk',disks/f'drive{d}.dsk');run(['mkfs.cpm','-f','ibm-3740',disks/f'drive{d}.dsk'])
            text=text.replace('ASEG','CSEG',1) if 'ASEG' in text else '        CSEG\n'+text
            text=re.sub(r'(?m)^\s*ORG\s+[^\n]+',f'        .PHASE {origin:05X}H',text,count=1)
            text=text.rsplit('        END',1)[0]+'        .DEPHASE\n        END\n'
            src=work/(name+'.MAC');src.write_bytes(text.replace('\n','\r\n').encode('ascii')+b'\x1a')
            run(['cpmcp','-f','ibm-3740',disks/'drivec.dsk',src,'0:'+src.name])
            for tool in ['ZSM4.COM','LINK.COM']:run(['cpmcp','-f','ibm-3740',disks/'drived.dsk',a.tools/tool,'0:'+tool])
            script=['set timeout 30',f'spawn {{{a.cpmsim}}} -z -d {{{disks}}}','expect "A>"','send -- "B:\\r"','expect "B>"',f'send -- "D:ZSM4 B:{name}=C:{name}\\r"','expect "B>"',f'send -- [format "%s\\r" {{D:LINK {name}[A]}}]','expect "B>"','send "\\034"','expect eof']
            r=run(['expect','-c','\n'.join(script)],cwd=work,env=env,timeout=45)
            log=r.stdout+r.stderr;(out/(name+'-native.log')).write_bytes(log)
            if b'Errors: 0' not in log or b'CODE SIZE' not in log:raise RuntimeError(log.decode(errors='replace'))
            com=work/(name+'.COM');run(['cpmcp','-f','ibm-3740',disks/'driveb.dsk','0:'+com.name,com])
            expected=(out/filename).read_bytes();native=com.read_bytes()
            assert native[:len(expected)]==expected,(name,'native/cross byte mismatch',native[:16].hex(),expected[:16].hex())
            assert len(expected)<=len(native)<len(expected)+128
            (out/(name+'-native.bin')).write_bytes(native[:len(expected)])
            report[name]={'status':'PASS','bytes':len(expected),'origin':origin}
    (out/'native-report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
