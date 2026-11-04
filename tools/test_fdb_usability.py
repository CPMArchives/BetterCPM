"""Execute the 1.01 usability cases and their state-preservation postconditions."""
from pathlib import Path
from dataclasses import replace
import json
import re
import struct
from test_fdb_roundtrip import machine,diskkey,ROOT
from test_fdb_editor import DriveSession
from build_fdf_catalog import catalogue_payload
from fdfdecomp import decompile
from fdf_v1 import parse,serialize


def main():
    work=ROOT/'build/fdb-usability-test';work.mkdir(parents=True,exist_ok=True)
    m=machine(work,DriveSession)
    layout=(work/'fdb.lst').read_text()
    address=lambda name:int(re.search(r'^([0-9a-f]{4}).*\b'+name+':',layout,re.M|re.I)[1],16)
    assert address('IMAGEEND')<=0x3600 and address('EDITOREND')<=0xd3fc
    assert 0xa500+len((work/'FDBVIEW.OVL').read_bytes())+128<=0xb800
    assert 0xb800+255<=0xb900 and 0xc700+255<=0xc800
    m.read_return=int(re.search(r'^([0-9a-f]{4}).*\bASKREAD:',(work/'fdb.lst').read_text(),re.M|re.I)[1],16)
    key=lambda name:diskkey(1,name)
    stock=catalogue_payload();entries=parse(decompile(stock))
    original={key('DISK.FDB'):stock,key('FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes()}
    cases=[]
    def run(name,keys,files=original,user=0):
        m.keys=iter(keys);m.checkpoints=[];m.unexpected_prompt=False
        text=m.run('',files,user=user)
        assert not m.unexpected_prompt,(name,text)
        assert m.files==files,(name,m.files.keys())
        (work/(name+'.txt')).write_text(text)
        cases.append(name)
        return text

    # Both aliases, bounded last/partial chunks and local invalid-key retry.
    text=run('map-aliases','D\rMMI012\r2\r.\r>\r,\r<\rZ\rBAD\rQ\rQ\r')
    assert text.count('9-10/10')==2 and text.count('1-8/10')==3,text
    assert '17 absent' not in text and 'Invalid choice' in text
    assert text.count('Slot ID/bytes')==5,'invalid key appended another map'
    # Empty differences mean this range, not the entire comparison.
    text=run('empty-map-differences','P\rMMI012\rMMI012\r2\r.\rQ\rQ\r')
    assert 'No map differences in this range.' in text and '9-10/10' in text
    short=next(e for e in entries if e.ident=='MMI012')
    long=replace(short,ident='LONG',psectors=16,sector_ids=tuple(range(1,17)),spt=64,dsm=200)
    files={**original,key('LONG.FDB'):serialize((long,))}
    text=run('unequal-maps','P\rMMI012\r/\rLONG.FDB\rLONG\r2\r.\r>\rQ\rQ\r',files)
    assert text.count('9-16/16')==2 and '16 absent | 16/512' in text,text
    huge=replace(short,ident='BIG',psectors=255,sector_ids=tuple(range(255)),spt=1020,dsm=100)
    files={**original,key('BIG.FDB'):serialize((huge,))}
    text=run('empty-last-255-map','P\r/\rBIG.FDB\rBIG\r/\rBIG.FDB\rBIG\r2\r'+'.\r'*31+'Q\rQ\r',files)
    assert '249-255/255' in text and text.count('No map differences in this range.')==32,text
    # At most 32 echoed chars on a separate line; extra chars cannot act as commands.
    text=run('editable-full-filter','L\r'+'X'*33+'\x08\x7f\rQ\r')
    assert '\x07' in text and 'No matching formats.' in text
    assert 'Invalid filename or ID' not in text
    # Match the displayed DU without ever changing user area; bad names retry locally.
    text=run('copyable-current-du','F\rA0:DISK.FDB\rQ\r')
    assert 'Invalid filename' not in text
    text=run('reject-other-user','F\rA1:DISK.FDB\rA0:DISK.FDB\rQ\r')
    assert text.count('Invalid filename or ID')==1 and m.user==0
    files15={diskkey(1,'DISK.FDB',15):stock,diskkey(1,'FDBVIEW.OVL',15):original[key('FDBVIEW.OVL')]}
    text=run('two-digit-current-du','F\rA15:DISK.FDB\rQ\r',files15,user=15)
    assert 'Invalid filename' not in text and m.user==15
    assert all((de & 255)==255 for fn,de in m.events if fn==32)
    text=run('digit-filename','F\rA1.FDB\rQ\r',{**original,key('A1.FDB'):stock})
    assert 'Invalid filename' not in text
    text=run('untitled-save','N\rS\r\r\x1bQ\r')
    assert text.count('Filename required')==2 and 'displayed default' not in text
    text=run('default-save','S\r\x03Q\r')
    assert 'A0:DISK.FDB\r\nWrite file (Return uses name above)' in text
    # Unknown IDs preserve the comparison's first selection and retry the second.
    text=run('retry-second-source','P\rMMI012\rMISSING\rMMI012\r4\rA\rQ\rQ\r')
    assert 'ID not found; select a source again.' in text and 'Nothing imported' not in text
    assert 'Directory byte offset: 10240 | 10240' in text
    text=run('missing-viewer','D\rQ\r',{key('DISK.FDB'):stock})
    assert 'FDBVIEW.OVL unavailable. Copy the matching FDB pair.' in text
    bad=bytearray(original[key('FDBVIEW.OVL')]);bad[-1]^=1
    text=run('damaged-viewer','D\rQ\r',{**original,key('FDBVIEW.OVL'):bytes(bad)})
    assert 'FDBVIEW.OVL mismatched/damaged' in text
    text=run('pending-state','C\rQ\rQ\rD\r')
    assert 'Editor pending: not yet in catalogue.' in text
    assert 'S Catalogue+write' in text
    text=run('validation-cause','B\r\rMMI012\rG\r1\rV\rQ\rQ\rD\r')
    assert 'Page 3 E DSM / allowed maximum: 394/389' in text
    assert 'Page 3 A SPT / expected: 40/80' in text
    for name,edit,diagnostic in [
        ('block-rule','3\rB\r2\r','Page 3 B-D: BSH=3..7;'),
        ('directory-rule','3\rG\r0\rH\r0\r','Page 3 F-H: AL bitmap'),
        ('numbering-rule','2\rB\r1\r','Page 2: side/track/sector')]:
        text=run(name,'B\r\rMMI012\r'+edit+'V\rQ\rQ\rD\r')
        assert diagnostic in text,(name,text)
    text=run('numeric-retry','B\r\rMMI012\rA\rBOGUS\rA\r80\rQ\rQ\r')
    assert 'Invalid number.' in text and 'Value 0-255' in text and 'Cylinders: 80' in text
    ext={**original,key('OTHER.FDF'):(decompile(stock).encode()+b'\x1a')}
    text=run('text-source-identity','B\rOTHER.FDF\rNOPE\rMMI012\rQ\rQ\r',ext)
    assert 'ID not found' in text and 'OTHER.FDF' in text
    text=run('required-identity','C\rS\rK\rQ\rQ\rD\r')
    assert 'Set I ID and N Name first.' in text
    # Cancellation and rejected A do not change any active binding or reset drives.
    base=entries[0]
    dpb=struct.pack('<HBBBHHBBHH',base.spt,base.bsh,base.blm,base.exm,base.dsm,base.drm,base.al0,base.al1,base.cks,base.off)
    flags=(128 if base.encoding=='MFM' else 0)|(64 if base.sides==2 else 0)
    template=dpb+bytes((base.cylinders,base.psectors,base.secsize.bit_length()-8,flags))+bytes(base.sector_ids).ljust(32,b'\0')+bytes(12)
    m.drives={n:bytes([n])+template for n in (1,2,3)};before=dict(m.drives);m.reset_masks=[]
    text=run('cancel-apply','A\rB\rS\rD\rA\rC\rN\rQ\rQ\rD\r')
    assert m.drives==before and not m.reset_masks
    assert 'Physical 2 SPT current/new' in text and 'Active binding only' in text
    # Pre-existing recovery bytes stay untouched, with actual names reported.
    files={**original,key('DISK.BAK'):b'KEEP THIS BACKUP'}
    text=run('named-recovery','S\r\rY\rQ\r',files)
    assert 'Recovery file already exists.' in text
    assert all(n in text for n in ['A0:DISK.FDB','A0:DISK.BAK','A0:DISK.$$$'])
    report={'status':'PASS','cases':len(cases),'case_names':cases,'max_columns':m.max_console_width,'stack_peak':m.stack_used,'stack_allocation':512,'files_preserved':True,'apply_cancel_preserved_bindings':True}
    (work/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report)


if __name__=='__main__':main()
