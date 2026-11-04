from pathlib import Path
import sys,re,json,hashlib
r=Path('/Users/nathanael/.codex/.chatgpt-projects/g-p-6a682f002be881918281554d644daf48/native-fdb');sys.path.insert(0,str(r/'tools'))
from test_fdb_roundtrip import machine,diskkey
from test_fdb_session import Session
from build_fdf_catalog import catalogue_payload
out=r.parent/'fdb-usability-review-20261104';out.mkdir(exist_ok=True)
m=machine(out,Session);m.read_return=int(re.search(r'^([0-9a-f]{4}).*\bASKREAD:',(out/'fdb.lst').read_text(),re.M|re.I)[1],16)
files={diskkey(1,'DISK.FDB'):catalogue_payload(),diskkey(1,'FDBVIEW.OVL'):(out/'FDBVIEW.OVL').read_bytes()}
cases=[('displayed-du-filename','F\rA0:DISK.FDB\rQ\r',files),('missing-detail-id','D\rNOPE\rQ\r',files),('unknown-viewer-key','D\rMMI012\r2\rZ\rQ\rQ\r',files),('past-map-end','D\rMMI012\r2\r>\r>\rQ\rQ\r',files),('overlong-filter-backspace','L\r'+'X'*33+'\x08\x08\rQ\r',files),('untitled-save-default','N\rS\r\rQ\r',files),('missing-viewer','D\rQ\r',{diskkey(1,'DISK.FDB'):catalogue_payload()}),('pending-unmodified','C\rQ\rQ\rD\r',files),('generic-validation','B\r\rMMI012\rG\r1\rV\rQ\rQ\rD\r',files)]
results=[]
for name,keys,original in cases:
 m.keys=iter(keys);m.checkpoints=[];m.unexpected_prompt=False
 failure=None
 try:text=m.run('',original)
 except AssertionError as error:
  assert name=='overlong-filter-backspace' and 'console exceeds80columns' in str(error),str(error)
  text=m.console;failure='Console width assertion failed: 94 columns; retained as a finding, not a passing test'
 assert not m.unexpected_prompt,(name,text);assert m.files==original,(name,'changed files')
 (out/(name+'.txt')).write_text(text);results.append({'case':name,'files_unchanged':True,'transcript':name+'.txt','finding_assertion':failure})
 print(name,repr(text[-550:]))
(out/'results.json').write_text(json.dumps({'source_commit':'066336cd','scope':'Compiled full-Z80 review probes with model BDOS; not new native-platform qualification','com_sha256':hashlib.sha256(m.image).hexdigest(),'cases':results},indent=2)+'\n')
