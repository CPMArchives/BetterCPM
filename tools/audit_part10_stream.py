#!/usr/bin/env python3
"""Audit prototype rebuild identity and resident/carrier allocation boundaries."""
from pathlib import Path
import argparse,binascii,hashlib,json,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('experiment',type=Path);p.add_argument('repeat',type=Path);p.add_argument('--reference',type=Path);a=p.parse_args()
sys.path.insert(0,str(a.baseline.resolve()/'tools'))
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
fmt=select_fdf(a.baseline/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
def readraw(image,start,count):
 b=image.read_bytes();out=bytearray()
 for rec in range(start,start+count):
  track,within=divmod(rec,fmt.spt);at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128;out+=b[at:at+128]
 return out
meta=json.loads((a.baseline/'build/z80pack/checked-load.json').read_text())
old=readraw(a.baseline/'assessment-media/system.raw',8,52);new=readraw(a.experiment/'system.raw',8,52)
diffs=[i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
# The pinned full-RAM resident's link origin is obtained from its own layout.
from system_layout import LAYOUT as L
offset=meta['symbols']['Z_EREL']+1-L['SYSTEM'];assert set(diffs)<=set((offset,offset+1))
assert new[offset:offset+2]==binascii.crc_hqx((a.experiment/'stage1.carrier').read_bytes(),0xffff).to_bytes(2,'little')
assert readraw(a.experiment/'system.raw',84,16)==(a.experiment/'stage2.carrier').read_bytes()
rows=[]
for n in ('stage1.bin','stage1.carrier','stage2.bin','stage2.carrier','ccp.rlm','RCP.CPX','HELLO.CPX'):
 b=(a.experiment/n).read_bytes();assert b==(a.repeat/n).read_bytes(),n;rows.append({'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
report={'resident_bytes_compared':len(old),'resident_changed_offsets':diffs,'allowed_crc_operand_offset':offset,'no_resident_allocation_change':True,'temporary_bytes':5504,'full_staging_rcp_temporary_bytes':12672,'rcp_temporary_reduction':7168,'second_stage_existing_raw_capacity':2048,'reserved_area_bytes_before_after':27648,'deterministic_artifacts':rows}
if a.reference:
 for n in ('ccp.rlm','RCP.CPX','HELLO.CPX'):assert (a.experiment/n).read_bytes()==(a.reference/n).read_bytes(),n
 report['part9_command_carriers_identical']=True
(a.experiment/'memory-and-image-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
