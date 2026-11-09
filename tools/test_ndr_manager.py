#!/usr/bin/env python3
"""Load, move offline and unload NDR through the production RSX manager."""
from pathlib import Path
from test_rsx_disk_cache import setup, L
from test_rsx_stage3 import service_offset

ROOT = Path(__file__).resolve().parents[1]

def main():
    machine = setup()
    carrier = (ROOT/'build/rsx/NDR.RSX').read_bytes()
    machine.files[1,0,'NDR.RSX'] = carrier
    baseline = machine.word(6)
    assert machine.change(1,b'NDR',(1,0)) == 0
    shared_manager = L['HISTORY']-L['RSX']
    assert baseline-machine.word(6) == 512+shared_manager
    assert machine.change(2,b'NDR',(0,0)) == 0
    assert machine.word(6) == baseline
    assert machine.change(1,b'HELLO',(1,0)) == 0
    active_baseline = machine.word(6)
    assert machine.change(1,b'NDR',(1,0)) == 0
    assert active_baseline-machine.word(6) == 512
    def base():
        p = machine.word(L['SYSTEM']+0x84)
        for i in range(machine.mem[L['RSX_STATE']]):
            stem = bytes(machine.mem[L['RSX_STATE']+1+8*i:L['RSX_STATE']+9+8*i]).rstrip()
            if stem == b'NDR': return p
            p = machine.word(p)-8
        raise AssertionError('NDR missing from active profile')
    candidate = (b'COMMANDS'+bytes([1,0])+b'UTILS   '+bytes([2,31])).ljust(320,b'\0')
    machine.mem[0x3600:0x3740] = candidate
    machine.pair('HL',0x3600); machine.reg['A'].value = 3
    assert machine.run(base()+service_offset(carrier)) == 0
    def snapshot():
        machine.pair('HL',0x3800); machine.reg['A'].value = 2
        assert machine.run(base()+service_offset(carrier)) == 0
        return bytes(machine.mem[0x3800:0x3940])
    assert snapshot() == candidate
    del machine.files[1,0,'NDR.RSX']
    assert machine.change(2,b'HELLO',(0,0)) == 0
    assert snapshot() == candidate
    assert machine.change(1,b'HELLO',(1,0)) == 0
    assert snapshot() == candidate
    assert machine.change(2,b'HELLO',(0,0)) == 0
    assert machine.change(2,b'NDR',(0,0)) == 0
    assert machine.word(6) == baseline
    machine.files[1,0,'NDR.RSX'] = carrier
    assert machine.change(1,b'NDR',(1,0)) == 0
    assert not any(snapshot())
    assert machine.change(2,b'NDR',(0,0)) == 0
    assert machine.word(6) == baseline
    print('PASS production NDR load, exact 512-byte charge, offline stateful reconstruction, unload recovery and empty reload')

if __name__ == '__main__': main()
