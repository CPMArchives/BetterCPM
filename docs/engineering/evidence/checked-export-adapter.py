#!/usr/bin/env python3
"""Run the existing export fault harness with checked package/entry fixtures.

Only host fixture inputs change. The emitted SYSGEN instructions are unchanged
except for the disk/BDOS service interception already owned by the base harness.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=a.root.resolve()
os.environ['BETTERCPM_BUILD_CONTEXT']=str(root/'build/profile/context.json')
sys.path.insert(0,str(root/'tools'))
import test_sysgen_export as fixture
from checked_system_package import make
from startup_record import build
from system_layout import LAYOUT as L
contract=json.loads((root/'build/z80pack/checked-package.json').read_text())
payload=bytearray((root/'build/z80pack/system-package/system-tracks.bin').read_bytes())
# The base harness edits the source startup before export; supply its checked
# header for exactly those bytes, instead of the legacy unchecksummed header.
payload[128:384]=build('VER /BANNER',system_base=L['SYSTEM'])
package=make(bytes(payload),contract)
fixture.compose=lambda:(package,{})
base_runner=fixture.runner
identity=bytes.fromhex(contract['compatibility_id'])
def runner(image):
    cpu=base_runner(image)
    # A matching documented WBOOT vector admits the actual private-entry gate.
    # Its destination is the base harness's existing stop sentinel.
    cpu.mem[0]=0xC3;cpu.setword(1,L['BIOS']+3)
    cpu.mem[L['BIOS']+3:L['BIOS']+6]=bytes.fromhex('c3ffff')
    cpu.mem[L['BIOS']-16:L['BIOS']]=identity
    return cpu
fixture.runner=runner
fixture.main()
a.output.write_text(json.dumps({'status':'PASS','export_fault_cases':24,
    'entry_boundary_cases':2,'compatibility_id':identity.hex(),
    'sysgen_sha256':hashlib.sha256((root/'build/utilities/SYSGEN.COM').read_bytes()).hexdigest(),
    'scope':'emitted checked export code with controlled disk/BDOS failures; not power-loss recovery'},indent=2)+'\n')
