#!/usr/bin/env python3
"""Qualify the isolated ARC stored-member writer on both CP/M targets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from build_noah import ROOT
from dasm_native import campaign
from noah_overlays import assemble, native_export
from qualify_noah_proof import verify_system
from test_ark import crc16, member


def source(drive: int, payload: bytes) -> str:
    files = ["archive.inc", "ark.inc", "arkwrite.inc"]
    definitions = "\n".join((ROOT / "src/archive" / name).read_text() for name in files)
    payload_lines = "\n".join(" DB " + ",".join(str(x) for x in payload[i:i + 16])
                               for i in range(0, len(payload), 16))
    proof = (ROOT / "tools/ark_writer/proof.mac").read_text()
    proof = proof.replace("@definitions@", definitions)
    proof = proof.replace("@CRC@", str(crc16(payload)))
    proof = proof.replace("@PAYLOAD@", payload_lines)
    proof = proof.replace("OUT_FCB: DB 0,", f"OUT_FCB: DB {drive},")
    code = []
    for filename, macro in (("ark.mac", "ARK_CODE MACRO\n"),
                            ("arkwrite.mac", "ARK_WRITE_CODE MACRO\n")):
        body = (ROOT / "src/archive" / filename).read_text().replace(macro, "", 1)
        body = body.rsplit("        ENDM", 1)[0]
        code.append(body)
    return proof.replace("; @code@", "\n".join(code))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--system", type=Path, required=True)
    p.add_argument("--utilities", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--platforms", nargs="+", choices=("z80pack", "trs80gp"),
                   default=("z80pack", "trs80gp"))
    a = p.parse_args()
    a.output = a.output.resolve()
    a.output.mkdir(parents=True, exist_ok=False)
    systems = verify_system(a.system.resolve(), a.platforms)
    payload = bytes(range(256)) * 2 + b"last bytes"
    expected = member(payload, name=b"STREAM.BIN") + b"\x1a\0"
    padded = expected + b"\x1a" * (640 - len(expected))
    tools = {name: (ROOT / "third_party" / folder / name).read_bytes()
             for name, folder in (("ZSM4.COM", "zsm4"), ("LINK.COM", "dri-link"))}
    report = {"scope": "isolated ARK method-2 member writer under native CP/M",
              "payload_bytes": len(payload), "archive_bytes": len(expected),
              "archive_sha256": hashlib.sha256(expected).hexdigest(),
              "verified_systems": systems, "platforms": {}}
    cross_root = a.output / "cross"
    cross_root.mkdir()
    for platform in a.platforms:
        work = cross_root / platform
        work.mkdir()
        drive = 3 if platform == "z80pack" else 1
        text = source(drive, payload)
        cross, symbols = assemble(Path.home() / "bin/z80asm", work, "ARKWCPM", text)
        (work / "ARKWCPM.MAC").write_bytes(native_export(text))
        prefix = ["A:", "RSX LOAD ANSISCRN", "RSX LOAD ANSI", "C:"] if platform == "z80pack" else []
        log, outputs = campaign(platform,
            {"ARKWCPM.MAC": (work / "ARKWCPM.MAC").read_bytes()},
            prefix + ["B:ZSM4 ARKWCPM=ARKWCPM", "B:LINK ARKWCPM[A]", "ARKWCPM"],
            a.output / platform, system=a.system.resolve(), utilities=a.utilities.resolve(),
            extract=("ARKWCPM.COM", "OUT.ARC"), utility_files=tools, timeout=900)
        assert re.findall(rb"Errors: +([0-9]+)", log) == [b"0"], log[-3000:]
        image = outputs["ARKWCPM.COM"]
        assert image[:len(cross)] == cross
        assert len(image) == (len(cross) + 127) // 128 * 128
        assert b"ARK WRITER PASS" in log and b"ARK WRITER FAIL" not in log, log[-3000:]
        actual = outputs["OUT.ARC"]
        assert actual == padded, (platform, len(actual), hashlib.sha256(actual).hexdigest())
        ceiling = "C501" if platform == "z80pack" else "CA01"
        report["platforms"][platform] = {
            "status": "PASS", "runtime_ceiling_hex": ceiling,
            "image_bytes": len(cross), "required_end_hex": f"{symbols['IMAGE_END']:04X}",
            "native_image_sha256": hashlib.sha256(image).hexdigest(),
            "console_sha256": hashlib.sha256(log).hexdigest(),
            "archive_file_sha256": hashlib.sha256(actual).hexdigest()}
        (a.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print("PASS", platform, "native ARC stored-member writer", flush=True)


if __name__ == "__main__":
    main()
