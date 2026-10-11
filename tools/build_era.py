#!/usr/bin/env python3
"""Build the portable ERA.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/era.mac"
BUILD = ROOT / "build/utilities"


def expanded_source():
    from utility_versions import expand_versions
    common = ROOT / 'src/utilities/common'
    predicate = (common / 'attrselect.inc').read_text(encoding='ascii')
    predicate = predicate[:predicate.index('; Destination modification list:')]
    selector = 'DU_MAP: DS 64\nDU_WORK: DS 12\n' + ''.join(
        (common / name).read_text(encoding='ascii') + '\n'
        for name in ('duselect.inc','filespec.inc','operandqual.inc'))
    selector += predicate + (common / 'rcpselect.inc').read_text(encoding='ascii')
    selector += (common / 'dirmetrics.inc').read_text(encoding='ascii')
    # Reuse the same validated-span FCB encoder as RCP; no independent grammar.
    rcp = (ROOT / 'src/cpx/rcp.mac').read_text(encoding='ascii')
    start = rcp.index('BC_PFCB:')
    end = rcp.index('; ================================================================================', start)
    selector += rcp[start:end] + "\nBC_ALL: DB '*.*'\nBC_INPTR: DW 0\nBC_INLEN: DB 0\nBC_FCBPTR: DW 0\n"
    return expand_versions(SOURCE.read_text(encoding='ascii').replace('; @era-selector@', selector))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = expanded_source()
    text = text.replace("        CSEG\n", "        ASEG\n")
    text = text.replace("        .PHASE  0103H\n",
                        "        ORG     0103H\n")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "ERA.COM"
    with tempfile.TemporaryDirectory(prefix="bettercpm-era-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "era.bin"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{BUILD / 'era.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = raw.read_bytes()
    # This assembler omits the absolute origin from binary output. Reproduce
    # LINK's CP/M entry transfer explicitly; the assembled operands already
    # use their 0103h phased addresses.
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) == 3:
        raise SystemExit("empty ERA output")
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"ERA bytes: {len(data)}")


if __name__ == "__main__":
    main()
