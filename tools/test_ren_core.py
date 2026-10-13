#!/usr/bin/env python3
"""Execute transient REN's core against a directory/BDOS fixture."""
from pathlib import Path
from test_bios import Z80, SENTINEL
ROOT=Path(__file__).resolve().parents[1]
def run(tail, files, responses='', ledger_capacity=None, rename_failures=None, racing_target=False, drive_ro=False, attr_failures=None):
 responses=iter(responses)
 c=Z80(b''); image=(ROOT/'build/utilities/REN.COM').read_bytes()
 c.mem[0x100:0x100+len(image)]=image;c.mem[0:3]=bytes((0xC3,SENTINEL&255,SENTINEL>>8))
 c.mem[5:8]=bytes((0xDB,254,0xC9))
 c.mem[0x80]=len(tail);c.mem[0x81:0x81+len(tail)]=tail.encode()
 state={'drive':0,'user':0,'dma':0x80,'rows':[],'index':0};mutations=[];output=[]
 def io(port):
  assert port&255==254
  f=c.c
  if f==2:output.append(chr(c.e));return c.e
  if f==1:
   ch=next(responses,None);assert ch is not None,'unexpected prompt'
   output.append(ch);return ord(ch)
  if f==25:return state['drive']
  if f==32:
   if c.e!=255:state['user']=c.e
   return state['user']
  if f==14:state['drive']=c.e;return 0
  if f==26:state['dma']=c.de;return 0
  if f==29:c.hl=2 if drive_ro else 0;return 0
  if f==9:
   p=c.de
   while c.mem[p]!=36:output.append(chr(c.mem[p]));p+=1
   return 0
  if f in (17,18):
   if ledger_capacity is not None:
    import re
    listing=(ROOT/'build/utilities/ren.lst').read_text()
    def address(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    limit=address('R_HEAP')+11*ledger_capacity
    p=address('R_LIMIT');c.mem[p:p+2]=limit.to_bytes(2,'little')
   if f==17:
    pat=bytes(c.mem[c.de+1:c.de+12])
    state['rows']=[(k,attr) for k,v in files.items() for attr in (v if isinstance(v,tuple) else (v,)) if k[:2]==(state['drive'],state['user']) and all(a==63 or a==b for a,b in zip(pat,k[2]))]
    state['index']=0
   i=state['index']
   if i>=len(state['rows']):return 255
   k,attr=state['rows'][i];state['index']+=1
   row=bytearray(32);row[0]=k[1];row[1:12]=k[2]
   for b in range(3):row[9+b]|=((attr>>b)&1)*128
   c.mem[state['dma']:state['dma']+32]=row
   return 0
  if f==30:
   name=bytes(x&127 for x in c.mem[c.de+1:c.de+12]);key=(state['drive'],state['user'],name)
   if attr_failures and attr_failures.pop(0):return 255
   assert key in files
   files[key]=sum((c.mem[c.de+9+b]>>7)<<b for b in range(3))
   return 0
  if f==23:
   old=(state['drive'],state['user'],bytes(c.mem[c.de+1:c.de+12]));new=(old[0],old[1],bytes(c.mem[c.de+17:c.de+28]))
   if rename_failures and rename_failures.get(old,0):
    rename_failures[old]-=1
    if racing_target:files[new]=4
    return 255
   assert old in files and new not in files
   if any(v&1 for v in (files[old] if isinstance(files[old],tuple) else (files[old],))):return 255
   files[new]=files.pop(old);mutations.append((old,new));return 0
  raise AssertionError(f)
 c.port_read=io;c.run(0x100,limit=2000000)
 assert state['drive']==0 and state['user']==0,'caller DU not restored'
 return mutations,''.join(output)
def main():
 a=b'FOO     DOC';b=b'BAR     DOC'
 for command in ('B[1,3]:*.DOC *.TXT','*.TXT=B[1,3]:*.DOC'):
  files={(1,1,a):4,(1,3,b):0,(1,3,a):1}
  changes,out=run(command,files)
  assert len(changes)==2 and files[(1,1,b'FOO     TXT')]==4
  assert (1,3,a) in files,'RO source changed'
 for command in ('/DRY B[1,3]:*.DOC *.TXT','B[1,3]:*.DOC B2:*.TXT','B[1,3]:F*A.DOC *.TXT'):
  files={(1,1,a):0,(1,3,b):0};before=files.copy()
  changes,out=run(command,files);assert not changes and files==before,(command,out)
 changes,out=run('B1:*.DOC[$ARC] *.TXT',{(1,1,a):4,(1,1,b):0})
 assert len(changes)==1 and changes[0][0][2]==a
 for command,files in (
  ('B1:*.DOC *.TXT',{(1,1,a):0,(1,1,b'FOO     TXT'):0}),
  ('B1:*.DOC *.DOC',{(1,1,a):0}),
  ('B1:*.DOC *.TXT',{(1,1,a):2})):
  before=files.copy();changes,out=run(command,files,'S')
  assert not changes and files==before,(command,out)
 # A renamed target still matching the source is a fixed point, never renamed again.
 changes,out=run('B1:*.* X*.*',{(1,1,a):0,(1,1,b):0})
 assert len(changes)==2
 changes,out=run('/VER',{})
 assert not changes and 'BetterCP/M REN 1.0 (Build 005)' in out
 print('PASS: transient REN operand orders, multi-DU, predicates, attributes, protection, dry run, invalid syntax, caller DU and version')
if __name__=='__main__':main()
