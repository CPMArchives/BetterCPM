#!/usr/bin/env python3
"""Cost alternative terminal profiles in isolated BIOS assemblies.

Supply the read-only reconstructed MM source ZIP. These are size samples and
parser probes, not production terminal implementations. The VT52 screen sample
omits graphics, identification replies, keypad and hold-screen behavior.
"""
from __future__ import annotations
import argparse
import json
import re
from textwrap import dedent
import zipfile
from pathlib import Path
from audit_monitor_memory import assemble
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]


def mm_console(archive: Path) -> str:
    with zipfile.ZipFile(archive) as zipped:
        ref = zipped.read("mmcpm232/bios.asm").decode("latin1").replace("\r\n", "\n")
    start = ref.index("\nconoutcrt:") + 1
    end = ref.index("\ncursorflag:", start)
    end = ref.index("\n", end + 1)
    ref = ref[start:end+1].replace("conoutcrt:", "M4_SCROLL_OUT:")
    ref = ref.replace("\tld\ta,8eh\n\tout\t(optreg),a\n", "")
    ref = ref.replace("\tld\ta,8fh\n\tout\t(optreg),a\n", "")
    a = ref.index("initvideodata:")
    b = ref.index("; character at current video location", a)
    ref = ref[:a] + ref[b:]
    ref = ref.replace("soundport", "SOUNDPRT")
    head = """SOUNDPRT EQU 090H
videobase EQU VIDEOBASE
lastvidline EQU VIDEOEND-80
M4_INIT:
        LD A,08EH
        OUT (OPTREG),A
        XOR A
        LD DE,videopos
        LD BC,5
        CALL fillmem
        LD A,020H
        LD (videochar),A
        LD A,080H
        LD (cursorflag),A
        JP cls
"""
    private = """
M4_CUROUT:
        LD A,C
        OR A
        JR Z,MC_QUERY
        OR 080H
        LD C,A
        CALL M4_SCROLL_OUT
MC_QUERY:
        LD A,1
        RET
fillmem:
        LD H,D
        LD L,E
        LD (HL),A
        DEC BC
        LD A,B
        OR C
        RET Z
        INC DE
        LDIR
        RET
"""
    keyboard = (ROOT / "src/platform/trs80m4/m4cons.inc").read_text()
    keyboard = keyboard[keyboard.index("M4_IN:"):keyboard.index("M4CURSOR:")]
    return head + ref + private + keyboard + "M4_PENDING: DW 0\n"


def video_profiles(reference_console: str) -> dict[str, str]:
    front='''
    VT_OUTPUT:
            LD A,(escflag)
            OR A
            JR NZ,VT_ESCAPE
            LD A,C
            CP 27
            JP Z,eschandler
            LD HL,(videopos)
            CP 7
            JP Z,bellhandler
            CP 8
            JP Z,VT_LEFT
            CP 9
            JP Z,VT_TAB
            CP 10
            JP Z,incvidrow
            CP 13
            JP Z,crhandler
            CP 28
            JP Z,cls
            CP 32
            RET C
            CP 127
            RET Z
            CALL putvchar
            LD HL,(videopos)
            LD A,H
            CP 79
            RET Z
            INC H
            LD (videopos),HL
            RET
    VT_ESCAPE:
            CP 3
            JP NZ,escseq
            XOR A
            LD (escflag),A
            LD HL,(videopos)
            LD A,C
            CP 'Y'
            JR Z,VT_ADDRESS
            CP 'A'
            JP Z,VT_UP
            CP 'B'
            JR Z,VT_DOWN
            CP 'C'
            JR Z,VT_RIGHT
            CP 'D'
            JR Z,VT_LEFT
            CP 'H'
            JP Z,homecursor
            CP 'I'
            JR Z,VT_REVERSE
            CP 'J'
            JP Z,clreos
            CP 'K'
            JP Z,clreol
            RET
    VT_ADDRESS:
            LD A,2
            JP escseq6
    VT_UP:
            LD A,L
            OR A
            RET Z
            DEC L
            JR VT_STORE
    VT_DOWN:
            LD A,L
            CP 23
            RET Z
            INC L
            JR VT_STORE
    VT_RIGHT:
            LD A,H
            CP 79
            RET Z
            INC H
            JR VT_STORE
    VT_LEFT:
            LD A,H
            OR A
            RET Z
            DEC H
    VT_STORE:
            LD (videopos),HL
            RET
    VT_TAB:
            LD A,H
            AND 0F8H
            ADD A,8
            CP 80
            JR C,VT_TABOK
            LD A,79
    VT_TABOK:
            LD H,A
            JR VT_STORE
    VT_REVERSE:
            LD A,L
            OR A
            JR NZ,VT_UP
            JP insertline
    '''
    front=dedent(front)
    text=reference_console
    # Safe endpoint for the isolated reverse-scroll size sample; not an MM-binary equivalence claim.
    text=text.replace('\tld\tde,-127','\tld\tde,VIDEOEND-1')
    # Keep both parsers and one backend, choose compile-time entry for measurement.
    combined=text+front
    both=combined.replace('\tcall\toutputchar','\tcall\tPROFILE_OUT',1)+dedent('''
    PROFILE_OUT:
            LD A,(VT_PROFILE)
            OR A
            JP Z,outputchar
            JP VT_OUTPUT
    VT_PROFILE: DB 0
    ''')
    # VT-only: retain the common coordinate phase, but remove MM selector/control dispatcher.
    vt=combined.replace('\tcall\toutputchar','\tcall\tVT_OUTPUT',1)
    a=vt.index('outputchar:');b=vt.index('escseq2:',a)
    vt=vt[:a]+'escseq:\n        CP 2\n        JR Z,escseq4\n'+vt[b:]
    a=vt.index('outctrl:');b=vt.index('bellhandler:',a)
    vt=vt[:a]+vt[b:]
    a=vt.index('tabhandler:');b=vt.index('incvidrow:',a)
    vt=vt[:a]+vt[b:]
    a=vt.index('deleteline:');b=vt.index('clreol:',a)
    vt=vt[:a]+vt[b:]
    a=vt.index('shiftouthandler:');b=vt.index('eschandler:',a)
    vt=vt[:a]+vt[b:]
    a=vt.index('cursoronoff:');b=vt.index('videochar:',a)
    vt=vt[:a]+vt[b:]
    a=vt.index('ctrlcodetable:');b=vt.index('cursorflag:',a)
    vt=vt[:a]+vt[b:]
    return {"mm-reference-integration": reference_console, "vt52-screen": vt, "both-screen": both}


