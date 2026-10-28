"""Run actual COM query paths; only console output is allowed."""
from pathlib import Path
from test_bios import Z80
from utility_help import text
from build_dump import version_text
ROOT=Path(__file__).resolve().parents[1]

def execute(name,tail):
    c=Z80(b'');image=(ROOT/f'build/utilities/{name}.COM').read_bytes()
    c.mem[256:256+len(image)]=image
    c.mem[5:8]=b'\xd3\x00\xc9';c.mem[0:3]=b'\xc3\xfe\xff'
    raw=tail.encode();c.mem[128]=len(raw);c.mem[129:129+len(raw)]=raw
    saved=bytes(c.mem[128:256]);out=bytearray();services=[]
    def bdos(port,value):
        services.append(c.c);assert c.c==9,(name,c.c)
        end=c.mem.index(36,c.de);out.extend(c.mem[c.de:end])
        c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
    c.port_write=bdos;sp=c.sp;c.run(256,limit=2000000)
    assert c.sp==sp and bytes(c.mem[128:256])==saved
    return out.decode()

def main():
    count=0
    for name in ('DUMP','DASM','DSYM','TED'):
        identity=version_text().splitlines()[0] if name=='DUMP' else None
        expected=text(name,identity)
        for tail in ('/HELP','/help /VER /UNKNOWN','/VER /HELP BAD','FILE.BIN\t/HELP','X'*121+' /HELP'):
            actual=execute(name,tail);assert actual==expected,(name,tail,actual,expected);count+=1
        ver=execute(name,'/VER');assert ver.splitlines()[0]==expected.splitlines()[0];count+=1
    print(f'{count} compiled help/version queries: layout, identity, screen bounds, console-only services, stack/tail preservation PASS')

if __name__=='__main__':main()
