#!/usr/bin/env python3
"""Verify pinned compatibility references and inventory independent ARC fixtures.

Research tool only, not an ARC handler. --fetch writes an ignored cache; no
third-party code or historical binary is added to the distribution. Optional
Deark extraction records independent output hashes and checksum diagnostics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import urllib.request

from test_usq import squeeze

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT/'tests/fixtures/noah/references.json'


def vectors():
    """Independent host fixtures, then checked with the pinned external decoder."""
    data = bytes(range(256))+b'\0\x1a\xff'
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xa001 if crc & 1 else 0)
    sq = squeeze(data, name=b'ORACLE.BIN')
    tree = sq.index(0,4)+1
    bodies = {1:data,2:data,3:data.replace(b'\x90',b'\x90\0'),4:sq[tree:]}
    result = {}
    for method, body in bodies.items():
        header = bytes([26,method])+b'ORACLE.BIN'.ljust(13,b'\0')
        header += struct.pack('<IHHH',len(body),0,0,crc)
        if method != 1:
            header += struct.pack('<I',len(data))
        result[f'generated-method-{method}.arc'] = header+body+b'\x1a\0'
    return data, result


def inventory(raw):
    at, members = 0, []
    while True:
        assert at+2 <= len(raw) and raw[at] == 26, ('bad header',at)
        method = raw[at+1]
        if not method:
            return {'members':members,'end_offset':at+2,
                    'physical_bytes':len(raw),'trailing_bytes':len(raw)-at-2}
        assert 1 <= method <= 9
        size = 25 if method == 1 else 29
        assert at+size <= len(raw)
        name = raw[at+2:at+15].split(b'\0',1)[0].decode('ascii')
        stored = struct.unpack_from('<I',raw,at+15)[0]
        logical = stored if method == 1 else struct.unpack_from('<I',raw,at+25)[0]
        end = at+size+stored
        assert end <= len(raw)
        members.append({'name':name,'method':method,'header_offset':at,
                        'stored_bytes':stored,'decoded_bytes':logical,
                        'crc16':f'{struct.unpack_from("<H",raw,at+23)[0]:04x}'})
        at = end


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=ROOT/'build/noah-proof/references')
    p.add_argument('--fetch',action='store_true')
    p.add_argument('--oracle-deark',type=Path)
    p.add_argument('--generate-vectors',action='store_true',
                   help='Generate old/new stored, packed and squeezed fixtures')
    p.add_argument('--output',type=Path,default=ROOT/'build/noah-proof/compatibility.json')
    a = p.parse_args()
    a.cache = a.cache.resolve(); a.cache.mkdir(parents=True,exist_ok=True)
    refs = json.loads(PINS.read_text())['artifacts']
    checked, fixtures = {}, {}
    samples = {}
    for name, ref in refs.items():
        path = a.cache/name
        if not path.exists() and a.fetch:
            raw = urllib.request.urlopen(ref['url'],timeout=30).read()
            assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'], name
            path.write_bytes(raw)
        raw = path.read_bytes()
        assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'], name
        checked[name] = ref
        if name.endswith('.arc'):
            samples[name] = raw
    source_bytes, generated = vectors()
    if a.generate_vectors:
        samples.update(generated)
        for name, raw in generated.items():
            (a.cache/name).write_bytes(raw)
    for name, raw in samples.items():
        path = a.cache/name
        fixtures[name] = inventory(raw)
        fixtures[name]['sha256'] = hashlib.sha256(raw).hexdigest()
        if a.oracle_deark:
            out = a.cache/('decoded-'+name)
            out.mkdir(exist_ok=True)
            assert not list(out.iterdir()), 'use a fresh oracle output directory'
            result = subprocess.run([str(a.oracle_deark.resolve()),'-m','arc','-d',
                                     '-od',str(out),str(path)],capture_output=True,check=True)
            log = result.stdout+result.stderr
            assert b'Error' not in log and b'CRC mismatch' not in log, log
            reported = re.findall(rb'crc \(reported\): 0x([0-9a-f]+)',log)
            calculated = re.findall(rb'crc \(calculated\): 0x([0-9a-f]+)',log)
            assert reported == calculated and len(reported)==len(fixtures[name]['members'])
            (a.cache/(name+'.deark.log')).write_bytes(log)
            decoded = {x.name:{'bytes':x.stat().st_size,
                      'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}
                       for x in sorted(out.iterdir()) if x.is_file()}
            expected = fixtures[name]['members']
            assert len(decoded)==len(expected)
            assert sorted(x['bytes'] for x in decoded.values())==sorted(x['decoded_bytes'] for x in expected)
            if name in generated:
                assert len(decoded)==1
                assert next(iter(out.iterdir())).read_bytes()==source_bytes
            fixtures[name]['independent_decoded_outputs'] = decoded
            fixtures[name]['oracle_log_sha256'] = hashlib.sha256(log).hexdigest()
    report = {'scope':'reference and historical fixture inventory; not NOAH conformance',
              'pins_sha256':hashlib.sha256(PINS.read_bytes()).hexdigest(),
              'references':checked,'historical_arc_fixtures':fixtures}
    if a.oracle_deark:
        report['deark_executable_sha256'] = hashlib.sha256(a.oracle_deark.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: pinned references and historical fixture inventory',flush=True)


if __name__ == '__main__':
    main()
