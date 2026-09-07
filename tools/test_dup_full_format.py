#!/usr/bin/env python3
"""Format and verify all 160 surfaces of the default 800K data disk."""
from pathlib import Path
import tempfile
from test_disk_utilities import run,crc16

def main():
 with tempfile.TemporaryDirectory(prefix='dup-full-') as tmp:
  screens,w,old=run(Path(tmp),'format-80-ds',[
   ('DUP\r',5000),('A',700),('B',1000),('Y','Format complete.'),('\r',1000),('\x03',3000)],blank=True,timeout=900)
  assert 'Tracks written and verified: 00160' in screens[3][0],screens[3][0]
  assert 'Format complete.' in screens[3][0],screens[3][0]
  assert 'A0>' in screens[-1][0],screens[-1][0]
  # Exclude boot/menu waits. The final capture is triggered by completion,
  # not a fixed delay; the short Y keypress is included in the measurement.
  elapsed=(w/'trs80-text-3.bin').stat().st_mtime-(w/'trs80-text-2.bin').stat().st_mtime
  print(f'Format + verify: {elapsed:.2f} wall seconds (trs80gp -turbo).',flush=True)
  data=(w/'b.dmk').read_bytes();size=int.from_bytes(data[2:4],'little')
  count=0
  for cyl in range(80):
   for side in range(2):
    t=data[16+(cyl*2+side)*size:16+(cyl*2+side+1)*size];ids=[]
    for j in range(0,128,2):
     p=int.from_bytes(t[j:j+2],'little')&0x3fff
     if not p:break
     assert t[p:p+3]==bytes([254,cyl,side]),(cyl,side)
     assert t[p+4]==2
     assert t[p+5:p+7]==crc16(b'\xa1'*3+t[p:p+5]).to_bytes(2,'big')
     mark=t.find(b'\xa1'*3+b'\xfb',p+7);assert mark>=0
     assert t[mark+4:mark+516]==b'\xe5'*512,(cyl,side,t[p+3])
     assert t[mark+516:mark+518]==crc16(t[mark:mark+516]).to_bytes(2,'big')
     ids.append(t[p+3]);count+=1
    assert sorted(ids)==list(range(1,11)),(cyl,side,ids)
  assert count==1600
  print('PASS: all 160 tracks / 1600 sectors have valid IDs, CRCs and erased data; completion count and warm exit verified.')
if __name__=='__main__':main()
