#!/usr/bin/env python3
"""Execute complete TED input/prompt/render/file paths on the independent CPU.

SCRN/BDOS are modeled; native paired-emulator campaigns are separate evidence.
Response chunks in key lists arrive at actual controller reads, so local
cancellation tests do not accidentally cancel an earlier document load.
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
            if self.input and isinstance(self.input[0],bytes):
                # A bytes chunk models a response typed after the choice is live.
                # Keep ESC/^C out of earlier load/flush cancellation polls.
                back=self.address(self.mapping['frontend']['UC_READ'])+3
                sp=self.reg['SP'].value
                if not any(int.from_bytes(bytes(self.mem[n:n+2]),'little')==back for n in range(sp,sp+64,2)):
                    return 0
                chunk=self.input.pop(0)
                assert chunk
                self.input[:0]=list(chunk)
            if self.input:
                value=self.input.pop(0)
                self.input_screens.append((value, ''.join(map(chr,self.screen[23]))))
                return value
            return 0
        if fn==9:
            self.console+=bytes(self.mem[de:]).split(b'$')[0]
            return 0
        if fn==2:
            self.console+=bytes([de&255]);return 0
        if fn==25:return self.drive-1
        if fn==14:self.drive=(de&255)+1;return 0
        if fn==182:
            self.providers.append(bytes(self.mem[de+4:de+10]))
            available=getattr(self,'service_versions',{b'MCON':(1,2),b'SCRN':(1,1)})
            version=available.get(bytes(self.mem[de+4:de+8]))
            requested=tuple(self.mem[de+8:de+10])
            if version is None or version[0]!=requested[0] or version[1]<requested[1]:
                return 1
            self.mem[de+12:de+14]=(0x40).to_bytes(2,'little')
            return 0
        return super().bdos(fn,de)

    def execute(self,tail=b'',keys=b'',files=None,ceiling=0xd000,instruction_budget=30000000,attributes=None):
        self.running=False
        self.begin()
        self.last_calls=[]
        self.input=list(keys);self.input_screens=[]
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
        for key,data in (files or {}).items():self.add(key,data,**(attributes or {}).get(key,{}))
        self.reg['SP'].value=0xf0
        protected=bytes(self.mem[ceiling:0xfffe])
        spare=bytes(self.mem[self.end:ceiling])
        self.running=True
        result=self.lib.test_run(0x100,instruction_budget)
        assert self.exception is None,(self.exception,self.last_calls,hex(self.value(self.mapping['frontend']['TE_OLDSP'],2)))
        assert result>=0,(tail,keys,result,hex(self.reg['PC'].value),self.input,self.text())
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
        if b'help' in tail.lower():
            from utility_help import text
            assert text('TED').encode() in m.console
        cases.append('query without provider/file operations '+tail.decode())
    for minor in (0,2):
        m.service_versions={b'MCON':(1,minor),b'SCRN':(1,1)}
        m.execute(keys=b'EX\r')
        assert b'TED requires' not in m.console
        assert m.providers[:2]==[b'MCON\x01\x00',b'SCRN\x01\x01']
        cases.append(f'integrated/legacy MCON 1.{minor} with SCRN 1.1 admission')
    for available in ({b'MCON':(1,0)}, {b'SCRN':(1,1)}, {b'MCON':(1,0),b'SCRN':(1,0)}):
        m.service_versions=available
        m.execute()
        assert b'TED requires SCRN 1.1' in m.console and not m.mutations
        cases.append('missing or insufficient display service refused '+repr(available))
    del m.service_versions
    original=padded(b'Original\t spaces  \r\nLF\nCR\rend  ')
    m.execute(b'INPUT.TXT',b'S\rX\x0bSY\x0bQ',files={(1,7,'INPUT.TXT'):original})
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
    m.execute(b'INPUT.TXT',b'S\rX\x0bQ\r\x0bQY',files={(1,7,'INPUT.TXT'):original})
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
        m.execute(b'INPUT.TXT',b'S\r'+keyseq+b'\x0bSY\x0bQ',files={(1,7,'INPUT.TXT'):data})
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
    data=(b'A'*64+b'\n')*21
    m.execute(b'INPUT.TXT',b'S\r'+b'X'*200+b'\x0bSY\x0bQ',
              files={(1,7,'INPUT.TXT'):padded(data)},instruction_budget=1000000000)
    assert m.files[(1,7,'INPUT.TXT')].data==padded(b'X'*200+b'\n'+data[65:])
    assert m.files[(1,7,'TEB00000.BAK')].data==padded(data)
    assert not m.input and m.value(m.mapping['frontend']['TE_QUEUE_COUNT'],1)==0
    cases.append('200 queued keys cross disk-backed redraw pages and safe-save; bounded FIFO preserves all keys')
    # Real choice entry, every raw byte, no editor-buffer or typeahead damage.
    m.execute(b'',b'EX\r')
    label=m.address(m.mapping['operations']['OP_ABANDONLABEL'])
    question='Discard changes? (Y/N) [N]: '
    for key in range(256):
        m.input=[key,ord('N'),ord('!')];m.input_screens=[]
        m.mem[m.address(m.mapping['frontend']['TE_COMMAND_READ'])]=1
        state_names=['EDITBUF','EDITLEN','EDITCUR','EDITSTART','TE_FIELD','TE_FIELDLEN','TE_HISTORY','TE_HISTORY_LEN']
        spans=[(m.address(m.mapping['frontend'].get(n,n)),95 if n in ('EDITBUF','TE_HISTORY') else 96 if n=='TE_FIELD' else 1) for n in state_names]
        before=[bytes(m.mem[a:a+n]) for a,n in spans]
        m.reg['H'].value=label>>8;m.reg['L'].value=label&255
        m.reg['IX'].value=0x1234;m.reg['IY'].value=0x5678
        failed=m.invoke('TE_CHOOSE')
        cancel=key in (3,27)
        immediate=key in (3,13,27,ord('Y'),ord('y'),ord('N'),ord('n'))
        assert bool(failed)==cancel,(key,failed)
        if not cancel:assert m.reg['A'].value==(ord('Y') if key in (ord('Y'),ord('y')) else ord('N')),key
        assert m.input==([ord('N'),ord('!')] if immediate else [ord('!')]),(key,m.input)
        assert all(row.startswith(question) for _,row in m.input_screens),(key,m.input_screens)
        assert [bytes(m.mem[a:a+n]) for a,n in spans]==before,key
        assert m.reg['IX'].value==0x1234 and m.reg['IY'].value==0x5678
        assert m.mem[m.address(m.mapping['frontend']['TE_COMMAND_READ'])]==1
        cases.append('choice raw byte '+str(key))
    # Missing/malformed configuration must fail closed without reading a key.
    for name,value in [('UC_COUNT',0),('UC_DEF',ord('X'))]:
        at=m.address(m.mapping['frontend'][name]);old=m.mem[at];m.mem[at]=value
        m.input=[ord('Y')];m.reg['H'].value=label>>8;m.reg['L'].value=label&255
        assert m.invoke('TE_CHOOSE') and m.input==[ord('Y')]
        m.mem[at]=old;cases.append('choice malformed '+name)
    # Denied/cancelled save keeps the target; only a later explicit abandonment exits.
    target=(1,7,'INPUT.TXT');original=padded(b'Original\r\n')
    for answer in (b'N',b'n',b'\r',b'\x1b',b'\x03',b'??xN'):
        m.execute(b'INPUT.TXT',[*b'S\rX\x0bS',answer,*b'\x0bQ',b'Y'],files={target:original})
        assert m.files[target].data==original
        assert not any(k[2].endswith('.BAK') for k in m.files)
        assert not m.input and m.value(m.mapping['frontend']['TE_QUEUE_COUNT'],1)==0
        cases.append('save refusal '+answer.hex())
    # No and Cancel at abandonment keep the modified document available to save.
    for answer in (b'N',b'\r',b'\x1b',b'\x03',b'?xN'):
        m.execute(b'INPUT.TXT',[*b'S\rX\x0bQ',answer,*b'\x0bS',b'Y',*b'\x0bQ'],files={target:original})
        assert m.files[target].data==b'X'+original[1:]
        assert m.files[(1,7,'TEB00000.BAK')].data==original
        cases.append('abandon refusal retains edit '+answer.hex())
    # Protection authorization is independent from overwrite approval.
    for flags in ({'ro':True},{'sys':True},{'ro':True,'sys':True}):
        for answer in (b'N',b'\r',b'\x1b',b'\x03',b'??N'):
            m.execute(b'INPUT.TXT',[*b'S\rX\x0bS',b'Y',answer,*b'\x0bQ',b'Y'],files={target:original},attributes={target:flags})
            assert m.files[target].data==original
            assert bool(m.files[target].attributes[0][8])==flags.get('ro',False)
            assert bool(m.files[target].attributes[0][9])==flags.get('sys',False)
            assert not any(k[2].endswith('.BAK') for k in m.files)
            cases.append('protected refusal '+str(flags)+' '+answer.hex())
        m.execute(b'INPUT.TXT',[*b'S\rX\x0bS',b'Y',b'Y',*b'\x0bQ'],files={target:original},attributes={target:flags})
        assert m.files[target].data==b'X'+original[1:]
        assert m.files[(1,7,'TEB00000.BAK')].data==original
        cases.append('protected explicit double approval '+str(flags))
    # N/default skip one match, cancellation stops before the remaining matches.
    for answers,want in [(b'NY\r',b'one X one\r\n'),(b'??YNN',b'X one one\r\n'),
                          (b'Y\x1b',b'X one one\r\n'),(b'Y\x03',b'X one one\r\n')]:
        source=padded(b'one one one\r\n')
        m.execute(b'INPUT.TXT',[*b'SU M /one/X/\r',*[bytes([key]) for key in answers],*b'W\r',b'Y',*b'EX\r'],files={target:source})
        assert m.files[target].data==padded(want),(answers,m.files[target].data)
        assert m.files[(1,7,'TEB00000.BAK')].data==source
        assert not m.input and m.value(m.mapping['frontend']['TE_QUEUE_COUNT'],1)==0
        cases.append('per-match choice scope '+answers.hex())
    from qualify_ted_engine import checkpoint,RECOVERED
    recovery=(1,7,'CHECKP.TMP');saved=checkpoint(1)
    for answer in (b'N',b'\r',b'\x1b',b'\x03',b'??N'):
        m.execute(b'INPUT.TXT',[*b'RECOVER CHECKP.TMP\r',answer,*b'EX\r'],files={target:original,recovery:saved})
        assert m.files[target].data==original and m.files[recovery].data==saved
        cases.append('recovery refusal '+answer.hex())
    m.execute(b'INPUT.TXT',[*b'RECOVER CHECKP.TMP\r',b'Y',*b'W A7:OUT.TXT\rEX\r',b'Y'],files={target:original,recovery:saved})
    assert m.files[(1,7,'OUT.TXT')].data==padded(RECOVERED)
    assert m.files[recovery].data==saved and m.files[target].data==original
    cases.append('recovery immediate approval retains source')
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
