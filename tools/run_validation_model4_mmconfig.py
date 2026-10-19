#!/usr/bin/env python3
"""Capture the unmodified MM CONFIG opening screen through shipped ADM3A/M4SCRN."""
import argparse,json,shutil,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False)
 report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256']
 raw=extract_raw(original.read_bytes());refs={'MMCONF.COM':ROOT/'third_party/montezuma/CONFIG-3.10.COM','DISK.FDF':ROOT/'third_party/montezuma/DISK.FDF'}
 for name,path in refs.items():add_file(raw,name,path.read_bytes())
 image=w/'a.dmk';image.write_bytes(build(bytes(raw)));shutil.copy2(__file__,w/'executed-runner.py')
 cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']+key_args('MMCONF\r',delay=25)+['-iw','Your choice:','-id','120','-it','-ics','-ix']
 (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=900)
 pages=list(w.glob('trs80-text-*.bin'));assert len(pages)==1;page=bytes(c&127 for c in pages[0].read_bytes()[:1920]);assert b'Configuration options:' in page and b'Your choice:' in page
 (w/'screen.txt').write_text('\n'.join(page[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
 audit=audit_files(original,image,report,w)
 fsck=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'file-audit/after.raw')],cwd=w/'file-audit',capture_output=True,check=True);(w/'filesystem.txt').write_bytes(fsck.stdout+fsck.stderr)
 assert sha(original)==report['sha256']
 (w/'result.json').write_text(json.dumps({'status':'PASS','application':'unchanged Montezuma Micro CONFIG 3.10','reference_sha256':{k:sha(v) for k,v in refs.items()},'baseline_sha256':report['sha256'],'runner_sha256':sha(w/'executed-runner.py'),'emulator_sha256':sha(DEFAULT_EMULATOR),'file_audit':audit,'scope':'Opening menu through default shipped ADM3A/M4SCRN, native screen bytes and screenshot; emulator intentionally exits at menu. No MM CONFIG changes, persistence or application-exit compatibility claimed.'},indent=2)+'\n');print('PASS native MM CONFIG opening screen',w)
if __name__=='__main__':main()
