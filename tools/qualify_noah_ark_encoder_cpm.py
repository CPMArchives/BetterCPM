#!/usr/bin/env python3
"""Run the ARC method-8 encoder as a native CP/M program on both targets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess

from build_noah import ROOT
from dasm_native import campaign
from noah_overlays import assemble, native_export
from qualify_noah_codecs import probe
from qualify_noah_proof import verify_system
from test_noah_ark_lzw import dynamic_codes, rle


DRIVER = r""" ORG 100H
 JP START
START:
 LD SP,STACK_TOP
 LD E,@BDOSDRIVE@
 LD C,14
 CALL 5
 LD E,0
 LD C,32
 CALL 5
 LD HL,IN_FCB+12
 LD DE,IN_FCB+13
 LD BC,23
 LD (HL),0
 LDIR
 LD HL,OUT_FCB+12
 LD DE,OUT_FCB+13
 LD BC,23
 LD (HL),0
 LDIR
 LD A,1
 LD (FAIL_CODE),A
 LD DE,IN_FCB
 LD C,15
 CALL 5
 CP 255
 JP Z,FAIL
 LD A,2
 LD (FAIL_CODE),A
 LD DE,OUT_FCB
 LD C,22
 CALL 5
 CP 255
 JP Z,FAIL
 LD HL,0
 LD (OUT_COUNT),HL
 LD HL,IN_BUFFER
 LD (IN_PTR),HL
 XOR A
 LD (IN_LEFT),A
 LD HL,OUT_BUFFER
 LD (OUT_PTR),HL
 XOR A
 LD (OUT_USED),A
 LD HL,CTX
 LD (HL),1
 XOR A
 LD HL,CTX+1
 LD DE,CTX+2
 LD BC,14
 LD (HL),A
 LDIR
 LD HL,READ_CB
 LD (CTX+6),HL
 LD HL,WRITE_CB
 LD (CTX+8),HL
 LD HL,CTX
 LD DE,CR_CONTEXT_SIZE
 LD (CTX+14),DE
 LD HL,NAME
 LD DE,CTX+CR_NAME
 LD BC,9
 LDIR
 LD IX,CTX
 LD A,3
 LD (FAIL_CODE),A
 CALL CR_INIT
 JR NC,INIT_OK
 LD (FAIL_STATUS),A
 JP FAIL
INIT_OK:
 LD A,4
 LD (FAIL_CODE),A
 CALL N8_RUN
 JR NC,ENCODE_OK
 LD (FAIL_STATUS),A
 JP FAIL
ENCODE_OK:
 LD A,5
 LD (FAIL_CODE),A
 CALL FLUSH_OUT
 JP C,FAIL
 LD A,6
 LD (FAIL_CODE),A
 LD DE,OUT_FCB
 LD C,16
 CALL 5
 CP 255
 JP Z,FAIL
 LD DE,IN_FCB
 LD C,16
 CALL 5
 CP 255
 JP Z,FAIL
 LD DE,COUNT_TEXT
 LD C,9
 CALL 5
 LD HL,(OUT_COUNT)
 LD A,H
 PUSH HL
 CALL HEX_BYTE
 POP HL
 LD A,L
 CALL HEX_BYTE
 LD DE,CRLF
 LD C,9
 CALL 5
 JP 0

FAIL:
 LD DE,FAIL_TEXT
 LD C,9
 CALL 5
 LD A,(FAIL_CODE)
 CALL HEX_BYTE
 LD A,(FAIL_STATUS)
 CALL HEX_BYTE
 LD A,(CTX+4)
 CALL HEX_BYTE
 LD DE,CRLF
 LD C,9
 CALL 5
 JP 0

; CP/M sequential-record input, exposed as a byte callback.
READ_CB:
 PUSH IX
 PUSH IY
 LD A,(IN_LEFT)
 OR A
 JR NZ,READ_HAVE
 LD DE,IN_BUFFER
 LD C,26
 CALL 5
 LD DE,IN_FCB
 LD C,20
 CALL 5
 OR A
 JR NZ,READ_EOF
 LD A,128
 LD (IN_LEFT),A
 LD HL,IN_BUFFER
 LD (IN_PTR),HL
READ_HAVE:
 LD HL,(IN_PTR)
 LD A,(HL)
 INC HL
 LD (IN_PTR),HL
 LD HL,IN_LEFT
 DEC (HL)
 POP IY
 POP IX
 OR A
 RET
READ_EOF:
 POP IY
 POP IX
 XOR A
 SCF
 RET

; CP/M sequential-record output, buffering bytes written by NCAR8.
WRITE_CB:
 PUSH BC
 PUSH DE
 PUSH HL
 PUSH IX
 PUSH IY
 LD HL,(OUT_PTR)
 LD (HL),A
 INC HL
 LD (OUT_PTR),HL
 LD HL,(OUT_COUNT)
 INC HL
 LD (OUT_COUNT),HL
 LD A,(OUT_USED)
 INC A
 LD (OUT_USED),A
 CP 128
 JR NZ,WRITE_CB_DONE
 CALL WRITE_RECORD
 JR C,WRITE_CB_ERROR
WRITE_CB_DONE:
 POP IY
 POP IX
 POP HL
 POP DE
 POP BC
 OR A
 RET
WRITE_CB_ERROR:
 POP IY
 POP IX
 POP HL
 POP DE
 POP BC
 SCF
 RET

WRITE_RECORD:
 PUSH BC
 PUSH DE
 PUSH HL
 LD DE,OUT_BUFFER
 LD C,26
 CALL 5
 LD DE,OUT_FCB
 LD C,21
 CALL 5
 OR A
 JR NZ,WRITE_BAD
 LD HL,OUT_BUFFER
 LD (OUT_PTR),HL
 XOR A
 LD (OUT_USED),A
 POP HL
 POP DE
 POP BC
 OR A
 RET
