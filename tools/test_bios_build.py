#!/usr/bin/env python3
"""Exercise BIOS overflow and stale-resident failures in a disposable tree.

Run after building the system and boot disk. Uses the real assembler.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="bettercpm-bios-build-test-") as name:
        root = Path(name)
        for directory in ("tools", "src", "build", "third_party"):
            shutil.copytree(ROOT / directory, root / directory)
        bios = root / "build/bios/bios.bin"
        resident = root / "build/system/resident.bin"
        disk = root / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"
        originals = {p: p.read_bytes() for p in (bios, resident, disk)}

        def run(tool, expected=None):
            result = subprocess.run([sys.executable, str(root / "tools" / tool)],
                                    capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr
            if expected is None:
                assert result.returncode == 0, output
            else:
                assert result.returncode != 0 and expected in output, output

        source = root / "src/bios/bios.mac"
        original_source = source.read_text()
        padding = LAYOUT["FILE"] - LAYOUT["BIOS"] + 12 - len(originals[bios])
        assert padding > 0
        source.write_text(original_source.replace(
            "        .DEPHASE", f"        DS      {padding}\n        .DEPHASE"))
        for tool in ("build_bios.py", "build_system.py", "build_trs80_boot.py"):
            run(tool, "exceeds by 12 bytes")
            for path, data in originals.items():
                assert path.read_bytes() == data, f"failed build replaced {path}"
        print("PASS: 12-byte overrun rejected by BIOS, system, and disk builds")

        source.write_text(original_source)
        stale = bytearray(originals[resident])
        stale[LAYOUT["BIOS"] - LAYOUT["SYSTEM"]] ^= 1
        resident.write_bytes(stale)
        run("build_trs80_boot.py", "does not contain the current BIOS")
        assert disk.read_bytes() == originals[disk]
        print("PASS: stale resident BIOS rejected without replacing boot disk")

        resident.write_bytes(originals[resident])
        runtime_source = root / "src/bios/disk.mac"
        runtime_original = runtime_source.read_text()
        runtime_source.write_text(runtime_original.replace("DB 5,80,2,0,2,15", "DB 5,80,2,0,3,15"))
        run("build_trs80_boot.py", "does not contain the current disk")
        assert disk.read_bytes() == originals[disk]
        runtime_source.write_text(runtime_original)
        print("PASS: stale runtime disk module rejected without replacing boot disk")
        run("build_system.py")
        run("build_trs80_boot.py")
        for path, data in originals.items():
            assert path.read_bytes() == data, f"rebuild changed {path}"
        print("PASS: rebuilding installs current BIOS and reproduces original disk")


if __name__ == "__main__":
    main()
