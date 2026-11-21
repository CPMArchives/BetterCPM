#!/usr/bin/env python3
"""Cost MCL integration against emitted foundation components; no production edits."""
import argparse
import json
from pathlib import Path
import struct

from build_ccp import assemble
from build_z80pack_image import symbols
from pds_layout import header, layout
from system_layout import LAYOUT as L
from test_bios import Z80, SENTINEL

ROOT=Path(__file__).resolve().parents[1]


def measure(out, checked_loader=None):
    out.mkdir(parents=True,exist_ok=True)
    # Reference implementation of the approved immediate cancellation contract.
    # Reuse the production validator rather than assuming unchecked owner bounds.
    text='''        INCLUDE layout.inc
        ASEG
        ORG 02000H
MC_CANCEL:
        CALL PH_VALIDATE
        RET NZ
        LD DE,(LY_PD2+6)
        LD A,D
        OR A
        RET NZ
        LD A,E
        CP 128
        RET NZ
        LD DE,(LY_PD2+4)
        ADD HL,DE
        LD B,128
        XOR A
MC_CLEAR:
        LD (HL),A
        INC HL
        DJNZ MC_CLEAR
        RET
MC_VALIDATORS:
        INCLUDE pds-directory.inc
        END
'''
    data=assemble(Path.home()/'bin/z80asm',text,out/'direct-cancel.bin',out/'direct-cancel.lst',0x2000)
    labels=symbols(out/'direct-cancel.lst')
    cases=0
    for h,m,v in ((2,1,0),(0,1,0),(3,1,3),(2,0,0)):
        for damaged in (False,True):
            cpu=Z80(b'')
            cpu.mem[0x2000:0x2000+len(data)]=data
            directory=bytearray(header(h,m,v))
            plan=layout(directory,L['SYSTEM'])
            cpu.mem[plan['low']:L['SYSTEM']]=b'\xa5'*plan['total']
            if damaged:directory[10]^=1
            cpu.mem[L['SYSTEM']-12:L['SYSTEM']]=directory
            before=bytes(cpu.mem[plan['low']:L['SYSTEM']])
            cpu.sp=0x7000
            cpu.run(0x2000,limit=10000)
            expected=bytearray(before)
            if m and not damaged:
                start,size=plan['owners']['MCL']
                expected[start-plan['low']:start-plan['low']+size]=bytes(size)
            assert bytes(cpu.mem[plan['low']:L['SYSTEM']])==expected
            cases+=1
    # Alternative for review only: latch in an existing byte, then clear MCL
    # after warm reconstruction can safely execute the transient validator.
    latch='''        INCLUDE layout.inc
        ASEG
        ORG 02000H
        LD HL,LY_SYS+095H
        SET 2,(HL)
        JP LY_BIOS+3
        END
'''
    latch_data=assemble(Path.home()/'bin/z80asm',latch,out/'latched-abort.bin',out/'latched-abort.lst',0x2000)
    for flags in range(4):
        cpu=Z80(b'')
        cpu.mem[0x2000:0x2000+len(latch_data)]=latch_data
        cpu.mem[L['SYSTEM']+0x95]=flags
        cpu.mem[L['BIOS']+3:L['BIOS']+6]=bytes((0xc3,SENTINEL&255,SENTINEL>>8))
        cpu.run(0x2000)
        assert cpu.mem[L['SYSTEM']+0x95]==flags|4
    carrier=(ROOT/'build/ccp/ccp.rlm').read_bytes()
    fields=struct.unpack_from('<4sBBHHHHH',carrier)
    result=dict(
        ccp_payload_bytes=fields[4],ccp_allocation_bytes=fields[5],
        ccp_relocations=fields[7],ccp_relocation_capacity=504,
        raw_ccp_carrier_bytes=len(carrier),raw_ccp_carrier_spare=6656-len(carrier),
        checked_ccp_carrier_spare=6656-len(carrier)-22,
        pds_worker_bytes=(ROOT/'build/pds/worker.bin').stat().st_size,
        pds_worker_raw_capacity=2045,pds_worker_checked_budget=1598,
        model4_reloader_bytes=(ROOT/'build/trs80/ccpreload.bin').stat().st_size,
        model4_reloader_capacity=L['RELOADER_CAPACITY'],
        direct_cancel_reference_bytes=len(data),
        direct_cancel_body_bytes=labels['MC_VALIDATORS']-0x2000,
        direct_cancel_owner_canary_cases=cases,
        alternative_latched_abort_bytes=len(latch_data),
        alternative_flag_preservation_cases=4,
        note='Reference costs, not a proof of minimum implementation size. The measurement probe changes no production behavior.')
    if checked_loader:
        checked=json.loads(checked_loader.read_text())
        result['checked_stage1_bytes']=checked['stage1_bytes']
        result['checked_stage2_bytes']=checked['stage2_bytes']
        result['checked_stage1_payload_spare']=932-checked['stage1_bytes']
        result['checked_stage2_payload_spare']=2024-checked['stage2_bytes']
        result['checked_embedded_worker_growth_budget']=(
            result['checked_stage1_payload_spare']+result['checked_stage2_payload_spare'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/review-1.3/mcl-integration')
    parser.add_argument('--checked-loader',type=Path,
                        help='matching checked loader results.json for its carrier-space budget')
    args=parser.parse_args()
    print(json.dumps(measure(args.output.resolve(),args.checked_loader),indent=2))
