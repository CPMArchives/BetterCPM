#!/usr/bin/env python3
"""Compare real sequential directory-full outcomes with a DRI reference disk."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from build_ccp import assemble
from run_validation_returning import sha
from test_z80pack_sysgen_install import session

SOURCE = """ ORG 100H
 LD A,@EXT@
 LD (FCB+12),A
 LD DE,FCB
 LD C,15
 CALL 5
 CP 255
 JP Z,BAD
 LD A,128
 LD (FCB+32),A
 LD HL,@RECORD@
 LD (FCB+33),HL
 LD HL,FCB
 LD DE,BEFORE
 LD BC,36
 LDIR
 LD HL,9000H
 LD DE,9001H
 LD BC,127
 LD (HL),0A5H
 LDIR
 LD DE,9000H
 LD C,26
 CALL 5
 LD DE,FCB
 LD C,@FUNCTION@
 CALL 5
 LD (STATUS),A
 LD DE,HEAD
 LD C,9
 CALL 5
 LD A,(STATUS)
 CALL HEX
 LD DE,BHEAD
 LD C,9
 CALL 5
 LD HL,BEFORE
 CALL DUMP
 LD DE,AHEAD
 LD C,9
 CALL 5
 LD HL,FCB
 CALL DUMP
 LD DE,NL
 LD C,9
 CALL 5
 JP 0
BAD: LD DE,ERROR
 LD C,9
 CALL 5
 JP 0
DUMP: LD B,36
LOOP: LD A,(HL)
 PUSH HL
 PUSH BC
 CALL HEX
 POP BC
 POP HL
 INC HL
 DJNZ LOOP
 RET
HEX: PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 AND 15
 CALL DIGIT
 POP AF
 AND 15
DIGIT: ADD A,'0'
 CP ':'
 JR C,PUT
 ADD A,7
PUT: LD E,A
 LD C,2
 JP 5
HEAD: DB 'SEQ STATUS ','$'
BHEAD: DB 13,10,'BEFORE ','$'
AHEAD: DB 13,10,'AFTER ','$'
NL: DB 13,10,'$'
ERROR: DB 'PROBE OPEN FAILED',13,10,'$'
STATUS: DB 0
FCB: DB 0,'SOURCE  DAT'
 DEFS 24,0
BEFORE: DEFS 36,0
 END
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--reference-system', type=Path, default=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-62khd.dsk')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, a.output/'executed-runner.py')
    report = json.loads((a.baseline/'report.json').read_text())
    baseline = a.baseline/report['image']
    assert report['target'] == 'z80pack' and sha(baseline) == report['sha256']
    simulator = Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
    results = {}
    for label, function in ((name,fn) for fn in (21,34) for name in ('DRI','BetterCPM')):
        key = f'{label}-{function}'
        w = a.output/key
        disks = w/'disks'
        disks.mkdir(parents=True)
        reference = label == 'DRI'
        source = a.reference_system if reference else baseline
        shutil.copy2(source,disks/'drivea.dsk')
        target = disks/'drived.dsk'
        if reference:
            target.write_bytes(bytes(256256))
            subprocess.run(['mkfs.cpm','-f','ibm-3740',str(target)],cwd=w,check=True)
            fmt, block, entries = 'ibm-3740',1024,64
        else:
            shutil.copy2(baseline,target)
            shutil.copy2(a.baseline/'diskdefs',w/'diskdefs')
            text = (w/'diskdefs').read_text().split('end',1)[0]
            fmt = 'bettercpm-default'
            block = int(re.search(r'blocksize\s+(\d+)',text)[1])
            entries = int(re.search(r'maxdir\s+(\d+)',text)[1])
            subprocess.run(['cpmrm','-T','raw','-f',fmt,str(target),'0:*.*'],cwd=w,check=True)
        extent_bytes = block*16  # both selected geometries have eight-bit allocation maps
        last_extent = extent_bytes//16384-1
        code = SOURCE.replace('@EXT@',str(last_extent)).replace('@RECORD@',str(extent_bytes//128)).replace('@FUNCTION@',str(function))
        (w/'probe.asm').write_text(code)
        program = w/'FULLSEQ.COM'
        assemble(Path.home()/'bin/z80asm',code,program,w/'probe.lst',0x100)
        payload = bytes((i*29+7)&255 for i in range(extent_bytes))
        (w/'SOURCE.DAT').write_bytes(payload)
        empty = w/'EMPTY.DAT'
        empty.write_bytes(b'')
        def cpm(*args):
            return subprocess.run(list(args),cwd=w,check=True,capture_output=True)
        for f in (w/'SOURCE.DAT', program):
            cpm('cpmcp','-T','raw','-f',fmt,str(target),str(f),'0:'+f.name)
        for i in range(entries-2):
            cpm('cpmcp','-T','raw','-f',fmt,str(target),str(empty),f'0:F{i:07d}.DAT')
        cpm('fsck.cpm','-T','raw','-f',fmt,'-n',str(target))
        shutil.copy2(target,w/'before.dsk')
        initial = b'A>' if reference else b'A0>_ '
        prompt = b'D>' if reference else b'D0>_ '
        trace = session(simulator,disks,[(b'D:\r',prompt,30),(b'FULLSEQ\r',prompt,30)],w/'transcript.bin',initial_prompt=initial)
        assert b'PROBE OPEN FAILED' not in trace
        match = re.search(rb'SEQ STATUS ([0-9A-F]{2})',trace)
        assert match, trace[-1500:]
        status = int(match[1],16)
        before = re.search(rb'BEFORE ([0-9A-F]{72})',trace)
        after = re.search(rb'AFTER ([0-9A-F]{72})',trace)
        assert before and after
        extracted = w/'source-after.bin'
        cpm('cpmcp','-T','raw','-f',fmt,str(target),'0:SOURCE.DAT',str(extracted))
        assert extracted.read_bytes() == payload
        audit = cpm('fsck.cpm','-T','raw','-f',fmt,'-n',str(target))
        (w/'filesystem.txt').write_bytes(audit.stdout+audit.stderr)
        results[key] = {'function':function,'status_code':status,'fcb_before_hex':before[1].decode(),
                          'fcb_after_hex':after[1].decode(),'source_unchanged':True,
                          'whole_data_disk_unchanged':sha(target)==sha(w/'before.dsk'),
                          'program_sha256':sha(program),'system_sha256':sha(source),
                          'extent_bytes':extent_bytes,'directory_entries':entries}
        print(key,results[key],flush=True)
    assert results['DRI-21']['status_code'] == 1, 'DRI sequential reference differs'
    assert results['DRI-34']['status_code'] == 5, 'DRI random reference differs'
    good = all(results[f'BetterCPM-{fn}']['status_code'] == results[f'DRI-{fn}']['status_code'] for fn in (21,34))
    good = good and all(r['source_unchanged'] and r['whole_data_disk_unchanged'] for r in results.values())
    good = good and all(results[f'{name}-21']['fcb_before_hex'] == results[f'{name}-21']['fcb_after_hex'] for name in ('DRI','BetterCPM'))
    result = {'status':'PASS' if good else 'FAIL','baseline_sha256':report['sha256'],
              'simulator_sha256':sha(simulator),'results':results,
              'runner_sha256':sha(a.output/'executed-runner.py'),
              'scope':'Real public sequential and random writes at a physical-extent boundary with every directory entry occupied but free data blocks; separate DRI reference and BetterCP/M disk geometries, source/data filesystem audits.'}
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert sha(baseline) == report['sha256']
    assert good, 'directory-full status, FCB, or filesystem preservation differs'


if __name__ == '__main__':
    main()
