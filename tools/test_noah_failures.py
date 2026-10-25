#!/usr/bin/env python3
"""Safe source decisions: no duplicated output, preserved versions and bounds."""
from test_noah_write import machine
from test_usq_com import diskkey, padded
from test_lbr import archive, entry, with_crcs
from test_lbr_write import members
from test_sq import host_decode


def tests(m):
    m.instruction_budget=150000000
    source=diskkey(2,'TEXT.DAT',7);new=diskkey(1,'NEW.LBR')
    data=bytes(range(128));inputs={source:data}
    # Retry reopens/rechecks the source once and accepts one plan/payload.
    text=m.run('/ADD NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1},keys='R')
    assert 'Retry/Skip/Abort?' in text and m.answers==[ord('R')] and 'published' in text,text
    raw=m.files[new];assert len(members(raw))==1 and raw[256:]==data,text
    # Skip is the default. No implicit directory growth creates an empty file.
    for options,answer in (('','S'),('','\r'),('/Q','s'),('/COMPACT','S'),('/Y','')):
        text=m.run(f'/ADD {options} NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1},keys=answer)
        assert new not in m.files and not m.created and not m.renamed and not m.opened,text
        assert 'unchanged' in text,text
        assert bool(m.answers)==('/Y' not in options),text
    # Explicit valid capacity is still an intentional change; invalid capacity
    # must fail instead of being hidden by the no-accepted-source shortcut.
    text=m.run('/ADD /Y /CAPACITY=1 NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1})
    assert new in m.files and not members(m.files[new]),text
    text=m.run('/ADD /Y /CAPACITY=262140 NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1})
    assert new not in m.files and not m.created,text
    # Failure of a replacement preserves the original accepted version.
    old=with_crcs(archive([entry(b'TEXT    DAT')],b'O'*128))
    # Make only the writer's source callback fail, after old-archive preflight.
    text=m.run('/ADD /Y NEW.LBR B7:TEXT.DAT',{**inputs,new:old},failures={'open':2})
    assert m.files[new]==old and not m.created,text
    # A later same-name source failure cannot displace this invocation's
    # earlier accepted version, either.
    original=with_crcs(archive([entry(b'ORIGINALBIN')],b'O'*128))
    same={diskkey(2,'TEXT.DAT',0):b'A'*128,diskkey(2,'TEXT.DAT',1):b'B'*128}
    text=m.run('/ADD /Y NEW.LBR B[0,1]:TEXT.DAT',{new:original,**same},failures={'open':3})
    rows=members(m.files[new]);active=[r for r in rows if r[0]==0 and r[1:12]==b'TEXT    DAT']
    assert len(active)==1,text
    at=int.from_bytes(active[0][12:14],'little')*128
    assert m.files[new][at:at+128]==b'A'*128 and not m.opened,text
    # Abort and ESC stop before later sources and do not publish partial work.
    second=diskkey(2,'ZED.DAT',7)
    for answer in ('A','\x1b','\x03'):
        text=m.run('/ADD NEW.LBR B7:*.DAT',{**inputs,second:b'NEXT'},failures={'read':1},keys=answer)
        assert 'Cancelled' in text and new not in m.files and not m.created,text
    # A retry that fails again returns to the choice; there is no automatic loop.
    text=m.run('/ADD NEW.LBR B7:TEXT.DAT',inputs,failures={'read':0},keys='RS')
    assert text.count('Retry/Skip/Abort?')==2 and new not in m.files,text
    # Standalone codec preflight retries restart without prior stages.
    target=diskkey(3,'TEXT.DQT',3)
    text=m.run('/SQ B7:TEXT.DAT C3:',inputs,failures={'read':1},keys='R')
    assert m.answers==[ord('R')] and host_decode(m.files[target],record_padding=True)[1]==data,text
    assert len(m.created)==1 and not m.opened,text
    for options,answer in (('','S'),('/Q','A'),('/Y','')):
        text=m.run(f'/SQ {options} B7:TEXT.DAT C3:',inputs,failures={'read':1},keys=answer)
        assert target not in m.files and not m.created and not m.opened,text
        if '/Y' in options:assert not m.answers and 'Retry/Skip/Abort?' not in text,text
    # Compressed ADD preflight uses the same safe choice before its own stage.
    text=m.run('/ADD /SQ NEW.LBR B7:TEXT.DAT',inputs,failures={'read':1},keys='R')
    assert len(members(m.files[new]))==1 and m.answers==[ord('R')] and not m.opened,text
    # A retained candidate stage prevents retry over uncertain output.
    text=m.run('/SQ B7:TEXT.DAT C3:',inputs,failures={'write':1,'delete':1},keys='R')
    assert not m.answers and 'Retry/Skip/Abort?' not in text and target not in m.files,text
    # An input that cannot be confirmed closed must not be reset/reopened over.
    text=m.run('/SQ B7:*.DAT C3:',{**inputs,second:b'NEXT'},failures={'source_close':0},keys='R')
    assert not m.answers and 'source close uncertain; batch stopped' in text,text
    assert 'unprocessed 0001' in text and not m.created,text
    print(f'PASS: {m.cases} safe source-failure transactions')


if __name__=='__main__':
    tests(machine())
