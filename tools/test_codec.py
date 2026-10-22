#!/usr/bin/env python3
"""Assemble the real codec macro and exercise ABI boundary behavior."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/codec"
BASE = 0x100
CONTEXT = 0x8000
ENTRIES = (
    "CX_CHECK_BASE", "CX_CHECK_SIZE", "CX_CHECK_STATE", "CX_CHECK_WRITE",
    "CX_CHECK_REWIND", "CX_CALL_READ", "CX_CALL_WRITE", "CX_CALL_REWIND",
    "CX_READ_ERROR", "CX_WRITE_ERROR", "CX_REWIND_ERROR", "CX_FAIL",
    "CX_RETURN_STATUS", "CX_READY", "CX_DATA", "CX_DONE", "CX_OK", "CX_END",
    "CBPASS", "CBZERO", "CBERROR",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path,
                        default=Path.home() / "bin/z80asm")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="bettercpm-codec-") as directory:
        work = Path(directory)
        for name in ("codec.inc", "codec.mac"):
            shutil.copy2(SOURCE / name, work / name)
        text = "        ORG 100H\n        INCLUDE codec.inc\n        INCLUDE codec.mac\n"
        text += "".join(f"        DW {entry}\n" for entry in ENTRIES)
        text += """        CODEC_CODE
CBPASS: LD BC,1234H
        LD DE,5678H
        LD HL,9ABCH
        RET
CBZERO: XOR A
        SCF
        RET
CBERROR: LD A,0FEH
        SCF
        RET
        END
