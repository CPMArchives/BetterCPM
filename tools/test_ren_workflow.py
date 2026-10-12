#!/usr/bin/env python3
"""Exercise REN confirmation, reporting and no-write option precedence."""
from test_ren_core import run
A=b'FOO     DOC';B=b'BAR     DOC'
def fixture():return {(1,1,A):0,(1,1,B):0}
def main():
 changes,out=run('B1:*.DOC *.TXT',fixture())
 assert len(changes)==2 and '2 FILES RENAMED' in out and 'FOO.DOC -> FOO.TXT success' in out
 for tail in ('/DRY /Y B1:*.DOC *.TXT','/Y B1:*.DOC /DRY *.TXT','B1:*.DOC *.TXT /N','/C /Y /N B1:*.DOC *.TXT'):
  files=fixture();before=files.copy();changes,out=run(tail,files)
  assert not changes and files==before,(tail,out)
  assert 'BAR.DOC -> BAR.TXT' in out
 changes,out=run('/C /N /Y B1:*.DOC *.TXT',fixture())
 assert len(changes)==2
 changes,out=run('/C B1:*.DOC *.TXT',fixture(),'NY')
 assert len(changes)==1 and '1 FILES RENAMED, 1 SKIPPED' in out,out
 changes,out=run('/C B1:*.DOC *.TXT',fixture(),'\x03')
 assert not changes
 changes,out=run('B1:*.DOC *.TXT',{(1,1,A):1,(1,1,B):2})
 assert not changes and 'BAR.DOC -> BAR.TXT [SKIPPED - SYSTEM]' in out and 'FOO.DOC -> FOO.TXT [SKIPPED - READ ONLY]' in out,out
 changes,out=run('/Q B1:*.DOC *.TXT',fixture())
 assert len(changes)==2 and out=='2 FILES RENAMED\r\n',repr(out)
 notice='REN: /Y not specified. /QQ assumes /Y.\r\n'
 changes,out=run('/QQ B1:*.DOC *.TXT',fixture())
 assert len(changes)==2 and out==notice,repr(out)
 for tail in ('/Y /QQ B1:*.DOC *.TXT','/QQ B1:*.DOC *.TXT /Y'):
  changes,out=run(tail,fixture());assert len(changes)==2 and out=='',repr(out)
 for tail in ('/DRY /QQ B1:*.DOC *.TXT','/QQ /DRY /Y B1:*.DOC *.TXT'):
  changes,out=run(tail,fixture());assert not changes and out=='',repr(out)
 changes,out=run('/QQ /N B1:*.DOC *.TXT',fixture())
 assert not changes and out==notice
 for tail in ('/Y B1:*.DOC *.TXT','/QQ B1:*.DOC *.TXT','/N B1:*.DOC *.TXT'):
  files=fixture();files[(1,1,b'BAR     TXT')]=4
  changes,out=run(tail,files)
  assert len(changes)==(0 if '/N' in tail else 1) and files[(1,1,b'BAR     TXT')]==4
 for tail in ('B1:*.DOC *.TXT /BAD','/Y B1:*.DOC *.TXT /C=Y'):
  files=fixture();before=files.copy();changes,out=run(tail,files)
  assert not changes and files==before and 'Invalid filespec.' in out
 changes,out=run('/Y /Q B1:*.DOC *.TXT /QQ /Q',fixture())
 assert len(changes)==2 and out=='2 FILES RENAMED\r\n'
 changes,out=run('[B1,B3]:*.DOC *.TXT',{(1,1,A):0,(1,3,B):0})
 assert out.index('B1:')<out.index('FOO.DOC')<out.index('B3:')<out.index('BAR.DOC'),out
 print('PASS: REN confirmations, Ctrl-C, preview, grouping, summaries, quiet modes, collision skips and complete option validation')
if __name__=='__main__':main()
