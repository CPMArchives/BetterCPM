#!/usr/bin/env python3
"""Reject corrupt session graphs on real native filesystems without changing live tables."""
import argparse,json,zlib
from pathlib import Path
from build_dasm import build
from dasm_native import campaign,DEFAULT_SYSTEM
from dasm_script_harness import scripted


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',default=['z80pack','trs80gp'],choices=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    seed={n:(a.seed/('after-'+n)).read_bytes() for n in ('SESSION.ALL','DSA00000.SYM','DSA00000.DOC','DSA00000.CTL')}
    report={'scope':'real filesystem session graph corruption; live-table preservation','platforms':{}}
    cases=['valid','descriptor','symbol','comment','control','binary','missing']
    for platform in a.platforms:
        files={'TINY.COM':bytes.fromhex('210112c9'),'LIVE.SYM':b'1200 KEEP\r\n'};lines=['RTINY.COM','N4','O1200'];outputs=[]
        for i,kind in enumerate(cases):
            descriptor=bytearray(seed['SESSION.ALL']);descriptor[14]=1 if platform=='trs80gp' else 3
            for j,ext in enumerate(('SYM','DOC','CTL')):
                name=f'F{i}{j:06d}.{ext}';entry=31+j*19
                descriptor[entry:entry+12]=bytes([descriptor[14]])+name.replace('.','').encode()
                data=seed['DSA00000.'+ext]
                if kind==('symbol','comment','control')[j]:data=bytes([data[0]^1])+data[1:]
                if kind!='missing' or j!=0:files[name]=data
            if kind=='binary':descriptor[27]^=1
            descriptor[124:]=zlib.crc32(descriptor[:124]).to_bytes(4,'little')
            if kind=='descriptor':descriptor[124]^=1
            files[f'CASE{i}.ALL']=bytes(descriptor)
            lines+=['K.START','K.ALIAS','K.INSIDE','K.LAST','K.KEEP','RLIVE.SYM',f'RCASE{i}.ALL',f'SRESULT{i}.SYM']
            outputs.append(f'RESULT{i}.SYM')
        files['QSESS.COM']=scripted(image,lines+['G'])
        log,out=campaign(platform,files,['QSESS'],a.output/platform,system=a.system,utilities=a.utilities,
            extract=outputs,utility_files={'DASM.COM':image})
        assert b'DASM RESIDENT CANARY PASS' in log and b'DASM RESIDENT CANARY FAIL' not in log
        for i,kind in enumerate(cases):
            data=out[outputs[i]].split(b'\x1a',1)[0]
            if kind=='valid':assert b'1200 START\r\n' in data and b'KEEP' not in data,(kind,data)
            else:assert data==b'1200 KEEP\r\n',(kind,data)
        report['platforms'][platform]={'status':'PASS','cases':cases,'live_tables_preserved':True,'resident_canary':True,'execution_report':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'valid session and six rejected damaged graphs with unchanged live symbols',flush=True)
if __name__=='__main__':main()
