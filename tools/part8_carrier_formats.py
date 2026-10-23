"""Candidate CCP/CPX carriers: binding trailer outside relocation headers.
Not installed on prototype media until the command loader is redesigned.
"""
import struct

def candidate(data,identity):
    b=bytearray(data)
    if b[:4]==b'BCPX':
        assert b[4]==1
        name=b[32:40].decode().strip();public=name=='HELLO'
        b[4]=2
        end=struct.unpack_from('<H',b,30)[0]+8*b[42]
        assert end==len(b)
    elif b[:4]==b'BCM1':
        assert b[4]==1
        public=False;b[:4]=b'BCM2';b[4]=2
        end=512*b[5]+struct.unpack_from('<H',b,8)[0]
        assert end==len(b)
    else:raise ValueError('unsupported carrier')
    return bytes(b)+b'BP'+bytes((1,0 if public else 1))+(bytes(16) if public else bytes.fromhex(identity))

def inspect(data,identity):
    if data[:4]==b'BCPX':
        if data[:8]!=b'BCPX\2\1\1\0':raise ValueError('CPX format/ABI')
        linked,size,allocation,entry,init,shutdown,nrel,header,payload,table,metadata=struct.unpack_from('<11H',data,10)
        if not (512<=header<=1536 and header%512==0 and payload==header and table==48 and table+2*nrel<=header and metadata==header+size):raise ValueError('CPX bounds')
        if not size or allocation<size or allocation%256 or entry>=size:raise ValueError('CPX allocation')
        if (sum(data[payload:metadata])&65535)!=struct.unpack_from('<H',data,44)[0]:raise ValueError('CPX checksum')
        end=metadata+8*data[42];private_required=False
    elif data[:4]==b'BCM2':
        if data[4:6]!=b'\2\2':raise ValueError('CCP version/header')
        linked,size,allocation,entry,nrel=struct.unpack_from('<5H',data,6)
        if not size or allocation<size or allocation%256 or entry>=size or 16+2*nrel>1024:raise ValueError('CCP bounds')
        end=1024+size;private_required=True
    else:raise ValueError('legacy/unknown format')
    if len(data)!=end+20:raise ValueError('binding extent')
    rec=data[end:]
    if rec[:3]!=b'BP\1' or rec[3] not in (0,1):raise ValueError('binding schema/class')
    if private_required and rec[3]!=1:raise ValueError('CCP must be private')
    expected=bytes.fromhex(identity) if rec[3] else bytes(16)
    if rec[4:]!=expected:raise ValueError('binding identity')
    return {'binding_offset':end,'class':rec[3],'bytes':len(data),'allocation':allocation}
