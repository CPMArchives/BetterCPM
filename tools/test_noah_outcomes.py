#!/usr/bin/env python3
"""Final command outcomes on assembled NOAH, including useful partial work."""
from test_noah_write import machine
from test_usq_com import diskkey
from test_lbr import archive, entry, with_crcs


def tests(m):
    lib=diskkey(1,'TEST.LBR'); other=diskkey(1,'TWO.LBR')
    first=diskkey(3,'FIRST.DAT',3); second=diskkey(3,'SECOND.DAT',3)
    raw=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],b'A'*128+b'B'*128))
    def outcome(t,wanted):
        assert t.count('Outcome: ')==1 and 'Outcome: '+wanted+'.' in t,t
    t=m.run('/TEST TEST.LBR',{lib:raw});outcome(t,'success')
    assert 'completed 0001; no-match 0000; skipped 0000' in t,t
    t=m.run('/LIST TEST.LBR NONE.*',{lib:raw});outcome(t,'warning/no-work')
    assert 'completed 0000; no-match 0001; skipped 0000' in t,t
    t=m.run('/X TEST.LBR C3:',{lib:raw,first:b'old',second:b'old'},keys='NN')
    outcome(t,'warning/no-work');assert 'skipped 0001' in t,t
    t=m.run('/X /Y TEST.LBR C3:',{lib:raw},failures={'write':1})
    outcome(t,'warning/partial')
    assert first not in m.files and m.files[second]==b'B'*128,t
    assert 'failed 0001' in t and 'completed 0000' in t,t
    t=m.run('/X TEST.LBR C3:',{lib:raw},keys='R',failures={'write':1})
    outcome(t,'warning/partial');assert 'completed 0001' in t and 'failed 0000' in t,t
    t=m.run('/X *.LBR C3:',{lib:raw,other:raw},keys='A',failures={'write':1})
    outcome(t,'cancellation');assert 'unprocessed 0001' in t,t
    t=m.run('/X /Y TEST.LBR C3:',{lib:raw},failures={'write':1,'close_output':0})
    outcome(t,'failure');assert 'Close unconfirmed:' in t,t
    t=m.run('/TEST *.LBR',{lib:raw,other:b'bad'});outcome(t,'warning/partial')
    t=m.run('/TEST TEST.LBR',{lib:b'bad'});outcome(t,'failure')
    t=m.run('/LIST NONE.LBR',{});outcome(t,'warning/no-work')
    t=m.run('/BOGUS TEST.LBR',{});outcome(t,'failure')
    src=diskkey(2,'TEXT.DAT',7)
    t=m.run('/ADD TEST.LBR B7:TEXT.DAT',{src:b'A'*128});outcome(t,'success')
    t=m.run('/ADD /Y TEST.LBR B7:TEXT.DAT',{src:b'A'*128},failures={'read':1});outcome(t,'failure')
    t=m.run('/ADD /SQ /Y TEST.LBR B7:TEXT.DAT',{src:b'A'*128},failures={'read':1});outcome(t,'failure')
    t=m.run('/ADD TEST.LBR B7:TEXT.DAT',{src:b'A'*128},failures={'read':1},keys='R');outcome(t,'warning/partial')
    t=m.run('/ADD /Y TEST.LBR B[0,1]:TEXT.DAT',
            {diskkey(2,'TEXT.DAT',0):b'A'*128,diskkey(2,'TEXT.DAT',1):b'B'*128},failures={'open':2})
    outcome(t,'warning/partial')
    t=m.run('/SQ /Y B7:TEXT.DAT C3:',{src:b'A'*128},failures={'write':1});outcome(t,'failure')
    t=m.run('/SQ B7:TEXT.DAT C3:',{src:b'A'*128});outcome(t,'success')
    for tail in ('/HELP','/VER'):
        t=m.run(tail,{},supply_overlay=False);assert 'Outcome:' not in t,t
    print(f'PASS: {m.cases} final-outcome transactions')

if __name__=='__main__':tests(machine())
