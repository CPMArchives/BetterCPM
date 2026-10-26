#!/usr/bin/env python3
"""One boot per target: native parity, installed editor workflows and real capacity.

All expected text is independent fixture data. API probes are host assembled;
product native ZSM4/LINK parity is a separate, explicit build observation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from build_ted import build,source
from dasm_native import campaign,compact_source,cpm_text
from qualify_ted_engine import probe,checkpoint,INITIAL,ORIGINAL,RECOVERED,padded,print_helpers

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def assemble(work,name,text):
    p=work/(name+'.MAC');p.write_text(text)
    out=work/(name+'.BIN')
    subprocess.run([str(Path.home()/'bin/z80asm'),'-e32','-fb','-o'+str(out),str(p)],check=True)
    b=out.read_bytes()
    return b[256:] if b[:256]==bytes(256) else b


def postcheck(work,name,tag,listing):
    addr=lambda n:int(re.search(r'(?mi)^([0-9a-f]+)\s+.*?\s'+n+r':',listing)[1],16)
    top,guard=addr('TED_STACK_TOP'),addr('WL_GUARD')
    return assemble(work,name,f''' ASEG
 ORG 100H
 LD HL,{top-2048-32}
 CALL QC_GUARD
 LD HL,{guard}
 CALL QC_GUARD
 LD HL,{top-2048}
QC_SCAN:
 LD A,(HL)
 CP 0A5H
 JR NZ,QC_FOUND
 INC HL
 LD DE,{top}
 OR A
 SBC HL,DE
 ADD HL,DE
 JR NZ,QC_SCAN
QC_FOUND:
 LD DE,{top}
 EX DE,HL
 OR A
 SBC HL,DE
 PUSH HL
 LD DE,QC_STACK
 LD C,9
 CALL 5
 POP HL
 CALL TD_HLDEC
 LD DE,QC_TPA
 LD C,9
 CALL 5
 LD HL,(6)
 CALL TD_HLDEC
 LD DE,QC_PASS
 LD C,9
 CALL 5
 RET
QC_GUARD:
 LD B,32
QC_CHECK:
 LD A,(HL)
 CP 0A5H
 JP NZ,QC_FAIL
 INC HL
 DJNZ QC_CHECK
 RET
QC_FAIL:
 LD DE,QC_BAD
 LD C,9
 CALL 5
 JP 0
QC_STACK: DB 'TED STACK HIGH WATER $'
QC_TPA: DB ' TPA CEILING $'
QC_PASS: DB ' TED {tag} PASS',13,10,'$'
QC_BAD: DB 'TED GUARD FAIL',13,10,'$'
{print_helpers()}
 END
''')


def qualify(system,utilities,output,platform,skip_native_build=False,reuse_groups=None):
    output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',output/'cross',identity_state='assigned')
    listing=(output/'cross/TEDDEV.LST').read_text()
    group=padded(b'one\r\ntwo\r\nthree\r\nfour\r\n')
    mixed=padded(b'ALPHA BETA  \r\nSECOND\tEND\nTHIRD\rLAST')
    large=padded((b'long file with literal TAB\t and trailing spaces  \r\n'*900).rstrip(b'\r\n'))
    insert=padded(b'read line\n')
    drive=1 if platform=='trs80gp' else 3
    maintained,_=source()
    api=maintained.replace(' JP TE_START\n',' JP TD_START\n',1).replace('TED_END EQU $',probe(drive,'TED_STACK_TOP')+'\nTED_END EQU $')
    files={'IGRP.TXT':group,'IMIX.TXT':mixed,'ILARGE.TXT':large,'INSERT.TXT':insert,
           'INPUT.TXT':padded(INITIAL),'CHECKP.TMP':checkpoint(drive),'BAD.TXT':padded(b'good\x1aBAD'),
           'EXIST.TXT':padded(ORIGINAL),'TEDCORE.COM':padded(assemble(output,'TEDCORE',api)),
           'ENDPROBE.COM':bytes.fromhex('1109010e09cd0500c9')+b'TED ALL DONE\r\n$'}
    bad=bytearray(checkpoint(drive));bad[8]^=1;files['BADCKP.TMP']=bytes(bad)
    for name,tag in [('QGROUP','GROUPS'),('QMIX','INTERACTION'),('QLARGE','LARGE')]:
        files[name+'.COM']=postcheck(output,name,tag,listing)
    native=platform=='trs80gp'
    # Native source/REL coexist with the complete fixtures on the 800K native
    # System work copy. The 332K simulator work disk uses a separate native-build gate.
    commands=['RSX UNLOAD ADM3A','RSX LOAD ANSI'] if native else ['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:']
    if native and not skip_native_build:
        files['TEDNAT.MAC']=cpm_text(compact_source((output/'cross/TEDNAT.MAC').read_text().rstrip('\x1a')))
        commands=['B:ZSM4 TEDDEV=TEDNAT','B:LINK TEDDEV[A]']+commands
    seq=[]
    def key(b,ready):seq.append((b,ready,1800))
    def k(suffix,ready):key(b'\x0b',b'^K...');key(suffix,ready)
    def prompt():key(b'',b'TED>')
    command_ready=b'TED>'
    if not native:key(b'B:TED IGRP.TXT\r',b'TED>')
    key(b'S\r',b'^Z command')
    k(b'C',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'After line:');key(b'3\r',b'Copied.')
    k(b'V',b'First line:');key(b'4\r',b'Last line:');key(b'4\r',b'After line:');key(b'1\r',b'Moved.')
    k(b'Y',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'Deleted.')
    k(b'R',b'R arguments:');key(b'(1) INSERT.TXT\r',b'Read.')
    k(b'W',b'W arguments:');key(b'2 2 WRITE.TXT\r',b'Written.')
    k(b'Y',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'Deleted.')
    k(b'X',b'replace? Y/N:');key(b'Y\r',b'TED GROUPS PASS' if native else b'C0>_ ')
    if native:prompt()
    else:
        key(b'QGROUP\r',b'TED GROUPS PASS');key(b'B:TED IMIX.TXT\r',b'TED>')
    key(b'SU /SECOND/CHANGED/\r',command_ready);key(b'P 1\r',command_ready)
    key(b'/ALPHA/\r',b'Found.');key(b'\x14',b'BETA'.ljust(80) if native else b'BETA  ');key(b'\x16',b'INS')
    key(b'ALPHA ',b'ALPHA BETA');key(b'\x16',b'OVR')
    for control in (1,6,19,4,5,24,18,3,17,15,12,21,31):
        if native and control==31:continue
        key(bytes([control]),b'^Z command')
    key(b'\x0e',b'BROWSE');key(b'\r',b'^Z command');key(b'\x1a',b'TED>')
    key(b'P 1\r',command_ready);key(b'W\r',b'replace? Y/N:');key(b'Y\r',command_ready)
    key(b'S\r',b'^Z command');k(b'Q',b'TED INTERACTION PASS' if native else b'C0>_ ')
    if native:prompt()
    else:
        key(b'QMIX\r',b'TED INTERACTION PASS');key(b'B:TED ILARGE.TXT\r',b'TED>')
    key(b'S\r',b'^Z command');key(b'X',b'Xong');k(b'X',b'replace? Y/N:')
    key(b'Y\r',b'TED LARGE PASS' if native else b'C0>_ ')
    if native:key(b'',b'TED ALL DONE')
    else:
        key(b'QLARGE\r',b'TED LARGE PASS');key(b'TEDCORE\r',b'TED ENGINE NATIVE PASS.')
        key(b'ENDPROBE\r',b'TED ALL DONE')
    reused=None
    if reuse_groups:
        assert native and skip_native_build
        reused=json.loads((reuse_groups/'report.json').read_text())
        assert reused['status']=='PASS' and reused['payload_sha256']==sha(image)
        assert reused['platforms'][platform]['groups_outputs_verified']
        begin=next(i for i,item in enumerate(seq) if item[0].startswith(b'SU '))
        seq=[(b'',b'TED>',1800)]+seq[begin:]
    extract=['IGRP.TXT','INSERT.TXT','WRITE.TXT','IMIX.TXT','ILARGE.TXT',
             'TEB00000.BAK','TEB00001.BAK','TEB00002.BAK','TEB00003.BAK',
             'FIRST.TXT','SECOND.TXT','BLOCK.TXT','RECOVER.TXT','AFTERB.TXT','AFTERC.TXT','EXIST.TXT']
    if reuse_groups:
        extract.remove('WRITE.TXT');extract.remove('TEB00003.BAK')
    if native and not skip_native_build:extract+=['TEDDEV.COM']
    log,outputs=campaign(platform,files,commands,output/platform,system=system,utilities=utilities,
        extract=extract,utility_files={'TED.COM':image},interactive=seq,timeout=3600,input_wait_frames=600000,
        interactive_launch=('B:TED IMIX.TXT' if reuse_groups else 'B:TED IGRP.TXT') if native else None,
        interactive_followup=('QMIX\r\nB:TED ILARGE.TXT\r\nQLARGE\r\nTEDCORE\r\nENDPROBE' if reuse_groups else 'QGROUP\r\nB:TED IMIX.TXT\r\nQMIX\r\nB:TED ILARGE.TXT\r\nQLARGE\r\nTEDCORE\r\nENDPROBE'),
        interactive_prompt='TED>',interactive_frames=[3600 if x[1]==command_ready else 600 for x in seq] if native else None,
        interactive_ready=[x[1].decode() for x in seq] if native else None)
    if native and not skip_native_build:assert outputs['TEDDEV.COM'][:len(image)]==image
    expected={'IGRP.TXT':group,'INSERT.TXT':group,'WRITE.TXT':insert,
              'IMIX.TXT':padded(mixed.rstrip(b'\x1a').replace(b'SECOND',b'CHANGED')),
              'ILARGE.TXT':b'X'+large[1:], 'TEB00000.BAK':insert,
              'TEB00001.BAK':mixed,'TEB00002.BAK':large,'TEB00003.BAK':padded(ORIGINAL)}
    if reuse_groups:
        expected.pop('WRITE.TXT');expected['INSERT.TXT']=insert
        expected['TEB00000.BAK']=mixed;expected['TEB00001.BAK']=large
        expected['TEB00002.BAK']=padded(ORIGINAL);expected.pop('TEB00003.BAK')
    edited=INITIAL[:3]+b'\t '+INITIAL[3:]
    expected.update({'FIRST.TXT':padded(INITIAL),'SECOND.TXT':padded(edited),
                     'BLOCK.TXT':padded(edited[2:-2]),'RECOVER.TXT':padded(RECOVERED),
                     'AFTERB.TXT':padded(RECOVERED),'AFTERC.TXT':padded(RECOVERED),'EXIST.TXT':padded(RECOVERED)})
    for name,wanted in expected.items():assert outputs[name]==wanted,(name,len(outputs[name]),sha(outputs[name]),sha(wanted))
    assert b'TED CAPACITY PASS:' in log and b'TED ENGINE NATIVE FAIL' not in log
    assert b'TED GUARD FAIL' not in log and b'TED ALL DONE' in log
    measured=re.findall(rb'TED STACK HIGH WATER (\d+) TPA CEILING (\d+) TED (GROUPS|INTERACTION|LARGE) PASS',log)
    results={tag.decode():{'stack_high_water':int(used),'tpa_ceiling':int(ceiling)} for used,ceiling,tag in measured}
    if reuse_groups:
        assert set(results)=={'INTERACTION','LARGE'}
        results['GROUPS']=reused['platforms'][platform]['scenarios']['GROUPS']
        execution=json.loads((output/platform/'execution.json').read_text())
        old_execution=json.loads((reuse_groups/platform/'execution.json').read_text())
        assert all(execution[k]==old_execution[k] for k in ('system_sha256','utilities_sha256'))
    assert set(results)=={'GROUPS','INTERACTION','LARGE'}
    assert all(v['stack_high_water']<=1536 for v in results.values())
    assert len(large)>2*(results['LARGE']['tpa_ceiling']-(len(image)+256))
    used=[int(v) for v in re.findall(rb'TED ENGINE NATIVE PASS\. Stack high-water: (\d+)',log)]
    assert used and max(used)<=1536
    proof={'status':'PASS','native_cross_parity':native and not skip_native_build,'native_build':native and not skip_native_build,
           'stack_high_water':max(v['stack_high_water'] for v in results.values()),'private_stack_bytes':2048,
           'guard_bytes':64,'tpa_ceiling':results['LARGE']['tpa_ceiling'],'scenarios':results,
           'reused_groups_receipt_sha256':sha((reuse_groups/'report.json').read_bytes()) if reuse_groups else None,
           'physical_redraw_chord':'UNAVAILABLE' if native else 'terminal US tested',
           'api_stack_high_water':max(used),'execution':platform+'/execution.json'}
    report={'status':'PASS','scope':('completed groups reused from separately verified identical payload/pair; one-boot interaction/large/real-capacity API' if reuse_groups else 'one-boot installed groups/interaction/large and real-capacity API execution; native product parity separate field'),
            'installed':True,'payload_sha256':sha(image),'platforms':{platform:proof},'large_file_bytes':len(large)}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',platform,'native/installed workflows/capacity',flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True);p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--platform',choices=['z80pack','trs80gp'],required=True)
    p.add_argument('--skip-native-build',action='store_true',help='use a separate existing native build/parity receipt')
    p.add_argument('--reuse-groups',type=Path,help='reuse completed groups on the identical payload and original paired media')
    a=p.parse_args();qualify(a.system,a.utilities,a.output,a.platform,a.skip_native_build,a.reuse_groups)
