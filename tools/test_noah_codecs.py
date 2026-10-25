#!/usr/bin/env python3
"""Bounded production overlay and NOAH codec transaction acceptance."""
from test_noah_write import machine
from test_usq_com import diskkey,padded
from test_usq import squeeze
from test_cr import reference
from test_sq import host_decode
from test_uncr import decode
from test_lbr import archive,entry,with_crcs
from test_lbr_write import members,check_crc


def tests(m):
    m.instruction_budget=150000000
    src=diskkey(2,'BINARY.DAT',7);original=bytes(range(256))*2
    for op,ext in [('SQ','DQT'),('CR','DZT')]:
        out=diskkey(3,'BINARY.'+ext,3)
        text=m.run(f'/{op} B7:BINARY.DAT C3:',{src:original},user=7)
        assert 'published' in text and m.files[src]==original,text
        compressed=m.files[out]
        if op=='SQ':assert host_decode(compressed,record_padding=True)[1]==original
        else:assert decode(compressed)[0]==original
        text=m.run(f'/EXPAND C3:BINARY.{ext} D4:',{out:compressed},user=7)
        assert m.files[diskkey(4,'BINARY.DAT',4)]==original and not m.opened,text
        for ceiling in (0xc501,0xca01):
            text=m.run(f'/{op} B7:BINARY.DAT C3:',{src:original},user=7,tpa=ceiling)
            assert 'published' in text,text
        lib=diskkey(1,'TEST.LBR')
        text=m.run(f'/ADD /{op} /Y A0:TEST.LBR B7:BINARY.DAT',{src:original},user=7)
        assert 'published' in text,text
        raw=m.files[lib];check_crc(raw);row=members(raw)[0]
        assert row[1:12]==('BINARY  '+ext).encode() and 0<=row[26]<128
        text=m.run('/X /EXPAND A0:TEST.LBR C3:',{lib:raw},user=7)
        assert m.files[diskkey(3,'BINARY.DAT',3)]==original,text
        # Replacements use transformed stored names and retain the old member.
        text=m.run(f'/ADD /{op} /Y A0:TEST.LBR B7:BINARY.DAT',{lib:raw,src:b'A'*512},user=7)
        assert 'published' in text and [r[0] for r in members(m.files[lib])]==[254,0],text
    for wire in (squeeze(original,name=b'ORACLE.BIN'),reference(original,name=b'ORACLE.BIN')):
        text=m.run('/EXPAND B7:ODD.EXT C3:',{diskkey(2,'ODD.EXT',7):wire},user=7)
        assert m.files[diskkey(3,'ORACLE.BIN',3)]==original,text
    for data in (b'',b'plain\x1a\x00\xff'):
        text=m.run('/EXPAND B7:PLAIN.DAT C3:',{diskkey(2,'PLAIN.DAT',7):data},user=7)
        assert m.files[diskkey(3,'PLAIN.DAT',3)]==padded(data) and 'Not compressed' in text,text
        text=m.run('/EXPAND B7:PLAIN.DAT',{diskkey(2,'PLAIN.DAT',7):data},drive=2,user=7)
        assert not m.created and m.files[diskkey(2,'PLAIN.DAT',7)]==data,text
    for wire in (b'\x76\xfdunsupported',squeeze(original,name=b'B:EVIL.BIN'),squeeze(original,name=b'../BAD')):
        text=m.run('/EXPAND B7:ODD.BIN C3:',{diskkey(2,'ODD.BIN',7):wire},user=7)
        assert 'published' not in text and not m.created,text
    for tamper in (True,'append','truncate'):
        target=diskkey(3,'BINARY.DQT',3)
        text=m.run('/SQ /Y B7:BINARY.DAT C3:',{src:original,target:b'KEEP'},user=7,tamper=tamper)
        assert 'published' not in text and m.files[target]==b'KEEP',text
    for operation in ('read','write','make','rename','close_output'):
        target=diskkey(3,'BINARY.DQT',3)
        text=m.run('/SQ /Y B7:BINARY.DAT C3:',{src:original,target:b'KEEP'},user=7,failures={operation:1})
        assert 'published' not in text and m.files[target]==b'KEEP',text
    for tail in ('/SQ /CR B7:*.DAT','/SQ /EXPAND B7:*.DAT','/SQ /REMOVE A0:X.LBR *.*',
                 '/SQ /CAPACITY=4 B7:*.DAT','/CR B7:*.DAT C3:X.BIN','/COMPACT /EXPAND A0:X.LBR'):
        text=m.run(tail,{src:original},user=7)
        assert 'Usage:' in text and not m.created,text
    target=diskkey(3,'BINARY.DQT',3)
    text=m.run('/SQ /Y B7:BINARY.DAT C3:',{src:original,target:b'KEEP'},user=7,
               source_change=(src,6,b'X'*len(original)))
    assert 'published' not in text and m.files[target]==b'KEEP',text
    lib=diskkey(1,'TEST.LBR');old=with_crcs(archive([],b'',sectors=2))
    text=m.run('/ADD /SQ /Y A0:TEST.LBR B7:BINARY.DAT',{src:original,lib:old},user=7,
               writer_change=(src,b'X'*len(original)))
    assert 'published' not in text and m.files[lib]==old,text
    # One explicit expansion layer: a decoded compressed file stays compressed.
    inner=squeeze(b'layer two',name=b'FINAL.TXT')
    outer=squeeze(inner,name=b'INNER.TQT')
    text=m.run('/EXPAND B7:OUTER.BIN C3:',{diskkey(2,'OUTER.BIN',7):outer},user=7)
    assert m.files[diskkey(3,'INNER.TQT',3)]==padded(inner),text
    wire=squeeze(b'preserve stamped bytes',name=b'STAMPED.TXT')
    tail=-len(wire)%128
    stamped=bytearray(entry(b'STAMPED TQT',records=(len(wire)+127)//128,pad=tail))
    stamped[18]=1
    raw=with_crcs(archive([bytes(stamped)],wire+bytes([26])*tail))
    text=m.run('/X /EXPAND B7:STAMP.LBR C3:',{diskkey(2,'STAMP.LBR',7):raw},user=7)
    assert m.files[diskkey(3,'STAMPED.TXT',3)]==padded(b'preserve stamped bytes'),text
    assert 'timestamp' in text.lower() and 'Warnings' in text,text
    # Every load validates the entire companion before executing its code.
    ovl=m.overlay;key=diskkey(1,'NOAH.OVL')
    for bad in (ovl[:-128],ovl+bytes(128),bytes([0])+ovl[1:],ovl[:-1]+bytes([ovl[-1]^1])):
        text=m.run('/SQ B7:BINARY.DAT C3:',{src:original,key:bad},user=0)
        assert 'operation stopped' in text and not m.created,text
    text=m.run('/SQ B7:BINARY.DAT C3:',{src:original},supply_overlay=False)
    assert 'operation stopped' in text and not m.created,text
    for at in (2,4,5):
        target=diskkey(3,'BINARY.DQT',3)
        text=m.run('/SQ /Y B7:BINARY.DAT C3:',{src:original,target:b'KEEP'},user=7,overlay_change_at=at)
        assert 'operation stopped' in text and m.files[target]==b'KEEP' and not m.opened,text
        if at>=4:assert 'Temporary retained:' in text,text
    text=m.run('/SQ B7:BINARY.DAT C3:',{src:original,key:ovl},drive=2,user=7,supply_overlay=False)
    assert 'published' in text and m.drive==2 and m.user==7,text
    # No output may overwrite the resolved executable companion.
    wire=squeeze(original,name=b'NOAH.OVL')
    text=m.run('/EXPAND /Y B7:ODD.BIN A0:',{key:ovl,diskkey(2,'ODD.BIN',7):wire},user=0)
    assert m.files[key]==ovl and 'cannot be replaced' in text,text
    print(f'PASS: {m.cases} bounded codec/overlay transactions; stack {m.max_stack} bytes with BDOS intercepted')


if __name__=='__main__':tests(machine())
