#!/usr/bin/env python3
"""Native analysis/session, address-edge and mixed-data reconstruction gate."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib
from build_dasm import build
from dasm_native import campaign,DEFAULT_SYSTEM
from dasm_script_harness import scripted


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    binary=bytes.fromhex('210112c9');raw=bytes.fromhex('c9001aff')
    symbols=b'1200 START\r\n1200 ALIAS\r\n1201 INSIDE\r\nFFFF LAST\r\n'
    comments=b'1200 Mixed Case Annotations\r\n'
    controls=b'1200,I\r\n1203,H\r\n'
    lines=['RTINY.COM','N4','O1200','RINPUT.SYM','RINPUT.DOC','RINPUT.CTL','SSESSION.ALL',
        'K.START',';1200,Changed','C1200,H','RSESSION.ALL','SOUT.SYM','SOUT.DOC','SOUT.CTL',
        'SSESSION.ASM','P1200,1204','QL1200,1204','Z']
    cases={'SESSION':(0x1200,binary)}
    for name,origin,payload in [('LOW',0,raw),('HIGH',0xfffc,raw),('LAST',0xffff,raw[:1])]:
        end=origin+len(payload)
        lines+=['RRAW.COM',f'N{len(payload):X}',f'O{origin:X}','S'+name+'.ASM',
            f'P{origin:X},{end:X}',f'QL{origin:X},{end:X}','Z']
        cases[name]=(origin,payload)
    files={'TINY.COM':binary,'RAW.COM':raw,'INPUT.SYM':symbols,'INPUT.DOC':comments,'INPUT.CTL':controls,
        'QANALY.COM':scripted(image,lines+['G'])}
    commands=['B:DASM /VER','QANALY']
    for name,(origin,payload) in cases.items():
        commands += [f'B:ZSM4 {name}={name}.ASM',f'B:LINK {name}[A]']
    names=['SESSION.ALL','DSA00000.SYM','DSA00000.DOC','DSA00000.CTL','OUT.SYM','OUT.DOC','OUT.CTL']
    names += [name+ext for name in cases for ext in ('.ASM','.REL','.COM')]
    report={'scope':'native mixed-data/session/origin gate; release acceptance pending','platforms':{}}
    for platform in a.platforms:
        log,out=campaign(platform,files,commands,a.output/platform,system=a.system,utilities=a.utilities,
            extract=names,utility_files={'DASM.COM':image})
        assert b'DASM RESIDENT CANARY PASS' in log and b'DASM RESIDENT CANARY FAIL' not in log,log[-2000:]
        assert b'insufficient' not in log.lower() and b'Errors: 0' in log,log[-2000:]
        for name,(origin,payload) in cases.items():
            restored=out[name+'.COM']
            assert restored[:len(payload)]==payload,(platform,name,restored[:24].hex())
            assert len(restored)==(len(payload)+127)//128*128 and set(restored[len(payload):])<={26},(platform,name,len(restored))
        descriptor=out['SESSION.ALL']
        assert len(descriptor)==128 and descriptor[:5]==b'BCDS\x02'
        assert int.from_bytes(descriptor[124:],'little')==zlib.crc32(descriptor[:124])
        assert int.from_bytes(descriptor[10:14],'little')==4 and int.from_bytes(descriptor[8:10],'little')==0x1200
        assert int.from_bytes(descriptor[27:31],'little')==zlib.crc32(binary)
        for i,name in enumerate(('DSA00000.SYM','DSA00000.DOC','DSA00000.CTL')):
            entry=descriptor[31+i*19:50+i*19];data=out[name]
            assert int.from_bytes(entry[13:15],'little')*128==len(data)
            assert int.from_bytes(entry[15:19],'little')==zlib.crc32(data)
        expected=b'1200 ALIAS\r\n1201 INSIDE\r\nFFFF LAST\r\n1200 START\r\n'
        assert out['OUT.SYM'].split(b'\x1a',1)[0]==expected
        assert out['OUT.DOC'].split(b'\x1a',1)[0]==comments
        assert out['OUT.CTL'].split(b'\x1a',1)[0]==controls
        report['platforms'][platform]={'status':'PASS','cases':list(cases),'session_crc_and_tables':True,
            'resident_canary':True,'source_sha256':hashlib.sha256(image).hexdigest(),
            'utilities_members_verified':True,'execution_report':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'session/component CRCs, aliases/comments/controls and four native origin round trips',flush=True)
if __name__=='__main__':main()
