#!/usr/bin/env python3
"""Native TED text/workspace/publisher gate on disposable paired media.

The probe assembles the maintained engine instructions and calls their public
APIs. It is not an editor UI or WordStar compatibility acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zlib

from build_ted import source, native_source
from dasm_native import campaign, compact_source, cpm_text

ROOT = Path(__file__).resolve().parents[1]
INITIAL = b'\tKeep  \r\nLF\nCR\rno final  '
RECOVERED = b'recovered\t  \r\nno final newline  '
ORIGINAL = b'protected original\r\n'


def padded(data):
    return data+b'\x1a'*(-len(data) % 128)


def descriptor(drive, filename):
    name, _, extension = filename.partition('.')
    return bytes([drive])+(name.ljust(8)+extension.ljust(3)).encode()+bytes(25)


def checkpoint(drive):
    data = padded(RECOVERED)
    h = bytearray(128)
    h[:8] = b'BCTED001'
    h[8:12] = zlib.crc32(data).to_bytes(4, 'little')
    h[12:15] = len(RECOVERED).to_bytes(3, 'little')
    h[15:17] = (len(data)//128).to_bytes(2, 'little')
    h[17:20] = (2).to_bytes(3, 'little')
    h[20], h[21] = 1, 1
    h[22:59] = descriptor(drive, 'RECOVER.TXT')
    h[124:128] = zlib.crc32(h[:124]).to_bytes(4, 'little')
    return bytes(h)+data


def print_helpers():
    return r"""
TD_PUTC:
 PUSH AF
 PUSH BC
 PUSH DE
 PUSH HL
 LD E,A
 LD C,2
 CALL 5
 POP HL
 POP DE
 POP BC
 POP AF
 RET
TD_HLDEC:
 LD DE,10000
 CALL TD_DIGIT
 LD DE,1000
 CALL TD_DIGIT
 LD DE,100
 CALL TD_DIGIT
 LD DE,10
 CALL TD_DIGIT
 LD DE,1
TD_DIGIT:
 LD A,'0'-1
TD_DIGIT_LOOP:
 INC A
 OR A
 SBC HL,DE
 JR NC,TD_DIGIT_LOOP
 ADD HL,DE
 JP TD_PUTC
"""


def capacity_probe(drive):
    fcb = lambda name: ','.join(str(x) for x in descriptor(drive,name)[:36])
    return r"""
 ; Reserve exactly one allocation block for the few-block test.
 LD DE,TD_ONE
 CALL TD_MAKE_ABSENT
 LD DE,TD_FILLBUF
 LD C,26
 CALL 5
 LD DE,TD_ONE
 LD C,21
 CALL 5
 OR A
 JP NZ,TD_FAIL
 LD DE,TD_ONE
 LD C,16
 CALL 5
 CP 255
 JP Z,TD_FAIL
 LD DE,TD_FILL
 CALL TD_MAKE_ABSENT
 LD HL,0
 LD (TD_FILLCOUNT),HL
TD_FILL_LOOP:
 LD DE,TD_FILLBUF
 LD C,26
 CALL 5
 LD DE,TD_FILL
 LD C,21
 CALL 5
 OR A
 JR NZ,TD_FILLED
 LD HL,(TD_FILLCOUNT)
 INC HL
 LD (TD_FILLCOUNT),HL
 LD DE,8192
 OR A
 SBC HL,DE
 JP NC,TD_FAIL
 JR TD_FILL_LOOP
