#!/usr/bin/env python3
"""Qualify resident TYPE without TYPE.COM on disposable emulator media."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

def main():
    p=argparse.ArgumentParser();p.add_argument('--platform',choices=('z80pack','model4'),required=True)
    p.add_argument('--transient',action='store_true');p.add_argument('--image-dir',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    fixtures=[('ONE.TXT',b'TYPE ONE $ TEXT\r\n\x1aHIDDEN',3,1),
              ('TWO.TXT',b'TYPE TWO TEXT\r\n\x1a',5,2),
              ('LONG.TXT',b''.join(f'TYPE ROW {i:02d}\r\n'.encode() for i in range(30))+b'\x1a',3,0)]
    commands=['TYPE /VER','TYPE A[3,5]:[ $RW]','TYPE A[3,5]:*.TXT[$RO,$SYS]',
              'TYPE A3:ONE.TXT /7','TYPE A3:ONE.TXT','TYPE A5:TWO.TXT']
    expected=['Resident, RCP Build 007','Invalid filespec.','TYPE ONE $ TEXT',
              'Invalid filespec.','TYPE ONE $ TEXT','TYPE TWO TEXT']
    if a.transient:
        commands=[':TYPE /VER',':TYPE A[3,5]:[ $RW]',':TYPE /CTL A[3,5]:*.TXT[$RO,$SYS]',
                  ':TYPE A3:ONE.TXT /7 /T',':TYPE /CTL /T A3:ONE.TXT',':TYPE A5:TWO.TXT /P']
        expected=['BetterCP/M TYPE 1.0 (Build 001)','Invalid filespec.','TYPE ONE $ TEXT^M^J',
                  'TYPE ONE $ TEXT','TYPE ONE $ TEXT^M^J','Invalid filespec.']
    module=(ROOT/'build/cpx/RCP.CPX').read_bytes()
    if a.platform=='z80pack':
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',work/'disks');shutil.copy2(a.image_dir/'diskdefs',work/'diskdefs')
        disk=work/'disks/drivea.dsk'
        def cpm(tool,*values):
            subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True,stdout=subprocess.DEVNULL)
        cpm('cpmrm','0:*.*')
        f=work/'RCP.CPX';f.write_bytes(module);cpm('cpmcp',f,'0:RCP.CPX')
        if a.transient:cpm('cpmcp',ROOT/'build/utilities/TYPE.COM','0:TYPE.COM')
        for name,data,user,mask in fixtures:
            f=work/name;f.write_bytes(data);cpm('cpmcp',f,f'{user}:{name}')
            if mask:cpm('cpmchattr','r' if mask==1 else 's',f'{user}:{name}')
        before=disk.read_bytes()
        sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
        for i,(command,wanted) in enumerate(zip(commands,expected)):
            out=session(sim,work/'disks',[(command.encode()+b'\r',b'A0>_ ',60)],work/f'case-{i}.txt').decode(errors='replace')
            assert wanted in out and 'HIDDEN' not in out,(command,out)
            if i==2:assert 'TYPE TWO TEXT' in out and '----------' in out,out
        for key in (() if a.transient else (b'.',b' ')):
            out=session(sim,work/'disks',[(b'TYPE A3:LONG.TXT /P\r',b'--More--',60),(key,b'A0>_ ',60)]).decode(errors='replace')
            assert 'TYPE ROW 29' in out,out
        if not a.transient:
            out=session(sim,work/'disks',[(b'TYPE A3:LONG.TXT /P\r',b'--More--',60),(b'\x03',b'A0>_ ',60)]).decode(errors='replace')
            assert 'TYPE ROW 29' not in out,out
        assert disk.read_bytes()==before,'TYPE modified source disk'
    else:
        extras=[*fixtures,('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes())]
        if a.transient:extras.append(('TYPE.COM',(ROOT/'build/utilities/TYPE.COM').read_bytes()))
        script=[]
        for i,command in enumerate(commands):
            script += [command,f'CHECK{i}']
            extras.append((f'CHECK{i}.COM',bytes.fromhex('110b010e09cd0500c30000')+f'\r\nTYPE CHECK {i}\r\n$'.encode()))
        extras.append(('CASE.SUB',('\r\n'.join(script).replace('$','$$')+'\r\n').encode()+b'\x1a'))
        disk=work/'a.dmk';disk.write_bytes(medium(extras));before=disk.read_bytes()
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']+keys('SUBMIT CASE\r')+['-itime','0']
        for i in range(len(commands)):invocation+=['-iw',f'TYPE CHECK {i}','-it']
        invocation+=['-ix'];run(invocation,cwd=work,timeout=300,check=True)
        for i,wanted in enumerate(expected):
            out=screen(work/f'trs80-text-{i+1}.bin');(work/f'case-{i}.txt').write_text(out)
            assert wanted in out and 'HIDDEN' not in out,(i,out)
            if i==2:assert 'TYPE TWO TEXT' in out and '----------' in out,out
        # SUBMIT consumes its queue; compare selected files, not the whole system disk.
        from add_cpm_file_to_dmk import extract_raw
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
        from test_model4_copy import files
        old=files(extract_raw(before)[FILESYSTEM_FIRST_SECTOR*512:])
        new=files(extract_raw(disk.read_bytes())[FILESYSTEM_FIRST_SECTOR*512:])
        for name,_,user,_ in fixtures:
            stem,ext=name.split('.');key=(user,(stem.ljust(8)+ext.ljust(3)).encode())
            assert old[key]==new[key],name
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'commands':commands,'transient':a.transient,'rcp_sha256':hashlib.sha256(module).hexdigest()},indent=2)+'\n')
    print(f'PASS: {"transient" if a.transient else "resident"} TYPE selectors, protected text, separators, syntax, EOF, version and unchanged source on {a.platform}')
if __name__=='__main__':main()
