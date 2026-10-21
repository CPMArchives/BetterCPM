#!/usr/bin/env python3
"""Execute bounded documentary-card oracles with production BDOS instructions.

The existing foundation supplies declared private disks and BIOS providers.
These are instruction-model witnesses, not physical endpoint observations or
modified independent-suite PASS rows.
"""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import shutil


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('build-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    root = a.build_root.resolve()
    a.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / 'tools'))
    import test_unified_bdos as f
    from system_layout import LAYOUT
    shutil.copy2(__file__, a.output / 'executed-runner.py')
    original = f.Z80
    captured = []

    def capture(*args, **kwargs):
        cpu = original(*args, **kwargs)
        captured.append(cpu)
        return cpu

    f.Z80 = capture
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            f.main()
    finally:
        f.Z80 = original
    assert len(captured) == 1
    cpu = captured[0]
    state = f.symbols()
    emitted = f.IMAGE.read_bytes()
    end = state['UB_OLDSP'] - f.BASE
    cpu.mem[f.BASE:state['UB_OLDSP']] = emitted[:end]
    assert bytes(cpu.mem[f.BASE:state['UB_OLDSP']]) == emitted[:end]
    sp = cpu.sp

    def call(number, value=0):
        cpu.c, cpu.de = number, value
        cpu.run(f.BASE, limit=100000)
        assert cpu.sp == sp, ('stack', number)
        return cpu.a

    # The foundation's final A/B/A fixture has exactly one live file at block 5.
    call(31)
    dpb = cpu.hl
    dsm = cpu.word(dpb + 5)
    call(27)
    alv = cpu.hl
    size = (dsm + 8) // 8
    mask = (cpu.mem[dpb + 9] << 8) | cpu.mem[dpb + 10]
    expected = bytearray(size)
    for block in range(dsm + 1):
        occupied = block == 5 or (block < 16 and bool(mask & (0x8000 >> block)))
        if occupied:
            expected[block // 8] |= 0x80 >> (block & 7)
        assert bool(cpu.mem[alv + block // 8] & (0x80 >> (block & 7))) == occupied, block
    allocation = {'dsm': dsm, 'derived_bytes': size, 'reserved_mask': mask,
                  'live_block': 5, 'observed_hex': bytes(cpu.mem[alv:alv + size]).hex()}
    # Modify only the in-model DPB OFF word, read it through a new public query,
    # then restore and re-query before any disk operation can use the change.
    off = cpu.word(dpb + 13)
    try:
        cpu.setword(dpb + 13, off ^ 1)
        call(31)
        assert cpu.word(cpu.hl + 13) == (off ^ 1)
    finally:
        cpu.setword(dpb + 13, off)
    call(31)
    assert cpu.word(cpu.hl + 13) == off

    # Legal small private DPBs make the two sequential-write failure classes
    # independent: free directory/no data blocks versus free data/no directory.
    saved_memory = bytes(cpu.mem)
    write_failures = {}
    try:
        for kind, dsm_value, expected_status in (('allocation_full',7,2),('directory_full',31,1)):
            cpu.mem[:] = saved_memory
            call(31)
            test_dpb = cpu.hl
            cpu.mem[test_dpb+2:test_dpb+5] = bytes((3,7,0))  # 1K blocks, EXM=0
            cpu.setword(test_dpb+5,dsm_value)
            cpu.setword(test_dpb+7,15)
            cpu.mem[test_dpb+9:test_dpb+11] = bytes((0x80,0))
            cpu.mem[f.FIXTURE:f.FIXTURE+512] = bytes((229,))*512
            entry = bytearray(32)
            entry[1:12] = b'OWNER   DAT'
            entry[15] = 56 if kind == 'allocation_full' else 128
            blocks = range(1,8) if kind == 'allocation_full' else range(1,17)
            for i,block in enumerate(blocks):
                entry[16+i] = block
            cpu.mem[f.FIXTURE:f.FIXTURE+32] = entry
            if kind == 'directory_full':
                for i in range(1,16):
                    dummy = bytearray(32)
                    dummy[1:12] = (f'F{i:07d}'+'DAT').encode()
                    cpu.mem[f.FIXTURE+i*32:f.FIXTURE+(i+1)*32] = dummy
            call(32,0)
            assert call(13) == 0
            cpu.mem[f.FCB:f.FCB+36] = bytes(36)
            cpu.mem[f.FCB+1:f.FCB+12] = b'NEW     DAT' if kind == 'allocation_full' else b'OWNER   DAT'
            assert call(22 if kind == 'allocation_full' else 15,f.FCB) != 255
            if kind == 'directory_full':
                cpu.mem[f.FCB+32] = 128
            call(26,0x9000)
            cpu.mem[0x9000:0x9080] = b'X'*128
            before = bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512])
            fcb_before = bytes(cpu.mem[f.FCB:f.FCB+36])
            status = call(21,f.FCB)
            (a.output / (kind + '.json')).write_text(json.dumps({'kind':kind,'observed_status':status,'expected_status':expected_status,'dsm':dsm_value},indent=2)+'\n')
            assert status == expected_status, (kind,status)
            assert bytes(cpu.mem[f.FCB:f.FCB+36]) == fcb_before, (kind,'FCB changed')
            assert bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512]) == before, kind
            write_failures[kind] = {'status':status,'directory_preserved':True}
    finally:
        cpu.mem[:] = saved_memory

    bios = LAYOUT['BIOS']
    for offset, address, value in ((6,0x9E00,255),(9,0x9E10,65),(21,0x9E20,82)):
        cpu.mem[bios+offset:bios+offset+3] = bytes((0xC3,address & 255,address >> 8))
        cpu.mem[address:address+3] = bytes((0x3E,value,0xC9))
    for offset, address, counter in ((12,0x9E40,0x9FC0),(15,0x9E60,0x9FC2),(18,0x9E80,0x9FC4)):
        cpu.mem[bios+offset:bios+offset+3] = bytes((0xC3,address & 255,address >> 8))
        code = bytes((0x3A,counter & 255,counter >> 8,0x3C,0x32,counter & 255,counter >> 8,
                      0x79,0x32,(counter+1) & 255,(counter+1) >> 8,0xC9))
        cpu.mem[address:address+len(code)] = code
    cpu.mem[state['UB_LISTE']] = 0  # isolate cooked output from optional printer echo
    saved_iobyte = cpu.mem[3]
    for value in (0,0x55,0x95,0xFF):
        call(8,value)
        cpu.mem[0x9FC0:0x9FC6] = bytes(6)
        call(4,0xA5)
        assert bytes(cpu.mem[0x9FC0:0x9FC6]) == bytes((0,0,0,0,1,0xA5)), value
    call(8,saved_iobyte)

    cpu.mem[0x9FC0:0x9FC6] = bytes(6)
    assert call(3) == 82 and cpu.mem[0x9FC0] == 0
    call(5,76)
    assert bytes(cpu.mem[0x9FC0:0x9FC6]) == bytes((0,0,1,76,0,0))
    call(4,80)
    assert bytes(cpu.mem[0x9FC0:0x9FC6]) == bytes((0,0,1,76,1,80))

    # Direct BIOS input is raw; BDOS input echoes. Direct TAB is one raw byte;
    # cooked Function 2 expands it to the next eight-column boundary.
    cpu.mem[0x9FC0:0x9FC6] = bytes(6)
    cpu.run(bios+9)
    assert cpu.a == 65 and cpu.mem[0x9FC0] == 0
    assert call(1) == 65 and bytes(cpu.mem[0x9FC0:0x9FC2]) == bytes((1,65))
    call(2,13)
    cpu.mem[0x9FC0:0x9FC2] = bytes(2)
    cpu.c = 9
    cpu.run(bios+12)
    assert bytes(cpu.mem[0x9FC0:0x9FC2]) == bytes((1,9))
    cpu.mem[0x9FC0:0x9FC2] = bytes(2)
    call(2,9)
    assert bytes(cpu.mem[0x9FC0:0x9FC2]) == bytes((8,32))

    dma_checks = []
    cpu.mem[0x9FA0:0x9FA3] = b'OK$'
    for dma in (0x80,0x9D00):
        call(26,dma)
        cpu.mem[0x80:0x100] = b'\xA5' * 128
        cpu.mem[0x9D00:0x9D80] = b'\x5A' * 128
        for number, value in ((1,0),(2,81),(3,0),(4,83),(5,76),(6,255),
                              (6,90),(7,0),(8,0x95),(9,0x9FA0),(10,0x9F80),(11,0)):
            if number == 10:
                cpu.mem[0x9F80:0x9F84] = bytes((1,0,0,0))
            call(number,value)
            assert cpu.mem[0x80:0x100] == b'\xA5' * 128, (dma,number,'default DMA')
            assert cpu.mem[0x9D00:0x9D80] == b'\x5A' * 128, (dma,number,'alternate DMA')
            dma_checks.append([dma,number,value])
    call(8,saved_iobyte)
    call(26,0x80)
    result = {'status':'PASS', 'cards':['0405','0516','0425','0433','0439','0445','0448','0473','0600','0606','0607'],
              'allocation':allocation, 'sequential_write_failures':write_failures, 'restored_dpb_off':off, 'dma_checks':dma_checks,
              'artifacts':{str(p.relative_to(root)):sha(p) for p in (f.IMAGE,f.BIOS)},
              'foundation_sha256':sha(Path(f.__file__)), 'runner_sha256':sha(Path(__file__)),
              'scope':'Production instruction-model oracles with private DPB/disk fixture and synthetic logical BIOS devices; no physical printer, UART, terminal or native full-system execution claim.'}
    (a.output/'foundation.txt').write_text(log.getvalue())
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS documentary allocation/DPB/character-layer probes',a.output)


if __name__ == '__main__':
    main()
