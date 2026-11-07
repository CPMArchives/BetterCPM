#!/usr/bin/env python3
"""Replay external CP/M cases using the actual Model II resident, CCP and BCM2SS files."""
import argparse
import ctypes as C
import hashlib
import json
import re
import struct
import tempfile
from pathlib import Path

from build_z80pack_image import symbols
from run_model2_conformance import (GROUPS, SUITE_REV, OFFSET, CPMTOOLS, DISKDEFS, DISK_RO, FAULTS, SWAPS,
                                    decoded, disk, compiled, cpm, normalized)
from model2_media import geometry
from test_model2_screen import WINDOW, cpu_library
from test_usq import SHIM

# Disk transfer is the only replaced resident routine. Stop a running CPU after
# repeated empty keyboard polls. This preserves the actual prompt and CPU stack
# between inputs and lets an injected write fail after it has dirtied media.
KEYS = """
static BYTE keys[1024]; static unsigned head, tail;
static unsigned idle;
int defer_after_first; unsigned deferred_polls;
void type_keys(const BYTE *p, unsigned count) {
    memcpy(keys,p,count); head=0; tail=count; idle=0;
}
BYTE io_in(BYTE port, BYTE high) {
    if (port == 0xff) {
        if(defer_after_first && head==1 && deferred_polls<64) {++deferred_polls;return 0;}
        if(head==tail) ++idle;
        return head<tail ? 0x80 : 0;
    }
    if (port == 0xfc && head<tail) {idle=0;return keys[head++];}
    return 0;
}
"""
ADVANCE = """
int advance(int budget) {
    cpu_error=0; tmax=100000000; idle=0;
    for(int i=0;i<budget;i++) {
        if(idle>512) return 0;
        if(PC==readpc) hook(0);
        if(PC==writepc) {idle=0;hook(1);}
        cpu_state=ST_SINGLE_STEP; cpu_z80();
        if(cpu_error) return -cpu_error;
    }
    return -1000;
}
"""


class Session:
    def __init__(self, library, out, media):
        self.lib = library
        self.read_count = 0
        self.drives = [bytearray(decoded(blob)[2]) for blob in media]
        self.output = bytearray()
        self.error = None
        self.fail_writes = []
        self.write_count = 0
        self.writes = []
        self.ram = (C.c_ubyte*65536).in_dll(library,'memory')
        self.reg = {n:C.c_ubyte.in_dll(library,n) for n in 'ACDEHL'}
        self.flags = C.c_int.in_dll(library,'F')
        self.pc = C.c_ushort.in_dll(library,'PC')
        self.ram[:] = bytes(65536)
        syms = json.loads((out.parent/'profile/context.json').read_text())['symbols']
        base = syms['LY_SYS']
        code = (out/'resident.bin').read_bytes()
        self.ram[base:base+len(code)] = code
        self.pc.value = syms['LY_BIOS']
        C.c_ushort.in_dll(library,'SP').value = 0x2000
        xfer = symbols(out/'disk.lst')['M2_XFER']
        output = symbols(out/'bios.lst')['PL_CONOT']
        cb = C.CFUNCTYPE(None,C.c_int)
        self.hook = cb(self.on_instruction)
        library.set_hooks.argtypes = [C.c_ushort,C.c_ushort,cb]
        library.set_hooks(xfer,output,self.hook)
        self.ram[xfer] = 0xc9
        self.step(b'',b'A0>')

    def on_instruction(self, event):
        try:
            if event:
                if C.c_int.in_dll(self.lib,'defer_after_first').value:
                    assert C.c_uint.in_dll(self.lib,'deferred_polls').value==64, 'output escaped before XON'
                self.output.append(self.reg['C'].value & 127)
                return
            drive,command,cylinder,sector = (self.reg[n].value for n in 'ACDE')
            size = 512 if cylinder else 128
            assert drive<len(self.drives) and cylinder<77 and 1<=sector<=(16 if cylinder else 26)
            offset = (3328+(cylinder-1)*8192 if cylinder else 0) + (sector-1)*size
            dma = self.reg['H'].value*256 + self.reg['L'].value
            assert dma+size<=65536
            raw = self.drives[drive]
            status = 0
            if command == 0x80:
                self.read_count += 1
                self.ram[dma:dma+size] = raw[offset:offset+size]
            else:
                assert command==0xa0
                self.write_count += 1
                self.writes.append((drive,cylinder,sector))
                if self.write_count in self.fail_writes:
                    raw[offset:offset+size] = b'!'*size
                    status = 1
                else:
                    raw[offset:offset+size] = bytes(self.ram[dma:dma+size])
            self.reg['H'].value,self.reg['L'].value = divmod((dma+size)&65535,256)
            self.reg['A'].value = status
            self.flags.value = 0x40 if status==0 else 0
        except Exception as error:
            self.error = error

    def step(self, keys, witness):
        assert len(keys)<1024
        self.lib.type_keys(keys,len(keys))
        self.output.clear()
        code = self.lib.advance(100000000)
        assert self.error is None, self.error
        text = bytes(self.output)
        assert code==0 and witness in text, (keys,code,hex(self.pc.value),text[-1200:])
        return text


