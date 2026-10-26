#!/usr/bin/env python3
"""Focused complete SEARCH execution on disposable BetterCP/M platform media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from test_z80pack_sysgen_install import session
from test_disk_utilities import keys
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from search_source import ROOT
from build_ccp import assemble

PROMPT = 'Space/Enter: next page; Ctrl-C: stop display'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--model4-image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--target', choices=('both','cpmsim','model4'), default='both')
    parser.add_argument('--qualification', action='store_true',
                        help='Add large-directory and native stack-watermark checks')
    args = parser.parse_args()
    work = args.report.resolve()
    work.mkdir(parents=True, exist_ok=False)
    binary = (ROOT/'build/utilities/SEARCH.COM').read_bytes()
    fixture = b'4142 AB 4142\r\n'+b'\x1a'*114
    pages = b'X\r\n'*80+b'\x1a'*16
    files = [('SEARCH.COM', binary, '0:SEARCH.COM'), ('FIX.DAT', fixture, '3:FIX.DAT'),
             ('FIX.DAT', fixture, '31:FIX.DAT'), ('PAGES.TXT', pages, '0:PAGES.TXT')]
    evidence = {'binary_sha256':hashlib.sha256(binary).hexdigest(),
                'scope':'focused complete-command platform checks; not release promotion'}
    if args.target in ('both','cpmsim'):
        evidence['cpmsim_system_input_sha256'] = hashlib.sha256((args.image_dir/'disks/drivea.dsk').read_bytes()).hexdigest()
        w = work/'cpmsim'
        w.mkdir()
        shutil.copytree(args.image_dir/'disks', w/'disks')
        shutil.copy2(args.image_dir/'diskdefs', w/'diskdefs')
        disk = w/'disks/drivea.dsk'
        def cpm(tool, *arguments):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,arguments)],
                           cwd=w, check=True, stdout=subprocess.DEVNULL)
        cpm('cpmrm','0:*.*')
        for name, payload, destination in files:
            path = w/name
            path.write_bytes(payload)
            cpm('cpmcp',path,destination)
        if args.qualification:
            from qualify_search_native import probe
            path = w/'PROBE.COM'
            path.write_bytes(probe(binary,(ROOT/'build/utilities/search.lst').read_text(),w,8192))
            cpm('cpmcp',path,'0:PROBE.COM')
            path = w/'EMPTY.TXT'
            path.write_bytes(b'.'*128)
            for i in range(56):
                cpm('cpmcp',path,f'5:F{i:07}.TXT')
        before = disk.read_bytes()
        commands = [(b':SEARCH /VER /HELP\r', b'A0>_ ',30),
                    (b':SEARCH "4142" [A3,A31]:FIX.DAT\r', b'A0>_ ',30),
                    (b':SEARCH "X" A0:PAGES.TXT /NOHEX /P\r', PROMPT.encode(),30),
                    (b'\x03', b'A0>_ ',30)]
        if args.qualification:
            commands += [(b':SEARCH "Z" A5:*.TXT /NOHEX\r', b'A0>_ ',60),
                         (b'PROBE "X" A0:PAGES.TXT /NOHEX /P\r',PROMPT.encode(),30),
                         (b'\x03',b'A0>_ ',30)]
        text = session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim', w/'disks', commands, w/'transcript.txt')
        for marker in (b'Usage: SEARCH', b'A3:FIX.DAT [TEXT] line 1:', b'A31:FIX.DAT [HEX] offset 00000005',
                       b'Files searched: 2', b'Total matches: 6', b'DISPLAY INTERRUPTED',
                       b'SEARCH CONTINUING...', b'Total matches: 80'):
            assert marker in text, (marker,text[-2000:])
        assert disk.read_bytes() == before, 'SEARCH changed cpmsim media'
        evidence['cpmsim'] = {'result':'PASS','whole_disk_unchanged':True}
        if args.qualification:
            import re
            assert b'Files searched: 56' in text
            watermark = re.search(rb'PROBE STACK USED HEX: ([0-9A-F]+) GUARD OK',text)
            assert watermark, text[-2000:]
            evidence['cpmsim_resources'] = {'directory_files':56,
                'advertised_tpa_payload_bytes':8192,'stack_watermark_bytes':int(watermark[1],16)}
            # Keep the directory/allocation valid and truncate a separate data
            # drive below its late file: force an actual BIOS transfer failure.
            fault_disk = w/'disks/driveb.dsk'
            def fcpm(tool,*arguments):
                subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(fault_disk),*map(str,arguments)],
                               cwd=w,check=True,stdout=subprocess.DEVNULL)
            fcpm('cpmrm','0:*.*')
            filler = w/'FILL.DAT'
            filler.write_bytes(b'.'*65536)
            fcpm('cpmcp',filler,'0:FILL.DAT')
            fcpm('cpmcp',w/'PAGES.TXT','0:FAULT.TXT')
            damaged = fault_disk.read_bytes()[:50000]
            fault_disk.write_bytes(damaged)
            fault = session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',
                            [(b':SEARCH "X" B0:FAULT.TXT /NOHEX\r',b'Bad Sector',30),
                             (b'\x03',b'B0>_ ',30)],w/'bad-sector.txt')
            assert b'Total matches:' not in fault
            assert fault_disk.read_bytes() == damaged and disk.read_bytes() == before
            evidence['cpmsim_bad_sector'] = 'BDOS prompt and Ctrl-C warm boot; no SEARCH totals, disk unchanged'
        print('PASS BetterCP/M cpmsim: queries, user 3/31 selection, dual results, paging stop, immutable disk', flush=True)
    if args.target in ('both','model4'):
        evidence['model4_system_input_sha256'] = hashlib.sha256(args.model4_image.read_bytes()).hexdigest()
        w = work/'model4'
        w.mkdir()
        raw = w/'system.raw'
        raw.write_bytes(extract_raw(args.model4_image.read_bytes()))
        (w/'diskdefs').write_text('diskdef search-system\n libdsk:format pcw800\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
        def mtool(tool, *arguments):
            subprocess.run([tool,'-T','raw','-f','search-system',str(raw),*map(str,arguments)],
                           cwd=w, check=True, stdout=subprocess.DEVNULL)
        mtool('cpmrm','0:STARTUP.SUB')
        hold_source = """        ORG 0100H
        LD DE,HMSG
        LD C,9
        CALL 5