TD_FILLED:
 LD DE,TD_FILL
 LD C,16
 CALL 5
 CP 255
 JP Z,TD_FAIL
 LD HL,(TD_FILLCOUNT)
 LD DE,100
 OR A
 SBC HL,DE
 JP C,TD_FAIL
 CALL TD_FREE_BLOCKS
 LD A,H
 OR L
 JP NZ,TD_FAIL
 CALL TD_PREP_SMALL
 LD A,14
 LD (TD_STAGE),A
 CALL TW_EDIT
 JP NC,TD_FAIL
 ; Deleting our one-record fixture frees exactly one allocation block.
 LD DE,TD_ONE
 LD C,19
 CALL 5
 CP 255
 JP Z,TD_FAIL
 CALL TD_FREE_BLOCKS
 DEC HL
 LD A,H
 OR L
 JP NZ,TD_FAIL
 LD HL,TD_LARGE_SEG
 LD DE,TW_SEGMENTS
 LD BC,7
 LDIR
 LD A,1
 LD (TW_SEGCOUNT),A
 LD A,15
 LD (TD_STAGE),A
 CALL TW_EDIT
 JP NC,TD_FAIL
 CALL TD_FREE_BLOCKS
 LD A,H
 OR L
 JP NZ,TD_FAIL
 ; Release only the filler created above; the failed stage is retained.
 LD DE,TD_FILL
 LD C,19
 CALL 5
 CP 255
 JP Z,TD_FAIL
 CALL TD_FREE_BLOCKS
 LD A,H
 OR L
 JP Z,TD_FAIL
 LD HL,0
 LD (TD_DIRCOUNT),HL
TD_DIR_LOOP:
 LD DE,TD_DIRFCB
 LD C,17
 CALL 5
 CP 255
 JR NZ,TD_DIR_NEXT
 LD DE,TD_DIRFCB
 LD C,22
 CALL 5
 CP 255
 JR Z,TD_DIR_FULL
 LD DE,TD_DIRFCB
 LD C,16
 CALL 5
 CP 255
 JP Z,TD_FAIL
 LD HL,(TD_DIRCOUNT)
 INC HL
 LD (TD_DIRCOUNT),HL
TD_DIR_NEXT:
 LD HL,TD_DIRFCB+8
 LD B,5
TD_DIR_INCREMENT:
 INC (HL)
 LD A,(HL)
 CP '9'+1
 JR C,TD_DIR_RESET
 LD (HL),'0'
 DEC HL
 DJNZ TD_DIR_INCREMENT
 JP TD_FAIL
TD_DIR_RESET:
 LD HL,TD_DIRFCB+12
 LD DE,TD_DIRFCB+13
 LD BC,23
 LD (HL),0
 LDIR
 JR TD_DIR_LOOP
TD_DIR_FULL:
 LD HL,(TD_DIRCOUNT)
 LD DE,20
 OR A
 SBC HL,DE
 JP C,TD_FAIL
 CALL TD_FREE_BLOCKS
 LD A,H
 OR L
 JP Z,TD_FAIL
 CALL TD_PREP_SMALL
 LD A,16
 LD (TD_STAGE),A
 CALL TW_EDIT
 JP NC,TD_FAIL
 LD HL,TD_CAPMSG
 CALL TD_PRINT
 LD HL,(TD_FILLCOUNT)
 CALL TD_HLDEC
 LD HL,TD_DIRMSG
 CALL TD_PRINT
 LD HL,(TD_DIRCOUNT)
 CALL TD_HLDEC
 LD HL,TD_NEWLINE
 CALL TD_PRINT
 JP TD_CAP_DONE
TD_PREP_SMALL:
 LD HL,TD_SMALL_SEG
 LD DE,TW_SEGMENTS
 LD BC,7
 LDIR
 LD A,1
 LD (TW_SEGCOUNT),A
 RET
TD_MAKE_ABSENT:
 PUSH DE
 LD C,17
 CALL 5
 POP DE
 CP 255
 JP NZ,TD_FAIL
 LD C,22
 CALL 5
 CP 255
 JP Z,TD_FAIL
 RET
; Public CPM DPB/ALV services, read-only: prove disk-full vs directory-full.
TD_FREE_BLOCKS:
 LD C,31
 CALL 5
 LD DE,5
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 INC DE
 LD (TD_BLOCKS),DE
 LD C,27
 CALL 5
 LD (TD_ALV),HL
 LD HL,0
 LD (TD_FREE),HL
 LD A,128
 LD (TD_MASK),A
