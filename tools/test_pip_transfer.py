#!/usr/bin/env python3
"""PIP exact disk transaction, guarded replacement and injected failure cleanup."""
from test_pip_parser import cpu,addr
from test_bios import SENTINEL

def key(d,u,name):
 stem,_,ext=name.partition('.');return (d,u,(stem.ljust(8)+ext.ljust(3)).encode())
def execute(tail,files,fail=None,answer='N',readonly=0,unused=None,exm=0,patch_out=False,input_bytes=b'',patch_in=False):
 c=cpu();c.mem[0:3]=bytes((0xC3,SENTINEL&255,SENTINEL>>8));c.mem[5:8]=bytes((0xDB,254,0xC9));c.mem[0x80]=len(tail);c.mem[0x81:0x81+len(tail)]=tail.encode()
 if patch_out:c.mem[0x106:0x109]=bytes((0xDB,253,0xC9))
 if patch_in:c.mem[0x103:0x106]=bytes((0xDB,252,0xC9))
 inputs=iter(input_bytes)
 files={k:[bytes(v[0]),v[1]] for k,v in files.items()};state={'drive':0,'user':5,'dma':0x80};out=[];calls=[];writes=[]
 def kf(p):return (state['drive'],state['user'],bytes(v&127 for v in c.mem[p+1:p+12]))
 def record(p):return ((c.mem[p+14]&63)*32+(c.mem[p+12]&31))*128+c.mem[p+32]
 def advance(p,n):
  n+=1;c.mem[p+32]=n%128;c.mem[p+12]=(n//128)%32;c.mem[p+14]=n//4096
 def io(port):
  if port==252:c.mem[0x109]=next(inputs);return 0
  if port==253:out.append(chr(c.c));return 0
  f=c.c;p=c.de;calls.append(f)
  if f==0:c.pc=SENTINEL;return 0
  if f==25:return state['drive']
  if f==32:
   if c.e!=255:state['user']=c.e
   return state['user']
  if f==14:state['drive']=c.e;return 0
  if f==26:state['dma']=c.de;return 0
  if f==29:c.hl=readonly;return 0
  if f==31:c.hl=0x7000;c.mem[0x7004]=exm;return 0
  if f==9:
   while c.mem[p]!=36:out.append(chr(c.mem[p]));p+=1
   return 0
  if f in (1,3) and input_bytes:return next(inputs)
  if f==1:return ord(answer)
  if f in (2,4,5):out.append(chr(c.e));c.bc=0;c.hl=0;return 0
  k=kf(p)
  if f in (17,18):
   if f==17:
    pattern=k[2]
    state['search']=[]
    for name in sorted(files):
     if name[:2]!=k[:2] or not all(a==63 or a==b for a,b in zip(pattern,name[2])):continue
     length=len(files[name][0]);group=16384*(exm+1)
     for start in range(0,max(length,1),group):
      extent=start//16384+min(exm,max(0,(min(group,length-start)-1)//16384))
      if c.mem[p+12]==63 or extent==c.mem[p+12]:state['search'].append((name,extent))
    state['searchpos']=0
   else:state['searchpos']+=1
   index=state['searchpos']
   if index>=len(state['search']):return 255
   name,extent=state['search'][index];slot=index%4;start=state['dma']+32*slot
   c.mem[start:start+32]=bytes(32);c.mem[start]=name[1];c.mem[start+1:start+12]=name[2]
   for bit in range(3):c.mem[start+9+bit]|=((files[name][1]>>bit)&1)<<7
   c.mem[start+12]=extent&31;c.mem[start+14]=extent//32
   return slot
  if f==15:
   if k not in files:return 255
   c.mem[p+13]=(-len(files[k][0]))%128
   for bit in range(3):c.mem[p+9+bit]=(c.mem[p+9+bit]&127)|(((files[k][1]>>bit)&1)<<7)
   return 0
  if f==16:
   if fail=='close' and k[2].endswith(b'$$$'):return 255
   if k[2].endswith(b'$$$') and fail is None:
    source_lengths=[len(v[0]) for name,v in files.items() if name[2].startswith(b'SRC')]
    if unused is not None:assert c.mem[p+13]==unused
    elif source_lengths and c.mem[addr('PP_COUNT')]==2:assert c.mem[p+13]==(-source_lengths[0])%128
   return 0
  if f==22:
   if fail=='make':return 255
   assert k not in files
   attr=sum((c.mem[p+9+i]>>7)<<i for i in range(3));files[k]=[b'',attr];return 0
  if f==19:
   if fail=='cancel' and k==key(0,0,'$$$.SUB'):return 255
   if fail=='read_cleanup' and k[2].endswith(b'$$$'):return 255
   if fail=='delete' and not k[2].endswith(b'$$$'):return 255
   if k not in files:return 255
   assert not files[k][1]&1,'unsafe RO delete'
   del files[k];return 0
  if f==30:
   if fail=='attributes':return 255
   files[k][1]=sum((c.mem[p+9+i]>>7)<<i for i in range(3));return 0
  if f==23:
   if fail=='rename':return 255
   target=(k[0],k[1],bytes(v&127 for v in c.mem[p+17:p+28]));assert target not in files
   files[target]=files.pop(k);return 0
  if f==20:
   n=record(p)
   if fail in ('read','read_cleanup') and n==1:return 2
   data=files[k][0];start=n*128
   if start>=len(data):return 1
   c.mem[state['dma']:state['dma']+128]=data[start:start+128].ljust(128,b'\x1a');advance(p,n);return 0
  if f==21:
   n=record(p)
   if fail=='write' and n==1:return 2
   writes.append(k);assert k[2].endswith(b'$$$'),'intended destination modified before commit'
   data=bytes(c.mem[state['dma']:state['dma']+128]);old=files[k][0];start=n*128
   files[k][0]=old[:start].ljust(start,b'\0')+data+old[start+128:];advance(p,n);return 0
  if f==33:
   if fail=='verify_read':return 2
   n=int.from_bytes(c.mem[p+33:p+36],'little');data=files[k][0][128*n:128*n+128]
   if fail=='verify':data=bytes((data[0]^1,))+data[1:]
   c.mem[state['dma']:state['dma']+128]=data;return 0
  raise AssertionError(('unexpected BDOS',f))
 c.port_read=io;c.run(256,limit=8000000)
 assert {k:state[k] for k in ('drive','user','dma')}=={'drive':0,'user':5,'dma':0x80},state
 return ''.join(out),files,calls,writes

def main():
 s=key(0,2,'SRC.DAT');d=key(1,7,'DEST.DAT');t=key(1,7,'DEST.$$$')
 payload=bytes(range(256))*140+b'\x1atail';expected=payload.ljust((len(payload)+127)//128*128,b'\x1a')
 base={s:(payload,5),d:(b'OLD DESTINATION',0)}
 for params in ['', '[V]','[OV]']:
  out,fs,calls,writes=execute('B7:DEST.DAT=A2:SRC.DAT'+params,base)
  assert fs[s]==[payload,5] and fs[d]==[expected,0] and t not in fs,(out,fs.keys())
  assert bool(33 in calls)==('V' in params)
 for failure,diagnostic in [('read','DISK READ ERROR'),('write','DISK WRITE ERROR'),('verify','VERIFY ERROR'),('verify_read','VERIFY ERROR'),('close','CANNOT CLOSE DESTINATION'),('make','NO DIRECTORY SPACE'),('delete','CANNOT REPLACE DESTINATION')]:
  out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT[V]',base,fail=failure)
  assert diagnostic in out and fs[s]==[payload,5] and fs[d]==[b'OLD DESTINATION',0] and t not in fs,(failure,out,fs.keys())
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT[V]',base,fail='rename')
 assert 'CANNOT RENAME' in out and t in fs and fs[t][0]==expected and d not in fs
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT',base,fail='read_cleanup')
 assert 'DISK READ ERROR' in out and 'CLEANUP FAILED: temporary file remains.' in out
 assert t in fs and fs[d]==[b'OLD DESTINATION',0] and fs[s]==[payload,5]
 protected={**base,d:(b'OLD DESTINATION',1)}
 for answer,param in [('N',''),('Y',''),('N','[W]')]:
  out,fs,calls,_=execute('B7:DEST.DAT=A2:SRC.DAT'+param,protected,answer=answer)
  assert fs[d][0]==(b'OLD DESTINATION' if answer=='N' and not param else expected)
  assert (1 in calls)==(not param)
 for tail in ['A2:SRC.DAT=A2:SRC.DAT','A2:SRC.$$$=A2:SRC.DAT','A2:SRC.TXT=A2:SRC.$$$']:
  out,fs,calls,writes=execute(tail,base);assert 'staging-name conflict' in out and not any(f in calls for f in (19,22,23))
 out,fs,calls,_=execute('B7:DEST.DAT=A2:SRC.DAT',base,readonly=2);assert 'DRIVE IS R/O' in out and fs=={k:list(v) for k,v in base.items()}
 sysbase={s:(payload,2),d:(b'OLD DESTINATION',0)}
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT',sysbase);assert 'NO FILE' in out and fs[d][0]==b'OLD DESTINATION'
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT[RV]',sysbase);assert fs[d][0]==expected
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT', {**base,t:(b'OLD TEMP',1)});assert 'CANNOT REMOVE TEMPORARY' in out and fs[t]==[b'OLD TEMP',1]
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT', {**base,t:(b'OLD TEMP',6)});assert fs[d]==[expected,0]
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT', {s:(b'',0)});assert fs[d]==[b'',0]
 for command in ['PRN:=A2:SRC.DAT','B7:=A2:*.DAT[U]','B7:D=A2:SRC.DAT[U]','B7:D=A2:SRC.DAT,A2:SRC.DAT[U]']:
  out,fs,calls,_=execute(command,base);assert 'not implemented' in out and not any(f in calls for f in (19,22,23))
 queue=key(0,0,'$$$.SUB');other=key(1,7,'$$$.SUB')
 batch={**base,queue:(b'BATCH',0),other:(b'UNRELATED',0)}
 for command in ['BAD','B7:DEST.DAT=A2:MISSING.DAT','B7:D=A2:SRC.DAT[U]']:
  out,fs,_,_=execute(command,batch)
  assert queue not in fs and fs[other]==[b'UNRELATED',0] and fs[d]==[b'OLD DESTINATION',0]
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT',batch,fail='read')
 assert queue not in fs and fs[other]==[b'UNRELATED',0] and t not in fs
 out,fs,_,_=execute('B7:DEST.DAT=A2:SRC.DAT',batch)
 assert fs[queue]==[b'BATCH',0]
 out,fs,calls,_=execute('/VER',batch)
 assert 'Build 010' in out and fs[queue]==[b'BATCH',0] and calls==[9]
 for protection in ['cancel','roqueue','rodrive']:
  protected_batch={**batch,queue:(b'BATCH',1 if protection=='roqueue' else 0)}
  out,fs,_,_=execute('BAD',protected_batch,fail='cancel' if protection=='cancel' else None,readonly=1 if protection=='rodrive' else 0)
  assert 'CANNOT CANCEL SUBMIT QUEUE' in out and queue in fs and fs[other]==[b'UNRELATED',0]
 print('PASS: exact PIP record copy, V/W/R, DU restoration, guarded replacement and injected transaction failures')
if __name__=='__main__':main()
