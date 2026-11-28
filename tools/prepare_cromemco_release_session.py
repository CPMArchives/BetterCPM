#!/usr/bin/env python3
"""Materialize disposable A/B/C/D mounts from a verified Cromemco collection."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from cromemco_media import image


def prepare(source, output):
    source=source.resolve();output=output.resolve()
    report=json.loads((source/'release/collection.json').read_text())
    output.mkdir(parents=True,exist_ok=False);(output/'disks').mkdir();(output/'disks/disk.map').write_text(''.join(f'drive{d}.dsk\n' for d in 'abcd'))
    by_volume={v['volume']:v for v in report['volumes']}
    for letter,volume in [('a','System'),('c','Utilities-1'),('d','Utilities-2')]:
        row=by_volume[volume];data=(source/'release'/row['image']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        (output/f'disks/drive{letter}.dsk').write_bytes(data)
    (output/'disks/driveb.dsk').write_bytes(image(bytes(20480),[]))
    for name in ('system.conf','candidate.json','bios.bin','bios.lst'):
        shutil.copy2(source/name,output/name)
    shutil.copy2(source/'release/diskdefs',output/'diskdefs')
    shutil.copy2(source/'release/collection.json',output/'collection.json')
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(prepare(a.image_dir,a.output))
