#!/usr/bin/env python3
"""Execute selected original MM 2.32 console pages; no reference bytes redistributed."""
import argparse
import hashlib
from pathlib import Path
from test_bios import Z80

SHA256='a13e310d0668b744ebe36c0aa5621a9d6148dcb45b3477d425ea3efb38e5504e'
DEFAULT=Path('/Users/nathanael/CPM/montezuma-micro/images/CPMb232.dsk')


def reference(image):
    data=image.read_bytes()
    assert hashlib.sha256(data).hexdigest()==SHA256,'unqualified reference image'
    length=int.from_bytes(data[2:4],'little')
    raw=bytearray()
    for track in range(3):
        block=data[16+track*length:16+(track+1)*length]
        for i in range(0,128,2):
            address=int.from_bytes(block[i:i+2],'little')&0x3fff
            if not address:break
            assert block[address]==254
            size=128<<block[address+4]
            mark=block.find(b'\xfb',address+7,address+100)
            assert mark>=0
            raw.extend(block[mark+1:mark+1+size])
    cpu=Z80(b'')
    # Physical sectors are not a linear memory dump. Locate console and fill
    # pages using their original instruction signatures and absolute operands.
    for signature,low,address in [(bytes.fromhex('3e8ed3843ac8f0cd6cef'),0x48,0xEF00),
                                  (bytes.fromhex('af1808af18033acbf0ee8032cbf0'),0x8F,0xF000),
                                  (bytes.fromhex('626b770b78b1c813edb0c9'),0x33,0xED00)]:
        found=raw.find(signature)
        assert found>=0 and raw.find(signature,found+1)<0
        start=found-low
        assert start%256==0
        cpu.mem[address:address+256]=raw[start:start+256]
    return cpu


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=DEFAULT)
    args=parser.parse_args()
    cpu=reference(args.image)
    def control(char):
        cpu.c=char
        cpu.run(0xEFD9,limit=20000)  # original table dispatch, not a replacement handler
    for old in [0,128]:
        cpu.mem[0xF0CB]=old
        control(15)
        assert cpu.mem[0xF0CB]==128
        control(15)
        assert cpu.mem[0xF0CB]==128
    pattern=bytes(33+(i//80)%90 for i in range(1920))
    cases=0
    for row in range(24):
        for col in range(80):
            for reverse in [0,128]:
                for char in [28,29]:
                    cpu.mem[0xF800:0xFF80]=pattern
                    cpu.mem[0xF0CB]=reverse
                    cpu.setword(0xF0C9,row+256*col)
                    expected=bytearray(pattern)
                    start=row*80
                    blank=bytes([32|reverse])*80
                    if char==28:
                        expected[start+80:]=pattern[start:1840]
                        expected[start:start+80]=blank
                    else:
                        expected[start:1840]=pattern[start+80:]
                        expected[1840:]=blank
                    control(char)
                    assert cpu.mem[0xF800:0xFF80]==expected,(row,col,reverse,char)
                    assert cpu.word(0xF0C9)==row+256*col
                    cases+=1
    print(f'PASS: original MM 2.32 0Fh sets reverse ON; {cases} insert/delete cases preserve cursor and use mode-aware blanks')


if __name__=='__main__':main()
