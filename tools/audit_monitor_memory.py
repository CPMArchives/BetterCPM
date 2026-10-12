#!/usr/bin/env python3
"""Assemble isolated monitor-space candidates without publishing system images.

These are audit experiments, not approved production replacements. Public entry
addresses stay fixed; internal addresses and scratch flags can move. Callers and
stack depth must be qualified before any candidate is adopted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"candidate source anchor is not unique: {old[:75]!r}")
    return text.replace(old, new)


def bdos_candidates(text: str, groups: tuple[str, ...]) -> str:
    if "bounds" in groups:
        text = replace_once(text, """        LD      HL,(UB_DSM)
        LD      A,D
        CP      H
        JR      C,UB_AAVAL
        JR      NZ,UB_AABAD
        LD      A,E
        CP      L
        JR      C,UB_AAVAL
        JR      NZ,UB_AABAD""", """        LD      HL,(UB_DSM)
        OR      A
        SBC     HL,DE
        JR      C,UB_AABAD""")
    if "bitmask" in groups:
        start, end = text.index("UB_SETBIT:"), text.index("UB_LOMASK:")
        text = text[:start] + """UB_SETBIT:
        CALL    UA_MASK
        OR      (HL)
        LD      (HL),A
        RET
UB_TESTBIT:
        CALL    UA_MASK
        AND     (HL)
        RET
UA_MASK:
        LD      A,C
        CP      8
        JR      C,UB_BTLOW
        INC     HL
        SUB     8
UB_BTLOW:
        PUSH    BC
        CALL    UB_LOMASK
        POP     BC
        RET

""" + text[end:]
    if "returns" in groups:
        # Only public-operation normal returns use this new return address.
        # UB_BAD, UB_FULL and invalid random decode retain nonlocal exits.
        text = replace_once(text, """        LD      D,(HL)
        PUSH    DE
        PUSH    IX""", """        LD      D,(HL)
        LD      HL,UB_RETA
        PUSH    HL
        PUSH    DE
        PUSH    IX""")
        public_tails = {
            "UB_VERSION", "UB_READER", "UB_OUTOK", "UB_GETIO", "UB_CONST",
            "UB_READY", "UB_DGET", "UB_CONIN", "UB_RESET", "UB_SELECT",
            "UB_CURDSK", "UB_SETDMA", "UB_WRPROT", "UB_PTRBAD", "UB_GETUSR",
            "UB_RSTDRV", "UB_SEARCH", "UB_OPEN", "UB_CLOSE", "UB_MAKE",
            "UB_DDONE", "UB_RNDONE", "UB_ATDONE", "UB_SZDONE", "UB_SETRR",
            "UB_READ", "UB_WRITE", "UB_RRETURN",
        }
        label = ""
        lines = []
        for line in text.splitlines(keepends=True):
            match = re.match(r"(\w+):", line)
            if match:
                label = match[1]
            if label in public_tails:
                line = re.sub(r"\b(?:JP|JR)\s+UB_RETA\b", "RET", line)
            if label == "UB_DIN":
                line = re.sub(r"\bJR\s+Z,UB_RETA\b", "RET     Z", line)
            lines.append(line)
        text = "".join(lines)
    if "finish" in groups:
        start, end = text.index("UB_RNDONE:"), text.index("UB_ATTR:")
        section = text[start:end]
        body = section[:section.index("  ; Function 30")]
        text = replace_once(text, body, "UB_RNDONE:\n        JP      UB_ATDONE\n\n")
    if "divides" in groups:
        # Both sites overwrite B before using it again. Added loop iterations
        # trade instruction count for byte count; do not advertise a speed win.
        old = """        SRL     H
        RR      L
        SRL     H
        RR      L
        SRL     H
        RR      L"""
        if text.count(old) != 2:
            raise ValueError("expected two allocation-vector divide-by-eight sites")
        for name in ("UA_DIV1", "UA_DIV2"):
            text = text.replace(old, f"""        LD      B,3
{name}:
        SRL     H
        RR      L
        DJNZ    {name}""", 1)
    if "position" in groups:
        text = replace_once(text, """        LD      BC,0

