#!/usr/bin/env python3
"""Check the compiled parser against an existing original SIG/M survey corpus.

--corpus contains sigmvNNN directories with original catalogs and lists.
Archive material is supplied independently; reconstructed -CATALOG.ALL is not
an original-format acceptance fixture. No network access or archive mutation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
from test_bios import Z80
from build_crc import ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', required=True, type=Path)
    a = p.parse_args()
    listing = (ROOT/'build/utilities/crc.lst').read_text()
    symbols = {n:int(next(x[:4] for x in listing.splitlines() if re.search(r'\b'+n+':',x)),16)
               for n in ('PARSELIN','LISTLINE','LISTFORM','LISTPEND','ENAME','EMASK','EVALUES','CATCRC')}
    binary = (ROOT/'build/utilities/CRC.COM').read_bytes()
    samples = sorted(set(a.corpus.glob('sigmv*/CRCKLIST.*')) |
                     set(a.corpus.glob('sigmv*/CRCKFILE.*')) |
                     set(a.corpus.glob('sigmv*/-CATALOG.*')))
    assert samples, 'no original SIG/M samples found'
    report = []
    for path in samples:
        c = Z80(b'')
        c.mem[256:256+len(binary)] = binary
        for n in ('LISTFORM','LISTPEND','CATCRC'):
            c.mem[symbols[n]] = 0
        entries = []
        for lineno, line in enumerate(path.read_bytes().split(b'\x1a')[0].replace(b'\r',b'').split(b'\n'),1):
            line = bytes(x & 127 for x in line).upper()
            if not line.strip() or line.lstrip().startswith(b';'):
                continue
            assert len(line) <= 255, (path, lineno, 'overlong original line')
            at = symbols['LISTLINE']
            c.mem[at:at+256] = bytes(256)
            c.mem[at:at+len(line)] = line
            c.run(symbols['PARSELIN'], limit=200000)
            assert not c.carry, (path, lineno, line)
            if c.a:
                at = symbols['ENAME']
                name = bytes(c.mem[at:at+11]).decode()
                crc = c.word(symbols['EVALUES'])
                entries.append((name, f'{crc:04X}'))
        assert not c.mem[symbols['LISTPEND']], (path, 'unfinished header')
        if path.parent.name == 'sigmv310' and path.name == '-CATALOG.310':
            assert entries == [('ZMD146  LBR','136B'),('ZMDOVL2 LBR','B06D')], entries
        if path.name.startswith(('CRCKLIST','CRCKFILE')):
            assert entries, (path, 'no entries')
        report.append({'path':str(path.relative_to(a.corpus)),
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'entries':len(entries)})
    out = ROOT/'build/crc-development'
    out.mkdir(exist_ok=True)
    (out/'HISTORICAL-CRC-PARSER.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'CRC original SIG/M parser: {len(samples)} files, {sum(x["entries"] for x in report)} entries pass')


if __name__ == '__main__':
    main()
