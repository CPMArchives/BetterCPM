#!/usr/bin/env python3
"""DRI text/object HEX transfer: records, end tails, recovery and staging."""
from test_pip_transfer import execute,key
from test_pip_hex import record

def main():
 src=key(0,2,'SRC.HEX');dest=key(1,7,'DEST.HEX');temp=key(1,7,'DEST.$$$')
 records=[record(b'ABC'),record(bytes(range(33)),address=0x3456)]
 ending=b':00000001FF\r\n\x1a'
 data=b'noise\r\n'+b'\n'.join(records)+b'\r\n'+ending
 base=b''.join(r+b'\r\n' for r in records)
 for option in ['H','I','HV','IV']:
  out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX['+option+']',{src:(data,0)})
  expected=base+(ending if 'I' not in option else b'')+b'\r\n'
  assert out=='' and fs[dest][0]==expected.ljust(((len(expected)+127)//128)*128,b'\x1a'),(option,out,fs[dest])
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[H]',{src:(records[0]+b'\x1a',0)},answer='\x1a')
 assert 'END OF FILE, CTL-Z?' in out and fs[dest][0]==(records[0]+b'\r\n').ljust(128,b'\x1a')
 bad=records[0][:-2]+b'00'
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[H]',{src:(bad+b'\n'+data,0)},answer='\r')
 assert 'CHECKSUM ERROR' in out and 'CORRECT ERROR' in out and fs[dest][0].startswith(base+ending+b'\r\n')
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[H]',{src:(bad+b'\x1a',0)},answer='\x1a')
 assert 'CHECKSUM ERROR' in out and fs[dest]==[b'',0]
 for invalid,message in [(b':01ZZ000001FE','INVALID DIGIT'),(record(bytes(range(34))),'RECORD TOO LONG')]:
  out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[H]',{src:(invalid+b'\x1a',0)},answer='\x1a')
  assert message in out and fs[dest]==[b'',0]
 out,fs,_,_=execute('B7:DEST.HEX=INP:[H]',{},input_bytes=data,patch_in=True)
 assert out=='' and fs[dest][0].startswith(base+ending+b'\r\n')
 out,fs,_,_=execute('B7:DEST.HEX=INP:',{},input_bytes=data,patch_in=True)
 assert out=='' and fs[dest][0].startswith(base+ending+b'\r\n')
 out,fs,_,_=execute('B7:DEST.HEX=INP:',{},input_bytes=data,patch_in=True,break_keys=[ord('X')])
 assert 'READER STOPPING' in out and fs[dest][0].startswith(base+ending+b'\r\n')
 for device,patch in [('RDR',False),('CON',False)]:
  out,fs,_,_=execute('B7:DEST.HEX='+device+':',{},input_bytes=data,patch_in=patch)
  assert out=='' and fs[dest][0].startswith(data[:-1]),(device,out)
 out,fs,_,_=execute('B7:DEST.TXT=INP:',{},input_bytes=data,patch_in=True)
 assert out=='' and fs[key(1,7,'DEST.TXT')][0].startswith(data[:-1])
 out,fs,_,_=execute('B7:DEST.HEX=INP:,RDR:',{},input_bytes=data+b'raw-reader\x1a',patch_in=True)
 assert out=='' and fs[dest][0].startswith(base+ending+b'\r\nraw-reader')
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[HV]',{src:(b'\x13'.join(bytes([v]) for v in data),0)})
 assert out=='' and fs[dest][0].startswith(base+ending+b'\r\n')
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.HEX[OH]',{src:(data,0)})
 assert out=='' and fs[dest][0].startswith(base+ending+b'\r\n')
 obj=key(0,2,'SRC.COM')
 for option in ['H','I','OHV']:
  out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.COM['+option+']',{obj:(data+b'AFTER EOF MUST NOT COPY',0)})
  expected=base+(ending if 'I' not in option else b'')+b'\r\n'
  assert out=='' and fs[dest][0]==expected.ljust(((len(expected)+127)//128)*128,b'\x1a'),(option,out)
 out,fs,_,_=execute('B7:DEST.HEX=A2:SRC.COM[H]',{obj:(records[0]+b'\x1aAFTER EOF',0)},answer='\x1a')
 assert 'END OF FILE, CTL-Z?' in out and fs[dest][0]==(records[0]+b'\r\n').ljust(128,b'\x1a')
 print('PASS: PIP H/I record transfer, zero-length drain, EOF/correction prompts, retry and XOFF suppression')
if __name__=='__main__':main()