UB_POSDIV:                              ; posdiv
        OR      A
        SBC     HL,DE
        JR      C,UB_POSDONE
        INC     BC
        JR      UB_POSDIV""", """        LD      BC,0FFFFH
        OR      A
UB_POSDIV:
        INC     BC
        SBC     HL,DE
        JR      NC,UB_POSDIV""")
    if "names" in groups:
        for prefix, bad, branch in (("UB_MK", "UB_MBAD", "JR"),
                                    ("UB_SZ", "UB_BAD", "JP")):
            old = f"""        LD      B,11

{prefix}NAME:                              ; {'mkname' if prefix == 'UB_MK' else 'szname'}
        LD      A,(HL)
        AND     07FH
        CP      '?'
        {branch}      Z,{bad}
        INC     HL
        DJNZ    {prefix}NAME"""
            text = replace_once(text, old, f"""        CALL    UA_NAME
        {branch}      Z,{bad}""")
        start, end = text.index("UB_RNAMES:"), text.index("        LD      (UB_ITFCB),HL", text.index("UB_RNAMES:"))
        text = text[:start] + """UB_RNAMES:
        PUSH    IX
        POP     HL
        INC     HL
        PUSH    HL
        CALL    UA_NAME
        JP      Z,UB_BAD
        POP     HL
        LD      DE,16
        ADD     HL,DE
        CALL    UA_NAME
        JP      Z,UB_BAD
        PUSH    IX
        POP     HL
        ADD     HL,DE
""" + text[end:]
        # DE is 16 across UA_NAME, so the last ADD reconstructs the target FCB.
        text = replace_once(text, "UB_OLDSP:       DW", """UA_NAME:
        LD      B,11
UA_NLOOP:
        LD      A,(HL)
        AND     07FH
        CP      '?'
        RET     Z
        INC     HL
        DJNZ    UA_NLOOP
        RET

UB_OLDSP:       DW""")
    if "attributes" in groups:
        for label, mask, invert in (("UB_RNCOPY", "07FH", False),
                                    ("UB_ATCOPY", "080H", True)):
            first_mask, second_mask = ("07FH", "080H") if invert else ("080H", "07FH")
            old = f"""{label}:                              ; {'rncopy' if not invert else 'atcopy'}
        LD      A,(HL)
        AND     {first_mask}
        LD      C,A
        LD      A,(DE)
        AND     {second_mask}
        OR      C
        LD      (HL),A
        INC     HL
        INC     DE
        DJNZ    {label}"""
            text = replace_once(text, old, f"""        LD      C,{mask}
        CALL    UA_MERGE""")
        text = replace_once(text, "UA_NAME:", """UA_MERGE:
        LD      A,(DE)
        XOR     (HL)
        AND     C
        XOR     (HL)
        LD      (HL),A
        INC     HL
        INC     DE
        DJNZ    UA_MERGE
        RET

UA_NAME:""")
    return text


def disk_candidates(text: str, groups: tuple[str, ...]) -> str:
    if "geometry" in groups:
        start, end = text.index("        LD B,(IX+18)\n", text.index("DC_CYL:")), text.index("DC_DIVDONE:")
        text = text[:start] + """        LD B,(IX+18)
        LD C,L
        LD A,1
        INC B
DC_QMASK:
        DJNZ DC_QSHIFT
        JR DC_QDONE
DC_QSHIFT:
        ADD A,A
        SRL H
        RR L
        JR DC_QMASK
DC_QDONE:
        DEC A
        AND C
        LD (BIO_QUART),A

""" + text[end:]
    if "length" in groups:
        old = """        LD A,(DC_SIZE)
        OR A
        LD A,1
        JR Z,DC_BSET
        LD A,(DC_SIZE)
        DEC A
        LD B,A
        LD A,1
        JR Z,DC_BSET

