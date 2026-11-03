#!/usr/bin/env python3
"""Build a self-starting CAPS diagnostic for the unchanged 37fa57a draft.

No emulator is launched by this builder. The standalone launcher contains its
test disk, uses the installed app's real bundle, and requests a new instance.
The monitor reads the private CAPS byte only after checking the draft scanner;
keyboard status and returned characters use the actual public BIOS vectors.
"""
import argparse
import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import zlib

from add_cpm_file_to_dmk import add_file, extract_raw
from build_ccp import assemble
from build_montezuma_extended_790k import build, verify
from startup_record import build as startup_record, parse as parse_startup
from system_layout import LAYOUT
from test_bios import Z80
from test_monitor_profiles import load

ROOT = Path(__file__).resolve().parents[1]
DRAFT = '37fa57a1310f771227115fd269ef224e411ace1d'
BIOS_SHA = 'c7b8150ce55ae151880de64ab38ed4f873d3080ea5589be090253a1461a8ab4c'
SOURCE_IMAGE = ROOT / 'build/model4-keyboard-test-37fa57a/BetterCPM-Model4-Lowercase-37fa57a.dmk'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(cpu, labels):
    scan = labels['M4_SCAN']
    signature = bytes(cpu.mem[scan:scan+16])
    return f'''        ASEG
        ORG 0100H
        LD SP,STACKTOP
        LD HL,0F800H
        LD DE,0F801H
        LD BC,1919
        LD (HL),' '
        LDIR
        LD HL,(1)
        LD DE,0{LAYOUT['BIOS']+3:04X}H
        OR A
        SBC HL,DE
        JP NZ,BADBIOS
        LD HL,0{scan:04X}H
        LD DE,SIGNATURE
        LD B,16
GUARD:  LD A,(DE)
        CP (HL)
        JP NZ,BADBIOS
        INC DE
        INC HL
        DJNZ GUARD
        LD HL,TITLE
        LD DE,0F800H
        CALL TEXT
        LD HL,GUIDE
        LD DE,0F850H
        CALL TEXT
        LD HL,STATES
        LD DE,0F8A0H
        CALL TEXT
        LD HL,HEADER
        LD DE,0F940H
        CALL TEXT
LOOP:   XOR A
        LD (NEWBYTE),A
        CALL 0{LAYOUT['BIOS']+6:04X}H
        OR A
        JR Z,SAMPLE
        LD A,1
        LD (NEWBYTE),A
        CALL 0{LAYOUT['BIOS']+9:04X}H
        LD (CURRENT+2),A
        CP 3
        JR NZ,SAMPLE
        LD A,1
        LD (FINISHED),A
SAMPLE: LD A,(0F480H)
        LD (CURRENT),A
        LD A,(0{labels['M4_KSTATE']:04X}H)
        LD (CURRENT+1),A
        LD A,(NEWBYTE)
        OR A
        JR NZ,CHANGED
        LD HL,CURRENT
        LD DE,PREVIOUS
        LD B,3
COMPARE:LD A,(DE)
        CP (HL)
        JR NZ,CHANGED
        INC HL
        INC DE
        DJNZ COMPARE
        JR CHECKEND
CHANGED:LD HL,CURRENT
        LD DE,PREVIOUS
        LD BC,3
        LDIR
        CALL ROW
CHECKEND:
        LD A,(FINISHED)
        OR A
        JP NZ,0
        JR LOOP
BADBIOS:
        LD HL,BADMSG
        LD DE,0F800H
        CALL TEXT
        JP 0
TEXT:   LD A,(HL)
        OR A
        RET Z
        LD (DE),A
        INC DE
        INC HL
        JR TEXT
ROW:    LD HL,(POSITION)
        LD DE,0FF80H
        OR A
        SBC HL,DE
        JR C,ROWOK
        LD HL,0F990H
        LD (POSITION),HL
ROWOK:  LD HL,(POSITION)
        LD D,H
        LD E,L
        INC DE
        LD BC,79
        LD (HL),' '
        LDIR
        LD DE,(POSITION)
        LD HL,CURRENT
        LD B,3
FIELDS: LD A,(HL)
        CALL HEXBYTE
        LD A,' '
        LD (DE),A
        INC DE
        INC HL
        DJNZ FIELDS
        LD HL,(POSITION)
        LD DE,80
        ADD HL,DE
        LD (POSITION),HL
        RET
HEXBYTE:CP 0FFH
        JR NZ,HASBYTE
        LD A,'-'
        LD (DE),A
        INC DE
        LD (DE),A
        INC DE
        RET
HASBYTE:PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIBBLE
        POP AF
NIBBLE: AND 15
        ADD A,'0'
        CP ':'
        JR C,DIGIT
        ADD A,7
DIGIT:  LD (DE),A
        INC DE
        RET
TITLE:  DB 'CAPS TRACE 37FA57A - PUBLIC BIOS INPUT',0
GUIDE:  DB 'Type a; tap CAPS once, release, type a; repeat. Ctrl-C exits.',0
STATES: DB 'STATE: 20/28=lowercase, 00/08=uppercase. RAW bit 08=CAPS held.',0
HEADER: DB 'RAW STATE LAST-BYTE (hex; -- means no input yet)',0
BADMSG: DB 'BIOS mismatch: this diagnostic requires the unchanged 37fa57a draft.',0
SIGNATURE: DB {','.join(f'0{b:02X}H' for b in signature)}
CURRENT: DB 0,0,0FFH
PREVIOUS: DB 0FFH,0FFH,0FFH
FINISHED: DB 0
NEWBYTE: DB 0
POSITION: DW 0F990H
        DS 128
STACKTOP:
        END
'''


