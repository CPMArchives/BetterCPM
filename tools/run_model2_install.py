#!/usr/bin/env python3
"""Install, boot, check and duplicate the Model II candidate on private IMD copies."""
import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from model2_media import image
from run_model2_qualification import ROOT, EMU, EMU_SHA, sha, screen
from test_model2_release_media import decoded, repack
from trs80gp_launch import run, launch_services_lookup


CONFIG_BINDINGS=tuple(f'{drive}: {unit}: BetterCP/M Model II 584K SS' for unit,drive in enumerate('ABCD'))


def completed_phase(previous,old,name):
    item=next((row for row in old['phases'] if row['name']==name and row['status']=='PASS'),None)
    if item is None:return None
    evidence=Path(item.get('evidence',previous/name))
    captures=item['capture_sha256']
    if not captures or any(sha(evidence/path)!=digest for path,digest in captures.items()):
        raise ValueError(f'changed or missing {name} captures')
    return dict(item,evidence=str(evidence))


def saved_install(previous,manifest,reference):
    """Read the completed installer evidence and its actual disk before resuming."""
    old=json.loads((previous/'result.json').read_text())
    if old['status'] not in ('INCOMPLETE','PASS'):
        raise ValueError('resume requires a finished run, not a live or prepared one')
    if (old['system_sha256']!=manifest['files']['Model-II-System-candidate.imd']
            or old['emulator_sha256']!=EMU_SHA):
        raise ValueError('old run belongs to another disk or emulator')
    install=completed_phase(previous,old,'install')
    if install is None:
        raise ValueError('old run has no verified installation')
    evidence=Path(install['evidence'])
    if ('Proceed (Y/N)?' not in screen(evidence/'trs80-text-2.bin')
            or 'System installed and verified' not in screen(evidence/'trs80-text-4.bin')):
        raise ValueError('missing installer witness')
    if decoded((previous/'installed.imd').read_bytes())[2]!=reference:
        raise ValueError('old installed media differs from the candidate')
    return dict(install,evidence=str(evidence))


