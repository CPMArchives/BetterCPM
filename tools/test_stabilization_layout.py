#!/usr/bin/env python3
"""Execute the agreed narrow CRC layout, COPY help and NOAH presentation."""
from pathlib import Path
from test_crc import execute, name83
from test_utility_versions import runner, output
from test_noah_write import machine
from test_usq_com import diskkey

ROOT = Path(__file__).resolve().parents[1]

def main():
    data = b'123456789' + b'\x1a' * 119
    files = {(2, 7, 'STARTUP.SUB'): data}
    defaults = ['CRCK', 'CRCK5', 'CHEK', 'CRC32', 'SUM8', 'SUM16', 'KERM6', 'KERM12']
    for algorithms in (defaults, ['SUM16'], ['KERM12','SUM8','CRCK'], ['CRC32','CHEK']):
        switches = '' if algorithms == defaults else ' '.join('/'+a for a in algorithms)
        result = execute(files, '/40 /FILE=CRC.LST '+switches)
        lines = result['text'].splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith('NAME     EXT'))
        groups = [lines[start+i*4:start+i*4+3] for i in range((len(algorithms)+1)//2)]
        for index, group in enumerate(groups):
            assert len(group)==3, result['text']
            for column, algorithm in enumerate(algorithms[index*2:index*2+2]):
                position = 19+10*column
                assert group[0][position:position+8].strip()==algorithm,group
                assert group[1][position:position+8]=='--------',group
                assert group[2][position:position+8].strip(),group
            assert max(map(len,group))<=40,group
            if index: assert all(line[:19].isspace() for line in group),group
        assert result['text'].count('STARTUP  SUB')==1,result['text']
        wide = execute(files, '/FILE=CRC.LST '+switches)
        assert result['files'][2,7,name83('CRC.LST')]==wide['files'][2,7,name83('CRC.LST')]
    image=(ROOT/'build/utilities/COPY.COM').read_bytes()
    for tail in ('/HELP','/VER /HELP /BOGUS','\t/help\t','/HELP /VER'):
        cpu=runner(image);raw=tail.encode();cpu.mem[128]=len(raw);cpu.mem[129:129+len(raw)]=raw
        cpu.run(256,limit=100000)
        text=output(cpu)
        assert 'Usage: COPY' in text and 'Options:' in text,text
        for option in ('/O','/S','/B','/V','/BACKUP','/HELP','/VER'): assert option in text,text
        assert max(map(len,text.splitlines()))<=80,text
    m=machine();src=diskkey(2,'STARTUP.SUB',7);lib=diskkey(1,'TEST.LBR')
    normal=m.run('/ADD TEST.LBR B7:STARTUP.SUB',{src:data});expected=dict(m.files)
    alias=m.run('/A TEST.LBR B7:STARTUP.SUB',{src:data})
    assert m.files==expected and normal==alias and '1 file added.' in alias,alias
    raw=m.files[lib]
    listing=m.run('/LIST TEST.LBR',{lib:raw})
    assert listing==m.run('/L TEST.LBR',{lib:raw}),listing
    assert 'STARTUP.SUB  128' in listing and '1 file listed.' in listing,listing
    tested=m.run('/TEST TEST.LBR',{lib:raw})
    assert 'STARTUP.SUB: CRC OK' in tested and '1 file checked' in tested,tested
    for report in (normal,listing,tested):
        assert not any(word in report for word in ('(hex)','Accepted candidates','Disposition','Recovery artifacts','Outcome: success')),report
    for value in (0,1,9,10,128,65535,65536,1000000,0xffffffff):
        address=m.symbols['NX_BUFFER']
        m.mem[address:address+4]=value.to_bytes(4,'little')
        m.reg['H'].value,m.reg['L'].value=address>>8,address&255
        m.console=''
        m.library_call('NH_PRINT_COUNT')
        assert m.console==str(value),(value,m.console)
    for tail in ('/H','/VER /H /BOGUS','/HELP /VER','/VER /HELP'):
        text=m.run(tail,{},supply_overlay=False)
        assert 'Usage:' in text and '/LIST /L' in text and not m.overlay_events,text
    for bad in ('/HH','/LX TEST.LBR','/AA TEST.LBR B7:STARTUP.SUB','/QUIETX /LIST TEST.LBR','/V'):
        text=m.run(bad,{lib:raw,src:data})
        assert 'Usage:' in text and not m.created and not m.renamed,text
    text=m.run('/QUIET /X TEST.LBR C3:',{lib:raw})
    assert '1 file extracted.' in text and m.files[diskkey(3,'STARTUP.SUB',3)]==data,text
    for keys in ('??N','?C'):
        text=m.run('/QUIET /X TEST.LBR C3:',{lib:raw,diskkey(3,'STARTUP.SUB',3):b'OLD'},keys=keys)
        assert 'Y Yes, N No, A All, C Cancel, ? Help' in text,text
        assert m.files[diskkey(3,'STARTUP.SUB',3)]==b'OLD',text
    print('PASS: grouped CRC console/saved rows, COPY help, NOAH aliases/quiet/presentation')

if __name__=='__main__':main()
