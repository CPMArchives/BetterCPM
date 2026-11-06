"""New CONFIG must query capability before publishing a boot-exception binding."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text();entry=address(listing,'API')
    for marker in (0,1):
        for capability in (0,1,2,0xb301,0xb300):
            cpu=Z80(b'');cpu.mem[256:256+len(image)]=image
            cpu.mem[5:8]=bytes((0xdb,254,0xc9))
            cpu.de=0x7000;cpu.mem[0x7000]=1;cpu.mem[0x703e]=marker
            before=bytes(cpu.mem[0x7000:0x7050]);ops=[]
            def io(port):
                assert cpu.c==181
                ops.append(cpu.b)
                if cpu.b==6:cpu.hl=capability
                elif cpu.b==4:cpu.hl=0
                else:raise AssertionError(cpu.b)
                return cpu.l
            cpu.port_read=io;cpu.b=4;cpu.run(entry)
            accepted=not marker or capability==0xb301
            assert ops==([6,4] if marker else [4]) if accepted else ops==[6]
            assert cpu.hl==(0 if accepted else 2)
            assert bytes(cpu.mem[0x7000:0x7050])==before
    print('PASS new CONFIG + old/new BIOS capability matrix: no unsupported binding request or request mutation')
if __name__=='__main__':main()
