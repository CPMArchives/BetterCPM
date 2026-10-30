#!/usr/bin/env python3
"""Candidate identities and final extraction counters, independent of attempts."""
from test_noah_write import machine
from test_usq_com import diskkey
from test_lbr import archive, entry, with_crcs
from test_lbr_write import members


def tests(m):
    m.instruction_budget=150000000
    src=diskkey(2,'TEXT.DAT',7);lib=diskkey(1,'NEW.LBR')
    inputs={src:b'A'*128}
    def counts(t,kind,completed,skipped,failed,unprocessed,accepted=None):
        action = 'added' if kind == 'ADD candidates' else 'extracted'
        word = 'file' if completed == 1 else 'files'
        assert f'{completed} {word} {action}.' in t,t
        for count,action in ((skipped,'skipped'),(failed,'failed'),(unprocessed,'unprocessed')):
            if count:
                word = 'file' if count == 1 else 'files'
                assert f'{count} {word} {action}.' in t,t
        assert [m.count32('NA_COUNTS', offset) for offset in (0,4,8,12)] == [completed,skipped,failed,unprocessed],t
        assert 'Accepted candidates' not in t and '(hex)' not in t,t
    add='ADD candidates';extract='Known members'
    t=m.run('/ADD NEW.LBR B7:TEXT.DAT',inputs);counts(t,add,1,0,0,0,1)
    t=m.run('/ADD NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1},keys='R');counts(t,add,1,0,0,0,1)
    t=m.run('/ADD /Y NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1});counts(t,add,0,0,1,0,0)
    t=m.run('/ADD NEW.LBR B7:TEXT.DAT',{**inputs,lib:with_crcs(archive([entry(b'TEXT    DAT')],b'O'*128))},keys='N');counts(t,add,0,1,0,0,0)
    t=m.run('/ADD NEW.LBR B7:TEXT.DAT',inputs,failures={'write':1},keys='R');counts(t,add,1,0,0,0,1)
    t=m.run('/ADD /Y NEW.LBR B7:TEXT.DAT',inputs,failures={'write':1});counts(t,add,0,0,0,1,0)
    old=with_crcs(archive([entry(b'OLD     DAT')],b'O'*128))
    t=m.run('/ADD /SQ /Y NEW.LBR B7:TEXT.DAT',{**inputs,lib:old},attributes={lib:1})
    counts(t,add,0,1,0,0,0);assert m.files[lib]==old,t
    two={**inputs,diskkey(2,'ZED.DAT',7):b'B'*128}
    t=m.run('/ADD NEW.LBR B7:*.DAT',two,failures={'read':1},keys='A');counts(t,add,0,0,1,1,0)
    for mode in ('/SQ','/CR'):
        t=m.run(f'/ADD {mode} /Y NEW.LBR B7:*.DAT',two,failures={'read':1});counts(t,add,1,0,1,0,1)
        assert len(members(m.files[lib]))==1,t
    same={diskkey(2,'TEXT.DAT',0):b'A'*128,diskkey(2,'TEXT.DAT',1):b'B'*128}
    for mode in ('','/SQ'):
        t=m.run(f'/ADD {mode} /Y NEW.LBR B[0,1]:TEXT.DAT',same);counts(t,add,1,1,0,0,2)
        assert 'Outcome: warning/partial.' in t,t
    five={diskkey(2,f'F{i}.DAT',7):bytes([65+i])*128 for i in range(5)}
    t=m.run('/ADD /Y NEW.LBR B7:*.DAT',five,failures={'open':4});counts(t,add,4,0,1,0,4)
    limit={diskkey(2,f'F{i:03}.DAT',7):b'A'*128 for i in range(512)}
    t=m.run('/ADD /Y NEW.LBR B7:*.DAT',limit,failures={'open':0});counts(t,add,0,0,512,0,0)
    one=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],b'A'*128+b'B'*128))
    second=with_crcs(archive([entry(b'THIRD   DAT',start=1)],b'C'*128))
    libs={diskkey(1,'ONE.LBR'):one,diskkey(1,'TWO.LBR'):second}
    t=m.run('/X /Y *.LBR C3:',libs);counts(t,extract,3,0,0,0)
    t=m.run('/X /Q /Y *.LBR C3:',libs,failures={'write':1});counts(t,extract,2,0,1,0)
    t=m.run('/X *.LBR C3:',libs,failures={'write':1},keys='R');counts(t,extract,3,0,0,0)
    t=m.run('/X *.LBR C3:',libs,failures={'write':1},keys='A');counts(t,extract,0,0,1,1)
    assert '1 file unprocessed.' in t and 'Outcome: cancellation.' in t,t
    print(f'PASS: {m.cases} member/candidate accounting transactions')

if __name__=='__main__':tests(machine())
