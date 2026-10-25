#!/usr/bin/env python3
"""Actual logical command core against pinned WordStar and preserving-edit fixtures."""
import argparse
import ctypes as C
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_ted import ROOT, source
from test_ted_publisher import PROBE
from test_ted_workspace import Workspace, padded
from test_usq import SHIM


class Commands(Workspace):
    def callback(self, kind):
        if kind == 1:
            try:
                label = bytes(self.mem[self.reg['H'].value*256+self.reg['L'].value:])[:80].split(b'\0')[0]
                assert self.prompts, ('unexpected prompt', label)
                answer = self.prompts.pop(0)
                at = self.address('TE_FIELD')
                self.mem[at:at+len(answer)+1] = answer+b'\0'
                self.mem[self.address('TE_FIELDLEN')] = len(answer)
                self.mem[0x40] = 0xc9
                self.reg['PC'].value = 0x40
                self.reg['F'].value = 0
                self.reg['A'].value = 0
            except BaseException as error:
                self.exception = error
                self.reg['PC'].value = 0xffff
            return
        super().callback(kind)

    def bdos(self, fn, de):
        if fn == 6:
            return 0
        return super().bdos(fn, de)


    def start(self, text):
        self.begin()
        self.prompts = []
        self.lib.set_hooks(5, self.address('TE_PROMPT'), self.hook)
        assert self.load(padded(text)) == 0
        assert self.invoke('TC_INIT') == 0

    def position(self):
        return self.value('TC_POS', 3)

    def putpos(self, position):
        at = self.address('TC_POS')
        self.mem[at:at+3] = position.to_bytes(3, 'little')
        self.mem[self.address('TC_PREFVALID')] = 0
        self.mem[self.address('TC_VIRTUAL'):self.address('TC_VIRTUAL')+2] = bytes(2)

    def keys(self, data):
        for byte in data:
            self.reg['A'].value = byte
            failed = self.invoke('TC_KEY')
            if not failed:
                self.owned.add(self.fcbkey_with_user(self.address('TW_DOC')))
            assert not failed, (byte, self.value('TW_ERROR', 1), self.position())
        return self.value('TC_ACTION', 1)

    def logical(self):
        _, header, raw = self.workspace()
        data = raw[:int.from_bytes(header[12:15], 'little')]
        if self.value('WL_ACTIVE', 1):
            names = self.mapping['inline']
            start = self.value(names['WL_START'], 3)
            old = self.value(names['WL_OLDLEN'], 3)
            length = self.value(names['WL_LENGTH'], 3)
            at = self.address('WL_RAM')
            data = data[:start]+bytes(self.mem[at:at+length])+data[start+old:]
        return data


