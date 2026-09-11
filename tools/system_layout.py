"""Canonical protected-memory addresses, shared by both assemblers and tests."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/layout.inc"
SYMBOLS = {name: int(value, 16) for name, value in re.findall(
    r"^(LY_\w+)\s+EQU\s+0([0-9A-F]+)H", SOURCE.read_text(), re.MULTILINE)}
ALIASES = dict(SYSTEM="LY_SYS", BDOS="LY_BDOS", FILE="LY_FILE",
    RSX="LY_RSX", EXTENSIONS="LY_EXT", TABLES="LY_TAB", RELOADER="LY_LOAD",
    RSX_STATE="LY_RSTA", STACK_LOW="LY_STKL", STACK_TOP="LY_STKT",
    DIRBUF="LY_DIR", MODULEBUF="LY_BUF", DISK="LY_DISK", BIOS="LY_BIOS", CEILING="LY_LIMIT",
    HISTORY="LY_HIST", TPA="LY_TPA", BOOT_SECTORS="LY_SECTS", CONFIG="LY_CFG", CPX_CONTROL="LY_CPX", RAM_END="LY_RAMEND")
LAYOUT = {name: SYMBOLS[symbol] for name, symbol in ALIASES.items()}
LAYOUT.update(PDS_DESCRIPTOR=LAYOUT["SYSTEM"] + 0x80,
              PDS_TOP=LAYOUT["SYSTEM"], PDS_LOW=LAYOUT["HISTORY"],
              PDS_SIZE=LAYOUT["SYSTEM"] - LAYOUT["HISTORY"])

def expand_layout(text: str) -> str:
    """Inline the canonical include for host z80asm and native ZSM4."""
    text = re.sub(r"^\s*INCLUDE\s+layout\.inc\s*$",
                  lambda _: SOURCE.read_text(encoding="ascii").rstrip(),
                  text, flags=re.MULTILINE | re.IGNORECASE)

    order = (1,3,5,7,9,2,4,6,8,10)
    def table(start, count):
        return "\n".join(f"        DB {n//20},{n//10%2},{order[n%10]}" for n in range(start, start+count))
    return text.replace("; @resident-sector-table@", table(2, LAYOUT["BOOT_SECTORS"])) .replace(
        "; @command-sector-table@", table(8 + LAYOUT["BOOT_SECTORS"], 13)).replace("; @reloader-sector-table@", table(2 + LAYOUT["BOOT_SECTORS"], 2)).replace("; @control-sector-table@", table(4 + LAYOUT["BOOT_SECTORS"], 2)).replace("; @rsx-sector-table@", table(6 + LAYOUT["BOOT_SECTORS"], 2))