class Finished(Exception):
    pass


class MatrixFrames(bytearray):
    def __getitem__(self, address):
        if address == 0 and self.cpu.pc == 0:
            raise Finished
        if address == self.scan and self.cpu.pc == self.scan:
            if not self.frames:
                raise AssertionError('Diagnostic requested unexpected extra input')
            modifiers, row0 = self.frames.pop(0)
            self[0xF480] = modifiers
            self[0xF401] = row0
        return super().__getitem__(address)


def execute_frames(program, labels, frames, *, wrong_bios=False):
    cpu, _ = load(ROOT/'build/bios')
    cpu.run(labels['MONBASE'])
    cpu.mem[3] = 0x55                 # Production boot selects CRT console/list.
    cpu.mem[0x100:0x100+len(program)] = program
    cpu.setword(1, LAYOUT['BIOS']+3)
    cpu.mem = MatrixFrames(cpu.mem)
    cpu.mem.cpu, cpu.mem.scan = cpu, labels['M4_SCAN']
    cpu.mem.frames = list(frames)
    if wrong_bios:
        cpu.mem[labels['M4_SCAN']] ^= 0xFF
    try:
        cpu.run(0x100, limit=400000)
    except Finished:
        pass
    except AssertionError as error:
        raise AssertionError(f'{error}; PC={cpu.pc:04X}, SP={cpu.sp:04X}, remaining frames={cpu.mem.frames}') from error
    else:
        raise AssertionError('Ctrl-C did not return through warm boot')
    if wrong_bios:
        assert bytes(cpu.mem[0xF800:0xF850]).startswith(b'BIOS mismatch:')
        assert cpu.mem.frames == frames
        return []
    assert not cpu.mem.frames
    rows = [bytes(cpu.mem[a:a+80]).decode('ascii').strip() for a in range(0xF990,0xFF80,80)]
    return [line for line in rows if line.strip()]


