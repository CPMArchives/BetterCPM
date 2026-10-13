#!/usr/bin/env python3
"""Build the portable TYPE.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/type.mac"
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
    code += resident[resident.index('RF_SELECT:'):resident.index('; Map one concrete name')]
    era = (ROOT / 'src/cpx/era-resident.inc').read_text(encoding='ascii')
    code += era[era.index('RE_CAPTURE:'):era.index('RE_FAILED:')]
    code += era[era.index('RE_DVALID:'):]
    directory = (ROOT / 'src/cpx/dir-select.inc').read_text(encoding='ascii')
    code += directory[directory.index('RD_FILTER:'):directory.index('RD_PRINTUSER:')]
    rcp = (ROOT / 'src/cpx/rcp.mac').read_text(encoding='ascii')
    start = rcp.index('BC_PFCB:')
    code += rcp[start:rcp.index('; ================================================================================', start)]
    code += rcp[rcp.index('BC_WCMP:'):rcp.index('BC_CSELS:')]
    text = SOURCE.read_text(encoding='ascii').replace('; @type-selector@', code)
    text = text.replace('; @type-paging@', (common/'typepage.inc').read_text(encoding='ascii'))
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
    output = BUILD / "TYPE.COM"
    with tempfile.TemporaryDirectory(prefix="bettercpm-type-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "type.bin"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{BUILD / 'type.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = raw.read_bytes()
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) == 3:
        raise SystemExit("empty TYPE output")
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"TYPE bytes: {len(data)}")


if __name__ == "__main__":
    main()
