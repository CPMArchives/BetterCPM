"""Execute the editor UI, including pending work and full-size sector maps."""
import re
import struct
from dataclasses import replace
from test_fdb_session import Session
from test_fdb_roundtrip import ROOT, machine, diskkey
from build_fdf_catalog import catalogue_payload
from fdfdecomp import decompile
from fdf_v1 import parse, serialize


class DriveSession(Session):
    """Model only the two binding calls, independently of FDB's encoder."""
    def callback(self, kind):
        function = self.reg['C'].value
        super().callback(kind)
        if function == 181:
            self.reg['L'].value = self.status

    def bdos(self, fn, de):
        if fn == 181:
            operation = self.reg['B'].value
            drive = self.mem[de]
            assert drive in (1, 2, 3)
            self.status = 0
            if operation == 3:
                self.mem[de+1:de+65] = self.drives[drive]
            elif operation == 4:
                self.drives[drive] = bytes(self.mem[de+1:de+65])
            else:
                raise AssertionError(operation)
            return 0
        if fn == 37:
            self.reset_masks.append(de)
            return 0
        return super().bdos(fn, de)


def main():
    work=ROOT/'build/fdb-editor-test'
    work.mkdir(parents=True,exist_ok=True)
    m=machine(work,DriveSession)
    m.read_return=int(re.search(r'^([0-9a-f]{4}).*\bASKREAD:',(work/'fdb.lst').read_text(),re.M|re.I)[1],16)
    stock=catalogue_payload()
    entries=parse(decompile(stock))
    src=diskkey(1,'DISK.FDB')
    out=diskkey(1,'OUT.FDB')

    def run(keys, files):
        m.keys=iter(keys)
        m.checkpoints=[]
        m.unexpected_prompt=False
        console=m.run('',files)
        assert not m.unexpected_prompt,console
        return console

    console=run('B\r\rMMI012\rG\r1\rV\r3\rA\r80\rE\r389\rV\rQ\rQ\rD\r',{src:stock})
    assert 'Directory byte: 10240' in console and 'Maximum DSM: 394' in console,console
    assert 'Directory byte: 20480' in console and 'Maximum DSM: 389' in console,console
    assert 'Page 3 E DSM / allowed maximum' in console and 'Format validates.' in console, console
    assert '! invalid allocation' in console
    assert m.files=={src:stock}
    # Reverting an edit clears the indicator and permits a clean exit.
    console=run('B\r\rMMI012\rG\r1\rG\r0\rQ\rQ\r',{src:stock})
    assert 'Working format pending' not in console and m.files=={src:stock}
    # Load an external entry, edit the staged copy and include it in Save As.
    external=replace(entries[0],ident='EXT1',description='external')
    other=diskkey(1,'OTHER.FDB')
    files={src:stock,other:serialize((external,))}
    run('B\rOTHER.FDB\rEXT1\rN\rNew definition\rQ\rS\rW\rY\rOUT.FDB\rY\rQ\r',files)
    assert m.files=={**files,out:serialize((*entries,replace(external,description='New definition')))}
    # Map slot 255 stays accessible. A catalogue can exceed the 32-slot
    # drive-binding ABI and still survive a native edit and save.
    mixed=replace(entries[0],ident='BIG',psectors=255,sector_ids=tuple(range(255)),
                  secsize=1024,sector_sizes=(128,)+(1024,)*254,sides=2,
                  logical_track='CYLINDER',spt=(1+8*254)*2,bsh=7,blm=127,
                  exm=15,dsm=100,al0=128)
    files={src:serialize((mixed,))}
    console=run('B\r\rBIG\r2\rM\r255\r255\r3\rV\rQ\rS\rW\rY\rR\rOUT.FDB\rY\rQ\r',files)
    assert 'Format validates.' in console
    assert m.files[out]==serialize((replace(mixed,sector_ids=tuple(range(254))+(255,)),))
    # Build a valid new definition from a blank editor and stage it separately
    # from the session save. BREAK cancels a field edit without losing it.
    console=run('N\rC\rI\rTINY\rN\rSmall example\rA\r40\rB\r1\r3\rA\r1\r'
                'B\r3\rC\r7\rE\r2\rF\r7\rG\r128\rJ\r\x03V\r'
                'S\rK\rS\rW\rOUT.FDB\rY\rQ\r',{src:stock})
    assert 'Format validates.' in console
    tiny,=parse(decompile(m.files[out]))
    assert (tiny.ident,tiny.description,tiny.cylinders,tiny.dsm,tiny.off)==('TINY','Small example',40,2,0)
    assert m.files[src]==stock
    # Capture an anonymous live definition, name it, reject A, decline D,
    # apply to C, then catalogue the SAME edited copy after applying.
    base=entries[0]
    dpb=struct.pack('<HBBBHHBBHH',base.spt,base.bsh,base.blm,base.exm,base.dsm,
                    base.drm,base.al0,base.al1,base.cks,base.off)
    assert base.sector_sizes is None and base.side_order=='ALTERNATING'
    flags=(128 if base.encoding=='MFM' else 0)|(64 if base.sides==2 else 0)
    template=dpb+bytes((base.cylinders,base.psectors,base.secsize.bit_length()-8,flags))
    template+=bytes(base.sector_ids).ljust(32,bytes(1))+bytes(12)
    m.drives={n:bytes([n])+template for n in (1,2,3)}
    m.reset_masks=[]
    console=run('A\rB\rI\rcap1\rN\rCaptured format\r3\rE\r100\rS\rD\rA\r'
                '\x03E\rS\rD\rD\rN\rS\rD\rC\rY\rS\rK\rS\rW\rOUT.FDB\rY\rQ\r',{src:stock})
    assert '<unset> <unset>' in console
    assert m.reset_masks==[4]
    assert m.drives[1]==b'\x01'+template and m.drives[3]==b'\x03'+template
    expected=bytearray(b'\x02'+template)
    expected[6:8]=bytes((100,0))
    assert m.drives[2]==expected
    assert m.files[out]==serialize((*entries,replace(base,ident='CAP1',description='Captured format',dsm=100)))
    # Applying a cylinder catalogue format uses surface-track runtime units,
    # while retaining the original format in the working catalogue/editor.
    before_drives = dict(m.drives)
    m.reset_masks=[]
    console=run('B\r\rBCPM780\rS\rD\rB\rY\rQ\rQ\r',{src:stock})
    cylinder=next(entry for entry in entries if entry.ident=='BCPM780')
    expected=bytearray(64)
    expected[0]=before_drives[1][0]
    expected[1:16]=struct.pack('<HBBBHHBBHH',cylinder.spt//2,cylinder.bsh,
        cylinder.blm,cylinder.exm,cylinder.dsm,cylinder.drm,cylinder.al0,
        cylinder.al1,cylinder.cks,cylinder.off*2)
    expected[16:20]=bytes((cylinder.cylinders,cylinder.psectors,
                           cylinder.secsize.bit_length()-8,0xC0))
    expected[20:20+cylinder.psectors]=bytes(cylinder.sector_ids)
    assert m.drives[1]==expected, (console,m.drives[1].hex(),expected.hex())
    assert m.drives[2]==before_drives[2] and m.drives[3]==before_drives[3]
    assert m.files=={src:stock} and m.reset_masks==[2]
    viewfiles={src:stock,diskkey(1,'FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes()}
    console=run('P\r:B\r:C\r4\rA\rQ\rQ\r', viewfiles)
    assert '<unknown> | <unknown>' in console and m.files==viewfiles
    console=run('B\r\rMMI012\rG\r1\rQ\rD\r@\rE\rG\r0\rQ\rQ\r',viewfiles)
    assert 'Cannot inspect; format preserved.' in console and 'Working format pending' not in console
    print('PASS effective geometry, DSM warning, external working copy, mixed 255-slot editing and save')


if __name__=='__main__':
    main()
