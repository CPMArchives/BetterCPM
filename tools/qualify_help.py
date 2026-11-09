#!/usr/bin/env python3
"""Exercise the actual HELP.COM on disposable cpmsim media."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from build_help import OUTPUT
from test_ark import member
from test_cr import reference as crunch
from test_lbr import archive, entry, with_crcs
from test_noah_ark_lzw import lzw
from test_noah_ark_packed import packed
from test_noah_ark_squeezed import squeezed
from test_usq import squeeze
from test_z80pack_sysgen_install import session

PROMPT = b"Choice (< > Q): "
CCP = b"B0>_ "


def library(items):
    count = (len(items) + 4) // 4
    payload = bytearray()
    entries = []
    for name, data in items:
        base, extension = name.split(".")
        pad = (-len(data)) % 128
        n = (len(data) + pad) // 128
        entries.append(entry(base.encode().ljust(8) + extension.encode(),
                             count + len(payload) // 128, n, pad))
        payload.extend(data + b"\x1a" * pad)
    return with_crcs(archive(entries, bytes(payload), count))


def topic(title, body=""):
    return f"# {title}\r\n\r\n{body}\r\n".encode("ascii")


def put(disks, letter, user, name, raw):
    staged = disks.parent / name
    staged.write_bytes(raw)
    subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                    str(disks / f"drive{letter}.dsk"), str(staged), f"{user}:{name}"],
                   cwd=disks.parent, check=True, capture_output=True)


def prepare(disks, built):
    def install(letter, user, name, data):
        put(disks, letter, user, name, data)

    install("b", 0, "HELP.COM", (built / "HELP.COM").read_bytes())
    install("b", 0, "HELP.LBR", (built / "HELP.LBR").read_bytes())
    install("c", 3, "PIP.HQP", squeeze(topic("Loose PIP in C3"), name=b"PIP.HLP"))
    install("c", 3, "PIP.HZP", crunch(topic("Crunch PIP in C3"), name=b"PIP.HLP"))
    install("c", 3, "PLAIN.HLP", topic("Preferred plain form"))
    install("c", 3, "PLAIN.HQP", squeeze(topic("Later squeezed form")))
    install("c", 3, "HELP.LBR", library([("SHADOW.HLP", topic("Shadowed library"))]))
    install("b", 0, "BAD.HQP", b"broken")
    install("b", 0, "MENU.LBR", library([
        ("DIR.HLP", topic("Archive DIR")), ("COPY.HLP", topic("Archive COPY")),
        ("LIST.HLP", topic("Archive LIST")), ("COMMAND.HZP", crunch(topic("Crunched command"))),
        ("STAT.HLP", topic("Archive STAT")), ("WIZ.HQP", squeeze(topic("Archive wizard"))),
        ("CMD2.HLP", topic("Archive CMD2")), ("WIZ.HLP", topic("Preferred archive wizard")),
        ("SKIP.TXT", b"not help")]))
    install("b", 0, "WIZ.HLP", topic("Loose wizard"))
    install("b", 0, "LONG.HLP", topic("Paging", "## Records\r\n```\r\n" +
            "\r\n".join(f"Record {i:02d}" for i in range(65)) + "\r\n```"))
    install("b", 0, "SECTIONS.HLP", topic("Many sections", "\r\n".join(
            f"## Item {i:02d}\r\n\r\nUnique {i:02d}" for i in range(40))))
    install("b", 0, "LINKS.HLP", topic("Link tests",
            "[multiword](SECTIONS.HLP#item-17), [absent](SECTIONS.HLP#absent) "
            "and [missing](BOGUS.HLP)."))
    install("b", 0, "AMBIG.HLP", topic("Ambiguous links",
            "## File attributes\r\nFirst.\r\n## File-attributes\r\nSecond."))
    install("b", 0, "SPELL.HLP", topic("Literal punctuation",
            "[ambiguous](AMBIG.HLP#file-attributes)\r\n\r\n"
            "Keep `A  B` together with a single literal ` marker.\r\n\r\n"
            "A single ** marker and B[-]:*.COM.\r\n\r\n"
            "[print](X.BIN) and **emphasis across\r\na line**."))
    install("b", 0, "TWINS.HLP", topic("Long headings",
            "## File selection by name\r\nName form.\r\n"
            "## File selection by drive\r\nDrive form."))
    install("b", 0, "FRAME.HLP", topic("Reading [PIP](PIP.HLP) on a forty-column terminal display",
            "## A section heading that runs beyond forty columns\r\nBody text."))
    install("b", 0, "LARGE.HLP", topic("Large topic") + b"x" * 47000)
    # The first default archive controls bare HELP even if another archive
    # on PATH has an authored index; the loose names never enter its menu.
    install("b", 4, "HELP.LBR", library([("ONLY.HQP", squeeze(topic("Only in this archive")))]))
    install("b", 4, "ONLY.HLP", topic("Only as a loose file"))
    wire = bytearray()
    for method in range(1, 10):
        data = topic(f"ARK method {method}")
        name = f"M{method}.HLP".encode()
        if method <= 2:
            part = member(data, method, name)
        elif method == 3:
            part = packed(data, name)
        elif method == 4:
            part = squeezed(data, name)
        else:
            part = lzw(data, method, name)
        wire.extend(part)
    wire.extend(lzw(squeeze(topic("Nested squeeze")), 8, b"NESTSQ.HQP"))
    wire.extend(squeezed(crunch(topic("Nested crunch")), b"NESTCR.HZP"))
    wire.extend(member(topic("ARK index"), name=b"_INDEX.HLP"))
    wire.extend(b"\x1a\0")
    install("d", 15, "HELP.ARK", bytes(wire))
    install("d", 15, "BROKEN.ARK", member(topic("bad"), name=b"BAD.HLP", crc=1) + b"\x1a\0")


class Dialog:
    def __init__(self):
        self.steps = []

    def send(self, text, *expect):
        for i, wanted in enumerate(expect):
            self.steps.append((text.encode("ascii") if i == 0 else b"",
                               wanted.encode("ascii") if isinstance(wanted, str) else wanted, 10))

    def command(self, text, *expect):
        self.send(text + "\r", *expect)

    def quit(self):
        self.send("Q", CCP)


def exercise(simulator, disks, transcript):
    d = Dialog()
    d.command("B:", CCP)
    d.command("HELP /S=ABSENT.ARK /VER /HELP", "For detailed help, see HELP HELP", CCP)
    d.command("HELP /S=ABSENT.ARK /VER", "Topic Help Reader", CCP)
    d.command("HELP PIP /R", "B0:HELP.LBR (PIP.HLP)", CCP)
    d.command("HELP", "[0] COPY", PROMPT)
    d.send("0", "COPY - Copy files", "[1] PIP selectors.", PROMPT)
    d.send("1", "Selectors\r\n", "PIP A4:=B[-]:*.COM", PROMPT)
    d.send("\x03", "COPY - Copy files", PROMPT)
    d.send("q", "[0] COPY", PROMPT)
    d.quit()
    d.command("HELP PIP syntax", "Syntax\r\n", "PIP D:=A:*.COM", PROMPT)
    d.quit()
    d.command("HELP /S=MENU.LBR", "0. DIR", "3. COMMAND", "6. CMD2", PROMPT)
    d.send("5", "Preferred archive wizard", PROMPT)
    d.send("q", "0. DIR", PROMPT)
    d.send("3", "Crunched command", PROMPT)
    d.send("q", "0. DIR", PROMPT)
    d.quit()
    d.command("A0:PATH C3: D15:", CCP)
    d.command("HELP PIP /REPORT", "C3:PIP.HQP", CCP)
    d.command("HELP PLAIN /R", "C3:PLAIN.HLP", CCP)
    d.command("HELP PIP", "Loose PIP in C3", PROMPT)
    d.quit()
    d.command("HELP /S=C3:PIP.HZP", "Crunch PIP in C3", PROMPT)
    d.quit()
    d.command("HELP PIP /S=B0:HELP.LBR /R", "B0:HELP.LBR (PIP.HLP)", CCP)
    d.command("HELP SHADOW /R", "No help for SHADOW was found.", CCP)
    d.command("HELP GONE", "[0] COPY", PROMPT)
    d.quit()
    d.command("HELP GONE /R", "No help for GONE was found.", CCP)
    d.command("HELP BAD", "Damaged or unreadable", CCP)
    d.command("HELP LARGE", "Insufficient memory", CCP)
    d.command("HELP /S=D15:HELP.ARK", "ARK index", PROMPT)
    d.quit()
    for method in range(1, 10):
        d.command(f"HELP M{method}", f"ARK method {method}", PROMPT)
        d.quit()
    for name, title in [("NESTSQ", "Nested squeeze"), ("NESTCR", "Nested crunch")]:
        d.command(f"HELP {name}", title, PROMPT)
        d.quit()
    d.command("HELP BAD /S=D15:BROKEN.ARK", "Damaged or unreadable", CCP)
    d.command("HELP LONG RECORDS", "Record 00", PROMPT)
    d.send(">", "Record 28", PROMPT)
    d.send("<", "Record 00", PROMPT)
    d.quit()
    d.command("HELP SECTIONS", "A  Item 10", "Z  Item 34", PROMPT)
    d.send(".", "0  Item 35", PROMPT)
    d.send("0", "Unique 35", PROMPT)
    d.send("q", "0  Item 35", PROMPT)
    d.quit()
    d.command("HELP LINKS", "multiword", PROMPT)
    d.send("0", "Unique 17", PROMPT)
    d.send("q", "Link tests", PROMPT)
    d.send("1", "Link tests", "No such section:", PROMPT)
    d.send("2", "Link tests", "BOGUS.HLP", PROMPT)
    d.quit()
    d.command("HELP SPELL", "A  B together with a single literal ` marker.",
              "A single ** marker and B[-]:*.COM.", "[print](X.BIN) and emphasis across a line.", PROMPT)
    d.send("0", "Literal punctuation", "Ambiguous section:", PROMPT)
    d.quit()
    d.command("HELP TWINS FILE SELECTION BY DRIVE", "Drive form.", PROMPT)
    d.quit()
    d.command("HELP COPY /SOURCE=C3:PIP.HZP", "Invalid HELP usage", CCP)
    d.command("HELP /S=B7:ABSENT.ARK", "B7:ABSENT.ARK", CCP)
    d.command("B4:", "B4>_ ")
    d.command("B0:HELP", "0. ONLY", PROMPT)
    d.send("0", "Only in this archive", PROMPT)
    d.send("Q", "0. ONLY", PROMPT)
    d.send("Q", "B4>_ ")
    d.command("B0:HELP ONLY /R", "B4:ONLY.HLP", "B4>_ ")
    d.command("B0:HELP /S=0:HELP.LBR", "BetterCP/M Help", PROMPT)
    d.send("Q", "B4>_ ")
    d.command("B6:", "B6>_ ")
    d.command("A0:PATH D15:", "B6>_ ")
    d.command("B0:HELP", "ARK index", PROMPT)
    d.send("Q", "B6>_ ")
    d.command("A0:PATH B6:", "B6>_ ")
    d.command("B0:HELP", "No help archive was found.", "B6>_ ")
    d.command("B0:HELP GONE", "No help for GONE was found.", "B6>_ ")
    output = session(simulator, disks, d.steps, transcript)
    return len([s for s, _, _ in d.steps if s]), output


def check_console(simulator, disks, built):
    """Read back full HELP screens from shipped personalities and altered TCAP fixtures."""
    from tcap_test_support import Guest

    work = disks.parent
    original = work / "shipped-ansi.rsx"
    subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                    str(disks / "drivea.dsk"), "0:ANSI.RSX", str(original)], cwd=work, check=True)
    def ansi_fixture(user, width, capabilities=15, rows=24):
        image = bytearray(original.read_bytes())
        facts = b"TC\x02\x08\x18\x50\x0f\x02"
        assert image.count(facts) == 1
        pos = image.index(facts)
        image[pos + 4:pos + 7] = bytes((rows, width, capabilities))
        start = struct.unpack_from("<H", image, 24)[0]
        size = struct.unpack_from("<H", image, 12)[0]
        struct.pack_into("<H", image, 44, sum(image[start:start + size]) & 65535)
        put(disks, "b", user, "ANSI.RSX", bytes(image))

    for width, source in ((80, "A0:ADM3A"), (80, "A0:ANSI"), (40, "B0:ANSI"), (80, "A0:VT52")):
        if width == 40:
            ansi_fixture(0, 40)
        personality = source.split(":")[1]
        folder = work / f"console-{personality}-{width}"
        folder.mkdir()
        guest = Guest(simulator, disks, folder)
        def send(keys):
            os.write(guest.terminal, keys.encode("ascii"))
        def frame(title, footer, marker):
            guest.expect(marker.encode(), rendered=True)
            guest.expect(footer.encode(), rendered=True)
            rows = [row.rstrip() for row in guest.screen.display]
            assert rows[0] == title and rows[-1] == footer, rows
            assert all(len(row) <= width for row in rows), rows
            return rows
        def quit_reader():
            send("Q")
            guest.prompt()
            assert not any("Q Exit" in row for row in guest.screen.display)
        try:
            guest.prompt()
            guest.prompt("RSX LOAD " + source)
            send("B0:HELP PIP /S=B0:HELP.LBR\r")
            title = "PIP - File and device transfer"
            menu = "0  Syntax           1  Selectors"
            rows = frame(title, "0-2 Select  Q Exit", menu)
            if width == 40:
                assert rows[rows.index(menu) + 1] == "2  Examples", rows
            else:
                assert menu + "        2  Examples" in rows, rows
            send("0")
            rows = frame("PIP - Syntax", "Q Back", "Put the")
            row = next(i for i, line in enumerate(rows) if "destination" in line)
            col = rows[row].index("destination")
            cells = guest.screen.buffer[row]
            standout = personality != "VT52"
            assert all(cells[n].reverse == standout for n in range(col, col + len("destination")))
            assert not cells[col + len("destination")].reverse
            send("Q")
            frame(title, "0-2 Select  Q Exit", menu)
            quit_reader()

            send("B0:HELP LONG RECORDS /S=B0:LONG.HLP\r")
            rows = frame("LONG - Records", "> Next  Q Exit", "Record 21")
            assert rows[1] == "Record 00" and rows[-2] == "Record 21", rows
            send(".")
            rows = frame("LONG - Records", "< Prev  > Next  Q Exit", "Record 43")
            assert rows[1] == "Record 22" and rows[-2] == "Record 43", rows
            send(">")
            frame("LONG - Records", "< Prev  Q Exit", "Record 64")
            send("<")
            frame("LONG - Records", "< Prev  > Next  Q Exit", "Record 22")
            quit_reader()

            send("B0:HELP /S=B0:MENU.LBR\r")
            frame("Help topics", "0-6 Select  Q Exit", "3. COMMAND")
            send("3")
            frame("Crunched command", "Q Back", "Crunched command")
            send("\x03")
            frame("Help topics", "0-6 Select  Q Exit", "6. CMD2")
            quit_reader()

            if width == 40:
                send("B0:HELP /S=B0:SECTIONS.HLP\r")
                frame("Many sections", "0-P,R-Z Select  > Next  Q Exit", "Z  Item 34")
                send(">")
                frame("Many sections", "0-4 Select  < Prev  Q Exit", "0  Item 35")
                quit_reader()
                send("B0:HELP /S=B0:LINKS.HLP\r")
                frame("Link tests", "0-2 Select  Q Exit", "absent")
                send("2")
                frame("Link tests", "0-2 Q Link not found: BOGUS.HLP", "Link not found")
                quit_reader()
                send("B0:HELP /S=B0:FRAME.HLP\r")
                long_title = "Reading PIP on a forty-column terminal display"
                rows = frame(long_title[:40].rstrip(), "0-1 Select  Q Exit", "1  A section")
                assert any("[0] PIP" in row for row in rows[1:-1])
                send("1")
                heading = "A section heading that runs beyond forty columns"
                rows = frame(("FRAME - " + heading)[:40].rstrip(), "Q Back", "Body text.")
                assert heading in " ".join(row for row in rows[1:-1] if row)
                send("Q")
                frame(long_title[:40].rstrip(), "0-1 Select  Q Exit", "1  A section")
                quit_reader()
        finally:
            guest.close()
        shutil.copyfile(folder / "transcript.bin", built / f"cpmsim-help-{personality}-{width}.log")
        print(f"PASS: {personality} at {width} columns, fixed header/footer, paging, selection and return.")

    for user, (name, width, capabilities, height) in enumerate((
            ("unknown-width", 0, 15, 24), ("no-position", 80, 13, 24),
            ("refused-position", 80, 15, 25)), 1):
        ansi_fixture(user, width, capabilities, height)
        folder = work / name
        folder.mkdir()
        guest = Guest(simulator, disks, folder)
        try:
            guest.prompt()
            guest.prompt(f"RSX LOAD B{user}:ANSI")
            os.write(guest.terminal, b"B0:HELP PIP /S=B0:HELP.LBR\r")
            guest.expect(PROMPT.rstrip(), rendered=True)
            rows = [row.strip() for row in guest.screen.display]
            assert "PIP - File and device transfer" in rows, (name, rows)
            assert PROMPT.decode().strip() in rows[:-1], rows
            os.write(guest.terminal, b"Q")
            guest.prompt()
        finally:
            guest.close()
        print(f"PASS: {name} uses sequential browsing.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--system", type=Path, required=True, help="BetterCP/M cpmsim System disk.raw")
    p.add_argument("--simulator", type=Path, required=True, help="patched cpmsim executable")
    p.add_argument("--build", type=Path, default=OUTPUT)
    p.add_argument("--console", action="store_true", help="also check rendered TCAP screens (requires pyte)")
    args = p.parse_args()
    system = args.system.resolve()
    built = args.build.resolve()
    with tempfile.TemporaryDirectory(prefix="bettercpm-help-test-") as tmp:
        work = Path(tmp)
        disks = work / "disks"
        disks.mkdir()
        shutil.copyfile(system, disks / "drivea.dsk")
        shutil.copyfile(system.parent / "diskdefs", work / "diskdefs")
        for letter in "bcd":
            target = disks / f"drive{letter}.dsk"
            target.write_bytes(bytes([0xe5]) * system.stat().st_size)
        prepare(disks, built)
        before = [hashlib.sha256(p.read_bytes()).digest() for p in sorted(disks.glob("drive[bcd].dsk"))]
        count, _ = exercise(args.simulator.resolve(), disks, built / "cpmsim-help.log")
        after = [hashlib.sha256(p.read_bytes()).digest() for p in sorted(disks.glob("drive[bcd].dsk"))]
        assert before == after, "HELP modified a data disk"
        print(f"PASS: {count} command and navigation inputs, unchanged data disks.")
        if args.console:
            check_console(args.simulator.resolve(), disks, built)


if __name__ == "__main__":
    main()
