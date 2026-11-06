"""Check the reusable adapter against every pinned original and retained guest result."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/engineering/evidence/2026-11-06-model2'
sys.path.insert(0,str(HERE))
from adapt import to_raw,to_imd
from inspect_images import decode,raw_image,digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--images',type=Path,required=True);p.add_argument('--results',type=Path,required=True);a=p.parse_args()
    for spec in json.loads((HERE/'sources.json').read_text())['images']:
        original=(a.images/spec['filename']).read_bytes();assert digest(original)==spec['sha256']
        if spec['filename']=='ATN225BS.IMD':
            try:to_raw(original)
            except ValueError:continue
            raise AssertionError('ambiguous image accepted')
        raw=to_raw(original);roundtrip=to_imd(original,raw)
        assert raw_image(decode(roundtrip)[1])==raw_image(decode(original)[1])
        written=(a.results/Path(spec['filename']).stem/'disks/driveb.dsk').read_bytes()
        assert to_imd(original,written)==(a.results/Path(spec['filename']).stem/'written.imd').read_bytes()
        for offset in (0,3328,8192,16383):
            bad=bytearray(raw);bad[offset]^=1
            try:to_imd(original,bytes(bad))
            except ValueError:pass
            else:raise AssertionError(('accepted changed reserved region',offset))
        try:to_imd(original,raw[:-1])
        except ValueError:pass
        else:raise AssertionError('accepted truncated raw')
    print('PASS five original and guest-written adapter round trips; malformed original, reserved/padding changes and truncation refused')
if __name__=='__main__':main()
