"""Inspect pinned P&T originals without flattening data beyond sequential EOF."""
from argparse import ArgumentParser
from pathlib import Path
import json,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'2026-11-06-model2'))
from adapt import inspect
from inspect_images import raw_image,read_extents,sequential_files,read_files,digest


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--images',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();records=[]
    for spec in json.loads((HERE/'sources.json').read_text())['images']:
        original=(a.images/spec['filename']).read_bytes()
        assert digest(original)==spec['sha256']
        _,tracks=inspect(original)
        assert len(tracks)==77 and all(t['size']==512 for t in tracks[1:])
        raw=raw_image(tracks)
        extents,used,count=read_extents(raw,299,128,range(1,17),512)
        files=sequential_files(extents)
        dpb=bytes.fromhex('4000040f002b017f00c00020000200')
        positions=[i for i in range(len(raw)) if raw.startswith(dpb,i)]
        assert positions
        extra=[dict(file=n,record=e*128+offset//128,sha256=digest(data[offset:offset+128]))
               for n,parts in extents.items() for e,data in parts.items()
               for offset in range(0,len(data),128) if e*16384+offset>=len(files[n])]
        if extra:
            assert [(r['file'],r['record']) for r in extra]==[('0:menu.com',256)]
            assert len(files['0:menu.com'])==19840
            try:read_files(raw,299,128,range(1,17),512)
            except AssertionError as error:
                assert 'data beyond sequential EOF' in str(error)
            else:raise AssertionError('simple reader silently flattened random extent')
        records.append(dict(filename=spec['filename'],track_count=len(tracks),raw_bytes=len(raw),
            sequential_files={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()},
            file_count=len(files),extent_count=count,free_blocks=300-len(used),final_block_free=299 not in used,
            dpb_hex=dpb.hex(),dpb_raw_offsets=positions,boot_sector_bytes=128,boot_ids=tracks[0]['ids'],
            data_sector_bytes=512,data_sector_orders=sorted({tuple(t['ids']) for t in tracks[1:]}),
            records_beyond_sequential_eof=extra))
    a.output.write_text(json.dumps(records,indent=2)+'\n')
    print('PASS three pinned originals, embedded DPBs, recorded extents and sequential EOF distinction')


if __name__=='__main__':main()
