"""Reversible Model II IMD <-> cpmsim canonical raw adapter; never formats media."""
from argparse import ArgumentParser
from pathlib import Path
from inspect_images import decode,raw_image,repack,PREFIX


def canonical(raw):
    return raw[:3328]+bytes(8192-3328)+raw[3328:]


def historical(raw):
    if raw[3328:8192]!=bytes(8192-3328):
        raise ValueError('canonical boot padding changed')
    return raw[:3328]+raw[8192:]


def inspect(original):
    comment,tracks,errors=decode(original)
    if errors:raise ValueError('ambiguous or unreadable IMD sectors: '+repr(errors))
    sides={77:1,154:2}.get(len(tracks))
    if not sides:raise ValueError('expected 77-cylinder single- or double-sided image')
    if sorted((t['cylinder'],t['head']) for t in tracks)!=[(c,h) for c in range(77) for h in range(sides)]:
        raise ValueError('unexpected cylinder/head coverage')
    for t in tracks:
        expected=(0,128,list(range(1,27))) if t['cylinder']==t['head']==0 else (3,1024,list(range(1,9)))
        if (t['mode'],t['size'],sorted(t['ids']))!=expected:raise ValueError('unsupported recording/sector profile')
    return comment,tracks


def to_raw(original):
    _,tracks=inspect(original)
    return canonical(raw_image(tracks))


def to_imd(original,raw):
    comment,tracks=inspect(original);before=raw_image(tracks)
    if len(raw)!=len(tracks)*8192:raise ValueError('canonical image length changed')
    after=historical(raw)
    if after[:PREFIX]!=before[:PREFIX]:raise ValueError('reserved original bytes changed')
    result=repack(comment,tracks,after)
    _,restored=inspect(result)
    if raw_image(restored)!=after:raise ValueError('IMD read-back mismatch')
    return result


def main():
    p=ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('to-raw');a.add_argument('original',type=Path);a.add_argument('output',type=Path)
    a=sub.add_parser('to-imd');a.add_argument('original',type=Path);a.add_argument('raw',type=Path);a.add_argument('output',type=Path)
    args=p.parse_args()
    try:
        source=args.original.read_bytes()
        result=to_raw(source) if args.mode=='to-raw' else to_imd(source,args.raw.read_bytes())
        with args.output.open('xb') as stream:stream.write(result)
    except (OSError,ValueError,AssertionError,IndexError) as error:p.exit(1,f'Model II adapter: {error}\n')
    print(args.output)
if __name__=='__main__':main()