HWAIT:
        LD E,255
        LD C,6
        CALL 5
        OR A
        JR Z,HWAIT
        RET
HMSG: DB 13,10,'SEARCH TEST STEP',13,10,'$'
        END
"""
        if args.qualification:
            hold_source = hold_source.replace('''HWAIT:
        LD E,255
        LD C,6
        CALL 5
        OR A
        JR Z,HWAIT''','''HWAIT:
        LD C,1
        CALL 5''')
        hold = assemble(Path.home()/'bin/z80asm',hold_source,w/'hold.bin',w/'hold.lst',0x100)
        startup = (b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n'
                   b':SEARCH "4142" A31:FIX.DAT\r\nHOLD\r\n'
                   b':SEARCH "X" A0:PAGES.TXT /NOHEX /P\r\n\x1a')
        additions = []
        if args.qualification:
            from qualify_search_native import probe
            listing = (ROOT/'build/utilities/search.lst').read_text()
            additions.append(('PROBE.COM',probe(binary,listing,w,8192),'0:PROBE.COM'))
            hold2 = assemble(Path.home()/'bin/z80asm',hold_source.replace('SEARCH TEST STEP','SEARCH DIRECTORY STEP'),
                             w/'hold2.bin',w/'hold2.lst',0x100)
            additions.append(('HOLD2.COM',hold2,'0:HOLD2.COM'))
            additions += [(f'F{i:07}.TXT',b'.'*128,f'5:F{i:07}.TXT') for i in range(80)]
            startup = (b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n'
                       b':SEARCH "4142" A31:FIX.DAT\r\nHOLD\r\n\x1a')
        for name, payload, destination in files+additions+[('STARTUP.SUB',startup,'0:STARTUP.SUB'),('HOLD.COM',hold,'0:HOLD.COM')]:
            path = w/name
            path.write_bytes(payload)
            mtool('cpmcp',path,destination)
        original = make_dmk(raw.read_bytes())
        disk = w/'a.dmk'
        disk.write_bytes(original)
        command = [str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-sx','-sfmute','-ktx','-d0',str(disk),
                   '-itime','60000']
        if args.qualification:
            # Independent boots avoid a keyboard-dependent handoff between
            # test pauses. Physical input is used only for SEARCH's own pager.
            prefix = command
            all_texts = []
            for step, script, actions in [
                ('results',startup,['-iw','SEARCH TEST STEP','-it','-ix']),
                ('directory',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n:SEARCH "Z" A5:*.TXT /NOHEX\r\nHOLD2\r\n\x1a',
                 ['-iw','SEARCH DIRECTORY STEP','-it','-ix']),
                ('resources',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nPROBE "X" A0:PAGES.TXT /NOHEX /P\r\n\x1a',
                 ['-iw',PROMPT,'-it']+keys('\x03')+['-iw','GUARD OK','-id','60','-it','-ix']),
            ]:
                (w/'STARTUP.SUB').write_bytes(script)
                mtool('cpmrm','0:STARTUP.SUB')
                mtool('cpmcp',w/'STARTUP.SUB','0:STARTUP.SUB')
                disk.write_bytes(make_dmk(raw.read_bytes()))
                stepdir = w/step
                stepdir.mkdir()
                invocation = prefix+actions
                (stepdir/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
                run(invocation,cwd=stepdir,timeout=90,check=True)
                captures = sorted(stepdir.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))
                for capture in captures:
                    text = screen(capture)
                    capture.with_suffix('.txt').write_text(text)
                    all_texts.append(text)
            texts = all_texts
        else:
            command += ['-iw','SEARCH TEST STEP','-it']+keys('\r')+['-iw',PROMPT,'-it']
            command += keys('\x03')+['-iw','SEARCH CONTINUING...','-iw','Total matches: 80','-id','60','-it','-ix']
            (w/'invocation.json').write_text(json.dumps(command,indent=2)+'\n')
            run(command,cwd=w,timeout=90,check=True)
            captures = sorted(w.glob('trs80-text-*.bin'), key=lambda f:int(f.stem.rsplit('-',1)[1]))
            texts = [screen(path) for path in captures]
            for path, text in zip(captures,texts):
                path.with_suffix('.txt').write_text(text)
        assert len(texts) == (4 if args.qualification else 3), len(texts)
        if args.qualification:
            assert 'Files searched: 80' in texts[1] and 'Total matches: 0' in texts[1], texts[1]
            import re
            watermark = re.search(r'PROBE STACK USED HEX: ([0-9A-F]+) GUARD OK',texts[-1])
            assert watermark, texts[-1]
            evidence['model4_resources'] = {'directory_files':80,
                'advertised_tpa_payload_bytes':8192,
                'stack_watermark_bytes':int(watermark[1],16),
                'limits':'Exercised native stack watermark; not a physical interrupt worst-case proof'}
            texts = [texts[0],texts[2],texts[3]]
        assert 'A31:FIX.DAT [TEXT] line 1:' in texts[0] and 'A31:FIX.DAT [HEX] offset 00000005' in texts[0], texts[0]
        assert 'Total matches: 3' in texts[0] and 'Files searched: 1' in texts[0]
        assert PROMPT in texts[1], texts[1]
        assert 'DISPLAY INTERRUPTED' in texts[2] and 'Total matches: 80' in texts[2], texts[2]
        # SUBMIT itself creates/deletes its command spool. Check the searched
        # fixture bytes rather than claiming the whole boot/script disk is immutable.
        raw.write_bytes(extract_raw(disk.read_bytes()))
        for user, name, payload in ((3,'FIX.DAT',fixture),(31,'FIX.DAT',fixture),(0,'PAGES.TXT',pages)):
            restored = w/f'{user}-{name}'
            mtool('cpmcp',f'{user}:{name}',restored)
            assert restored.read_bytes() == payload, (user,name,'content changed')
        evidence['model4'] = {'result':'PASS','fixture_contents_unchanged':True,
                              'whole_disk_unchanged':'not asserted: startup SUBMIT writes its spool'}
        print('PASS Model 4: user 31 selection, dual results, Ctrl-C display stop, unchanged searched files', flush=True)
    (work/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')


if __name__ == '__main__':
    main()
