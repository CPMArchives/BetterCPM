#!/usr/bin/env python3
"""Exercise CONFIG working copy, apply, warm exit and DUP on scratch media."""
from pathlib import Path
import tempfile
from test_disk_utilities import run

def main():
 with tempfile.TemporaryDirectory(prefix='bettercpm-editor-') as tmp:
  # Clone standard MM, then make a two-cylinder, data-only experiment.
  steps=[('CONFIG\r',4000),('G',1000),('B',1000),('A',1000),('1',1500),
   ('\r',1000),('\x03',1000),('I',1000),('B',1000),
   ('L',700),('2\r',1000),('K',700),('0\r',1000),('F',700),('3\r',1000),
   ('Q',1500),('\r',1000),('\x03',3000),('DUP\r',4000),('A',1000),('B',1200),
   ('Y',5000),('\r',1000),('\x03',3000)]
  screens,w,old=run(Path(tmp),'format-editor',steps)
  assert 'Disk configuration changed' in screens[15][0],screens[15][0]
  assert 'Format complete.' in screens[21][0],screens[21][0]
  assert 'A0>' in screens[-1][0],screens[-1][0]
  disk=(w/'b.dmk').read_bytes();size=int.from_bytes(disk[2:4],'little')
  for cyl in range(80):
   for side in range(2):
    off=16+(cyl*2+side)*size;t=disk[off:off+size]
    if cyl>=2 or side:
     assert t==old[off:off+size],(cyl,side,'untargeted track changed')
     continue
    ids=[]
    for j in range(0,128,2):
     ptr=int.from_bytes(t[j:j+2],'little')&0x3fff
     if not ptr:break
     assert t[ptr:ptr+3]==bytes([254,cyl,0])
     assert t[ptr+4]==1
     ids.append(t[ptr+3])
     mark=t.find(b'\xa1\xa1\xa1\xfb',ptr+7)
     assert mark>=0 and t[mark+4:mark+260]==b'\xe5'*256
    assert ids==list(range(1,19,2))+list(range(2,19,2)),ids
  print('PASS: CONFIG edited format survives exit; DUP formats precisely two selected tracks; system disk unchanged.')
if __name__=='__main__':main()
