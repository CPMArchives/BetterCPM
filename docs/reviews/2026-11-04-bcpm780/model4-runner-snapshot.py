from pathlib import Path
import sys,json,shutil,hashlib
r=Path(__file__).resolve().parent/(sys.argv[2] if len(sys.argv)>2 else 'model4');r.mkdir();p=r.parent.parent
sys.path.insert(0,str(p/'licensing-review-20261103/review/tools'))
from add_cpm_file_to_dmk import add_file,extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_sysgen_install import screen
from run_validation_model4 import audit_files,sha
base=p/'combined-media-qualification-20261103/systems/trs80gp';report=json.loads((base/'report.json').read_text());master=base/report['image'];assert sha(master)==report['sha256']
raw=extract_raw(master.read_bytes());target_raw=bytearray(raw);sentinel=b'SHIPPED TOOLS INSTALL PRESERVES THIS FILE\r\n\x1a';add_file(target_raw,'KEEP.TXT',sentinel)
patched=Path(sys.argv[1]).resolve();code=patched.read_bytes()
from add_cpm_file_to_dmk import FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
for disk in (raw,target_raw):
 for i in range(DIRECTORY_ENTRIES):
  at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
  if disk[at]==0 and disk[at+1:at+12]==b'CONFIG  COM':disk[at]=0xe5
 add_file(disk,'CONFIG.COM',code)
report=dict(report,included=[dict(f,sha256=hashlib.sha256(code+b'\x1a'*((-len(code))%128)).hexdigest(),bytes=((len(code)+127)//128)*128) if f['name']=='CONFIG.COM' else f for f in report['included']])
# audit_files needs a matching private baseline with the rebuilt CONFIG.
base_private=r/'baseline';base_private.mkdir();patched_master=base_private/report['image'];patched_master.write_bytes(build(raw));report['sha256']=sha(patched_master);master=patched_master
(base_private/'diskdefs').write_bytes((base/'diskdefs').read_bytes())
source=r/'source.dmk';target=r/'target.dmk';source.write_bytes(build(raw));target.write_bytes(build(target_raw))
steps=['CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="BetterCP/M Model 4 System 780K"','DIR B:','TYPE B:KEEP.TXT','SYSGEN A: B:INSTALL.SYS','SYSGEN B:INSTALL.SYS B:']
w=r/'install';w.mkdir();cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(source),'-d1',str(target),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']
waits=['Disk configuration changed (until cold boot).','P2DOS','SHIPPED TOOLS INSTALL PRESERVES THIS FILE','Package exported and verified.','Proceed (Y/N)?']
for text,wait in zip(steps,waits):cmd+=key_args(text+'\r',delay=35)+['-iw',wait,'-id','6000','-it']
cmd+=key_args('Y',delay=60)+['-iw','System installed and verified.','-id','6000','-it','-ix']
(w/'invocation.json').write_text(json.dumps(cmd,indent=2));run(cmd,cwd=w,timeout=600)
after=extract_raw(target.read_bytes());assert after[20480:]!=target_raw[20480:] # exported file added
from test_model4_copy import files
old_files=files(target_raw[20480:]);new_files=files(after[20480:])
assert set(new_files)==set(old_files)|{(0,b'INSTALL SYS')}
for k,v in old_files.items():assert new_files[k]==v,k
package=new_files[(0,b'INSTALL SYS')][0];assert len(package)==20608 and package[:4]==b'BCSY'
differences=[(i,x,y) for i,(x,y) in enumerate(zip(package[128:],after[:20480])) if x!=y]
assert differences==[(7030,0xe0,0xa0)],differences
# Compare filesystem bytes captured after export with final install using retained screens separately.
audit_files(master,target,report,r)
cold=r/'cold';cold.mkdir();cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(target),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']
for text,wait in [('TYPE KEEP.TXT','SHIPPED TOOLS INSTALL PRESERVES THIS FILE'),('CONFIG /SHOW','Saved disk-boot IOBYTE (decimal): 149'),('RSX LIST','ADM3A')]:cmd+=key_args(text+'\r',delay=35)+['-iw',wait,'-id','6000','-it']
cmd+=['-ix'];(cold/'invocation.json').write_text(json.dumps(cmd,indent=2));run(cmd,cwd=cold,timeout=450)
texts=[screen(f) for f in sorted(cold.glob('trs80-text*.bin'))];assert len(texts)==3 and 'SHIPPED TOOLS INSTALL PRESERVES THIS FILE' in texts[0]
assert sha(master)==report['sha256']
(r/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':sha(master),'config_sha256':sha(patched),'emulator_sha256':sha(DEFAULT_EMULATOR),'commands':steps+['Y','cold boot target in physical drive 0','TYPE KEEP.TXT','CONFIG /SHOW','RSX LIST'],'cold_screens':texts,'scope':'Only shipped commands; private source and 780K SYSTEM target copies plus KEEP.TXT fixture.'},indent=2))
