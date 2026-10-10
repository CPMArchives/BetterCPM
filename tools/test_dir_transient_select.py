#!/usr/bin/env python3
"""Qualify DIR selectors and multi-extent sizes with RCP unloaded on both platforms."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--platform',choices=('z80pack','model4'),required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--image-dir',type=Path)
    p.add_argument('--verify-existing',action='store_true',help='Verify saved Model 4 captures without rerunning')
    a=p.parse_args();report=a.report.resolve();report.mkdir(parents=True,exist_ok=a.verify_existing)
    assert not a.verify_existing or a.platform=='model4'
    binary=(ROOT/'build/utilities/DIR.COM').read_bytes()
    fixtures=[('SELZERO.TXT',b'ZERO\r\n',0,0),('SELTWO.TXT',b'TWO\r\n',2,0),
              ('SELRO.TXT',b'RO\r\n',0,1),('SELSYS.TXT',b'SYS\r\n',0,2),
              ('SELARC.TXT',b'ARC\r\n',0,4),
              ('SIZMULT.DAT',b'M'*40000,0,0),('SIZEMPTY.DAT',b'',0,0),
              ('SIZMULT.DAT',b'T'*2048,2,0),
              ('SELMIX.COM',b'C'*2048,0,0),('SELMIX.ASM',b'A'*4000,0,0)]
    cases=[
        (':DIR A[0,2]:SEL*.TXT',['A0:','A2:','SELZERO','SELTWO',
                               '3 FILES, 6K TOTAL','1 FILE, 2K TOTAL'],['SELSYS']),
        ('.DIR A0:SEL*.TXT[$SYS]',['SELSYS','1 FILE, 2K TOTAL'],['SELZERO','SELRO','SELARC']),
        ('DIR A0:SEL*.TXT[$ARC+!$SYS]',['SELARC','1 FILE, 2K TOTAL'],['SELZERO','SELRO','SELSYS']),
        ('DIR [A0,A2]:SEL?*.TXT[$RO,$SYS]',['SELRO','SELSYS','2 FILES, 4K TOTAL'],['SELZERO','SELTWO','SELARC']),
        ('DIR A0:SEL*ZERO.TXT',['Invalid filespec.'],['SELZERO  TXT']),
        ('DIR A[32]:SEL*.TXT',['Invalid filespec.'],['SELZERO  TXT']),
        ('DIR A0:SIZ*.DAT',['SIZMULT  DAT  40K','SIZEMPTY DAT  0K',
                           '2 FILES, 40K TOTAL'],[]),
        ('DIR A[0,2]:SIZMULT.DAT',['A0:','A2:','SIZMULT  DAT  40K',
                                 'SIZMULT  DAT  2K','1 FILE, 40K TOTAL',
                                 '1 FILE, 2K TOTAL'],[]),
        ('DIR A0:SELMIX.*',['SELMIX   ASM  4K','SELMIX   COM  2K',
                            '2 FILES, 6K TOTAL'],[])]
    def check_order(output,index):
        expected={0:['SELARC','SELRO','SELZERO'],3:['SELRO','SELSYS'],
                  6:['SIZEMPTY','SIZMULT'],8:['SELMIX   ASM','SELMIX   COM']}.get(index,[])
        positions=[output.index(name) for name in expected]
        assert positions==sorted(positions),(index,expected,output)
    observations=[]
    if a.platform=='z80pack':
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',report/'disks')
        shutil.copy2(a.image_dir/'diskdefs',report/'diskdefs')
        disk=report/'disks/drivea.dsk'
        # This seed predates force-transient dispatch; WBOOT reads reserved CCP.
        from fdf_format import select_fdf
        fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',
                       'California Computer Systems (40T, DS, DD, 332K)')
        mapping=fmt.raw_record_map();raw=bytearray(disk.read_bytes())
        carrier=(ROOT/'build/ccp/ccp.rlm').read_bytes().ljust(13*512,b'\0')
        assert len(carrier)==13*512
        for i in range(len(carrier)//128):
            track,record=divmod(108+i,len(mapping))
            offset=(track*len(mapping)+mapping[record])*128
            raw[offset:offset+128]=carrier[i*128:(i+1)*128]
        disk.write_bytes(raw)
        def cpm(tool,*args):
            return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=report,check=True)
        cpm('cpmrm','0:*.COM')
        cpm('cpmcp',ROOT/'build/utilities/CPX.COM','0:CPX.COM')
        (report/'DIR.COM').write_bytes(binary);cpm('cpmcp',report/'DIR.COM','0:DIR.COM')
        for name,data,user,mask in fixtures:
            path=report/name;path.write_bytes(data);cpm('cpmcp',path,f'{user}:{name}')
            if mask:cpm('cpmchattr', {1:'r',2:'s',4:'a'}[mask],f'{user}:{name}')
        before={path.name:path.read_bytes() for path in (report/'disks').glob('*.dsk')}
        for i,(command,required,excluded) in enumerate(cases):
            text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',
                [(b'CPX UNLOAD RCP\r',b'A0>_ ',60),(command.encode()+b'\r',b'A0>_ ',60)],
                report/f'case-{i}.txt').decode(errors='replace')
            # Check only output after the completed command echo.
            output=text.rsplit(command+' ',1)[-1]
            for value in required:assert value in output,(command,value,output)
            for value in excluded:assert value not in output,(command,value,output)
            if i==6:assert output.count('SIZMULT  DAT')==1,(command,output)
            if i==7:assert output.count('SIZMULT  DAT')==2,(command,output)
            check_order(output,i)
            observations.append({'command':command,'result':'PASS'})
        assert all((report/'disks'/name).read_bytes()==data for name,data in before.items())
    else:
        def marker(i):return f'DIR CASE {i}'
        script=[];extras=[('DIR.COM',binary),('CPX.COM',(ROOT/'build/utilities/CPX.COM').read_bytes()),
            ('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),*fixtures]
        for i,(command,_,_) in enumerate(cases):
            script += [command,f'CHECK{i}']
            code=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00'
            extras.append((f'CHECK{i}.COM',code+('\r\n'+marker(i)+'\r\n$').encode()))
        extras.append(('CASE.SUB',('\r\n'.join(script)+'\r\n').replace('$','$$').encode()+b'\x1a'))
        disk=report/'a.dmk';before=medium(extras)
        if not a.verify_existing:disk.write_bytes(before)
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
        invocation+=keys('CPX UNLOAD RCP\r')+['-id','3000','-it']+keys('SUBMIT CASE\r')+['-itime','0']
        for i in range(len(cases)):invocation+=['-iw',marker(i),'-it']
        invocation+=['-id','3000','-it','-ix']
        if not a.verify_existing:
            (report/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
            run(invocation,cwd=report,timeout=900,check=True)
        for i,(command,required,excluded) in enumerate(cases):
            text=screen(report/f'trs80-text-{i+2}.bin')
            output=text.split('>'+command,1)[-1].split('A0>CHECK',1)[0]
            for value in required:assert value in output,(command,value,text)
            for value in excluded:assert value not in output,(command,value,text)
            if i==6:assert output.count('SIZMULT  DAT')==1,(command,output)
            if i==7:assert output.count('SIZMULT  DAT')==2,(command,output)
            check_order(output,i)
            assert marker(i) in text,(i,text)
            (report/f'case-{i}.txt').write_text(text)
            observations.append({'command':command,'result':'PASS'})
        # SUBMIT changes its command stream; fixture content/attributes stay intact.
        from test_model4_copy import files
        from add_cpm_file_to_dmk import extract_raw
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
        offset=FILESYSTEM_FIRST_SECTOR*512
        old,new=files(extract_raw(before)[offset:]),files(extract_raw(disk.read_bytes())[offset:])
        assert new[(0,b'DIR     COM')][0][:len(binary)]==binary,'saved DIR binary differs'
        for name,_,user,_ in fixtures:
            key=name.partition('.')[0].ljust(8).encode()+name.partition('.')[2].ljust(3).encode()
            assert old[(user,key)]==new[(user,key)],name
        assert screen(report/f'trs80-text-{len(cases)+2}.bin').rstrip().endswith('A0>')
    (report/'DIR.COM').write_bytes(binary)
    (report/'harness.py').write_bytes(Path(__file__).read_bytes())
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,
        'RCP_unloaded':True,'dir_sha256':hashlib.sha256(binary).hexdigest(),'cases':observations},indent=2)+'\n')
    print('Self-contained DIR selection, sizes, per-DU name sorting and totals: PASS')


if __name__=='__main__':main()
