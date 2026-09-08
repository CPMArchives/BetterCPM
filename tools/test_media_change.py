#!/usr/bin/env python3
"""Swap two healthy, different directories on one logged removable drive."""
import subprocess,time,json,os,sys
from pathlib import Path
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build,RAW_SIZE
import build_trs80_boot as boot
from run_trs80_command import DEFAULT_EMULATOR,key_args
R=Path(__file__).resolve().parents[1];W=R/'build/compatibility'/time.strftime('media-%Y%m%d-%H%M%S');W.mkdir()
mode=sys.argv[1] if len(sys.argv)>1 else 'observe'
source='''        ORG 100H
        LD SP,7000H
        LD A,(82H)
        LD (MODE),A
        LD E,1
        LD C,14
        CALL 5
        LD C,31
        CALL 5
        LD DE,11
        ADD HL,DE
        LD A,(HL)
        INC HL
        OR (HL)
        LD DE,NOCHECK
        CALL Z,PRINT
        LD DE,OLD
        LD C,17
        CALL 5
        CP 4
        JP NC,BAD
        LD DE,SWAP
        CALL PRINT
        LD C,1
        CALL 5
        LD DE,AFILE
        LD C,17
        CALL 5
        LD DE,NEW
        LD C,17
        CALL 5
        CP 4
        JP NC,BAD
        LD DE,SEEN
        CALL PRINT
        LD C,29
        CALL 5
        BIT 1,L
        LD DE,RO
        JR NZ,DONE
        LD DE,RW
DONE:   CALL PRINT
        JP 0
BAD:    LD DE,FAIL
        JR DONE
PRINT:  LD C,9
        JP 5
MODE:   DB 0
NOCHECK: DB 13,10,'DPB CHECKSUM VECTOR SIZE ZERO',13,10,'$'
SWAP:   DB 13,10,'SWAP LOGGED B NOW',13,10,'$'
SEEN:   DB 13,10,'REPLACEMENT DIRECTORY READ',13,10,'$'
RO:     DB 'MEDIA CHANGE SET READ ONLY',13,10,'$'
RW:     DB 'MEDIA CHANGE LEFT DRIVE WRITABLE',13,10,'$'
FAIL:   DB 'FIXTURE FAILED',13,10,'$'
OLD:    DB 2,'OLD     TXT'
        DB 0,0,0,0,0,0,0,0,0,0,0,0
        DB 0,0,0,0,0,0,0,0,0,0,0,0
NEW:    DB 2,'NEW     TXT'
        DB 0,0,0,0,0,0,0,0,0,0,0,0
        DB 0,0,0,0,0,0,0,0,0,0,0,0
AFILE:  DB 1,'BTONE   DAT'
        DB 0,0,0,0,0,0,0,0,0,0,0,0
        DB 0,0,0,0,0,0,0,0,0,0,0,0
        END
'''
if mode in ('write','reset'):
 source=source.replace('DONE:   CALL PRINT\n        JP 0', 'DONE:   CALL PRINT\n        LD A,(MODE)\n        CP 82\n        JR Z,RESET\n        LD DE,CREATED\n        LD C,22\n        CALL 5\n        LD DE,RESUMED\n        JP FINISH\nRESET:  LD DE,2\n        LD C,37\n        CALL 5\n        LD C,29\n        CALL 5\n        BIT 1,L\n        JP NZ,BAD\n        LD DE,CREATED\n        LD C,22\n        CALL 5\n        CP 4\n        JP NC,BAD\n        LD DE,CREATED\n        LD C,16\n        CALL 5\n        CP 4\n        JP NC,BAD\n        LD DE,RECOVERED\nFINISH: CALL PRINT\n        JP 0')
 source=source.replace('        END', "RESUMED: DB 'WRITE CALLER RESUMED - FAIL',13,10,'$'\nRECOVERED: DB 'RESET AND NEW FILE PASSED',13,10,'$'\nCREATED: DB 2,'CREATED TXT'\n        DB 0,0,0,0,0,0,0,0,0,0,0,0\n        DB 0,0,0,0,0,0,0,0,0,0,0,0\n        END")
if os.environ.get('MEDIA_SAME_DRIVE'):
 source=source.replace('        LD DE,AFILE\n        LD C,17\n        CALL 5\n','')
p=assemble(Path('/Users/nathanael/bin/z80asm'),source,W/'MEDIA.COM',W/'media.lst',0x100)
a=extract_raw(Path(os.environ.get('BETTERCPM_TEST_IMAGE',str(R/'build/compatibility/BetterCPM-Compatibility-Qualification.dmk'))).read_bytes());add_file(a,'MEDIA.COM',p);(W/'a.dmk').write_bytes(build(a))
boot.FILESYSTEM_FIRST_SECTOR=0;boot.BLOCK_COUNT=RAW_SIZE//2048
for name in ('OLD','NEW'):
 b=bytearray(b'\xe5'*RAW_SIZE);boot.install_files(b,[(name+'.TXT',name.encode())]);(W/(name+'.dmk')).write_bytes(build(b))
args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(W/'a.dmk'),'-d1',str(W/'OLD.dmk'),'-id','3500']+key_args('MEDIA'+(' R' if mode=='reset' else '')+'\r')+['-id','6000','-it','-im','eject','1','1','-im','insert','1',str(W/'NEW.dmk')]+key_args('Y')+['-id','6000','-it']+key_args('VER\r')+['-id','3000','-it','-ix']
subprocess.run(args,cwd=W,timeout=180,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
s=[]
for p in sorted(W.glob('trs80-text-*.bin')):
 d=p.read_bytes()[:1920];s.append('\n'.join(bytes(x&127 for x in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
(W/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(s));print(W);print(s[-1])

if mode=='write':
 assert 'Disk R/O' in s[-1] and 'WRITE CALLER RESUMED' not in s[-1] and 'BetterCP/M 0.3' in s[-1]
if mode=='reset':
 assert 'RESET AND NEW FILE PASSED' in s[-1] and 'FIXTURE FAILED' not in s[-1]