def tests(m):
    cases = []
    def field(name, value):
        at = m.address(name)
        m.mem[at:at+len(value)] = value
    def command(text):
        field('TE_FIELD', text+b'\0')
        m.mem[m.address('TE_FIELDLEN')] = len(text)
        return m.invoke('OP_DISPATCH')
    for suffix, action in (('S',1),('X',3),('Q',4),('R',5),('W',6),('C',18),('V',19),('Y',20)):
        for value in (ord(suffix),ord(suffix.lower()),ord(suffix)-64):
            m.start(b'unchanged')
            assert m.keys(bytes([11,value])) == action
            assert m.logical() == b'unchanged' and m.value('TC_PREFIX',1) == 0
            cases.append(f'approved prefix {value}')
    for suffix in b'BDKH':
        m.start(b'unchanged')
        assert m.keys(bytes([11,suffix])) == 255
        assert m.logical() == b'unchanged'
        cases.append(f'excluded prefix {suffix}')
    m.start(b'unchanged')
    m.keys(b'\x0b\x1b')
    assert m.value('TC_PREFIX',1) == 0
    assert m.value('TC_INSERT',1) == 0
    cases.append('cancel prefix and overwrite startup')
    for key,action in ((2,11),(14,11),(26,12),(31,13),(21,14),(10,17),(16,16)):
        m.start(b'unchanged')
        assert m.keys(bytes([key])) == action
        cases.append(f'TED retained or relocated action {key}')
    m.start(b'unchanged')
    m.keys(b'\x17')
    assert m.logical() == b'unchanged'
    m.keys(b'X')
    assert m.logical() == b'Xnchanged'
    cases.append('W no-op; ordinary typing overwrites')
    for key,initial,pos,expected,newpos in (
        (8,b'A\r\nB',3,b'AB',1),
        (7,b'A\r\nB',1,b'A\r\nB',1),
        (127,b'abc',1,b'ac',1),
        (8,b'abc',1,b' bc',0),
        (7,b'abc',1,b'ac',1),
        (25,b'abc\r\nnext',2,b'next',0),
        (13,b'ab\nnext',1,b'a\nb\nnext',2),
        (9,b'ab',1,b'a\tb',2),
        (20,b'aa.bb cc\r\nnext',2,b'aabb cc\r\nnext',2),
        (20,b'word   \nnext',1,b'w\nnext',1),
        (20,b'word\nnext',4,b'word\nnext',4)):
        m.start(initial);m.putpos(pos);m.keys(bytes([key]))
        assert m.logical()==expected and m.position()==newpos,(key,m.logical(),m.position())
        cases.append(f'preserving TED edit {key}/{pos}')
    m.start(b'a\r\nb')
    m.putpos(1);m.keys(b'\x04');assert m.position()==1
    m.putpos(3);m.keys(b'\x13');assert m.position()==3
    cases.append('horizontal motion stays within TED line')
    for initial,pos,key,expected in (
        (b'aa.bb  cc',0,6,3),(b'aa.bb  cc',2,6,3),
        (b'aa.bb  cc',3,6,7),(b'aa-bb_cc zz',0,6,9),
        (b'word\r\nnext',0,6,4),(b'word\r\nnext',4,6,4),
        (b'word\r\nnext',6,1,6),(b'word\r\nnext',8,1,6),
        (b'aa.bb  cc',9,1,7),(b'aa.bb  cc',7,1,3)):
        m.start(initial);m.putpos(pos);m.keys(bytes([key]));assert m.position()==expected,(initial,pos,key,m.position())
        assert m.logical()==initial
        cases.append(f'line-local word {key}/{pos}')
    m.start(b'ab\tXYZ 12345')
    m.keys(b'\x0f');assert m.position()==3
    m.keys(b'\x11');assert m.position()==0
    m.putpos(4);m.keys(b'\x0c');assert m.position()==0
    m.keys(b'\x0c');assert m.position()==12
    cases.append('O/Q tab stops and retained L toggle')
    for operation,expected in (
        (b'M 1 2 3',b'one\ntwo\nthree\none\ntwo\nfour\n'),
        (b'MD 1 2 3',b'three\none\ntwo\nfour\n'),
        (b'D 2 3',b'one\nfour\n')):
        m.start(b'one\ntwo\nthree\nfour\n')
        assert command(operation)==0,(operation,m.value('TW_ERROR',1))
        assert m.logical()==expected,(operation,m.logical())
        assert not m.value('TC_BSET',1) and not m.value('TC_ESET',1)
        cases.append('TED command '+operation.decode())
    for operation in (b'M 1 3 2',b'MD 1 3 2',b'D 3 1',b'M 1 2 65536'):
        m.start(b'one\ntwo\nthree\nfour\n')
        assert command(operation)!=0,operation
        assert m.logical()==b'one\ntwo\nthree\nfour\n'
        cases.append('rejected range '+operation.decode())
    for token,key in ((b'A0:FILE.TXT',(1,0,'FILE.TXT')),(b'P31:LAST.ASM',(16,31,'LAST.ASM')),
                      (b'16:TEST',(1,16,'TEST')),(b'file.txt',(1,0,'FILE.TXT'))):
        m.start(b'')
        m.mem[m.address('TE_CALLER')]=1;m.mem[m.address('TE_CALLER')+36]=0
        field('TE_FIELD',token+b'\0');m.reg['H'].value=m.address('TE_FIELD')>>8;m.reg['L'].value=m.address('TE_FIELD')&255
        assert m.invoke('OP_PARSE_FILE')==0,token
        assert m.fcbkey_with_user(m.address('TE_FILE'))==key
        cases.append('exact DU '+token.decode())
    for token in (b'Q:FILE',b'A32:FILE',b'A256:FILE',b'LONGERNAM.TXT',b'BAD.*',b'FILE.XYZQ',b'A-1:FILE'):
        m.start(b'')
        field('TE_FIELD',token+b'\0');m.reg['H'].value=m.address('TE_FIELD')>>8;m.reg['L'].value=m.address('TE_FIELD')&255
        assert m.invoke('OP_PARSE_FILE')!=0,token
        cases.append('refused filespec '+token.decode())
    m.start(b'ABC abc\r\nABC')
    assert command(b'/abc/')==0 and m.position()==4
    assert command(b'/absent/')!=0 and m.position()==4
    cases.append('existing forward case-sensitive find, no wrap')
    m.start(b'aa aa\r\naa')
    assert command(b'SU /aa/b/')==0
    assert m.logical()==b'b b\r\nb'
    cases.append('existing substitute-all')
    m.start(b'aa aa\r\naa')
    assert command(b'SU 2 /aa//')==0
    assert m.logical()==b' \r\naa'
    cases.append('existing counted empty substitution')
    m.start(b'first\r\nsecond\nthird\rlast  ')
    identity=bytes(m.mem[m.address('TW_META')+22:m.address('TW_META')+59])
    assert command(b'W D12:OUT.TXT')==0
    assert m.files[(4,12,'OUT.TXT')].data==padded(b'first\r\nsecond\nthird\rlast  ')
    assert bytes(m.mem[m.address('TW_META')+22:m.address('TW_META')+59])==identity
    cases.append('alternate whole W preserves exact records and default identity')
    assert command(b'W 2 3 D12:RANGE.TXT')==0
    assert m.files[(4,12,'RANGE.TXT')].data==padded(b'second\nthird\r')
    cases.append('inclusive line-range W')
    m.add((4,12,'IN.TXT'),padded(b'ignore\ninsert1\r\ninsert2\nignore2'))
    assert command(b'R (1) D12:IN.TXT (2,3)')==0, (m.value('TW_ERROR',1), m.value('TS_ERROR',1),m.value(m.mapping['operations']['OP_FIRST'],2),m.value(m.mapping['operations']['OP_LAST'],2),m.value(m.mapping['operations']['OP_SOURCE_BEGIN'],3),m.value(m.mapping['operations']['OP_SOURCE_END'],3),m.value('TW_INPUT_LEN',3))
    assert m.logical()==b'first\r\ninsert1\r\ninsert2\nsecond\nthird\rlast  ',m.logical()
    assert m.fcbkey_with_user(m.address('TW_META')+22)==(4,12,'IN.TXT')
    cases.append('TED R destination/source range and latest-read default')
    m.start(b'appended\t  \r\n')
    m.add((4,12,'APP.TXT'),padded(b'existing\r\n'))
    m.prompts=[b'Y']
    assert command(b'W D12:APP.TXT $')==0
    assert m.files[(4,12,'APP.TXT')].data==padded(b'existing\r\nappended\t  \r\n')
    assert m.files[(4,12,'TEB00000.BAK')].data==padded(b'existing\r\n')
    assert m.logical()==b'appended\t  \r\n'
    cases.append('safe W append uses immutable target snapshot and retains backup')
    m.start(b'abc')
    before=list(m.mutations)
    m.keys(b'XYZ')
    assert m.logical()==b'XYZ' and m.mutations==before
    assert m.value('WL_ACTIVE',1)==1
    assert m.invoke('WL_FLUSH')==0 and m.value('WL_ACTIVE',1)==0
    assert m.logical()==b'XYZ'
    cases.append('ordinary typing buffered with no disk mutations until verified flush')
    m.start(b'abc')
    m.keys(b'X')
    m.failures[22]=(m.calls.get(22,0)+1,False)
    assert m.invoke('WL_FLUSH')!=0
    assert m.logical()==b'Xbc' and m.value('WL_ACTIVE',1)==1
    m.failures.clear()
    assert m.invoke('WL_FLUSH')==0 and m.logical()==b'Xbc'
    cases.append('failed dirty-line flush retains editable RAM text and can retry')
    m.start(b'abc')
    m.putpos(3);m.keys(b'\x04\x04X')
    assert m.logical()==b'abc  X' and m.position()==6
    m.keys(b'\x08');assert m.logical()==b'abc   ' and m.position()==5
    cases.append('TED virtual columns materialize only on typing; overwrite Backspace blanks')
    m.start(b'abc')
    m.keys(b'X\r')
    assert m.logical()==b'X\r\nbc'
    cases.append('line split flushes dirty line without losing insertion arguments')
    m.start(b'abc')
    assert m.invoke('OP_DUPLICATE')==0
    assert m.logical()==b'abc\r\nabc' and m.position()==5
    cases.append('duplicate unterminated final line preserves new last-line termination')
    m.start(b'abc')
    m.putpos(1)
    assert m.invoke('OP_LINE_BELOW')==0
    assert m.logical()==b'abc\r\n' and m.position()==5 and m.value('TC_VIRTUAL',2)==1
    cases.append('TED insert-below preserves visual column without implicit spaces')
    for operation,expected in (
        (b'M 3 3 0', b'last\none\ntwo\nlast'),
        (b'M 1 1 3', b'one\ntwo\nlast\none\n'),
        (b'MD 3 3 0', b'last\none\ntwo\n'),
        (b'MD 1 1 3', b'two\nlast\none\n')):
        m.start(b'one\ntwo\nlast')
        assert command(operation)==0,operation
        assert m.logical()==expected,(operation,m.logical())
        cases.append('whole-line boundary '+operation.decode())
    m.start(b'one\rTWO\n\nlast')
    assert command(b'M 3 3 1')==0
    assert m.logical()==b'one\r\r\nTWO\n\nlast',m.logical()
    cases.append('copy prevents CR/LF coalescence across new line boundaries')
    m.start(b'first\nlast')
    m.add((4,12,'IN.TXT'),padded(b'insert'))
    assert command(b'R (1) D12:IN.TXT')==0
    assert m.logical()==b'first\ninsert\nlast'
    cases.append('R unterminated source remains a whole inserted line')
    m.start(b'right')
    m.add((4,12,'APP.TXT'),padded(b'left'))
    m.prompts=[b'Y']
    assert command(b'W D12:APP.TXT $')==0
    assert m.files[(4,12,'APP.TXT')].data==padded(b'left\r\nright')
    cases.append('append after unterminated target supplies only required separator')
    m.start(b'right')
    assert command(b'W D12:NEW.TXT $')==0
    assert m.files[(4,12,'NEW.TXT')].data==padded(b'right')
    cases.append('append to absent target creates it through safe publication')
    m.start(b'one\ntwo\nthree')
    assert command(b'P 2 7')==0
    assert m.position()==7 and m.value('TC_VIRTUAL',2)==4
    assert command(b'P +1')==0 and m.position()==8
    assert command(b'/one/(1,1)')==0 and m.position()==0
    assert command(b'/three/(1,1)')!=0
    cases.append('TED indexed positions, virtual columns, relative line and bounded search')
    m.start(b'A'*4094)
    m.putpos(4094);m.keys(b'\x16B')
    assert m.logical()==b'A'*4094+b'B'
    m.reg['A'].value=ord('C')
    assert m.invoke('TC_KEY')!=0
    assert m.logical()==b'A'*4094+b'B' and m.position()==4095
    assert bytes(m.mem[m.address('WL_GUARD'):m.address('WL_GUARD')+32])==b'\xa5'*32
    m.keys(b'\x08');assert m.logical()==b'A'*4094
    cases.append('4095-byte RAM line, refused overflow, intact guard and editable retry')
    m.start(b'A'*4095)
    m.keys(b'\x14');assert m.logical()==b''
    cases.append('delete-word removes full 4095-byte line without zero-count copy overrun')
    m.start(b'A'*2048+b'\r\n'+b'B'*2047)
    m.putpos(2050);m.keys(b'\x08')
    assert m.logical()==b'A'*2048+b'B'*2047
    cases.append('join reaches exact 4095-byte limit with original byte preservation')
    m.start(b'A'*4095+b'\nB')
    m.putpos(4096);m.reg['A'].value=8
    assert m.invoke('TC_KEY')!=0
    assert m.logical()==b'A'*4095+b'\nB'
    cases.append('overlong join refused without truncating either source line')
    m.start(b'one\ntwo\nthree')
    assert command(b'/two/(1,3)+1')==0 and m.position()==8
    assert command(b'/three/(1,3)-2')==0 and m.position()==0
    cases.append('TED text-index displacement uses found line and zero column')
    return cases

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-commands-') as directory:
        work = Path(directory)
        prepared, mapping = source()
        prepared = prepared.replace('TED_END EQU $', PROBE+'\nTED_END EQU $')
        (work/'probe.mac').write_text(prepared)
        subprocess.run([str(Path.home()/'bin/z80asm'), '-e32', '-fb', '-o'+str(work/'probe.bin'),
                        '-l'+str(work/'probe.lst'), str(work/'probe.mac')], check=True)
        image = (work/'probe.bin').read_bytes()
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(a.z80pack/'z80sim/srcsim'/name, work/name)
        (work/'shim.c').write_text(SHIM.replace('cpu_state=ST_SINGLE_STEP;', 'if(PC==65535) return i; cpu_state=ST_SINGLE_STEP;'))
        core = a.z80pack/'z80core'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', f'-I{work}', f'-I{core}',
                        str(work/'shim.c'), str(core/'simglb.c'),
                        *map(str, sorted(core.glob('simz80*.c'))), '-o', str(work/'core.so')], check=True)
        m = Commands(C.CDLL(str(work/'core.so')), image, (work/'probe.lst').read_text(), mapping)
        results = tests(m)
        report = {'status': 'PASS', 'scope': 'compiled logical commands; frontend/physical key acceptance separate',
                  'cases': len(results), 'results': results}
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(report, indent=2)+'\n')
        print('PASS', len(results), 'compiled command cases')


if __name__ == '__main__':
    main()
