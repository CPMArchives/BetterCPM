#!/usr/bin/env python3
"""Prove safe transaction restarts, trusted skips and preserved recovery state."""
from test_noah_write import machine
from test_usq_com import diskkey
from test_lbr import archive, entry, with_crcs
from test_lbr_write import members, check_crc
from test_sq import host_decode


def tests(m):
    m.instruction_budget=150000000
    source=diskkey(2,'TEXT.DAT',7);data=bytes(range(128))
    encoded=diskkey(3,'TEXT.DQT',3)
    text=m.run('/SQ B7:TEXT.DAT C3:',{source:data,encoded:b'OLD'},keys='YRY',failures={'write':1})
    assert host_decode(m.files[encoded],record_padding=True)[1]==data,text
    assert m.answers==list(b'YRY') and len(m.created)==2 and not m.opened,text
    assert all(not k[2].endswith(('.TMP','.BAK')) for k in m.files),text
    text=m.run('/SQ /Y B7:TEXT.DAT C3:',{source:data,encoded:b'OLD'},failures={'write':1})
    assert m.files[encoded]==b'OLD' and not m.answers and not m.opened,text

    lib=diskkey(1,'TEST.LBR');first=diskkey(3,'FIRST.DAT',3);second=diskkey(3,'SECOND.DAT',3)
    raw=with_crcs(archive([entry(b'FIRST   DAT',start=1),entry(b'SECOND  DAT',start=2)],b'A'*128+b'B'*128))
    text=m.run('/X TEST.LBR C3:',{lib:raw},keys='R',failures={'write':1})
    assert m.files[first]==b'A'*128 and m.files[second]==b'B'*128,text
    assert '2 files extracted.' in text and m.count32('NA_COUNTS',8)==0 and not m.opened,text
    assert len(m.created)==3 and len(m.renamed)==2,text
    for options,answer in (('','S'),('/Q','\r'),('/Y','')):
        text=m.run(f'/X {options} TEST.LBR C3:',{lib:raw},keys=answer,failures={'write':1})
        assert first not in m.files and m.files[second]==b'B'*128 and not m.opened,text
        assert '1 file failed.' in text and m.count32('NA_COUNTS',4)==0 and m.count32('NA_COUNTS',12)==0,text
        assert 'Skipped after failure.' in text,text
        if options=='/Y':assert not m.answers,text
    text=m.run('/X TEST.LBR C3:',{lib:raw},keys='A',failures={'write':1})
    assert first not in m.files and second not in m.files and 'cancelled' in text.lower(),text
    assert '1 file failed.' in text and '1 file unprocessed.' in text,text

    # Whole archive reconstruction must regenerate the same intended bytes.
    text=m.run('/ADD TEST.LBR B7:TEXT.DAT',{source:data})
    expected=m.files[lib]
    text=m.run('/ADD TEST.LBR B7:TEXT.DAT',{source:data},keys='R',failures={'write':1})
    assert 'A0:TEST.LBR' in text and m.files[lib]==expected and m.answers==[ord('R')] and len(m.created)==2 and not m.opened,text
    check_crc(m.files[lib])
    # Compressed candidate stages can restart before aggregate ownership begins.
    text=m.run('/ADD /SQ TEST.LBR B7:TEXT.DAT',{source:data},keys='R',failures={'write':1})
    assert len(members(m.files[lib]))==1 and m.answers==[ord('R')] and not m.opened,text

    # A sticky archive reader error never gets reset to SELECTED just to skip.
    m.run('/X TEST.LBR C3:',{lib:raw})
    make=next(i for i,(fn,_) in enumerate(m.events) if fn==22)
    read=sum(fn==33 for fn,_ in m.events[:make])+1
    text=m.run('/X TEST.LBR C3:',{lib:raw},keys='R',failures={'read':read})
    assert not m.answers and first not in m.files and second not in m.files,text
    assert '1 file unprocessed.' in text,text
    # Retained or unconfirmed names/handles prevent restart and continuation.
    for failures,options in (({'write':1,'delete':1},{}),
                             ({'write':1},{'delete_keeps_on_success':True}),
                             ({'write':1,'close_output':0},{}),
                             ({'make':1},{'make_creates_on_failure':True,
                                           'physical_extents':{diskkey(3,'FIRST00.TMP',3):[2]}})):
        text=m.run('/X TEST.LBR C3:',{lib:raw},keys='R',failures=failures,**options)
        assert not m.answers and first not in m.files and second not in m.files,text
        assert 'Temporary retained:' in text and any(k[2].endswith('.TMP') for k in m.files),text
        assert m.files[lib]==raw,text
    text=m.run('/X *.LBR C3:',{lib:raw,diskkey(1,'TWO.LBR'):raw},keys='R',
               failures={'write':1,'close_output':0})
    assert 'Close unconfirmed: C3:FIRST00.TMP' in text and 'Unprocessed operations: 1' in text and not m.answers,text
    # The publication boundary is never crossed again, even after rollback.
    text=m.run('/X TEST.LBR C3:',{lib:raw,first:b'OLD'},keys='YR',failures={'rename':2})
    assert m.files[first]==b'OLD' and m.answers==[ord('Y')] and second not in m.files,text
    assert 'Temporary retained:' in text,text
    # Do not advance a frozen batch over an archive input that failed to close.
    another=diskkey(1,'TWO.LBR')
    text=m.run('/TEST *.LBR',{lib:raw,another:raw},failures={'close_input':1})
    assert 'Unprocessed operations: 1' in text and not m.created,text
    print(f'PASS: {m.cases} staged failure/recovery transactions')


if __name__=='__main__':
    tests(machine())
