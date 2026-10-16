#!/usr/bin/env python3
"""Build-symbol ownership, instruction/record bounds and unambiguous descriptors."""
import struct,zlib,tempfile
from pathlib import Path
from build_distribution import validate_config_cold_patch
from iobyte_config import descriptor,assembly

def main():
 code=bytearray(256);code[16:21]=bytes.fromhex('3e95320300')
 listing='5010  3e 95  1 1 IO_COLD: LD A,095H\n'
 item=descriptor(code,0x5000,listing,80,4)
 assert struct.unpack('<HBBHI',item)==(80,4,17,65535,zlib.crc32(code[:128]))
 item2=descriptor(code,0x5000,listing,36,8)
 assert struct.unpack('<HBBHI',item2)==(36,8,17,17,zlib.crc32(code[:128]))
 for bad_code,bad_listing in [(code,''),(code,listing+listing),
                              (bytes([0])*256,listing),
                              (code,listing.replace('5010','50ff'))]:
  try:descriptor(bad_code,0x5000,bad_listing,80,4)
  except ValueError:pass
  else:raise AssertionError('unsafe descriptor accepted')
 try:assembly([item,item])
 except ValueError:pass
 else:raise AssertionError('ambiguous descriptors accepted')
 # No buffer may overlap another owner or the existing track/save regions.
 spans=[(0xa800,127),(0xa880,256),(0xa980,24),(0xa9a0,256),(0xaaa0,64),(0xaae0,128),(0xab60,128)]
 for i,(at,size) in enumerate(spans):
  assert 0xa800<=at and at+size<=0xac00
  for other,n in spans[i+1:]:assert at+size<=other or other+n<=at
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);(root/'build/trs80').mkdir(parents=True)
  stage=bytes.fromhex('3e95320300')+bytes(507)
  listing='5000  3e 95  1 1 IO_COLD: LD A,095H\n'
  (root/'build/trs80/stage1.lst').write_text(listing)
  raw=root/'image';raw.write_bytes(bytes(512)+stage)
  item=descriptor(stage,0x5000,listing,80,4)
  component={'name':'CONFIG.COM','user':0}
  validate_config_cold_patch('trs80gp',raw,[(component,b'program'+item)],root)
  for program in [b'program',b'program'+item+item]:
   try:validate_config_cold_patch('trs80gp',raw,[(component,program)],root)
   except ValueError:pass
   else:raise AssertionError('missing/duplicate patch descriptor published')
 print('PASS build-owned cold IOBYTE descriptors and disjoint CONFIG scratch ranges')
if __name__=='__main__':main()