TD_ALV_LOOP:
 LD HL,(TD_ALV)
 LD A,(TD_MASK)
 AND (HL)
 JR NZ,TD_ALV_USED
 LD HL,(TD_FREE)
 INC HL
 LD (TD_FREE),HL
TD_ALV_USED:
 LD A,(TD_MASK)
 SRL A
 JR NZ,TD_ALV_MASK
 LD HL,(TD_ALV)
 INC HL
 LD (TD_ALV),HL
 LD A,128
TD_ALV_MASK:
 LD (TD_MASK),A
 LD HL,(TD_BLOCKS)
 DEC HL
 LD (TD_BLOCKS),HL
 LD A,H
 OR L
 JR NZ,TD_ALV_LOOP
 LD HL,(TD_FREE)
 RET
TD_CAPMSG: DB 'TED CAPACITY PASS: full-data records ',0
TD_DIRMSG: DB '; one-block refusal; full-directory entries ',0
TD_FILLCOUNT: DW 0
TD_DIRCOUNT: DW 0
TD_BLOCKS: DW 0
TD_ALV: DW 0
TD_FREE: DW 0
TD_MASK: DB 0
TD_FILL: DB """+fcb('TDFILL.TMP')+r"""
TD_ONE: DB """+fcb('TDONE.TMP')+r"""
TD_DIRFCB: DB """+fcb('TDF00000.TMP')+r"""
TD_LARGE_SEG: DB 4,0,0,0,160,15,0
TD_SMALL_SEG: DB 1,0,0,0,"""+str(len(RECOVERED))+r""",0,0
TD_FILLBUF:
 REPT 128
 DB 0
 ENDM
