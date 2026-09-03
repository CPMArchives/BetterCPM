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
    DIRBUF="LY_DIR", MODULEBUF="LY_BUF", BIOS="LY_BIOS", CEILING="LY_LIMIT",
    HISTORY="LY_HIST", TPA="LY_TPA", BOOT_SECTORS="LY_SECTS")
LAYOUT = {name: SYMBOLS[symbol] for name, symbol in ALIASES.items()}

def expand_layout(text: str) -> str:
    """Inline the canonical include for host z80asm and native ZSM4."""
    return re.sub(r"^\s*INCLUDE\s+layout\.inc\s*$",
                  lambda _: SOURCE.read_text(encoding="ascii").rstrip(),
                  text, flags=re.MULTILINE | re.IGNORECASE)