def suite_rows(library, out, packet, system):
    info = json.loads((packet/'packet.json').read_text())
    assert info['system_sha256']==hashlib.sha256(system).hexdigest() and info['suite_revision']==SUITE_REV
    rows = {}
    for name,selector,expected in GROUPS:
        mounts = info['cases'][name.lower()]['mounts']
        media = [system]+[(packet/mounts[k]).read_bytes() for k in sorted(mounts)]
        for k in mounts: assert hashlib.sha256((packet/mounts[k]).read_bytes()).hexdigest()==Path(mounts[k]).stem
        guest = Session(library,out,media)
        guest.step(b'B:\r',b'B0>')
        if name=='DISKTEST':
            # A full allocation map with free directory slots (unlike FILETEST D).
            fmt = geometry()
            full = [('BTFULL.DAT',bytes(127*128)+b'FULL-127'+bytes(120)),('BTREL.DAT',bytes(128)),
                    ('BTFILL.DAT',bytes((fmt.dsm+1-fmt.directory_blocks-9)*fmt.block_bytes))]
            guest.drives.append(bytearray(decoded(disk(full))[2]))
            guest.step(b'DISKTEST /GROUP:REQUIRED\r',b'Enter its configured drive letter')
            trace = guest.step(b'D',b'Summary:')
            expected = 11
        else:
            trace = guest.step((name+' '+selector+'\r').encode(),b'Summary:')
        assert f'Summary: {expected} pass, 0 fail, 0 error'.encode() in trace, (name,trace[-1500:])
        result = {}
        for match in re.finditer(rb'^\s*(\d{4})\s+([PFEOS?\-])\s+([A-Z?])\s+([^\r\n]*)',trace,re.M):
            card,status,_,detail = [v.decode('ascii') for v in match.groups()]
            assert card not in result and status not in ('F','E'), (name,card,detail)
            result[card] = [status,detail]
        assert sum(row[0]=='P' for row in result.values())==expected, (name,result)
        rows[name] = result
    return rows



def terminal_cases(library,out,packet,system):
    cases=json.loads((packet/'packet.json').read_text())['cases']
    results={}
    for name in (*DISK_RO,*FAULTS,*SWAPS):
        case=cases[name]
        mounts=case['mounts']
        guest=Session(library,out,[system]+[(packet/mounts[k]).read_bytes() for k in sorted(mounts)])
        original=bytes(guest.drives[1])
        if name in SWAPS:
            mode=' R' if name.endswith('reset') else ''
            guest.step(('C0:MEDIA'+mode+'\r').encode(),b'OR-0143 SWAP LOGGED B NOW')
            assert bytes(guest.drives[1])==original
            original=decoded((packet/case['replacement']).read_bytes())[2]
            guest.drives[1]=bytearray(original)
            result=guest.step(b'Y',b'OR-0143 RESET AND CREATE PASS' if mode else b'Disk R/O')
            assert b'OR-0143 REPLACEMENT READ AND PROTECTED' in result
            if mode:
                assert guest.drives[1]!=original and b'CREATED TXT' in guest.drives[1][OFFSET:OFFSET+4096]
            else:
                assert bytes(guest.drives[1])==original
        elif name in DISK_RO:
            guest.step(b'B:\r',b'B0>')
            guest.step(('C0:DISKTEST /'+name[-4:]+'\r').encode(),b'Enter its configured drive letter')
            result=guest.step(b'B',b'Disk R/O')
            assert (name[-4:]+': requesting').encode() in result and bytes(guest.drives[1])==original
        else:
            guest.step(b'B:\r',b'B0>')
            result=guest.step(b'C0:FAULTIO\r',b'Bad Sector')
            assert b'Healthy file read passed' in result and b'READ CALLER RESUMED' not in result
            if name=='fault-suspended':
                assert guest.step(b'',b'')==b''
            elif name=='fault-abort':
                result+=guest.step(b'\x03',b'B0>')
                assert b'READ CALLER RESUMED' not in result
                result+=guest.step(b'TYPE BTONE.DAT\r',b'HEALTHY READ AFTER ABORT')
            else:
                result+=guest.step(b'I',b'READ CALLER RESUMED after operator ignore.')
                result+=guest.step(b'I',b'FAULT PROVIDER COMPLETED BOTH CALLS')
                assert b'WRITE CALLER RESUMED' in result
            assert bytes(guest.drives[1])==original
        if name!='fault-suspended':
            result+=guest.step(b'C0:STATE\r',b'STATE D=01 U=00 TOP=E101')
        results[name]=result.decode('ascii')
    return results