"""
        (work / "probe.mac").write_text(text, encoding="ascii")

        def assemble(name):
            subprocess.run([str(args.assembler), "-e32", "-fb", f"-o{name}.bin",
                            f"-l{name}.lst", f"{name}.mac"], cwd=work, check=True)
            image = (work / f"{name}.bin").read_bytes()
            if image[:BASE] == bytes(BASE):
                image = image[BASE:]
            return image

        image = assemble("probe")
        # Including either file alone must emit neither code nor storage.
        (work / "defs.mac").write_text(
            "        ORG 100H\n        INCLUDE codec.inc\n"
            "        INCLUDE codec.mac\n        DB 0A5H\n        END\n")
        assert assemble("defs") == bytes([0xA5])
        cpu = Z80(b"")
        cpu.mem[BASE:BASE + len(image)] = image
        symbols = {name: cpu.word(BASE + 2 * i) for i, name in enumerate(ENTRIES)}
        checks = 0

        def fresh(size=1440, address=CONTEXT):
            cpu.ix = address
            cpu.mem[address - 1:address + 17] = bytes([0xA5]) * 18
            cpu.mem[address:address + 16] = bytes(16)
            cpu.mem[address] = 1
            cpu.setword(address + 6, symbols["CBPASS"])
            cpu.setword(address + 14, size)

        def call(name, a=0, e=0, hl=0, carry=False):
            nonlocal checks
            cpu.a, cpu.e, cpu.hl, cpu.carry = a, e, hl, carry
            ix, sp = cpu.ix, cpu.sp
            cpu.run(symbols[name])
            assert (cpu.ix, cpu.sp) == (ix, sp), name
            assert cpu.mem[ix - 1] == cpu.mem[ix + 16] == 0xA5, name
            assert bytes(cpu.mem[BASE:BASE + len(image)]) == image, name
            checks += 1

        def result(status, detail=0, phase=4):
            assert cpu.carry and cpu.a == status
            assert list(cpu.mem[cpu.ix + 2:cpu.ix + 5]) == [phase, status, detail]

        # Size is checked before any prefix writes, including status latching.
        for size in (0, 1, 15):
            fresh(size)
            before = bytes(cpu.mem[CONTEXT:CONTEXT + 16])
            call("CX_CHECK_BASE")
            assert cpu.carry and cpu.a == 11
            assert bytes(cpu.mem[CONTEXT:CONTEXT + 16]) == before

        for size in (16, 255, 256, 1440, 65535):
            fresh(size)
            call("CX_CHECK_BASE")
            assert not cpu.carry and cpu.a == 0
        for offset, value, detail in ((0, 0, 1), (0, 2, 1), (1, 1, 2),
                                      (1, 255, 2), (5, 1, 3)):
            fresh()
            cpu.mem[CONTEXT + offset] = value
            call("CX_CHECK_BASE")
            result(13, detail)
        fresh()
        cpu.setword(CONTEXT + 6, 0)
        call("CX_CHECK_BASE")
        result(13, 4)
        for address in (0x0034, 0x3400):
            fresh()
            cpu.setword(CONTEXT + 6, address)
            call("CX_CHECK_BASE")
            assert not cpu.carry

        for allocated in (16, 255, 256, 1439, 1440, 1441, 65535):
            fresh(allocated)
            call("CX_CHECK_SIZE", hl=1440, carry=True)
            if allocated < 1440:
                result(11)
            else:
                assert not cpu.carry

        for phase in range(5):
            fresh()
            cpu.mem[CONTEXT + 2:CONTEXT + 5] = bytes([phase, 7, 0x9A])
            call("CX_CHECK_STATE", a=2)
            if phase == 2:
                assert not cpu.carry
            elif phase == 4:
                result(7, 0x9A)
            else:
                result(12, phase)

        for helper, offset, status, detail in (
                ("CX_CHECK_WRITE", 8, 13, 5),
                ("CX_CHECK_REWIND", 10, 9, 0)):
            fresh()
            call(helper)
            result(status, detail)
            for address in (0x0034, 0x3400):
                fresh()
                cpu.setword(CONTEXT + offset, address)
                call(helper)
                assert not cpu.carry

        # All byte values and both carry states survive raw tail dispatch.
        # Callbacks deliberately overwrite BC/DE/HL to exercise caller-save ABI.
        for helper, offset in (("CX_CALL_READ", 6), ("CX_CALL_WRITE", 8),
                               ("CX_CALL_REWIND", 10)):
            fresh()
            cpu.setword(CONTEXT + offset, symbols["CBPASS"])
            before = bytes(cpu.mem[CONTEXT:CONTEXT + 16])
            for value in range(256):
                for carry in (False, True):
                    call(helper, a=value, carry=carry)
                    assert cpu.a == value and cpu.carry == carry
                    assert (cpu.bc, cpu.de, cpu.hl) == (0x1234, 0x5678, 0x9ABC)
                    assert bytes(cpu.mem[CONTEXT:CONTEXT + 16]) == before
            for callback, value in (("CBZERO", 0), ("CBERROR", 254)):
                cpu.setword(CONTEXT + offset, symbols[callback])
                call(helper)
                assert cpu.carry and cpu.a == value

        for helper, status in (("CX_READ_ERROR", 7), ("CX_WRITE_ERROR", 8),
                               ("CX_REWIND_ERROR", 10)):
            for reason in (0, 1, 255):
                fresh()
                call(helper, a=reason)
                result(status, reason)
                call("CX_CHECK_STATE", a=2)
                result(status, reason)

        for helper, phase in (("CX_READY", 1), ("CX_DATA", 2), ("CX_DONE", 3)):
            fresh()
            call("CX_FAIL", a=6, e=99)
            result(6, 99)
            call(helper)
            assert not cpu.carry and cpu.a == 0
            assert list(cpu.mem[CONTEXT + 2:CONTEXT + 5]) == [phase, 0, 0]
        fresh()
        call("CX_END")
        result(1, phase=3)
        call("CX_RETURN_STATUS")
        result(1, phase=3)

        # Reinitialization and independent contexts sharing immutable code.
        fresh(address=0x8100)
        call("CX_FAIL", a=8, e=17)
        saved = bytes(cpu.mem[0x8100:0x8110])
        fresh()
        call("CX_CHECK_BASE")
        call("CX_READY")
        assert bytes(cpu.mem[0x8100:0x8110]) == saved
        cpu.ix = 0x8100
        call("CX_CHECK_BASE")
        call("CX_CHECK_SIZE", hl=1440)
        call("CX_READY")
        assert list(cpu.mem[0x8102:0x8105]) == [1, 0, 0]

        # Runner models IX and stack; source audit covers the untouched IY and
        # alternate banks, which this limited runner does not model.
        for line in (SOURCE / "codec.mac").read_text().splitlines():
            code = line.split(";", 1)[0].strip().upper()
            assert not code.startswith(("EX ", "EXX", "DI", "EI")), code
            assert "IY" not in code, code
        print(f"PASS: {checks} assembled codec ABI calls; definitions emit no code.")
        print("IX/stack/canaries/immutable code checked; IY/alternate banks source-audited.")


if __name__ == "__main__":
    main()
