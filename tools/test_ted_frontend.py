#!/usr/bin/env python3
"""Execute complete TED input/prompt/render/file paths on the independent CPU.

SCRN/BDOS are modeled; native paired-emulator campaigns are separate evidence.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_ted import ROOT,source
from test_ted_commands import Commands
from test_ted_publisher import PROBE
from test_ted_workspace import padded
from test_usq import SHIM


class Frontend(Commands):
    def callback(self,kind):
        if kind==1:
            try:
                op=self.reg['A'].value
                b,c=self.reg['B'].value,self.reg['C'].value
                if op==12:
                    self.reg['H'].value=0
                    self.reg['L'].value=0x48
                elif op==6:
                    assert b<24 and c<80,('bad position',b,c)
                    self.row,self.col=b,c
                elif op==7:
                    self.screen[self.row][self.col]=c&127
                    self.col=min(79,self.col+1)
                elif op==8:
                    self.screen[self.row][self.col:]=[c&127]*(80-self.col)
                elif op==15:
                    assert c in (0,1)
                else:raise AssertionError(('unexpected SCRN',op,hex(self.reg['SP'].value),bytes(self.mem[self.reg['SP'].value:self.reg['SP'].value+24]).hex(),bytes(self.mem[self.address('TE_STATUS'):self.address('TE_STATUS')+80])))
                self.reg['A'].value=0
                self.reg['F'].value=0
            except BaseException as error:
                self.exception=error;self.reg['PC'].value=0xffff
            return
        super(Commands,self).callback(kind)

    def bdos(self,fn,de):
        if getattr(self, 'running', False):
            self.last_calls.append((fn, de, self.reg['SP'].value, bytes(self.mem[0xee:0xf0]).hex()))
            self.last_calls=self.last_calls[-20:]
        if fn==6:
            assert de&255==255
            return self.input.pop(0) if self.input else 0
        if fn==9:
            self.console+=bytes(self.mem[de:]).split(b'$')[0]
            return 0
        if fn==2:
            self.console+=bytes([de&255]);return 0
        if fn==25:return self.drive-1
        if fn==14:self.drive=(de&255)+1;return 0
        if fn==182:
            self.providers.append(bytes(self.mem[de+4:de+10]))
            self.mem[de+12:de+14]=(0x40).to_bytes(2,'little')
            return 0
        return super().bdos(fn,de)

    def execute(self,tail=b'',keys=b'',files=None,ceiling=0xd000):
        self.running=False
        self.begin()
        self.last_calls=[]
        self.input=list(keys)
        self.console=b'';self.providers=[]
        self.row,self.col=0,0;self.screen=[[32]*80 for _ in range(24)]
        self.lib.set_hooks(5,0x40,self.hook)
        self.mem[0x40]=0xc9
        self.mem[0x48:0x51]=b'SCR\x01\x00\x18\x50\xff\xff'
        self.mem[0:3]=bytes([0xc3,0,0xf0])
        self.mem[0xf03f]=0xc9
        self.mem[0xf000]=0xc9
        self.mem[6:8]=ceiling.to_bytes(2,'little')
        self.mem[0x80]=len(tail)
        self.mem[0x81:0x81+len(tail)]=tail
        self.drive,self.user,self.dma=1,7,0x80
        for key,data in (files or {}).items():self.add(key,data)
        self.reg['SP'].value=0xf0
        protected=bytes(self.mem[ceiling:0xfffe])
        spare=bytes(self.mem[self.end:ceiling])
        self.running=True
        result=self.lib.test_run(0x100,30000000)
        assert self.exception is None,(self.exception,self.last_calls,hex(self.value(self.mapping['frontend']['TE_OLDSP'],2)))
        assert result>=0,(result,hex(self.reg['PC'].value),self.input,self.text())
        assert bytes(self.mem[ceiling:0xfffe])==protected,'TPA ceiling crossed'
        assert bytes(self.mem[self.end:ceiling])==spare,'unexpected dynamic allocation'
        assert self.reg['SP'].value==0xf0
        if self.providers:
            top=self.address('TED_STACK_TOP')
            low=top-2048-32
            assert bytes(self.mem[low:low+32])==bytes([0xa5])*32, 'low stack canary'
            first=next((at for at in range(low+32,top) if self.mem[at]!=0xa5),top)
            self.high_water=max(getattr(self,'high_water',0),top-first)
            assert top-first<=1536, 'stack reserve below 512 bytes'
            at=self.address('WL_GUARD')
            assert bytes(self.mem[at:at+32])==bytes([0xa5])*32, 'inline RAM canary'
        return self.text()

    def text(self):return '\n'.join(''.join(map(chr,row)) for row in self.screen)


def tests(m):
    cases=[]
    for tail in (b'/VER',b'file.txt /ver',b'/HELP /VER',b'bad:* /hElP'):
        m.execute(tail)
        assert not m.providers and not m.mutations
        assert b'TED' in m.console
        if b'help' in tail.lower():assert b'^K:' in m.console
        cases.append('query without provider/file operations '+tail.decode())
    original=padded(b'Original\t spaces  \r\nLF\nCR\rend  ')
    m.execute(b'INPUT.TXT',b'S\rX\x0bSY\r\x0bQ',files={(1,7,'INPUT.TXT'):original})
    assert m.files[(1,7,'INPUT.TXT')].data==b'X'+original[1:]
    assert m.files[(1,7,'TEB00000.BAK')].data==original
    assert (m.drive,m.user,m.dma)==(1,7,0x80)
    assert not any(k[2].startswith('TEW') for k in m.files)
    cases.append('full editor open overwrite safe-save backup clean-exit caller-context')
    m.execute(b'NEW.TXT',b'S\rhello\x0bS\x0bQ')
    assert m.files[(1,7,'NEW.TXT')].data==padded(b'hello')
    cases.append('new named document creates target only on save')
    m.execute(b'INPUT.TXT',b'\x03\x0e\x1a\x1a',files={(1,7,'INPUT.TXT'):original})
    assert m.files[(1,7,'INPUT.TXT')].data==original
    cases.append('command Ctrl-C enters screen; N browse; Z returns twice then exits')
    m.execute(b'INPUT.TXT',b'S\rX\x0bQ\r\x0bQY\r',files={(1,7,'INPUT.TXT'):original})
    assert m.files[(1,7,'INPUT.TXT')].data==original
    cases.append('default-No abandon and explicit Yes leave original unchanged')
    m.execute(b'',b'EX\r')
    assert not m.mutations
    cases.append('empty command tail returns safely without a workspace')
    m.execute(b'',b'S\rhello\x0bSNEW.TXT\r\x0bQ')
    assert m.files[(1,7,'NEW.TXT')].data==padded(b'hello')
    cases.append('unnamed buffered document names and saves through W prompt')
    for keyseq,expected in (
        (b'\x0bC1\r2\r3\r',b'one\ntwo\nthree\none\ntwo\nfour\n'),
        (b'\x0bV1\r2\r3\r',b'three\none\ntwo\nfour\n'),
        (b'\x0bY2\r3\r',b'one\nfour\n')):
        data=padded(b'one\ntwo\nthree\nfour\n')
        m.execute(b'INPUT.TXT',b'S\r'+keyseq+b'\x0bSY\r\x0bQ',files={(1,7,'INPUT.TXT'):data})
        assert m.files[(1,7,'INPUT.TXT')].data==padded(expected)
        cases.append('full shared prompts for line-range '+keyseq[:2].hex())
    m.execute(b'INPUT.TXT OTHER',b'EX\r',files={(1,7,'INPUT.TXT'):original})
    assert not m.mutations
    cases.append('extra invocation operand rejected before file operations')
    for ceiling in (m.end-1,m.end,m.end+1,0xa800,0xd000):
        m.execute(b'',b'EX\r',ceiling=ceiling)
        assert not m.mutations
        cases.append('exclusive TPA boundary '+hex(ceiling))
    m.execute(b'INPUT.TXT', b'P 2\r\x05\x15P 1\r\x07EX\r',
              files={(1,7,'INPUT.TXT'):original})
    assert m.files[(1,7,'INPUT.TXT')].data==original
    cases.append('TED command recall E/G and U clear retain command-mode behavior')
    return cases


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/ted-frontend.json')
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ted-frontend-') as directory:
        w=Path(directory);prepared,mapping=source()
        prepared=prepared.replace('TED_END EQU $',PROBE+'\nTED_END EQU $')
        (w/'probe.mac').write_text(prepared)
        subprocess.run([str(Path.home()/'bin/z80asm'),'-e32','-fb','-o'+str(w/'probe.bin'),'-l'+str(w/'probe.lst'),str(w/'probe.mac')],check=True)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        pack=Path.home()/'projects/git/z80pack'
        for name in ('simmem.h','simport.h'):shutil.copy2(pack/'z80sim/srcsim'/name,w/name)
        (w/'shim.c').write_text(SHIM.replace('cpu_state=ST_SINGLE_STEP;','if(PC==65535) return i; cpu_state=ST_SINGLE_STEP;'))
        core=pack/'z80core'
        subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{w}',f'-I{core}',str(w/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        m=Frontend(C.CDLL(str(w/'core.so')),(w/'probe.bin').read_bytes(),(w/'probe.lst').read_text(),mapping)
        (ROOT/'build/ted-frontend-debug.lst').write_text((w/'probe.lst').read_text())
        results=tests(m)
        report={'status':'PASS','scope':'complete frontend on independent CPU; modeled BDOS/SCRN','cases':len(results),'results':results,
                'source_sha256':hashlib.sha256(prepared.encode()).hexdigest(), 'modeled_stack_high_water':m.high_water, 'private_stack_bytes':2048, 'reserve_bytes':512}
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',len(results),'complete frontend cases')

if __name__=='__main__':main()
