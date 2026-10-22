#!/usr/bin/env python3
"""PIP's shared RO approval retains every input outcome and transfer policy."""
import hashlib,json,re
from pathlib import Path
from build_pip import expanded_source
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address,runner,output
from utility_versions import banner
import test_pip_transfer as transfer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/pip-shared-input'


def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=expanded_source().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
 old=(ROOT/'tools/fixtures/pip-legacy-confirm.inc').read_text();anchor='        CALL UI_ASK\n';assert source.count(anchor)==1
 source=source.replace(anchor,old,1);(OUT/'legacy-expanded.mac').write_text(source)
 before=assemble(Path.home()/'bin/z80asm',source,OUT/'legacy.bin',OUT/'legacy.lst',256)
 current=(ROOT/'build/pip-development/PIP.COM').read_bytes();listing=(ROOT/'build/pip-development/pip.lst').read_text()
 maxstack=0;original_cpu,original_addr=transfer.cpu,transfer.addr
 def run(image,ls,tail,files,answer):
  nonlocal maxstack
  positions={name:address(ls,name) for name in ('OP_DATA','PP_COUNT','P_STACK')}
  def factory():
   c=Z80(b'');c.mem[256:256+len(image)]=image
   push=c.push;top=positions['P_STACK']
   def tracked(value):
    nonlocal maxstack
    push(value)
    if c.sp<top:
     used=top-c.sp;assert used<=128,('PIP stack exceeded',used)
     maxstack=max(maxstack,used)
   c.push=tracked;return c
  transfer.cpu=factory;transfer.addr=positions.__getitem__
  return transfer.execute(tail,files,answer=answer)
 sourcekey=transfer.key(0,2,'SRC.DAT');dest=transfer.key(1,7,'DEST.DAT');temp=transfer.key(1,7,'DEST.$$$')
 fixture={sourcekey:(b'S'*128,0),dest:(b'OLD'*42+b'!!',1)};cases=0
 try:
  for key in range(256):
   # Actual controller with hostile console service; one byte only, no flush.
   c=Z80(b'');c.mem[256:256+len(current)]=current;c.mem[5:8]=b'\xdb\xf4\xc9'
   pending=[key,ord('!')];reads=[]
   def io(port):
    assert port&255==244 and c.c==1
    value=pending.pop(0);reads.append(value)
    c.bc=0xeeee;c.de=0xdddd;c.hl=0xcccc;c.ix=0xbbbb
    return value
   c.port_read=io;sp=c.sp;c.run(address(listing,'UI_ASK'),limit=100000)
   expected=key&0xdf if (key&0xdf) in (ord('Y'),ord('N')) else 0
   assert c.a==expected and c.sp==sp and reads==[key] and pending==[ord('!')],key
   a=run(before,(OUT/'legacy.lst').read_text(),'B7:DEST.DAT=A2:SRC.DAT[V]',fixture,chr(key))
   b=run(current,listing,'B7:DEST.DAT=A2:SRC.DAT[V]',fixture,chr(key))
   assert a==b,(key,a,b)
   assert b[2].count(1)==1 and temp not in b[1]
   assert b[1][dest][0]==(b'S'*128 if (key&0xdf)==ord('Y') else fixture[dest][0])
   cases+=1
  for flags in ('[W]','[WV]'):
   a=run(before,(OUT/'legacy.lst').read_text(),'B7:DEST.DAT=A2:SRC.DAT'+flags,fixture,'N')
   b=run(current,listing,'B7:DEST.DAT=A2:SRC.DAT'+flags,fixture,'N')
   assert a==b and 1 not in b[2] and b[1][dest][0]==b'S'*128
   cases+=1
 finally:transfer.cpu,transfer.addr=original_cpu,original_addr
 for symbol in ('EDITNEW','UP_RUN','UW_LEFT','UR_DRAW','UA_INIT'):assert not re.search(r'\b'+symbol+':',listing),symbol
 for tail in ['/VER',' /ver  ','/VER x','x /VER','/VER /VER','/VER /B']:
  c=runner(current);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data;c.run(256,limit=100000)
  expected=banner('PIP')+'\r\n' if tail.strip().upper()=='/VER' else 'Invalid /VER usage.\r\n'
  assert output(c)==expected,(tail,output(c))
 (OUT/'results.json').write_text(json.dumps({'result':'PASS','differential_transfers':cases,'pip_sha256':hashlib.sha256(current).hexdigest(),'bytes':len(current),'maximum_tested_stack_bytes':maxstack,'version_cases':6,'scope':'all input bytes through complete verified protected replacement, W/WV bypass, filesystem mutation/calls/output equivalence; no command/HEX/device editor replacement'},indent=2)+'\n')
 print(f'PASS: {cases} complete PIP RO transfers; maximum tested stack {maxstack}/128 bytes')
if __name__=='__main__':main()
