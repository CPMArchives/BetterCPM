#!/usr/bin/env python3
"""Disposable native DASM toolchain campaign support on both BetterCP/M targets."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from add_cpm_file_to_dmk import extract_raw, add_file, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as make_dmk
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from fdf_format import select_fdf
from convert_fdf_image import dmk_to_raw
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run as launch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM = Path('/private/tmp/utilities-toolchain-fixed-system5/release-19b65de4799c-70e313cb974b')
SIMULATOR = Path.home()/'projects/git/z80pack/cpmsim/cpmsim'


def campaign(platform, files, commands, output, *, system=DEFAULT_SYSTEM,
             utilities=None, extract=(), interactive=(), emulator=None, utility_files=None, setup=None, interactive_frames=None, interactive_launch=None, interactive_ready=None, interactive_followup=None):
    """Run each shell command with a visible completion marker; preserve media."""
    output.mkdir(parents=True, exist_ok=False)
    native = platform == 'trs80gp'
    emulator=emulator or DEFAULT_EMULATOR
    if native and not emulator.is_file():
        emulator=Path.home()/'CPM/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp'
    if native and not emulator.is_file():raise FileNotFoundError(emulator)
    report = json.loads((system/platform/'report.json').read_text())
    original = system/platform/report['image']
    image = original.read_bytes()
    utility = (utilities or ROOT/'build/utilities-disks')/('BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk'
              if native else 'BetterCPM-Utilities-z80pack-332K.dsk')
    ub = utility.read_bytes()
    files = dict(files)
    script = [] if native else ['C:']
    for i, command in enumerate(commands):
        marker = f'DASM STEP {i} DONE'
        stub = '1110010e09cd05000e01cd0500c30000' if native else '110b010e09cd0500c30000'
        files[f'DM{i}.COM'] = bytes.fromhex(stub)+(marker+'\r\n$').encode()
        script += ['CLS', command, f'DM{i}' if native else f'A:DM{i}']
    if native and interactive_launch:
        script += ['CLS',interactive_launch]
        if interactive_followup:script += [interactive_followup]
    files['QUALIFY.SUB'] = ('\r\n'.join(script)+'\r\n\x1a').encode()
    defs = disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT))
    defs += '''diskdef dasm-system
 libdsk:format pcw800
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
'''
    (output/'diskdefs').write_text(defs)
    definition = 'dasm-system' if native else 'bettercpm-default'
    raw = output/'system.raw'
    raw.write_bytes(extract_raw(image) if native else image)
    def tool(*args):
        return subprocess.run(list(map(str,args)), cwd=output, check=True, capture_output=True)
    if not native:
        system_raw=output/'boot.raw'
        shutil.copyfile(raw,system_raw)
        tool('mkfs.cpm','-f',definition,raw)
    for name, data in files.items():
        host = output/name
        host.write_bytes(data)
        target=system_raw if not native and (name.startswith('DM') or name=='QUALIFY.SUB') else raw
        tool('cpmcp','-T','raw','-f',definition,target,host,'0:'+name)
    utility_members={}
    if utility_files:
        utility_raw=output/'utilities-audit.raw'
        if native:
            fmt=select_fdf(ROOT/'third_party/montezuma/DISK-INT.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
            utility_raw.write_bytes(dmk_to_raw(ub,fmt))
        else:utility_raw.write_bytes(ub)
        utility_definition='bettercpm-mm-80t-ds-data' if native else 'bettercpm-default'
        for member,expected in utility_files.items():
            extracted=output/('utilities-'+member)
            tool('cpmcp','-T','raw','-f',utility_definition,utility_raw,'0:'+member,extracted)
            actual=extracted.read_bytes()
            assert actual[:len(expected)]==expected and len(expected)<=len(actual)<=(len(expected)+127)//128*128,('packaged member mismatch',member)
            assert set(actual[len(expected):])<={0,26},('packaged padding mismatch',member)
            utility_members[member]=hashlib.sha256(actual).hexdigest()
    if setup:setup(raw,definition,output)
    if native:
        data = bytearray(raw.read_bytes())
        for i in range(DIRECTORY_ENTRIES):
            at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
            if data[at] == 0 and data[at+1:at+12] == b'STARTUP SUB':
                data[at]=0xe5
        add_file(data,'STARTUP.SUB',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nSUBMIT QUALIFY\r\n\x1a')
        disk=output/'a.dmk';disk.write_bytes(make_dmk(data))
        (output/'b.dmk').write_bytes(ub)
        args=[str(emulator),'-m4','-batch','-turbo','-ktx','-d0',str(disk),
              '-d1',str(output/'b.dmk'),'-itime','60000','-id','300','-it']
        for i in range(len(commands)):
            args += ['-iw',f'DASM STEP {i} DONE','-it']+key_args('\r',25)+['-id','60']
        if interactive_launch:args += ['-iw','*']
        for index,(outgoing,wanted,timeout) in enumerate(interactive):
            frames=interactive_frames[index] if interactive_frames is not None else 120
            ready=interactive_ready[index] if interactive_ready is not None else None
            if outgoing==b'\x03' and ready:
                # M4_IN debounces by waiting for physical key release before
                # returning ETX. Hold through a blocking sector operation, then
                # release before waiting for the application's abort question.
                args += ['-ik','6','4','-id','1200','-ik','6','0','-id','60','-iw',ready]
            else:
                args += key_args(outgoing.decode(),25)
                if ready:args += ['-iw',ready]
            args += ['-id',str(frames),'-it']
        args += ['-ix']
        (output/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
        launch(args,cwd=output,timeout=1800)
        captures=sorted(output.glob('trs80-text-*'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
        logs=[bytes(x&127 for x in p.read_bytes()[:1920]) for p in captures]
        assert len(logs)==1+len(commands)+len(interactive), 'missing native screen captures'
        assert (output/'b.dmk').read_bytes()==ub
        raw.write_bytes(extract_raw(disk.read_bytes()))
    else:
        disks=output/'disks';disks.mkdir()
        shutil.copyfile(system_raw,disks/'drivea.dsk')
        for letter in 'bcd':(disks/f'drive{letter}.dsk').write_bytes(ub)
        shutil.copyfile(raw,disks/'drivec.dsk')
        steps=[(b'SUBMIT QUALIFY\r',f'DASM STEP {len(commands)-1} DONE'.encode(),240),
               (b'',b'C0>_ ',30)] + list(interactive)
        logs=[session(SIMULATOR,disks,steps,output/'transcript.bin')]
        shutil.copyfile(disks/'drivec.dsk',raw)
        shutil.copyfile(disks/'drivea.dsk',system_raw)
        assert (disks/'driveb.dsk').read_bytes()==ub
    log=b'\n'.join(logs);(output/'console.bin').write_bytes(log)
    recovered={}
    for name in extract:
        target=output/('after-'+name)
        volume=system_raw if not native and (name.startswith('DM') or name=='QUALIFY.SUB') else raw
        tool('cpmcp','-T','raw','-f',definition,volume,'0:'+name,target)
        recovered[name]=target.read_bytes()
    for name,data in files.items():
        if name in extract:continue
        target=output/('after-'+name)
        volume=system_raw if not native and (name.startswith('DM') or name=='QUALIFY.SUB') else raw
        tool('cpmcp','-T','raw','-f',definition,volume,'0:'+name,target)
        assert target.read_bytes()[:len(data)]==data, ('input changed',name)
    check=tool('fsck.cpm','-T','raw','-f',definition,'-n',raw)
    (output/'filesystem.txt').write_bytes(check.stdout+check.stderr)
    assert original.read_bytes()==image and utility.read_bytes()==ub
    evidence={'platform':platform,'system_sha256':hashlib.sha256(image).hexdigest(),
              'utilities_sha256':hashlib.sha256(ub).hexdigest(),
              'commands':commands,'utilities_members':utility_members,'input_hashes':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
              'emulator_sha256':hashlib.sha256((emulator if native else SIMULATOR).read_bytes()).hexdigest(),
              'outputs':{n:hashlib.sha256(v).hexdigest() for n,v in recovered.items()},
              'console_sha256':hashlib.sha256(log).hexdigest(),'original_media_unchanged':True}
    (output/'execution.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return log,recovered


def cpm_text(text):
    return text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')+b'\x1a'


def compact_source(text):
    """Discard comments outside quoted strings to fit native work media."""
    lines=[]
    for line in text.splitlines():
        quoted=False
        for i,char in enumerate(line):
            if char=="'": quoted=not quoted
            if char==';' and not quoted:
                line=line[:i]
                break
        if line.strip():lines.append(line.rstrip())
    return '\n'.join(lines)+'\n'
