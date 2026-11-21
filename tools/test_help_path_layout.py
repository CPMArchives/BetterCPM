"""Execute HELP's PATH discovery using independent post-PDS kernel fixtures."""
import argparse
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=Path('build/help'));args=p.parse_args()
    image=(args.build/'HELP.COM').read_bytes()
    listing=(args.build/'help.lst').read_text(encoding='latin-1')
    # WBOOT, BM1 descriptor and numeric PATH from the merged 1.3 layouts.
    for wboot,descriptor,path in ((0xe994,0xd650,0xe432),
                                  (0xf594,0xe250,0xf032),
                                  (0xf5ec,0xe250,0xf032)):
        c=Z80(b'');c.mem[0x100:0x100+len(image)]=image;c.sp=0x7000
        c.setword(1,wboot);c.mem[descriptor:descriptor+4]=b'BM\1\5'
        c.mem[path:path+5]=bytes((2,2,3,3,2))  # B3:, C2:
        c.mem[address(listing,'home_drive')]=1;c.mem[address(listing,'home_user')]=0
        c.mem[address(listing,'path_count')]=0
        c.run(address(listing,'init_path'),limit=100000)
        count=c.mem[address(listing,'path_count')];at=address(listing,'path_list')
        assert count==3 and c.mem[at:at+6]==bytes((1,0,2,3,3,2)),(wboot,count,bytes(c.mem[at:at+6]))
    print('PASS HELP reads effective protected PATH on all three 1.3 layouts')


if __name__=='__main__':main()
