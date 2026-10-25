#!/usr/bin/env python3
"""Build an isolated NOAH ABI/overlay/TPA experiment, never a shipping NOAH.

Uses the unchanged LBR and UNCR libraries with a memory-source adapter. Reserves
the recorded increments 1–2 NOAH image *in addition* to the proof resident. No archive
writer, browser, production CLI dispatch or Utilities Disk packaging is added.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zlib

from qualify_codec_native import native_text
from test_cr import reference
from test_lbr import archive, entry

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT/'tools/noah_proof'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def align(n):
    return (n+127)//128*128


def flatten(source, includes):
    return re.sub(r'(?mi)^\s*INCLUDE\s+(\S+)\s*$',
                  lambda m: includes[m[1]].rstrip(), source)


def assemble(assembler, out, name, source, origin):
    (out/(name+'.mac')).write_text(source)
    subprocess.run([str(assembler), '-e32', '-sn', '-fb', '-o'+name+'.bin',
                    '-l'+name+'.lst', name+'.mac'], cwd=out, check=True,
                   capture_output=True)
    raw = (out/(name+'.bin')).read_bytes()
    # Munk flat binary starts at the first ORG, not at address zero.
    return raw


def native(source):
    source = re.sub(r'(?mi)^\s*ORG\s+(\S+)',
                    r' CSEG\n .PHASE \1', source, count=1)
    source = re.sub(r'(?mi)^\s*END\s*$', ' .DEPHASE\n END', source)
    return native_text(source)


def build(assembler, out):
    out.mkdir(parents=True, exist_ok=True)
    # This isolated experiment reserves a frozen, recorded baseline. Rebasing it
    # onto later writer work would silently change the earlier proof's question.
    # Current production memory is measured by the LBR-write qualification.
    record = ROOT/'docs/engineering/NOAH-Compatibility-Memory-Proof.json'
    baseline = json.loads(record.read_text())['layout']['baseline']
    includes = {p.name: p.read_text() for folder in
                (ROOT/'src/archive', ROOT/'src/codec', PROOF)
                for p in folder.glob('*.inc')}
    for folder in (ROOT/'src/archive', ROOT/'src/codec'):
        includes.update({p.name: p.read_text() for p in folder.glob('*.mac')})
    sizes = {}
    for codec, context in (('sq', 3524), ('usq', 1440), ('cr', 25207), ('uncr', 26582)):
        source = ' ORG 100H\n'+''.join(includes[n]+'\n' for n in
                    ('codec.inc', 'codec.mac', codec+'.inc', codec+'.mac'))
        source += ' CODEC_CODE\n '+codec.upper()+'_CODE\n END\n'
        image = assemble(assembler, out, 'size-'+codec, source, 256)
        sizes[codec] = {'code_bytes_including_common': len(image), 'context_bytes': context}
    data = bytes(range(256))*4
    compressed = reference(data)
    pad = -len(compressed)%128
    fixture = archive([entry(b'PROOF   BZN', records=(len(compressed)+127)//128, pad=pad)],
                      compressed+bytes(pad))
    def db(raw):
        return '\n'.join(' DB '+','.join(str(x) for x in raw[i:i+16])
                         for i in range(0, len(raw), 16))+'\n'
    # Determine proof resident length; layout constants have fixed-width uses.
    includes['generated.inc'] = 'EXPECTED_HEADER:\n'+db(bytes(124))+'FIXTURE:\n'+db(fixture)
    def layout(base, ovl_bytes=256, handler=0, codec=0):
        ac = base+ovl_bytes+1
        cc = ac+138+2
        end = cc+26582+1
        return f'''BASELINE_BYTES EQU {baseline["bytes"]}
OVERLAY EQU {base}
OVL_BYTES EQU {ovl_bytes}
OVL_RECORDS EQU {ovl_bytes//128}
ARCHIVE_CONTEXT EQU {ac}
CODEC_CONTEXT EQU {cc}
PROOF_END EQU {end}
HANDLER_OPEN EQU {handler}
HANDLER_NEXT EQU {handler+3}
HANDLER_READ EQU {handler+6}
CODEC_INIT EQU {codec}
CODEC_HEAD EQU {codec+3}
CODEC_RUN EQU {codec+6}
FIXTURE_BYTES EQU {len(fixture)}
DECODED_BYTES EQU {len(data)}
'''
    includes['layout.inc'] = layout(0x6000)
    raw = assemble(assembler, out, 'layout', flatten((PROOF/'proof.mac').read_text(), includes), 256)
    base = align(256+len(raw))
    hbase = base+128
    hsource = f' ORG {hbase}\n'+includes['archive.inc']+'\n'+includes['lbr.mac']+'''
 JP LBR_OPEN
 JP LBR_NEXT
 JP LBR_READ
 LBR_CODE
 END
'''
    handler = assemble(assembler, out, 'LBRMOD', hsource, hbase)
    cbase = align(hbase+len(handler))
    csource = f' ORG {cbase}\n'+''.join(includes[n]+'\n' for n in
                    ('codec.inc', 'codec.mac', 'uncr.inc', 'uncr.mac'))+'''
 JP UNCR_INIT
 JP UNCR_HEAD
 JP UNCR_RUN
 CODEC_CODE
 UNCR_CODE
 END
'''
    codec = assemble(assembler, out, 'UNCRMOD', csource, cbase)
    ovl_bytes = align(cbase+len(codec))-base
    source_inputs = [ROOT/'tools/build_noah_proof.py', record, *PROOF.glob('*')]
    source_inputs += [ROOT/'src/archive'/n for n in ('archive.inc', 'lbr.mac')]
    source_inputs += [ROOT/'src/codec'/n for n in ('codec.inc','codec.mac','uncr.inc','uncr.mac')]
    hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(source_inputs) if p.is_file()}
    build_id = hashlib.sha256((json.dumps(hashes, sort_keys=True)+baseline['sha256']).encode()).digest()[:8]
    header = bytearray(128)
    struct.pack_into('<4sHH8sIHH', header, 0, b'NHOV', 1, 2, build_id, ovl_bytes, 128, 0)
    for i, (ident, image, address, workspace) in enumerate(
            ((1, handler, hbase, 138), (2, codec, cbase, 26582))):
        struct.pack_into('<HHIHHHH', header, 24+i*16,
                         ident, 1, address-base, len(image), address, address, workspace)
    ovl = bytearray(ovl_bytes)
    ovl[:128] = header
    ovl[hbase-base:hbase-base+len(handler)] = handler
    ovl[cbase-base:cbase-base+len(codec)] = codec
    struct.pack_into('<I', ovl, 124, zlib.crc32(ovl))
    includes['layout.inc'] = layout(base, ovl_bytes, hbase, cbase)
    includes['generated.inc'] = 'EXPECTED_HEADER:\n'+db(header[:124])+'FIXTURE:\n'+db(fixture)
    source = flatten((PROOF/'proof.mac').read_text(), includes)
    image = assemble(assembler, out, 'PROOF', source, 256)
    assert align(256+len(image)) == base
    for name, src in (('PROOF', source), ('LBRMOD', hsource), ('UNCRMOD', csource)):
        (out/(name+'.MAC')).write_bytes(native(src))
    (out/'PROOF.COM').write_bytes(image)
    (out/'NOAH.OVL').write_bytes(ovl)
    ac = base+ovl_bytes+1
    cc = ac+138+2
    end = cc+26582+1
    report = {'scope': 'isolated read/decode feasibility, not production NOAH or writer proof',
              'build_id': build_id.hex(), 'source_sha256': hashes,
              'baseline': {**baseline, 'reservation': 'frozen increments 1–2 image; not current writer memory'},
              'codecs': sizes,
              'ranges_exclusive': {'proof_plus_baseline': [256, 256+len(image)],
                  'overlay_header': [base, hbase], 'lbr_code': [hbase, hbase+len(handler)],
                  'uncr_code': [cbase, cbase+len(codec)],
                  'archive_context': [ac, ac+138], 'codec_context': [cc, cc+26582]},
              'required_ceiling': end, 'required_tpa_bytes': end-256,
              'guard_bytes': 4, 'private_stack_bytes': 512,
              'artifacts': {name: {'bytes':len(payload), 'sha256':sha(payload)}
                  for name, payload in (('PROOF.COM', image), ('NOAH.OVL', ovl),
                                        ('LBRMOD', handler), ('UNCRMOD', codec))}}
    (out/'layout.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'NOAH proof: minimum ceiling {end:04X}; {end-256} TPA bytes; not a production guarantee')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    p.add_argument('--output', type=Path, default=ROOT/'build/noah-proof/cross')
    a = p.parse_args()
    build(a.assembler, a.output)
