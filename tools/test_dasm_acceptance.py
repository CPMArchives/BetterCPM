#!/usr/bin/env python3
"""Reject acceptance receipts for different binaries, images or failed platforms."""
import copy,unittest
from build_utilities_disk import validate_dasm_acceptance,sha

class Acceptance(unittest.TestCase):
 def setUp(self):
  self.files={n:b'code'+n.encode() for n in ('DASM.COM','DSYM.COM','DLINK.COM')}
  self.receipt={'dasm_acceptance':'PASS','binaries':{n:{'sha256':sha(b)} for n,b in self.files.items()},'platforms':{'z80pack':{'status':'PASS','utilities_sha256':sha(b'disk'),'system_sha256':'system'}}}
 def test_exact(self):
  self.assertEqual(validate_dasm_acceptance(self.receipt,self.files,'z80pack',b'disk')['status'],'PASS')
 def test_mismatches(self):
  for kind in ('status','image','DASM.COM','DSYM.COM','DLINK.COM','platform','system'):
   with self.subTest(kind=kind):
    q=copy.deepcopy(self.receipt)
    if kind=='status':q['dasm_acceptance']='IN_PROGRESS'
    elif kind=='image':q['platforms']['z80pack']['utilities_sha256']='wrong'
    elif kind in self.files:q['binaries'][kind]['sha256']='wrong'
    elif kind=='platform':q['platforms']['z80pack']['status']='FAIL'
    else:q['platforms']['z80pack']['system_sha256']=''
    with self.assertRaises(ValueError):validate_dasm_acceptance(q,self.files,'z80pack',b'disk')
if __name__=='__main__':unittest.main()
