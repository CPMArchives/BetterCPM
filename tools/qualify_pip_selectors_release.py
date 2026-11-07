"""Check expanded PIP selectors on exact release System/work images."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_system_dmk
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from convert_fdf_image import raw_to_dmk, dmk_to_raw
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from build_ccp import assemble

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=('z80pack','trs80gp'),required=True)
    for name in ('system','work-disk','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False);native=a.target=='trs80gp'
    original=a.system.read_bytes();work_original=a.work_disk.read_bytes()
    fmt=select_fdf(ROOT/'metadata/DISK.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
    definitions=disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT))
    if native:definitions+='\ndiskdef release-system\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n'
    (w/'diskdefs').write_text(definitions)
    disks={letter:w/(letter+'.raw') for letter in 'abcd'}
    disks['a'].write_bytes(extract_raw(original) if native else original)
    for letter in 'bcd':disks[letter].write_bytes(dmk_to_raw(work_original,fmt) if native else work_original)
    def definition(letter):return 'release-system' if native and letter=='a' else 'bettercpm-mm-80t-ds-data' if native else 'bettercpm-default'
    def cpm(tool,letter,*args,check=True):return subprocess.run([tool,'-T','raw','-f',definition(letter),str(disks[letter]),*map(str,args)],cwd=w,check=check,capture_output=True)
    def put(letter,user,name,data):
        f=w/(letter+str(user)+'-'+name);f.write_bytes(data)
        cpm('cpmrm',letter,f'{user}:{name}',check=False);cpm('cpmcp',letter,f,f'{user}:{name}')
    def get(letter,user,name):
        f=w/'readback';f.unlink(missing_ok=True);cpm('cpmcp',letter,f'{user}:{name}',f,check=False)
        return f.read_bytes() if f.exists() else None
    pip=get('a',0,'PIP.COM');assert pip is not None
    # Exercise the program delivered in the System, without substituting a build.
    expected_pip=(ROOT/'build/pip-development/PIP.COM').read_bytes()
    assert pip[:len(expected_pip)]==expected_pip and set(pip[len(expected_pip):])<={0,26}
    pip=expected_pip
    expected={'PSZERO.COM':b'0'*128,'PSLAST.COM':b'Z'*33024,'PSSYS.COM':b'S'*128}
    put('b',0,'PSZERO.COM',expected['PSZERO.COM']);put('b',31,'PSLAST.COM',expected['PSLAST.COM']);put('c',7,'PSSYS.COM',expected['PSSYS.COM'])
    cpm('cpmchattr','c','s','7:PSSYS.COM')
    for user,byte in ((7,b'1'),(9,b'2')):put('b',user,'PDNAME.COM',byte*128)
    put('b',0,'PDUNIQ.COM',b'3'*128);old=b'D'*128;staging=b'T'*128
    put('d',5,'PDNAME.COM',old);put('d',5,'PDNAME.$$$',staging)
    for index in (1,):
        code=f'''        ASEG
        ORG 100H
        LD DE,MSG
        LD C,9
        CALL 5
        LD C,1
        CALL 5
        JP 0
MSG:    DB 'PIP CHECK {index:02d}','$'
'''
        data=assemble(Path.home()/'bin/z80asm',code,w/f'RP0{index}.COM',w/f'rp0{index}.lst',256);put('a',0,f'RP0{index}.COM',data)
    batch=b'CLS\r\n:PIP D4:=[B[0,31],C7]:PS*.COM[RV]\r\nRP01\r\n\x1a'
    put('a',0,'PIPTEST.SUB',batch)
    startup=(b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n' if native else b'')+batch
    put('a',0,'STARTUP.SUB',startup);before={letter:disks[letter].read_bytes() for letter in 'bc'}
    if native:
        images={letter:w/(letter+'.dmk') for letter in 'abcd'}
        images['a'].write_bytes(make_system_dmk(disks['a'].read_bytes()))
        for letter in 'bcd':images[letter].write_bytes(raw_to_dmk(disks[letter].read_bytes(),fmt))
        args=[str(DEFAULT_EMULATOR),'-m4','-frehd','-batch','-turbo','-na','-ktx','-itime','60000']
        for i,letter in enumerate('abcd'):args+=['-d'+str(i),str(images[letter])]
        args+=['-iw','PIP CHECK 01','-id','1000','-it']+key_args('\r')
        args+=['-iw','A0>','-id','2000']+key_args('CLS\r')+['-id','1500']
        args+=key_args(':PIP D5:=B[-]:PD*.COM[VW]\r')+['-id','8000','-iw','No files copied.','-id','2000','-it']
        args+=key_args('CLS\r')+['-id','1500']+key_args(':PIP /VER\r')
        from utility_versions import banner
        args+=['-iw',banner('PIP'),'-id','3000','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
        run(args,cwd=w,timeout=900)
        captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==3
        text='\n'.join(screen(p) for p in captures)
        for letter in 'abcd':disks[letter].write_bytes(extract_raw(images[letter].read_bytes()) if letter=='a' else dmk_to_raw(images[letter].read_bytes(),fmt))
    else:
        folder=w/'disks';folder.mkdir()
        for letter in 'abcd':shutil.copy2(disks[letter],folder/f'drive{letter}.dsk')
        steps=[(b'\r',b'A0>_ ',30),(b':PIP D5:=B[-]:PD*.COM[VW]\r',b'A0>_ ',120),(b':PIP /VER\r',b'A0>_ ',30)]
        text=session(a.simulator.resolve(),folder,steps,w/'transcript.bin',initial_prompt=b'PIP CHECK 01').decode('ascii','replace')
        for letter in 'abcd':shutil.copy2(folder/f'drive{letter}.dsk',disks[letter])
    assert 'DUPLICATE DESTINATION NAME' in text and 'No files copied.' in text,text[-2000:]
    assert 'B7:PDNAME.COM' in text and 'B9:PDNAME.COM' in text
    assert 'INVALID FORMAT' not in text and 'VERIFY ERROR' not in text
    for name,data in expected.items():assert get('d',4,name)==data,name
    assert get('d',5,'PDNAME.COM')==old and get('d',5,'PDNAME.$$$')==staging
    assert get('d',5,'PDUNIQ.COM') is None
    for letter,data in before.items():assert disks[letter].read_bytes()==data,letter
    for letter in 'abcd':
        audit=disks[letter]
        if letter=='b':
            # cpmtools' CP/M 2.2 fsck treats supported users 16..31 as bad
            # status bytes. Map only fixture user 31 to unused user 15 on a
            # disposable audit copy; allocation and extent bytes stay intact.
            data=bytearray(audit.read_bytes());mapping=fmt.raw_record_map();changed=0
            for record in range((fmt.drm+1)*32//128):
                track,slot=divmod(fmt.reserved_records+record,fmt.spt)
                at=track*fmt.raw_track_bytes+mapping[slot]*128
                for offset in range(at,at+128,32):
                    if data[offset]==31:data[offset]=15;changed+=1
            assert changed>=2,'user-31 multi-extent fixture missing'
            audit=w/'b-fsck-user15.raw';audit.write_bytes(data)
        subprocess.run(['fsck.cpm','-T','raw','-f',definition(letter),'-n',str(audit)],cwd=w,check=True,capture_output=True)
    assert a.system.read_bytes()==original and a.work_disk.read_bytes()==work_original
    result={'status':'PASS','target':a.target,'system_sha256':sha(original),'work_sha256':sha(work_original),'pip_sha256':sha(pip),
            'scope':['compound and all-user selectors','user 31','SYS/V','multi-extents','duplicate-name preflight with existing destination/staging preserved'],
            'source_images_unchanged':True,'original_media_unchanged':True,'filesystem':'PASS; user-31 status normalized to unused user 15 on disposable fsck-only B copy'}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',a.target,'packaged PIP expanded selectors and collision atomicity')


if __name__=='__main__':main()
