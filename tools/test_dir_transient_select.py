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
    p.add_argument('--extents-only',action='store_true',help='Qualify physical directory-entry display units')
    p.add_argument('--edges-only',action='store_true',help='Run combined selector/report edge cases')
    p.add_argument('--free-only',action='store_true',help='Run drive-level free-space qualification')
    p.add_argument('--columns-only',action='store_true',help='Run only the column-layout increment')
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
    fixtures += [(f'ATR{mask}.TXT',b'ATTR\r\n',0,mask) for mask in range(8)]
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
                            '2 FILES, 6K TOTAL'],[]),
        ('DIR /S=N- A0:SEL*.TXT',['3 FILES, 6K TOTAL'],['SELSYS']),
        ('DIR /S=T- A0:SELMIX.*',['SELMIX   COM  2K','SELMIX   ASM  4K'],[]),
        ('DIR A0:SIZ*.DAT /S=Z-',['SIZMULT  DAT  40K','SIZEMPTY DAT  0K','2 FILES, 40K TOTAL'],[]),
        ('DIR /S=N- A0:SELMIX.* /S=U',['2 FILES, 6K TOTAL'],[]),
        ('DIR /S=U A0:SELMIX.* /S=N+',['2 FILES, 6K TOTAL'],[]),
        ('DIR A0:SELMIX.* /S=U-',['Invalid option.'],['A0:','2 FILES','SELMIX   ASM']),
        ('DIR /S=N A0:SELMIX.* /S=BAD',['Invalid option.'],['A0:','2 FILES','SELMIX   ASM']),
        ('DIR /S=X /S=N A0:SELMIX.*',['Invalid option.'],['A0:','2 FILES','SELMIX   ASM']),
        ('DIR /S=Z A0:SELMIX.*',['SELMIX   COM  2K','SELMIX   ASM  4K','2 FILES, 6K TOTAL'],[])]
    cases += [
        ('DIR /A A[0,2]:SEL*.TXT',
         ['SELARC   TXT  2K  --A','SELRO    TXT  2K  -R-',
          'SELZERO  TXT  2K  ---','SELTWO   TXT  2K  ---'],['SELSYS']),
        ('DIR A0:SEL*.TXT[$SYS] /A', ['SELSYS   TXT  2K  S--'],['SELZERO']),
        ('DIR /A /S=N- A0:ATR*.TXT[$RO,$RW]',
         [f'ATR{mask}     TXT  2K  '+''.join(letter if mask&bit else '-'
            for bit,letter in [(2,'S'),(1,'R'),(4,'A')]) for mask in range(8)],[]),
        ('DIR /A /A A0:SEL*.TXT',['SELRO    TXT  2K  -R-'],['SELSYS']),
        ('DIR A0:SEL*.TXT',['SELRO    TXT  2K'],['  -R-','  --A','  ---']),
        ('DIR /A=RO A0:SEL*.TXT',['Invalid option.'],['SELRO    TXT']),
        ('DIR /AA A0:SEL*.TXT',['Invalid option.'],['SELRO    TXT'])]
    cases += [
        ('DIR /Z A0:SIZ*.DAT',['SIZMULT  DAT  40K','SIZEMPTY DAT  0K','2 FILES, 40K TOTAL'],[]),
        ('DIR /Z=K A0:SIZ*.DAT',['SIZMULT  DAT  40K','SIZEMPTY DAT  0K','2 FILES, 40K TOTAL'],[]),
        ('DIR /Z=S /S=Z- A0:SIZ*.DAT',['SIZMULT  DAT  320S','SIZEMPTY DAT  0S','2 FILES, 320S TOTAL'],[]),
        ('DIR /Z=S /A A[0,2]:SEL*.TXT',['SELARC   TXT  16S  --A','SELRO    TXT  16S  -R-',
          'SELZERO  TXT  16S  ---','SELTWO   TXT  16S  ---','3 FILES, 48S TOTAL','1 FILE, 16S TOTAL'],['SELSYS']),
        ('DIR /Z=S /Z=K A0:SIZ*.DAT',['SIZMULT  DAT  40K','2 FILES, 40K TOTAL'],['320S']),
        ('DIR /Z=K /Z=S A0:SIZ*.DAT',['SIZMULT  DAT  320S','2 FILES, 320S TOTAL'],['40K']),
        ('DIR A0:SIZ*.DAT',['SIZMULT  DAT  40K','2 FILES, 40K TOTAL'],['320S']),
        ('DIR /Z=X A0:SIZ*.DAT',['Invalid option.'],['SIZMULT  DAT']),
        ('DIR /Z=S+ A0:SIZ*.DAT',['Invalid option.'],['SIZMULT  DAT'])]
    column_cases=[
        ('DIR /C=1 A0:SEL*.TXT',['SELARC   TXT  2K','SELRO    TXT  2K','3 FILES, 6K TOTAL'],[' : ']),
        ('DIR /C=2 A0:SEL*.TXT',['SELARC   TXT  2K : SELRO    TXT  2K','3 FILES, 6K TOTAL'],[]),
        ('DIR /C=4 A0:SIZ*.DAT',['SIZEMPTY DAT  0K  : SIZMULT  DAT  40K','2 FILES, 40K TOTAL'],[]),
        ('DIR /Z=S /C=4 A0:SIZ*.DAT',['Requested columns do not fit.'],['A0:', 'SIZMULT  DAT','2 FILES']),
        ('DIR /A /C=4 A0:SEL*.TXT',['Requested columns do not fit.'],['SELARC   TXT','3 FILES']),
        ('DIR /A /C=2 A0:SEL*.TXT',['SELARC   TXT  2K  --A : SELRO    TXT  2K  -R-','3 FILES, 6K TOTAL'],[]),
        ('DIR /C=4 /A /C=1 A0:SEL*.TXT',['SELARC   TXT  2K  --A','3 FILES, 6K TOTAL'],[' : ']),
        ('DIR /Z=S A0:SIZ*.DAT',['SIZEMPTY DAT  0S   : SIZMULT  DAT  320S','2 FILES, 320S TOTAL'],[]),
        ('DIR /A A0:SEL*.TXT',['SELARC   TXT  2K  --A : SELRO    TXT  2K  -R-','3 FILES, 6K TOTAL'],[])]
    free_cases=[
        ('DIR A0:SEL*.TXT',['3 FILES, 6K TOTAL'],[]),
        ('DIR A[0,2]:SIZ*.DAT',['A0:','A2:','2 FILES, 40K TOTAL','1 FILE, 2K TOTAL'],[]),
        ('DIR [A0,A2,B0,B2]:SIZ*.DAT',['A0:','A2:','B0:','B2:'],[]),
        ('DIR /Z=S A[0,2]:NONE.*',['NO FILE'],[' FILES,'])]
    edge_cases=[
        ('DIR /P /A /Z=S /C=2 /S=N- A[00,0,02]:SEL***.TXT[$RO,$RW]',
         ['SELZERO  TXT  16S  --- : SELSYS   TXT  16S  S--','4 FILES, 64S TOTAL','1 FILE, 16S TOTAL','K FREE'],['MORE --']),
        ('DIR /A /Z=S /C=2 /S=T- A0:SELMIX.?**',
         ['SELMIX   COM  16S  --- : SELMIX   ASM  32S  ---','2 FILES, 48S TOTAL'],[]),
        ('DIR /C=4 /C=1 /Z=S /Z /S=Z- A0:SIZ*.DAT',
         ['SIZMULT  DAT  40K','SIZEMPTY DAT  0K','2 FILES, 40K TOTAL'],[' : ','320S']),
        ('DIR /A /Z=S /C=2 A0:NONE.*', ['NO FILE','K FREE'],[' FILES,','MORE --']),
        ('DIR /P /A /C=2 A0:F*?.TXT',['Invalid filespec.'],['K FREE',' FILES,']),
        ('DIR /A /Z=S /C=2 A0:SEL*.TXT /Z=X',['Invalid option.'],['K FREE','SELARC   TXT']),
        ('DIR /C=1 A0:SEL*.TXT /C=3 /C=2',['Invalid option.'],['K FREE','SELARC   TXT']),
        ('DIR /P /A /Z=S /C=2 A[0,2]:SEL*.TXT[$ARC+!$SYS]',
         ['SELARC   TXT  16S  --A','1 FILE, 16S TOTAL','NO FILE','K FREE'],['SELRO    TXT','MORE --']),
        ('DIR /C=1 A0:SEL*.TXT[$RO+!$RO]', ['NO FILE','K FREE'],[' FILES,']),
        ('DIR A0:SIZ*.DAT', ['SIZEMPTY DAT  0K  : SIZMULT  DAT  40K','2 FILES, 40K TOTAL'],['  ---','320S','MORE --'])]
    extent_cases=[
        ('DIR /Z=E /C=1 A0:SIZ*.DAT', ['SIZEMPTY DAT  1E','SIZMULT  DAT  {MULT}E','2 FILES, {SUM}E TOTAL','K FREE'],['40K','320S']),
        ('DIR /Z=E /S=Z- /C=2 /A /P A[0,2]:SIZMULT.DAT', ['A0:','A2:','SIZMULT  DAT  {MULT}E  ---','SIZMULT  DAT  1E  ---','1 FILE, {MULT}E TOTAL','1 FILE, 1E TOTAL'],['40K','320S']),
        ('DIR /Z=S /Z=E /C=4 A0:SEL*.TXT', ['3 FILES, 3E TOTAL','1E'],['SELSYS','16S']),
        ('DIR /Z=E A0:SEL*.TXT[$SYS]', ['SELSYS   TXT  1E','1 FILE, 1E TOTAL'],['SELRO']),
        ('DIR /Z=E /S=N- /C=2 A0:SELMIX.*', ['SELMIX   COM  1E','SELMIX   ASM  1E','2 FILES, 2E TOTAL'],[]),
        ('DIR /Z=E /Z A0:SIZ*.DAT', ['2 FILES, 40K TOTAL'],['E TOTAL']),
        ('DIR /Z=E+ /Z=E A0:SIZ*.DAT', ['Invalid option.'],['SIZMULT',' FILES,']),
        ('DIR /Z=EE A0:SIZ*.DAT', ['Invalid option.'],['SIZMULT']),
        ('DIR /Z=E A0:NONE.*', ['NO FILE','K FREE'],['E TOTAL']),
        ('DIR A0:SIZ*.DAT', ['2 FILES, 40K TOTAL'],['E TOTAL'])]
    cases = extent_cases if a.extents_only else edge_cases if a.edges_only else free_cases if a.free_only else column_cases if a.columns_only else cases + column_cases + edge_cases + extent_cases

    def check_free(output,index,expected):
        import re
        values=re.findall(r'^([A-P]): (\d+)K FREE\r?$',output,re.M)
        drives=['A','B'] if index==2 else ['A']
        assert values==[(drive,str(expected[drive])) for drive in drives],(index,values,expected,output)

    def check_order(output,index):
        if a.columns_only or a.free_only or a.edges_only or a.extents_only:return
        expected={0:['SELARC','SELRO','SELZERO'],3:['SELRO','SELSYS'],
                  6:['SIZEMPTY','SIZMULT'],8:['SELMIX   ASM','SELMIX   COM'],
                  9:['SELZERO','SELRO','SELARC'],10:['SELMIX   COM','SELMIX   ASM'],
                  11:['SIZMULT','SIZEMPTY'],12:['SELMIX   COM','SELMIX   ASM'],
                  13:['SELMIX   ASM','SELMIX   COM'],17:['SELMIX   COM','SELMIX   ASM']}.get(index,[])
        if index==20:expected=[f'ATR{mask}     TXT' for mask in range(7,-1,-1)]
        positions=[output.index(name) for name in expected]
        assert positions==sorted(positions),(index,expected,output)
    def extent_expectations(raw):
        entries=[raw[i:i+32] for i in range(0,len(raw),32)]
        count=sum(e[0]==0 and bytes(v&127 for v in e[1:12])==b'SIZMULT DAT' for e in entries)
        assert count>1,count
        return [(cmd,[x.format(MULT=count,SUM=count+1) for x in required],excluded) for cmd,required,excluded in cases]
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
            if mask:cpm('cpmchattr', ''.join(flag for bit,flag in
                        [(1,'r'),(2,'s'),(4,'a')] if mask&bit),f'{user}:{name}')
        if a.free_only:shutil.copy2(disk,report/'disks/driveb.dsk')
        if a.free_only:
            import re
            listing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default','-D',str(disk)],cwd=report).decode()
            free=int(re.search(r'(\d+)K Free',listing)[1]);expected_free={'A':free,'B':free}
        from test_z80pack_attributes import directory
        cases=extent_expectations(directory(disk,report/'diskdefs'))
        before={path.name:path.read_bytes() for path in (report/'disks').glob('*.dsk')}
        for i,(command,required,excluded) in enumerate(cases):
            text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',
                [(b'CPX UNLOAD RCP\r',b'A0>_ ',60),(command.encode()+b'\r',b'A0>_ ',60)],
                report/f'case-{i}.txt').decode(errors='replace')
            # Check only output after the completed command echo.
            output=text.rsplit(command+' ',1)[-1]
            for value in required:assert value in output,(command,value,output)
            for value in excluded:assert value not in output,(command,value,output)
            if i==6 and not a.columns_only and not a.free_only and not a.edges_only and not a.extents_only:assert output.count('SIZMULT  DAT')==1,(command,output)
            if i==7 and not a.columns_only and not a.free_only and not a.edges_only and not a.extents_only:assert output.count('SIZMULT  DAT')==2,(command,output)
            check_order(output,i)
            if a.free_only:check_free(output,i,expected_free)
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
        from add_cpm_file_to_dmk import extract_raw
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
        cases=extent_expectations(extract_raw(before)[FILESYSTEM_FIRST_SECTOR*512:][:4096])
        if a.free_only:
            from add_cpm_file_to_dmk import extract_raw
            from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
            filesystem=extract_raw(before)[FILESYSTEM_FIRST_SECTOR*512:]
            used={0,1}
            for position in range(0,4096,32):
                entry=filesystem[position:position+32]
                if entry[0]>31:continue
                used.update(block for at in range(16,32,2) if (block:=int.from_bytes(entry[at:at+2],'little')))
            free=(len(filesystem)//2048-len(used))*2
            from build_source_disk import install_files
            from build_montezuma_extended_790k import build
            braw=install_files([(user,name,data) for name,data,user,_ in fixtures])
            bused={0,1}
            for position in range(0,4096,32):
                entry=braw[position:position+32]
                if entry[0]>31:continue
                bused.update(block for at in range(16,32,2) if (block:=int.from_bytes(entry[at:at+2],'little')))
            expected_free={'A':free-2,'B':(len(braw)//2048-len(bused))*2}
            # A is SYSTEM media; B's default binding is DATA media.
            bimage=build(braw)
            (report/'b.dmk').write_bytes(bimage)
        invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']
        if a.free_only:invocation+=['-d1',str(report/'b.dmk')]
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
            if i==6 and not a.columns_only and not a.free_only and not a.edges_only and not a.extents_only:assert output.count('SIZMULT  DAT')==1,(command,output)
            if i==7 and not a.columns_only and not a.free_only and not a.edges_only and not a.extents_only:assert output.count('SIZMULT  DAT')==2,(command,output)
            check_order(output,i)
            if a.free_only:check_free(output,i,expected_free)
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
        if a.free_only:assert (report/'b.dmk').read_bytes()==bimage
        assert screen(report/f'trs80-text-{len(cases)+2}.bin').rstrip().endswith('A0>')
    (report/'DIR.COM').write_bytes(binary)
    (report/'harness.py').write_bytes(Path(__file__).read_bytes())
    (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,
        'RCP_unloaded':True,'dir_sha256':hashlib.sha256(binary).hexdigest(),'cases':observations},indent=2)+'\n')
    print(f'Self-contained DIR selection, sizes, sorting, attributes and totals: {len(cases)} cases PASS')


if __name__=='__main__':main()
