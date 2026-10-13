#!/usr/bin/env python3
"""Physical aliases cannot silently use fixed logical BIOS routes."""
from test_pip_transfer import execute,key

def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT');files={src:(b'data\x1a',0),dest:(b'old',0)}
 for device in ['LPT','UL1','PRN','PTP','UP1','UP2','TTY','CRT','UC1']:
  out,fs,calls,_=execute(device+':=A2:SRC.TXT',files)
  assert out=='DEVICE UNAVAILABLE\r\n' and fs=={k:list(v) for k,v in files.items()}
  assert not any(f in calls for f in (1,2,3,4,5,8,20,21,22,23,30))
 for device in ['IRD','PTR','UR1','UR2','TTY','CRT','UC1']:
  for tail in ['B7:DEST.TXT='+device+':','CON:=NUL:,'+device+':','B7:DEST.TXT=A2:SRC.TXT,'+device+':']:
   out,fs,calls,_=execute(tail,files)
   assert out=='DEVICE UNAVAILABLE\r\n' and fs=={k:list(v) for k,v in files.items()},(tail,out)
   assert not any(f in calls for f in (1,2,3,4,5,8,20,21,22,23,30))
 print('PASS: PIP unavailable physical aliases fail before input/output, IOBYTE changes or destination mutation')
if __name__=='__main__':main()
