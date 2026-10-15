#!/usr/bin/env python3
"""X range copy, deferred records, bare-R pending tail and lifetime cleanup."""
from test_ed_buffer import context


def setup(body,write_error=False):
    c,s,call,state,run=context(1024);files={};ops=[];drive=0;user=0;dma=0;readpos=0;opened=None
    c.mem[s['EI_SDRV']]=0;c.mem[s['EI_SUSR']]=7
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal drive,user,dma,readpos,opened
        ops.append(c.c)
        if c.c==14:drive=c.e;return 0
        if c.c==32:user=c.e;return 0
        if c.c==26:dma=c.de;return 0
        f=c.de;key=(drive,user,bytes(c.mem[f+1:f+12]))
        if c.c==19:
            return 0 if files.pop(key,None) is not None else 255
        if c.c==22:files[key]=b'';return 0
        if c.c==16:return 0
        if c.c==21:
            assert dma==s['GX_DATA'] and key in files
            if write_error:return 2
            files[key]+=bytes(c.mem[dma:dma+128]);return 0
        if c.c==15:
            opened=key;readpos=0;return 0 if key in files else 255
        if c.c==20:
            assert dma==s['GR_DATA'];record=files[opened][readpos:readpos+128];readpos+=128
            if not record:return 1
            c.mem[dma:dma+128]=record;return 0
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io
    for byte in body:c.c=byte;assert not call('EB_PUT')[0]
    call('EB_TOP')
    return c,s,call,state,run,files,ops


def main():
    body=b'one\r\ntwo\r\nlast'
    c,s,call,state,run,files,ops=setup(body)
    assert run(b'x')[0]==(False,0) and state()==(body,0)
    assert c.mem[s['GX_POS']]==5 and list(files.values())==[b'']
    assert run(b'Lx')[0]==(False,0) and state()==(body,5)
    assert run(b'-Br')[0]==(False,0) and state()==(body+b'one\r\ntwo\r\n',24)
    assert run(b'0x')[0]==(False,0) and not files and c.mem[s['GX_ACTIVE']]==0
    assert run(b'r')[0]==(True,ord('O'))
    c,s,call,state,run,files,ops=setup(b'mixed\r\n'*30)
    assert not run(b'#x')[0][0] and c.mem[s['GX_POS']]==82
    assert list(files.values())==[(b'mixed\r\n'*30)[:128]]
    assert not run(b'-BR')[0][0]
    expected=(b'mixed\r\n'*30)+ (b'mixed\r\n'*30)[:128].upper()+(b'mixed\r\n'*30)[128:]
    assert state()==(expected,len(expected))
    c.mem[s['FQ_DRIVE']]=0;c.a=0;call('FQ_LEAVE')
    assert not files and c.mem[s['GX_ACTIVE']]==0
    c,s,call,state,run,files,ops=setup(b'a\x1ab')
    assert not run(b'#x-Br')[0][0] and state()==(b'a\x1aba\x1ab',6)
    c,s,call,state,run,files,ops=setup(b'x'*200,write_error=True)
    assert run(b'#x')[0]==(True,ord('?')) and c.mem[s['EC_IOERR']]==2
    assert state()==(b'x'*200,0) and c.mem[s['GX_POS']]==128
    print('PASS: X nonmoving ranges, append/clear, deferred disk records, R raw tail, cleanup and write failure')


if __name__=='__main__':main()
