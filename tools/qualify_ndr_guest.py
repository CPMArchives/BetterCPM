#!/usr/bin/env python3
"""Exercise NDR on a privately constructed, booted cpmsim development disk.

Run from the prepared checked source workspace with its build context.
Use that same workspace for --build-root. This does not qualify
release media. All disk writes are confined to a newly created output folder.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from build_ccp import ROOT as BUILD_SOURCE, assemble
from build_distribution import construct, geometry, selected_files
from test_z80pack_sysgen_install import session

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--simulator', type=Path, required=True)
    a = p.parse_args()
    root, out = a.build_root.resolve(), a.output.resolve()
    if root != BUILD_SOURCE:
        raise ValueError('run with the tools and build context from --build-root')
    out.mkdir(parents=True, exist_ok=False)
    files, _ = selected_files(json.loads((root/'metadata/distribution.json').read_text()), 'z80pack', root)
    keep = {'RCP.CPX', 'R3PACK.RSX', 'R3CACHE.RSX', 'RSX.COM', 'NDR.COM',
            'NDR.RSX', 'PATH.COM', 'SUBMIT.COM', 'STAT.COM'}
    files = [(c, data) for c, data in files if c['name'] in keep]
    assert {c['name'] for c, _ in files} == keep
    witness = assemble(Path.home()/'bin/z80asm',
                       """; Independent public-state witness after repeated transient termination.
        ORG 100H
        LD DE,DM
        CALL PRINT
        LD C,25
        CALL 5
        CALL HEX
        LD DE,UM
        CALL PRINT
        LD E,0FFH
        LD C,32
        CALL 5
        CALL HEX
        LD DE,TM
        CALL PRINT
        LD HL,(6)
        PUSH HL
        LD A,H
        CALL HEX
        POP HL
        LD A,L
        CALL HEX
        LD DE,NL
        CALL PRINT
        RET
PRINT:  LD C,9
        JP 5
HEX:    PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIB
        POP AF
NIB:    AND 0FH
        ADD A,'0'
        CP '9'+1
        JR C,OUT
        ADD A,7
OUT:    LD E,A
        LD C,2
        JP 5
DM:     DB 'STATE D=','$'
UM:     DB ' U=','$'
TM:     DB ' TOP=','$'
NL:     DB 13,10,'$'
        END
