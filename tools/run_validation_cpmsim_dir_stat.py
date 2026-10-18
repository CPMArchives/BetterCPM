#!/usr/bin/env python3
"""Validate shipped DIR WHEREIS and STAT on disposable cpmsim disks."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    report=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    disks={d:w/'disks'/('drive'+d+'.dsk') for d in 'abc'}
    for image in disks.values():shutil.copy2(base/report['image'],image)
    shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    def cpm(tool,d,*args):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[d]),*map(str,args)],cwd=w,check=True,capture_output=True)
    for d in 'bc':cpm('cpmrm',d,'0:*.*')
    def put(d,user,name,data,attrs=0):
        path=w/f'in-{d}-{user}-{name}';path.write_bytes(data);cpm('cpmcp',d,path,f'{user}:{name}')
        flags=''.join(ch for bit,ch in ((1,'r'),(2,'s'),(4,'a')) if attrs&bit)
        if flags:cpm('cpmchattr',d,flags,f'{user}:{name}')
    def rows(d,user,name):
        stem,ext=name.split('.');key=(stem.ljust(8)+ext.ljust(3)).encode();raw=directory(disks[d],w/'diskdefs')
        return [raw[i:i+32] for i in range(0,len(raw),32) if raw[i]==user and bytes(x&127 for x in raw[i+1:i+12])==key]
    def check(d,user,name,data,attrs=None):
        found=rows(d,user,name);assert found,(d,user,name)
        if attrs is not None:
            assert all(sum((r[9+i]>>7)<<i for i in range(3))==attrs for r in found),(name,attrs)
        out=w/f'out-{d}-{user}-{name}';cpm('cpmcp',d,f'{user}:{name}',out);assert out.read_bytes()==data,name
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';commands=[]
    def execute(command):
        text=session(sim,w/'disks',[(command.encode()+b'\r',b'A0>_ ',120)],w/f'case-{len(commands):02}.txt')
        commands.append(command);return text
    payload=bytes(range(256))*130
    for d,user,attrs in [('b',0,0),('b',3,2),('c',31,0)]:put(d,user,'W26.DAT',payload,attrs)
    put('b',5,'REPORT.DAT',payload)
    put('b',5,'EMPTY.DAT',b'')
    saved={d:disks[d].read_bytes() for d in 'bc'}
    text=execute('DIR /WHEREIS W26.DAT');assert b'DIR: Use :DIR.' in text
    text=execute(':DIR /WHEREIS W26.DAT')
    for label in (b'B0:W26.DAT',b'B3:W26.DAT',b'C31:W26.DAT'):assert text.count(label)==1,(label,text)
    assert b'3 MATCHES' in text
    text=execute(':DIR /WHEREIS B:W26.DAT');assert b'B0:W26.DAT' in text and b'B3:W26.DAT' not in text and b'1 MATCH' in text
    text=execute(':DIR /WHEREIS B[-]:W26.DAT');assert text.count(b'B0:W26.DAT')==1 and text.count(b'B3:W26.DAT')==1 and b'2 MATCHES' in text
    text=execute(':DIR /WHEREIS B[-]:W26.DAT[$SYS]');assert b'B3:W26.DAT' in text and b'B0:W26.DAT' not in text and b'1 MATCH' in text
    text=execute(':DIR /WHEREIS B0:MISSING.DAT');assert b'DIR: No matches found.' in text and b'Search incomplete.' not in text
    for command in (':DIR /WHEREIS W26.DAT /VER',':DIR /WHEREIS W26.DAT /A'):
        text=execute(command);assert b'Invalid' in text
    text=execute('DIR B5:*.DAT[$RW]');assert len(re.findall(rb'REPORT +DAT',text))==1 and len(re.findall(rb'EMPTY +DAT',text))==1
    text=execute(':DIR B5:*.DAT[$RW]');assert b'2 FILES' in text and len(re.findall(rb'REPORT +DAT',text))==1
    text=execute('STAT B5:REPORT.DAT');assert b'00260 Recs' in text and b'00034K Bytes' in text and b'00002 Ext' in text,text
    assert all(disks[d].read_bytes()==saved[d] for d in 'bc'),'read-only report changed media'
    from test_z80pack_stat_attributes import directory_offsets
    offsets=directory_offsets(w/'diskdefs')
    for option,column,on in [('$R/O',9,True),('$SYS',10,True),('$R/W',9,False),('$DIR',10,False)]:
        before=disks['b'].read_bytes();raw=directory(disks['b'],w/'diskdefs');expected=bytearray(before);count=0
        for at in range(0,len(raw),32):
            if raw[at]==5 and bytes(x&127 for x in raw[at+1:at+12])==b'REPORT  DAT':
                physical=offsets[at+column];expected[physical]=(expected[physical]|128) if on else (expected[physical]&127);count+=1
        assert count==2
        execute('STAT B5:REPORT.DAT '+option)
        assert disks['b'].read_bytes()==bytes(expected),(option,'unexpected disk mutation')
        check('b',5,'REPORT.DAT',payload)
    assert disks['c'].read_bytes()==saved['c']
    shipped=audit(base,report,w,disks['a'])
    for d in 'bc':
        image=disks[d]
        if d=='c':
            # Host fsck only accepts CP/M 2.2 users 0..15. Preserve original C
            # and validate allocation/connectivity on a user-number-only copy.
            raw=directory(image,w/'diskdefs');normalized=bytearray(image.read_bytes())
            assert not any(raw[at]==15 for at in range(0,len(raw),32))
            for at in range(0,len(raw),32):
                if raw[at]==31:normalized[offsets[at]]=15
            image=w/'user31-as-user15.dsk';image.write_bytes(normalized)
        r=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image)],cwd=w,capture_output=True,check=True)
        (w/f'filesystem-{d}.txt').write_bytes(r.stdout+r.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','filesystem_c_scope':'user-number-only normalized copy; original user31 media independently unchanged','commands':commands,'runner_sha256':sha(Path(__file__)),'baseline_sha256':report['sha256'],'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped},indent=2)+'\n')
    print('PASS shipped DIR/WHEREIS/STAT:',len(commands),'sessions',w)

if __name__=='__main__':main()
