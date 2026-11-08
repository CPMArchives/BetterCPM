#!/usr/bin/env python3
"""Exercise the shared VER entry with exact banner and invalid option tails."""
from pathlib import Path
from test_utility_versions import runner, output, address
ROOT = Path(__file__).resolve().parents[1]
from version_metadata import rows
RELEASE = next(row['implementation_version'] for row in rows()
               if row['component'] == 'BetterCP/M')
EXPECTED = "\r\n" + "\r\n".join([
    " - - -" + " " * 50 + "- - - ",
    "|" + " " * 60 + "|",
    "|" + "BetterCP/M".center(60) + "|",
    ("Core OS " + RELEASE).center(62).rstrip(),
    "",
    "CP/M 2.2 Compatible System".center(62).rstrip(),
    "",
    "Type TYPE README.TXT for more".center(62).rstrip(),
    "|" + " " * 60 + "|",
    " - - -" + " " * 50 + "- - - ",
]) + "\r\n"
def main():
    assert EXPECTED.isascii()
    assert len(EXPECTED.splitlines()[1:]) == 10
    assert max(map(len, EXPECTED.splitlines())) <= 80
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
            "\r\nBetterCP/M " + RELEASE + "\r\n" if not tail else "\r\n?\r\n")
        assert output(c) == expected, (tail, repr(output(c)))
    # Issue #612: keep normal resident queries separate from VER.COM queries.
    from test_resident_feature_hints import execute as resident_query
    from test_utility_finalization import execute as transient_query
    from test_utility_versions import expected_identification
    from utility_help import text, resident_identification
    from utility_versions import banner
    for base in (0x4000, 0x8101, 0xA000):
        for tail in ('/VER', '/ver', 'FILE /VER /BOGUS'):
            actual,calls=resident_query('VER '+tail,base,strict=True,hostile=True)
            assert actual==resident_identification('VER'),(base,tail,actual)
            assert set(calls)=={9},(base,tail,calls)
        for tail in ('/H', '/HELP', '/hElP', '/VER /HELP /BOGUS'):
            actual,_=resident_query('VER '+tail,base,strict=True,hostile=True)
            assert actual==text('VER',identity=banner('VER',True),resident=True),(base,tail,actual)
        actual,_=resident_query('VER',base,strict=True)
        assert actual=='\r\nBetterCP/M '+RELEASE+'\r\n',actual
    for tail in ('/VER', '/ver', 'FILE /VER /BOGUS'):
        assert transient_query('VER',tail)[0]==expected_identification('VER'),tail
    for tail in ('/H', '/HELP', '/hElP', '/VER /HELP /BOGUS'):
        assert transient_query('VER',tail)[0]==text('VER'),tail
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
