"""Execute the RAM adapter and BIOS: exceptional surface I/O must never reach ports."""
from pathlib import Path
import argparse,ctypes as C,shutil,subprocess
from test_usq import SHIM
from fdf_format import FDFFormat
from test_bios import Z80
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,default=ROOT/'build/z80pack');args=p.parse_args()
    fmt=FDFFormat('ATONDS',64,4,15,0,607,191,224,0,48,2,8,3,77,0xc0,(1,4,7,2,5,8,3,6),26,128,'FM',tuple(range(1,27)))
    resident=(args.build/'resident.bin').read_bytes();config=(args.build/'config.bin').read_bytes()
    bs=symbols(args.build/'bios.lst');ds=symbols(args.build/'disk.lst')
    def cpu():
        c=Z80(b'');c.sp=0x7800
        c.mem[L['SYSTEM']:L['SYSTEM']+len(resident)]=resident
        c.mem[L['CONFIG']:L['CONFIG']+len(config)]=config
        c.mem[L['TABLES']+96:L['TABLES']+160]=fmt.binding(1)
        c.mem[bs['BIO_DRIVE']]=1;c.setword(bs['BIO_TRACK'],0);c.setword(bs['BIO_SECTOR'],0);c.setword(bs['BIO_DMA'],0x7000)
        c.port_read=lambda port:(_ for _ in ()).throw(AssertionError(('forbidden port read',port)))
        c.port_write=lambda port,value:(_ for _ in ()).throw(AssertionError(('forbidden port write',port,value)))
        return c
    for entry in (ds['Z_MAP'],L['BIOS']+39,L['BIOS']+42):
        c=cpu();c.run(entry);assert c.a==1,(entry,c.a)
    # Use the independent full Z80 core for the overlay's indexed-IY code.
    work=ROOT/'build/boot-io-test';work.mkdir(parents=True,exist_ok=True)
    source=Path.home()/'projects/git/z80pack';core=source/'z80core'
    (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):shutil.copy2(source/'z80sim/srcsim'/name,work/name)
    shim=SHIM.replace('BYTE io_in', 'unsigned int port_accesses;\nBYTE io_in').replace('{ return 0; }','{ port_accesses++; return 2; }',1).replace('BYTE d) {}','BYTE d) { port_accesses++; }')
    (work/'shim.c').write_text(shim)
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',str(work/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
    lib=C.CDLL(str(work/'core.so'));mem=(C.c_ubyte*65536).in_dll(lib,'memory')
    lib.test_run.argtypes=[C.c_ushort,C.c_int];lib.test_run.restype=C.c_int
    for cyl in (0,1,76):
        c=cpu();c.mem[0x7200:0x7203]=bytes((1,cyl,0))
        entry=L['CONFIG']+6;c.mem[0x6000:0x6005]=bytes((0xdd,0xe5,0xc3,entry&255,entry>>8))
        mem[:]=bytes(c.mem);C.c_ushort.in_dll(lib,'SP').value=0x7800;C.c_ushort.in_dll(lib,'IX').value=0x7200
        C.c_uint.in_dll(lib,'port_accesses').value=0
        assert lib.test_run(0x6000,100000)>0
        assert C.c_ubyte.in_dll(lib,'H').value==0 and C.c_ubyte.in_dll(lib,'L').value==2
        assert C.c_uint.in_dll(lib,'port_accesses').value==0
    # The same mapper still accepts the next physical surface and the final
    # allocation-bearing surface, including alternating head-one mapping.
    for track,marker in ((0,0),(1,1),(2,1),(153,1)):
        c=cpu();c.mem[L['TABLES']+96+61]=marker;c.setword(bs['BIO_TRACK'],track)
        writes=[];c.port_write=lambda port,value:writes.append((port&255,value));c.port_read=lambda port:2
        c.run(ds['Z_MAP']);assert c.a==0 and writes,(track,c.a)
        assert c.mem[ds['ZP_TRACK']]==track
    print('PASS actual BIOS read/write refusal before port access, all format refusal, ordinary and final surface mapping')
if __name__=='__main__':main()
