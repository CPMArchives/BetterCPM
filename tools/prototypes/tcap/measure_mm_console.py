"""Measure the actual MM 2.31 ADM3A output engine behind the NZ-COM reference.

Read-only historical inputs; extracted source and binaries remain in build/.
The reconstructed 2.32 source identifies boundaries, then every byte is compared
with the original 2.31 disk, allowing its one known insert-line operand change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from build_ccp import assemble
from build_z80pack_image import symbols

IMAGE_SHA = '480cdf5dc504ad437448a27938241c81e45d91bab9c0073db738d11cabfb34aa'
SOURCE_SHA = 'feb519b34d2874e29b62b36d911c15631eca7ca8a35f8a10c1a048869ffdfa6b'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, default=ROOT/'build/nzcom-trs80/downloads/MMCPM231.DSK')
    p.add_argument('--source', type=Path, default=ROOT.parent/'sources/mmcpm232.zip')
    p.add_argument('--output', type=Path, default=ROOT/'build/tcap-console-comparison/verified')
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    disk, archive = a.image.read_bytes(), a.source.read_bytes()
    assert sha(disk) == IMAGE_SHA and sha(archive) == SOURCE_SHA
    with zipfile.ZipFile(a.source) as z:
        source = z.read('mmcpm232/bios.asm').decode('latin1').replace('\r\n', '\n')
    start = source.index('\nconoutcrt:')+1
    end = source.index('\ncursorflag:', start)
    end = source.index('\n', end+1)
    body = source[start:end+1]
    first = source.index('\nclearmem:')+1
    last = source.index('\ninc16hl:', first)
    helpers = source[first:last]
    head = ('        ASEG\n        ORG 0EF48H\noptreg EQU 084H\nsoundport EQU 090H\n'
            'videobase EQU 0F800H\nlastvidline EQU 0FF30H\n'
            'fillmem EQU 0ED33H\nclearmem EQU 0ED28H\n')
    assembled = assemble(Path.home()/'bin/z80asm', head+body+'\nMM_END:\n        END\n',
                         out/'console.bin', out/'console.lst', 0xef48)
    helper_code = assemble(Path.home()/'bin/z80asm',
                          '        ASEG\n        ORG 0ED28H\n'+helpers+'\nMM_END:\n        END\n',
                          out/'helpers.bin', out/'helpers.lst', 0xed28)
    table = symbols(out/'console.lst')
    labels = set(re.findall(r'^([a-z]\w*):', body, re.M))
    calls = set()
    for line in body.splitlines():
        match = re.search(r'\b(?:call|jp)\s+(?:(?:nz|z|nc|c|po|pe|p|m),)?(\w+)\b', line.split(';')[0])
        if match:
            calls.add(match[1])
    assert calls-labels == {'fillmem', 'clearmem'}
    raw = bytearray()
    track_size = int.from_bytes(disk[2:4], 'little')
    for track in range(3):
        block = disk[16+track*track_size:16+(track+1)*track_size]
        for pos in range(0, 128, 2):
            at = int.from_bytes(block[pos:pos+2], 'little') & 0x3fff
            if not at:
                break
            assert block[at] == 254
            size = 128 << block[at+4]
            mark = block.find(b'\xfb', at+7, at+100)
            assert mark >= 0
            raw.extend(block[mark+1:mark+1+size])
    memory = bytearray(65536)
    pages = []
    for signature, low, address in [(bytes.fromhex('3e8ed3843ac8f0cd6cef'), 0x48, 0xef00),
                                   (bytes.fromhex('af1808af18033acbf0ee8032cbf0'), 0x8f, 0xf000),
                                   (bytes.fromhex('626b770b78b1c813edb0c9'), 0x33, 0xed00)]:
        found = raw.find(signature)
        assert found >= 0 and raw.find(signature, found+1) < 0
        offset = found-low
        assert offset % 256 == 0
        memory[address:address+256] = raw[offset:offset+256]
        pages.append({'address':address, 'raw_offset':offset})
    actual = bytes(memory[0xef48:table['MM_END']])
    differences = [(0xef48+i, x, y) for i, (x,y) in enumerate(zip(assembled, actual)) if x != y]
    assert len(actual) == len(assembled) == 423
    assert differences == [(0xf056, 0x81, 0x7f)]
    assert len(helper_code) == 22 and bytes(memory[0xed28:0xed3e]) == helper_code
    # The very next original instruction is the printer-status IN, not display code.
    assert bytes(memory[table['MM_END']:table['MM_END']+2]) == bytes.fromhex('dbf8')
    benchmark = json.loads((ROOT/'docs/engineering/evidence/tcap-zsystem-benchmark/measurement.json').read_text())
    # Use the previously measured original REL closure, with geometry included.
    scenarios = benchmark['scenarios']
    candidates = [v for v in scenarios.values() if v.get('with_full_environment_bytes') == 869]
    assert len(candidates) == 1
    library = candidates[0]['linked_bytes']
    assert library == 613
    qualification_path = ROOT/'docs/engineering/evidence/tcap-public-integration/model4.json'
    qualification = json.loads(qualification_path.read_text())
    assert qualification['status'].startswith('PASS')
    lifecycle = qualification['checks']['installed-lifecycle']
    # The first three boundary readings are unloaded, backend, ADM3A+backend.
    boundaries = [c['boundary'] for c in lifecycle['commands'] if c['command'] == 'BOUND']
    generic_rsx = 1024
    resident = boundaries[0]-boundaries[2]-generic_rsx
    client = lifecycle['consumer_helper']['total_bytes']
    assert resident == 2560 and client == 777
    report = {
        'status':'MEASURED original MM 2.31 output engine and selected VLIB closure',
        'image_sha256':sha(disk), 'boundary_source_archive_sha256':sha(archive),
        'measurement_script_sha256':sha(Path(__file__).read_bytes()),
        'original_pages':pages, 'console_entry':0xef48, 'console_end_exclusive':table['MM_END'],
        'console_code_state_and_table_bytes':len(actual), 'shared_helpers_bytes':len(helper_code),
        'console_total_bytes':len(actual)+len(helper_code), 'console_sha256':sha(actual),
        'helpers_sha256':sha(helper_code), 'source_binary_differences':differences,
        'zsystem':{'environment_including_tcap_bytes':256, 'linked_vlib_with_geometry_bytes':library,
                   'native_console_bytes':445, 'static_total_bytes':256+library+445},
        'bettercpm_adm3a':{'backend_and_personality_allocation_bytes':resident,
                          'application_helper_bytes':client, 'subtotal_bytes':resident+client,
                          'shared_bios_cursor_state_bytes':3, 'static_total_bytes':resident+client+3,
                          'qualification_receipt_sha256':sha(qualification_path.read_bytes())},
        'scope':'Model 4 ADM3A core display path; excludes generic routing/loading, keyboard input, framebuffer, application call sites and stack on both sides',
        'limits':['Not a comparison of every VLIB or SCX feature',
                  'MM console is embedded in the baseline BIOS; BetterCPM backend/personality are unloadable',
                  'Full 256-byte Z-System environment and both shared MM helpers charged conservatively',
                  'BetterCPM includes complete required allocation rounding and descriptors']}
    report['bettercpm_to_zsystem_static_ratio'] = report['bettercpm_adm3a']['static_total_bytes']/report['zsystem']['static_total_bytes']
    (out/'measurement.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
