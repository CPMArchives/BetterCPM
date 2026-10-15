#!/usr/bin/env python3
"""N autoscan through bounded batches with real gap/output/source routines."""
from test_ed_finish import setup


def main():
    for prefix in (b'',b'old\r\n'*300):
        source=prefix+b'needle tail\r\n'
        c,s,call,state,run,writes,calls=setup(source,execution_limit=1000000)
        result,_=run(b'nneedle')
        assert result==(False,0) and state()[0].endswith(b'needle tail\r\n')
        text,pos=state();assert text[pos-6:pos]==b'needle'
        assert c.mem[s['EG_PATTERN']]==6
        # Finishing after autoscan must not duplicate or drop source text.
        assert call('EF_DRAIN')==(False,0)
        assert b''.join(writes).rstrip(b'\x1a')==source
    c,s,call,state,run,writes,calls=setup(b'one\r\nneedle x needle\r\n')
    assert run(b'2nneedle')[0]==(False,0) and state()[1]==20
    c,s,call,state,run,writes,calls=setup(b'no match\r\n')
    assert run(b'nmissing')[0]==(True,ord('#')) and state()==(b'',0)
    assert call('EF_DRAIN')==(False,0) and b''.join(writes).rstrip(b'\x1a')==b'no match\r\n'
    c,s,call,state,run,writes,calls=setup(b'Mixed mixed\r\n')
    assert run(b'Unmixed')[0]==(False,0) and state()[0]==b'MIXED MIXED\r\n'
    c,s,call,state,run,writes,calls=setup(b'anything')
    assert run(b'0nanything')[0]==(False,0) and not calls
    assert run(b'-nanything')[0]==(True,ord('?')) and not calls
    c,s,call,state,run,writes,calls=setup(b'anything',read_error=True)
    assert run(b'nanything')[0]==(True,ord('?')) and c.mem[s['EC_IOERR']]==2
    c,s,call,state,run,writes,calls=setup(b'needle',editing=b'x'*200,write_error=True)
    assert run(b'nneedle')[0]==(True,ord('?')) and c.mem[s['EC_IOERR']]==2
    assert state()==(b'x'*72,0) and 20 not in calls
    c,s,call,state,run,writes,calls=setup(b'needle',editing=b'prefix')
    original_io=c.port_read;polled=[]
    def interrupt(port):
        if c.c==11:polled.append(11);return 255
        if c.c==1:polled.append(1);return ord('x')
        return original_io(port)
    c.port_read=interrupt
    assert run(b'nneedle')[0]==(True,ord('#')) and state()==(b'prefix',6)
    assert polled==[11,1] and not calls
    # DRI discards the whole missed batch, retaining no search overlap.
    source=b'x'*510+b'A\nB\n'
    c,s,call,state,run,writes,calls=setup(source,execution_limit=1000000)
    assert run(b'nA\nB')[0]==(True,ord('#')) and state()==(b'',0)
    assert call('EF_DRAIN')==(False,0) and b''.join(writes).rstrip(b'\x1a')==source
    print('PASS: N source scanning, counts/EOF, global case, no-op counts, read errors and lossless save after scan')


if __name__=='__main__':main()
