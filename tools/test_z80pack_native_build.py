#!/usr/bin/env python3
"""Run the complete CP/M-native build under z80pack and retain its package."""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import re
import subprocess
from pathlib import Path

from build_ccp import assemble
from build_source_disk import z80pack_logical, extract_files
from build_system_package import compose
from test_z80pack_sysgen_install import digest, session

ROOT = Path(__file__).resolve().parents[1]
BUILD_DISK = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.dsk"
WORK_DISK = ROOT / "build/trs80/BetterCPM-Work-80T-DS-800K.dsk"


def build_binding_program(work: Path) -> Path:
    formats = json.loads((ROOT / "metadata/mm-builtin-formats.json").read_text())[
        "formats"]
    record = next(item for item in formats
                  if item["name"] ==
                  "Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)")
    parameters = record["parameters"]
    dpb = struct.pack("<HBBBHHBBHH", *parameters[:10])
    binding_tail = (dpb +
               bytes((parameters[12], parameters[10], parameters[11],
                      parameters[13])) +
               bytes(record["sector_ids"]).ljust(32, b"\0") + bytes(12))
    assert len(binding_tail) == 63
    requests = []
    for logical, physical in ((1, 1), (2, 2)):
        request = bytes((logical, physical)) + binding_tail + bytes(15)
        requests.append("\n".join(
            "        DB " + ",".join(map(str, request[offset:offset + 16]))
            for offset in range(0, len(request), 16)))
    source = f"""        ASEG
        ORG 100H
        LD SP,4000H
        LD DE,PHYS
        LD B,2
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,PHYS2
        LD B,2
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,REQ1
        LD B,4
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,REQ2
        LD B,4
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,GOOD
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
GOOD:   DB 'B SOURCE AND C WORK DISKS READY',13,10,'$'
FAIL:   DB 'BUILD DISK SETUP FAILED',13,10,'$'
PHYS:   DB 1,5,80,2,0,0,0
PHYS2:  DB 2,5,80,2,0,0,0
REQ1:
{requests[0]}
REQ2:
{requests[1]}
        END
"""
    output = work / "SETBUILD.COM"
    assemble(Path.home() / "bin/z80asm", source, output,
             work / "setbuild.lst", 0x100)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    parser.add_argument("--staged-only", action="store_true",
                        help="stop after individual stages for targeted diagnosis")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    report = ROOT / "build/test-results/z80pack-native-build"
    if report.exists():
        raise SystemExit(f"preserve prior evidence: move {report} before rerunning")
    report.mkdir(parents=True)
    work = report / "runtime"
    work.mkdir()
    shutil.copytree(image / "disks", work / "disks")
    shutil.copy2(image / "diskdefs", work / "diskdefs")
    setup = build_binding_program(work)
    subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                    str(work / "disks/drivea.dsk"), str(setup), "0:"],
                   cwd=work, check=True)
    for letter, source in (("b", BUILD_DISK), ("c", WORK_DISK)):
        target = work / f"disks/drive{letter}.dsk"
        target.unlink()
        shutil.copy2(source, target)
    source_files = extract_files(z80pack_logical(BUILD_DISK.read_bytes()))
    lines = source_files[(0, "BUILD.SUB")].decode("ascii").replace("\r", "").rstrip("\x1a\n").splitlines()
    stages = []
    start = 0
    for last, label in (("B:RESPACK", "resident"),
                        ("B:RLMBUILD", "reload-and-ccp"),
                        ("B:SYSBUILD", "system-package")):
        end = lines.index(last) + 1
        stages.append((label, lines[start:end]))
        start = end
    evidence = {"simulator": str(simulator), "stages": [],
                "build_disk_sha256": digest(BUILD_DISK.read_bytes()),
                "work_disk_sha256": digest(WORK_DISK.read_bytes())}
    for label, commands in stages:
        print(f"native build stage: {label}", flush=True)
        steps = [(b"SETBUILD\r", b"B SOURCE AND C WORK DISKS READY", 30),
                 (b"", b"A0>_ ", 30), (b"C:\r", b"C0>_ ", 30)]
        for line in commands:
            if line != "C:":
                steps.append((line.encode("ascii") + b"\r", b"C0>_ ", 60))
        transcript = session(simulator, work / "disks", steps,
                             report / f"{label}-transcript.txt")
        if any(int(count) for count in re.findall(rb"Errors: +(\d+)", transcript)):
            raise AssertionError(f"native assembler errors in {label}; see {report}")
        marker = {"resident": b"RESIDENT.BIN created (52 records).",
                  "reload-and-ccp": b"CCP.RLM created and verified",
                  "system-package": b"SYSTEM.SYS created and verified"}[label]
        assert marker in transcript, f"{label} did not produce its verified product"
        evidence["stages"].append({"name": label, "commands": commands})
        (report / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    products = extract_files(z80pack_logical((work / "disks/drivec.dsk").read_bytes()))
    package = products[(0, "SYSTEM.SYS")]
    (report / "SYSTEM.SYS").write_bytes(package)
    reference = compose()[0]
    first = next((i for i, (a, b) in enumerate(zip(package, reference)) if a != b), None)
    evidence.update({"system_sys_bytes": len(package),
                     "system_sys_sha256": digest(package),
                     "host_reference_sha256": digest(reference),
                     "first_difference": first})
    (report / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    assert package == reference, f"native SYSTEM.SYS differs at {first}; retained {report}"
    if not args.staged_only:
        print("native build integration: SUBMIT B:BUILD", flush=True)
        transcript = session(simulator, work / "disks", [
            (b"SETBUILD\r", b"A0>_ ", 30),
            (b"SUBMIT B:BUILD\r",
             b"SYSTEM.SYS created and verified (161 records).", 60),
            (b"", b"C0>_ ", 30),
        ], report / "submit-transcript.txt")
        products = extract_files(z80pack_logical((work / "disks/drivec.dsk").read_bytes()))
        submitted = products[(0, "SYSTEM.SYS")]
        (report / "submit-SYSTEM.SYS").write_bytes(submitted)
        assert submitted == reference, "SUBMIT integration package differs from staged build"
        evidence["submit_command"] = "SUBMIT B:BUILD"
        evidence["submit_sha256"] = digest(submitted)
        (report / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("PASS: three native build stages produced verified SYSTEM.SYS")


if __name__ == "__main__":
    main()
