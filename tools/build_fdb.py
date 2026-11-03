#!/usr/bin/env python3
"""Build the native FDB catalogue workbench from specification 209."""
import argparse
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(assembler=Path.home()/'bin/z80asm', destination=ROOT/'build/fdb'):
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/utilities/fdb.mac').read_text()
    source += (ROOT/'src/utilities/disk/fdbsession.inc').read_text()
    # Keep CONFIG's validator as the single source of truth.
    from checked_carriers import selected_contract
    selected_contract(assembler)
    source+='\nFDBVALID:'+(ROOT/'src/utilities/disk/fdbread.inc').read_text().split('FDBVALID:',1)[1]+'\nSTACK: DS 512\nSTACKTOP:\nIMAGEEND:\n END\n'
    with tempfile.TemporaryDirectory(prefix='fdb-build-') as temporary:
        staged=Path(temporary)/'fdb.mac';staged.write_text(source)
        subprocess.run([str(assembler),'-e32','-fb',f'-o{destination.resolve()}/FDB.COM',f'-l{destination.resolve()}/fdb.lst',str(staged)],check=True)
    image=(destination/'FDB.COM').read_bytes()
    if image[:256]==bytes(256):image=image[256:];(destination/'FDB.COM').write_bytes(image)
    if len(image)+0x100>0x3600: raise ValueError('FDB code overlaps catalogue workspace')
    return image
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,default=ROOT/'build/fdb');a=p.parse_args()
    print(f'{len(build(destination=a.output_dir))} bytes')