def execute_check(program, labels):
    # Actual CONST/CONIN need two scans for each pressed/released character.
    frames = [(0, 0), (0, 2), (0, 2), (0, 0)]
    for _ in range(4):
        frames += [(8, 0), (0, 0), (0, 2), (0, 2), (0, 0)]
    frames += [(4, 8), (4, 8), (0, 0)]
    actual = execute_frames(program,labels,frames)
    expected = ['00 20 --', '00 20 61', '08 08 61', '00 00 61', '00 00 41',
                '08 28 41', '00 20 41', '00 20 61', '08 08 61', '00 00 61',
                '00 00 41', '08 28 41', '00 20 41', '00 20 61', '00 20 03']
    assert actual == expected, actual
    latched = [(0,0)]
    for contact in (8,0,8,0):
        latched += [(contact,0),(contact,2),(contact,2),(contact,0)]
    latched += [(4,8),(4,8),(0,0)]
    latched_expected = ['00 20 --','08 08 --','08 08 41','00 00 41','00 00 41',
                        '08 28 41','08 28 61','00 20 61','00 20 61','00 20 03']
    assert execute_frames(program,labels,latched)==latched_expected
    execute_frames(program,labels,[(0,0)],wrong_bios=True)
    return {'status':'PASS', 'scope':'Assembled monitor executing real public CONST/CONIN; matrix events supplied by bounded instruction runner',
            'momentary_contact_rows':expected, 'momentary_returned_letter_bytes':['61','41','61','41','61'],
            'latched_contact_rows':latched_expected, 'latched_returned_letter_bytes':['41','41','61','61'],
            'latched_scope':'Controlled input model only; does not prove that macOS/trs80gp supplies a latched contact.',
            'wrong_bios_guard':'PASS'}


def launcher(image):
    # Single downloaded file, with no companion scripts or repository paths.
    payload = base64.b64encode(zlib.compress(image,9)).decode('ascii')
    code = '''import base64, hashlib, json, subprocess, sys, zlib
from pathlib import Path
from datetime import datetime
'''
    code += 'PAYLOAD = '+repr(payload)+'\nIMAGE_SHA = '+repr(sha(image))+'\n'
    code += '''image = zlib.decompress(base64.b64decode(PAYLOAD))
if hashlib.sha256(image).hexdigest() != IMAGE_SHA:
    raise SystemExit('Embedded disk checksum failed; emulator was not launched.')
if '--check' in sys.argv:
    print('PASS: standalone diagnostic disk checksum; no companion files needed; no launch.')
    raise SystemExit(0)
app = Path.home()/'trs80/trs80gp-2/mac/trs80gp.app'
if not app.is_dir():
    raise SystemExit('Installed emulator not found: '+str(app))
output = Path.home()/'Downloads'/datetime.now().strftime('BetterCPM-Caps-Monitor-%Y%m%d-%H%M%S-%f')
output.mkdir(parents=True)
disk = output/'Caps-Monitor-37fa57a.dmk'
disk.write_bytes(image)
events = output/'keyboard-events.txt'
args = ['-m4','-batch','-d0',str(disk),'-event','>'+str(events)]
record = {'status':'LAUNCH_REQUESTED_NOT_QUALIFIED','image_sha256':IMAGE_SHA,'args':args}
(output/'capture.json').write_text(json.dumps(record,indent=2)+'\\n')
print('Opening a NEW Model 4 instance on a private diagnostic disk.',flush=True)
print('The CAPS TRACE monitor starts automatically. No KEYREAD command is sent.',flush=True)
print('Type a. Then do FOUR rounds: press CAPS once, hold half a second, release, type a.',flush=True)
print('LAST-BYTE should alternate 61/41. Ctrl-C exits the monitor.',flush=True)
print('Capture the monitor screen, then quit only the new diagnostic instance.',flush=True)
print('CAPTURE DIRECTORY: '+str(output),flush=True)
subprocess.run(['/usr/bin/open','-n','-a',str(app),'--args',*args],check=True)
'''
    compile(code,'standalone-caps-monitor','exec')
    return '#!/bin/zsh\nset -eu\nexec /usr/bin/python3 - "$@" <<\'CAPS_MONITOR_PY\'\n'+code+'\nCAPS_MONITOR_PY\n'


