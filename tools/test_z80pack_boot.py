#!/usr/bin/env python3
"""Boot cpmsim from private disks; test files, warm boot and RSX restoration."""
from pathlib import Path
import argparse,os,shutil,subprocess,tempfile
from build_ccp import assemble
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack');p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');args=p.parse_args()
 image=args.image_dir.resolve()
 with tempfile.TemporaryDirectory(prefix='bettercpm-cpmsim-test-') as tmp:
  w=Path(tmp);shutil.copytree(image/'disks',w/'disks');shutil.copy2(image/'diskdefs',w/'diskdefs')
  source='''        ASEG
        ORG 100H
        LD SP,4000H
        LD A,1
        LD (FCB),A
NEXT:   LD HL,FCB+12
        LD DE,FCB+13
        LD BC,23
        LD (HL),0
        LDIR
        LD DE,FCB
        LD C,22
        CALL 5
        INC A
        JP Z,FAIL
        LD HL,BUFFER
        LD B,128
FILL:   LD A,B
        LD (HL),A
        INC HL
        DJNZ FILL
        LD DE,BUFFER
        LD C,26
        CALL 5
        LD DE,FCB
        LD C,21
        CALL 5
        OR A
        JP NZ,FAIL
        LD DE,FCB
        LD C,16
        CALL 5
        INC A
        JP Z,FAIL
        LD HL,FCB+12
        LD DE,FCB+13
        LD BC,23
        LD (HL),0
        LDIR
        LD DE,FCB
        LD C,15
        CALL 5
        INC A
        JP Z,FAIL
        LD HL,BUFFER
        LD DE,BUFFER+1
        LD BC,127
        LD (HL),0
        LDIR
        LD DE,FCB
        LD C,20
        CALL 5
        OR A
        JP NZ,FAIL
        LD HL,BUFFER
        LD B,128
CHECK:  LD A,(HL)
        CP B
        JP NZ,FAIL
        INC HL
        DJNZ CHECK
        LD A,(FCB)
        INC A
        LD (FCB),A
        CP 2
        JP C,NEXT
        LD DE,OK
        JR REPORT
FAIL:   LD DE,BAD
REPORT: LD C,9
        CALL 5
        JP 0
OK:     DB 'Z80PACK FILE IO PASS',13,10,'$'
BAD:    DB 'Z80PACK FILE IO FAILED',13,10,'$'
FCB:    DB 2,'PROBE   DAT'
        DS 24
BUFFER: DS 128
        END
'''
  probe=assemble(Path.home()/'bin/z80asm',source,w/'IOTEST.COM',w/'probe.lst',0x100)
  subprocess.run(['cpmcp','-f','bettercpm-default',str(w/'disks/drivea.dsk'),str(w/'IOTEST.COM'),'0:IOTEST.COM'],cwd=w,check=True)
  (w/'CPMTOOLS.TXT').write_bytes(b'Created with cpmtools\r\n')
  subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(w/'disks/driveb.dsk'),str(w/'CPMTOOLS.TXT'),'0:CPMTOOLS.TXT'],cwd=w,check=True)
  target=w/'disks/drivec.dsk'
  raw=bytearray(target.read_bytes());raw[-128:]=b'\x5a'*128;target.write_bytes(raw)
  simulator=args.simulator.expanduser().resolve()
  # Tcl receives paths as positional arguments, so shell metacharacters are
  # not interpreted. Every wait is bounded; no user's mounted media is used.
  report=image/'verification.txt'
  script='''set timeout 25
set send_slow {1 .02}
log_file -noappend [lindex $argv 2]
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -exact {A0>_ } {}
  timeout { puts "PROMPT TIMEOUT"; exit 1 }
  eof { puts "UNEXPECTED EXIT"; exit 1 }
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact "Booting..."
prompt
send -s -- "DIR\\r"
expect -exact "RCP"
prompt
send -s -- "HELLO\\r"
expect -exact "BetterCP/M on z80pack"
prompt
send -s -- "DIR B:\\r"
expect -exact "CPMTOOLS TXT"
prompt
send -s -- "IOTEST\\r"
expect {
 "Z80PACK FILE IO PASS" {}
 "Z80PACK FILE IO FAILED" {exit 1}
 timeout {exit 1}
}
prompt
send -s -- "RSX LOAD ECHO\\r"
prompt
send -s -- "RSX LIST\\r"
expect -exact "ECHO : BDOS 199"
prompt
send -s -- "RSX UNLOAD ECHO\\r"
prompt
send -s -- "RSX LIST\\r"
expect -exact "TPA available: 53K"
prompt
send -s -- "BYE\\r"
expect eof
'''
  (w/'test.exp').write_text(script)
  env=dict(os.environ);env['PATH']=str(simulator.parent/'srctools')+os.pathsep+env['PATH']
  run=subprocess.run(['expect',str(w/'test.exp'),str(simulator),str(w/'disks'),str(report)],cwd=w,env=env,capture_output=True,text=True,timeout=240)
  if run.returncode:
   tail=report.read_text(errors='replace')[-1500:] if report.exists() else run.stdout[-1500:]
   raise AssertionError(f'cpmsim test failed: {report}\n{tail}')
  print('PASS: cpmsim disk boot, A: directory, cpmtools-created B: directory, cpmtools-supplied transient, file create/write/close/open/read on A, RSX load/unload and 53K TPA.')
if __name__=='__main__':main()
