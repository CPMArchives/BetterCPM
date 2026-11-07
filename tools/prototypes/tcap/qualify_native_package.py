#!/usr/bin/env python3
"""Qualify disposable native-reference media in the full Model 4 emulator."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from trs80gp_launch import run
from run_trs80_command import DEFAULT_EMULATOR,key_args
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build,RAW_SIZE
from build_trs80_boot import install_files

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'build/tcap-manager-integration/native-package'


def screen(path):
    return '\n'.join(''.join(chr(c&127) if 32<=c&127<127 else ' ' for c in path.read_bytes()[i:i+80]).rstrip() for i in range(0,1920,80))


def campaign(name,image,commands,second=None):
    out=OUT/name
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-id','5000','-it']
    if second:cmd+=['-d1',str(second)]
    for command in commands:
        cmd+=key_args(command+'\r',delay=8)+['-id','600','-it']
    cmd+=['-ix']
    run(cmd,cwd=out,timeout=120)
    texts=[screen(p) for p in sorted(out.glob('trs80-text-*.bin'))]
    for i,text in enumerate(texts):(out/f'{i:02d}.txt').write_text(text+'\n')
    return texts


def installation_campaign(image,destination,name='install',success=True):
    out=OUT/name
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    manifest=json.loads((OUT/'package-manifest.json').read_text())
    raw=bytearray(extract_raw(image.read_bytes()))
    raw[60*512:]=b'\xe5'*(len(raw)-60*512)
    files=[(n,(OUT/n).read_bytes()) for n in manifest['files']]
    queue=['SETBSYS','INSTALL SYSTEM.SYS B:']
    submit=b''.join(bytes((len(c),))+c.encode()+bytes(127-len(c)) for c in reversed(queue))
    files.append(('$$$.SUB',submit))
    install_files(raw,files,directory=60*512,block_count=385)
    source=OUT/(name+'-source.dmk');source.write_bytes(build(bytes(raw)))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(source),
         '-d1',str(destination),'-itime','20000','-iw','Proceed (Y/N)?','-id','60','-it']
    cmd+=key_args('Y',delay=25)
    cmd+=['-iw','System installed and verified' if success else 'system package is invalid', '-it','-ix']
    run(cmd,cwd=out,timeout=420)
    texts=[screen(p) for p in sorted(out.glob('trs80-text-*.bin'))]
    for i,text in enumerate(texts):(out/f'{i:02d}.txt').write_text(text+'\n')
    return texts


def batch_workflow(name,image,commands):
    manifest=json.loads((OUT/'package-manifest.json').read_text())
    # Fresh disposable filesystem, with stock reverse-order CP/M SUBMIT records.
    # Each checkpoint blocks for one key, so no command depends on keyboard timing.
    raw=bytearray(extract_raw(image.read_bytes()))
    raw[60*512:]=b'\xe5'*(len(raw)-60*512)
    files=[(n,(OUT/n).read_bytes()) for n in manifest['files']]
    queue=[]
    markers=[]
    for i in range(len(commands)+1):
        marker=f'NATIVE STAGE {i:02d}'
        markers.append(marker)
        program=bytes.fromhex('1110010e09cd05000e01cd0500c30000')+marker.encode()+b'$'
        # LD DE points immediately after the 16-byte instruction sequence.
        assert len(bytes.fromhex('1110010e09cd05000e01cd0500c30000'))==16
        files.append((f'R{i:02d}.COM',program))
        queue.append(f'R{i:02d}')
        if i<len(commands):queue.append(commands[i])
    submit=b''.join(bytes((len(c),))+c.encode()+bytes(127-len(c)) for c in reversed(queue))
    files.append(('$$$.SUB',submit))
    install_files(raw,files,directory=60*512,block_count=385)
    disk=OUT/(name+'-batch.dmk');disk.write_bytes(build(bytes(raw)))
    out=OUT/name
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-itime','20000']
    for i,marker in enumerate(markers):
        if i:cmd+=key_args(' ',delay=25)
        cmd+=['-iw',marker,'-it']
    cmd+=['-ix']
    run(cmd,cwd=out,timeout=420)
    texts=[screen(p) for p in sorted(out.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))]
    for i,text in enumerate(texts):(out/f'{i:02d}.txt').write_text(text+'\n')
    return texts


def checksum_campaign():
    import ctypes as C
    import re
    lib=C.CDLL(str(OUT.parent/'packed-core/build/rsx-offline-test/core.so'))
    mem=(C.c_ubyte*65536).in_dll(lib,'memory')
    regs={n:C.c_ubyte.in_dll(lib,n) for n in 'AFBCDEHL'}
    sp=C.c_ushort.in_dll(lib,'SP')
    def address(file,name):
        match=re.search(r'^([0-9a-f]{4}).*?\b'+name+r':',file.read_text(),re.M|re.I)
        assert match,name
        return int(match[1],16)
    def load(at,data):mem[at:at+len(data)]=data
    def pair(name,value):regs[name[0]].value=value>>8;regs[name[1]].value=value&255
    def invoke(pc):
        sp.value=0x3f00
        result=lib.test_run(pc,12000000)
        assert result>=0,(hex(pc),result)
        return bool(regs['F'].value&64)
    import binascii
    counts={}
    boot=(OUT/'boot.bin').read_bytes();load(0x4300,boot)
    crc=address(OUT/'boot.lst','BC_CRC')
    # Exercise every stage-one and resident boundary, not only one damaged byte.
    for name,data,at in (('stage1',(OUT/'stage1.bin').read_bytes().ljust(512,b'\0'),0x5000),
                         ('resident',(OUT/'system-tracks.bin').read_bytes()[1024:17*512],0xd1c4)):
        offsets=(None,0,1,len(data)//2,len(data)-2,len(data)-1)
        for offset in offsets:
            damaged=bytearray(data)
            if offset is not None:damaged[offset]^=1
            load(at,damaged);pair('HL',at);pair('BC',len(data));pair('DE',binascii.crc_hqx(data,65535))
            assert invoke(crc)==(offset is None),(name,offset)
        counts[name]=len(offsets)
    load(0x100,(OUT/'INSTALL.COM').read_bytes())
    verifier=address(OUT/'install.lst','PK_VERIFY')
    payload=(OUT/'system-tracks.bin').read_bytes()
    offsets=(None,0,127,128,383,384,511,512,1023,1024,8703,8704,9728,10752,12800,14848,len(payload)-1)
    for offset in offsets:
        data=bytearray(payload)
        if offset is not None:data[offset]^=1
        load(0x4000,data)
        assert invoke(verifier)==(offset is None),('installer',offset)
    counts['installer_before_write']=len(offsets)
    print('PASS native bootstrap and installer CRC CPU cases',counts,flush=True)
    return counts


def verify_inputs():
    manifest=json.loads((OUT/'package-manifest.json').read_text())
    integration=json.loads((OUT.parent/'report.json').read_text())
    assert integration['identity']==manifest['identity'],'mixed integration/package identities'
    for name,digest in integration['contract']['inputs'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'changed build input: '+name
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,'changed package file: '+name
    for name,key in (('SYSTEM.SYS','package_sha256'),('reference.raw','raw_sha256')):
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==manifest[key],name
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--switch-only',action='store_true')
    a=p.parse_args()
    report_path=OUT/'qualification.json';report_path.unlink(missing_ok=True)
    verify_inputs()
    raw=bytearray((OUT/'reference.raw').read_bytes())
    image=OUT/'qualification.dmk';image.write_bytes(build(bytes(raw)))
    sequence=['RSX LOAD M4SCRN','RSX LOAD ADM3A','ADMAPP','RSX UNLOAD ADM3A',
              'RSX LOAD ANSI','ANSIAPP','RSX LIST','RSX UNLOAD ANSI',
              'RSX LOAD XTCAP','TSCOPE','TBEGIN','TCHECK','RSX UNLOAD XTCAP',
              'RSX UNLOAD M4SCRN','RSX LIST']
    def workflow(label,disk):
        texts=batch_workflow(label,disk,sequence)
        assert len(texts)==len(sequence)+1
        assert 'A0>' in texts[0],texts[0]
        for index,marker in ((3,'ADMAPP NORMAL CONSOLE PASS'),(6,'ANSIAPP NORMAL CONSOLE PASS')):
            assert texts[index].splitlines()[4][9:].startswith(marker),texts[index]
        assert 'ANSI' in texts[7] and 'M4SCRN' in texts[7],texts[7]
        assert 'TSCOPE PASS' in texts[10] and 'FAIL' not in texts[10],texts[10]
        assert 'TCHECK PASS' in texts[12] and 'FAIL' not in texts[12],texts[12]
        assert 'No RSXs loaded' in texts[-1] and 'TPA available: 52K' in texts[-1],texts[-1]
        assert not any('error' in text.lower() or 'not found' in text.lower() or 'FAIL' in text for text in texts),texts
        print('PASS',label,'ADM3A app, unload, ANSI app, TCAP scope/warm recovery/unload and TPA restoration',flush=True)
        return [hashlib.sha256(t.encode()).hexdigest() for t in texts]
    checks={'checksum_cpu':checksum_campaign(),'source_workflow':workflow('switch',image)}
    if a.switch_only:return
    manifest=json.loads((OUT/'package-manifest.json').read_text())
    # Destination is formatted with OFF=3 before installation. Preserve its
    # complete file area, including actual providers and an independent sentinel.
    target=bytearray(b'\xe5'*RAW_SIZE)
    files=[(name,(OUT/name).read_bytes()) for name in manifest['files'] if name!='SYSTEM.SYS']
    files.append(('KEEP.TXT',b'INSTALL MUST PRESERVE THIS FILE\r\n'))
    install_files(target,files,directory=60*512,block_count=385)
    target_before=bytes(target);destination=OUT/'installed.dmk';destination.write_bytes(build(target_before))
    install=installation_campaign(image,destination)
    assert 'B SYSTEM READY' in install[0],install[0]
    assert 'Proceed (Y/N)?' in install[0],install[0]
    assert 'System installed and verified' in install[-1],install[-1]
    installed=extract_raw(destination.read_bytes())
    assert installed[:60*512]==raw[:60*512],'installation changed sealed package bytes'
    assert installed[60*512:]==target_before[60*512:],'installation changed filesystem'
    checks['installation']={'protected_records_verified':240,'file_area_unchanged':True,
                            'installed_payload_sha256':hashlib.sha256(installed[:60*512]).hexdigest()}
    checks['installed_workflow']=workflow('installed-cold',destination)
    for name,offset in (('bad-stage1',512+100),('bad-resident',1024+100),
                        ('bad-resident-padding',1024+7679),('bad-reloader',17*512),
                        ('bad-ccp',29*512+1024+5)):
        damaged=bytearray(raw);damaged[offset]^=1
        disk=OUT/(name+'.dmk');disk.write_bytes(build(bytes(damaged)))
        texts=campaign(name,disk,[])
        assert 'A0>' not in texts[0],(name,texts[0])
        if name=='bad-stage1':assert b'BetterCP/M boot error' in (OUT/name/'trs80-text-0.bin').read_bytes(),texts[0]
        checks[name]={'corrupt_offset':offset,'reached_prompt':False,
                      'screen_sha256':hashlib.sha256(texts[0].encode()).hexdigest()}
        print('PASS',name,'rejected before command prompt',flush=True)
    result={'status':'PASS','emulator_sha256':hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest(),
            'package_manifest_sha256':hashlib.sha256((OUT/'package-manifest.json').read_bytes()).hexdigest(),
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':checks,
            'limits':['emulated Model 4, not physical hardware or native-assembler parity',
                      'private XTCP probe entry offsets; no public request ABI claim',
                      'utility migrations and release assignment deferred']}
    report_path.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS installable native-reference qualification',flush=True)

if __name__=='__main__':main()
