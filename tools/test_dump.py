#!/usr/bin/env python3
"""Differential DUMP byte-stream/BDOS tests against the retained DRI executable.

The BDOS fixture supplies record I/O and pending status; no production OS is
patched. Output, consumed records, FCB addressing and direct return are checked.
"""
from pathlib import Path
import hashlib
import json
from test_bios import Z80
from utility_versions import identities
from test_dump_enhanced import execute as enhanced_execute
ROOT = Path(__file__).resolve().parents[1]


def execute(image, payload=b'', tail='', pending_line=None, opened=True, read_error=None, drive=0):
    c = Z80(b'')
    c.mem[0x100:0x100+len(image)] = image
    c.mem[5:8] = b'\xd3\x00\xc9'  # OUT fixture port; RET through genuine caller stack.
    c.mem[0:3] = b'\xc3\xfe\xff'  # A warm boot must not be used.
    c.mem[0x5c:0x5c+36] = bytes(36)
    c.mem[0x5c] = drive
    c.mem[0x5d:0x68] = b'TEST    BIN'
    c.mem[0x7c] = 99
    data = tail.encode('ascii'); c.mem[0x80]=len(data);c.mem[0x81:0x81+len(data)]=data
    output = bytearray(); services=[]; record=0; checks=0; key=False
    def bdos(port, value):
        nonlocal record,checks,key
        fn=c.c;services.append(fn)
        if fn==2: output.append(c.e)
        elif fn==9:
            end=c.mem.index(36,c.de);output.extend(c.mem[c.de:end])
        elif fn==11:
            checks+=1;key=pending_line is not None and checks>=pending_line;c.a=255 if key else 0
        elif fn==15:
            assert c.de==0x5c and c.mem[0x7c]==0
            assert c.mem[0x5c]==drive
            c.a=0 if opened else 255
        elif fn==20:
            assert c.de==0x5c
            if read_error and record==read_error[0]: c.a=read_error[1]
            elif record*128>=len(payload): c.a=1
            else:
                chunk=payload[record*128:(record+1)*128];assert len(chunk)==128
                c.mem[0x80:0x100]=chunk;record+=1;c.a=0
        else: raise AssertionError(f'unexpected BDOS {fn}')
        # Only the documented A result survives this hostile service fixture.
        c.bc=0xA5A5;c.de=0x5A5A;c.hl=0x1234
    c.port_write=bdos
    sp=c.sp;c.run(0x100,limit=15000000)
    assert c.sp==sp, 'caller stack not restored'
    return dict(output=bytes(output),services=services,records=record,status_checks=checks,key_pending=key)


def main():
    ours=(ROOT/'build/utilities/DUMP.COM').read_bytes()
    dri=(ROOT/'third_party/dri-dump/DUMP.COM').read_bytes()
    count=0
    cases=[('empty',b'',{}),('one-record',bytes(range(128)),{}),
           ('all-bytes',bytes(range(256)),{}),('drive-B',b'\x1a'*128,dict(drive=2)),
           ('missing',b'',dict(opened=False)),('padding',b'HELLO'+b'\x1a'*123,{}),
           ('wrap',bytes(range(256))*257,{}),('abort-first',bytes(256),dict(pending_line=1)),
           ('abort-second',bytes(range(256)),dict(pending_line=2)),
           ('read-status-2',bytes(256),dict(read_error=(1,2))),
           ('read-status-255',bytes(256),dict(read_error=(0,255)))]
    for label,payload,kw in cases:
        b=execute(dri,payload,**kw)
        error=kw.get('read_error')
        r=enhanced_execute(payload,tail=('B:TEST.BIN' if kw.get('drive') else 'TEST.BIN')+' /BARE',
            opened=kw.get('opened',True), pending_bare=kw.get('pending_line'),
            error=(lambda rec,n:rec==error[0]) if error else None)
        a=dict(output=r['output'],services=r['services'],records=sum(1 for rec in r['reads'] if rec*128<len(payload) and not (error and rec==error[0])),
               status_checks=r['services'].count(11),key_pending=kw.get('pending_line') is not None)
        assert a['output']==b['output'] and a['records']==b['records'] and a['status_checks']==b['status_checks'],(label,a['output'][:160],b['output'][:160])
        if label=='one-record':assert a['output'].count(b'\r\n')==9
        if label=='wrap':assert b'\r\nFFF0' in a['output'] and a['output'].count(b'\r\n0000 ')==2
        if label.startswith('abort'):assert a['key_pending'] and 1 not in a['services']
        count+=1
    version,build=identities()['DUMP']
    expected=(f'DUMP {version} ({build:03d})\r\n  - - -\r\n | BetterCP/M Utilities\r\n | Hexadecimal File Display\r\n').encode()
    for tail in ['/VER',' /ver  ','/VeR']:
        a=enhanced_execute(tail=tail);assert a['output']==expected and a['services']==[9];count+=1
    for tail in ['/VER x','x /VER','/VER /VER']:
        a=enhanced_execute(tail=tail);assert a['output']==expected and a['services']==[9];count+=1
    for tail in ['/VERIFY','/VERBOSE']:
        a=enhanced_execute(tail=tail,opened=False);assert 15 not in a['services'] and b'DUMP:' in a['output'];count+=1
    report={'status':'PASS','cases':count,'dri_sha256':hashlib.sha256(dri).hexdigest(),'dump_sha256':hashlib.sha256(ours).hexdigest(),'scope':'Actual compiled programs; synthetic public BDOS record/status fixture. Direct RET/stack balance, output and pending character checked; not live platform qualification.'}
    (ROOT/'build/utilities/dump-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {count} DUMP reference/EOF/wrap/interruption/return/version cases')


if __name__=='__main__':main()
