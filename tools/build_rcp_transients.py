#!/usr/bin/env python3
"""Build transient fallbacks directly from the RCP.CPX command code."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/rcp.mac"
BUILD = ROOT / "build/utilities"
ORIGIN = 0x0100
COMMANDS = {
    "DIR": "BC_DIR",
    "USER": "BC_USER",
    "CLS": "BC_CLR",
    "VER": "BC_VER",
    "COPY": "BC_COPY",
    "MOVE": "BC_MOVE",
}


def symbol(listing: Path, name: str) -> int:
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:\s*(?:;.*)?$",
                         listing.read_text(encoding="ascii"),
                         re.MULTILINE | re.IGNORECASE)
    if not matches:
        raise SystemExit(f"RCP transient listing lacks {name}")
    return int(matches[-1], 16)


def transient(image: bytes, entry: int) -> bytes:
    # CP/M supplies a blank-prefixed command tail. Strip its leading spaces,
    # call the very same routine used by RCP.CPX, then warm boot. Keeping the
    # complete command body is intentionally a first parity implementation;
    # later dead-code removal may reduce the files without changing behavior.
    prefix = bytes((
        0x21, 0x81, 0x00,       # LD HL,0081h
        0x3A, 0x80, 0x00,       # LD A,(0080h)
        0x47,                   # LD B,A
        0x78, 0xB7, 0x28, 0x09, # skip: LD A,B / OR A / JR Z,ready
        0x7E, 0xFE, 0x20,       # LD A,(HL) / CP ' '
        0x20, 0x04,             # JR NZ,ready
        0x23, 0x05, 0x18, 0xF3, # INC HL / DEC B / JR skip
        0xCD, entry & 0xFF, entry >> 8,
        0x0E, 0x00,             # LD C,0
        0xC3, 0x05, 0x00,       # JP 0005h
    ))
    result = bytearray(image)
    result[:len(prefix)] = prefix
    return bytes(result)


def copy_source(text: str) -> str:
    """Replace only the transient COPY wildcard driver; keep CPX untouched."""
    start = text.index("BC_WSTART:")
    end = text.index("BC_WCMP:", start)
    batch = (SOURCE.parent / "copy-batch.inc").read_text(encoding="ascii")
    text = text[:start] + batch + text[end:]
    # Only the transient accepts destination wildcards. Validation still owns
    # their legality; the batch driver owns concrete-name mapping and safety.
    old = "        JR      NZ,BC_CVBAD\n        LD      A,(BC_MVFLAG)"
    assert text.count(old) == 1, "COPY wildcard hook changed"
    text = text.replace(old, "        JP      NZ,CTDWILD\n        LD      A,(BC_MVFLAG)", 1)
    start = text.index("BC_COPNAME:")
    end = text.index("BC_COPDONE:", start)
    text = text[:start] + "BC_COPNAME:\n" + text[end:]
    old = "        LD      A,(BC_CWILD)\n        OR      A\n        JP      NZ,BC_WSTART"
    assert text.count(old) == 1, "COPY batch entry changed"
    text = text.replace(old, "        JP      BC_WSTART", 1)
    text = re.sub(r"(?m)^(\s*)JR(\s+(?:(?:NZ|Z|NC|C),)?BC_CV\w+)", r"\1JP\2", text)
    start = text.index("BC_COPT:")
    end = text.index("BC_CVALID:", start)
    options = (SOURCE.parent / "copy-options.inc").read_text(encoding="ascii")
    text = text[:start] + options + text[end:]
    old = "        JR      Z,BC_CMAKE\n        LD      A,(BC_OVER)"
    assert text.count(old) == 1, "COPY destination-open hook changed"
    text = text.replace(old, "        JP      Z,BC_CMAKE\n        JP      CTEXIST\nCTALLOW:\n        LD      A,(BC_OVER)", 1)
    text = text.replace("destination=source [/O]", "destination=source [/O|/S] [/B] [/V]", 1)
    old = "        JP      Z,BC_CEXIST\n        LD      A,(BC_NEWFCB+9)"
    assert text.count(old) == 1, "COPY one-file overwrite entry changed"
    text = text.replace(old, "        JP      Z,BC_CEXIST\nCTYALLOW:\n        LD      A,(BC_NEWFCB+9)", 1)
    old = "        JR      Z,BCCLERR\n  ; Apply attributes"
    assert text.count(old) == 1, "COPY close verification hook changed"
    text = text.replace(old, "        JP      Z,BCCLERR\n        JP      CTVPOST\nCTVATTR:\n  ; Apply attributes", 1)
    old = "        CALL    BC_COPT\n        JP      C,BC_CSYNT\n        LD      A,B"
    assert text.count(old) == 1, "COPY option cursor hook changed"
    text = text.replace(old, "        CALL    BC_COPT\n        JP      C,BC_CSYNT\n        LD      (BC_CBASE),HL\n        LD      A,B", 1)
    old = "BC_CLOOP:                               ; cloop\n        CALL    BC_CSELS"
    assert text.count(old) == 1, "COPY transfer polling hook changed"
    text = text.replace(old, "BC_CLOOP:                               ; cloop\n        CALL    CTCHECK\n        JP      C,CTCANCEL\n        CALL    BC_CSELS", 1)
    for fcb in ("BC_FCB", "BC_NEWFCB"):
        old = "        LD      B,A\n        LD      DE," + fcb + "\n        CALL    BC_COPAR"
        assert text.count(old) == 1, "COPY operand trim hook changed"
        text = text.replace(old, "        LD      B,A\n        CALL    CTTRIM\n        JP      C,BC_CSYNT\n        LD      DE," + fcb + "\n        CALL    BC_COPAR", 1)
    # Shared set parser is linked only into COPY.COM, never into RCP/MOVE.
    start = text.index("BC_CPARSE:")
    end = text.index("BC_CSOK:", start)
    part = text[start:end].replace("CALL    BC_COPAR", "CALL    CTSCOPE", 1)
    text = text[:start] + part + text[end:]
    start = text.index("BC_CSOK:")
    end = text.index("BC_CDOK:", start)
    part = text[start:end].replace("CALL    BC_COPAR", "CALL    CTDSCOPE", 1)
    text = text[:start] + part + text[end:]
    old = "        DJNZ    BC_CATTR\n        LD      DE,BC_NEWFCB"
    assert text.count(old) == 1, "COPY destination attributes hook changed"
    text = text.replace(old, "        DJNZ    BC_CATTR\n        CALL    CTDATTR\n        LD      DE,BC_NEWFCB", 1)
    old = "        OR      A\n        JR      NZ,BCCLERR\n        XOR     A\n        LD      (BC_CMADE),A"
    assert text.count(old) == 1, "COPY metadata completion hook changed"
    text = text.replace(old, "        OR      A\n        JP      NZ,CTBMFAIL\n        XOR     A\n        LD      (BC_CMADE),A\n        CALL    CTBPOST\n        JP      C,BC_COK\n        CALL    CTR_OK", 1)
    start = text.index("BC_CFAIL:")
    end = text.index("BC_CPRINT:", start)
    text = text[:start] + (SOURCE.parent / "copy-error.inc").read_text(encoding="ascii") + text[end:]
    old = "        LD      DE,BC_NOSPACE\n        JP      BC_CFAIL\n\nBC_CCLOSE:"
    assert text.count(old) == 1, "COPY write status hook changed"
    text = text.replace(old, "        CP      2\n        LD      DE,BC_NOSPACE\n        JP      Z,BC_CFAIL\n        LD      DE,BC_WRITEERR\n        JP      BC_CFAIL\n\nBC_CCLOSE:", 1)
    old = "BC_CNOFILE:                             ; cnofile\n        LD      DE,BC_NOFILE\n        JR      BC_CPRINT"
    assert text.count(old) == 1, "COPY source-open failure hook changed"
    text = text.replace(old, "BC_CNOFILE:                             ; cnofile\n        LD      DE,BC_NOFILE\n        JP      BC_CFAIL", 1)
    text = re.sub(r"(?m)^(\s*)JR(\s+(?:(?:NZ|Z|NC|C),)?BC_C(?:PRINT|OK))", r"\1JP\2", text)
    scope = (SOURCE.parent / "copy-scope.inc").read_text(encoding="ascii")
    scope += (SOURCE.parent / "copy-report.inc").read_text(encoding="ascii")
    scope += (SOURCE.parent / "copy-backup.inc").read_text(encoding="ascii")
    scope += (SOURCE.parent / "copy-dest.inc").read_text(encoding="ascii")
    scope += (SOURCE.parent / "copy-verify.inc").read_text(encoding="ascii")
    scope += (SOURCE.parent / "copy-rename.inc").read_text(encoding="ascii")
    scope += (ROOT / "src/utilities/common/attrselect.inc").read_text(encoding="ascii")
    scope += (ROOT / "src/utilities/common/operandqual.inc").read_text(encoding="ascii")
    scope += (ROOT / "src/utilities/common/duselect.inc").read_text(encoding="ascii")
    state = """
