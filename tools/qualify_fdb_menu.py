"""Qualify the FDB main menu and unchanged exits on private released media."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from trs80gp_launch import run

ROOT=Path(__file__).resolve().parents[1]
PROMPT='Your choice: [ ]'
CHOICES='FN LDP ABCE IOS'.replace(' ','')
sha=lambda b:hashlib.sha256(b).hexdigest()


def steps():
    return [('CLS','A0>'),('FDB',PROMPT),('D','Source: catalogue ID,'),('MMI012','Q or BREAK Return:'),('4','Q or BREAK Return:'),('Q',PROMPT),('Q','A0>'),('TYPE MENUOK.TXT','FDB MENU CCP READY'),
            ('CLS','A0>'),('FDB',PROMPT),('\x03','A0>'),('TYPE MENUOK.TXT','FDB MENU CCP READY'),
            ('CLS','A0>'),('FDB',PROMPT),('N',PROMPT),('Q','A0>'),
            ('CLS','A0>'),('FDB',PROMPT),('B','Source file (Return=RAM):'),('','Catalogue ID:'),
            ('MMI012','Q Back:'),('G','Value 0 or 1'),('1','Q Back:'),('Q',PROMPT),
            ('Q','Editor pending: S Save'),('C',PROMPT),('E','Q Back:'),('Q',PROMPT),
            ('\x03','Editor pending: S Save'),('D','A0>'),('TYPE MENUOK.TXT','FDB MENU CCP READY')]


def menu_check(text):
    assert 'FDB 1.01 (003)' in text,text
    for key in CHOICES:assert '[ '+key+' ]' in text,(key,text)
    assert PROMPT in text and 'or Q' in text and 'BREAK (^C)' in text,text
    assert max(map(len,text.splitlines()))<=80,text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=('z80pack','trs80gp'),required=True)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    native=a.target=='trs80gp';original=a.system.resolve().read_bytes()
    baseline=extract_raw(original) if native else original
    raw=w/'system.raw';raw.write_bytes(baseline)
    from build_z80pack_image import disk_definition, DEFAULT_FORMAT
    from fdf_format import select_fdf
    (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n' if native else disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT)))
    def cmd(*args):return subprocess.run(list(map(str,args)),cwd=w,check=True,capture_output=True)
    def get(disk,name,out):
        cmd('cpmcp','-T','raw','-f','bettercpm-default',disk,'0:'+name,out)
        return out.read_bytes()
    listing=cmd('cpmls','-f','bettercpm-default',raw).stdout.decode()
    names=re.findall(r'^[a-z0-9$][a-z0-9_$.-]*\.[a-z0-9$]+$',listing,re.M|re.I)
    assert len(names)>20,listing
    original_files={name:sha(get(raw,name,w/'readback')) for name in names if name.upper() not in ('FDB.COM','FDBVIEW.OVL')}
    artifacts={name:(a.artifacts/name).read_bytes() for name in ('FDB.COM','FDBVIEW.OVL')}
    def put(name,data):
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(raw),'0:'+name],cwd=w,capture_output=True)
        f=w/name;f.write_bytes(data);cmd('cpmcp','-T','raw','-f','bettercpm-default',raw,f,'0:'+name)
    for name,data in artifacts.items():put(name,data)
    put('MENUOK.TXT',b'FDB MENU CCP READY\r\n\x1a')
    flow=steps()
    if native:
        put('MENULOAD.SUB',b'CLS\r\nRSX UNLOAD ADM3A\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\nTYPE MENURDY.TXT\r\n\x1a')
        put('MENURDY.TXT',b'FDB MENU 53K READY\r\n\x1a')
    (w/'steps.json').write_text(json.dumps(flow,indent=2)+'\n')
    menu_frames=[]
    if not native:
        disks=w/'disks';disks.mkdir();shutil.copy2(raw,disks/'drivea.dsk')
        commands=[((s if s=='\x03' else s+'\r').encode(), b'A0>_ ' if want=='A0>' else want.encode(),30) for s,want in flow]
        trace=session(a.simulator.resolve(),disks,commands,w/'transcript.bin')
        text=trace.decode('ascii','replace')
        for part in text.split('FDB 1.01 (003)')[1:]:
            if PROMPT in part:menu_frames.append('FDB 1.01 (003)'+part.split(PROMPT)[0]+PROMPT)
        shutil.copy2(disks/'drivea.dsk',raw)
    else:
        disk=w/'system.dmk';disk.write_bytes(make_dmk(raw.read_bytes()))
        args=[str(DEFAULT_EMULATOR),'-m4','-frehd','-batch','-turbo','-na','-ktx','-d0',str(disk),'-itime','60000','-iw','Type TYPE README.TXT for more','-iw','A0>','-id','3000']
        args+=key_args('SUBMIT MENULOAD\r')+['-iw','FDB MENU 53K READY','-iw','A0>','-id','3000','-it']
        for s,want in flow:
            args+=key_args(s if s=='\x03' else s+'\r')+['-id','6000' if s=='FDB' or s=='' else '3000','-iw','A0>' if want=='A0>' else want,'-id','1000','-it']
        args+=key_args('SUBMIT STARTUP\r')+['-iw','Type TYPE README.TXT for more','-iw','A0>','-id','3000']
        args+=key_args('TYPE MENUOK.TXT\r')+['-iw','FDB MENU CCP READY','-iw','A0>','-id','3000','-it','-ix']
        (w/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
        run(args,cwd=w,timeout=900)
        frames=[screen(f) for f in sorted(w.glob('trs80-text*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))]
        assert len(frames)==len(flow)+2,(len(frames),len(flow))
        assert 'TPA available: 53K' in frames[0],frames[0]
        for i,(_,want) in enumerate(flow):
            assert want in frames[i+1],(i,want,frames[i+1])
            if want==PROMPT:menu_frames.append(frames[i+1])
        text='\n'.join(frames)
        assert 'FDB MENU CCP READY' in frames[-1]
        raw.write_bytes(extract_raw(disk.read_bytes()))
    assert len(menu_frames)>=7,len(menu_frames)
    for text_menu in menu_frames:menu_check(text_menu)
    assert 'Untitled' in text and 'Editor pending: not yet in catalogue.' in text
    for i,text_menu in enumerate(menu_frames):(w/f'menu-{i}.txt').write_text(text_menu+'\n')
    reserved=20480 if native else 27648
    assert raw.read_bytes()[:reserved]==baseline[:reserved]
    for name,digest in original_files.items():assert sha(get(raw,name,w/'readback'))==digest,name
    for name,data in artifacts.items():assert get(raw,name,w/'readback')[:len(data)]==data,name
    cmd('fsck.cpm','-T','raw','-f','bettercpm-default','-n',raw)
    assert a.system.resolve().read_bytes()==original
    result={'status':'PASS','target':a.target,'system_sha256':sha(original),'artifacts':{n:sha(b) for n,b in artifacts.items()},'menu_captures':len(menu_frames),'preserved_files':list(original_files),'reserved_bytes_unchanged':reserved,'original_media_unchanged':True,'exit_cases':['clean Q','clean BREAK','new Untitled Q','pending editor Q/Cancel/Resume','pending editor BREAK/Discard'],'post_exit_file_read':'PASS','filesystem':'PASS'}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',a.target,'menu, pending editor, Q/BREAK and CCP/file restoration')


if __name__=='__main__':main()
