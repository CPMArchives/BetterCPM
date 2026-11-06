#!/usr/bin/env python3
"""Execute RSX/XSUB source parsing and query precedence on the full Z80 core."""
from test_rsx_offline import Machine, ROOT, L


def main():
    m=Machine()
    calls=[];console=[]
    original=m.callback
    def bdos(kind):
        if kind!=1:
            return original(kind)
        fn=m.reg['C'].value
        de=m.pair('DE')
        if fn==25:value=2
        elif fn==32:value=17
        elif fn==177:
            request=bytes(m.mem[de:de+20]);calls.append(request);value=0
        elif fn==9:
            for i in range(de,65536):
                if m.mem[i]==36:break
                console.append(chr(m.mem[i]))
            else:raise AssertionError('unterminated message')
            value=0
        elif fn==2:value=0
        else:raise AssertionError(fn)
        m.reg['A'].value=value
        m.reg['F'].value=0x40 if value==0 else 0
    # Rebind the native hook, retaining it throughout execution.
    import ctypes as C
    m.hook=C.CFUNCTYPE(None,C.c_int)(bdos)
    m.lib.set_hooks(L['FILE'],L['BDOS'],m.hook)
    m.mem[5:8]=bytes((0xC3,L['BDOS']&255,L['BDOS']>>8))
    def run(name,tail):
        calls.clear();console.clear()
        image=(ROOT/f'build/utilities/{name}.COM').read_bytes()
        m.mem[0x100:0x100+len(image)]=image
        raw=tail.encode('ascii');m.mem[0x80]=len(raw);m.mem[0x81:0x81+len(raw)]=raw
        m.run(0x100)
        return list(calls)
    for stem in ('XSUB','RSX'):
        for drive in (0,1,15):
            for user in (0,3,17,31):
                operand=f'{chr(65+drive)}{user}:'
                command=' '+operand if stem=='XSUB' else ' LOAD '+operand+'HELLO.RSX'
                result=run(stem,command)
                assert result and result[-1][0]==3,(stem,command,''.join(console))
                assert result[-1][18:20]==bytes((drive,user)),(stem,command,result)
                assert result[-1][2]==0
        result=run(stem,'' if stem=='XSUB' else ' LOAD HELLO')
        assert result[-1][18:20]==bytes((2,17)) and result[-1][2]==1
        for bad in ('Q0:','B32:','B999:','1:','B-1:'):
            result=run(stem,' '+bad if stem=='XSUB' else ' LOAD '+bad+'HELLO')
            assert not result,(stem,bad,result)
        for query in (' /HELP B32:',' /VER B32:'):
            assert not run(stem,query),(stem,query)
    assert not run('XSUB',' B0: JUNK')
    assert not run('RSX',' UNLOAD B0:HELLO')
    print('PASS bounded drive/user parsing, current-DU defaults, malformed sources, explicit search restriction and query precedence')


if __name__=='__main__':main()