CT_BATCH: DB 0
CT_CHOICE: DB 0
CT_LINE: DS 48
CT_ASKM: DB ' [Destination exists. Overwrite? Y/N/O/S/R/?] $'
CT_HELPM: DB 'Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename',13,10,'$'
CT_ABORTM: DB 13,10,'COPY ABORTED',13,10,'$'
CT_SKIP: DB 0
CT_SKIPS: DB 0
CT_FAILS: DB 0
CT_SKIPM: DB 13,10,'SKIPPED',13,10,'$'
CT_COUNT: DB 0
CT_LEFT: DB 0
CT_END: DW 0
CT_CURSOR: DW 0
CT_FULLMSG: DB 13,10,'COPY BATCH TOO LARGE',13,10,'$'
CT_NAMES: DS 64*11
CT_TARGETS: DS 64*11
CT_PATTERN: DS 11
CT_DCUR: DW 0
CTGPTR: DW 0
CTCKPTR: DW 0
CT_DONE: DB 0
CTSCAN: DB 0
CT_MAPMSG: DB 13,10,'COPY DESTINATION CONFLICT',13,10,'$'
CT_NAMEMSG: DB 13,10,'INVALID DESTINATION NAME',13,10,'$'
"""
    marker = "        .DEPHASE" if "        .DEPHASE" in text else "        END\n"
    return text.replace(marker, scope + state + marker, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii")
    text = text.replace('; @rcp-shared-selector@', '')
    text = text.replace("CPXBASE         EQU     08000H",
                        "CPXBASE         EQU     00100H")
    text = text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ").replace(
                            "        .DEPHASE\n", "")
    listing = BUILD / "rcp-transient.lst"
    base = assemble(args.assembler, text, BUILD / "rcp-transient.bin",
                    listing, ORIGIN)
    for command, entry_name in COMMANDS.items():
        command_base, command_listing = base, listing
        if command == "COPY":
            copy_text = copy_source(text)
            command_listing = BUILD / "copy-transient.lst"
            command_base = assemble(args.assembler, copy_text,
                                    BUILD / "copy-transient.bin", command_listing, ORIGIN)
        data = transient(command_base, symbol(command_listing, entry_name))
        output = BUILD / f"{command}.COM"
        output.write_bytes(data)
        print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
        print(f"{command} transient bytes: {len(data)}")


if __name__ == "__main__":
    main()
