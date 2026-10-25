#!/usr/bin/env python3
"""Qualify production NOAH phase overlays and codec transactions on both targets."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import struct
from build_noah import build,ROOT
from noah_overlays import assemble
from dasm_native import campaign
from qualify_noah_proof import verify_system
from test_lbr import archive,entry,with_crcs
from test_lbr_write import members,check_crc
from test_usq import squeeze
from test_cr import reference
from test_sq import host_decode
from test_uncr import decode


def sha(b):return hashlib.sha256(b).hexdigest()


def native_match(raw,expected):
    assert raw[:len(expected)]==expected,'native machine-code mismatch'
    assert len(raw)==(len(expected)+127)//128*128,'native record count'
    assert set(raw[len(expected):])<={26},'native tail padding'


def probe(assembler,out):
    text=''' ORG 100H
 LD DE,TEXT
 LD C,9
 CALL 5
 LD A,(7)
 CALL HEX
 LD A,(6)
 CALL HEX
 LD DE,NL
 LD C,9
 CALL 5
 JP 0
HEX: PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 CALL NIB
 POP AF
NIB: AND 15
 ADD A,'0'
 CP '9'+1
 JR C,DIGIT
 ADD A,7
DIGIT: LD E,A
 LD C,2
 JP 5
TEXT: DB 'NOAH QUAL TPA ','$'
NL: DB 13,10,'$'
 END
'''
    return assemble(assembler,out,'NCMEM',text)[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,default=ROOT/'build/ted-qualified-utilities')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    p.add_argument('--reuse-build',type=Path,help='Reuse retained parity-checked native groups for unchanged source')
    p.add_argument('--source-failures',action='store_true',help='Qualify safe source-preflight choices')
    p.add_argument('--quiet-reporting',action='store_true',help='Run the bounded quiet-reporting native campaign')
    p.add_argument('--stamp-delta-from',type=Path,help='Qualify only the timestamp diagnostic delta from a retained full campaign')
    a=p.parse_args();a.output=a.output.resolve();a.system=a.system.resolve();a.utilities=a.utilities.resolve()
    systems=verify_system(a.system,a.platforms)
    a.output.mkdir(parents=True,exist_ok=False)
    cross=a.output/'cross';assembler=Path.home()/'bin/z80asm';image=build(assembler,cross)
    ovl=(cross/'NOAH.OVL').read_bytes();layout=json.loads((cross/'layout.json').read_text())
    names=['NOAH','NHCLI','NCSQ','NCUSQ','NCCR','NCUNCR']
    expected={n:(cross/(n+'.bin')).read_bytes() for n in names}
    tools={n:(ROOT/'third_party'/folder/n).read_bytes() for n,folder in [('ZSM4.COM','zsm4'),('LINK.COM','dri-link')]}
    report={'scope':'NOAH production controller/codec phase integration; LBR and codec commands only',
      'layout':layout,'verified_systems':systems,'resident_sha256':sha(image),
      'companion_sha256':sha(ovl),'platforms':{}}
    if a.stamp_delta_from:
        old=a.stamp_delta_from/'cross'
        previous=(old/'NHCLI.bin').read_bytes();current=expected['NHCLI']
        assert len(previous)==len(current)
        changed=[i for i,(x,y) in enumerate(zip(previous,current)) if x!=y]
        assert 1<=len(changed)<=2 and max(changed)-min(changed)<2
        assert any(current[j]==previous[j]==0xC3 and set(changed)<=set((j+1,j+2)) for j in range(max(0,min(changed)-2),min(changed)))
        assert (old/'NOAH.bin').read_bytes()[:-128]==expected['NOAH'][:-128]
        for n in names[2:]:assert (old/(n+'.bin')).read_bytes()==expected[n]
        report['qualification_mode']='timestamp diagnostic delta'
        report['full_baseline_report_sha256']=sha((a.stamp_delta_from/'report.json').read_bytes())
        report['controller_changed_offsets']=changed
    mem=probe(assembler,cross)
    for platform in a.platforms:
        base=a.output/platform;base.mkdir()
        native={};groups=[]
        for number,group in enumerate((names[:2],names[2:])):
            folder=base/('build-'+str(number))
            if a.reuse_build:
                old=a.reuse_build/platform/('build-'+str(number))
                try:
                    retained={n:(old/('after-'+n+'.COM')).read_bytes() for n in group}
                    for n in group:native_match(retained[n],expected[n])
                except (AssertionError,FileNotFoundError):
                    pass
                else:
                    native.update(retained)
                    groups.append({'reused':str(old),'status':'PASS'})
                    continue
            files={n+'.MAC':(cross/(n+'.MAC')).read_bytes() for n in group}
            prefix=['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN'] if platform=='trs80gp' else []
            commands=prefix+[f'B:ZSM4 {n}={n}' for n in group]+[f'B:LINK {n}[A]' for n in group]
            log,outputs=campaign(platform,files,commands,folder,system=a.system,utilities=a.utilities,
                extract=[n+'.COM' for n in group],utility_files=tools,timeout=600)
            assert re.findall(rb'Errors: +([0-9]+)',log)==[b'0']*len(group),log[-3000:]
            for n in group:
                native[n]=outputs[n+'.COM'];native_match(native[n],expected[n])
            groups.append({'execution':folder.name+'/execution.json','console_sha256':sha(log),'status':'PASS'})
        # Construct the companion from native module bytes with the same header
        # and zero record fill. Parity must include the complete result.
        native_ovl=bytearray(ovl[:128])
        for n in names[1:]:
            body=native[n][:len(expected[n])]
            native_ovl.extend(body+bytes(-len(body)%128))
        assert bytes(native_ovl)==ovl
        if a.source_failures:
            payload=b'safe next source\x00\x1a\xff'
            post=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00NOAH FAILURE POSTEXIT PASS\r\n$'
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                'FAIL1.SQ':b'\x76\xfdunsupported','FAIL2.SQ':squeeze(payload,name=b'RESULT.TXT'),'NFPOST.COM':post}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /Y /EXPAND FAIL1.SQ']
            question=b'Retry/Skip/Abort?'
            launch='NOAH /Q /EXPAND FAIL*.SQ'
            if platform=='trs80gp':
                sequence=[(b'R',question,60),(b'S',b'NOAH FAILURE POSTEXIT PASS',120)]
            else:
                sequence=[((launch+'\r').encode(),question,60),(b'R',question,60),
                          (b'S',b'Files (hex): selected',120),(b'NFPOST\r',b'NOAH FAILURE POSTEXIT PASS',60)]
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['RESULT.TXT'],interactive=sequence,interactive_launch=launch if platform=='trs80gp' else None,
                interactive_followup='NFPOST' if platform=='trs80gp' else None,interactive_prompt=question.decode(),
                interactive_frames=[3600,600] if platform=='trs80gp' else None,
                interactive_ready=[question.decode(),'NOAH FAILURE POSTEXIT PASS'] if platform=='trs80gp' else None,
                timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert outputs['RESULT.TXT']==payload+bytes([26])*(-len(payload)%128)
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            for text in (question,b'codec operation failed',b'NOAH FAILURE POSTEXIT PASS',b'unprocessed 0000'):
                assert text in log,text
            report['qualification_mode']='safe source failures'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native source Retry/Skip with loaded terminal providers',flush=True)
            continue
        if a.quiet_reporting:
            data=bytes(range(128))
            raw=with_crcs(archive([entry(b'TEXT    DAT')],data))
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   'TEXT.DAT':data,'TEST.LBR':raw,'BAD.BIN':b'\x76\xfdunsupported'}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /LIST TEST.LBR','NOAH /Q /X /Y TEST.LBR',
                'NOAH /Q /SQ TEXT.DAT','NOAH /Q /EXPAND /Y TEXT.DQT',
                'NOAH /Q /ADD /SQ /Y OUT.LBR TEXT.DAT','NOAH /Q /TEST OUT.LBR',
                'NOAH /Q /REMOVE /Y OUT.LBR TEXT.DQT','NOAH /Q /EXPAND BAD.BIN']
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['TEXT.DAT','TEXT.DQT','OUT.LBR'],timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert outputs['TEXT.DAT']==data and host_decode(outputs['TEXT.DQT'],record_padding=True)[1]==data
            check_crc(outputs['OUT.LBR']);assert members(outputs['OUT.LBR'])[0][0]==254
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            for text in (b'verified codec output published',b'extracted and verified',b'LBR update verified and published',b' -> stored member '):
                assert text not in log,text
            for text in (b'TEXT     DAT',b'Archives (hex): selected',b'Files (hex): selected',b'Accepted source versions',
                         b'explicit compression increased',b'BAD.BIN',b'codec operation failed',b'TEXT    .DQT'):
                assert text in log,text
            report['qualification_mode']='quiet reporting'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native quiet reporting with terminal providers loaded',flush=True)
            continue
        if a.stamp_delta_from:
            payload=b'preserve stamped bytes'
            wire=squeeze(payload,name=b'STAMPED.TXT');tail=-len(wire)%128
            member=bytearray(entry(b'STAMPED TQT',records=(len(wire)+127)//128,pad=tail));member[18]=1
            stamped=with_crcs(archive([bytes(member)],wire+bytes([26])*tail))
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,'STAMP.LBR':stamped}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            log,outputs=campaign(platform,files,prefix+['NCMEM','NOAH /X /EXPAND STAMP.LBR'],base/'runtime',
                system=a.system,utilities=a.utilities,extract=['STAMPED.TXT'],timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert outputs['STAMPED.TXT']==payload+bytes([26])*(-len(payload)%128)
            assert b'Timestamp not restored: filesystem service unavailable.' in log
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert b'codec operation failed' not in log
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native timestamp diagnostic delta with terminal providers loaded',flush=True)
            continue
        rng=random.Random(501);data=bytes(rng.randrange(256) for _ in range(4096))
        original=with_crcs(archive([entry(b'BINARY  DAT',records=32)],data))
        bad=bytearray(ovl);bad[-8]^=1
        boot=native['NOAH'];assert boot.count(b'NOAH    OVL')==1
        files={'NOAH.COM':boot,'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
          'BINARY.DAT':data,'ORASQ.BIN':squeeze(data,name=b'ORASQ.DAT'),
          'ORACR.BIN':reference(data,name=b'ORACR.DAT'),
          'REPLACE.LBR':original,'REMOVE.LBR':original,'COMPACT.LBR':original,
          'BAD.OVL':bytes(bad),'NOBAD.COM':boot.replace(b'NOAH    OVL',b'BAD     OVL'),
          'MISSING.COM':boot.replace(b'NOAH    OVL',b'MISSING OVL')}
        prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
        commands=prefix+['NCMEM','NOAH /VER','NOAH /SQ BINARY.DAT','NOAH /CR BINARY.DAT',
          'NOAH /EXPAND /Y BINARY.DQT','NOAH /EXPAND /Y BINARY.DZT',
          'NOAH /EXPAND ORASQ.BIN','NOAH /EXPAND ORACR.BIN',
          'NOAH /ADD /SQ SQ.LBR BINARY.DAT','NOAH /ADD /CR CR.LBR BINARY.DAT',
          'NOAH /X /EXPAND /Y SQ.LBR','NOAH /X /EXPAND /Y CR.LBR',
          'NOAH /TEST SQ.LBR','NOAH /TEST CR.LBR',
          'NOAH /ADD CREATED.LBR BINARY.DAT','NOAH /ADD /Y REPLACE.LBR BINARY.DAT',
          'NOAH /REMOVE /Y REMOVE.LBR BINARY.DAT',
          'NOAH /REMOVE /COMPACT /Y COMPACT.LBR BINARY.DAT',
          'NOAH /ADD /CAPACITY=1 LIMITED.LBR BINARY.DAT',
          'NOBAD /SQ BINARY.DAT','MISSING /VER','MISSING /SQ BINARY.DAT']
        extract=['BINARY.DAT','BINARY.DQT','BINARY.DZT','ORASQ.DAT','ORACR.DAT',
                 'SQ.LBR','CR.LBR','CREATED.LBR','REPLACE.LBR','REMOVE.LBR','COMPACT.LBR','LIMITED.LBR']
        log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
              extract=extract,timeout=900)
        assert outputs['BINARY.DAT']==outputs['ORASQ.DAT']==outputs['ORACR.DAT']==data
        assert host_decode(outputs['BINARY.DQT'],record_padding=True)[1]==data
        assert decode(outputs['BINARY.DZT'])[0]==data
        for n in ['SQ.LBR','CR.LBR','CREATED.LBR','REPLACE.LBR','REMOVE.LBR','COMPACT.LBR','LIMITED.LBR']:
            check_crc(outputs[n])
        assert [r[0] for r in members(outputs['REPLACE.LBR'])]==[254,0]
        assert outputs['REPLACE.LBR'][128:128+len(data)]==data
        assert members(outputs['REMOVE.LBR'])[0][0]==254
        assert len(outputs['COMPACT.LBR'])==128 and not members(outputs['COMPACT.LBR'])
        assert int.from_bytes(outputs['LIMITED.LBR'][14:16],'little')==1
        ceiling=b'C501' if platform=='z80pack' else b'CA01'
        assert b'NOAH QUAL TPA '+ceiling in log,log[-4000:]
        assert log.count(b'operation stopped')==2,log[-4000:]
        assert b'codec operation failed' not in log and b'update failed' not in log
        # A separate larger fixture exercises Model 4 extent transitions without
        # filling the smaller z80pack work disk with all acceptance outputs.
        rng=random.Random(502);large=bytes(rng.randrange(256) for _ in range(20480))
        extent_files={'NOAH.COM':boot,'NOAH.OVL':ovl,'BIG.BIN':large,'NCMEM.COM':mem}
        extent_commands=prefix+['NCMEM','NOAH /ADD /CR BIG.LBR BIG.BIN',
             'NOAH /X /EXPAND /Y BIG.LBR','NOAH /TEST BIG.LBR']
        elog,eout=campaign(platform,extent_files,extent_commands,base/'extent',system=a.system,
             utilities=a.utilities,extract=['BIG.LBR','BIG.BIN'],timeout=600)
        assert eout['BIG.BIN']==large;check_crc(eout['BIG.LBR'])
        assert b'codec operation failed' not in elog and b'update failed' not in elog and b'Integrity checks complete' in elog
        report['platforms'][platform]={'status':'PASS','native_groups':groups,
          'runtime_ceiling_hex':ceiling.decode(),'native_outputs':{n:sha(b) for n,b in native.items()},
          'runtime_outputs':{n:sha(b) for n,b in outputs.items()},'extent_outputs':{n:sha(b) for n,b in eout.items()},
          'runtime_console_sha256':sha(log),'extent_console_sha256':sha(elog),'cross_extent_source_bytes':len(large)}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'six native modules, loaded-RSX codec/LBR commands and cross-extent writes',flush=True)


if __name__=='__main__':main()
