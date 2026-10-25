#!/usr/bin/env python3
"""Observed audit coverage and distinct reported recovery names, not all-pass claims."""
from test_noah_write import machine
from test_usq_com import diskkey
from test_lbr import archive,entry,with_crcs
from test_usq import squeeze


def tests(m):
    m.instruction_budget=150000000
    lib=diskkey(1,'ONE.LBR');other=diskkey(1,'TWO.LBR')
    first=diskkey(3,'FIRST.DAT',3);second=diskkey(3,'SECOND.DAT',3)
    raw=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],b'A'*128+b'B'*128))
    missing=archive([entry(b'THIRD   DAT')],b'C'*128)
    def recovery(t,n):assert f'Recovery artifacts reported (hex): {n:08X}' in t,t
    t=m.run('/Q /LIST *.LBR',{lib:raw,other:missing})
    assert 'Listed members (hex): 00000003' in t and 'LIST: contents not tested.' in t,t
    assert 'Known CRC regions' not in t,t
    recovery(t,0)
    t=m.run('/Q /TEST *.LBR',{lib:raw,other:missing})
    assert 'Listed members (hex): 00000003' in t,t
    assert 'Known CRC regions (hex): verified 00000003; unavailable/ambiguous: 00000002' in t,t
    assert 'Outcome: warning/partial.' in t,t
    t=m.run('/TEST ONE.LBR FIRST.*',{lib:raw})
    assert 'Known CRC regions (hex): verified 00000002; unavailable/ambiguous: 00000000' in t,t
    assert t.count('Members not selected (hex): 00000001')==2,t
    corrupt=bytearray(raw);corrupt[256]^=1
    t=m.run('/TEST ONE.LBR',{lib:bytes(corrupt)})
    assert 'Known CRC regions (hex): verified 00000002; unavailable/ambiguous: 00000000' in t,t
    assert 'Listed members (hex): 00000000' in t and 'Outcome: failure.' in t,t
    t=m.run('/X /Q /Y *.LBR C3:',{lib:raw,other:missing})
    assert 'Known CRC regions (hex): verified 00000003; unavailable/ambiguous: 00000002' in t,t
    assert m.files[first]==b'A'*128 and m.files[second]==b'B'*128,t
    for failures in ({'write':1,'delete':1},{'write':1,'close_output':0}):
        t=m.run('/X /Q /Y ONE.LBR C3:',{lib:raw},failures=failures)
        recovery(t,1);assert any(k[2].endswith('.TMP') for k in m.files),t
    t=m.run('/X /Q ONE.LBR C3:',{lib:raw,first:b'OLD'},keys='Y',failures={'rename':(2,3)})
    recovery(t,2);assert any(k[2].endswith('.BAK') for k in m.files),t
    t=m.run('/X /Q /Y ONE.LBR C3:',{lib:raw,first:b'OLD'},failures={'delete':1})
    recovery(t,1);assert m.files[first]==b'A'*128 and 'Outcome: warning/partial.' in t,t
    t=m.run('/X /Q /Y ONE.LBR C3:',{lib:raw,first:b'OLD',second:b'OLD'},failures={'delete':(1,2)})
    recovery(t,2)
    t=m.run('/X /Q /Y ONE.LBR C3:',{lib:raw},failures={'write':1})
    recovery(t,0);assert not any(k[2].endswith(('.TMP','.BAK')) for k in m.files),t
    payload=b'inner member data';wire=squeeze(payload,name=b'INNER.DAT');pad=-len(wire)%128
    inner=with_crcs(archive([entry(b'INNER   DQT',records=(len(wire)+127)//128,pad=pad)],wire+bytes([26])*pad))
    t=m.run('/X /EXPAND /Q /Y ONE.LBR C3:',{lib:inner},failures={'delete':1})
    recovery(t,1);assert m.files[diskkey(3,'INNER.DAT',3)].startswith(payload),t
    src=diskkey(2,'TEXT.DAT',7)
    t=m.run('/ADD /SQ /Q /Y NEW.LBR B7:TEXT.DAT',{src:b'A'*128},failures={'delete':2})
    recovery(t,1);assert diskkey(1,'NEW.LBR') in m.files and 'Outcome: warning/partial.' in t,t
    for query in ('/VER','/HELP'):
        t=m.run(query,{},supply_overlay=False)
        assert 'Recovery artifacts reported' not in t and 'Known CRC regions' not in t,t
    print(f'PASS: {m.cases} coverage/recovery transactions')

if __name__=='__main__':tests(machine())
