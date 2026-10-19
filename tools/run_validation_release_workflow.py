#!/usr/bin/env python3
"""Continuous shipped cpmsim release workflow, followed by a second cold boot."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session as raw_session
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
ROOT=Path(__file__).resolve().parents[1]

def session(simulator,disks,steps,transcript):
 # A prompt prefix can precede editor readiness. Do not send a whole new
 # command at that partial boundary; final media and command outcomes remain
 # mandatory oracles, rather than accepting input echo as execution.
 def settled():
  for step in steps:
   time.sleep(0.05)
   yield step
 return raw_session(simulator,disks,settled(),transcript)


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False)
 report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert report['target']=='z80pack' and sha(original)==report['sha256'];disks=w/'disks';disks.mkdir();shutil.copy2(a.baseline/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
 for letter in 'ab':shutil.copy2(original,disks/f'drive{letter}.dsk')
 b=disks/'driveb.dsk';subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(b),'0:*.*'],cwd=w,check=True,capture_output=True)
 def put(letter,user,name,data):
  source=w/name;source.write_bytes(data);subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{letter}.dsk'),str(source),f'{user}:{name}'],cwd=w,check=True,capture_output=True)
 old=b'ORIGINAL NOTES\r\n\x1a';sentinel=b'WORKFLOW SENTINEL\r\n\x1a'
 put('b',7,'NOTES.TXT',old);put('b',0,'KEEP.TXT',sentinel)
 batch=b':TYPE B9:BACKUP.TXT\r\n:DIR /WHEREIS B[-]:BACKUP.TXT\r\nVER /VER\r\nWFEND\r\n\x1a';put('a',0,'WFLOW.SUB',batch)
 put('a',0,'WFEND.COM',bytes.fromhex('110b010e09cd0500c30000')+b'BATCH WORKFLOW COMPLETE\r\n$')
 (w/'a-before.dsk').write_bytes((disks/'drivea.dsk').read_bytes());(w/'b-before.dsk').write_bytes(b.read_bytes())
 steps=[];prompt=b'A0>_ '
 def command(text,reply=None):
  nonlocal prompt
  if text in ('RSX LOAD ADM3A','RSX LOAD VT52'):prompt=b'A0>\x1b[7m '
  elif text=='RSX LOAD ANSI' or text in ('RSX UNLOAD ADM3A','RSX UNLOAD VT52','RSX UNLOAD ANSI'):prompt=b'A0>_ '
  steps.append((text.encode()+b'\r',prompt if reply is None else reply,60))
 command('TYPE README.TXT',b'Disk; it is not part of this System Disk.');steps.append((b'',prompt,30));command('DIR B:');command(':DIR /WHEREIS B[-]:NOTES.TXT')
 command(':ED B7:NOTES.TXT',b'*');steps += [(b'IEDITED \x1a\r',b'*',30),(b'E\r',b'B7>_ ',30)];command('A0:')
 command(':PIP B3:COPY.TXT=B7:NOTES.TXT[V]');command(':REN B3:COPY.TXT FINAL.TXT /Y');command('STAT B3:FINAL.TXT $R/O');command('STAT B3:FINAL.TXT');command('STAT B3:FINAL.TXT $R/W')
 command(':COPY /V /B B3:FINAL.TXT B9:BACKUP.TXT');command(':ERA B3:FINAL.TXT /Y');command('SUBMIT WFLOW',b'BATCH WORKFLOW COMPLETE');steps.append((b'',prompt,30))
 for _ in range(2):command(':PIP B3:AGAIN.TXT=B9:BACKUP.TXT[V]');command(':ERA B3:AGAIN.TXT /Y')
 command('RSX LOAD ANSISCRN')
 for name in ('ADM3A','VT52','ANSI'):
  command('RSX LOAD '+name);command('RSX LIST');command('TYPE B9:BACKUP.TXT');command('RSX UNLOAD '+name)
 command('RSX UNLOAD ANSISCRN');command('RSX LIST',b'TPA available: 53K');steps.append((b'',prompt,30));command('BYE',b'System halted')
 trace=session(a.simulator,disks,steps,w/'session-1.bin')
 assert b'B7:NOTES.TXT' in trace and b'B9:BACKUP.TXT' in trace and b'R/O' in trace
 assert trace.count(b'EDITED ORIGINAL NOTES')>=4
 for name in ('ADM3A','VT52','ANSI'):assert name.encode()+b' : BDOS 255' in trace
 assert b'BATCH WORKFLOW COMPLETE' in trace and b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
 boot=session(a.simulator,disks,[(b'RSX LIST\r',b'TPA available: 53K',30),(b'',prompt,30),(b':TYPE B9:BACKUP.TXT\r',b'EDITED ORIGINAL NOTES',30),(b'',prompt,30),(b'BYE\r',b'System halted',30)],w/'session-2-cold.bin');assert b'No RSXs loaded' in boot
 listing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(b)],cwd=w,text=True);(w/'b-directory.txt').write_text(listing)
 for user,name,expected in [(0,'KEEP.TXT',sentinel),(7,'NOTES.TXT',b'EDITED '+old),(7,'NOTES.BAK',old),(9,'BACKUP.TXT',b'EDITED '+old)]:
  exported=w/f'after-{user}-{name}';subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(b),f'{user}:{name}',str(exported)],cwd=w,check=True,capture_output=True);assert exported.read_bytes().split(b'\x1a')[0]==expected.split(b'\x1a')[0]
 assert all(name not in listing.lower() for name in ('copy.txt','final.txt','again.txt','notes.$$$'))
 shipped=audit(a.baseline,report,w,disks/'drivea.dsk')
 fs=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(b)],cwd=w,capture_output=True,check=True);(w/'b-filesystem.txt').write_bytes(fs.stdout+fs.stderr)
 fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT);before=(w/'a-before.dsk').read_bytes();after=(disks/'drivea.dsk').read_bytes()
 for i in range(160):
  track,within=divmod(i,fmt.spt);at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128;assert before[at:at+128]==after[at:at+128]
 (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':report['sha256'],'simulator_sha256':sha(a.simulator),'runner_sha256':sha(w/'executed-runner.py'),'sessions':2,'unchanged_shipped_files':shipped,'scope':'Continuous shipped README/DIR/WHEREIS/ED/PIP/REN/STAT/COPY/ERA/SUBMIT and three-personality TYPE sessions, repeated command returns and cold boot persistence, data/file/filesystem/system-track audits. No configuration installation workflow claim.'},indent=2)+'\n');print('PASS complete two-session cpmsim release workflow',w)
if __name__=='__main__':main()