TD_CAP_DONE:
"""


def probe(drive, stack):
    parts = [f'''TD_START:
 LD HL,(6)
 LD DE,TED_END
 OR A
 SBC HL,DE
 JP C,0
 LD HL,{stack}-TED_STACK_SIZE-32
 LD DE,{stack}-TED_STACK_SIZE-31
 LD BC,TED_STACK_SIZE+31
 LD (HL),0A5H
 LDIR
 LD SP,{stack}
 CALL TW_INIT
''']
    def copy(name, target):
        parts.append(f' LD HL,{name}\n LD DE,{target}\n LD BC,37\n LDIR\n')
    def call(entry, stage, failure_expected=False):
        parts.append(f' LD A,{stage}\n LD (TD_STAGE),A\n CALL {entry}\n JP '+('NC' if failure_expected else 'C')+',TD_FAIL\n')
    copy('TD_AREA', 'TW_AREA')
    copy('TD_INPUT', 'TW_INPUT')
    call('TW_LOAD', 1)
    copy('TD_FIRST', 'TS_TARGET')
    call('TW_SAVE', 2)
    parts.append(' LD HL,TD_SEGMENTS\n LD DE,TW_SEGMENTS\n LD BC,21\n LDIR\n LD A,3\n LD (TW_SEGCOUNT),A\n LD A,9\n LD (TW_INSERT),A\n LD A,32\n LD (TW_INSERT+1),A\n')
    call('TW_EDIT', 3)
    copy('TD_SECOND', 'TS_TARGET')
    call('TW_SAVE', 4)
    parts.append(f' LD HL,TD_BLOCKSEG\n LD DE,TW_SEGMENTS\n LD BC,7\n LDIR\n LD A,1\n LD (TW_SEGCOUNT),A\n')
    copy('TD_BLOCK', 'TS_TARGET')
    call('TW_WRITE_BLOCK', 5)
    copy('TD_CHECKPOINT', 'TW_INPUT')
    call('TW_RECOVER', 6)
    copy('TD_RECOVERED', 'TS_TARGET')
    call('TW_SAVE', 7)
    copy('TD_BAD', 'TW_INPUT')
    call('TW_LOAD', 8, True)
    copy('TD_AFTER_BAD', 'TS_TARGET')
    call('TW_SAVE', 9)
    copy('TD_BAD_CK', 'TW_INPUT')
    call('TW_RECOVER', 10, True)
    copy('TD_AFTER_CK', 'TS_TARGET')
    call('TW_SAVE', 11)
    parts.append(' LD HL,TD_PROTECTED+9\n SET 7,(HL)\n INC HL\n SET 7,(HL)\n LD DE,TD_PROTECTED\n LD C,30\n CALL 5\n CP 255\n JP Z,TD_FAIL\n')
    copy('TD_EXIST', 'TS_TARGET')
    parts.append(' LD A,1\n LD (TS_REPLACE),A\n XOR A\n LD (TS_PROTECT),A\n')
    call('TW_SAVE', 12, True)
    parts.append(' LD A,1\n LD (TS_PROTECT),A\n')
    call('TW_SAVE', 13)
    parts.append(capacity_probe(drive))
    parts.append(f''' LD HL,{stack}-TED_STACK_SIZE-32
 LD B,32
TD_GUARD:
 LD A,(HL)
 CP 0A5H
 JP NZ,TD_FAIL
 INC HL
 DJNZ TD_GUARD
 LD HL,TD_PASS
 CALL TD_PRINT
 LD HL,{stack}-TED_STACK_SIZE
TD_SCAN:
 LD A,(HL)
 CP 0A5H
 JR NZ,TD_USED
 INC HL
 JR TD_SCAN
TD_USED:
 EX DE,HL
 LD HL,{stack}
 OR A
 SBC HL,DE
 LD A,'0'
 CALL TD_HLDEC
 LD HL,TD_NEWLINE
 CALL TD_PRINT
 JP 0
TD_FAIL:
 LD HL,TD_ERROR
 CALL TD_PRINT
 LD A,(TD_STAGE)
 LD L,A
 LD H,0
 LD A,'0'
 CALL TD_HLDEC
 LD HL,TD_NEWLINE
 CALL TD_PRINT
 JP 0
TD_PRINT:
 LD A,(HL)
 OR A
 RET Z
 CALL TD_PUTC
 INC HL
 JR TD_PRINT
TD_STAGE: DB 0
TD_PASS: DB 'TED ENGINE NATIVE PASS. Stack high-water: ',0
TD_ERROR: DB 'TED ENGINE NATIVE FAIL stage ',0
TD_NEWLINE: DB 13,10,0
TD_SEGMENTS: DB 1,0,0,0,3,0,0,2,0,0,0,2,0,0,1,3,0,0,{len(INITIAL)-3},0,0
TD_BLOCKSEG: DB 1,2,0,0,{len(INITIAL)-2},0,0
''')
    parts.append(print_helpers())
    names = {'TD_AREA': 'IGNORED.TMP', 'TD_INPUT': 'INPUT.TXT', 'TD_FIRST': 'FIRST.TXT',
             'TD_SECOND': 'SECOND.TXT', 'TD_BLOCK': 'BLOCK.TXT', 'TD_CHECKPOINT': 'CHECKP.TMP',
             'TD_RECOVERED': 'RECOVER.TXT', 'TD_BAD': 'BAD.TXT', 'TD_AFTER_BAD': 'AFTERB.TXT',
             'TD_BAD_CK': 'BADCKP.TMP', 'TD_AFTER_CK': 'AFTERC.TXT',
             'TD_PROTECTED': 'EXIST.TXT', 'TD_EXIST': 'EXIST.TXT'}
    for label, filename in names.items():
        parts.append(label+': DB '+','.join(str(x) for x in descriptor(drive, filename))+'\n')
    return ''.join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--utilities', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--platforms', nargs='+', choices=['z80pack', 'trs80gp'], default=['z80pack', 'trs80gp'])
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    maintained, mapping = source()
    report = {'status': 'IN_PROGRESS', 'scope': 'native text/workspace/recovery/publisher and real capacity API gates; UI separate',
              'editor_qualified': False, 'source_sha256': hashlib.sha256(maintained.encode()).hexdigest(), 'platforms': {}}
    for platform in a.platforms:
        cross = a.output/('cross-'+platform)
        cross.mkdir()
        drive = 1 if platform == 'trs80gp' else 3
        text = maintained.replace(' JP TE_START\n', ' JP TD_START\n', 1)
        text = text.replace('TED_END EQU $', probe(drive, 'TED_STACK_TOP')+'\nTED_END EQU $')
        (cross/'TEDCORE.MAC').write_text(text)
        subprocess.run([str(Path.home()/'bin/z80asm'), '-e32', '-fb', '-o'+str((cross/'TEDCORE.BIN').resolve()),
                        '-l'+str((cross/'TEDCORE.LST').resolve()), str((cross/'TEDCORE.MAC').resolve())], check=True)
        binary = (cross/'TEDCORE.BIN').read_bytes()
        native = cpm_text(compact_source(native_source(text)))
        recovery = checkpoint(drive)
        bad = bytearray(recovery)
        bad[8] ^= 1
        files = {'TEDNAT.MAC': native, 'INPUT.TXT': padded(INITIAL), 'CHECKP.TMP': recovery,
                 'BADCKP.TMP': bytes(bad), 'BAD.TXT': padded(b'good\x1aBAD'), 'EXIST.TXT': padded(ORIGINAL)}
        outputs = ['TEDCORE.COM', 'FIRST.TXT', 'SECOND.TXT', 'BLOCK.TXT', 'RECOVER.TXT',
                   'AFTERB.TXT', 'AFTERC.TXT', 'EXIST.TXT', 'TEB00000.BAK']
        log, data = campaign(platform, files, ['B:ZSM4 TEDCORE=TEDNAT', 'B:LINK TEDCORE[A]', 'TEDCORE'],
                             a.output/platform, system=a.system, utilities=a.utilities, extract=outputs)
        assert b'Errors: 0' in log and b'UNDEFINED SYMBOLS' not in log.upper()
        assert b'TED ENGINE NATIVE FAIL' not in log
        assert b'TED CAPACITY PASS:' in log
        used = [int(x) for x in re.findall(rb'TED ENGINE NATIVE PASS\. Stack high-water: ([0-9]+)', log)]
        assert used and max(used) <= 2048-512, used
        actual = data['TEDCORE.COM']
        assert actual[:len(binary)] == binary
        assert len(actual) == (len(binary)+127)//128*128 and set(actual[len(binary):]) <= {26}
        edited = INITIAL[:3]+b'\t '+INITIAL[3:]
        expected = {'FIRST.TXT': padded(INITIAL), 'SECOND.TXT': padded(edited),
                    'BLOCK.TXT': padded(edited[2:-2]), 'RECOVER.TXT': padded(RECOVERED),
                    'AFTERB.TXT': padded(RECOVERED), 'AFTERC.TXT': padded(RECOVERED),
                    'EXIST.TXT': padded(RECOVERED), 'TEB00000.BAK': padded(ORIGINAL)}
        for name, wanted in expected.items():
            assert data[name] == wanted, (platform, name, data[name], wanted)
        report['platforms'][platform] = {'status': 'PASS', 'native_cross_parity': True,
                                       'stack_high_water': max(used), 'stack_reserved': 2048,
                                       'observed_margin': 2048-max(used), 'low_canary_bytes': 32,
                                       'payload_sha256': hashlib.sha256(binary).hexdigest(),
                                       'execution': platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', platform, 'native text/workspace/recovery/safe publication', flush=True)
    report['status'] = 'PASS'
    (a.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
