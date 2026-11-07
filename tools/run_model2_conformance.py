#!/usr/bin/env python3
"""Prepare and run independent CP/M 2.2 groups and Model II boundary probes."""
import argparse
import hashlib
import json
import math
import fcntl
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_ccp import assemble
from model2_media import geometry, image
from qualify_numeric_path_trs80 import marker
from startup_record import build as startup_record
from run_model2_qualification import EMU, EMU_SHA, ROOT, screen, sha
from test_model2_release_media import DISKDEFS, decoded
from trs80gp_launch import launch_services_lookup, run

SUITE_REV = 'a9a878fcd2e36698c7e856654a85847a004fdd20'
SUITE = ROOT.parent/'BetterCPM-release-push/build/rc564-conformance-suite'
MEDIA = ROOT/'build/conformance11-candidate'
PACKET = ROOT/'build/model2-conformance11'
CPMTOOLS = ROOT.parent/'post-1.0-model2-formats/cpmtools-posix'
GROUPS = (
    ('CPUTEST','/ALL',2), ('ECOTEST','/GROUP:REQUIRED',1),
    ('DISKTEST','/SAFE',7), ('CCPTEST','/GROUP:REQUIRED',12),
    ('ENTRYTST','/GROUP:REQUIRED',25), ('BIOSTEST','/SAFE',5), ('ERRTEST','/SAFE',5),
    ('DIRTEST','/SAFE',49), ('BDOSTEST','/GROUP:REQUIRED',56),
    ('FILETEST','/GROUP:REQUIRED',68), ('RANDTEST','/SAFE',39))
CHECKS = ('last-block','write-protect','directory-full','file-ro-0368','file-ro-0369','keyboard','config-rejection','config-persistence')
DISK_RO = tuple(f'disk-ro-{card:04d}' for card in range(379,385))
FAULTS = ('fault-suspended','fault-ignore','fault-abort')
SWAPS = ('media-change-write','media-change-reset')
CHECKS += DISK_RO + FAULTS + SWAPS
OFFSET=26*128+3*8192


