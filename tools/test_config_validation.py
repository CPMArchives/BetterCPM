#!/usr/bin/env python3
"""CONFIG fingerprint generation: exact editable masks and bounded records."""
import struct
import unittest
import zlib
from config_validation import validation_record,assembly


class ValidationRecords(unittest.TestCase):
    def setUp(self):
        self.base=0xd400;self.physical=self.base+64;self.logical=self.base+128
        self.data=bytearray((i*17+3)&255 for i in range(52*128))
        self.data[:8]=b'BDCF'+bytes((5,4,4,64))
        struct.pack_into('<HH',self.data,8,self.physical,self.logical)

    def record(self,data=None):
        return validation_record(self.data if data is None else data,self.base,52,8,80)

    def test_exact_normalization_and_crc(self):
        original=bytes(self.data);masked=bytearray(original)
        editable=set(range(64,88))
        for i in range(4):editable.update(range(128+i*80+16,128+(i+1)*80))
        for n in editable:masked[n]=0
        record=self.record()
        self.assertEqual(len(record),20)
        self.assertEqual(struct.unpack_from('<I',record,16)[0],zlib.crc32(masked))
        changed=bytearray(original)
        for n in editable:changed[n]^=0xff
        self.assertEqual(self.record(changed),record)
        # Fixed bytes include the DPH's first 16 bytes, unlike its binding.
        for n in [63,88,128,143,208,223,len(original)-1]:
            changed=bytearray(original);changed[n]^=1
            self.assertNotEqual(self.record(changed),record)
        changed=bytearray(original);changed[0]^=1
        with self.assertRaises(ValueError):self.record(changed)
        self.assertEqual(bytes(self.data),original)

    def test_bounds_and_ambiguous_profiles(self):
        bad=bytearray(self.data);struct.pack_into('<H',bad,8,self.base+len(bad)-1)
        with self.assertRaises(ValueError):self.record(bad)
        record=self.record();changed=bytearray(record);changed[-1]^=1
        with self.assertRaisesRegex(ValueError,'ambiguous'):assembly([record,bytes(changed)])
        self.assertEqual(assembly([record,record]),assembly([record]))


if __name__=='__main__':unittest.main()
