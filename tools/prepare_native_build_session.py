#!/usr/bin/env python3
"""Prepare private Model 4 native-build media with a SYSTEM work disk in C:."""
import json
import struct
import sys
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build, verify, RAW_SIZE
from build_source_disk import BUILD_INCLUDES, build_source
from build_trs80_boot import install_files, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE
from system_layout import LAYOUT
from sysgen_image import sysgen_image

ROOT = Path(__file__).resolve().parents[1]


def prepare(out: Path) -> None:
    # Preserve C:'s own DPH pointers; replace only its 64-byte binding with A:'s
    # established SYSTEM geometry, selecting physical drive two.
    raw = extract_raw((out / 'drivea.dmk').read_bytes())
    start = 1024
    size = LAYOUT['BOOT_SECTORS'] * 512
    resident = bytearray(raw[start:start + size])
    info = resident.index(b'BDCF\x05\x04\x04\x40')
    logical = struct.unpack_from('<H', resident, info + 10)[0] - LAYOUT['SYSTEM']
    assert 0 <= logical and logical + 320 <= len(resident)
    binding = bytearray(resident[logical + 16:logical + 80])
    assert struct.unpack_from('<H', binding, 14)[0] == 2
    binding[0] = 2
    resident[logical + 176:logical + 240] = binding
    raw[start:start + size] = resident
    # CONFIG H's reference carrier must describe the same private boot image.
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    found = False
    for offset in range(directory, directory + 4096, 32):
        if raw[offset] == 0 and raw[offset + 1:offset + 12] == b'SYSGEN  DAT':
            raw[offset] = 0xE5
            found = True
    assert found, 'boot image lacks SYSGEN.DAT'
    reference = sysgen_image(bytes(resident), LAYOUT['SYSTEM'],
                             LAYOUT['BOOT_SECTORS'] * 4, 8, 80)
    add_file(raw, 'SYSGEN.DAT', reference)
    (out / 'drivea.dmk').write_bytes(build(bytes(raw)))
    (out / 'drivea.img').write_bytes(raw)

    work = bytearray([0xE5]) * RAW_SIZE
    includes = [(name, build_source((ROOT / relative).read_bytes(), name))
                for name, relative in BUILD_INCLUDES]
    install_files(work, includes)
    (out / 'drivec.dmk').write_bytes(build(bytes(work)))
    (out / 'drivec.img').write_bytes(work)
    for letter in 'ac':
        verify((out / f'drive{letter}.dmk').read_bytes(), require_blank=False)
    manifest = json.loads((out / 'configuration.json').read_text())
    manifest['drives'][1]['format'] = 'MM 80T DS DATA 800K; native source/build kit'
    manifest['drives'][2]['format'] = 'BetterCP/M SYSTEM 780K; native work and install target'
    manifest['native_commands'] = ['B:', 'SUBMIT BUILD', 'B:SYSGEN C:SYSTEM.SYS C:']
    (out / 'configuration.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]).resolve())
