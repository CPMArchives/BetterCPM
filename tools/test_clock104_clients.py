#!/usr/bin/env python3
"""Run independently supplied historical SCTIME/DATE501 under cpmsim."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from test_z80pack_sysgen_install import session
ROOT = Path(__file__).resolve().parents[1]
READ = """        ASEG
        ORG 100H
        LD HL,10H
        LD DE,SAVED
        LD BC,6
        LDIR
        LD DE,TITLE
        LD C,9
        CALL 5
        LD HL,SAVED
        LD B,6
LOOP:   LD A,(HL)
        PUSH HL
        PUSH BC
        CALL HEX
        LD E,' '
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ LOOP
        JP 0
HEX:    PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIBBLE
        POP AF
NIBBLE: AND 0FH
        ADD A,'0'
        CP ':'
        JR C,CHAR
        ADD A,7
CHAR:   LD E,A
        LD C,2
        JP 5
TITLE:  DB 'SCTIME RECORD: $'
SAVED:  DB 0,0,0,0,0,0
        END
"""
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sctime', type=Path, required=True)
    parser.add_argument('--date501', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    frozen = {
        'SCTIME': (args.sctime, 'd176ad1622087126dd986b138ff28517e765a40458f20263dd171a6af24a0609'),
        'DATE501': (args.date501, 'c4d1e909ab277256fbfce8d0e4d397bc02278cbc49fbd1c7e08fbd2989a7cd84')
    }
    for name, (path, expected) in frozen.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(name + ' differs from the independently retrieved qualification binary')
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    disk = work / 'disks/drivea.dsk'
    subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disk),
                    '0:bdosprb.com','0:rsx2tst.com','0:rsxtest.com','0:stattst.com',
                    '0:svctest.com','0:r3coord.rsx'],cwd=work,check=True)
    read = report / 'SCREAD.COM'
    (report / 'scread.mac').write_text(READ)
    assemble(Path.home() / 'bin/z80asm',READ,read,report / 'scread.lst',0x100)
    inputs = [(args.sctime,'SCTIME.COM'),(args.date501,'DATE501.COM'),(read,'SCREAD.COM'),
              (ROOT / 'build/rsx/T104C3.RSX','T104C3.RSX'),
              (ROOT / 'build/rsx/T104Z8.RSX','T104Z8.RSX'),
              (ROOT / 'build/system/R3COORD.RSX','R3COORD.RSX')]
    for path,name in inputs:
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=work,check=True)
    commands = ['RSX LOAD ZPRTC','RSX LOAD T104C3','TIME','SCTIME','SCREAD','TIME',
                'RSX UNLOAD T104C3','RSX LOAD T104Z8','TIME','DATE501','TIME',
                'RSX UNLOAD T104Z8','RSX UNLOAD ZPRTC','RSX LIST']
    output = session(args.simulator.resolve(),work/'disks',
                     [(c.encode()+b'\r',b'A0>_ ',20) for c in commands],report/'transcript.txt')
    blocks=[]
    cursor=0
    for command in commands:
        start=output.index(command.encode(),cursor)
        end=output.index(b'A0>_ ',start)
        blocks.append(output[start:end])
        cursor=end
    stamp = rb'(20[0-9]{2})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})'
    times=[datetime.datetime(*map(int,re.search(stamp,blocks[i]).groups())) for i in (2,5,8,10)]
    match=re.search(rb'SCTIME RECORD: ((?:[0-9A-F]{2} ){6})',blocks[4])
    assert match,blocks[4]
    values=[int(s,16) for s in match.group(1).split()]
    assert all(v>>4<=9 and v&15<=9 for v in values),values
    dec=[(v>>4)*10+(v&15) for v in values]
    sc=datetime.datetime(2000+dec[2],dec[0],dec[1],dec[3],dec[4],dec[5])
    assert times[0]<=sc<=times[1],(times,dec)
    # SCTIME stores SuperCalc's month/day/year record, not day/month/year.
    # DATE501 source PRDMJ independently specifies DD-Mon-YYYY hh:mm:ss.
    match=re.search(rb'[0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}',blocks[9])
    assert match,blocks[9]
    date=datetime.datetime.strptime(match.group().decode(),'%d-%b-%Y %H:%M:%S')
    assert times[2]<=date<=times[3],(times,date)
    assert b'53K' in blocks[-1] and b'No RSXs loaded' in blocks[-1],blocks[-1]
    (report/'evidence.json').write_text(json.dumps({
        'source_urls': {name: 'https://ftpmirror.infania.net/sites/www.seasip.info/Cpm/2000/' + name.lower() + '.com' for name in frozen},
        'boot_image_sha256': hashlib.sha256((args.image_dir / 'disks/drivea.dsk').read_bytes()).hexdigest(),
        'result':'PASS','commands':commands,'sctime_record':dec,'date501':str(date),
        'sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in inputs},
        'simulator_sha256':hashlib.sha256(args.simulator.read_bytes()).hexdigest()
    },indent=2)+'\n')
    print('PASS: original SCTIME and DATE501 records agree with bracketing native TIME')
if __name__=='__main__': main()
