import argparse,gzip,hashlib,io,json,os,platform,subprocess,sys,tarfile,zipfile,zlib
from pathlib import Path,PurePosixPath

sha=lambda b:hashlib.sha256(b).hexdigest()
REPO='CPMArchives/BetterCPM'

def safe(root,name):
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe publication path')
 path=(root/name).resolve();path.relative_to(root.resolve());return path

def archive(path,rows,read):
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for row in sorted(rows,key=lambda r:r['name']):
   item=zipfile.ZipInfo(row['name'],(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
   item.external_attr=0o100644<<16;z.writestr(item,read(row))
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  for row in rows:assert sha(z.read(row['name']))==row['sha256']

def gh(*args):
 return subprocess.check_output(['gh',*args],text=True)

def release():return json.loads(gh('api','repos/'+REPO+'/releases/tags/v1.3'))

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--publish',action='store_true');a=p.parse_args()
 raw=b''.join(f.read_bytes() for f in sorted(a.inputs.glob('inputs.part*')))
 files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
  for member in t:
   if not member.isfile():raise ValueError('unexpected publication bundle member')
   safe(a.output,member.name);files[member.name]=t.extractfile(member).read()
 m=json.loads(files['manifest.json']);a.output.mkdir(parents=True,exist_ok=False)
 def read(row):
  data=safe(a.source,row['source']).read_bytes() if 'source' in row else files['payload/'+row['payload']]
  assert len(data)==row['bytes'] and sha(data)==row['sha256'],row.get('name',row)
  return data
 expected={}
 print('Python',sys.version,'zlib',zlib.ZLIB_RUNTIME_VERSION,flush=True)
 for row in m['archives']:
  target=safe(a.output,row['name']);archive(target,row['members'],read)
  actual=sha(target.read_bytes());print(row['name'],actual,flush=True)
  assert actual==row['sha256'],'archive bytes differ from approved candidate: '+row['name']
  expected[row['name']]=actual
 for row in m['support']:
  safe(a.output,row['name']).write_bytes(read(row));expected[row['name']]=row['sha256']
 result={'status':'PASS','source_commit':m['source_commit'],'assets':expected,'publication':'not requested'}
 if a.publish:
  before=release();old={r['name']:r for r in before['assets']}
  for row in m['existing_assets']:
   observed=old[row['name']]
   assert all(observed[k]==row[k] for k in ('id','size','digest')),'existing asset changed: '+row['name']
  for name,wanted in expected.items():
   if name in old:
    assert old[name].get('digest')=='sha256:'+wanted,'existing additive asset differs: '+name
    continue
   print('Uploading',name,flush=True)
   gh('release','upload','v1.3',str(a.output/name),'--repo',REPO)
  after=release();assets={r['name']:r for r in after['assets']}
  for row in m['existing_assets']:
   assert all(assets[row['name']][k]==row[k] for k in ('id','size','digest')),'existing asset changed'
  for name,wanted in expected.items():assert assets[name].get('digest')=='sha256:'+wanted,(name,assets[name].get('digest'),wanted)
  heading='## Altair Z80 / Tarbell addition'
  if heading not in (after.get('body') or ''):
   addition='''

## Altair Z80 / Tarbell addition

BetterCP/M 1.3 now includes the Altair Z80 platform: 64 KiB RAM, 88-2SIO console and Tarbell 1011D single-density floppy controller under the pinned z80pack Altair emulator.

- **[Altair System + Utilities package](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/BetterCPM-1.3-Altair.zip)** — System, three Utilities disks, a writable Work template, launcher, offline emulator source, notices and qualification evidence.
- **[Matching Altair source](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/BetterCPM-1.3-Altair-Source.zip)** and **[checksums](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/SHA256SUMS-Altair-1.3.txt)**.
- **[Altair installation guide](https://github.com/CPMArchives/BetterCPM/blob/main/docs/platform/ALTAIR-INSTALLATION.md)** and **[exact artifact ledger](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/ALTAIR-RELEASE.json)**.

Extract to a fresh folder and run `python3 Run-Altair.py`. The first launch builds the emulator using a C compiler and make; subsequent launches preserve the working session. The banner identifies `BetterCP/M 1.3 - Altair`.

All seven platform acceptance gates pass, including 269 automatic compatibility assertions, installation/configuration, disk management, media errors, 45 utility identity queries, full-screen HELP with all three terminal personalities, NOAH overlays and native assembler/linker execution. Qualification covers this emulator configuration; physical Altair hardware and the 8080 CPU remain unqualified. Altair currently uses fixed Tarbell single-density geometry.

This is an additional platform for OS 1.3. Existing cpmsim and TRS-80 downloads remain unchanged. The matching frozen Altair product source is `6bfb621b6348e1f3782e2f12be4512fe37197306`.
'''
   notes=a.output/'release-notes.md';notes.write_text((after.get('body') or '')+addition)
   gh('release','edit','v1.3','--repo',REPO,'--notes-file',str(notes))
  result.update(publication='PUBLISHED; all uploaded digests verified; original assets unchanged',release_url=after['html_url'],asset_urls={n:assets[n]['browser_download_url'] for n in expected})
 (a.output/'publication-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
