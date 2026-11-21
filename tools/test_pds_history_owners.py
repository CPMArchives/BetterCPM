#!/usr/bin/env python3
"""Exercise real CCP operand binding and history across composed owner sizes."""
from pds_layout import header, layout
from system_layout import LAYOUT as L
from test_ccp import cpu, call, symbol, BASE


def main():
    for choice in range(4):
        machine=cpu()
        directory=header(choice,1,3)
        plan=layout(directory,L['SYSTEM'])
        low,size=plan['owners']['HISTORY']
        machine.mem[low:L['SYSTEM']-12]=b'\xa5'*(plan['total']-12)
        machine.mem[L['SYSTEM']-12:L['SYSTEM']]=directory
        machine.mem[low:low+size]=bytes(size)
        outside=bytes(machine.mem[low+size:L['SYSTEM']])
        machine.setword(L['SYSTEM']+0x8c,BASE)
        machine.ix=symbol('HF_MAIN')
        machine.hl=symbol('CCP_RAW')
        call(machine,0x1706)             # production worker's CCP binding entry
        assert machine.z
        for text in (b'DIR',b'A'*127):
            machine.mem[symbol('CCP_COUNT')]=len(text)
            at=symbol('CCP_DATA')
            machine.mem[at:at+len(text)]=text
            call(machine,symbol('CCP_HADD'))
        assert bytes(machine.mem[low+size:L['SYSTEM']])==outside, 'history escaped its owner'
        if not size:
            continue
        count=1 if size==128 else 2
        assert bytes(machine.mem[low:low+4])==b'BH\x01'+bytes((count,))
        machine.a=count-1
        call(machine,symbol('CCP_HGET'))
        expected=b'DIR' if size==128 else b'A'*127
        length=machine.mem[symbol('CCP_COUNT')]
        at=symbol('CCP_DATA')
        assert bytes(machine.mem[at:at+length])==expected
    print('PASS CCP binding for Off/128/192/384 HISTORY, maximum-line admission and neighboring MCL/VAR/directory canaries')


if __name__=='__main__':
    main()
