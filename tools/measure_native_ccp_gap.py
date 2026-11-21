"""Measure the native CCP rebuild boundary without changing runtime artifacts."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def measure(root):
    folder=Path(root)/'build/ccp'
    inner=(folder/'ccp.bin').read_bytes();module=(folder/'ccp.rlm').read_bytes()
    if module[:5]!=b'BCM1\1':
        raise ValueError('native RLMBUILD is a raw-profile path; checked carriers are intentionally unsupported')
    outer_size=int.from_bytes(module[8:10],'little')
    outer_alloc=int.from_bytes(module[10:12],'little')
    outer_relocs=int.from_bytes(module[14:16],'little')
    records=math.ceil(len(inner)/128)
    stride=0x1600
    return {'status':'NATIVE_REBUILD_REVIEW_BOUNDARY',
        'inner_image_bytes':len(inner),'inner_record_bytes':records*128,
        'outer_payload_bytes':outer_size,'outer_allocation':outer_alloc,
        'outer_relocations':outer_relocs,'outer_header_bytes':module[5]*512,
        'raw_module_bytes':len(module),'raw_module_sha256':hashlib.sha256(module).hexdigest(),
        'legacy_input_stride':stride,
        'legacy_inner_slot_overlap_bytes':max(0,records*128-stride),
        'legacy_outer_slot_overlap_bytes':max(0,math.ceil(outer_size/128)*128-stride),
        'legacy_header_plus_outer_bytes':1024+outer_size,
        'fixed_carrier_capacity':6656,
        'current_metadata_sources':{'size':'inner ccp.bin','allocation':'rounded inner ccp.bin','relocations':'outer ccp.rlm'},
        'proposed_prepared_inputs':{'size':outer_size,'allocation':outer_alloc,
            'relocations':outer_relocs,'header_records':module[5]*4,
            'input_stride':6144,'highest_workspace_end':0x8c00},
        'review_required':'Host-prepared packed bootstrap assembly preserves native assembly/module construction, but edited inner CCP source needs host repacking. A fully native packer is additional build-tool work, not implemented here.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT);args=p.parse_args()
    print(json.dumps(measure(args.root),indent=2))


if __name__=='__main__':main()
