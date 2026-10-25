#!/usr/bin/env python3
"""Quiet must change presentation without changing decisions or file outcomes."""
from test_noah_write import machine
from test_usq_com import diskkey, padded
from test_lbr import archive, entry, with_crcs


def tests(m):
    m.instruction_budget=150000000
    source=diskkey(2,'TEXT.DAT',7);lib=diskkey(1,'TEST.LBR')
    target=diskkey(3,'TEXT.DAT',3);data=b'preserve\x00\x1a\xff'*8
    raw=with_crcs(archive([entry(b'TEXT    DAT')],padded(data)))
    inputs={source:data,lib:raw}
    commands=[('/LIST TEST.LBR',''),('/TEST TEST.LBR',''),
              ('/X TEST.LBR C3:',': extracted and verified.'),
              ('/SQ B7:TEXT.DAT C3:','verified codec output published'),
              ('/CR B7:TEXT.DAT C3:','verified codec output published'),
              ('/EXPAND B7:TEXT.DAT C3:','Not compressed; copying'),
              ('/ADD /Y TEST.LBR B7:TEXT.DAT','LBR update verified and published'),
              ('/ADD /SQ /Y TEST.LBR B7:TEXT.DAT',' -> stored member '),
              ('/REMOVE /Y TEST.LBR TEXT.DAT','LBR update verified and published')]
    for command,progress in commands:
        normal=m.run(command,inputs)
        outcome=(dict(m.files),dict(m.attrs),list(m.created),list(m.renamed),list(m.deleted))
        quiet=m.run('/q /Q '+command,inputs)
        assert outcome==(dict(m.files),dict(m.attrs),list(m.created),list(m.renamed),list(m.deleted)),(command,quiet)
        if progress:assert progress in normal and progress not in quiet,(command,normal,quiet)
        else:assert quiet==normal,(command,normal,quiet)
        assert ('selected ' in quiet or 'Accepted source versions' in quiet),quiet
        if command.startswith('/REMOVE'):assert 'TEXT    .DAT' in quiet,quiet
    # Quiet does not imply Yes, suppress authorization, or consume different keys.
    for answer in ('Y','N'):
        text=m.run('/X /Q TEST.LBR C3:',{lib:raw,target:b'OLD'},keys=answer)
        assert 'Replace? Y/N/A/C [N]:' in text,text
        assert m.files[target]==(padded(data) if answer=='Y' else b'OLD'),text
        if answer=='N':assert 'declined' in text and 'skipped: 00000001' in text,text
    text=m.run('/X /Q /Y /R TEST.LBR C3:',{lib:raw,target:b'OLD'},attributes={target:1})
    assert 'protected; skipped' in text and not m.answers and m.files[target]==b'OLD',text
    text=m.run('/SQ /Q /Y B7:TEXT.DAT C3:',{source:data},failures={'write':1})
    assert 'B7:TEXT.DAT' in text and 'codec operation failed' in text and 'failed 0001' in text,text
    # A rollback failure retains exact recovery names even with quiet enabled.
    text=m.run('/X /Q TEST.LBR C3:',{lib:raw,target:b'OLD'},keys='Y',failures={'rename':(2,3)})
    assert 'BAK' in text and 'TMP' in text and 'retained' in text.lower(),text
    # Explicit compression growth and timestamp capability warnings remain visible.
    text=m.run('/SQ /Q B7:TEXT.DAT C3:',{source:bytes(range(128))})
    assert 'explicit compression increased' in text,text
    row=bytearray(entry(b'TEXT    DAT'));row[18]=1
    stamped=with_crcs(archive([bytes(row)],padded(data)))
    text=m.run('/X /Q TEST.LBR C3:',{lib:stamped})
    assert 'Timestamp not restored' in text and 'Warnings' in text,text
    # Failed source identities must remain visible; preserve the existing outcome.
    m.run('/ADD NEW.LBR B7:TEXT.DAT',{source:data},failures={'read':1})
    normal_files=dict(m.files)
    text=m.run('/ADD /Q NEW.LBR B7:TEXT.DAT',{source:data},failures={'read':1})
    assert 'B7:TEXT' in text and 'Source preflight failed.' in text and m.files==normal_files,text
    text=m.run('/ADD /Q /Y TEST.LBR TEST.LBR',{lib:raw})
    assert 'A0:TEST' in text and 'target excluded' in text and not m.created,text
    # Query precedence still requires no companion, regardless of quiet tokens.
    text=m.run('/Q /VER /BAD',{},supply_overlay=False)
    assert 'NOAH 1.0' in text and not m.overlay_events,text
    for command in ('/QQ TEST.LBR','/Q=Y TEST.LBR'):
        text=m.run(command,inputs)
        assert 'Usage:' in text and not m.created,text
    print(f'PASS: {m.cases} quiet presentation/decision transactions')


if __name__=='__main__':
    tests(machine())
