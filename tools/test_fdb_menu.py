"""Exercise the specified menu and every encoded message on the full Z80 core."""
from pathlib import Path
from unittest.mock import patch
import json
import re
from test_fdb_roundtrip import machine, diskkey, ROOT
from test_fdb_session import Session
from build_fdf_catalog import catalogue_payload
import fdb_menu_text


def main():
    original=fdb_menu_text.messages;captured=[]
    def capture(source):
        result=original(source);captured.extend((m[1],b) for m,b in result);return result
    work=ROOT/'build/fdb-menu-test';work.mkdir(exist_ok=True)
    with patch.object(fdb_menu_text,'messages',capture):m=machine(work,Session)
    listing=(work/'fdb.lst').read_text()
    symbol=lambda name:int(re.search(r'^([0-9a-f]{4}).*\b'+name+':',listing,re.M|re.I)[1],16)
    m.read_return=symbol('ASKREAD')
    files={diskkey(1,'DISK.FDB'):catalogue_payload()}
    def run(keys):
        m.keys=iter(keys);m.unexpected_prompt=False
        text=m.run('',files,drive=1)
        assert not m.unexpected_prompt,text
        assert m.files==files
        return text
    text=run('Q\r')
    header=re.search(r'FDB 1\.01 \([^)]+\)',text)[0]
    start=text.index(header);end=text.index('Your choice: [ ]',start)+len('Your choice: [ ]')
    menu=text[start:end]
    choices=re.findall(r'\[ ([A-Z]) \]',menu)
    assert choices==list('FN LDP ABCE IOS'.replace(' ','')),choices
    assert 'A0:DISK.FDB' in menu and 'Entries: 108' in menu and 'Unmodified' in menu
    assert 'or Q' in menu and 'BREAK (^C)' in menu
    assert len(menu.split('\r\n'))+1<=23
    run('\x03')
    run('N\rQ\r')
    dirty=run('B\r\rMMI012\rG\r1\rQ\rQ\rC\rE\rQ\r\x03D\r')
    assert 'Editor pending:' in dirty and 'Editor pending: S Save' in dirty,dirty[-2200:]
    # Check every selected fixed message against its unencoded source bytes.
    # Also check PUTS's pointer/register contract and private stack budget.
    for name,expected in captured:
        pointer=symbol(name)
        m.reg['SP'].value=symbol('STACKTOP');m.reg['H'].value=pointer>>8;m.reg['L'].value=pointer&255
        m.reg['B'].value=0x12;m.reg['C'].value=0x34;m.reg['D'].value=0x45;m.reg['E'].value=0x67
        m.console='';m.exception=None
        assert m.lib.test_run(symbol('PUTS'),1000000)>=0,name
        assert m.exception is None,(name,m.exception)
        assert m.console.encode('ascii')==expected,name
        assert (m.reg['B'].value<<8|m.reg['C'].value)==0x1234 and (m.reg['D'].value<<8|m.reg['E'].value)==0x4567,name
        assert m.mem[m.reg['H'].value<<8|m.reg['L'].value]==0,name
        assert m.reg['SP'].value==symbol('STACKTOP'),name
    assert m.stack_used<128,m.stack_used
    (work/'menu.txt').write_text(menu.replace('\r\n','\n')+'\n')
    (work/'results.json').write_text(json.dumps({'status':'PASS','message_cases':len(captured),'menu_rows_with_input':len(menu.split('\r\n'))+1,'max_width':m.max_console_width,'stack_used':m.stack_used},indent=2)+'\n')
    print('PASS grouped menu, Q/BREAK, pending editor Cancel/Resume/Discard,',len(captured),'lossless messages; stack',m.stack_used)


if __name__=='__main__':main()
