"""Boot packaged engineering media and load the maximum COM with each profile."""
import argparse
import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys

from build_ccp import assemble
from build_montezuma_extended_790k import RAW_SIZE,build as dmk
from build_trs80_boot import install_files
from model2_media import image as imd
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from qualify_tcap_trs80 import screen
from integrated_display_qualification import ROOT

from tcap_test_support import Guest


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path)
    p.add_argument('--platform',choices=('cpmsim','model4','model2'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=ROOT/'build/tcap-cpmsim-emulator/z80pack/cpmsim/cpmsim')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    package=a.package.resolve();folder=package/a.platform
    manifest=json.loads((package/'manifest.json').read_text())['platforms'][a.platform]
    budgets=manifest['budgets'];baseline=54529 if a.platform=='model4' else 57601
    maxima={'MAXBASE':(baseline-256)//128*128}
    for name,short in (('ADM3A','MAXADM'),('VT52','MAXVT'),('ANSI','MAXANSI')):
        maxima[short]=(baseline-1024-budgets[name]['resident_profile_bytes']-256)//128*128
    assembler=Path.home()/'bin/z80asm';files={}
    def program(name,text):
        data=assemble(assembler,'        ASEG\n        ORG 0100H\n'+text+'\n        END\n',out/(name+'.bin'),out/(name+'.lst'),0x100)
        files[name+'.COM']=data;return data
    client=(ROOT/'src/utilities/common/tcap2.inc').read_text()
    for name,size in maxima.items():
        text='''        LD HL,PADDING
        LD BC,%d-(PADDING-0100H)
VERIFY: LD A,(HL)
        CP 0A5H
        JR NZ,BAD
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,VERIFY
        CALL T2_OPEN
        CP %d
        JR NZ,BAD
        LD DE,PASS
        LD C,9
        CALL 5
        LD HL,PADDING
        LD BC,%d-(PADDING-0100H)
WIPE:   LD (HL),0
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,WIPE
        JP 0
BAD:    LD DE,FAIL
        LD C,9
        CALL 5
        JP 0
PASS: DB 'CAPACITY %s %d PASS',13,10,'$'
FAIL: DB 'CAPACITY FAIL',13,10,'$'
'''%(size,1 if name=='MAXBASE' else 0,size,name,size)
        data=program(name,text+client+'\nPADDING:\n');files[name+'.COM']=data.ljust(size,b'\xa5')
    commands=['RSX LIST','MAXBASE','RSX LOAD ADM3A','MAXADM','RSX UNLOAD ADM3A',
        'RSX LOAD VT52','MAXVT','RSX UNLOAD VT52','RSX LOAD ANSI','MAXANSI','RSX UNLOAD ANSI','MAXBASE','RSX LIST']
    report={'status':'RUNNING','platform':a.platform,'maximum_com_bytes':maxima,
        'packaged_image_sha256':manifest['boot_image_sha256'],'checks':[],
        'complete_com_bytes_verified_on_disk':True,'every_loaded_padding_byte_checked':True,
        'padding_cleared_before_warm_return':True,'fixture_drive':'B:' if a.platform=='cpmsim' else 'A:'}
    try:
        if a.platform=='cpmsim':
            shutil.copytree(folder/'disks',out/'disks');shutil.copy2(folder/'diskdefs',out/'diskdefs')
            for name,data in files.items():
                path=out/name;path.write_bytes(data)
                subprocess.run(['cpmcp','-f','bettercpm-default',str(out/'disks/driveb.dsk'),str(path),'0:'+name],cwd=out,check=True,capture_output=True)
            for name,data in files.items():
                check=out/'readback.tmp'
                subprocess.run(['cpmcp','-f','bettercpm-default',str(out/'disks/driveb.dsk'),'0:'+name,str(check)],cwd=out,check=True,capture_output=True)
                assert check.read_bytes()==data,('short or corrupt test file',name)
                check.unlink()
            guest=Guest(a.simulator.resolve(),out/'disks',out)
            try:
                cold=guest.prompt();assert b'?' not in cold and b'error' not in cold.lower(),cold
                for logical in commands:
                    command='B0:'+logical if logical in maxima else logical
                    data=guest.prompt(command)
                    data=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',data)
                    if logical in maxima:assert f'CAPACITY {logical} {maxima[logical]} PASS'.encode() in data
                    assert b'FAIL' not in data and b'error' not in data.lower()
                    report['checks'].append(command)
            finally:guest.close()
            report['transcript_sha256']=sha(out/'transcript.bin')
        else:
            program('MARK',"""        LD DE,MSG
        LD C,9
        CALL 5
        LD HL,82H
        LD B,2
SHOW:   PUSH HL
        PUSH BC
        LD E,(HL)
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ SHOW
        LD A,(82H)
        SUB '0'
        LD B,A
        ADD A,A
        ADD A,A
        ADD A,B
        ADD A,A
        LD B,A
        LD A,(83H)
        SUB '0'
        ADD A,B
        ADD A,'A'
        LD (WANT),A
WAIT:   LD C,1
        CALL 5
        LD HL,WANT
        CP (HL)
        JR NZ,WAIT
        JP 0
WANT: DB 0
MSG: DB 'CAPACITY STEP $'
""")
            queue=[]
            for i in range(len(commands)+1):
                queue.append(f'MARK {i:02d}')
                if i<len(commands):queue.append(commands[i])
            files['CAPRUN.SUB']=('\r\n'.join(queue)+'\r\n\x1a').encode()
            for path in folder.iterdir():
                if path.suffix.upper() in ('.COM','.RSX','.CPX','.SYS','.SUB','.TXT'):
                    files[path.name]=path.read_bytes()
            assert 'SUBMIT.COM' in files,'compile the existing ordinary SUBMIT for this platform first'
            payload=files['SYSTEM.SYS'][128:]
            m2=a.platform=='model2'
            if m2:
                disk=out/'capacity.imd';disk.write_bytes(imd(payload,list(files.items())))
            else:
                raw=bytearray(b'\xe5'*RAW_SIZE);raw[:len(payload)]=payload
                install_files(raw,list(files.items()),directory=20480,block_count=(RAW_SIZE-20480)//2048)
                disk=out/'capacity.dmk';disk.write_bytes(dmk(raw))
            from package_integrated_tcap import native_files
            observed=native_files(disk,a.platform)
            for name,size in maxima.items():
                assert observed[name+'.COM']==files[name+'.COM'],('short or corrupt test file',name,size)
            def key(value):return ['-i',value,'-id','60'] if m2 else key_args(value,delay=25)
            args=[str(DEFAULT_EMULATOR),'-m2' if m2 else '-m4','-batch','-turbo','-itime','20000','-d0',str(disk)]
            args+=['-mem','64'] if m2 else ['-ktx']
            args+=['-iw','A0>','-id','300','-it']+key('SUBMIT CAPRUN\r')
            args+=['-iw','CAPACITY STEP 00','-it']
            for i,_ in enumerate(commands):
                args+=['-id','60']+key(chr(65+i))+['-iw',f'CAPACITY STEP {i+1:02d}','-it']
            args+=['-ix'];(out/'arguments.json').write_text(json.dumps(args,indent=2)+'\n')
            run(args,cwd=out,timeout=900)
            captures=sorted(out.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
            assert len(captures)==len(commands)+2
            cold=screen(captures[0]);assert 'A0>' in cold and '\n?\n' not in cold and 'error' not in cold.lower(),cold
            for i,(command,capture) in enumerate(zip(commands,captures[2:])):
                text=screen(capture).split(f'CAPACITY STEP {i+1:02d}',1)[0]
                assert 'FAIL' not in text and 'error' not in text.lower(),text
                if command in maxima:assert f'CAPACITY {command} {maxima[command]} PASS' in text,(command,text)
                report['checks'].append(command)
            report['captures']={p.name:sha(p) for p in captures}
        report.update(status='PASS packaged cold boot and actual maximum COM loads with each profile',permanent_memory_loss_bytes=0)
    except BaseException as error:
        report.update(status='FAIL',detail=str(error));raise
    finally:(out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
