#!/usr/bin/env python3
"""Record a shipped monitor bell and audit unchanged native release files."""
import argparse,json,shutil,subprocess,wave
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR,key_args
from build_ccp import assemble
from test_sysgen_install import screen
from trs80gp_launch import run

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--monitor',choices=('ADM3A','VT52','ANSI'),required=True)
 a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False);report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256'];raw=extract_raw(original.read_bytes())
 for i in range(DIRECTORY_ENTRIES):
  at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
  if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=229
 commands=[':VER /BANNER','RSX LOAD M4SCRN']
 commands+=['RSX LOAD '+a.monitor,'BELLTST','RSX UNLOAD '+a.monitor]
 commands+=['RSX UNLOAD M4SCRN','RSX LIST','BELLEND'];add_file(raw,'STARTUP.SUB',('\r\n'.join(commands)+'\r\n\x1a').encode())
 source=" ORG 100H\n LD DE,READY\n LD C,9\n CALL 5\n LD C,1\n CALL 5\n LD E,7\n LD C,6\n CALL 5\n LD DE,EMITTED\n LD C,9\n CALL 5\n LD C,0\n JP 5\nREADY: DB 'BELL READY',13,10,'$'\nEMITTED: DB 'BELL EMITTED',13,10,'$'\n END\n"
 (w/'bell.asm').write_text(source);code=assemble(Path.home()/'bin/z80asm',source,w/'BELLTST.COM',w/'bell.lst',0x100)
 add_file(raw,'BELLTST.COM',code);add_file(raw,'BELLEND.COM',bytes.fromhex('110b010e09cd0500c30000')+b'BELL CAMPAIGN COMPLETE\r\n$')
 image=w/'a.dmk';image.write_bytes(build(bytes(raw)));shutil.copy2(__file__,w/'executed-runner.py')
 cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000','-sfmute','-iw','BELL READY','-id','120','-it','-ir','audio']+key_args(' ',delay=60)+['-iw','BELL EMITTED','-id','120','-ir','audio','-it','-iw','BELL CAMPAIGN COMPLETE','-id','6000','-it','-ix'];(w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=1200)
 recordings=list(w.glob('*.wav'));assert len(recordings)==1
 with wave.open(str(recordings[0]),'rb') as f:width=f.getsampwidth();channels=f.getnchannels();rate=f.getframerate();samples=f.readframes(f.getnframes())
 center=128 if width==1 else 0;values=[int.from_bytes(samples[i:i+width],'little',signed=width!=1) for i in range(0,len(samples),width*channels)];crossings=sum((x>center)!=(y>center) for x,y in zip(values,values[1:]));assert crossings==512,crossings
 text=screen(sorted(w.glob('trs80-text*'))[-1]);(w/'screen.txt').write_text(text);assert 'No RSXs loaded' in text and 'TPA available: 53K' in text and 'BELL CAMPAIGN COMPLETE' in text
 audit=audit_files(original,image,dict(report,included=[f for f in report['included'] if f['name']!='STARTUP.SUB']),w);assert extract_raw(original.read_bytes())[:20480]==extract_raw(image.read_bytes())[:20480]
 fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'file-audit/after.raw')],cwd=w/'file-audit',capture_output=True,check=True);(w/'filesystem.txt').write_bytes(fs.stdout+fs.stderr);assert sha(original)==report['sha256']
 (w/'result.json').write_text(json.dumps({'status':'PASS','personalities':[a.monitor],'crossings':crossings,'sample_rate':rate,'audio_sha256':sha(recordings[0]),'baseline_sha256':report['sha256'],'runner_sha256':sha(w/'executed-runner.py'),'emulator_sha256':sha(DEFAULT_EMULATOR),'file_audit':audit,'scope':'Native emulator audio waveform with effects muted, one personality bell, switching and unload/53K; no human hearing or physical-speaker claim.'},indent=2)+'\n');print('PASS native personality bell recording',w)
if __name__=='__main__':main()
