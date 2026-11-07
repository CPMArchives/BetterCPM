#!/usr/bin/env python3
"""Run the first Model II guest gates on private copies. Passing is not release qualification."""
import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_ccp import assemble
from model2_media import image
from trs80gp_launch import run, launch_services_lookup

ROOT=Path(__file__).resolve().parents[1]
EMU=Path.home()/'Applications/trs80gp.app/Contents/MacOS/trs80gp'
EMU_SHA='8f967e640927af1fb9de3a178bbf0bc4d687124780405885a6daa33a3fee1d9f'
SIZE=57344
# Each protocol positions the cursor on zero-based row 6, column 9.
SCREEN_CASES = [('ADM3A','QADM',bytes((27,61,38,41))),
                ('VT52','QVT',bytes((27,89,38,41))),
                ('ANSI','QANSI',b'\x1b[7;10H')]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def fixtures(work, assembler):
    def probe(name, text, size=None):
        data=assemble(assembler,text,work/(name+'.bin'),work/(name+'.lst'),0x100)
        if size:
            if len(data)>256:raise ValueError('fixture exceeds preserved first page')
            data=data.ljust(size,b'\xa5')
        return (name+'.COM',data)
    path=ROOT/'tests/fixtures/conformance'
    files=[probe('STATE',(path/'returnstate.mac').read_text())]
    route=(path/'fullreturn.mac').read_text()
    for name,exit_code in [('RET','RET'),('JUMP','JP 0'),('FN0','LD C,0\n        CALL 5\n        HALT')]:
        files.append(probe('E'+name,route.replace('@COUNT@',str(SIZE-256))
            .replace('@ROUTE@',name).replace('@EXIT@','        '+exit_code),SIZE))
    files.append(probe('OVER',"""        ORG 100H
        LD DE,MSG
        LD C,9
        CALL 5
        JP 0
MSG:    DB 'OVERSIZE PROGRAM ENTERED',13,10,'$'
        END
""",SIZE+128))
    for monitor, name, address in SCREEN_CASES:
        payload = address + (monitor+' MODEL II').encode('ascii') + b'$'
        files.append(probe(name, "        ORG 100H\n        LD DE,MSG\n        LD C,9\n"
                           "        CALL 5\n        LD C,1\n        CALL 5\n        JP 0\n"
                           "MSG:    DB "+','.join(map(str,payload))+"\n        END\n"))
    return files


def screen(path):
    data=path.read_bytes()
    if len(data)<1920:raise ValueError('truncated 80 x 24 capture')
    rows=[''.join(chr(c&127) if 32<=c&127<=126 else ' ' for c in data[i:i+80]).rstrip()
          for i in range(0,1920,80)]
    return '\n'.join(rows).strip()


# Every post-run result must include a new command echo, its own witness
# and a returned prompt. A stale/cached screen cannot satisfy a later case.
STEPS=[('', ['A0>']), ('B:STATE',['STATE D=00 U=00 TOP=E101']),
       ('B:ERET',['FULL-TPA RET ENTERED']), ('B:EJUMP',['FULL-TPA JUMP ENTERED']),
       ('B:EFN0',['FULL-TPA FN0 ENTERED']), ('B:OVER',[]),
       ('B:STATE',['STATE D=00 U=00 TOP=E101']), ('TIME',['No TIME provider is loaded']),
       ('CPX LIST',['RCP']), ('B:RSXTEST',['function 198 unsupported']),
       ('RSX LOAD B:HELLO',[]), ('B:RSXTEST',['Hello from HELLO.RSX','function 198 returned 5253h']),
       ('RSX LIST',['HELLO','TPA available: 53K']), ('B:STATE',['STATE D=00 U=00 TOP=D801']),
       ('RSX UNLOAD HELLO',[]),
       ('B:RSXTEST',['function 198 unsupported']), ('B:STATE',['STATE D=00 U=00 TOP=E101'])]


