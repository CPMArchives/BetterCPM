#!/usr/bin/env python3
"""Qualify safe resident ERA on disposable media without ERA.COM."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from test_disk_utilities import ROOT, medium, keys
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--platform',choices=('z80pack','model4'),required=True)
    p.add_argument('--image-dir',type=Path)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--verify-existing',action='store_true',help='recheck completed Model 4 captures and disk without rerunning')
    a=p.parse_args();w=a.report.resolve()
    if a.verify_existing:
        assert a.platform=='model4' and w.is_dir()
    else:w.mkdir(parents=True,exist_ok=False)
    names=('ERANORM.TXT','ERARO.TXT','ERASYS.TXT','ERABOTH.TXT','ERAARC.TXT','ERASAFE.TXT')
    fixtures=[(n,b'X'*(33024 if n=='ERANORM.TXT' else 128)) for n in names]
    commands=['CPX UNLOAD RCP','CPX LOAD RCP',
              'ERA [A0,E0]:ERASAFE.TXT','ERA A0:ERA*BAD.TXT',
              'ERA A0:ERASAFE.TXT /Y','ERA',
              'ERA /VER','ERA A0:ERARO.TXT','ERA A0:ERASYS.TXT','ERA A0:ERABOTH.TXT',
              'ERA A0:ERA*.TXT[$RO,$SYS]', 'DIR A0:ERA*.TXT[$RO,$SYS]',
              'CHECK','ERA A[0,2]:ERAN*.TXT','DIR A[0,2]:ERAN*.TXT',
              'ERA A0:ERAARC.TXT[$ARC]','DIR A0:ERAARC.TXT',
              'ERA A0:ERAARC.TXT[$RW]','DIR A0:ERAARC.TXT',
              'DIR A0:ERASAFE.TXT','DIR A0:ERA*.TXT[$RO,$SYS]','FINISH']
    finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00\r\nERA FINISH\r\n$'
    extras=fixtures+[(n,(ROOT/'build/utilities'/n).read_bytes()) for n in ('CPX.COM','SUBMIT.COM')]
    extras += [('CHECK.COM',finish.replace(b'ERA FINISH',b'ERA CHECK!')),('FINISH.COM',finish)]
    module=(ROOT/'build/cpx/RCP.CPX').read_bytes()
    if a.platform=='z80pack':
        assert a.image_dir
        shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
        disk=w/'disks/drivea.dsk'
        # Remove transient counterparts so accidental fallback cannot pass.
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disk),'0:*.*'],cwd=w,check=True)
        extras += [('RCP.CPX',module)]
        for name,data in extras:
            path=w/name;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=w,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(w/'ERANORM.TXT'),'2:ERANORM.TXT'],cwd=w,check=True)
        for flags,name in (('r','ERARO.TXT'),('s','ERASYS.TXT'),('rs','ERABOTH.TXT')):
            subprocess.run(['cpmchattr','-T','raw','-f','bettercpm-default',str(disk),flags,'0:'+name],cwd=w,check=True)
        steps=[(c.encode()+b'\r',b'A0>_ ',60) for c in commands]
        steps += [(b'ERA A0:*.*\r',b'ALL (Y/N)? ',60),(b'N\r',b'A0>_ ',60),
                  (b'DIR ERASAFE.TXT\r',b'A0>_ ',60),
                  (b'ERA A0:*.*[$RO,$SYS]\r',b'ALL (Y/N)? ',60),
                  (b'Y\r',b'A0>_ ',60),(b'DIR A0:ERA*.TXT[$RO,$SYS]\r',b'A0>_ ',60)]
        text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',steps,w/'transcript.txt').decode(errors='replace')
        early=text.split('ERA CHECK!',1)[0]
    else:
        from add_cpm_file_to_dmk import extract_raw
        from build_montezuma_extended_790k import build, SECTOR_SIZE
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES
        directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
        disk=w/'a.dmk'
        if not a.verify_existing:
            extras += [('CASE.SUB',('\r\n'.join(c.replace('$','$$') for c in commands)+'\r\n').encode()+b'\x1a')]
            extras += [('USER2.TXT',fixtures[0][1])]
            raw=extract_raw(medium(extras));directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
            for offset in range(directory,directory+DIRECTORY_ENTRIES*32,32):
                name=bytes(v&127 for v in raw[offset+1:offset+12])
                if name==b'USER2   TXT':
                    raw[offset]=2;raw[offset+1:offset+12]=b'ERANORM TXT'
                if name in (b'ERARO   TXT',b'ERABOTH TXT'):raw[offset+9]|=128
                if name in (b'ERASYS  TXT',b'ERABOTH TXT'):raw[offset+10]|=128
            disk=w/'a.dmk';disk.write_bytes(build(raw))
            invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000']
            invocation+=keys('SUBMIT CASE\r')+['-itime','0','-iw','ERA CHECK!','-it','-iw','ERA FINISH','-id','3000','-it','-ix']
            (w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
            run(invocation,cwd=w,timeout=900,check=True)
        captures=[screen(path) for path in sorted(w.glob('trs80-text-*.bin'))]
        early=captures[0];text='\n'.join(captures);(w/'transcript.txt').write_text(text)
        raw=extract_raw(disk.read_bytes())
        entries=[raw[o:o+32] for o in range(directory,directory+DIRECTORY_ENTRIES*32,32) if raw[o]<32]
        found={(e[0],bytes(v&127 for v in e[1:12])):e for e in entries}
        assert (0,b'ERANORM TXT') not in found and (2,b'ERANORM TXT') not in found
        assert (0,b'ERAARC  TXT') not in found
        assert (0,b'ERASAFE TXT') in found
        # Confirm the executed carrier and protected contents from the final
        # physical disk, rather than relying only on filenames on screen.
        def contents(entry):
            blocks=[int.from_bytes(entry[i:i+2],'little') for i in range(16,32,2)]
            return b''.join(raw[directory+b*2048:directory+(b+1)*2048] for b in blocks if b)
        assert contents(found[0,b'RCP     CPX'])[:len(module)]==module
        for name in (b'ERARO   TXT',b'ERASYS  TXT',b'ERABOTH TXT',b'ERASAFE TXT'):
            assert contents(found[0,name])[:128]==b'X'*128,name
        for name,bit in ((b'ERARO   TXT',9),(b'ERASYS  TXT',10),(b'ERABOTH TXT',9),(b'ERABOTH TXT',10)):
            assert found[0,name][bit]&128,(name,bit)

    if a.platform=='z80pack':
        assert 'Invalid filespec.' in early and 'INVALID DRIVE' in early,early
    else:
        assert 'RCP Build 005' in early,early
    assert all(n.split('.')[0] in early for n in ('ERARO.TXT','ERASYS.TXT','ERABOTH.TXT')),early
    assert 'ERA FINISH' in text,text
    assert 'ERASAFE  TXT' in text,text
    assert all(n in text for n in ('ERARO','ERASYS','ERABOTH')),text
    if a.platform=='z80pack':
        deleted=text.split('DIR A[0,2]:ERAN*.TXT',1)[1].split('ERA A0:ERAARC',1)[0]
        assert deleted.count('NO FILE')==2,deleted
        retained=text.split('DIR A0:ERAARC.TXT',1)[1].split('ERA A0:ERAARC.TXT[$RW]',1)[0]
        assert 'ERAARC   TXT' in retained,retained
        gone=text.split('ERA A0:ERAARC.TXT[$RW]',1)[1].split('DIR A0:ERASAFE',1)[0]
        assert 'NO FILE' in gone,gone
        assert 'ERASAFE  TXT' in text.split('ALL (Y/N)?',1)[1]
        assert all(n in text.rsplit('ALL (Y/N)?',1)[1] for n in ('ERARO','ERASYS','ERABOTH'))
    (w/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,
        'rcp_sha256':hashlib.sha256(module).hexdigest(),'no_ERA_transient':True,
        'coverage':['multi-DU multi-extent deletion','RO/SYS unconditional protection',
                    'attribute selection','complete validation before mutation','bare ERA safety',
                    'caller DU restoration','all-files cancellation' if a.platform=='z80pack' else 'SUBMIT execution']},indent=2)+'\n')
    print('Resident ERA safe shared selection: PASS')

if __name__=='__main__':main()
