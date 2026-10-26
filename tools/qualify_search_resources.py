#!/usr/bin/env python3
"""Measure compiled SEARCH resource envelopes and directory service growth.

This is a CPU/BDOS-adapter qualification, not a physical stack measurement.
The upper-address sentinel proves the command itself needs no scratch TPA above
its image plus the caller's two-byte return address in these exercised paths.
"""
import hashlib
import json
import re
from collections import Counter
from search_source import ROOT
from test_search_scan import entry, execute


def main():
    image = (ROOT/'build/utilities/SEARCH.COM').read_bytes()
    listing = (ROOT/'build/utilities/search.lst').read_text()
    labels = {name.upper(): int(value, 16) for value, name in
              re.findall(r'^([0-9a-f]{4})\s+.*?\b(\w+):', listing, re.M | re.I)}
    address = lambda name: labels[name.upper()]
    ceiling = 0x100 + len(image) + 2
    a = (0,0,b'ONE     TXT')
    dirs = {(0,0):[entry('ONE.TXT')]}
    data = {a:b'X\r\n'*80+b'\x1a'*16}
    cases = [
        ('help', '/HELP', {}),
        ('invalid', '"" A0:*.TXT', {}),
        ('results', '"X" A0:*.TXT /NOHEX', {}),
        ('paging', '"X" A0:*.TXT /NOHEX /P', {}),
        ('suppression', '"X" A0:*.TXT /NOHEX /P', {'keys':b'\x03'}),
        ('read-error', '"X" A0:*.TXT /NOHEX', {'read_error':(a,1)}),
        ('excerpt-error', '"X" A0:*.TXT /NOHEX', {'render_error':(a,0)}),
        ('open-error', '"X" A0:*.TXT /NOHEX', {'open_error':a}),
        ('close-error', '"X" A0:*.TXT /NOHEX', {'close_error':a}),
        ('directory-error', '"X" A0:*.TXT /NOHEX', {'dir_error':((0,0),0)}),
    ]
    resources = []
    for name, tail, options in cases:
        r = execute(image, address, tail, dirs, data, command=True,
                    entry_sp=ceiling, bdos_stack_bytes=256, **options)
        assert not any(r['c'].mem[ceiling:]), (name, 'upper TPA changed')
        resources.append({'case':name, 'stack_bytes':r['stack_bytes'],
                          'incomplete':r['incomplete']})
    growth = []
    for count in (8,32,64,128):
        names = [f'F{i:07}.TXT' for i in range(count)]
        items = [entry(name) for name in names]
        files = {(0,0,(name[:8]+'TXT').encode()):b'.'*128 for name in names}
        r = execute(image, address, '"X" A0:*.TXT /NOHEX', {(0,0):items}, files,
                    command=True, entry_sp=ceiling)
        assert r['totals'] == [count,0,0,0,0] and not r['incomplete']
        calls = Counter(r['services'])
        growth.append({'entries':count, 'search_first':calls[17],
                       'search_next':calls[18], 'reads':calls[33]})
        print(growth[-1], flush=True)
    report = {'sha256':hashlib.sha256(image).hexdigest(),
              'image_bytes':len(image), 'adapter_tpa_payload_bytes':len(image)+2,
              'simulated_service_stack_bytes':256, 'resources':resources,
              'directory_growth':growth,
              'limits':'Adapter evidence only; no physical BDOS depth, hardware timing, or actual reduced-system TPA claim.'}
    destination = ROOT/'build/search-resource-qualification.json'
    destination.write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(cases)} resource paths; maximum stack {max(x["stack_bytes"] for x in resources)}/512 bytes; {destination}')


if __name__ == '__main__':
    main()
