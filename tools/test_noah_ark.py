#!/usr/bin/env python3
"""Bounded production ARK dispatch, integrity and safe extraction qualification."""
from test_noah_write import machine
from test_ark import member
from test_usq_com import diskkey,padded
from test_lbr import archive,entry,with_crcs


def fixtures():
    from test_noah_ark_lzw import lzw
    return {
        'STORED.ARC':member(b'old',1,b'OLD.TXT')+member(b'\0'*129,2,b'ZERO.BIN')+b'\x1a\0',
        'MIXED.ARK':member(b'hello',2,b'FIRST.TXT')+lzw(b'packed data',8,b'PACKED.TXT')+member(b'last',1,b'LAST.TXT')+b'\x1a\0',
        'BAD.ARC':member(b'bad',crc=0)+b'\x1a\0',
        'DUP.ARC':member(b'a',name=b'SAME.TXT')+member(b'b',name=b'same.txt')+b'\x1a\0',
        'TAIL.ARC':member(b'tail',name=b'TAIL.TXT')+b'\x1a\0opaque',
        'EMPTY.ARC':b'\x1a\0',
    }


def tests(m):
    m.instruction_budget=150000000
    f=fixtures();lib=diskkey(1,'STORED.ARC');out=diskkey(3,'ZERO.BIN',3)
    for ceiling in (0xc501,0xca01):
        for op in ('/LIST','/TEST','/X /Y'):
            t=m.run(f'{op} STORED.ARC C3:*.*' if '/X' in op else f'{op} STORED.ARC',{lib:f['STORED.ARC']},tpa=ceiling)
            assert 'Outcome: success.' in t,t
            if '/LIST' in op:assert 'CRC verified.' not in t and not m.created,t
            else:assert 'verified 00000002; unavailable/ambiguous: 00000000' in t,t
            if '/X' in op:assert m.files[out]==padded(b'\0'*129) and m.files[diskkey(3,'OLD.TXT',3)]==padded(b'old'),t
            assert m.files[lib]==f['STORED.ARC'] and not m.opened,t
    mixed=diskkey(1,'MIXED.ARK')
    for op in ('/LIST','/TEST','/X /Y'):
        t=m.run(op+' MIXED.ARK',{mixed:f['MIXED.ARK']})
        assert 'unsupported' not in t and 'Outcome: success.' in t,t
        if '/X' in op:
            assert m.files[diskkey(1,'LAST.TXT')]==padded(b'last') and m.files[diskkey(1,'PACKED.TXT')]==padded(b'packed data'),t
        if '/LIST' not in op:assert 'verified 00000003; unavailable/ambiguous: 00000000' in t,t
    for name in ('BAD.ARC','DUP.ARC'):
        for op in ('/TEST','/X /Y'):
            t=m.run(op+' '+name,{diskkey(1,name):f[name]})
            assert 'Outcome: failure.' in t and not m.created,t
    t=m.run('/X /Y DUP.ARC NOFILE.*',{diskkey(1,'DUP.ARC'):f['DUP.ARC']})
    assert 'Archive/read error 09' in t and not m.created,t
    for op in ('/LIST','/TEST','/X /Y'):
        t=m.run(op+' TAIL.ARC',{diskkey(1,'TAIL.ARC'):f['TAIL.ARC']})
        assert 'opaque trailer: unvalidated' in t and 'Outcome: warning/partial.' in t,t
    t=m.run('/X /Y EMPTY.ARC',{diskkey(1,'EMPTY.ARC'):f['EMPTY.ARC']})
    assert 'No members matched' in t and not m.created,t
    dated=bytearray(member(b'date',name=b'DATE.TXT')+b'\x1a\0');dated[19:23]=b'\x01\x21\x00\x00'
    t=m.run('/X /Y DATE.ARC',{diskkey(1,'DATE.ARC'):bytes(dated)})
    assert 'ARK DOS timestamp not restored' in t and 'Outcome: warning/partial.' in t,t
    # Signature dispatch, mixed frozen queue and archive owner user, not extension.
    lbr=with_crcs(archive([entry(b'LBR     DAT')],b'L'*128))
    t=m.run('/X /Y B7:*.DAT C3:',{diskkey(2,'ARC.DAT',7):f['STORED.ARC'],diskkey(2,'LBR.DAT',7):lbr})
    assert m.files[out]==padded(b'\0'*129) and m.files[diskkey(3,'LBR.DAT',3)]==b'L'*128,t
    # /EXPAND does not recursively decode an ARC stored member's CP/M stream.
    from test_usq import squeeze
    inner=squeeze(b'inner',name=b'INNER.TXT')
    t=m.run('/X /EXPAND /Y ONE.ARC',{diskkey(1,'ONE.ARC'):member(inner,name=b'INNER.TQT')+b'\x1a\0'})
    assert m.files[diskkey(1,'INNER.TQT')]==padded(inner) and diskkey(1,'INNER.TXT') not in m.files,t
    for failures in ({'write':1},{'rename':1},{'close_output':0}):
        t=m.run('/X /Y STORED.ARC C3:ZERO.BIN',{lib:f['STORED.ARC'],out:b'ORIGINAL'},failures=failures)
        assert m.files[out]==b'ORIGINAL',t
        assert m.files[lib]==f['STORED.ARC'],t
    for op in ('/REMOVE /Y','/COMPACT /Y','/ADD /Y'):
        tail=op+' STORED.ARC'+(' B:NEW.TXT' if '/ADD' in op else ' *.*' if '/REMOVE' in op else '')
        t=m.run(tail,{lib:f['STORED.ARC'],diskkey(2,'NEW.TXT'):b'new'})
        assert 'verified and published' in t and not m.opened,t
    t=m.run('/X /Y STORED.ARC',{lib:f['STORED.ARC']},overlay_change_at=2)
    assert 'operation stopped' in t and not m.created,t
    t=m.run('/X /Y STORED.ARC',{lib:f['STORED.ARC']},cancel_poll=8)
    assert 'cancel' in t.lower() and not m.created,t
    t=m.run('/TEST STORED.ARC',{lib:f['STORED.ARC']},tpa=m.image.layout['required_ceilings'][0]-1)
    assert 'Insufficient transient memory' in t and not m.opened,t
    print(f'PASS: {m.cases} ARK production transactions; stack {m.max_stack} bytes')

def historical(m):
    import hashlib,json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    pins=json.loads((root/'tests/fixtures/noah/references.json').read_text())['artifacts']
    m.instruction_budget=700000000
    for name in ('crc32a.arc','de-lbr.arc','nulu15.arc'):
        raw=(root/'build/noah-proof/references'/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pins[name]['sha256']
        source=diskkey(1,'HIST.ARC')
        text=m.run('/LIST HIST.ARC',{source:raw})
        assert 'unsupported' not in text and 'Outcome: failure.' not in text and not m.created,text
        text=m.run('/TEST HIST.ARC',{source:raw})
        assert 'unsupported' not in text and 'Outcome: failure.' not in text and not m.created,text
        text=m.run('/X /Y HIST.ARC',{source:raw})
        assert 'unsupported' not in text and 'Outcome: failure.' not in text,text
        for output in (root/'build/noah-proof/references'/('decoded-'+name)).iterdir():
            dest='.'.join(output.name.split('.')[2:]).upper()
            assert m.files[diskkey(1,dest)]==padded(output.read_bytes()),(name,dest,text)
        assert m.files[source]==raw,text
        print('PASS: production historical LIST/TEST/EXTRACT',name)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--historical',action='store_true',help='Also exercise pinned cached historical archives')
    a=p.parse_args();m=machine();tests(m)
    if a.historical:historical(m)

