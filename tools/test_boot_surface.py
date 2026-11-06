"""Host/native round trips for the required reserved-first-surface profile."""
from dataclasses import replace
import re
from fdf_v1 import parse, serialize, read_fdb, crc16
from fdfdecomp import decompile
from test_fdb_roundtrip import machine, diskkey, ROOT
from test_fdb_editor import DriveSession

TEXT = '''FDF_VERSION 1
FORMAT
ID ATONSS
DESCRIPTION "ATON/Lifeboat Model II SS"
SPT 64
BSH 4
DSM 299
DRM 127
AL0 192
AL1 0
CKS 32
OFF 2
PSECTORS 8
SECSIZE 1024
CYLINDERS 77
SIDES 1
ENCODING MFM
SECTOR_IDS 1,4,7,2,5,8,3,6
BOOT_PSECTORS 26
BOOT_SECSIZE 128
BOOT_ENCODING FM
BOOT_SECTOR_IDS 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26
END
'''

def formats():
    ss, = parse(TEXT)
    return ss, replace(ss, ident='ATONDS', description='ATON Model II DS', sides=2,
                      dsm=607, drm=191, al0=224, cks=48)

class BootSession(DriveSession):
    capability=0xb301
    def bdos(self,fn,de):
        if fn==181:
            self.operations.append(self.reg['B'].value)
            if self.reg['B'].value==6:
                self.status=self.capability & 255
                return 0
        return super().bdos(fn,de)
    def callback(self,kind):
        operation=self.reg['B'].value;function=self.reg['C'].value
        super().callback(kind)
        if function==181:self.reg['H'].value=(self.capability>>8 if operation==6 else 0)

def main():
    work=ROOT/'build/boot-surface-test';work.mkdir(parents=True,exist_ok=True)
    entries=formats(); payload=serialize(entries)
    assert tuple(d.format for d in read_fdb(payload).descriptors)==entries
    assert serialize(parse(decompile(payload)))==payload
    m=machine(work,BootSession)
    m.read_return=int(re.search(r'^([0-9a-f]{4}).*\bASKREAD:',(work/'fdb.lst').read_text(),re.M|re.I)[1],16)
    key=lambda name:diskkey(1,name)
    console=m.run('IN.FDF OUT.FDB',{key('IN.FDF'):decompile(payload).encode()})
    assert m.files.get(key('OUT.FDB'))==payload,console
    console=m.run('IN.FDB OUT.FDF',{key('IN.FDB'):payload})
    assert serialize(parse(m.files[key('OUT.FDF')].split(b'\x1a')[0].decode()))==payload,console
    m.keys=iter('B\r\rATONDS\rN\rEdited ATON\rV\rQ\rS\rW\rY\rR\rOUT.FDB\rY\rQ\r')
    m.checkpoints=[];m.unexpected_prompt=False
    console=m.run('',{key('DISK.FDB'):payload})
    assert not m.unexpected_prompt,console
    assert m.files.get(key('OUT.FDB'))==serialize((entries[0],replace(entries[1],description='Edited ATON'))),console
    # Host and native compiler must reject incomplete, unreserved, ambiguous,
    # oversized, duplicate-ID and invalid-encoding boot profiles.
    badtexts=[TEXT.replace('BOOT_ENCODING FM\n',''), TEXT.replace('OFF 2','OFF 0'),
              TEXT.replace('SIDES 1','SIDES 1\nLOGICAL_TRACK CYLINDER'),
              TEXT.replace('BOOT_SECSIZE 128','BOOT_SECSIZE 1024'),
              TEXT.replace('24,25,26','24,25,25'), TEXT.replace('BOOT_ENCODING FM','BOOT_ENCODING BAD')]
    for bad in badtexts:
        try: parse(bad)
        except ValueError: pass
        else: raise AssertionError(bad)
        console=m.run('IN.FDF OUT.FDB',{key('IN.FDF'):bad.encode()})
        assert key('OUT.FDB') not in m.files,console
    # Apply the same edited catalogue binding only with the advertised BIOS.
    import struct
    f=entries[0]
    template=struct.pack('<HBBBHHBBHH',f.spt,f.bsh,f.blm,f.exm,f.dsm,f.drm,f.al0,f.al1,f.cks,f.off)
    template+=bytes((77,8,3,128))+bytes(f.sector_ids).ljust(32,b'\0')+bytes(12)
    for capability in (2,0xb301):
        m.capability=capability;m.operations=[];m.reset_masks=[]
        m.drives={n:bytes([n])+template for n in (1,2,3)};before=dict(m.drives)
        m.keys=iter('B\r\rATONSS\rS\rD\rB\rY\rQ\rQ\r');m.checkpoints=[];m.unexpected_prompt=False
        console=m.run('',{key('DISK.FDB'):payload})
        assert not m.unexpected_prompt,console
        if capability==2:
            assert m.drives==before and not m.reset_masks and 4 not in m.operations
        else:
            assert m.operations[-2:]==[6,4] and m.reset_masks==[2]
            assert m.drives[1][61]==1
    viewfiles={key('DISK.FDB'):payload,key('FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes()}
    m.keys=iter('D\rATONDS\r4\rQ\rQ\r');m.checkpoints=[];m.unexpected_prompt=False
    console=m.run('',viewfiles)
    assert 'Boot exception: 1' in console and 'Canonical directory byte: 16384' in console,console
    assert m.stack_used<96,m.stack_used
    print('PASS boot-surface host/native compile, export, editor preservation and rejection; stack',m.stack_used)

if __name__=='__main__':main()
