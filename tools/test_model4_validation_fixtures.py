#!/usr/bin/env python3
"""Check the independent native fixture decoder, without a host-tool round trip."""
import hashlib
import tempfile
from pathlib import Path
from run_validation_model4_directory import preflight_data


def main():
    with tempfile.TemporaryDirectory(prefix='model4-fixture-check-') as temporary:
        work=Path(temporary)
        payload=b'A'*16384+b'END'
        source=work/'BTRO.DAT';source.write_bytes(payload)
        raw=bytearray(b'\xe5'*819200)
        blocks=list(range(8,16))+[300]  # Exercise a second extent and a high block byte.
        for extent,allocated in enumerate((blocks[:8],blocks[8:])):
            entry=bytearray(32);entry[0]=7;entry[1:12]=b'BTRO    DAT'
            entry[9]|=128;entry[12]=extent;entry[15]=128 if extent==0 else 1
            for index,block in enumerate(allocated):entry[16+index*2:18+index*2]=block.to_bytes(2,'little')
            raw[extent*32:(extent+1)*32]=entry
        padded=payload+b'\x1a'*125
        for index,block in enumerate(blocks):
            chunk=padded[index*2048:(index+1)*2048]
            raw[block*2048:block*2048+len(chunk)]=chunk
        (work/'b.raw').write_bytes(raw);(work/'c.raw').write_bytes(b'\xe5'*819200)
        fixture={'drive':'B','user':7,'name':'BTRO.DAT','source':str(source),'sha256':hashlib.sha256(payload).hexdigest()}
        checked=preflight_data(work,[fixture])
        assert checked['b']['allocated_blocks_including_directory']==11
        assert checked['b']['verified_files'][0]['bytes']==len(payload)
        def rejected(data,diagnostic):
            (work/'b.raw').write_bytes(data)
            try:preflight_data(work,[fixture])
            except AssertionError as error:assert diagnostic in str(error),str(error)
            else:raise AssertionError('invalid fixture passed: '+diagnostic)
        misplaced=bytearray(raw);misplaced[300*2048:300*2048+128]=b'\xe5'*128
        misplaced[301*2048:301*2048+128]=padded[-128:]
        rejected(misplaced,'misplaced fixture data')
        shared=bytearray(raw);shared[48:50]=(8).to_bytes(2,'little')
        rejected(shared,'duplicate allocation block')
        hole=bytearray(raw);hole[15]=127
        rejected(hole,'hole in dense fixture extents')
    print('Native fixture decoder verifies dense extents, 16-bit blocks and RO; rejects misplaced/shared data and extent holes.')


if __name__=='__main__':main()