DC_BLSH:                                ; derive transfer block count
        ADD A,A
        DJNZ DC_BLSH"""
        text = replace_once(text, old, """        CALL DA_LEN
        LD A,D
        OR A
        JR NZ,DC_BSET
        INC A""")
        old = """        LD DE,128
        LD A,(DC_SIZE)
        OR A
        JR Z,DC_INVERT

DC_INVSH:                               ; scale inversion length
        SLA E
        RL D
        DEC A
        JR NZ,DC_INVSH"""
        text = replace_once(text, old, "        CALL DA_LEN")
        text = replace_once(text, "DC_INFO:                                ; format request descriptor", """DA_LEN:
        LD DE,128
        LD A,(DC_SIZE)
        OR A
        RET Z
DC_INVSH:
        SLA E
        RL D
        DEC A
        JR NZ,DC_INVSH
        RET

DC_INFO:                                ; format request descriptor""")
    return text


def assemble(source: str, name: str, base: int, output: Path, assembler: Path) -> bytes:
    output.mkdir(parents=True, exist_ok=True)
    source = expand_layout(source).replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     "
    ).replace("        .DEPHASE\n", "")
    (output / f"{name}.mac").write_text(source, encoding="ascii")
    for filename, path in (
        ("versions.inc", ROOT / "src/bdos/versions.inc"),
        ("hardware.inc", ROOT / "src/platform/trs80m4/hardware.inc"),
        ("bioslinks.inc", ROOT / "build/system/bioslink.inc"),
    ):
        (output / filename).write_bytes(path.read_bytes())
    binary, listing = output / f"{name}.bin", output / f"{name}.lst"
    subprocess.run([str(assembler), "-fb", f"-o{binary}", f"-l{listing}",
                    f"{name}.mac"], cwd=output, check=True, stdout=subprocess.DEVNULL)
    data = binary.read_bytes()
    if len(data) > base and data[:base] == bytes(base):
        data = data[base:]
        binary.write_bytes(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path("/Users/nathanael/bin/z80asm"))
    parser.add_argument("--output", type=Path, default=ROOT / "build/audit/monitor-efficiency")
    args = parser.parse_args()
    rows = []
    for name, relative, base, transform, groups in (
        ("bdos", "src/bdos/unified.mac", LAYOUT["BDOS"], bdos_candidates,
         ("bounds", "bitmask", "returns", "finish", "divides", "position", "names", "attributes")),
        ("disk", "src/bios/disk.mac", LAYOUT["DISK"], disk_candidates,
         ("geometry", "length")),
    ):
        source = (ROOT / relative).read_text(encoding="ascii")
        baseline = assemble(source, name, base, args.output / f"{name}-baseline", args.assembler)
        reference = ROOT / ("build/bdos/bdos.bin" if name == "bdos" else "build/system/disk.bin")
        if baseline != reference.read_bytes():
            raise ValueError(f"{name} baseline does not reproduce current build")
        previous = len(baseline)
        for index, group in enumerate(groups):
            cumulative = groups[:index + 1]
            data = assemble(transform(source, cumulative), name, base,
                            args.output / f"{name}-{'-'.join(cumulative)}", args.assembler)
            rows.append(dict(component=name, candidate=group, baseline=len(baseline),
                             bytes=len(data), incremental_saving=previous-len(data),
                             total_saving=len(baseline)-len(data),
                             directory=str((args.output / f"{name}-{'-'.join(cumulative)}").resolve())))
            previous = len(data)
    (args.output / "measurements.json").write_text(json.dumps(rows, indent=2) + "\n")
    for row in rows:
        print(f"{row['component']:4} {row['candidate']:8} {row['bytes']:4} bytes; "
              f"save {row['incremental_saving']:2} more, {row['total_saving']:2} total")


if __name__ == "__main__":
    main()
