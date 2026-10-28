#!/usr/bin/env python3
"""Native parity plus actual help execution for DUMP/DASM/DSYM/TED."""
from pathlib import Path
import os,shutil,tempfile,re,json,hashlib
from build_native_trs80 import blank,run
from test_z80pack_sysgen_install import session
from build_dump import expanded_source
from build_dasm import source as dasm_source
from build_dsym import source as dsym_source
from qualify_dasm import native_source
from dasm_native import compact_source,cpm_text
ROOT=Path(__file__).resolve().parents[1]

def main():
    z=Path.home()/'projects/git/z80pack/cpmsim';os.environ['PATH']=str(z/'srctools')+os.pathsep+os.environ['PATH']
    tools=Path.home()/'projects/git/cpm-compatibility/suite/build-tools'
    out=ROOT/'build/remaining-help-native';out.mkdir(parents=True,exist_ok=True)
    dump=re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',r'\1\n REPT \2\n DB 0FFH\n ENDM',expanded_source())
    sources={'DUMP':cpm_text(compact_source(dump)),'DASM':native_source(dasm_source()),'DSYM':native_source(dsym_source()),'TED':cpm_text(compact_source((ROOT/'build/utilities/TEDNAT.MAC').read_bytes().rstrip(b'\x1a').decode()))}
    report={}
    for name,source in sources.items():
      with tempfile.TemporaryDirectory(prefix='native-help-'+name+'-') as tmp:
        w=Path(tmp);disks=w/'disks';disks.mkdir()
        shutil.copy2(z/'disks/library/cpm22-62khd.dsk',disks/'drivea.dsk')
        for d in 'bcd':blank(z/'disks/library/cpm22-1.dsk',disks/f'drive{d}.dsk')
        path=w/(name+'.MAC');path.write_bytes(source)
        run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(path),'0:'+name+'.MAC')
        for n in ('ZSM4.COM','LINK.COM'):run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(tools/n),'0:'+n)
        session(z/'cpmsim',disks,[(b'B:\r',b'B>',15),(f'D:ZSM4 B:{name}=C:{name}\r'.encode(),b'Errors: 0',45),(b'',b'B>',15),(f'D:LINK {name}[A]\r'.encode(),b'CODE SIZE',30),(b'',b'B>',15),(f'{name} /HELP\r'.encode(),b'Display utility identification.',15),(b'',b'B>',15)],out/(name+'.log'),initial_prompt=b'A>')
        path=w/(name+'.COM');run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:'+name+'.COM',str(path))
        expected=(ROOT/f'build/utilities/{name}.COM').read_bytes();actual=path.read_bytes();assert actual[:len(expected)]==expected,name
        assert len(actual)==(len(expected)+127)//128*128
        (out/(name+'-native.COM')).write_bytes(actual)
        report[name]={'status':'PASS','bytes':len(expected),'sha256':hashlib.sha256(expected).hexdigest()}
        print(name,'native parity and stock CP/M help execution: PASS',flush=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