def public_calls(library,out,system):
    guest=Session(library,out,[system,disk(),disk([('GUARD.TXT',b'G'*128)]),disk()])
    mem=guest.ram
    bios=symbols(out/'bios.lst')['BIOS']
    sp=C.c_ushort.in_dll(library,'SP')
    def call(entry,c=0,de=0,bc=None,hl=0):
        pairs = (bc if bc is not None else c, hl, de)
        for n,v in zip('BCHLDE',b''.join(pair.to_bytes(2,'big') for pair in pairs)):
            C.c_ubyte.in_dll(library,n).value=v
        sp.value=0x9000
        steps=library.test_run(entry,5000000)
        assert guest.error is None and steps>=0 and sp.value==0x9000, (entry,c,de,steps,guest.error)
        return guest.reg['A'].value, guest.reg['H'].value*256+guest.reg['L'].value
    def bdos(fn,de=0):return call(5,fn,de)[0]
    def value(fn):return call(5,fn)[1]
    def vector(n,**regs):return call(bios+3*n,**regs)
    def word(address):return int.from_bytes(bytes(mem[address:address+2]),'little')
    checks={}
    dpbs={}
    for drive,first in [(1,0xc0),(2,0xe0),(1,0xc0)]:
        assert bdos(14,drive)==0
        dpb=value(31)
        expected=struct.pack('<H3BHHBBHH',64,4,15,0,291,127,192,0,32,4)
        assert bytes(mem[dpb:dpb+15])==expected
        alv=value(27)
        assert bytes(mem[alv:alv+37])==bytes([first])+bytes(36)
        dph=vector(9,c=drive)[1]
        assert word(dph+10)==dpb and word(dph+14)==alv
        dpbs[drive]={'dpb':dpb,'dph':dph,'alv':alv,'bytes':expected.hex(),'first_alv_byte':first}
    checks['0424-0426,0431-0432,0519']=dpbs
    # A documented live DPB pointer. Change CKS only while idle, then restore it.
    mem[dpb+11]=31
    assert value(31)==dpb and word(dpb+11)==31
    mem[dpb+11]=32
    assert word(dpb+11)==32
    checks['0433']='CKS 32 -> 31 -> 32 via the live pointer'
    for mask in (0,1,2,6,15,0x8000,0xffff):
        bdos(13)
        for drive in range(4):
            assert bdos(14,drive)==0 and bdos(28)==0
        bdos(14,1);bdos(32,7);bdos(26,0x7000)
        assert value(24)==value(29)==15
        io=(guest.read_count,guest.write_count)
        assert bdos(37,mask)==0 and value(24)==value(29)==15 & ~mask
        assert bdos(25)==1 and bdos(32,255)==7 and io==(guest.read_count,guest.write_count)
        assert word(symbols(out.parent/'bdos/bdos.lst')['UB_DMA'])==0x7000
        value(31)
        assert value(24)==((15 & ~mask)|2)
    checks['0435,0523']='Seven reset masks, unchanged caller DU and deferred relogin'
    bdos(13);bdos(32,0);bdos(14,1);bdos(26,0x7000)
    # Record the C register at each BIOS WRITE while continuing to the real
    # vector target. Functions Make, Write, Close and Erase use the test disk.
    ptr=bios+42
    target=word(ptr+1)
    shim=b'\xe5\xf5\x2a\x00\x58\x71\x23\x22\x00\x58\xf1\xe1\xc3'+struct.pack('<H',target)
    mem[0x5700:0x5700+len(shim)]=shim
    mem[ptr+1:ptr+3]=struct.pack('<H',0x5700)
    mem[0x5800:0x5802]=struct.pack('<H',0x5900)
    fcb=0x5a00
    def init():mem[fcb:fcb+36]=b'\0TRIAL   BIN'+bytes(24)
    init()
    assert bdos(22,fcb)<4
    mem[0x7000:0x7080]=b'Z'*128
    assert bdos(21,fcb)==0 and bdos(21,fcb)==0 and bdos(16,fcb)<4
    assert mem[value(27)]==0xe0
    init()
    assert bdos(19,fcb)<4 and mem[value(27)]==0xc0
    types=list(mem[0x5900:word(0x5800)])
    assert set(types)=={0,1,2}
    mem[ptr+1:ptr+3]=struct.pack('<H',target)
    checks['0427,0458']={'BIOS WRITE types':types,'ALV transitions':[192,224,192]}
    # Physical state is selected lazily. Exercise null and nonidentity XLT,
    # chosen DMA, and the first/last data record on a disposable disk.
    count=guest.read_count
    assert vector(9,c=2)[1]==dpbs[2]['dph'] and vector(9,c=4)[1]==0
    assert count==guest.read_count
    mem[0x6200:0x6203]=bytes([12,9,5])
    assert vector(16,bc=1,de=0x6200)[1]==9 and vector(16,bc=7)[1]==7
    vector(9,c=1)
    for track,sector,rawpos in [(4,0,OFFSET),(76,63,len(guest.drives[1])-128)]:
        vector(10,bc=track);vector(11,bc=sector);vector(12,bc=0x7000)
        assert vector(13)[0]==0
        assert bytes(mem[0x7000:0x7080])==guest.drives[1][rawpos:rawpos+128]
    checks['0449-0450,0453-0454,0456-0457']='Deferred selection, absent E:, XLT[1]=9, null XLT[7]=7, OFF=4 and final record'
    # With CRT selected, raw Function 6 emits TAB verbatim. Formatted 2/9
    # share the column, expanding the next TAB to the eighth position.
    guest.output.clear()
    bdos(2,13);bdos(2,ord('A'));mem[0x6200:0x6205]=b'B\tC$!';bdos(9,0x6200)
    assert bytes(guest.output)==b'\rAB'+b' '*6+b'C'
    guest.output.clear()
    for char in (65,9,19,16):bdos(6,char)
    assert bytes(guest.output)==b'A\t\x13\x10' and bdos(6,255)==0
    checks['0059-0062,0075-0078,0081-0082']='Formatted 2/9 share columns; direct emits A, TAB, XOFF and DLE unchanged'
    delay = C.c_int.in_dll(library,'defer_after_first')
    polls = C.c_uint.in_dll(library,'deferred_polls')
    for fn in (2,9):
        guest.output.clear()
        mem[0x6200:0x6202]=b'X$'
        delay.value, polls.value = 1,0
        library.type_keys(b'\x13\x11',2)
        bdos(fn,ord('X') if fn==2 else 0x6200)
        delay.value=0
        assert bytes(guest.output)==b'X' and polls.value==64
    for i in range(256):
        bdos(8,i)
        assert mem[3]==i and bdos(7)==i
    checks['0063-0064,0445']='XOFF/XON before formatted output; all 256 IOBYTE values round-trip'
    bdos(8,0x95)
    bdos(26,0x7400)
    guard=bytes(range(128))
    mem[0x7400:0x7480]=guard
    mem[0x80:0x100]=guard[::-1]
    dma_addr=symbols(out.parent/'bdos/bdos.lst')['UB_DMA']
    library.type_keys(b'K',1)
    guest.output.clear()
    assert vector(2)[0]==255 and vector(2)[0]==255 and vector(3)[0]==ord('K') and not guest.output
    library.type_keys(b'K',1)
    assert bdos(1)==ord('K') and bytes(guest.output)==b'K'
    for n in (4,5,6):vector(n,c=9)
    assert vector(7)[0]==0x1a
    assert word(dma_addr)==0x7400 and bytes(mem[0x7400:0x7480])==guard and bytes(mem[0x80:0x100])==guard[::-1]
    punch = bios+18
    saved = bytes(mem[punch:punch+3])
    mem[punch:punch+3] = b'\xc3\x00\x57'
    mem[0x5700:0x5705] = b'\x79\x32\x60\x58\xc9'
    guest.output.clear()
    for literal in (65,9,16):
        bdos(4,literal)
        assert mem[0x5860]==literal and not guest.output
    mem[punch:punch+3]=saved
    checks['0439']='Function 4 delivered all three unmodified bytes to the instrumented BIOS PUNCH entry'
    checks['0448,0473,0600,0606']='direct input without echo, BDOS echo and unchanged DMA address and guards'
    return checks