def write_json(path, data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n')
    tmp.replace(path)


def validate(condition, message):
    if not condition:raise ValueError(message)


def disk(files=()):
    return image(bytes(20480),files,bootable=False)


def allocation(raw):
    fmt=geometry()
    used=set(range(fmt.directory_blocks))
    occupied=0
    for i in range(fmt.drm+1):
        record=raw[OFFSET+i*32:OFFSET+(i+1)*32]
        if record[0]==0xe5:continue
        validate(record[0]<32,'invalid directory user')
        occupied+=1
        for j in range(16,32,2):
            block=int.from_bytes(record[j:j+2],'little')
            if block:
                validate(fmt.directory_blocks<=block<=fmt.dsm and block not in used,
                         f'invalid or overlapping block {block}')
                used.add(block)
    return len(used),occupied


def suite_blob(suite, filename):
    return subprocess.check_output(['git','-C',str(suite),'show',f'{SUITE_REV}:suite/{filename}'])


def compiled(asm,work,name,source):
    return assemble(asm,source,work/(name+'.COM'),work/(name+'.lst'),0x100)


def prepare(packet,media,suite,cpmtools):
    validate(not packet.exists(),'packet already exists; select another --packet')
    packet.parent.mkdir(parents=True,exist_ok=True)
    system=media/'Model-II-System-candidate.imd'
    manifest=json.loads((media/'candidate.json').read_text())
    validate(manifest['profile']=='model2-fullram' and manifest['planned_tpa']==57344 and
             sha(system)==manifest['files'][system.name],'incorrect Model II System Disk')
    asm=Path.home()/'bin/z80asm'
    validate(sha(asm)==manifest['assembler_sha256'],'assembler differs from System Disk producer')
    hashes={name:digest for digest,name in (l.split() for l in suite_blob(suite,'build/SHA256SUMS.txt').decode().splitlines() if l.strip())}
    payload_names=subprocess.check_output(['git','-C',str(suite),'ls-tree','--name-only',
                                          SUITE_REV+':suite/runtime-payload'],text=True).splitlines()
    payload=[(n,suite_blob(suite,'runtime-payload/'+n)) for n in payload_names if n.endswith(('.DAT','.CFG'))]
    with tempfile.TemporaryDirectory(dir=packet.parent) as tmp:
        root=Path(tmp)/'packet';root.mkdir()
        work=Path(tmp)/'asm';work.mkdir()
        programs={}
        for name,_,_ in GROUPS:
            data=suite_blob(suite,'build/'+name+'.COM')
            validate(hashlib.sha256(data).hexdigest()==hashes[name+'.COM'],name+' program hash')
            programs[name]=data
        probes={}
        for name,source in [('LASTCHK','lastblock'),('WPCHK','writeprotect'),('KCASE','keycase'),('BGET','livebinding')]:
            probes[name]=compiled(asm,work,name,(ROOT/'tests/fixtures/model2'/(source+'.mac')).read_text())
        external = ROOT/'tests/fixtures/conformance'
        probes['FAULTIO'] = compiled(asm,work,'FAULTIO',(external/'faultmore.mac').read_text())
        # Keep A exactly as shipped. The independent C anchor evicts the directory cache.
        media_probe = (external/'media-change-probe.mac').read_text()
        old = "ANCHOR: DB 1,'ANCHOR  DAT'"
        validate(media_probe.count(old)==1,'media-change anchor changed')
        probes['MEDIA'] = compiled(asm,work,'MEDIA',media_probe.replace(old,old.replace('DB 1','DB 3')))
        from run_validation_sequential_directory_full import SOURCE
        for name,fn in [('FDSEQ',21),('FDRAND',34)]:
            code=SOURCE.replace('@EXT@','0').replace('@RECORD@','128').replace('@FUNCTION@',str(fn))
            probes[name]=compiled(asm,work,name,code if fn==21 else code.replace('SEQ STATUS','RAND STATUS'))
        probes['BOOTOK']=marker('PERSISTED STARTUP EXECUTED')
        probes['STATE']=compiled(asm,work,'STATE',(ROOT/'tests/fixtures/conformance/returnstate.mac').read_text())
        shutil.copyfile(system,root/'system.imd')
        (root/'diskdefs').write_text(DISKDEFS)
        tools={}
        for name in ('fsck.cpm','cpmcp'):
            path=(cpmtools/name).resolve()
            validate(path.is_file(),f'missing {name}; supply --cpmtools with POSIX raw-file tools')
            tools[name]={'path':str(path),'sha256':sha(path)}

        blobs={};cases={}
        def keep(content):
            digest=hashlib.sha256(content).hexdigest()
            if digest not in blobs:
                filename=digest+'.imd';(root/filename).write_bytes(content);blobs[digest]=filename
            return blobs[digest]
        cross=disk([('BTBFILE.DAT',(b'BFILE-000 '*15)[:128])])
        fmt=geometry()
        total=fmt.dsm+1
        full=[('BTFULL.DAT',bytes(127*128)+b'FULL-127'+bytes(120)),('BTREL.DAT',bytes(128)),
              ('BTFILL.DAT',bytes((total-fmt.directory_blocks-8-1)*2048))]
        _,entries=allocation(decoded(disk(full))[2])
        full.extend((f'F{i:07}.DAT',b'') for i in range(fmt.drm+1-entries))
        full_disk=disk(full)
        validate(allocation(decoded(full_disk)[2])==(total,128),'full D fixture')
        for name,selector,count in GROUPS:
            files=[(name+'.COM',programs[name]),*payload]
            if name=='BDOSTEST':files.extend([('BDSA.TMP',b''),('BDSB.TMP',b'')])
            if name=='RANDTEST':
                used,_=allocation(decoded(disk(files))[2])
                files.append(('RANDFILL.DAT',bytes((total-used-1)*fmt.block_bytes)))
            b=disk(files)
            if name=='RANDTEST':validate(allocation(decoded(b)[2])[0]==total-1,'RANDTEST needs one free block')
            mounts={'b':keep(b),'c':keep(cross)}
            if name in ('FILETEST','RANDTEST'):mounts['d']=keep(full_disk)
            cases[name.lower()]={'command':name+' '+selector,'expected':count,'mounts':mounts}
        last=disk([('FILL.DAT',bytes((total-fmt.directory_blocks-1)*2048)),('LAST.DAT',b'S'*2048)])
        raw=decoded(last)[2]
        validate(allocation(raw)[0]==total and raw[-2048:]==b'S'*2048,'final block fixture')
        helpers=keep(disk([(k+'.COM',v) for k,v in probes.items()]+[('RANDTEST.COM',programs['RANDTEST']),
                      ('DISKTEST.COM',programs['DISKTEST']),('ANCHOR.DAT',b'CACHE EVICTION')]))
        crowded=disk([('SOURCE.DAT',bytes((i*29+7)&255 for i in range(16384)))]+
                     [(f'F{i:07}.DAT',b'') for i in range(127)])
        validate(allocation(decoded(crowded)[2])==(10,128),'directory-full, disk-not-full fixture')
        protected=disk([('BTRO.DAT',dict(payload)['BTRO.DAT'])])
        validate(decoded(protected)[2][OFFSET+9]&128,'read-only file attribute absent')
        for case,b in [('last-block',last),('write-protect',last),('directory-full',crowded),
                       ('file-ro-0368',protected),('file-ro-0369',protected),('keyboard',disk()),('config-rejection',disk()),
                       ('config-persistence',disk())]:
            cases[case]={'mounts':{'b':keep(b),'c':helpers}}
        for name in DISK_RO:
            cases[name] = {'mounts':{'b':keep(full_disk),'c':helpers}}
        for name in FAULTS:
            cases[name] = {'mounts':{'b':keep(disk([('BTONE.DAT',b'HEALTHY READ AFTER ABORT\r\n\x1a')])),'c':helpers}}
        for name in SWAPS:
            cases[name] = {'mounts':{'b':keep(disk([('OLD.TXT',b'ORIGINAL MEDIA SENTINEL')])),'c':helpers},
                           'replacement':keep(disk([('NEW.TXT',b'REPLACEMENT SENTINEL')]))}
        # Independent filesystem checker for every distinct prepared fixture.
        for filename in ['system.imd',*blobs.values()]:
            fsck(root/filename,Path(tmp),root/'diskdefs',tools)
        # Verify the actual on-disk executables and both user areas through cpmtools.
        for name,_,_ in GROUPS:
            raw=decoded((root/cases[name.lower()]['mounts']['b']).read_bytes())[2]
            rawfile=normalized(raw,Path(tmp))
            for guest,desired in [('0:'+name+'.com',programs[name]),('1:btusr.dat',dict(payload)['BTUSR.DAT'])]:
                extracted=Path(tmp)/'extracted.bin'
                cpm('cpmcp',[rawfile,guest,extracted],Path(tmp),root/'diskdefs',tools)
                validate(extracted.read_bytes()==desired.ljust(math.ceil(len(desired)/128)*128,b'\x1a'),guest)
        info={'schema':1,'platform':'trs80m2','profile':manifest['profile'],'source_revision':manifest['source_revision'],
              'system_sha256':sha(system),'suite_revision':SUITE_REV,'emulator_sha256':EMU_SHA,'tools':tools,
              'program_sha256':{n:hashes[n+'.COM'] for n in programs},'fixtures':blobs,'cases':cases}
        write_json(root/'packet.json',info)
        root.rename(packet)
    print(f'Prepared {len(cases)} independent cases in {packet}',flush=True)


def normalized(raw,folder):
    path=folder/'filesystem.raw'
    path.write_bytes(raw[:3328]+bytes(4864)+raw[3328:])
    return path


def cpm(tool,args,folder,defs,tools):
    env=dict(os.environ,DISKDEFS=str(defs.resolve()))
    # POSIX cpmtools searches the current directory for diskdefs.
    if defs.resolve()!=(folder/'diskdefs').resolve():shutil.copyfile(defs,folder/'diskdefs')
    p=subprocess.run([tools[tool]['path'],'-f','bcm2ss',*map(str,args)],cwd=folder,
                     env=env,text=True,capture_output=True)
    validate(p.returncode==0,f'{tool}: {p.stdout} {p.stderr}')
    return p.stdout


def fsck(path,folder,defs,tools):
    raw=decoded(path.read_bytes())[2]
    checked=cpm('fsck.cpm',['-n',normalized(raw,folder)],folder,defs,tools)
    return checked


def commands(name,case):
    def send(text):return ['-i',text+'\r']
    def mark(text):return ['-iw',text,'-id','1200','-it']
    begin=['-iw','A0>','-id','300','-it']
    if 'expected' in case:
        return begin+send('B:')+mark('B0>')+send(case['command'])+mark('Summary: ')+['-ix']
    if name in ('last-block','write-protect'):
        key,marker=('LASTCHK','FINAL BLOCK READ WRITE') if name=='last-block' else ('WPCHK','MEDIA WRITE PROTECT')
        protect=['-im','wp','1','on'] if name=='write-protect' else []
        return begin+protect+send('C0:'+key)+mark(marker)+['-ix']
    if name=='directory-full':
        return begin+send('B:')+mark('B0>')+send('C0:FDSEQ')+mark('SEQ STATUS')+['-id','4000']+send('C0:FDRAND')+mark('RAND STATUS')+['-ix']
    if name.startswith('file-ro'):
        item=name[-4:]
        return begin+send('B:')+mark('B0>')+send('C0:RANDTEST /'+item+':REPORT')+mark('File R/O')+['-id','4000']+send('C0:STATE')+mark('STATE D=01 U=00 TOP=E101')+['-ix']
    state = ['-id','6500']+send('C0:STATE')+mark('STATE D=01 U=00 TOP=E101')+['-ix']
    if name in DISK_RO:
        return (begin+send('B:')+mark('B0>')+send('C0:DISKTEST /'+name[-4:])
                +mark('Enter its configured drive letter')+['-i','B']+mark('Disk R/O')+state)
    if name in FAULTS:
        start = begin+send('B:')+mark('B0>')+send('C0:FAULTIO')+mark('Bad Sector')
        if name=='fault-suspended':
            return start+['-id','6000','-it','-ix']
        if name=='fault-abort':
            return start+['-i','\x03','-id','10000']+send('TYPE BTONE.DAT')+mark('HEALTHY READ AFTER ABORT')+state
        return (start+['-i','I']+mark('READ CALLER RESUMED after operator ignore.')
                +['-id','2000','-i','I']+mark('FAULT PROVIDER COMPLETED BOTH CALLS')+state)
    if name in SWAPS:
        text = 'OR-0143 RESET AND CREATE PASS' if name.endswith('reset') else 'Disk R/O'
        arg = ' R' if name.endswith('reset') else ''
        return (begin+send('C0:MEDIA'+arg)+mark('OR-0143 SWAP LOGGED B NOW')
                +['-im','eject','1','1','-im','insert','1','replacement.imd','-i','Y']+mark(text)+state)
    if name=='config-rejection':
        return (begin+send('CONFIG /EDIT=B /DSM=292')+mark('Cannot apply logical binding.')
                +['-id','2500']+send('C0:BGET')+mark('LIVE B BINDING')+['-ix'])
    if name=='config-persistence':
        return (begin+send('CONFIG /STARTUP="C0:BOOTOK"')+mark('Save pending cold-boot changes')
                +['-i','Y']+mark('Pending cold-boot changes saved and verified.')+['-ix'])
    if name=='keyboard':
        return begin+['-i','CANCEL\x03','-iw','^C','-id','6000','-it','-i','C0:KCASE AbX\x08cD\r']+mark('EDITED MIXED CASE')+['-ix']
    raise ValueError(name)


def check_filetest_cross_drive(before, after):
    """FILETEST writes one E7h record on C and deletes BTTEMP.DAT."""
    fmt = geometry()
    expected = bytearray(before)
    entries = range(OFFSET, OFFSET + (fmt.drm + 1) * 32, 32)
    changed = [i for i in entries if before[i:i+32] != after[i:i+32]]
    validate(len(changed) == 1, 'expected one deleted cross-drive scratch entry')
    index = changed[0]
    entry = after[index:index+32]
    block = int.from_bytes(entry[16:18], 'little')
    validate(before[index:index+32] == bytes([0xe5])*32 and
             entry == b'\xe5BTTEMP  DAT' + bytes([0, 0, 0, 1]) + entry[16:18] + bytes(14),
             'unexpected FILETEST cross-drive entry')
    validate(fmt.directory_blocks <= block <= fmt.dsm, 'invalid FILETEST scratch allocation')
    for i in entries:
        if before[i] < 32:
            for slot in range(i+16, i+32, 2):
                validate(int.from_bytes(before[slot:slot+2], 'little') != block,
                         'FILETEST scratch overlaps an existing file')
    expected[index:index+32] = entry
    start = OFFSET + block * fmt.block_bytes
    expected[start:start+128] = bytes([0xe7])*128
    validate(after == expected, 'FILETEST changed bytes outside its C scratch record and entry')


def audit(name,case,packet,work,info):
    screens=[screen(p) for p in sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))]
    for i,value in enumerate(screens):(work/f'screen-{i}.txt').write_text(value+'\n')
    validate(screens and 'A0>' in screens[0],'missing cold boot capture')
    for value in screens:
        if any(row in value.splitlines() for row in ('EDITED MIXED CASE FAIL','FINAL BLOCK READ WRITE FAIL',
                'MEDIA WRITE PROTECT FAIL','LIVE B BINDING FAIL','PROBE OPEN FAILED')):
            raise GuestFailure('guest probe reported failure')
    if name=='config-persistence':
        validate(len(screens)==3 and 'Pending cold-boot changes saved and verified.' in screens[2],
                 'CONFIG did not verify the saved startup record')
        cold=screen(work/'cold/trs80-text-0.bin')
        validate('PERSISTED STARTUP EXECUTED' in cold and cold.endswith('A0>'),
                 'cold boot did not execute the saved command and return')
    elif name=='config-rejection':
        validate(len(screens)==3 and 'Cannot apply logical binding.' in screens[1] and
                 'LIVE B BINDING INTACT' in screens[2],'CONFIG did not reject geometry and retain B binding')
    elif 'expected' in case:
        validate(len(screens)==3 and 'B0>' in screens[1],'suite did not start on B0')
        match=re.search(r'Summary:\s*(\d+) pass,\s*(\d+) fail,\s*(\d+) error',screens[2])
        validate(match is not None,'no complete suite summary')
        observed=tuple(map(int,match.groups()))
        if observed[1] or observed[2]:raise GuestFailure(f"{case['command']} returned {observed}")
        validate(observed==(case['expected'],0,0),f"{case['command']} returned {observed}")
    elif name=='directory-full':
        validate(len(screens)==4,'missing directory-full captures')
        for text,label,value in zip(screens[2:],('SEQ','RAND'),('01','05')):
            section=text.rpartition(label+' STATUS ')[2]
            fields=[re.search(label+r' ([0-9A-F]{72})',section) for label in ('BEFORE','AFTER')]
            validate(section.startswith(value) and all(fields),'missing FCB/status '+label)
            if label=='SEQ':validate(fields[0][1]==fields[1][1],'rejected sequential write changed FCB')
    elif name.startswith('file-ro'):
        validate(len(screens)==4 and 'File R/O' in screens[2].splitlines()
                 and 'REQUESTED_SCOPE /'+name[-4:] in screens[2].splitlines()
                 and 'STATE D=01 U=00 TOP=E101' in screens[3],'missing read-only error or WBOOT recovery')
    elif name in DISK_RO:
        validate(len(screens)==5 and name[-4:]+': requesting' in screens[3]
                 and 'Disk R/O' in screens[3].splitlines() and 'STATE D=01 U=00 TOP=E101' in screens[4],
                 'missing disk protection or warm recovery')
    elif name in FAULTS:
        validate('Healthy file read passed' in screens[2] and 'Bad Sector' in screens[2],
                 'missing healthy read and physical-error prompt')
        if name=='fault-suspended':
            validate('Bad Sector' in screens[-1] and 'READ CALLER RESUMED' not in screens[-1],
                     'caller resumed before operator input')
        else:
            validate('STATE D=01 U=00 TOP=E101' in screens[-1], 'no recovered B0 state')
            if name=='fault-ignore':
                validate('READ CALLER RESUMED after operator ignore.' in screens[3]
                         and 'WRITE CALLER RESUMED after operator ignore.' in screens[4]
                         and 'FAULT PROVIDER COMPLETED BOTH CALLS' in screens[4], 'missing ignored error witnesses')
            else:
                validate('HEALTHY READ AFTER ABORT' in screens[3]
                         and all('READ CALLER RESUMED' not in t for t in screens),'abort failed')
    elif name in SWAPS:
        expected = 'OR-0143 RESET AND CREATE PASS' if name.endswith('reset') else 'Disk R/O'
        validate('OR-0143 SWAP LOGGED B NOW' in screens[1] and expected in screens[2]
                 and 'OR-0143 REPLACEMENT READ AND PROTECTED' in screens[2]
                 and 'STATE D=01 U=00 TOP=E101' in screens[3], 'media change recovery')
        original = decoded((packet/case['replacement']).read_bytes())[2]
        revised = decoded((work/'replacement.imd').read_bytes())[2]
        if name.endswith('reset'):
            # The fixture has exactly one live entry. Creating an empty file
            # may occupy exactly one blank directory slot and no data blocks.
            want = bytearray(original)
            changed = [i for i in range(OFFSET, OFFSET+4096,32) if original[i:i+32]!=revised[i:i+32]]
            validate(len(changed)==1 and original[changed[0]]==0xe5,'unexpected directory changes')
            pos = changed[0]
            want[pos:pos+32] = b'\0CREATED TXT'+bytes(20)
            validate(revised==want, 'reset failed to create exactly one empty file')
        else:
            validate(revised==original,'protected replacement media changed')
    elif name=='keyboard':
        validate(len(screens)==3 and '^C' in screens[1] and 'EDITED MIXED CASE PASS' in screens[2],'keyboard / edit / recovery')
    else:
        expected='MEDIA WRITE PROTECT PASS' if name=='write-protect' else 'FINAL BLOCK READ WRITE PASS'
        validate(len(screens)==2 and expected in screens[1],expected+' not observed')
    # Only the CONFIG persistence case may change the System Disk.
    expected_system=bytearray(decoded((packet/'system.imd').read_bytes())[2])
    if name=='config-persistence':
        system_base=int.from_bytes(expected_system[142:144],'little')
        expected_system[128:384]=startup_record('C0:BOOTOK',system_base=system_base)
    validate(decoded((work/'a.imd').read_bytes())[2]==expected_system,'unexpected System disk sector changes')
    for letter,filename in case['mounts'].items():
        path=work/(letter+'.imd')
        after=decoded(path.read_bytes())[2]
        before=decoded((packet/filename).read_bytes())[2]
        if name=='last-block' and letter=='b':
            validate(after[-128:]==b'\xa7'*128 and before[:-128]==after[:-128],
                     'disk change outside expected final record or missing write')
        elif name=='filetest' and letter=='c':
            check_filetest_cross_drive(before,after)
        elif letter!='b' or name in CHECKS:
            validate(before==after,'unexpected change on '+letter.upper())
        else:
            validate(before[:OFFSET]==after[:OFFSET],'reserved surfaces modified on B')
        if before!=after:
            with tempfile.TemporaryDirectory(dir=work) as tmp:
                (work/(letter+'-filesystem.txt')).write_text(fsck(path,Path(tmp),packet/'diskdefs',info['tools']))
    captures={str(p.relative_to(work)):sha(p) for p in sorted(work.rglob('trs80-text-*.bin'))}
    return {'status':'PASS','screens':len(captures),'summary':case.get('expected'),
            'capture_sha256':captures}