def host_source(platform: str) -> str:
    source = (ROOT / "src/bios/bios.mac").read_text()
    source, count = re.subn(r"(BIOREADR:[^\n]*\n)\s*LD\s+A,01AH\n\s*RET",
                            r"\1        IN A,(5)\n        RET", source, count=1)
    if count != 1:
        raise ValueError("READER source anchor changed")
    a, b = source.index("BIOREAD:"), source.index("; LISTST", source.index("BIOREAD:"))
    source = source[:a] + (ROOT / "src/platform/z80pack/recordio.inc").read_text() + source[b:]
    return source.replace("        INCLUDE biosplat.inc", platform)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mm-reference", required=True, type=Path)
    parser.add_argument("--assembler", type=Path, default=Path("/Users/nathanael/bin/z80asm"))
    parser.add_argument("--output", type=Path, default=ROOT / "build/audit/monitor-efficiency")
    args = parser.parse_args()
    rows = []
    for profile, console in video_profiles(mm_console(args.mm_reference)).items():
        stage = args.output / profile
        stage.mkdir(parents=True, exist_ok=True)
        (stage / "m4cons.inc").write_text(console)
        (stage / "m4scroll.inc").write_text("; Output lives in isolated m4cons.inc.\n")
        (stage / "biosplat.inc").write_text((ROOT / "src/bios/biosplat.inc").read_text())
        (stage / "reload.inc").write_text(expand_layout((ROOT / "src/platform/trs80m4/reload.inc").read_text()))
        data = assemble((ROOT / "src/bios/bios.mac").read_text(), "bios", LAYOUT["BIOS"], stage, args.assembler)
        rows.append(dict(profile=profile, bytes=len(data), growth=len(data)-636, directory=str(stage)))
    platform = (ROOT / "src/platform/z80pack/biosplat.inc").read_text()
    for profile, definition in (("host-ansi", platform), ("host-vt52-pass", platform.replace(
            "DB 27,'[2J',27,'[H',0", "DB 27,'H',27,'J',0"))):
        stage = args.output / profile
        data = assemble(host_source(definition), "bios", LAYOUT["BIOS"], stage, args.assembler)
        rows.append(dict(profile=profile, bytes=len(data), allocation=638, directory=str(stage)))
    (args.output / "profiles.json").write_text(json.dumps(rows, indent=2)+"\n")
    for row in rows:
        print(f"{row['profile']}: {row['bytes']} BIOS bytes")


if __name__ == "__main__":
    main()
