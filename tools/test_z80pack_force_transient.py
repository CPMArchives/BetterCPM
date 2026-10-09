#!/usr/bin/env python3
"""Qualify explicit transient prefixes without changing ordinary dispatch."""
import argparse, shutil, subprocess, json, hashlib
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session
from build_ccp import assemble
from fdf_format import select_fdf

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 work=args.report.resolve();work.mkdir(parents=True,exist_ok=False)
 shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
 a=work/'disks/drivea.dsk';b=work/'disks/driveb.dsk'
 # CCP reconstruction reads its reserved carrier, not a filesystem CCP.RLM.
 fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF','California Computer Systems (40T, DS, DD, 332K)')
 mapping=fmt.raw_record_map(); raw=bytearray(a.read_bytes())
 carrier=(ROOT/'build/ccp/ccp.rlm').read_bytes().ljust(13*512,b'\0')
 for i in range(len(carrier)//128):
  logical=108+i;track,record=divmod(logical,len(mapping))
  offset=(track*len(mapping)+mapping[record])*128
  raw[offset:offset+128]=carrier[i*128:(i+1)*128]
 a.write_bytes(raw)

 def cpm(tool,disk,*values):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True)
 # Leave directory entries for the SUBMIT stream on this disposable fixture.
 cpm('cpmrm',a,'0:RSXTEST.COM','0:RSX2TST.COM','0:STATTST.COM','0:STATEFUL.RSX')
 for name,path in [('SUBMIT.COM','build/utilities/SUBMIT.COM')]:
  cpm('cpmrm',a,'0:'+name);cpm('cpmcp',a,ROOT/path,'0:'+name)
 marker='''        ORG 0100H
        LD DE,MSG
        LD C,9
        CALL 5
        LD A,(0080H)
        LD B,A
        LD HL,0081H
LOOP:   LD A,B
        OR A
        JR Z,DONE
        LD E,(HL)
        PUSH HL
        PUSH BC
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ LOOP
DONE:   LD C,0
        JP 5
MSG:    DB 13,10,'TRANSIENT:', '$'
        END
'''
 assemble(Path.home()/'bin/z80asm',marker,work/'MARK.COM',work/'marker.lst',0x100)
 b.write_bytes(bytes([229])*len(b.read_bytes()))
 for name in ['DIR','GET','FOO']:
  cpm('cpmrm',a,'0:'+name+'.COM');cpm('cpmcp',a,work/'MARK.COM','0:'+name+'.COM')
 cpm('cpmcp',b,work/'MARK.COM','3:FOO.COM')
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
 cases=[]
 for i,cmd in enumerate([':DIR ARG','.DIR ARG',':GET ARG','.GET ARG',':B3:FOO ARG','.B3:FOO ARG',':FOO '+'X'*120,'DIR','B:','FOO ARG',':NOFILE ARG',':','.']):
  prompt=b'B0>_ ' if cmd=='B:' else b'A0>_ '
  text=session(sim,work/'disks',[(cmd.encode()+b'\r',prompt,30)],work/f'case-{i}.txt')
  expected=cmd not in ['DIR','B:',':NOFILE ARG',':','.']
  assert (b'TRANSIENT:' in text)==expected,(cmd,text)
  if expected:assert b'TRANSIENT: '+(b'X'*120 if len(cmd)>100 else b'ARG') in text,(cmd,text)
  cases.append(cmd)
 cpm('cpmrm',a,'0:GET.COM')
 text=session(sim,work/'disks',[(b':GET ARG\r',b'A0>_ ',30)],work/'missing-core.txt')
 assert b'\n?' in text and b'TRANSIENT:' not in text
 cpm('cpmcp',a,work/'MARK.COM','0:GET.COM')
 script=work/'FORCE.SUB';script.write_bytes(b':DIR FIRST\r\n.GET SECOND\r\n\x1a');cpm('cpmcp',a,script,'0:FORCE.SUB')
 text=session(sim,work/'disks',[(b'SUBMIT FORCE\r',b'TRANSIENT: SECOND',30)],work/'submit.txt')
 assert b'TRANSIENT: FIRST' in text and b'TRANSIENT: SECOND' in text,text
 (work/'evidence.json').write_text(json.dumps({'result':'PASS','cases':cases,'submit':[':DIR FIRST','.GET SECOND'],'ccp_sha256':hashlib.sha256((ROOT/'build/ccp/ccp.bin').read_bytes()).hexdigest()},indent=2)+'\n')
 print('Explicit prefixes, core/CPX bypass, DU, tail, normal dispatch and SUBMIT pass')
if __name__=='__main__':main()
