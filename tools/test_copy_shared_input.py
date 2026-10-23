#!/usr/bin/env python3
"""Compare COPY prompt and replacement-field I/O with retained legacy loops."""
import hashlib,json,re
from functools import lru_cache
from pathlib import Path
from build_ccp import assemble
from build_rcp_transients import transient_source,copy_source,symbol,transient
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/copy-shared-input'


@lru_cache(maxsize=2)
def positions(listing):
 return {n:address(listing,n) for n in ('CTPROMPT','CVVASK','CTRENAME','CTYALLOW','CTSKIP','CTALLOW','CVVRETRY','CVVSKIP','CVVABORT','CTABORT','CTRLINE','BC_FCB','BC_NEWFCB','BC_CSDRV','BC_CSUSR','BC_CDDRV','BC_CDUSR','BC_OVER','CT_SKIP','BC_WERROR','CTRLEN','CTROVER','CTRBUF')}


def invoke(image,listing,context,keys):
 at=positions(listing).__getitem__;c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
 # Stop at the chosen caller-owned action, retaining choice-side policy writes.
 for name,tag in [('CTYALLOW',1),('CTSKIP',2),('CTALLOW',4),('CVVRETRY',5),('CVVSKIP',6),('CVVABORT',7),('CTABORT',8),('CTRLINE',9)]:c.mem[at(name):at(name)+3]=bytes([0x3e,tag,0xc9])
 if context!='name':c.mem[at('CTRENAME'):at('CTRENAME')+3]=b'\x3e\x03\xc9'
 for name,value in [('BC_CSDRV',1),('BC_CSUSR',31),('BC_CDDRV',2),('BC_CDUSR',3),('BC_OVER',0),('CT_SKIP',0),('BC_WERROR',0)]:c.mem[at(name)]=value
 for name,filename in [('BC_FCB',b'FOO     DAT'),('BC_NEWFCB',b'BAR     TXT')]:c.mem[at(name)+1:at(name)+12]=filename
 if context=='name':c.mem[at('CTRBUF')-1]=0xa5;c.mem[at('CTRBUF')+126]=0x5a
 queue=list(keys);text=bytearray();reads=[]
 def io(port):
  assert port&255==244
  if c.c==6:
   assert c.e==255 and queue,'unexpected input poll'
   value=queue.pop(0);reads.append(value)
  elif c.c==2:text.append(c.e);value=0
  elif c.c==9:
   p=c.de
   while c.mem[p]!=36:text.append(c.mem[p]);p+=1
   value=0
  else:raise AssertionError(('unexpected BDOS',c.c))
  c.bc=0xeeee;c.de=0xdddd;c.hl=0xcccc;c.ix=0xbbbb
  return value
 c.port_read=io;sp=c.sp;c.run(at({'overwrite':'CTPROMPT','verify':'CVVASK','name':'CTRENAME'}[context]),limit=300000)
 assert c.sp==sp
 if context=='name':assert (c.mem[at('CTRBUF')-1],c.mem[at('CTRBUF')+126])==(0xa5,0x5a)
 field=(c.mem[at('CTRLEN')],c.mem[at('CTROVER')],bytes(c.mem[at('CTRBUF'):at('CTRBUF')+c.mem[at('CTRLEN')]])) if context=='name' else None
 return (c.a,bytes(text),queue,reads,c.mem[at('BC_OVER')],c.mem[at('CT_SKIP')],field)


def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=copy_source(transient_source()).replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
 fixture=json.loads((ROOT/'tools/fixtures/copy-legacy-input.json').read_text())
 for first,last,label in [('CTREAD:','CTANSWER:','overwrite'),('CVVREAD:','CVVANS:','verify')]:
  a=source.index(first)+len(first);b=source.index(last,a);source=source[:a]+'\n'+fixture[label]+source[b:]
 a=source.index('CTRENAME:');b=source.index('CTRLINE:',a);source=source[:a]+fixture['name']+source[b:]
 (OUT/'legacy-expanded.mac').write_text(source)
 ls=OUT/'legacy.lst';raw=assemble(Path.home()/'bin/z80asm',source,OUT/'legacy.bin',ls,256)
 baseline=transient(raw,symbol(ls,'BC_COPY'),symbol(ls,'UV_CHECK'),symbol(ls,'UV_TCOPY'));before=ls.read_text()
 image=(ROOT/'build/utilities/COPY.COM').read_bytes();listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
 count=0
 for context in ('overwrite','verify','name'):
  for key in range(256):
   fallback=b'Y!' if context=='overwrite' else b'S!' if context=='verify' else b'NEW.DAT\r!'
   keys=bytes([key])+fallback
   a=invoke(baseline,before,context,keys);b=invoke(image,listing,context,keys)
   assert a==b,(context,key,a,b)
   count+=1
 for keys in [b'new.txz\x08t\r!',b'new.txz\x7ft\n!',b'\x08\x7f\r!',b'X'*127+b'\x08'*125+b'\r!',b'AB\x15CD\r!',b'\x1b\r!']:
  assert invoke(baseline,before,'name',keys)==invoke(image,listing,'name',keys),keys
  count+=1
 # Keep the selected modules bounded; the standard editor is not linked.
 for label in ('EDITNEW','UP_RUN','UW_LEFT','UR_DRAW'):assert not re.search(r'\b'+label+':',listing),label
 from test_utility_versions import runner,output
 from utility_versions import banner
 for tail in ['/VER',' /ver  ','/VER x','x /VER','/VER /VER','/VER /B']:
  cpu=runner(image);data=tail.encode();cpu.mem[128]=len(data);cpu.mem[129:129+len(data)]=data;cpu.run(256,limit=100000)
  expected=banner('COPY')+'\r\n'
  assert output(cpu)==expected,(tail,output(cpu))
 (OUT/'results.json').write_text(json.dumps({'result':'PASS','differential_cases':count,'copy_sha256':hashlib.sha256(image).hexdigest(),'bytes':len(image),'scope':'actual prompt/field code, echoed bytes, consumed input, choice policy flags and bounded field; actions stop at dispatch and are separately native-media qualified'},indent=2)+'\n')
 print(f'PASS: {count} COPY prompt/field comparisons including hostile BDOS clobbers')
if __name__=='__main__':main()
