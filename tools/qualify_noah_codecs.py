#!/usr/bin/env python3
"""Qualify production NOAH phase overlays and codec transactions on both targets."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import subprocess
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


def disk_filler(assembler,out):
    # Disposable qualification media only. Fill after SUBMIT has materialized
    # its work file; leave enough directory entries for zero-length outputs.
    text=''' ORG 100H
 LD DE,FCB
 LD C,22
 CALL 5
 CP 255
 JR Z,BAD
 LD DE,BUFFER
 LD C,26
 CALL 5
LOOP: LD DE,FCB
 LD C,21
 CALL 5
 OR A
 JR NZ,FULL
 LD HL,(LEFT)
 DEC HL
 LD (LEFT),HL
 LD A,H
 OR L
 JR NZ,LOOP
 JR BAD
FULL: LD DE,FCB
 LD C,16
 CALL 5
 CP 255
 JR Z,BAD
 LD DE,DONE
 JR PRINT
BAD: LD DE,ERROR
PRINT: LD C,9
 CALL 5
 JP 0
LEFT: DW 8192
FCB: DB 0,'NFILL   DAT'
 REPT 24
 DB 0
 ENDM
BUFFER: DS 128
DONE: DB 'NOAH DISK FILL DONE',13,10,'$'
ERROR: DB 'NOAH DISK FILL FAILED',13,10,'$'
 END
'''
    return assemble(assembler,out,'NFILL',text)[0]


def near_full(raw,definition,folder):
    # Reserve four blocks for startup/SUBMIT; NFILL consumes the small remainder
    # natively. Filling the entire Model 4 volume through console automation
    # would spend the campaign on unrelated long extent writes.
    def run(*args):
        return subprocess.run(args,cwd=folder,check=True,capture_output=True)
    before=run('fsck.cpm','-T','raw','-f',definition,'-n',str(raw))
    used,total=map(int,re.findall(rb'(\d+)/(\d+) blocks',before.stdout+before.stderr)[-1])
    defs=(folder/'diskdefs').read_text()
    section=re.search(r'diskdef '+re.escape(definition)+r'\s+(.*?)\bend\b',defs,re.S)[1]
    block=int(re.search(r'blocksize\s+(\d+)',section)[1])
    size=(total-used-4)*block
    assert size>0
    base=folder/'NBASE.DAT';base.write_bytes(bytes(size))
    run('cpmcp','-T','raw','-f',definition,str(raw),str(base),'0:NBASE.DAT')
    after=run('fsck.cpm','-T','raw','-f',definition,'-n',str(raw))
    now,maximum=map(int,re.findall(rb'(\d+)/(\d+) blocks',after.stdout+after.stderr)[-1])
    assert maximum-now==4
    (folder/'full-media-preparation.json').write_text(json.dumps({
        'block_bytes':block,'used_before':used,'total_blocks':total,
        'reserved_free_blocks':4,'prefill_bytes':size,'prefill_sha256':sha(base.read_bytes())},indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,default=ROOT/'build/ted-qualified-utilities')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    p.add_argument('--reuse-build',type=Path,help='Reuse retained parity-checked native groups for unchanged source')
    p.add_argument('--reuse-ark-runtime',type=Path,help='Reuse an exact input/command-matched retained ARK runtime campaign')
    p.add_argument('--ark-lzw',action='store_true',help='Qualify production ARC methods 5-9 decoding and dictionary workspace')
    p.add_argument('--ark-squeezed',action='store_true',help='Qualify production ARC method-4 decoding')
    p.add_argument('--ark-packed',action='store_true',help='Qualify production ARC method-3 decoding')
    p.add_argument('--ark-cli',action='store_true',help='Qualify stored ARK LIST/TEST/EXTRACT production integration')
    p.add_argument('--coverage-recovery',action='store_true',help='Qualify observed audit coverage and recovery summaries')
    p.add_argument('--member-accounting',action='store_true',help='Qualify extraction totals and ADD candidate accounting')
    p.add_argument('--outcome-reporting',action='store_true',help='Qualify final command outcomes and batch dispositions')
    p.add_argument('--staged-failures',action='store_true',help='Qualify stage cleanup and Retry/Skip on full media')
    p.add_argument('--source-failures',action='store_true',help='Qualify safe source-preflight choices')
    p.add_argument('--quiet-reporting',action='store_true',help='Run the bounded quiet-reporting native campaign')
    p.add_argument('--stamp-delta-from',type=Path,help='Qualify only the timestamp diagnostic delta from a retained full campaign')
    a=p.parse_args();a.output=a.output.resolve();a.system=a.system.resolve();a.utilities=a.utilities.resolve()
    systems=verify_system(a.system,a.platforms)
    a.output.mkdir(parents=True,exist_ok=False)
    cross=a.output/'cross';assembler=Path.home()/'bin/z80asm';image=build(assembler,cross)
    ovl=(cross/'NOAH.OVL').read_bytes();layout=json.loads((cross/'layout.json').read_text())
    names=['NOAH','NHCLI','NCSQ','NCUSQ','NCCR','NCUNCR','NHARK','NCLZW','NCAR8']
    expected={n:(cross/(n+'.bin')).read_bytes() for n in names}
    tools={n:(ROOT/'third_party'/folder/n).read_bytes() for n,folder in [('ZSM4.COM','zsm4'),('LINK.COM','dri-link')]}
    report={'scope':'NOAH production phases; ARK methods 1-9 decoding, isolated method-8 encoder phase, LBR and standalone codecs',
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
        for number,group in enumerate((names[:2],names[2:6],names[6:])):
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
        if a.ark_lzw or a.ark_packed or a.ark_squeezed:
            if a.ark_lzw:
                from test_noah_ark_lzw import lzw,fixtures as lzw_fixtures
                from test_ark import member,crc16
                small,_=lzw_fixtures()
                small_members=b''.join(lzw(small,method,f'M{method}.BIN'.encode()) for method in range(5,10))
                small_members+=lzw(b'',8,b'EMPTY8.BIN')+lzw(b'',9,b'EMPTY9.BIN')
                rng=random.Random(517)
                maximum=bytes(rng.randrange(256) for _ in range(20000))
                large_members=lzw(maximum,8,b'FULL8.BIN')+lzw(maximum,9,b'FULL9.BIN')
                cases={'ALL.ARC':small_members+b'\x1a\0','FULL.ARC':large_members+b'\x1a\0'}
                invalid={
                    'BADCRC.ARC':bytearray(lzw(small,5,b'BADCRC.BIN')),
                    'BADSTAT.ARC':member(b'\xff',5,b'BAD5.BIN',logical=1,crc=crc16(b'A')),
                    'BADDYN.ARC':member(b'\x0c\x2c\x01',8,b'BAD8.BIN',logical=1,crc=crc16(b'A')),
                }
                invalid['BADCRC.ARC'][23]^=1
                cases.update({name:(bytes(data)+b'\x1a\0') for name,data in invalid.items()})
                pins=json.loads((ROOT/'tests/fixtures/noah/references.json').read_text())['artifacts']
                historical={}
                for name in ('crc32a.arc','de-lbr.arc','nulu15.arc'):
                    raw=(ROOT/'build/noah-proof/references'/name).read_bytes()
                    assert sha(raw)==pins[name]['sha256']
                    cpm_name=name.upper()
                    historical[cpm_name]=raw
                cases.update(historical)
                payload=small
                method=5
            elif a.ark_squeezed:
                from test_noah_ark_squeezed import fixtures
            else:
                from test_noah_ark_packed import fixtures
            from test_usq_com import padded
            if not a.ark_lzw:
                payload,cases=fixtures()
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,**cases}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            if a.ark_lzw:
                method='5-9'
                commands=prefix+['NCMEM','NOAH /Q /LIST ALL.ARC','NOAH /Q /TEST ALL.ARC',
                    'NOAH /Q /X /Y ALL.ARC','NOAH /Q /TEST FULL.ARC',
                    'NOAH /Q /X /Y BADCRC.ARC','NOAH /Q /X /Y BADSTAT.ARC',
                    'NOAH /Q /X /Y BADDYN.ARC']
                for name in historical:
                    commands.extend(['NOAH /Q /LIST '+name,'NOAH /Q /TEST '+name])
                wanted=[f'M{i}.BIN' for i in range(5,10)]+['EMPTY8.BIN','EMPTY9.BIN']
                log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                    extract=wanted+list(cases),utility_files=tools,timeout=900)
                assert outputs['M5.BIN']==padded(payload)
                for i in range(6,10):assert outputs[f'M{i}.BIN']==padded(payload)
                assert outputs['EMPTY8.BIN']==outputs['EMPTY9.BIN']==b''
                assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[
                    b'success']*4+[b'failure']*3+[b'success']*2+[b'warning/partial']*2+[b'success']*2
                assert b'unsupported' not in log and b'Insufficient transient' not in log
                assert b'verified 00000007; unavailable/ambiguous: 00000000' in log
                assert b'Archive/read error 08' in log
                assert layout['lzw_bytes']==1705 and layout['lzw_workspace'][1]==47488
                required=layout['lzw_workspace'][1]
                assert layout['required_ceilings'][6]==required
                assert required < 0xC501 < 0xCA01
                report['workspace_proof']={'overlay_bytes':layout['lzw_bytes'],'dictionary_bytes':24576,
                    'workspace_start_hex':f"{layout['lzw_workspace'][0]:04X}",
                    'required_end_hex':f'{required:04X}','z80pack_ceiling_hex':'C501',
                    'model4_ceiling_hex':'CA01','z80pack_headroom':0xC501-required,
                    'model4_headroom':0xCA01-required,
                    'native_max_dictionary_case_bytes':len(maximum),
                    'runtime_cases':'static and dynamic dictionaries, full 8/13-bit paths, validated 20 KiB output sink'}
                report['qualification_mode']='ARC methods 5-9 decode, historical interoperability and 24 KiB workspace proof'
                report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':'C501' if platform=='z80pack' else 'CA01',
                    'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                    'runtime_console_sha256':sha(log)}
                (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                print('PASS',platform,'native ARC methods 5-9 and 24 KiB dictionary workspace',flush=True)
                continue
            stem='SQUEEZED' if a.ark_squeezed else 'PACKED'
            method=4 if a.ark_squeezed else 3
            commands=prefix+['NCMEM',f'NOAH /Q /LIST {stem}.ARC',f'NOAH /Q /TEST {stem}.ARC',
                f'NOAH /Q /X /Y {stem}.ARC','NOAH /Q /X /Y EMPTY.ARC']
            bad_names=list(cases)[2:]
            commands += ['NOAH /Q /X /Y '+n for n in bad_names]
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=[stem+'.BIN','EMPTY.BIN']+list(cases),utility_files=tools,timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[b'success']*4+[b'failure']*len(bad_names)
            assert b'unsupported' not in log and b'operation stopped' not in log
            assert b'verified 00000001; unavailable/ambiguous: 00000000' in log
            assert outputs[stem+'.BIN']==padded(payload) and outputs['EMPTY.BIN']==b''
            for n,b in cases.items():assert outputs[n]==b,n
            report['qualification_mode']=f'ARC method-{method} streaming decode, integrity and safe extraction'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,f'native method-{method} decode and corruption refusal with providers loaded',flush=True)
            continue
        if a.ark_cli:
            from test_noah_ark import fixtures
            from test_usq_com import padded
            cases=fixtures()
            lbr=with_crcs(archive([entry(b'LBR     DAT')],b'L'*128))
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   **cases,'ONE.LBR':lbr}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /LIST STORED.ARC','NOAH /Q /TEST STORED.ARC',
                'NOAH /Q /X /Y STORED.ARC','NOAH /Q /LIST MIXED.ARK','NOAH /Q /TEST MIXED.ARK',
                'NOAH /Q /X /Y MIXED.ARK','NOAH /Q /X /Y BAD.ARC','NOAH /Q /X /Y DUP.ARC',
                'NOAH /Q /TEST TAIL.ARC','NOAH /Q /X /Y TAIL.ARC',
                'NOAH /Q /X /Y EMPTY.ARC','NOAH /Q /X /Y ONE.LBR','NOAH /VER']
            outputs_wanted=['OLD.TXT','ZERO.BIN','FIRST.TXT','LAST.TXT','TAIL.TXT','LBR.DAT']
            retained=a.reuse_ark_runtime/platform/'runtime' if a.reuse_ark_runtime else None
            wanted=outputs_wanted+list(cases)+['ONE.LBR']
            if retained and (retained/'execution.json').is_file():
                audit=json.loads((retained/'execution.json').read_text())
                assert audit['commands']==commands and audit['original_media_unchanged']
                assert audit['system_sha256']==systems[platform]['image_sha256']
                assert all(audit['input_hashes'][n]==sha(b) for n,b in files.items())
                assert audit['utilities_members']=={n:sha(b) for n,b in tools.items()}
                log=(retained/'console.bin').read_bytes();assert sha(log)==audit['console_sha256']
                outputs={n:(retained/('after-'+n)).read_bytes() for n in wanted}
                assert all(sha(b)==audit['outputs'][n] for n,b in outputs.items())
                runtime_evidence={'runtime_reused_from':str(retained)}
            else:
                log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                    extract=wanted,utility_files=tools,timeout=600)
                runtime_evidence={}

            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert b'Insufficient transient' not in log and b'operation stopped' not in log
            assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[
                b'success',b'success',b'success',b'warning/partial',b'warning/partial',b'warning/partial',
                b'failure',b'failure',b'warning/partial',b'warning/partial',b'warning/no-work',b'success']
            assert b'Archive/read error 08' in log and b'Archive/read error 09' in log
            assert b'ARK method 08: unsupported' in log and b'opaque trailer: unvalidated' in log
            assert b'verified 00000002; unavailable/ambiguous: 00000001' in log
            for n,b in zip(outputs_wanted,(b'old',b'\0'*129,b'hello',b'last',b'tail',b'L'*128)):
                assert outputs[n]==padded(b),(n,outputs[n])
            for n,b in {**cases,'ONE.LBR':lbr}.items():assert outputs[n]==b,n
            report['qualification_mode']='ARK stored production LIST/TEST/EXTRACT and unchanged LBR extraction'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log),**runtime_evidence}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native ARK stored integration with terminal providers loaded',flush=True)
            continue
        if a.coverage_recovery:
            first=b'A'*128;second=b'B'*128
            good=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],first+second))
            bad=bytearray(good);bad[256]^=1
            missing=archive([entry(b'THIRD   DAT')],b'C'*128)
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   'GOOD.LBR':good,'BAD.LBR':bytes(bad),'MISS.LBR':missing}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /LIST GOOD.LBR','NOAH /Q /TEST GOOD.LBR',
                'NOAH /Q /TEST *.LBR','NOAH /Q /TEST GOOD.LBR FIRST.*','NOAH /Q /X /Y GOOD.LBR']
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['FIRST.DAT','SECOND.DAT'],timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert b'LIST: contents not tested.' in log
            assert b'Known CRC regions (hex): verified 00000005; unavailable/ambiguous: 00000002' in log
            assert b'Known CRC regions (hex): verified 00000002; unavailable/ambiguous: 00000000' in log
            assert b'Listed members (hex): 00000003' in log
            assert log.count(b'Recovery artifacts reported (hex): 00000000')==5
            assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[b'success',b'success',b'warning/partial',b'success',b'success']
            assert outputs['FIRST.DAT']==first and outputs['SECOND.DAT']==second
            report['qualification_mode']='observed coverage and recovery summaries'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native observed coverage and recovery summaries with terminal providers loaded',flush=True)
            continue
        if a.member_accounting:
            first=b'A'*128;second=b'B'*128;third=b'C'*128
            one=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],first+second))
            two=with_crcs(archive([entry(b'THIRD   DAT',start=1)],third))
            payloads=[bytes(range(128)),b'compress me '*10+bytes(8)]
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   'LIB1.LBR':one,'LIB2.LBR':two,'SRC1.BIN':payloads[0],'SRC2.BIN':payloads[1]}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /X /Y LIB?.LBR','NOAH /Q /ADD OUT.LBR SRC?.BIN',
                            'NOAH /Q /ADD /SQ SQOUT.LBR SRC?.BIN']
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['FIRST.DAT','SECOND.DAT','THIRD.DAT','OUT.LBR','SQOUT.LBR'],timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert b'Known members (hex): completed 00000003; skipped: 00000000; failed: 00000000' in log
            assert log.count(b'ADD candidates (hex): completed 00000002; skipped: 00000000; failed: 00000000')==2
            assert log.count(b'Accepted candidates (hex): 0002')==2
            assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[b'success']*3
            assert [outputs[n] for n in ('FIRST.DAT','SECOND.DAT','THIRD.DAT')]==[first,second,third]
            for name in ('OUT.LBR','SQOUT.LBR'):
                raw=outputs[name];check_crc(raw);rows=members(raw);assert len(rows)==2
                for row,payload in zip(rows,payloads):
                    start=int.from_bytes(row[12:14],'little')*128
                    length=int.from_bytes(row[14:16],'little')*128
                    data=raw[start:start+length]
                    if name=='SQOUT.LBR':assert host_decode(data,record_padding=True)[1]==payload
                    else:assert data==payload
            report['qualification_mode']='extraction totals and ADD candidate accounting'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native extraction totals and ADD candidates with terminal providers loaded',flush=True)
            continue
        if a.outcome_reporting:
            data=bytes(range(128))
            raw=with_crcs(archive([entry(b'TEXT    DAT')],data))
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   'TEXT.DAT':data,'GOOD.LBR':raw,'BAD.LBR':b'bad archive'}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NOAH /Q /TEST GOOD.LBR','NOAH /Q /LIST GOOD.LBR NONE.*',
                'NOAH /Q /TEST *.LBR','NOAH /Q /TEST BAD.LBR','NOAH /Q /BOGUS GOOD.LBR',
                'NOAH /Q /SQ TEXT.DAT','NOAH /Q /ADD OUT.LBR TEXT.DAT']
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['TEXT.DQT','OUT.LBR'],timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            outcomes=re.findall(rb'Outcome: ([a-z/-]+)\.',log)
            assert outcomes==[b'success',b'warning/no-work',b'warning/partial',b'failure',
                              b'failure',b'success',b'success'],outcomes
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            assert b'completed 0000; no-match 0001; skipped 0000' in log
            assert host_decode(outputs['TEXT.DQT'],record_padding=True)[1]==data
            check_crc(outputs['OUT.LBR']);assert len(members(outputs['OUT.LBR']))==1
            report['qualification_mode']='final outcomes and batch dispositions'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'outcomes':[x.decode() for x in outcomes],
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native command outcomes with terminal providers loaded',flush=True)
            continue
        if a.staged_failures:
            rng=random.Random(506);data=bytes(rng.randrange(256) for _ in range(8192))
            raw=with_crcs(archive([entry(b'FIRST   DAT',start=1,records=64),
                                  entry(b'EMPTY   DAT',start=65,records=0)],data))
            post=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00NOAH STAGED POSTEXIT PASS\r\n$'
            files={'NOAH.COM':native['NOAH'],'NOAH.OVL':bytes(native_ovl),'NCMEM.COM':mem,
                   'NFILL.COM':disk_filler(assembler,cross),'NFPOST.COM':post,'TEST.LBR':raw}
            prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
            commands=prefix+['NCMEM','NFILL']
            question=b'Retry/Skip/Abort?';launch='NOAH /X TEST.LBR'
            if platform=='trs80gp':
                sequence=[(b'R',question,120),(b'S',b'NOAH STAGED POSTEXIT PASS',120)]
            else:
                sequence=[((launch+'\r').encode(),question,120),(b'R',question,120),
                          (b'S',b'Unprocessed (hex):',120),(b'NFPOST\r',b'NOAH STAGED POSTEXIT PASS',60)]
            log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=a.utilities,
                extract=['EMPTY.DAT'],setup=near_full,interactive=sequence,interactive_launch=launch if platform=='trs80gp' else None,
                interactive_followup='NFPOST' if platform=='trs80gp' else None,interactive_prompt=question.decode(),
                interactive_frames=[3600,600] if platform=='trs80gp' else None,
                interactive_ready=[question.decode(),'NOAH STAGED POSTEXIT PASS'] if platform=='trs80gp' else None,
                timeout=600)
            ceiling='C501' if platform=='z80pack' else 'CA01'
            assert outputs['EMPTY.DAT']==b''
            assert ('NOAH QUAL TPA '+ceiling).encode() in log
            for text in (b'NOAH DISK FILL DONE',b'R/S/A [S]: R',b'R/S/A [S]: S',
                         b'NOAH STAGED POSTEXIT PASS',b'failed: 00000001',b'Unprocessed (hex): 00000000'):
                assert text in log,text
            assert b'NOAH DISK FILL FAILED' not in log
            report['qualification_mode']='staged failures on full media'
            report['platforms'][platform]={'status':'PASS','native_groups':groups,'runtime_ceiling_hex':ceiling,
                'native_outputs':{n:sha(b) for n,b in native.items()},'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
                'runtime_console_sha256':sha(log)}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'native stage Retry/Skip on full disposable media',flush=True)
            continue
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