WRITE_BAD:
 POP HL
 POP DE
 POP BC
 SCF
 RET

FLUSH_OUT:
 LD A,(OUT_USED)
 OR A
 RET Z
 LD B,A
 LD HL,(OUT_PTR)
FLUSH_PAD:
 LD (HL),26
 INC HL
 DJNZ FLUSH_PAD
 JP WRITE_RECORD

HEX_BYTE:
 PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 CALL HEX_NIBBLE
 POP AF
HEX_NIBBLE:
 AND 15
 ADD A,'0'
 CP '9'+1
 JR C,HEX_DIGIT
 ADD A,7
HEX_DIGIT:
 LD E,A
 LD C,2
 JP 5

COUNT_TEXT: DB 'NOAH ARK ENCODE BYTES: ','$'
FAIL_TEXT: DB 'NOAH ARK ENCODE FAILED',13,10,'$'
CRLF: DB 13,10,'$'
NAME: DB 'TEST.BIN',0
IN_FCB: DB @DRIVE@,'INPUT   ','BIN'
 DS 24
OUT_FCB: DB @DRIVE@,'ENC     ','BIN'
 DS 24
IN_PTR: DW 0
IN_LEFT: DB 0
OUT_PTR: DW 0
OUT_USED: DB 0
OUT_COUNT: DW 0
FAIL_CODE: DB 0
FAIL_STATUS: DB 0
IN_BUFFER: DS 128
OUT_BUFFER: DS 128
CTX: DS CR_CONTEXT_SIZE
STACK: DS 1024
STACK_TOP:
"""


def source(drive: int) -> str:
    pieces = []
    for name in ("codec.inc", "codec.mac", "cr.inc", "cr.mac"):
        pieces.append((ROOT / "src/codec" / name).read_text())
    pieces.append(DRIVER.replace("@DRIVE@", str(drive)).replace("@BDOSDRIVE@", str(drive - 1)))
    pieces.append("        CODEC_CODE\n        CR_CODE\n")
    pieces.append((ROOT / "src/utilities/common/noahark-crencode.inc").read_text())
    pieces.append("\n END\n")
    return "\n".join(pieces)


def input_vector() -> bytes:
    rng = random.Random(80517)
    data = bytearray(rng.randrange(256) for _ in range(20480))
    data[100:700] = b"\x90" * 600
    data[1000:1600] = b"A" * 600
    data[2000:2200] = b"\x1a\x00" * 100
    return bytes(data)


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
    cross_root = a.output / "cross"
    cross_root.mkdir()
    memory_probe = probe(Path.home() / "bin/z80asm", cross_root)
    sample = input_vector()
    expected = b"\x0c" + dynamic_codes(rle(sample), 12)
    tools = {name: (ROOT / "third_party" / folder / name).read_bytes()
             for name, folder in (("ZSM4.COM", "zsm4"), ("LINK.COM", "dri-link"))}
    report = {"scope": "Native CP/M invocation of isolated NCAR8 via BDOS file callbacks",
              "input_bytes": len(sample), "expected_body_bytes": len(expected),
              "expected_body_sha256": hashlib.sha256(expected).hexdigest(),
              "verified_systems": systems, "platforms": {}}
    for platform in a.platforms:
        work = cross_root / platform
        work.mkdir()
        drive = 3 if platform == "z80pack" else 1
        text = source(drive)
        cross, _ = assemble(Path.home() / "bin/z80asm", work, "N8CPM", text)
        (work / "N8CPM.MAC").write_bytes(native_export(text))
        base = a.output / platform
        prefix = ["A:", "RSX LOAD ANSISCRN", "RSX LOAD ANSI", "C:"] if platform == "z80pack" else []
        commands = prefix + ["NCMEM", "B:ZSM4 N8CPM=N8CPM", "B:LINK N8CPM[A]", "N8CPM"]
        log, outputs = campaign(platform,
            {"N8CPM.MAC": (work / "N8CPM.MAC").read_bytes(),
             "NCMEM.COM": memory_probe, "INPUT.BIN": sample},
            commands, base, system=a.system.resolve(), utilities=a.utilities.resolve(),
            extract=("N8CPM.COM", "ENC.BIN"), utility_files=tools, timeout=900)
        assert re.findall(rb"Errors: +([0-9]+)", log) == [b"0"], log[-3000:]
        built = outputs["N8CPM.COM"]
        assert built[:len(cross)] == cross and len(built) == (len(cross) + 127) // 128 * 128
        match = re.search(rb"NOAH ARK ENCODE BYTES: ([0-9A-F]{4})", log)
        assert match and b"NOAH ARK ENCODE FAILED" not in log, log[-3000:]
        count = int(match.group(1), 16)
        body = outputs["ENC.BIN"][:count]
        assert body == expected, (platform, count, len(expected), hashlib.sha256(body).hexdigest())
        ceiling = b"C501" if platform == "z80pack" else b"CA01"
        assert b"NOAH QUAL TPA " + ceiling in log
        report["platforms"][platform] = {
            "status": "PASS", "runtime_ceiling_hex": ceiling.decode(),
            "native_com_sha256": hashlib.sha256(built).hexdigest(),
            "encoded_bytes": count, "encoded_sha256": hashlib.sha256(body).hexdigest(),
            "runtime_console_sha256": hashlib.sha256(log).hexdigest(),
            "execution": f"{platform}/execution.json"}
        print("PASS", platform, "native NCAR8 runtime", count, "encoded bytes", flush=True)
    (a.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
