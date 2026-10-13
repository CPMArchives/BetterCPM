#!/usr/bin/env python3
"""PIP device precedence, native single DU, FCB fields and historical parameters."""
from test_pip_parser import cpu,addr

def parse(text):
 c=cpu();data=text.encode();c.mem[0x6000:0x6000+len(data)]=data;c.mem[addr('P_DRIVE')]=1;c.mem[addr('P_USER')]=7
 c.hl=0x6000;c.b=len(data);c.run(addr('PO_PARSE'),limit=100000)
 assert bytes(c.mem[0x6000:0x6000+len(data)])==data
 return c.carry,bytes(c.mem[addr('OP_REC'):addr('OP_REC')+80]),c

def main():
 for text,drive,user in [('FOO.TXT',1,7),('A0:FOO.TXT',0,0),('B31:FOO.TXT',1,31),('C01:FOO.TXT',2,1),('5:FOO.TXT',1,5),('00:FOO.TXT',1,0),('B:FOO.TXT',1,7),('A: FOO.TXT',0,7),('FOO.TXT[G0]',1,0),('A:FOO.TXT[G31]',0,31)]:
  bad,r,_=parse(text);assert not bad and r[0]==2 and r[2:4]==bytes((drive,user)),(text,bad,r[:8])
  assert r[8:20]==bytes((drive+1,))+b'FOO     TXT'
 for number,device in enumerate(['INP','IRD','PTR','UR1','UR2','RDR','OUT','LPT','UL1','PRN','LST','PTP','UP1','UP2','PUN','TTY','CRT','UC1','CON','NUL','EOF']):
  bad,r,_=parse(device.lower()+':');assert not bad and r[0:2]==bytes((4,number)),(device,bad,r[:8])
 bad,r,_=parse('LST:[NT8U]');assert not bad and r[44+13]==1 and r[44+19]==8 and r[44+20]==1
 for text in ['B:','B12:','12:']:
  bad,r,_=parse(text);assert not bad and r[0]==3
 for text,name in [('*.COM',b'????????COM'),('F?*.D*',b'F???????D??'),('FOO',b'FOO        ')]:
  bad,r,_=parse(text);assert not bad and r[9:20]==name,(text,bad,r[9:20])
 for text in ['B32:X','B003:X','003:X','Q:X','A7:X[G2]','A7:X[G7]','X[G32]','X[G260]','X[G999]','F***.COM','F*A.COM','FOO.ABCD','FOOBARBAZ.COM','FOO.TXT EXTRA','FOO.TXT [V]','CON: [U]','BOGUS:','B[-]:*.COM','[A0,B3]:*.COM','X[$RO]','X[Qbad]']:
  bad,r,_=parse(text);assert bad and r[0]==0,(text,r)
 bad,r,c=parse('A3:F.TXT[Sfoo, =[bar]\x1aQend\x1aV]');assert not bad and r[44+18]==1 and r[44+16]==1 and r[44+21]==1
 for offset,expected in [(70,b'foo, =[bar]'),(73,b'end')]:
  p=r[offset]|r[offset+1]<<8;assert bytes(c.mem[p:p+r[offset+2]])==expected
 from test_pip_parser import scan
 for command in ['B:=A:*.COM','A3:BIG.TXT=B1:ONE.TXT,C7:TWO.TXT','LST:=FOO.TXT','OUT.TXT=CON:','FOO.TXT=B:[G1]']:
  bad,parts=scan(command);assert not bad,(command,parts)
 for command in ['B:FOO.TXT=A:*.COM','FOO.TXT[W]=A:FOO.TXT','NUL:=FOO.TXT','LST:=B:','B:=A:ONE.TXT,A:TWO.TXT','OUT.TXT=OUT:']:
  bad,parts=scan(command);assert bad and not parts,(command,parts)
 print('PASS: PIP operand DU inheritance, devices, FCB wildcards, G bounds/conflicts, parameter values and extraction strings')
if __name__=='__main__':main()
