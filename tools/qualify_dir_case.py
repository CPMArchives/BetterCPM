"""Qualify DIR's lowercase filespec correction on private released media."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
CASES=[(':OLDIR *.com','NO FILE'),(':OLDIR *.COM','FILES,'),
       (':DIR *.COM','FILES,'),(':DIR *.com','FILES,'),(':dir *.CoM','FILES,'),
       (':DIR caseone.com','1 FILE,'),(':DIR c?se*.cOm','1 FILE,'),
       (':DIR a0:*.com /s=n /c=2','FILES,'),
       (':DIR a0:caseone.com /whereis','1 MATCH'),
       (':DIR absent.com','NO FILE'),(':DIR c*a.com','Invalid filespec.'),
       ('DIR *.com','CASEONE'),('TYPE DIRRDY.TXT','DIR CASE CCP READY')]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=('z80pack','trs80gp'),required=True)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify-existing',action='store_true',help='Audit a completed capture without replaying guest commands')
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=a.verify_existing)
    (w/'report.json').unlink(missing_ok=True)
    native=a.target=='trs80gp';original=a.system.read_bytes()
    baseline=extract_raw(original) if native else original
    raw=w/'system.raw';raw.write_bytes(baseline)
    defs='diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n' if native else disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT))
    (w/'diskdefs').write_text(defs)
    def cpm(tool,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(raw),*map(str,args)],cwd=w,check=True,capture_output=True)
    def read(name):
        out=w/'readback';cpm('cpmcp','0:'+name,out);return out.read_bytes()
    names=re.findall(r'^[a-z0-9$][a-z0-9_$.-]*\.[a-z0-9$]+$',cpm('cpmls').stdout.decode(),re.M|re.I)
    assert len(names)>20
    before={n:sha(read(n)) for n in names if n.upper()!='DIR.COM'}
    files={'DIR.COM':a.binary.read_bytes(),'OLDIR.COM':a.reference.read_bytes(),
           'CASEONE.COM':b'CASE MATCH\r\n\x1a','CASEONE.DAT':b'NONMATCH\r\n\x1a',
           'CASETWO.COM':b'SYSTEM HIDDEN\r\n\x1a','DIRRDY.TXT':b'DIR CASE CCP READY\r\n\x1a'}
    subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(raw),'0:DIR.COM'],cwd=w,check=True,capture_output=True)
    for n,b in files.items():
        f=w/n;f.write_bytes(b);cpm('cpmcp',f,'0:'+n)
    cpm('cpmchattr','s','0:CASETWO.COM')
    prepared={n:sha(read(n)) for n in list(files)+list(before)}
    (w/'prepared.raw').write_bytes(raw.read_bytes())
    frames=[]
    if native:
        disk=w/'system.dmk'
        if not a.verify_existing:disk.write_bytes(make_dmk(raw.read_bytes()))
        args=[str(DEFAULT_EMULATOR),'-m4','-frehd','-batch','-turbo','-na','-ktx','-d0',str(disk),'-itime','60000',
              '-iw','Type TYPE README.TXT for more','-iw','A0>','-id','3000']
        args+=key_args('TYPE DIRRDY.TXT\r')+['-iw','DIR CASE CCP READY','-iw','A0>','-id','3000']
        for command,want in CASES:
            args+=key_args('CLS\r')+['-iw','A0>','-id','1000']
            args+=key_args(command+'\r',preserve_case=True)+['-iw',want,'-iw','A0>','-id','2000','-it']
        args+=['-ix'];(w/'invocation.json').write_text(json.dumps(args,indent=2)+'\n')
        if not a.verify_existing:run(args,cwd=w,timeout=600)
        captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
        assert len(captures)==len(CASES)
        frames=[screen(f) for f in captures]
        for (command,_),text in zip(CASES,frames):assert command in text,(command,text)
        raw.write_bytes(extract_raw(disk.read_bytes()))
    else:
        disks=w/'disks';disks.mkdir(exist_ok=a.verify_existing)
        if not a.verify_existing:shutil.copy2(raw,disks/'drivea.dsk')
        for i,(command,want) in enumerate(CASES):
            trace=(w/f'case-{i}.bin').read_bytes() if a.verify_existing else session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[(command.encode()+b'\r',b'A0>_ ',30)],w/f'case-{i}.bin')
            # Discard startup and character-by-character CCP command echo.
            text=trace.decode('ascii','replace');at=text.index(command+' \r\n')+len(command+' \r\n')
            frames.append(text[at:].split('\r\nA0>')[0]);assert want in frames[-1],(command,frames[-1])
        shutil.copy2(disks/'drivea.dsk',raw)
    for (command,want),text in zip(CASES,frames):assert want in text,(command,text)
    for i in (1,2,3,4,7,11):
        assert 'CASEONE' in frames[i] and 'CASETWO' not in frames[i] and ' DAT' not in frames[i],frames[i]
    def entries(text):return re.findall(r'([A-Z0-9]+) +COM',text)
    assert entries(frames[2])==entries(frames[3])==entries(frames[4])==entries(frames[7])
    assert 'CASEONE' in frames[5] and 'CASEONE' in frames[6] and 'A0:CASEONE.COM' in frames[8]
    reserved=20480 if native else 27648
    assert raw.read_bytes()[:reserved]==baseline[:reserved]
    for n,h in prepared.items():assert sha(read(n))==h,n
    subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(raw)],cwd=w,check=True,capture_output=True)
    assert a.system.read_bytes()==original
    for i,text in enumerate(frames):(w/f'case-{i}.txt').write_text(text.replace('\r\n','\n').rstrip()+'\n')
    result={'status':'PASS','target':a.target,'system_sha256':sha(original),'binary_sha256':sha(files['DIR.COM']),
            'reference_sha256':sha(files['OLDIR.COM']),'cases':CASES,'before_lowercase':'NO FILE',
            'corrected_case_variants_identical':True,'preserved_original_files':list(before),
            'prepared_files_unchanged':True,'reserved_bytes_unchanged':reserved,'original_media_unchanged':True,'filesystem':'PASS'}
    (w/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',a.target,'DIR case variants, before/after, SYS suppression and CCP restoration')


if __name__=='__main__':main()
