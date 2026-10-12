#!/usr/bin/env python3
"""Inject rename failures and exercise retry policy without real disk writes."""
from test_ren_core import run
A=(1,1,b'BAR     DOC');B=(1,1,b'FOO     DOC')
def fixture():return {A:4,B:0}
def main():
 changes,out=run('B1:*.DOC *.TXT',fixture(),'?R',rename_failures={A:1})
 assert len(changes)==2 and '2 FILES RENAMED' in out and ' FAILED' not in out,out
 assert out.count('R Retry, S Skip file, A Abort remainder.')==1
 changes,out=run('/C B1:*.DOC *.TXT',fixture(),'YR Y'.replace(' ',''),rename_failures={A:1})
 assert len(changes)==2 and out.count('Rename? Y/N')==2,out
 changes,out=run('B1:*.DOC *.TXT',fixture(),'RS',rename_failures={A:2})
 assert len(changes)==1 and '1 FILES RENAMED, 1 FAILED' in out,out
 for response in ('A','\x03'):
  files=fixture();changes,out=run('B1:*.DOC *.TXT',files,response,rename_failures={B:1})
  assert len(changes)==1 and B in files and '1 FILES RENAMED, 1 FAILED' in out,out
 for flags in ('/Y','/QQ','/Y /QQ','/Q /Y'):
  changes,out=run(flags+' B1:*.DOC *.TXT',fixture(),rename_failures={A:1})
  assert len(changes)==1
  if '/QQ' in flags:assert out==('' if '/Y' in flags else 'REN: /Y not specified. /QQ assumes /Y.\r\n'),repr(out)
  else:assert '1 FILES RENAMED, 1 FAILED' in out,out
 # A new target appearing after a failed attempt must not be overwritten on retry.
 files=fixture();changes,out=run('B1:*.DOC *.TXT',files,'RS',rename_failures={A:1},racing_target=True)
 assert len(changes)==1 and files[(1,1,b'BAR     TXT')]==4 and A in files,out
 assert 'File exists. N/S/A/?' in out
 changes,out=run('/Y B1:*.DOC *.TXT',fixture(),drive_ro=True)
 assert not changes and '2 FAILED' in out,out
 changes,out=run('/DRY B1:*.DOC *.TXT',fixture(),drive_ro=True)
 assert not changes and 'Dry run only:' in out
 print('PASS: REN retry/help, skip/abort, no duplicate confirmation, failed accounting, unattended policy, retry target race and read-only drive')
if __name__=='__main__':main()
