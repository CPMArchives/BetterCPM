#!/usr/bin/env python3
"""Validate shipped resident/transient REN without replacing release files."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
from test_z80pack_attributes import directory
from run_validation_returning import sha
from utility_versions import banner

def audit(baseline,report,work,image):
    results=[]
    for item in report['included']:
        outputs=[]
        for label,disk in [('before',baseline/report['image']),('after',image)]:
            path=work/(label+'-'+item['name'])
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),f"{item.get('user',0)}:{item['name']}",str(path)],cwd=work,check=True,capture_output=True)
            outputs.append(path)
        assert sha(outputs[0])==item['sha256'] and outputs[0].read_bytes()==outputs[1].read_bytes(),item['name']
        results.append(item['name'])
    check=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image)],cwd=work,capture_output=True,text=True)
    (work/'filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
    assert sha(baseline/report['image'])==report['sha256']
    return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 work=args.report.resolve();work.mkdir(parents=True,exist_ok=False)
 baseline=args.image_dir.resolve();manifest=json.loads((baseline/'report.json').read_text())
 (work/'disks').mkdir()
 for letter in 'abc':shutil.copy2(baseline/manifest['image'],work/'disks'/('drive'+letter+'.dsk'))
 shutil.copy2(baseline/'diskdefs',work/'diskdefs');shutil.copy2(__file__,work/'executed-runner.py')
 disks={d:work/'disks'/f'drive{d}.dsk' for d in 'abc'}
 def cpm(tool,d,*values):
  subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[d]),*map(str,values)],cwd=work,check=True,stdout=subprocess.DEVNULL)
 for d in 'bc':cpm('cpmrm',d,'0:*.*')
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';cases=[]
 def execute(command,steps=()):
  transcript=session(sim,work/'disks',[(command.encode()+b'\r',b'A0>_ ',30)] if not steps else list(steps),work/f'case-{len(cases)}.txt')
  cases.append(command);return transcript
 def put(user,name,payload,attrs=0):
  f=work/f'in-{user}-{name}';f.write_bytes(payload);cpm('cpmcp','b',f,f'{user}:{name}')
  flags=''.join(ch for bit,ch in [(1,'r'),(2,'s'),(4,'a')] if attrs&bit)
  if flags:cpm('cpmchattr','b',flags,f'{user}:{name}')
 def entries(user,name):
  stem,ext=name.split('.');key=(stem.ljust(8)+ext.ljust(3)).encode();raw=directory(disks['b'],work/'diskdefs')
  return [raw[i:i+32] for i in range(0,len(raw),32) if raw[i]==user and bytes(v&127 for v in raw[i+1:i+12])==key]
 def check(user,name,payload,attrs):
  rows=entries(user,name);assert rows,(user,name)
  for row in rows:assert sum((row[9+i]>>7)<<i for i in range(3))==attrs,(user,name,row.hex())
  f=work/f'out-{user}-{name}';cpm('cpmcp','b',f'{user}:{name}',f);assert f.read_bytes()==payload,(user,name)
 payloads={}
 for a in range(8):
  payload=bytes([a+40])*(20096 if a==7 else 256);payloads[a]=payload;put(1,f'F{a}.DOC',payload,a)
 text=execute(':REN /P B1:*.DOC *.TXT');assert b'8 FILES RENAMED' in text,text
 for a,payload in payloads.items():assert not entries(1,f'F{a}.DOC');check(1,f'F{a}.TXT',payload,a)
 for a in range(8):put(2,f'F{a}.DOC',b'Q'*128,a)
 text=execute(':REN B2:*.DOC *.TXT');assert b'2 FILES RENAMED, 6 SKIPPED' in text,text
 for a in range(8):check(2,f'F{a}.DOC' if a&3 else f'F{a}.TXT',b'Q'*128,a)
 before=disks['b'].read_bytes();text=execute(':REN /P /DRY B2:*.DOC *.BAK');assert disks['b'].read_bytes()==before and b'Dry run only:' in text
 text=execute(':REN B2:*.DOC *.BAK /BAD');assert disks['b'].read_bytes()==before and b'Invalid filespec.' in text
 put(3,'ONE.DOC',b'A'*128,4);put(3,'ONE.TXT',b'B'*128)
 text=execute('interactive',[(b':REN /C B3:ONE.DOC ONE.TXT\r',b'N/S/A/? ',30),(b'?',b'N/S/A/? ',30),(b'N',b'New name? ',30),(b'BAD*.TXT\r',b'New name? ',30),(b'NEW.TXT\r',b'Rename? Y/N ',30),(b'Y',b'A0>_ ',30)])
 assert b'N New name, S Skip file, A Abort remainder.' in text and b'Invalid filename.' in text
 check(3,'NEW.TXT',b'A'*128,4);check(3,'ONE.TXT',b'B'*128,0);assert not entries(3,'ONE.DOC')
 put(4,'FOO.DOC',b'F'*128);put(4,'XOO.DOC',b'X'*128)
 execute('ledger',[(b':REN B4:*.DOC X*.DOC\r',b'N/S/A/? ',30),(b'N',b'New name? ',30),(b'ZOO.DOC\r',b'A0>_ ',30)])
 check(4,'ZOO.DOC',b'F'*128,0);check(4,'XOO.DOC',b'X'*128,0)
 put(5,'A.DOC',b'5'*128);put(7,'B.DOC',b'7'*128)
 text=execute(':REN *.TXT=B[5,7]:*.DOC');assert b'2 FILES RENAMED' in text
 check(5,'A.TXT',b'5'*128,0);check(7,'B.TXT',b'7'*128,0)
 for user in (8,9):
  put(user,'PLAIN.DOC',b'P'*33024);put(user,'READONLY.DOC',b'R'*128,1);put(user,'SYSTEM.DOC',b'S'*128,2)
 execute('REN B[8,9]:*.DOC *.TXT')
 for user in (8,9):
  check(user,'PLAIN.TXT',b'P'*33024,0);assert not entries(user,'PLAIN.DOC')
  check(user,'READONLY.DOC',b'R'*128,1);check(user,'SYSTEM.DOC',b'S'*128,2)
 before=disks['b'].read_bytes()
 text=execute('REN /P B8:*.DOC *.TXT');assert b'Use :REN' in text and disks['b'].read_bytes()==before
 execute('REN B8:*.DOC[$RO,$SYS] *.TXT');assert disks['b'].read_bytes()==before
 text=execute(':REN /Y B3:ONE.TXT NEW.TXT');assert b'EXISTS' in text.upper()
 check(3,'NEW.TXT',b'A'*128,4);check(3,'ONE.TXT',b'B'*128,0)
 text=execute(':REN /VER');assert banner('REN').encode() in text
 shipped=audit(baseline,manifest,work,disks['a'])
 for letter in 'bc':
  result=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks[letter])],cwd=work,capture_output=True,check=True)
  (work/('filesystem-'+letter+'.txt')).write_bytes(result.stdout+result.stderr)
 (work/'evidence.json').write_text(json.dumps({'result':'PASS','commands':cases,'runner_sha256':sha(Path(__file__)),'baseline_sha256':manifest['sha256'],'unchanged_shipped_files':shipped,'ren_sha256':sha(work/'after-REN.COM'),'simulator_sha256':hashlib.sha256(sim.read_bytes()).hexdigest()},indent=2)+'\n')
 print('PASS: native BDOS REN all attributes, multi-extents, safe default, dry run, invalid syntax, interactive collision/help/confirmation, ledger and multi-DU')
if __name__=='__main__':main()
