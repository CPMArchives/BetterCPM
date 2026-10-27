#!/usr/bin/env python3
"""Focused CRC commands on disposable BetterCP/M cpmsim and Model 4 media."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
from test_z80pack_sysgen_install import session
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from test_sysgen_install import screen
from build_ccp import assemble
from build_crc import ROOT
from test_crc import oracle


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--model4-image', type=Path, required=True)
    p.add_argument('--historical-volume', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--target', choices=('both','cpmsim','model4'), default='both')
    a = p.parse_args()
    report = a.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    binary = (ROOT/'build/utilities/CRC.COM').read_bytes()
    fixture = b'123456789'+b'\x1a'*119
    large = bytes(range(256))*257  # 514 records, includes high bits and 1Ah.
    expected = '  '.join(f'{x:0{8 if i==3 else 4}X}'.rjust(5 if i==1 else 0)
                         for i,x in enumerate(oracle(large)))
    files = [('CRC.COM',binary,'0:CRC.COM'), ('FIX.DAT',fixture,'31:FIX.DAT'),
             ('LARGE.DAT',large,'3:LARGE.DAT')]
    for name in ('ZMD146.LBR','ZMDOVL2.LBR','-CATALOG.310'):
        files.append((name,(a.historical_volume/name).read_bytes(),'7:'+name))
    evidence = {'binary_sha256':hashlib.sha256(binary).hexdigest(),
                'large_fixture_records':len(large)//128,
                'scope':'focused development qualification; release media unchanged'}
    if a.target in ('both','cpmsim'):
        w = report/'cpmsim'
        w.mkdir()
        shutil.copytree(a.image_dir/'disks',w/'disks')
        shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
        disk = w/'disks/drivea.dsk'
        def cpm(tool,*args):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],
                           cwd=w,check=True,capture_output=True)
        cpm('cpmrm','0:*.*')
        for name,payload,destination in files:
            path = w/name
            path.write_bytes(payload)
            cpm('cpmcp',path,destination)
        commands = [
            (b':CRC /HELP /VER\r',b'A0>_ ',30),
            (b':CRC A7:*.LBR /LOCAL=CRC.LST\r',b'A0>_ ',30),
            (b':CRC /CHECK A7:*.LBR\r',b'A0>_ ',30),
            (b':CRC /CHECK=-CATALOG.310 A7:*.LBR\r',b'A0>_ ',30),
            (b':CRC A3:LARGE.DAT /LOCAL=CRC.LST\r',b'A0>_ ',30),
            (b':CRC /CHECK A3:LARGE.DAT\r',b'A0>_ ',30),
            (b':CRC A31:FIX.DAT /LEGACY /LOCAL=CRC.LST\r',b'A0>_ ',30),
            (b':CRC /CHECK A31:FIX.DAT\r',b'A0>_ ',30)]
        text = session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',
                       commands,w/'transcript.txt').decode('ascii',errors='replace')
        assert text.count('Verification complete:')==4,text[-4000:]
        assert '136B   A548  D24B  82A2F154' in text and 'B06D   6B36  C153  DE35205C' in text
        assert expected in text, expected
        for name,payload,destination in files:
            out = w/('READ-'+name)
            cpm('cpmcp',destination,out)
            assert out.read_bytes()[:len(payload)]==payload,(destination,'changed')
        evidence['cpmsim'] = 'PASS: queries, all algorithms, >64K, original catalog, native/legacy lists, user31, unchanged inputs'
        print(evidence['cpmsim'],flush=True)
    if a.target in ('both','model4'):
        w = report/'model4'
        w.mkdir()
        raw = w/'system.raw'
        raw.write_bytes(extract_raw(a.model4_image.read_bytes()))
        (w/'diskdefs').write_text('diskdef crc-system\n libdsk:format pcw800\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
        def cpm(tool,*args):
            subprocess.run([tool,'-T','raw','-f','crc-system',str(raw),*map(str,args)],
                           cwd=w,check=True,capture_output=True)
        cpm('cpmrm','0:STARTUP.SUB')
        hold = assemble(Path.home()/'bin/z80asm',"""        ORG 0100H
        LD DE,MSG
        LD C,9
        CALL 5
WAIT:   JR WAIT
MSG:    DB 13,10,'CRC TEST DONE',13,10,'$'
        END
""",w/'hold.bin',w/'hold.lst',0x100)
        for name,payload,destination in files+[('HOLD.COM',hold,'0:HOLD.COM')]:
            path = w/name
            path.write_bytes(payload)
            cpm('cpmcp',path,destination)
        pristine = raw.read_bytes()
        steps = [
            ('history',b':CRC A7:*.LBR /LOCAL=CRC.LST\r\n:CRC /CHECK=-CATALOG.310 A7:*.LBR\r\n',7,2),
            ('large',b':CRC A3:LARGE.DAT /LOCAL=CRC.LST\r\n:CRC /CHECK A3:LARGE.DAT\r\n',3,1),
            ('legacy',b':CRC A31:FIX.DAT /LEGACY /LOCAL=CRC.LST\r\n:CRC /CHECK A31:FIX.DAT\r\n',31,1)]
        for step,script,user,n in steps:
            raw.write_bytes(pristine)
            startup = w/'STARTUP.SUB'
            startup.write_bytes(b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n'+script+b'HOLD\r\n\x1a')
            cpm('cpmcp',startup,'0:STARTUP.SUB')
            disk = w/(step+'.dmk')
            disk.write_bytes(make_dmk(raw.read_bytes()))
            out = w/step
            out.mkdir()
            command = [str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-sx','-sfmute','-ktx','-d0',str(disk),
                       '-itime','60000','-iw','CRC TEST DONE','-it','-ix']
            run(command,cwd=out,timeout=90,check=True)
            captures = list(out.glob('trs80-text-*.bin'))
            assert len(captures)==1,(step,captures)
            text = screen(captures[0])
            (out/'screen.txt').write_text(text)
            assert 'Verification complete:' in text and f'Files verified: {n}' in text,text
            raw.write_bytes(extract_raw(disk.read_bytes()))
            cpm('cpmcp',f'{user}:CRC.LST',out/'CRC.LST')
            saved = (out/'CRC.LST').read_bytes().split(b'\x1a')[0]
            if step=='history':
                assert b'136B   A548  D24B  82A2F154' in saved and b'B06D   6B36  C153  DE35205C' in saved
            elif step=='large':
                assert expected.encode() in saved
            else:
                assert saved==b'\r\n--> FILE:  FIX     .DAT\t\tCRC = A6 87\r\n\r\n',saved
            for name,payload,destination in files:
                restored = out/('READ-'+name)
                cpm('cpmcp',destination,restored)
                assert restored.read_bytes()[:len(payload)]==payload,(step,destination,'changed')
        evidence['model4'] = 'PASS: four algorithms, historical anchors, >64K, catalog/native/legacy checks, user31, unchanged inputs'
        print(evidence['model4'],flush=True)
    (report/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')


if __name__ == '__main__':
    main()