def check(out, folder, z80pack, packet):
    window = WINDOW.replace('int enable =', 'if(port!=0xff)return;\n    int enable =')
    shim = SHIM[:SHIM.index('BYTE io_in')] + window + KEYS + SHIM[SHIM.index('void end_bus_request'):] + ADVANCE
    library = cpu_library(folder,z80pack,shim)
    system = (out/'Model-II-System-candidate.imd').read_bytes()
    root = Path(__file__).resolve().parents[1]
    fixtures = root/'tests/fixtures/conformance'
    asm = Path.home()/'bin/z80asm'
    def probe(name, source):
        return compiled(asm,folder,name,source)
    mark = (fixtures/'ccpmark.mac').read_text()
    helpers = [(name+'.COM',probe(name,(fixtures/source).read_text()))
               for name,source in [('BDOPROBE','bdos-manual-probes.mac'),('STATE','returnstate.mac'),
                                   ('MORECHAR','morechar.mac'),('FAULTIO','faultmore.mac')]]
    # Retain the actual 12-byte first default FCB independently of tail spelling.
    mark = mark.replace('        RET\nHEX:', """        LD DE,FCBMSG
        LD C,9
        CALL 5
        LD HL,5CH
        LD B,12
FCBOUT: LD A,(HL)
        PUSH HL
        PUSH BC
        CALL HEX
        POP BC
        POP HL
        INC HL
        DJNZ FCBOUT
        RET
FCBMSG: DB 'FCB=','$'
HEX:""",1)
    helpers.append(('MARK.COM',probe('MARK',mark.replace('@ID@','NAME'))))
    boot_probe = (fixtures/'bootmore.mac').read_text().replace("DB 1,'BTONE   DAT'","DB 3,'BTONE   DAT'")
    helpers += [('BOOTMORE.COM',probe('BOOTMORE',boot_probe)),('BTONE.DAT',b'ONE'),('BTEMPTY.DAT',b'')]

    live_base=symbols(out/'gateway.lst')['ECB_CCPBASE']
    overwrite=f""" ORG 100H
 LD HL,(0{live_base:04X}H)
 LD A,H
 CP 80H
 JR C,BAD
 CP 0E1H
 JR NC,BAD
 LD SP,7000H
 LD B,16
PAINT: LD (HL),0A5H
 INC HL
 DJNZ PAINT
 LD DE,OK
 LD C,9
 CALL 5
 JP 0
BAD: RET
OK: DB 'PAINTED LIVE CCP',13,10,'$'
 END
"""
    helpers.append(('PAINT.COM',probe('PAINT',overwrite)))
    no_run = probe('WRONG',mark.replace('@ID@','WRONG'))
    user_files = [('PROBE.TXT',b'first line\r\nlast line\x1a'),('BTRO.DAT',b'protected'),
                  ('BTONE.DAT',b'HEALTHY READ AFTER ABORT\r\n\x1a')]
    terminals = terminal_cases(library,out,packet,system) if packet else {}
    direct_checks = public_calls(library,out,system)
    row_result = suite_rows(library,out,packet,system) if packet else {}
    session = Session(library,out,[system,disk(user_files),disk(helpers),disk()])
    outputs = {}
    def command(text, witness):
        trace = session.step(text.encode()+b'\r',witness)
        output = trace.partition(b'\r\n')[2].decode('ascii')
        outputs[text] = output
        return output
    command('CPX LIST',b'RCP.CPX')
    command('B:',b'B0>')
    for line in ('',' ','   '):
        assert '?' not in command(line,b'B0>')
    partial=session.step(b'C0:MARK mIxEd.TxX\x08T',b'C0:MARK mIxEd.TxT')
    assert b'MARK NAME DU' not in partial
    executed=session.step(b'\r',b'MARK NAME DU B/00 TAIL[ mIxEd.TxT]')
    assert b'FCB=004D49584544202020545854' in executed
    outputs['case-preserving edit and FCB']=executed.decode()
    command('c0:maRk A:b?.TxT',b'FCB=01423F202020202020545854')
    command('C0:MARK B:ab*.c?m',b'FCB=0241423F3F3F3F3F3F433F4D')
    for bad in ('C0:MARK.TXT','C0:MARK.COM','C0:MARK\tBAD'):
        assert 'MARK NAME DU' not in command(bad,b'B0>')
    command('C0:MARK TEST',b'MARK NAME DU B/00')
    command('C0:PAINT',b'PAINTED LIVE CCP')
    command('C0:STATE',b'STATE D=01 U=00 TOP=E101')
    command('C0:BOOTMORE W',b'B0>')
    command('C0:BOOTMORE V',b'0595 P R')
    command('C0:BOOTMORE C',b'A0>')
    command('C0:BOOTMORE V',b'0593 P R')
    command('B:',b'B0>')
    command('A0:STAT DEV:',b'CRT')
    command('A0:STAT LST:=CRT:',b'B0>')
    assert session.ram[3]==0x55
    command('A0:STAT CON:=ZZZ:',b'Invalid Assignment')
    assert session.ram[3]==0x55
    command('A0:STAT LST:=LPT:',b'B0>')
    assert session.ram[3]==0x95
    for user in range(16):
        command(f'USER {user}',f'B{user}>'.encode())
        command('C0:STATE',f'STATE D=01 U={user:02X} TOP=E101'.encode())
    command('USER 0',b'B0>')
    command('C0:BDOPROBE',b'0420 INPUT READY')
    data = session.step(b'BUFFER42\r',b'OR-0519 PASS:')
    assert b'OR-0420 PASS:' in data and b'FAIL' not in data
    outputs['BDOPROBE result'] = data.decode()
    command('B:',b'B0>')
    command('C0:MORECHAR',b'0440 P R')
    for card in ('0065','0066','0079','0102','0436','0438','0440'):
        assert card+' P R' in outputs['C0:MORECHAR'], (card,outputs['C0:MORECHAR'])
    command('C0:ABSENT',b'B0>')
    command('C0:STATE',b'STATE D=01 U=00 TOP=E101')
    command('DIR PROBE.TXT',b'PROBE    TXT')
    before = bytes(session.drives[1])
    for cmd in ('ERA BTRO.DAT','REN BTRO.DAT LOST.TXT'):
        command(cmd,b'B0>')
        assert bytes(session.drives[1])==before, cmd
    command('REN PROBE.TXT NEW.TXT',b'B0>')
    command('TYPE NEW.TXT',b'first line\r\nlast line')
    command('ERA NEW.TXT',b'B0>')
    command('DIR NEW.TXT',b'NO FILE')
    for cmd in ('DIR MISSING.TXT','ERA MISSING.TXT','REN MISSING.TXT NEW.TXT','TYPE MISSING.TXT'):
        command(cmd,b'NO FILE')
    command('SAVE X BAD.COM',b'? SAVE')
    command('C0:STATE',b'STATE D=01 U=00 TOP=E101')
    for offset in range(0,256,16):
        cmd='POKE %04X '%(0x100+offset)+' '.join('%02X'%v for v in range(offset,offset+16))
        session.step(cmd.encode()+b'\r',b'B0>')
    command('SAVE 1 PAGE.BIN',b'B0>')
    tools = {'cpmcp':{'path':str((CPMTOOLS/'cpmcp').resolve())}}
    (folder/'diskdefs').write_text(DISKDEFS)
    cpm('cpmcp',[normalized(session.drives[1],folder),'0:page.bin',folder/'page.bin'],folder,folder/'diskdefs',tools)
    assert (folder/'page.bin').read_bytes()==bytes(range(256))
    outputs['SAVE host readback'] = hashlib.sha256(bytes(range(256))).hexdigest()
    before = bytes(session.drives[1])
    command('ERA *.*',b'ALL (Y/N)?')
    session.step(b'N\r',b'B0>')
    assert bytes(session.drives[1])==before
    text_payload=b'ECOLOGY\x07\r\n'+b'Z'*116+b'\r\n'
    session=Session(library,out,[system,disk([('PUBLIC.TXT',text_payload),('HIDDEN.TXT',b'SYS'),('OTHER.TXT',b'USER7',7)])])
    session.drives[1][OFFSET+32+10] |= 128
    command('B:',b'B0>')
    assert 'HIDDEN' not in command('DIR *.TXT',b'PUBLIC   TXT')
    assert 'HIDDEN' not in command('DIR',b'PUBLIC   TXT')
    assert 'HIDDEN' not in command('DIR HIDDEN.TXT',b'B0>')
    command('DIR OTHER.TXT',b'NO FILE')
    command('USER 7',b'B7>')
    command('DIR OTHER.TXT',b'OTHER    TXT')
    command('USER 0',b'B0>')
    command('DIR A:SYSTEM.SYS',b'SYSTEM   SYS')
    assert text_payload.decode() in command('TYPE PUBLIC.TXT',text_payload)
    command('REN PUBLIC.TXT OTHER.TXT',b'B0>')  # same name in another user is permitted
    command('TYPE OTHER.TXT',text_payload)
    command('REN B:X.TXT=A:PATH.COM',b'Invalid filespec.')
    command('REN X.TXT=MISSING.TXT',b'NO FILE')
    command('SAVE 1 PRESENT.TXT',b'B0>')
    command('REN PRESENT.TXT=OTHER.TXT',b'FILE EXISTS')
    command('ERA PRES*.TXT',b'B0>')
    command('DIR PRESENT.TXT',b'NO FILE')
    command('ERA *.*',b'ALL (Y/N)?')
    session.step(b'Y\r',b'B0>')
    raw=session.drives[1]
    assert raw[OFFSET]==0xe5 and raw[OFFSET+32]==0 and raw[OFFSET+64]==7
    # Prove that names matching resident commands do not invoke a colliding COM.
    session = Session(library,out,[system,disk(user_files+[(n+'.COM',no_run) for n in ('DIR','ERA','REN','SAVE','TYPE','USER','DIRX','DI')])])
    command('B:',b'B0>')
    for cmd,witness in [('DIR PROBE.TXT',b'PROBE    TXT'),('TYPE PROBE.TXT',b'first line'),('USER 0',b'B0>'),
                        ('SAVE X FILE.DAT',b'? SAVE'),('REN PROBE.TXT R.TXT',b'B0>'),('ERA R.TXT',b'B0>')]:
        assert 'MARK WRONG' not in command(cmd,witness)
    assert 'BTRO' in command('DIR *.DAT',b'BTRO')
    command('ERA *.*',b'ALL (Y/N)?')
    session.step(b'N\r',b'B0>')
    assert 'BTRO' in command('DIR BTRO.DAT',b'BTRO')
    for cmd in ('DI','DIRX'):
        command(cmd,b'MARK WRONG DU B/00')
    # CONFIG writes BCST records to A. Fail once after dirtying the requested
    # sector, so only a real restored record can make the whole-disk oracle pass.
    rollback=[]
    for failure in ([1],[2],[1,2]):
        session = Session(library,out,[system])
        command('CONFIG /STARTUP="NEW COMMAND"',b'Save pending cold-boot changes')
        before = bytes(session.drives[0])
        session.fail_writes = [session.write_count+n for n in failure]
        witness = b'Boot disk may be damaged' if len(failure)==2 else b'Original startup defaults restored'
        trace = session.step(b'Y',witness)
        equal = bytes(session.drives[0])==before
        assert equal==(len(failure)==1) and b'saved and verified' not in trace
        rollback.append({'failed_writes':failure,'message':witness.decode(),'disk_restored':equal,'physical_writes':session.writes})
    return {'scope':'Model II CPU with controlled keyboard and physical-sector transfer. Real filesystem, BIOS mapping, CCP, CONFIG and BDOS. Physical controller retries are qualified separately.',
            'system_sha256':hashlib.sha256(system).hexdigest(),'suite_revision':SUITE_REV,'suite_rows':row_result,
            'checks':outputs,'public_calls':direct_checks,'terminal_cases':terminals,'config_rollback':rollback}



if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifacts',type=Path)
    p.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    p.add_argument('--packet',type=Path)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        report = check(args.artifacts,Path(tmp),args.z80pack,args.packet)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Model II controlled system tests', args.report)
