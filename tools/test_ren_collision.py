#!/usr/bin/env python3
"""Run collision help, edited literal names and rescan safety in REN.COM."""
from test_ren_core import run
OLD=b'FOO     DOC';TARGET=b'FOO     TXT'
def fixture():return {(1,1,OLD):4,(1,1,TARGET):0}
def main():
 changes,out=run('B1:FOO.DOC FOO.TXT',fixture(),'?Nbad*name.doc\rB:BAD.TXT\rfoo.txt\rNnew.txt\r')
 assert len(changes)==1 and changes[0][1][2]==b'NEW     TXT',out
 assert out.count('N New name, S Skip file, A Abort remainder.')==1
 assert out.count('Invalid filename.')==2 and out.count('File exists.')==3,out
 files=fixture();changes,out=run('B1:FOO.DOC FOO.TXT',files,'N\rS')
 assert not changes and files==fixture() and '1 SKIPPED' in out
 for response in ('A','\x03','N\x03'):
  files=fixture();changes,out=run('B1:FOO.DOC FOO.TXT',files,response)
  assert not changes and files==fixture()
 changes,out=run('B1:FOO.DOC FOO.TXT',fixture(),'Nbad.txt\x15good.txz\x08t\r')
 assert len(changes)==1 and changes[0][1][2]==b'GOOD    TXT'
 changes,out=run('B1:FOO.DOC FOO.TXT',fixture(),'N'+'X'*40+'\rnew.txt\r')
 assert len(changes)==1 and 'Invalid filename.' in out
 changes,out=run('B1:FOO.DOC FOO.TXT',fixture(),'Nfoo[$RO]\rN[W].TXT\rnew.txt\r')
 assert len(changes)==1 and out.count('Invalid filename.')==2,out
 changes,out=run('B1:FOO.DOC FOO.TXT',fixture(),'Nfoo.doc\r')
 assert not changes and 'SAME NAME' in out
 # Arbitrary replacement remains in original source pattern and is not a fixed point.
 files={(1,1,b'FOO     DOC'):0,(1,1,b'XOO     DOC'):0}
 changes,out=run('B1:*.DOC X*.DOC',files,'Nzoo.doc\r')
 assert len(changes)==1 and changes[0][1][2]==b'ZOO     DOC',out
 assert (1,1,b'ZOO     DOC') in files and (1,1,b'XOO     DOC') in files
 # Existing original source must never be overwritten through the name prompt.
 files={(1,1,OLD):0,(1,1,TARGET):0,(1,1,b'BAR     DOC'):0}
 changes,out=run('B1:FOO.DOC FOO.TXT',files,'Nbar.doc\rS')
 assert not changes and files[(1,1,b'BAR     DOC')]==0
 # Confirmation still applies to the chosen replacement.
 changes,out=run('/C B1:FOO.DOC FOO.TXT',fixture(),'Nnew.txt\rN')
 assert not changes and 'Rename? Y/N' in out
 for capacity in (0,1):
  files={(1,1,b'BAR     DOC'):0,(1,1,OLD):0}
  changes,out=run('B1:*.DOC *.TXT',files,ledger_capacity=capacity)
  assert len(changes)==capacity and 'Insufficient memory.' in out,out
 print('PASS: REN collision help, retry names, editing, overflow, blank, abort, self-map, source overlap and rescan ledger')
if __name__=='__main__':main()
