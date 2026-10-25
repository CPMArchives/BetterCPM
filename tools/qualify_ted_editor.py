#!/usr/bin/env python3
"""Disposable real-terminal TED integration gate; source/payload-bound evidence."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from build_ted import ROOT, build
from dasm_native import campaign, compact_source, cpm_text
from qualify_ted_engine import print_helpers


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',default=['z80pack','trs80gp'])
    p.add_argument('--cross-smoke',action='store_true')
    p.add_argument('--scenario',choices=['basic','groups','large','interaction'],default='basic')
    p.add_argument('--installed',action='store_true')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross',identity_state='assigned')
    native=cpm_text(compact_source((a.output/'cross/TEDNAT.MAC').read_text().rstrip('\x1a')))
    original=b'Original\t spaces  \r\nLF\nCR\rend  '
    original+=b'\x1a'*(-len(original)%128)
    if a.scenario=='groups':original=cpm_text('one\ntwo\nthree\nfour\n')
    if a.scenario=='interaction':original=b'ALPHA BETA  \r\nSECOND\tEND\nTHIRD\rLAST'
    if a.scenario=='large':original=cpm_text(('long file with literal TAB\t and trailing spaces  \r\n'*900).rstrip('\r\n'))
    original+=b'\x1a'*(-len(original)%128)
    edited=original.replace(b'SECOND',b'CHANGED') if a.scenario=='interaction' else b'X'+original[1:]
    if a.scenario=='interaction':edited=edited.rstrip(b'\x1a')+b'\x1a'*(-len(edited.rstrip(b'\x1a'))%128)
    listing=(a.output/'cross/TEDDEV.LST').read_text()
    def address(name):
        return int(re.search(r'(?mi)^([0-9a-f]+)\s+.*?\s'+name+r':',listing)[1],16)
    top=address('TED_STACK_TOP');guard=address('WL_GUARD')
    post_source=f''' ASEG
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
QC_PASS: DB ' TED EDITOR POSTEXIT PASS',13,10,'$'
QC_BAD: DB 'TED GUARD FAIL',13,10,'$'
{print_helpers()}
 END
'''
    (a.output/'QPOST.MAC').write_text(post_source)
    subprocess.run([str(Path.home()/'bin/z80asm'),'-e32','-fb','-o'+str((a.output/'QPOST.BIN').resolve()),str(a.output/'QPOST.MAC')],check=True)
    post=(a.output/'QPOST.BIN').read_bytes()
    if post[:256]==bytes(256):post=post[256:]


    report={'status':'IN_PROGRESS','scope':'interactive startup/edit/save/exit integration gate; full acceptance separate',
            'scenario':a.scenario,'installed':a.installed,'payload_sha256':hashlib.sha256(image).hexdigest(),'platforms':{}}
    for platform in a.platforms:
        native_platform=platform=='trs80gp'
        files={'INPUT.TXT':original,'QPOST.COM':post}
        commands=(['RSX UNLOAD ADM3A','RSX LOAD ANSI'] if native_platform else
                  ['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'])
        if a.installed:pass
        elif a.cross_smoke:files['TEDDEV.COM']=image
        else:
            files['TEDNAT.MAC']=native
            commands=['B:ZSM4 TEDDEV=TEDNAT','B:LINK TEDDEV[A]']+commands
        sequence=[(b'S\r',b'^Z command',60),(b'X',b'Xriginal',90),
                  (b'\x0b',b'^K...',30),(b'S',b'replace? Y/N:',90),
                  (b'Y\r',b'Saved.',120),(b'\x0b',b'^K...',30),
                  (b'Q',b'TED EDITOR POSTEXIT PASS' if native_platform else b'C0>_ ',90)]
        executable='B:TED' if a.installed else 'TEDDEV'
        screen_ready=b'^Z command  ^K file/range  OVR'.ljust(80)+b' '*80 if native_platform else b'^Z command'
        if a.scenario=='groups':
            files['INSERT.TXT']=cpm_text('read line\n')
            files['INSERT.TXT']+=b'\x1a'*(-len(files['INSERT.TXT'])%128)
            sequence=[(b'S\r',b'^Z command',60)]
            def key(code,wanted):sequence.append((code,wanted,120))
            def prefix(suffix,prompt):
                key(b'\x0b',b'^K...');key(suffix,prompt)
            prefix(b'C',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'After line:');key(b'3\r',b'Copied.')
            prefix(b'V',b'First line:');key(b'4\r',b'Last line:');key(b'4\r',b'After line:');key(b'1\r',b'Moved.')
            prefix(b'Y',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'Deleted.')
            prefix(b'R',b'R arguments:');key(b'(1) INSERT.TXT\r',b'Read.')
            prefix(b'W',b'W arguments:');key(b'2 2 WRITE.TXT\r',b'Written.')
            prefix(b'Y',b'First line:');key(b'2\r',b'Last line:');key(b'2\r',b'Deleted.')
            prefix(b'X',b'replace? Y/N:');key(b'Y\r',b'TED EDITOR POSTEXIT PASS' if native_platform else b'C0>_ ')
        if a.scenario=='interaction':
            command_ready=b'TED> _'.ljust(80) if native_platform else b'TED>'
            sequence=[(b'SU /SECOND/CHANGED/\r',command_ready,120),
                      (b'P 1\r',command_ready,30),
                      (b'/ALPHA/\r',b'Found.',120),
                      (b'\x14',b'BETA'.ljust(80) if native_platform else b'BETA',120),
                      (b'\x16',b'INS',30),(b'ALPHA ',b'ALPHA BETA',120),
                      (b'\x16',b'OVR',30)]
            for control in (1,6,19,4,5,24,18,3,17,15,12,21,31):
                # Current Model 4 MCON has no populated physical US chord;
                # never synthesize a press in an unused matrix position.
                if native_platform and control==31:continue
                sequence.append((bytes([control]),b'^Z command',30))
            sequence += [(b'\x0e',b'BROWSE',30),(b'\r',b'^Z command',30),
                         (b'\x1a',b'TED>',30),(b'P 1\r',command_ready,30),
                         (b'W\r',b'replace? Y/N:',120),
                         (b'Y\r',command_ready,120),(b'S\r',b'^Z command',30),
                         (b'\x0b',b'^K...',30),
                         (b'Q',b'TED EDITOR POSTEXIT PASS' if native_platform else b'C0>_ ',90)]
        if a.scenario=='large':
            # One in-line overwrite of a file larger than twice free editor RAM;
            # exact full-file publication and backup are checked on the host.
            sequence=[(b'S\r',b'^Z command',60),(b'X',b'Xong',120),
                      (b'\x0b',b'^K...',30),(b'X',b'replace? Y/N:',120),
                      (b'Y\r',b'TED EDITOR POSTEXIT PASS' if native_platform else b'C0>_ ',240)]
        if native_platform:interactive=sequence
        else:
            interactive=[((executable+' INPUT.TXT\r').encode(),b'TED>',240)]+sequence+[(b'QPOST\r',b'TED EDITOR POSTEXIT PASS',30)]
        log,outputs=campaign(platform,files,commands,a.output/platform,system=a.system,
            utilities=a.utilities,extract=([] if a.installed else ['TEDDEV.COM'])+['INPUT.TXT','TEB00000.BAK']+(['INSERT.TXT','WRITE.TXT'] if a.scenario=='groups' else []),
            utility_files={'TED.COM':image} if a.installed else None,
            interactive=interactive,interactive_launch=executable+' INPUT.TXT' if native_platform else None,
            interactive_followup='QPOST',interactive_prompt='TED>',
            interactive_frames=[60 for x in sequence] if native_platform else None,
            interactive_ready=[x[1].decode() for x in sequence] if native_platform else None)
        if a.scenario=='groups':
            assert outputs['INPUT.TXT']==original
            assert outputs['INSERT.TXT']==original,(platform,outputs['INSERT.TXT'])
            assert outputs['TEB00000.BAK']==files['INSERT.TXT']
            assert outputs['WRITE.TXT']==files['INSERT.TXT']
        else:
            assert outputs['INPUT.TXT']==edited,(platform,len(outputs['INPUT.TXT']))
            assert outputs['TEB00000.BAK']==original
        if not a.installed:assert outputs['TEDDEV.COM'][:len(image)]==image
        measured=re.search(rb'TED STACK HIGH WATER (\d+) TPA CEILING (\d+)',log)
        assert measured and int(measured[1])<=1536, ('stack reserve',measured)
        assert b'TED GUARD FAIL' not in log
        if a.scenario=='large':
            assert len(original)>2*(int(measured[2])-(len(image)+256)), 'fixture fits available RAM'

        assert b'TED EDITOR POSTEXIT PASS' in log
        report['platforms'][platform]={'status':'PASS','stack_high_water':int(measured[1]),'tpa_ceiling':int(measured[2]),'private_stack_bytes':2048,'guard_bytes':64,'physical_redraw_chord':'UNAVAILABLE' if native_platform else 'terminal US tested','native_build':not a.cross_smoke and not a.installed,
            'native_cross_parity':not a.cross_smoke and not a.installed,'execution':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'interactive editor integration',flush=True)
    report['status']='PASS';(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
