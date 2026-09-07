#!/usr/bin/env python3
"""Boot cpmsim from private disks; test files, warm boot and RSX restoration."""
from pathlib import Path
import argparse,os,shutil,subprocess,tempfile
from build_ccp import assemble
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack');args=p.parse_args()
 image=args.image_dir.resolve()
 with tempfile.TemporaryDirectory(prefix='bettercpm-cpmsim-test-') as tmp:
  w=Path(tmp);shutil.copytree(image/'disks',w/'disks');shutil.copy2(image/'diskdefs',w/'diskdefs')
  source='''        ASEG
        ORG 100H
        LD SP,4000H
        LD A,2
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
        CP 5
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
  subprocess.run(['cpmcp','-T','raw','-f','bettercpm-z80pack-system',str(w/'disks/drivea.dsk'),str(w/'IOTEST.COM'),'0:IOTEST.COM'],cwd=w,check=True)
  target=w/'disks/drivec.dsk'
  raw=bytearray(target.read_bytes());raw[-128:]=b'\x5a'*128;target.write_bytes(raw)
  simulator=Path.home()/'CPM/z80pack/cpmsim/cpmsim'
  # Tcl receives paths as positional arguments, so shell metacharacters are
  # not interpreted. Every wait is bounded; no user's mounted media is used.
  script='''set timeout 25
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -re {\\r\\nA0>} {}
  timeout { puts "PROMPT TIMEOUT"; exit 1 }
  eof { puts "UNEXPECTED EXIT"; exit 1 }
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
prompt
send -- "DIR\\r"
expect -exact "BASIC"
prompt
send -- "HELLO\\r"
expect -exact "BetterCP/M on z80pack"
prompt
send -- "IOTEST\\r"
expect {
 "Z80PACK FILE IO PASS" {}
 "Z80PACK FILE IO FAILED" {exit 1}
 timeout {exit 1}
}
prompt
send -- "DUP\\r"
expect -exact "Your choice:"
send -- "B"
expect -exact "Source logical drive"
expect -exact "Your choice:"
send -- "B"
expect -exact "Destination logical drive"
expect -exact "Your choice:"
send -- "C"
expect -exact {[Y/N]}
send -- "Y"
expect -exact "Copy complete; destination verified."
expect -exact "Push ENTER for menu."
send -- "\\r"
expect -exact "Your choice:"
send -- "C"
expect -exact "Choose logical drive"
expect -exact "Your choice:"
send -- "C"
expect -exact "Unreadable sectors: 00000"
expect -exact "Push ENTER for menu."
send -- "\\r"
expect -exact "Your choice:"
send -- "C"
expect -exact "Choose logical drive"
expect -exact "Your choice:"
send -- "B\\003"
expect -exact "Check stopped. No disk contents changed."
expect -exact "Push ENTER for menu."
send -- "\\r"
expect -exact "Your choice:"
send -- "\\003"
prompt
send -- "RSX LOAD ECHO\\r"
prompt
send -- "RSX LIST\\r"
expect -exact "ECHO : BDOS 203"
prompt
send -- "RSX UNLOAD ECHO\\r"
prompt
send -- "RSX LIST\\r"
expect -exact "TPA available: 53K"
prompt
send -- "BYE\\r"
expect eof
'''
  (w/'test.exp').write_text(script)
  env=dict(os.environ);env['PATH']=str(simulator.parent/'srctools')+os.pathsep+env['PATH']
  run=subprocess.run(['expect',str(w/'test.exp'),str(simulator),str(w/'disks')],cwd=w,env=env,capture_output=True,text=True,timeout=240)
  report=image/'verification.txt';report.write_text(run.stdout+run.stderr)
  if run.returncode:raise AssertionError(f'cpmsim test failed: {report}\n{run.stdout[-1500:]}')
  assert (w/'disks/driveb.dsk').read_bytes()==(w/'disks/drivec.dsk').read_bytes(), 'DUP missed disk content'
  for letter in 'bcd':
   output=w/(letter+'.dat')
   subprocess.run(['cpmcp','-T','raw','-f','bettercpm-z80pack-data',str(w/f'disks/drive{letter}.dsk'),'0:PROBE.DAT',str(output)],cwd=w,check=True)
   assert output.read_bytes()==bytes(range(128,0,-1)),letter
  print('PASS: cpmsim disk boot, directory, transient/warm return, file create/write/close/open/read on B-D, DUP copy/check, RSX load/unload and 53K TPA. cpmtools verifies all three written files.')
if __name__=='__main__':main()
