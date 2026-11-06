"""Old native reader rejection and explicit Model 4 binding refusal."""
from pathlib import Path
import subprocess,tempfile
from build_ccp import assemble
from build_z80pack_image import symbols
from fdf_v1 import serialize
from test_boot_surface import formats
from test_bios import Z80
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]
BASELINE='6fea04295e2eb3cf1a748af428400e4e1389117c'

def main():
    old=subprocess.run(['git','show',BASELINE+':src/utilities/disk/fdbread.inc'],cwd=ROOT,check=True,capture_output=True,text=True).stdout
    prefix='''        ASEG
        ORG 100H
FDBRTON EQU 1
FCOUNT: DB 0
BIND: DS 64
CURB: DS 64
FINDIDX:DB 0
CUSTOM: DB 0
UNDEF: DB 0
PUTC: RET
PUTS: RET
FDFRAM EQU 04000H
FDFLIM EQU 07F80H
'''
    with tempfile.TemporaryDirectory(prefix='old-fdb-reader-') as tmp:
        out=Path(tmp);code=assemble(Path.home()/'bin/z80asm',prefix+old[old.index('FDBVALID:'):]+'\n END\n',out/'old.bin',out/'old.lst',0x100);names=symbols(out/'old.lst')
    c=Z80(b'');c.sp=0x7800;c.mem[0x100:0x100+len(code)]=code
    payload=serialize(formats());c.mem[0x4000:0x4000+len(payload)]=payload;c.setword(names['FDBLEN'],len(payload))
    c.run(names['FDBVALID'],limit=3000000);assert not c.carry
    for index in (0,1):
        c.a=index;c.run(names['FDBISSUPPORTED']);assert c.z
        c.a=index;c.run(names['FDBBIND']);assert c.carry
    # Model 4 rejects the marker before physical geometry or any I/O.
    c=Z80(b'');c.sp=0x7800
    resident=(ROOT/'build/system/resident.bin').read_bytes();control=(ROOT/'build/system/config.bin').read_bytes()
    assert len(control)<=1024
    c.mem[L['SYSTEM']:L['SYSTEM']+len(resident)]=resident;c.mem[L['CONFIG']:L['CONFIG']+len(control)]=control
    c.mem[0x7200]=1;c.mem[0x723e]=1;c.ix=0x7200
    entry=symbols(ROOT/'build/system/config.lst')['DC_VALIDATE']
    c.mem[0x6000:0x6005]=bytes((0xdd,0xe5,0xc3,entry&255,entry>>8));c.run(0x6000)
    assert c.hl==2
    print('PASS pinned pre-extension native reader refuses ATONSS/ATONDS; Model 4 refuses adapter marker')
if __name__=='__main__':main()