""",
                       out/'NDSTATE.COM', out/'state.lst', 0x100)
    probe = assemble(Path.home()/'bin/z80asm',
                     "        ORG 100H\n        LD DE,MSG\n        LD C,9\n        CALL 5\n        RET\nMSG: DB 'NDR PATH PROBE PASSED',13,10,'$'\n        END\n",
                     out/'NDPROBE.COM', out/'probe.lst', 0x100)
    files.append(({'name':'NDSTATE.COM','user':0}, witness))
    raw = construct('z80pack', root, out, files, geometry('z80pack', root), '')
    disks = out/'disks'; disks.mkdir()
    for drive in 'abcd':
        shutil.copy2(raw, disks/f'drive{drive}.dsk')
    def put(drive, user, name, data):
        artifact = out/('input-'+name)
        artifact.write_bytes(data)
        subprocess.run(['cpmcp','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),
                        str(artifact),f'{user}:{name}'],cwd=out,check=True)
    put('b',2,'NOTE.TXT',b'NDR NAMED FILE PASSED\r\n\x1a')
    put('b',3,'NDPROBE.COM',probe)
    fill = ['NDR /CLEAR'] + [f'NDR ENTRY{i:03d} '+('A0:' if i==1 else 'P31:') for i in range(1,33)]
    put('a',0,'FILL.SUB',('\r\n'.join(fill)+'\r\n\x1a').encode())
    steps = []
    def step(command, expected, prompt='A0 [COMMANDS]> _ '):
        steps.append((command, expected, prompt))
    step('NDSTATE','STATE D=00 U=00 TOP=', 'A0> _ ')
    step('NDR /HELP','Named Directory Management','A0> _ ')
    step('RSX LOAD NDR',None,'A0> _ ')
    step('NDSTATE','STATE D=00 U=00 TOP=','A0> _ ')
    step('NDR','NDR: 0 of 32 names in use.','A0> _ ')
    step('NDR COMMANDS A0:','updated')
    step('NDR SOURCE B2:','updated')
    step('NDR UTILS B3:','updated')
    step('NDR COMMANDS C7:','Name exists.')
    step('TYPE SOURCE:NOTE.TXT','NDR NAMED FILE PASSED')
    step('UTILS:NDPROBE','NDR PATH PROBE PASSED')
    step('SOURCE:',None,'B2 [SOURCE]> _ ')
    step('A0:NDSTATE','STATE D=01 U=02 TOP=','B2 [SOURCE]> _ ')
    step('A0:NDR /SAVE COMMANDS:DEMO','set saved.','B2 [SOURCE]> _ ')
    step('A0:NDR /CLEAR','updated','B2> _ ')
    step('A0:NDR /LOAD A0:DEMO','set loaded.','B2 [SOURCE]> _ ')
    step('A0:NDSTATE','STATE D=01 U=02 TOP=','B2 [SOURCE]> _ ')
    step('COMMANDS:',None)
    step('PATH $$ COMMANDS: UTILS:',None)
    step('NDPROBE','NDR PATH PROBE PASSED')
    step('NDR /DEL UTILS','updated')
    step('NDR UTILS C7:','updated')
    step('NDPROBE','NDR PATH PROBE PASSED')
    step('NDR /LOAD DEMO','set loaded.')
    step('NDSTATE','STATE D=00 U=00 TOP=')
    step('RSX UNLOAD NDR',None,'A0> _ ')
    step('NDSTATE','STATE D=00 U=00 TOP=','A0> _ ')
    step('RSX LOAD NDR',None,'A0> _ ')
    step('NDR','NDR: 0 of 32 names in use.','A0> _ ')
    step('SUBMIT FILL','NDR ENTRY032 P31:','A0 [ENTRY001]> _ ')
    step('NDR','NDR: 32 of 32 names in use.','A0 [ENTRY001]> _ ')
    step('NDR OVERFLOW A0:','NDR is full','A0 [ENTRY001]> _ ')
    for name in ('ENTRY031','ENTRY032'):
        step('NDR /DEL '+name,'updated','A0 [ENTRY001]> _ ')
    step('NDR /SAVE THIRTY','set saved.','A0 [ENTRY001]> _ ')
    step('NDR /LOAD THIRTY','set loaded.','A0 [ENTRY001]> _ ')
    for name in ('ENTRY029','ENTRY030'):
        step('NDR /DEL '+name,'updated','A0 [ENTRY001]> _ ')
    for i in range(1,4):
        step(f'NDR NEW{i} C{i}:','updated','A0 [ENTRY001]> _ ')
    step('NDR /SAVE EDITED','set saved.','A0 [ENTRY001]> _ ')
    step('NDR','NDR: 31 of 32 names in use.','A0 [ENTRY001]> _ ')
    # Reading the expected output before its prompt prevents a stale prompt
    # redraw from satisfying a later command's completion condition.
    commands = []
    for command, expected, prompt in steps:
        commands.append(((command+'\r').encode(),
                         (expected or prompt).encode(),30))
        if expected:
            commands.append((b'',prompt.encode(),30))
    transcript = session(a.simulator.resolve(),disks,commands,out/'session.txt',initial_prompt=b'A0> _ ')
    tops = [int(x,16) for x in re.findall(rb'STATE D=\d\d U=\d\d TOP=([0-9A-F]{4})',transcript)]
    assert len(tops)==6, tops
    assert tops[0]-tops[1]==1536 and tops[-1]==tops[0], tops
    assert len(set(tops[1:-1]))==1, tops
    # Check the actual full-capacity guest listing, including field spacing.
    lines = transcript.replace(b'\r',b'\n').split(b'\n')
    for row in range(8):
        fields = []
        for column in range(4):
            i = 1+row+column*8
            fields.append(f"ENTRY{i:03d} {('A0:' if i==1 else 'P31:'):<4}")
        expected = '    '.join(fields).rstrip().encode()
        assert expected in lines and len(expected)==64, expected
    sets = {}
    for name, count in [('DEMO',3),('THIRTY',30),('EDITED',31)]:
        destination=out/(name+'.NDR')
        subprocess.run(['cpmcp','-f','bettercpm-default',str(disks/'drivea.dsk'),
                        '0:'+name+'.NDR',str(destination)],cwd=out,check=True)
        data=destination.read_bytes()
        assert len(data)==384 and data[:8]==b'BNDR\x01\x20\x08\x0a'
        assert sum(bool(data[i]) for i in range(64,384,10))==count
        sets[name]={'bytes':len(data),'names':count,'sha256':hashlib.sha256(data).hexdigest()}
    # A separate cold boot executes the documented explicit restore sequence.
    put('a',0,'RESTORE.SUB',b'RSX LOAD NDR\r\nNDR /LOAD A0:DEMO\r\nNDR\r\n\x1a')
    from startup_record import build
    from system_layout import LAYOUT
    from fdf_format import select_fdf
    from build_z80pack_image import DEFAULT_FORMAT
    fmt=select_fdf(root/'metadata/DISK.FDF',DEFAULT_FORMAT)
    image=bytearray((disks/'drivea.dsk').read_bytes())
    startup=build('SUBMIT RESTORE',system_base=LAYOUT['SYSTEM'])
    for i in range(2):
        track,within=divmod(i+1,fmt.spt)
        at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
        image[at:at+128]=startup[i*128:(i+1)*128]
    (disks/'drivea.dsk').write_bytes(image)
    cold=session(a.simulator.resolve(),disks,[],out/'cold.txt',initial_prompt=b'A0 [COMMANDS]> _ ')
    assert b'set loaded.' in cold and b'NDR: 3 of 32 names in use.' in cold
    result={'status':'PASS','scope':'private booted cpmsim development media',
            'steps':len(steps),'first_provider_charge':tops[0]-tops[1],
            'unload_recovers_baseline':True,'cold_restore':True,'saved_sets':sets,
            'system_tracks_sha256':hashlib.sha256((root/'build/z80pack/system-package/system-tracks.bin').read_bytes()).hexdigest(),
            'inputs':{c['name']:hashlib.sha256(data).hexdigest() for c,data in files}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