def saved_cold_boot(previous):
    """Recover the completed /SHOW result from a capture made before the old timeout."""
    old=json.loads((previous/'result.json').read_text())
    row=next((item for item in old['phases'] if item['name']=='cold-config'),{})
    evidence=Path(row.get('evidence',previous/'cold-config'))
    paths=[evidence/f'trs80-text-{idx}.bin' for idx in range(3)]
    if not all(p.is_file() for p in paths):
        return None
    cmd=json.loads((evidence/'arguments.json').read_text())
    if '-m2' not in cmd or '-d1' in cmd or '-d0' not in cmd or Path(cmd[cmd.index('-d0')+1])!=evidence.parent/'installed.imd':
        return None
    boot,cpx,config=map(screen,paths)
    if ('A0>' not in boot or not all(x in cpx for x in ('A0>CPX LIST','RCP.CPX','TPA available: 56K'))
            or not all(x in config for x in ('Saved logical-drive bindings:',*CONFIG_BINDINGS))):
        return None
    if not config.endswith('A0>'):
        follow=evidence/'trs80-text-3.bin'
        if not follow.is_file() or not all(x in screen(follow) for x in
                                          ('A0>CPX LIST','RCP.CPX','TPA available: 56K')):
            return None
        paths.append(follow)
    return {'name':'cold-config','status':'PASS','evidence':str(evidence),
            'scope':'installed cold boot, CPX, saved drive bindings and returned prompt',
            'capture_sha256':{p.name:sha(p) for p in paths}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media',type=Path,default=ROOT/'build/model2-install-candidate')
    parser.add_argument('--output',type=Path,default=ROOT/'build/model2-install-guest')
    parser.add_argument('--emulator',type=Path,default=EMU)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--resume',type=Path,metavar='RUN',help='continue on a private copy of an already verified installation')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(dir=args.output.resolve(),prefix='run-'))
    media=args.media.resolve()
    manifest=json.loads((media/'candidate.json').read_text())
    original=media/'Model-II-System-candidate.imd'
    if manifest['profile']!='model2-fullram' or sha(original)!=manifest['files'][original.name]:
        raise ValueError('unexpected source System Disk')
    source=work/'source.imd'
    shutil.copyfile(original,source)
    comment,tracks,reference=decoded(source.read_bytes())
    reserved=26*128+3*16*512  # One FM and three MFM surfaces, OFF=4.
    dest=work/'installed.imd'
    reused=[]
    previous=args.resume.resolve() if args.resume else None
    if previous:
        reused.append(saved_install(previous,manifest,reference))
        shutil.copyfile(previous/'installed.imd',dest)
        cold=saved_cold_boot(previous)
        if cold:reused.append(cold)
    else:
        dest.write_bytes(repack(comment,tracks,b'\xe5'*reserved+reference[reserved:]))
    copy=work/'duplicate.imd'
    copy.write_bytes(image(bytes(160*128),[],bootable=False))
    if previous:
        old=json.loads((previous/'result.json').read_text())
        duplicate=completed_phase(previous,old,'duplicate')
        if duplicate:
            if decoded((previous/'duplicate.imd').read_bytes())[2]!=reference:
                raise ValueError('previous duplicate differs from installed source')
            shutil.copyfile(previous/'duplicate.imd',copy)
            reused.append(duplicate)
            checked=completed_phase(previous,old,'check-copy')
            if checked:reused.append(checked)
        iobyte=completed_phase(previous,old,'saved-iobyte')
        if iobyte:reused.append(iobyte)
    if not previous and decoded(dest.read_bytes())[2][:reserved]!=b'\xe5'*reserved:
        raise ValueError('target already contains protected records')
    emu=args.emulator.resolve()
    report={'status':'PREPARED','build':manifest['source_revision'],'system_sha256':sha(original),
            'emulator_sha256':EMU_SHA,'initial_target':sha(dest),'initial_duplicate':sha(copy),'phases':reused.copy()}
    if previous:report['resumed_from']=str(previous)
    result=work/'result.json'
    def save():result.write_text(json.dumps(report,indent=2)+'\n')
    save()
    print('Model II disk qualification:',result,flush=True)
    if reused:print('Verified prior phases:',', '.join(row['name'] for row in reused),flush=True)
    if args.prepare_only:return 0
    if sha(emu)!=EMU_SHA or plistlib.loads((emu.parents[1]/'Info.plist').read_bytes())['CFBundleShortVersionString']!='2.5.8':
        raise ValueError('this batch requires the pinned macOS trs80gp 2.5.8')
    if sys.platform=='darwin' and (code:=launch_services_lookup()):
        report.update(status='HOST BLOCKED',detail=f'LaunchServices {code}; no guest started')
        save();print(report['detail']);return 2

    def phase(name,d0,d1,actions,markers,timeout,verify):
        if any(row['name']==name for row in reused):
            return
        case=work/name
        case.mkdir()
        cmd=[str(emu),'-m2','-mem','64','-batch','-turbo','-itime','0','-d0',str(d0)]
        if d1:cmd+=['-d1',str(d1)]
        cmd+=['-iw','A0>','-id','300','-it',*actions,'-ix']
        (case/'arguments.json').write_text(json.dumps(cmd,indent=2)+'\n')
        report['status']='RUNNING'
        item={'name':name,'status':'RUNNING'};report['phases'].append(item);save()
        print('Running',name,flush=True)
        try:
            run(cmd,cwd=case,timeout=timeout)
            captures=sorted(case.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
            screens=[]
            for path in captures:
                value=screen(path);path.with_suffix('.txt').write_text(value+'\n');screens.append(value)
            for target,marker in markers:
                if target>=len(screens) or marker not in screens[target]:
                    raise ValueError(f'{name}: missing {marker!r} on capture {target}')
            verify()
            item['status']='PASS';item['capture_sha256']={p.name:sha(p) for p in captures};save()
        except Exception as exc:
            item.update(status='INCOMPLETE',detail=str(exc))
            report.update(status='INCOMPLETE',detail=f'{name}: {exc}')
            save();raise

    def verify_install():
        # Starting filesystem and destination binding are identical. Every
        # protected record must now equal the source; compare all other bytes too.
        actual=decoded(dest.read_bytes())[2]
        if actual[:reserved]!=reference[:reserved]:raise ValueError('installed reserved surfaces differ from source')
        if actual[reserved:]!=reference[reserved:]:raise ValueError('SYSGEN changed the existing filesystem')
        if decoded(source.read_bytes())[2]!=reference:raise ValueError('source media changed')
    def cold_source():
        if decoded(dest.read_bytes())[2]!=reference:raise ValueError('installed System Disk changed during read-only checks')
    def verify_copy():
        cold_source()
        if decoded(copy.read_bytes())[2]!=reference:raise ValueError('DUP target differs from installed source')

    # Finite diagnostic snapshots precede waits, so a failed guest retains a screen.
    phase('install',source,dest,
          ['-i','SYSGEN SYSTEM.SYS B:\r','-id','6500','-it','-iw','Proceed (Y/N)?','-it',
           '-i','Y','-id','18000','-it','-iw','System installed and verified','-it'],
          [(0,'A0>'),(2,'Proceed (Y/N)?'),(4,'System installed and verified')],420,verify_install)
    phase('cold-config',dest,None,
          ['-i','CPX LIST\r','-iw','TPA available: 56K','-it','-id','3500',
           '-i','CONFIG /SHOW\r','-iw',CONFIG_BINDINGS[-1],'-id','1200','-it',
           '-id','15000','-i','CPX LIST\r','-iw','TPA available: 56K','-id','300','-it'],
          [(1,'RCP.CPX'),(1,'TPA available: 56K'),(2,'Saved logical-drive bindings:'),
           *((2,line) for line in CONFIG_BINDINGS),(3,'A0>CPX LIST'),
           (3,'RCP.CPX'),(3,'TPA available: 56K')],240,cold_source)
    phase('duplicate',dest,copy,
          ['-i','DUP /COPY A: B:\r','-id','6500','-it','-iw','[Y/N]','-it','-i','Y',
           '-id','18000','-it','-iw','Copy complete; destination verified.','-it'],
          [(2,'[Y/N]'),(4,'Copy complete; destination verified.')],1500,verify_copy)
    phase('check-copy',copy,None,
          ['-i','DUP /CHECK A:\r','-id','12000','-it','-iw','Check complete. Unreadable sectors:',
           '-id','300','-it'],
          [(2,'Check complete. Unreadable sectors: 00000')],900,verify_copy)
    # CONFIG /SHOW can scroll IOBYTE off its 24-row display. Menu B calls the
    # same reader and holds both values on screen until the user enters a number.
    # Capture at the input prompt whether the saved value is right or wrong.
    phase('saved-iobyte',dest,None,
          ['-i','CONFIG\r','-iw','Configuration options:','-id','300','-i','B',
           '-iw','Disk-boot IOBYTE (decimal):','-id','300','-it'],
          [(1,'Live IOBYTE (decimal): 149'),(1,'Saved disk-boot IOBYTE (decimal): 149')],
          150,cold_source)
    report.update(status='PASS',scope='SYSGEN package install and filesystem preservation, independent cold boot and CONFIG /SHOW, whole-media DUP copy, cold boot and check of duplicate')
    save();print('PASS:',result);return 0


if __name__=='__main__':
    sys.exit(main())
