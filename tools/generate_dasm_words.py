#!/usr/bin/env python3
"""Generate the factual ZSM4 opcode/register/operator spelling guard."""
import argparse,hashlib,json,re,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def generate(check=False):
    archive=ROOT/'third_party/zsm4/source.tar.gz'
    with tarfile.open(archive) as tar:
        z=tar.extractfile('zsm4-source/zsm.mac').read().decode('ascii')
        e=tar.extractfile('zsm4-source/eval.mac').read().decode('ascii')
    start=z.index('OPCOD2:')
    pieces=[z[start:z.index('NUMOP8',start)],
            e[e.index('SREGS:'):e.index('EVALNEW:')],
            e[e.index('EXTOPS:'):e.index('OPLPAR',e.index('EXTOPS:'))]]
    words=sorted(set(re.findall(r"\bdb\s+[^,\n]+,'([A-Z_][A-Z0-9_]{0,11})',",'\n'.join(pieces),re.I))|{'I','R','F'})
    metadata={'source':'ZSM4 4.7 pinned opcode/register/condition/operator spelling tables plus architectural I/R/F register tokens',
              'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'words':words}
    manifest=ROOT/'metadata/dasm-zsm4-reserved.json'
    manifest_text=json.dumps(metadata,indent=2)+'\n'
    path=ROOT/'src/utilities/common/zsm4words.inc'
    prefix=path.read_text().split('RW_TABLE:',1)[0]
    generated=prefix+'RW_TABLE:\n'+''.join(f" DB {len(w)},'{w}'\n" for w in words)+' DB 0\n'
    if check:
        assert manifest.read_text()==manifest_text,'reserved-word JSON differs from pinned source'
        assert path.read_text()==generated,'native reserved-word table differs from pinned source'
    else:
        manifest.write_text(manifest_text)
        path.write_text(generated)
    return words

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    print('Verified' if args.check else 'Generated',len(generate(args.check)),'reserved spelling facts')
