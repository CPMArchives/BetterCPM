#!/usr/bin/env python3
"""Exercise the shared VER entry with exact banner and invalid option tails."""
from pathlib import Path
from test_utility_versions import runner, output, address
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "\r\n" + "\r\n".join([
    "------------------------------",
    "        BetterCP/M 0.3",
    "An enhanced CP/M-compatible OS",
    "             ----",
    "Type TYPE README.TXT for more",
    "------------------------------",
]) + "\r\n"
def main():
    image = (ROOT / "build/utilities/VER.COM").read_bytes()
    listing = (ROOT / "build/utilities/rcp-transient.lst").read_text()
    for tail in ["/BANNER", "", "/BANNER X", "/BANN", "/BANNER /V"]:
        c = runner(image)
        data = tail.encode()
        c.mem[0x6000:0x6000 + len(data)] = data
        c.hl = 0x6000
        c.b = len(data)
        c.run(address(listing, "BC_VER"), limit=100000)
        expected = EXPECTED if tail == "/BANNER" else (
            "\r\nBetterCP/M 0.3\r\n" if not tail else "\r\n?\r\n")
        assert output(c) == expected, (tail, repr(output(c)))
    resident = (ROOT / "build/cpx/rcp.bin").read_bytes()
    listing = (ROOT / "build/cpx/rcp.lst").read_text()
    c = runner(resident, 0x8000)
    tail = b"VER /BANNER"
    c.mem[0x6000:0x6000 + len(tail)] = tail
    c.de = 0x6000
    c.b = len(tail)
    c.run(address(listing, "BC_COMMAND"), limit=100000)
    assert output(c).endswith(".\r\n"), repr(output(c))
    assert (ROOT / "src/distribution/STARTUP.SUB").read_bytes() == b":VER /BANNER\r\n\x1a"
    print("VER exact banner, concise output, invalid combinations and startup script pass")
if __name__ == "__main__":
    main()
