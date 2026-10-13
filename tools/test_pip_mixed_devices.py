#!/usr/bin/env python3
"""Mixed PIP sources, cross-device routing and complete-list rejection."""
from test_pip_transfer import execute,key

def main():
 one=key(0,2,'ONE.DAT');two=key(1,7,'TWO.DAT');dest=key(2,4,'DEST.DAT')
 files={one:(b'one\x1a',0),two:(b'two\x1a',0)}
 tails=['C4:DEST.DAT=A2:ONE.DAT,CON:,B7:TWO.DAT,NUL:,EOF:',
        'C4:DEST.DAT=CON:,A2:ONE.DAT,NUL:,B7:TWO.DAT,EOF:']
 for index,tail in enumerate(tails):
  out,fs,calls,_=execute(tail,files,input_bytes=b'input\x1a')
  if index==0:expected=b'oneinputtwo'+bytes(40)+b'\x1a'
  else:expected=b'inputone'+bytes(40)+b'two\x1a'
  assert out=='' and fs[dest][0]==expected.ljust(128,b'\x1a'),(tail,out,fs[dest])
  assert fs[one]==list(files[one]) and fs[two]==list(files[two])
 for sink in ['CON','LST','PUN','OUT']:
  out,fs,calls,_=execute(sink+':=A2:ONE.DAT,INP:,NUL:,EOF:,B7:TWO.DAT',files,input_bytes=b'patch\x1a',patch_in=True,patch_out=True)
  assert out.encode()==b'onepatch'+bytes(40)+b'\x1atwo' and fs=={k:list(v) for k,v in files.items()}
 out,fs,_,_=execute('LST:=RDR:',{},input_bytes=b'\xc1\x9a')
 assert out=='A' and fs=={}
 for tail in ['LST:=NUL:,CON:[U]','C4:DEST.DAT=NUL:,PTR:',
              'C4:DEST.DAT=CON:,C4:DEST.$$$','C4:DEST.DAT=A2:ONE.DAT,CON:[O]']:
  out,fs,calls,_=execute(tail,files)
  assert out and not any(f in calls for f in (1,3,4,5,20,21,22,23)),(tail,out,calls)
 print('PASS: PIP mixed disk/device sources, special-source boundaries, device-to-device and full-list preflight')
if __name__=='__main__':main()