def audit_captures(work,report):
    for i,(command,witnesses) in enumerate(STEPS):
        text=screen(work/f'trs80-text-{i}.bin')
        (work/f'screen-{i:02}.txt').write_text(text+'\n')
        window=text
        if command:
            echo='A0>'+command
            if echo not in text:raise ValueError(f'missing command echo: {command}')
            window=text.rsplit(echo,1)[1]
        returned=window.rstrip().endswith('A0>')
        source='same capture'
        if not returned and command in ('RSX LOAD B:HELLO','RSX UNLOAD HELLO'):
            # A capture can land during floppy I/O. The following fresh service probe
            # must then prove the return, the state transition and its own return.
            next_command,next_witnesses=STEPS[i+1]
            following=screen(work/f'trs80-text-{i+1}.bin')
            after=following.rpartition('A0>'+command)
            later=after[2].partition('A0>'+next_command)
            returned=bool(after[1] and later[1] and all(w in later[2] for w in next_witnesses)
                          and later[2].rstrip().endswith('A0>'))
            source='next command echo and service result'
        ok=returned and all(w in window for w in witnesses)
        if command=='B:OVER':
            ok=ok and 'OVERSIZE PROGRAM ENTERED' not in window
        if 'PATTERN OR RETURN FAILED' in window:ok=False
        report['captures'].append({'command':command or 'cold boot','passed':ok,'return_evidence':source})
        if not ok:raise ValueError(f'failed {command or "cold boot"}: see screen-{i:02}.txt')
    for i,(monitor,_,_) in enumerate(SCREEN_CASES,len(STEPS)):
        path=work/f'trs80-text-{i}.bin'
        raw=path.read_bytes()
        marker=(monitor+' MODEL II').encode('ascii')
        start=6*80+9
        ok=bytes(c&127 for c in raw[start:start+len(marker)])==marker
        report['captures'].append({'positioned_by':monitor,'passed':ok})
        if not ok:raise ValueError(f'{monitor}: expected marker at row 7, column 10 in {path.name}')
    # Screen addressing leaves old text below the cursor. Read the freshly
    # painted rows in order, comparing with the immediately preceding frame.
    final_index=len(STEPS)+len(SCREEN_CASES)
    def rows(index):
        data=(work/f'trs80-text-{index}.bin').read_bytes()
        if len(data)<1920:raise ValueError('truncated final screen')
        return [bytes(c&127 for c in data[i:i+80]).decode('ascii').rstrip()
                for i in range(0,1920,80)]
    before,after=rows(final_index-1),rows(final_index)
    first=0
    evidence=[]
    for token in ('A0>RSX UNLOAD ANSI','A0>RSX UNLOAD M2SCRN','A0>B:STATE',
                  'STATE D=00 U=00 TOP=E101','A0>'):
        for row in range(first,len(after)):
            matches=(after[row]==token if token in ('A0>','STATE D=00 U=00 TOP=E101') else after[row].startswith(token))
            if matches and not before[row].startswith(token):
                first=row+1;evidence.append(first);break
        else:raise ValueError(f'missing fresh final screen row for {token!r}')
    report['captures'].append({'post_monitor_unload':'E101','fresh_rows':evidence,'passed':True})



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--media',type=Path,default=ROOT/'build/model2-candidate')
    p.add_argument('--output',type=Path,default=ROOT/'build/model2-guest')
    p.add_argument('--emulator',type=Path,default=EMU)
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--audit-only',type=Path,metavar='RUN',help='audit retained captures without launching the emulator')
    a=p.parse_args()
    if a.audit_only:
        work=a.audit_only.resolve()
        report=json.loads((work/'result.json').read_text())
        report.update(captures=[],original_status=report['status'])
        report.pop('detail',None)
        try:
            audit_captures(work,report)
            report['status']='PASS (first guest gates only)'
        except (OSError,ValueError) as exc:
            report.update(status='INCOMPLETE',detail=str(exc))
        path=work/'capture-audit.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(f"{report['status']} — {path}")
        if 'detail' in report:print(report['detail'])
        return int(report['status']=='INCOMPLETE')
    a.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(dir=a.output.resolve(),prefix='run-'))
    print(f'Model II qualification report: {work}/result.json',flush=True)
    media=a.media.resolve();emu=a.emulator.resolve()
    manifest=json.loads((media/'candidate.json').read_text())
    if manifest['profile']!='model2-fullram' or manifest['planned_tpa']!=SIZE:
        raise ValueError('unexpected build profile')
    for name,digest in manifest['files'].items():
        if sha(media/name)!=digest:raise ValueError('candidate hash mismatch: '+name)
    assembler=Path.home()/'bin/z80asm'
    if sha(assembler)!=manifest['assembler_sha256']:raise ValueError('assembler differs from candidate')
    system=work/'a.imd'
    shutil.copyfile(media/'Model-II-System-candidate.imd',system)
    secondary=work/'b.imd'
    programs=fixtures(work,assembler)
    for name,expected in manifest['qualification_files'].items():
        path=media/'qualification'/name
        if sha(path)!=expected:raise ValueError('incorrect qualification fixture: '+name)
        programs.append((name,path.read_bytes()))
    secondary.write_bytes(image(bytes(20480),programs,bootable=False))
    cmd=[str(emu),'-m2','-mem','64','-batch','-turbo','-itime','0','-d0',str(system),'-d1',str(secondary),'-id','9000']
    for command,_ in STEPS:
        if command:cmd+=['-i',command+'\r','-id','6000']
        cmd+=['-it']
    def enter(command):
        return ['-i',command+'\r','-id','6000']
    cmd+=enter('RSX LOAD M2SCRN')
    for monitor,name,_ in SCREEN_CASES:
        cmd+=enter('RSX LOAD '+monitor)+enter('B:'+name)+['-it','-i',' ','-id','6000']
        cmd+=enter('RSX UNLOAD '+monitor)
    cmd+=enter('RSX UNLOAD M2SCRN')+enter('B:STATE')+['-it','-ix']
    report={'status':'PREPARED','scope':'cold boot, 56 KiB boundary and recovery, RET/JP 0/BDOS 0, CPX, public RSX lifecycle/allocation, TIME without provider, screen personality positioning/unload',
            'candidate':manifest,'emulator':str(emu),'version':'2.5.8','rom':'built in; no -rom override',
            'emulator_sha256':EMU_SHA,'machine':'Model II 64K, two single-sided IMD drives',
            'arguments':cmd,'fixture_sha256':sha(secondary),'captures':[]}
    result=work/'result.json'
    def save():result.write_text(json.dumps(report,indent=2)+'\n')
    save()
    if a.prepare_only:return
    try:
        if sha(emu)!=EMU_SHA:raise ValueError('not the pinned macOS trs80gp 2.5.8 executable')
        if plistlib.loads((emu.parents[1]/'Info.plist').read_bytes())['CFBundleShortVersionString']!='2.5.8':
            raise ValueError('not trs80gp 2.5.8')
        if sys.platform=='darwin':
            code=launch_services_lookup()
            if code:
                report.update(status='HOST BLOCKED',detail=f'LaunchServices {code}; trs80gp was not started')
                save();print(report['detail']);return 2
        run(cmd,cwd=work,timeout=1200)
        audit_captures(work,report)
        report['status']='PASS (first guest gates only)'
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        report.update(status='INCOMPLETE',detail=str(exc));save();raise
    save();print(report['status']);return 0


if __name__=='__main__':
    sys.exit(main())
