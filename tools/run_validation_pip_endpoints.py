#!/usr/bin/env python3
"""Retain real cpmsim PIP endpoint bytes, DRI comparison and IOBYTE witnesses."""
import argparse
import json
import os
import shutil
import subprocess
import stat
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from run_validation_cpmsim_monitors import audit
from test_z80pack_sysgen_install import session
ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=False)
    report = json.loads((a.baseline / 'report.json').read_text())
    original = a.baseline / report['image']; assert sha(original) == report['sha256']
    sim = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    # cpmsim has a process-global auxiliary FIFO. Never feed another session.
    active = subprocess.run(['pgrep', '-x', 'cpmsim'], capture_output=True, text=True)
    assert active.returncode == 1, 'another cpmsim is active; do not share auxiliary endpoints'
    results = []
    for label in ('OUR', 'DRI'):
        w = a.output / label; (w / 'disks').mkdir(parents=True)
        shutil.copy2(a.baseline / 'diskdefs', w / 'diskdefs')
        shutil.copy2(__file__, w / 'executed-runner.py')
        for drive in 'ab': shutil.copy2(original, w / f'disks/drive{drive}.dsk')
        disk = w / 'disks/drivea.dsk'; target = w / 'disks/driveb.dsk'
        def cpm(tool, image, *args):
            return subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(image), *map(str,args)], cwd=w, check=True, capture_output=True)
        cpm('cpmrm', target, '0:*.*')
        def put(name, data):
            file = w / name; file.write_bytes(data); cpm('cpmcp', disk, file, '0:' + name)
        if label == 'DRI': put('PIPREF.COM', (ROOT / 'third_party/dri-pip/PIP-1.5-reference.COM').read_bytes())
        put('S7INPUT.TXT', b'alpha\r\nbeta\x1a')
        for name, source in {
            'IOS': " ORG 100H\n LD E,041H\n LD C,8\n CALL 5\n RET\n END\n",
            'IOC': " ORG 100H\n LD C,7\n CALL 5\n CP 041H\n LD DE,GOOD\n JR Z,SHOW\n LD DE,BAD\nSHOW: LD C,9\n CALL 5\n RET\nGOOD: DB 'IOBYTE PRESERVED',13,10,'$'\nBAD: DB 'IOBYTE LEAKED',13,10,'$'\n END\n"}.items():
            (w / (name + '.asm')).write_text(source)
            binary = assemble(Path.home() / 'bin/z80asm', source, w / (name + '.COM'), w / (name + '.lst'), 0x100)
            put(name + '.COM', binary)
        program = 'PIP' if label == 'OUR' else 'PIPREF'
        commands = [(b'IOS\r', b'A0>_ ', 30)]
        for command in (f'{program} PRN:=S7INPUT.TXT', f'{program} PTP:=S7INPUT.TXT', f'{program} B:READ.TXT=PTR:', f'{program} CRT:=S7INPUT.TXT'):
            commands.extend([(command.encode() + b'\r', b'A0>_ ', 60), (b'IOC\r', b'A0>_ ', 30)])
        commands.append((b'BYE /Y\r', b'System halted', 30))
        (w / 'commands.json').write_text(json.dumps([(x.decode(),y.decode(),z) for x,y,z in commands],indent=2)+'\n')
        # An unlimited-speed simulator can finish in milliseconds. Queue the
        # bounded input before launch and retain a FIFO handle so it survives
        # until the simulator opens its reader. No polling/thread timing oracle.
        fifo = '/tmp/.z80pack/cpmsim.auxin'
        assert stat.S_ISFIFO(os.stat(fifo).st_mode)
        fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        data = b'INPUT\r\nEND\x1a'; fed = [data.hex()]
        try:
            assert os.write(fd, data) == len(data)
            transcript = session(sim, w / 'disks', commands, w / 'transcript.bin')
        finally: os.close(fd)
        assert transcript.count(b'IOBYTE PRESERVED') == 4 and b'IOBYTE LEAKED' not in transcript
        assert b'alpha\r\nbeta' in transcript
        exported = w / 'READ.TXT'; cpm('cpmcp', target, '0:READ.TXT', exported)
        # cpmcp applies host S1 semantics to DRI's byte-count metadata. Read
        # the single record physically instead; never normalize runtime media.
        from run_validation_cpmsim_era_destructive import entries, record_offset
        raw = target.read_bytes()
        rows = [r for r in entries(raw) if r[0] == 0 and bytes(v & 127 for v in r[1:12]) == b'READ    TXT']
        assert len(rows) == 1 and rows[0][15] == 1 and rows[0][16] != 0
        at = record_offset(rows[0][16] * 16)
        records = raw[at:at+128]; (w / 'READ-records.bin').write_bytes(records)
        values = [(w / 'printer.txt').read_bytes(), (w / 'auxiliaryout.txt').read_bytes(), records]
        assert values[0] == b'\x0c     1: alpha\n     2: beta' and values[1] == b'alpha\nbeta'
        assert values[2] == b'INPUT\r\nEND\x1a'.ljust(128,b'\x1a')
        shipped = audit(a.baseline, report, w, disk)
        check = subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(target)],cwd=w,capture_output=True,check=True)
        (w/'secondary-filesystem.txt').write_bytes(check.stdout+check.stderr)
        result = {'status':'PASS','label':label,'baseline_sha256':report['sha256'],'runner_sha256':sha(w/'executed-runner.py'),
                  'simulator_sha256':sha(sim),'program_sha256':next(x['sha256'] for x in report['included'] if x['name']=='PIP.COM') if label=='OUR' else sha(w/'PIPREF.COM'),
                  'endpoint_sha256':[sha(w/n) for n in ('printer.txt','auxiliaryout.txt','READ-records.bin')],'reader_directory_s1':rows[0][13],'host_extraction_length':len(exported.read_bytes()),'iobyte_initial_and_restored':'41h','fed_hex':fed,
                  'unchanged_shipped_files':shipped}
        (w/'result.json').write_text(json.dumps(result,indent=2)+'\n'); results.append((result,values))
    assert results[0][1] == results[1][1]
    (a.output/'result.json').write_text(json.dumps({'status':'PASS','cases':[x[0]for x in results],
        'scope':'real cpmsim PRN/PTP/PTR/CRT routes, exact host bytes equal DRI and independent expectations, IOBYTE restoration; no physical printer/UART claim'},indent=2)+'\n')
    print('PASS retained PIP host endpoints',a.output)


if __name__=='__main__': main()
