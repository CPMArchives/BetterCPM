#!/usr/bin/env python3
"""Preserve the BM1 descriptor while publishing a separate PDS2 directory."""
from pathlib import Path
from system_layout import LAYOUT as L
from pds_layout import header, layout
from test_bios import require


def main():
    resident=(Path(__file__).resolve().parents[1]/'build/system/resident.bin').read_bytes()
    at=L['PDS_DESCRIPTOR']-L['SYSTEM']
    require(resident[at:at+3]==b'BM\x01', 'BM1 signature/version changed')
    require(resident[at+3]&5==5, 'PDS/symbolic PATH capabilities absent')
    require(int.from_bytes(resident[at+8:at+10], 'little')==L['HISTORY'], 'default RSX boundary changed')
    plan=layout(header(),L['SYSTEM'])
    require(plan['low']==L['PDS_LOW'] and plan['total']==L['PDS_SIZE']==204, 'default composition differs')
    require(plan['owners']['HISTORY'][1]==192 and L['TPA']==plan['low']-3, 'history/gateway changed')
    require(L['PDS_DIRECTORY']==L['SYSTEM']-12, 'directory discovery changed')
    print('PASS BM1 live-boundary compatibility and separate 204-byte PDS2 default')


if __name__=='__main__':
    main()