class GuestFailure(Exception):
    pass


def execute(packet,info,output,emulator,only,resume):
    selected=only or list(info['cases'])
    validate(all(n in info['cases'] for n in selected),'unknown case')
    for digest,filename in info['fixtures'].items():
        validate(sha(packet/filename)==digest,'fixture hash: '+filename)
    validate(sha(packet/'system.imd')==info['system_sha256'],'System disk hash')
    for tool in info['tools'].values():validate(sha(Path(tool['path']))==tool['sha256'],'cpmtools binary changed')
    validate(sha(emulator)==EMU_SHA and plistlib.loads((emulator.parents[1]/'Info.plist').read_bytes())['CFBundleShortVersionString']=='2.5.8','unexpected emulator')
    if sys.platform=='darwin' and (code:=launch_services_lookup()):
        raise RuntimeError(f'macOS LaunchServices {code}: run Run-Model-II-Conformance.command from Terminal; prepared media are ready')
    output.mkdir(parents=True,exist_ok=True)
    trial=resume.resolve() if resume else Path(tempfile.mkdtemp(prefix='run-',dir=output))
    lock=(trial/'run.lock').open('a')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        raise ValueError('this conformance run is already active') from None
    if resume:
        result=json.loads((trial/'result.json').read_text())
        validate(result['packet_sha256']==sha(packet/'packet.json'),'resume packet differs')
        validate(result['runner_sha256']==sha(Path(__file__)),'resume runner differs')
        validate(not only or list(only)==result['selected'],'resume selection differs')
        selected=result['selected']
    else:
        result={'packet_sha256':sha(packet/'packet.json'),'system_sha256':info['system_sha256'],
                'emulator_sha256':EMU_SHA,'suite_revision':SUITE_REV,'selected':selected,'cases':{},
                'runner_sha256':sha(Path(__file__))}
    print('Model II conformance report:',trial/'result.json',flush=True)
    for name in selected:
        case=info['cases'][name]
        old=result['cases'].get(name,{})
        if old.get('status')=='PASS':
            review=audit(name,case,packet,trial/old['folder'],info)
            validate(review['capture_sha256']==old['capture_sha256'],name+' capture changed since PASS')
            continue
        work=Path(tempfile.mkdtemp(prefix=name+'-',dir=trial))
        item={'folder':work.name,'status':'RUNNING'}
        result['cases'][name]=item;result['status']='RUNNING';write_json(trial/'result.json',result)
        print('Running',name,flush=True)
        try:
            args=[str(emulator),'-m2','-mem','64','-batch','-turbo','-itime','0']
            for idx,letter in enumerate('abcd'):
                filename='system.imd' if letter=='a' else case['mounts'].get(letter)
                if filename:
                    target=work/(letter+'.imd')
                    shutil.copyfile(packet/filename,target)
                    args+=['-d'+str(idx),str(target)]
            if 'replacement' in case:
                shutil.copyfile(packet/case['replacement'],work/'replacement.imd')
            boot=list(args)
            args+=commands(name,case)
            write_json(work/'arguments.json',args)
            run(args,cwd=work,timeout=1200 if name in ('randtest','filetest') else 360)
            if name=='config-persistence':
                cold=work/'cold';cold.mkdir()
                invoke=boot+['-iw','PERSISTED STARTUP EXECUTED','-iw','A0>','-id','300','-it','-ix']
                write_json(cold/'arguments.json',invoke)
                run(invoke,cwd=cold,timeout=180)
            item.update(audit(name,case,packet,work,info))
        except GuestFailure as err:
            item.update(status='FAIL',detail=str(err))
        except (OSError,ValueError,AssertionError,subprocess.SubprocessError) as err:
            item.update(status='INCOMPLETE',detail=str(err))
        write_json(trial/'result.json',result)
        print(item['status'],name,item.get('detail',''),flush=True)
    passed=all(item['status']=='PASS' for item in result['cases'].values())
    failed=any(r['status']=='FAIL' for r in result['cases'].values())
    result['status']='PASS (selected cases)' if passed else ('FAIL' if failed else 'INCOMPLETE')
    write_json(trial/'result.json',result)
    print(result['status'],trial/'result.json',flush=True)
    return 0 if passed else 1