def check_launcher(command, image):
    with tempfile.TemporaryDirectory(prefix='caps-monitor-standalone-') as directory:
        home = Path(directory)
        copy = home/command.name;copy.write_bytes(command.read_bytes())
        subprocess.run(['/bin/zsh',str(copy),'--check'],cwd=home,check=True)
        app = home/'trs80/trs80gp-2/mac/trs80gp.app';app.mkdir(parents=True)
        code = copy.read_text().split("<<'CAPS_MONITOR_PY'\n",1)[1].rsplit('\nCAPS_MONITOR_PY',1)[0]
        calls = []
        with patch('pathlib.Path.home',return_value=home),patch('subprocess.run',side_effect=lambda args,**kw:calls.append(args)),patch.object(sys,'argv',['caps-monitor']),contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code,'caps-launcher-check','exec'),{})
        assert len(calls)==1
        request = calls[0]
        assert request[:7]==['/usr/bin/open','-n','-a',str(app),'--args','-m4','-batch']
        disk = Path(request[request.index('-d0')+1])
        assert disk.read_bytes()==image
        assert request[request.index('-event')+1]=='>'+str(disk.parent/'keyboard-events.txt')
        assert '-ik' not in request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/model4-caps-monitor')
    parser.add_argument('--image',type=Path,default=SOURCE_IMAGE if SOURCE_IMAGE.exists() else ROOT/'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk')
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args = parser.parse_args()
    bios = (ROOT/'build/bios/bios.bin').read_bytes()
    original = args.image.read_bytes()
    if sha(bios)!=BIOS_SHA:
        raise SystemExit('This diagnostic is bound to the unchanged 37fa57a BIOS.')
    original_raw = extract_raw(original)
    bios_at = 1024+LAYOUT['BIOS']-LAYOUT['SYSTEM']
    if original_raw[bios_at:bios_at+len(bios)]!=bios:
        raise SystemExit('Input disk does not contain the expected 37fa57a BIOS.')
    cpu,labels = load(ROOT/'build/bios')
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    text = source(cpu,labels)
    (out/'CAPTRACE.MAC').write_text(text)
    program = assemble(args.assembler,text,out/'CAPTRACE.COM',out/'captrace.lst',0x100)
    regression = execute_check(program,labels)
    raw = bytearray(original_raw)
    original_reserved = bytes(raw[:20480])
    add_file(raw,'CAPTRACE.COM',program)
    raw[128:384] = startup_record('CAPTRACE',system_base=LAYOUT['SYSTEM'])
    assert parse_startup(raw[128:384],system_base=LAYOUT['SYSTEM'])=='CAPTRACE'
    image = build(raw);verify(image,require_blank=False)
    reread = extract_raw(image)
    assert reread[:128]==original_reserved[:128]
    assert reread[384:20480]==original_reserved[384:]
    at = 1024+LAYOUT['BIOS']-LAYOUT['SYSTEM']
    assert reread[at:at+len(bios)]==bios
    entries = [reread[p:p+32] for p in range(20480,24576,32)]
    installed = [e for e in entries if e[0]==0 and e[1:12]==b'CAPTRACECOM']
    assert len(installed)==1 and installed[0][12]==0
    record_bytes = installed[0][15]*128
    block = int.from_bytes(installed[0][16:18],'little')
    payload = reread[20480+block*2048:20480+block*2048+record_bytes]
    assert payload[:len(program)]==program and all(b==26 for b in payload[len(program):])
    allocated = []
    for entry in entries:
        if entry[0]<16:
            count = (entry[15]+15)//16
            allocated += [int.from_bytes(entry[i:i+2],'little') for i in range(16,16+2*count,2)]
    assert len(allocated)==len(set(allocated)) and all(2<=b<390 for b in allocated)
    disk = out/'Caps-Monitor-37fa57a.dmk';disk.write_bytes(image)
    command = out/'Run-Caps-Monitor.command';command.write_text(launcher(image));command.chmod(0o755)
    check_launcher(command,image)
    report = {'status':'DIAGNOSTIC_ONLY_NATIVE_INPUT_PENDING','bios_source_commit':DRAFT,
              'bios_sha256':sha(bios),'input_image_sha256':sha(original),'image_sha256':sha(image),
              'program_bytes':len(program),'program_sha256':sha(program),'cold_start':'CAPTRACE',
              'disk_readback_and_allocation':'PASS','standalone_packaging_and_launch_request':'PASS (launch API mocked)',
              'instruction_test':regression,'native_execution':'NOT STARTED',
              'interpretation':'RAW is F480h sampled after the public BIOS call; STATE is the draft CAPS byte; LAST-BYTE is the last actual CONIN return, retained on state-only rows. Values are sampled, not a continuous bus trace. Screen rows wrap after 19 records.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert args.image.read_bytes()==original
    print(json.dumps({'launcher':str(command),'disk':str(disk),'regression':regression['status'],'bios_unchanged':True}))


if __name__=='__main__':
    main()
