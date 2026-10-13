#!/usr/bin/env python3
"""Logical sink routing, EOF policy, patch entry and complete preflight."""
from test_pip_transfer import execute,key

def main():
 source=key(0,2,'ONE.DAT');second=key(1,7,'TWO.DAT')
 files={source:(b'first\r\n\x1aIGNORED',0),second:(b'second\x1a',0)}
 for sink,function in [('CON',2),('LST',5),('PUN',4),('OUT',None)]:
  out,fs,calls,writes=execute(sink+':=A2:ONE.DAT,B7:TWO.DAT',files,patch_out=True)
  assert out=='first\r\nsecond',(sink,out)
  assert fs=={k:list(v) for k,v in files.items()} and not writes
  assert not any(f in calls for f in (19,22,23,30))
  if function:assert calls.count(function)==13
  out,_,_,_=execute(sink+':=A2:ONE.DAT[O]',files,patch_out=True)
  assert out.encode()==files[source][0].ljust(128,b'\x1a')
 obj=key(0,2,'CODE.COM')
 payload=bytes(range(256))
 out,_,_,_=execute('CON:=A2:CODE.COM',{obj:(payload,0)})
 assert out.encode('latin1')==payload
 out,_,_,_=execute('CON:=A:ONE.DAT[G2]',files)
 assert out=='first\r\n'
 for tail in ['CON:=A2:ONE.DAT,B7:TWO.DAT[X]','LST:=A2:*.DAT','CON:[V]=A2:ONE.DAT','PUN:=A2:ONE.DAT[V]','CRT:=A2:ONE.DAT']:
  out,_,calls,_=execute(tail,files)
  assert ('not implemented' in out or 'INVALID FORMAT' in out or 'DEVICE UNAVAILABLE' in out) and not any(f in calls for f in (2,4,5,20)),(tail,out,calls)
 out,_,_,_=execute('CON:=A2:ONE.DAT',{source:(b'SYSTEM\x1a',2)})
 assert out=='NO FILE\r\n'
 out,_,_,_=execute('CON:=A2:ONE.DAT[R]',{source:(b'SYSTEM\x1a',2)})
 assert out=='SYSTEM'
 out,_,_,_=execute('CON:=A2:ONE.DAT',{source:(b'x'*256,0)},fail='read')
 assert out=='x'*128+'DISK READ ERROR\r\n'
 print('PASS: PIP logical character sinks, patch ABI, text/object EOF, multi-DU concatenation and preflight')
if __name__=='__main__':main()