def audit_run(trial, packet, info):
    """Review a completed desktop run without launching or modifying its disks."""
    result = json.loads((trial/'result.json').read_text())
    validate(result['status'] != 'RUNNING', 'desktop run is still active')
    validate(result['packet_sha256'] == sha(packet/'packet.json') and
             result['system_sha256'] == sha(packet/'system.imd') == info['system_sha256'] and
             result['suite_revision'] == info['suite_revision'] == SUITE_REV and
             result['emulator_sha256'] == info['emulator_sha256'] == EMU_SHA,
             'saved run does not match the supplied inputs')
    for digest, filename in info['fixtures'].items():
        validate(sha(packet/filename) == digest, 'fixture changed: '+filename)
    for tool in info['tools'].values():
        validate(sha(Path(tool['path'])) == tool['sha256'], 'cpmtools binary changed')
    cases = {}
    for name in result['selected']:
        row = result['cases'][name]
        work = trial/row['folder']
        case = info['cases'][name]
        try:
            arguments = json.loads((work/'arguments.json').read_text())
            actions = commands(name, case)
            mounts = {'a': 'system.imd', **case['mounts']}
            expected = ['-m2', '-mem', '64', '-batch', '-turbo', '-itime', '0']
            for letter in mounts:
                expected.extend(['-d'+str(ord(letter)-ord('a')), str(work/(letter+'.imd'))])
            validate(arguments[1:] == expected + actions, 'unexpected emulator arguments')
            if name == 'config-persistence':
                cold = json.loads((work/'cold/arguments.json').read_text())
                validate(cold == arguments[:1]+expected+['-iw','PERSISTED STARTUP EXECUTED',
                         '-iw','A0>','-id','300','-it','-ix'], 'unexpected cold-boot arguments')
            checked = audit(name, case, packet, work, info)
            if 'capture_sha256' in row:
                validate(row['capture_sha256'] == checked['capture_sha256'], 'capture changed')
            cases[name] = checked
        except GuestFailure as err:
            cases[name] = {'status':'FAIL', 'detail':str(err)}
        except (ValueError, OSError, AssertionError) as err:
            cases[name] = {'status':'INCOMPLETE', 'detail':str(err)}
    passed = all(v['status'] == 'PASS' for v in cases.values())
    failed = any(v['status'] == 'FAIL' for v in cases.values())
    status = 'PASS (selected cases)' if passed else ('FAIL' if failed else 'INCOMPLETE')
    report = {key:result[key] for key in ('runner_sha256','packet_sha256','emulator_sha256',
                                          'system_sha256','suite_revision')}
    report.update(run=trial.name, status=status, original_status=result['status'],
                  audit_sha256=sha(Path(__file__)), cases=cases)
    write_json(trial/'review.json', report)
    print(status, trial/'review.json', flush=True)
    return 0 if passed else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare',action='store_true')
    p.add_argument('--packet',type=Path,default=PACKET)
    p.add_argument('--media',type=Path,default=MEDIA)
    p.add_argument('--suite',type=Path,default=SUITE)
    p.add_argument('--cpmtools',type=Path,default=CPMTOOLS)
    p.add_argument('--output',type=Path,default=ROOT/'build/model2-conformance-guest')
    p.add_argument('--only',action='append',choices=[n.lower() for n,_,_ in GROUPS]+list(CHECKS))
    p.add_argument('--resume',type=Path)
    p.add_argument('--audit',type=Path,help='recheck a finished run and write review.json without running the emulator')
    p.add_argument('--emulator',type=Path,default=EMU)
    a=p.parse_args()
    if a.audit:
        if a.only or a.prepare or a.resume:
            p.error('--audit reviews the original selection and cannot be combined with --only, --prepare or --resume')
        return audit_run(a.audit.resolve(),a.packet.resolve(),json.loads((a.packet/'packet.json').read_text()))
    if a.prepare:
        prepare(a.packet.resolve(),a.media.resolve(),a.suite.resolve(),a.cpmtools.resolve())
        return 0
    return execute(a.packet.resolve(),json.loads((a.packet/'packet.json').read_text()),
                   a.output.resolve(),a.emulator.resolve(),a.only,a.resume)


if __name__=='__main__':
    try:
        sys.exit(main())
    except (RuntimeError,OSError,ValueError) as err:
        sys.exit(str(err))
