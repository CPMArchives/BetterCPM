#!/usr/bin/env python3
"""Bounded DRI HEXRECORD validator foundation; H/I dispatch remains disabled."""
from test_pip_parser import cpu,addr

def record(data,address=0x1234,kind=0):
 body=bytes([len(data),address>>8,address&255,kind])+data
 return b':'+(body+bytes([-sum(body)&255])).hex().upper().encode()
def parse(data):
 c=cpu();c.mem[0x6000:0x6000+len(data)]=data;c.hl=0x6000;c.b=len(data)
 c.run(addr('PH_PARSE'),limit=100000)
 assert bytes(c.mem[0x6000:0x6000+len(data)])==data
 def value(label):return c.mem[addr(label)]
 return c.a,value('PH_USED'),value('PH_SIZE'),value('PH_XOFF'),bytes(c.mem[addr('PH_BUFFER'):addr('PH_BUFFER')+value('PH_SIZE')])
def main():
 for count in [1,2,16,32,33]:
  text=record(bytes(range(count)))
  result=parse(text+b'\r\n')
  assert result==(0,len(text),len(text),0,text),(count,result)
 assert parse(record(bytes(range(34))))[0]==4
 assert parse(b':00NOT-A-CHECKED-RECORD')[0:3]==(1,3,3)
 assert parse(record(b'\x01',kind=7))[0]==0
 assert parse(b'!0100000001FE')[0]==2
 assert parse(b':01gg000001FE')[0]==2
 assert parse(record(b'\xab').lower())[0]==2
 assert parse(record(b'\x01')[:-2]+b'FF')[0]==3
 text=record(b'\x01\x02')
 for length in range(len(text)):assert parse(text[:length])[0]==5,length
 interrupted=b'\x13'.join(bytes([value]) for value in text)
 result=parse(interrupted)
 assert result==(0,len(interrupted),len(text),1,text),result
 print('PASS: PIP HEX record checksum/digits, zero-length prefix, DRI length bound, partial input and XOFF reporting')
if __name__=='__main__':main()
