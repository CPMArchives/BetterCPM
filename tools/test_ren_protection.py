#!/usr/bin/env python3
"""Exercise REN /P preservation and attribute-repair failures."""
from test_ren_core import run
OLD=(1,1,b'FOO     DOC');NEW=(1,1,b'FOO     TXT');OTHER=(1,1,b'ZOO     DOC')
def main():
 for attr in range(8):
  files={OLD:attr};changes,out=run('/P B1:*.DOC *.TXT',files)
  assert len(changes)==1 and files=={NEW:attr},(attr,files,out)
  files={OLD:attr};changes,out=run('B1:*.DOC *.TXT',files)
  assert len(changes)==(0 if attr&3 else 1)
 for flags in ('/P /DRY','/P /N','/P /DRY /Y /QQ'):
  files={OLD:7};changes,out=run(flags+' B1:*.DOC *.TXT',files)
  assert not changes and files=={OLD:7}
 files={OLD:7};changes,out=run('/P B1:*.DOC *.TXT',files,'R',rename_failures={OLD:1})
 assert len(changes)==1 and files=={NEW:7},(files,out)
 files={OLD:7};changes,out=run('/P B1:*.DOC *.TXT',files,'S',rename_failures={OLD:1})
 assert not changes and files=={OLD:7},(files,out)
 files={OLD:7};changes,out=run('/P /Y B1:*.DOC *.TXT',files,attr_failures=[True,False])
 assert not changes and files=={OLD:7} and '1 FAILED' in out
 # Failed restoration stops the command; it must not retry an already moved source.
 files={OLD:7,OTHER:0};changes,out=run('/P /Y B1:*.DOC *.TXT',files,attr_failures=[False,True])
 assert len(changes)==1 and OTHER in files and 'Unable to restore file attributes' in out
 for attrs in ((1,5),(2,6)):
  files={OLD:attrs};changes,out=run('/P /Y B1:*.DOC *.TXT',files)
  assert not changes and files=={OLD:attrs} and 'Inconsistent extent attributes' in out
 files={OLD:7};changes,out=run('/P /Y B1:*.DOC *.TXT',files,drive_ro=True)
 assert not changes and files=={OLD:7},out
 files={OLD:1,OTHER:2};changes,out=run('/P B1:*.DOC[$SYS] *.TXT',files)
 assert len(changes)==1 and files[OLD]==1 and files[(1,1,b'ZOO     TXT')]==2
 print('PASS: REN /P all attributes, protection, no-write policies, failed rename repair, clear/restore failures, mixed extents, drive RO and selector independence')
if __name__=='__main__':main()
