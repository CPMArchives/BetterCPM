#!/usr/bin/env python3
"""Build the portable REN.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/ren.mac"
BUILD = ROOT / "build/utilities"


def expanded_source():
    from utility_versions import expand_versions
    common = ROOT / 'src/utilities/common'
    code = 'DU_MAP: DS 64\nDU_WORK: DS 12\n'
    code += ''.join((common / n).read_text(encoding='ascii') + '\n'
                    for n in ('duselect.inc', 'filespec.inc', 'operandqual.inc'))
    attr = (common / 'attrselect.inc').read_text(encoding='ascii')
    code += attr[:attr.index('; Destination modification list:')]
    code += (common / 'rcpselect.inc').read_text(encoding='ascii')
    resident = (ROOT / 'src/cpx/ren-select.inc').read_text(encoding='ascii')
    def adapt(old, new):
        nonlocal resident
        if old not in resident:
            raise ValueError('resident REN adapter anchor changed: ' + old)
        resident = resident.replace(old, new, 1)
    adapt('JR NZ,RF_NEXT\n', 'JR Z,RFT_UNPROTECTED\n        LD A,(R_PMODE)\n        OR A\n        JR NZ,RFT_UNPROTECTED\n        CALL R_PROTECTED\n        JP RF_NEXT\nRFT_UNPROTECTED:\n')
    adapt('JR Z,RF_NEXT                 ; same-name mapping is a no-op',
          'JR NZ,RFT_CHANGED\n        CALL R_SAME\n        JP RF_NEXT\nRFT_CHANGED:')
    adapt('CALL RF_SELECT\n', 'CALL RF_SELECT\n        CALL R_DUSTART\n')
    adapt('JR C,RF_DONE\n', 'JR C,RF_DONE\n        CALL R_SEEN\n        JP C,RF_STEP\n')
    adapt('JP NZ,BC_REXISTS', 'JP NZ,R_COLLISION')
    adapt('RF_RENAME:\n', 'RF_RENAME:\n        CALL R_BEFORE\n        JP C,RF_NEXT\nR_MUTATE:\n        CALL R_DRIVEWR\n        JP C,R_FAILURE\n        CALL R_PREP\n        JP C,R_FAILURE\n')
    adapt('JP Z,RF_FAILED\n        JP RF_NEXT',
          'JP Z,R_FAILURE\n        CALL R_SUCCESS\n        JP RF_NEXT')
    adapt('JP NZ,RF_READONLY', 'JP NZ,R_FAILURE')
    adapt('JP C,RF_READONLY', 'JP C,R_FAILURE')
    adapt('LD A,(RF_ATTR)\n        AND 1\n        JP NZ,R_FAILURE',
          'LD A,(R_PMODE)\n        OR A\n        JR NZ,RFT_POK\n        LD A,(RF_ATTR)\n        AND 1\n        JP NZ,R_FAILURE\nRFT_POK:')
    adapt('LD DE,RF_FILE\n        LD C,23\n        CALL BDOS', 'CALL R_DO')
    code += resident
    era = (ROOT / 'src/cpx/era-resident.inc').read_text(encoding='ascii')
    code += era[era.index('RE_CAPTURE:'):era.index('RE_FAILED:')]
    code += era[era.index('RE_DVALID:'):]
    directory = (ROOT / 'src/cpx/dir-select.inc').read_text(encoding='ascii')
    code += directory[directory.index('RD_FILTER:'):directory.index('RD_PRINTUSER:')]
    rcp = (ROOT / 'src/cpx/rcp.mac').read_text(encoding='ascii')
    start = rcp.index('BC_PFCB:')
    code += rcp[start:rcp.index('; ================================================================================', start)]
    code += rcp[rcp.index('BC_WCMP:'):rcp.index('BC_CSELS:')]
    text = SOURCE.read_text(encoding='ascii').replace('; @ren-selector@', code)
    text = text.replace('; @ren-workflow@', (common / 'renflow.inc').read_text(encoding='ascii'))
    return expand_versions(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = expanded_source()
    text = text.replace("        CSEG\n", "        ASEG\n")
    text = text.replace("        .PHASE  0103H\n", "        ORG     0103H\n")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "REN.COM"
    with tempfile.TemporaryDirectory(prefix="bettercpm-ren-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "ren.bin"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{BUILD / 'ren.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = raw.read_bytes()
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) == 3:
        raise SystemExit("empty REN output")
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"REN bytes: {len(data)}")


if __name__ == "__main__":
    main()
