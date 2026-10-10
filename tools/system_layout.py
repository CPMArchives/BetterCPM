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
    HISTORY="LY_HIST", TPA="LY_TPA", BOOT_SECTORS="LY_SECTS", CONFIG="LY_CFG", CPX_CONTROL="LY_CPX", RAM_END="LY_RAMEND",
    RELOADER_CAPACITY="LY_RLCAP", RSX_SELECTOR="LY_RSSEL")
LAYOUT = {name: SYMBOLS[symbol] for name, symbol in ALIASES.items()}
LAYOUT.update(PDS_DESCRIPTOR=LAYOUT["SYSTEM"] + 0x80,
              PDS_TOP=LAYOUT["SYSTEM"], PDS_LOW=LAYOUT["HISTORY"],
              PDS_SIZE=LAYOUT["SYSTEM"] - LAYOUT["HISTORY"])

def expand_layout(text: str) -> str:
    """Inline the canonical include for host z80asm and native ZSM4."""
    from utility_versions import expand_versions
    text = expand_versions(text)
    text = re.sub(r"^\s*INCLUDE\s+layout\.inc\s*$",
                  lambda _: SOURCE.read_text(encoding="ascii").rstrip(),
        text, flags=re.MULTILINE | re.IGNORECASE)
    if '; @bounded-filespec@' in text:
        text = text.replace('; @bounded-filespec@',
            (ROOT / 'src/utilities/common/filespec.inc').read_text(encoding='ascii'))

    if '; @rcp-shared-selector@' in text:
        start = text.index('BC_DIR:')
        end = text.index('BC_FFIX:', start)
        directory = text[start:end]
        search = directory.index('  ; Search all physical directory extents.')
        directory = ((ROOT / 'src/cpx/dir-select.inc').read_text(encoding='ascii') +
                     '\nRD_SEARCH:\n' + directory[search:])
        directory = directory.replace('        LD      A,1                     ; stock NO FILE',
            '        CALL    RD_FILTER\n        JR      NC,BC_DSKIP\n'
            '        LD      A,1                     ; stock NO FILE', 1)
        directory = directory.replace("        ADD     A,'A'\n        CALL    BC_PCHAR\n",
            "        ADD     A,'A'\n        CALL    BC_PCHAR\n        CALL    RD_PRINTUSER\n", 1)
        # Each DU gets its own completed listing; restore the caller only at end.
        done = directory.index('BC_DDONE:')
        directory = directory[:done] + directory[done:].replace(
            '        JP      BC_DURST', '        JP      RD_NEXT', 2)
        directory = directory.replace('        LD      HL,(BC_DIREP)\n        LD      DE,10',
            '        LD      A,(OQ_LEN)\n        OR      A\n        JR      NZ,RD_VISIBLE\n'
            '        LD      HL,(BC_DIREP)\n        LD      DE,10', 1)
        directory = directory.replace('        LD      A,(BC_DCOL)\n',
            'RD_VISIBLE:\n        LD      A,(BC_DCOL)\n', 1)
        text = text[:start] + directory + text[end:]
        if 'CPXBASE         EQU     00100H' not in text:
            ren_start = text.index('BC_REN:')
            ren_end = text.index('BC_RNOQ:', ren_start)
            text = text[:ren_start] + (ROOT / 'src/cpx/ren-select.inc').read_text(encoding='ascii') + text[ren_end:]
            copy_start = text.index('BC_CPARSE:')
            copy_end = text.index('BC_COPEN:', copy_start)
            text = text[:copy_start] + (ROOT / 'src/cpx/copy-select.inc').read_text(encoding='ascii') + text[copy_end:]
            # Resident commands now use the shared selector/scanner. Keep the
            # legacy parser and wildcard driver only in transient expansions.
            text = text[:text.index('BC_COPAR:')] + text[text.index('BC_COPT:'):]
            text = text[:text.index('BC_CVALID:')] + text[text.index('; Shared bounded 8.3 validator.'):]
            text = text[:text.index('BC_WSTART:')] + text[text.index('BC_WCMP:'):]
            text = text.replace('BC_CDSAV', 'BC_DSAVE').replace('BC_CUSAV', 'BC_USAVE')
            text = text.replace('BC_CSDRV', 'RF_DRIVE').replace('BC_CSUSR', 'RF_USER')
            text = re.sub(r'^RF_DRIVE:.*COPY source drive.*\n|^RF_USER:.*COPY source user.*\n', '', text, flags=re.MULTILINE)
            text = re.sub(r'^BC_W(?:FCB|LAST|BEST|NAME):.*\n', '', text, flags=re.MULTILINE)
            text = re.sub(r'^BC_DSAVE:.*COPY saved drive.*\n|^BC_USAVE:.*COPY saved user.*\n', '', text, flags=re.MULTILINE)
            text = text.replace('        LD      (BC_CWILD),A\n', '')
            text = text.replace('        LD      A,(BC_MVFLAG)\n        AND     1\n        LD      (BC_MVFLAG),A\n', '')
        text = text.replace('BC_ERA:                                 ; execute ERA command\n',
            'BC_ERA:                                 ; execute ERA command\n'
            '        CALL    RE_VALIDATE\n        JP      C,RE_REJECT\n', 1)
        common = ROOT / 'src/utilities/common'
        predicate = (common / 'attrselect.inc').read_text(encoding='ascii')
        predicate = predicate[:predicate.index('; Destination modification list:')]
        selector = ('DU_MAP: DS 64\nDU_WORK: DS 12\n' +
                    (common / 'duselect.inc').read_text(encoding='ascii') +
                    (common / 'operandqual.inc').read_text(encoding='ascii') + predicate +
                    (common / 'rcpselect.inc').read_text(encoding='ascii') +
                    '\nRE_REJECT:\n        LD A,(FS_ERROR)\n        OR A\n'
                    '        JP NZ,BC_DBAD\n        JP BC_DURST\n' +
                    (ROOT / 'src/cpx/era-select.inc').read_text(encoding='ascii'))
        text = text.replace('; @rcp-shared-selector@', selector)

    order = (1,3,5,7,9,2,4,6,8,10)
    def table(start, count):
        return "\n".join(f"        DB {n//20},{n//10%2},{order[n%10]}" for n in range(start, start+count))
    return text.replace("; @resident-sector-table@", table(2, LAYOUT["BOOT_SECTORS"])) .replace(
        "; @command-sector-table@", table(14 + LAYOUT["BOOT_SECTORS"], 13)).replace(
        "; @reloader-sector-table@", table(2 + LAYOUT["BOOT_SECTORS"], 2)).replace(
        "; @control-sector-table@", table(4 + LAYOUT["BOOT_SECTORS"], 2)).replace(
        "; @rsx-sector-table@", table(6 + LAYOUT["BOOT_SECTORS"], 2)).replace(
        "; @rsx-validator-sector-table@", table(8 + LAYOUT["BOOT_SECTORS"], 2)).replace(
        "; @rsx-publisher-sector-table@", table(10 + LAYOUT["BOOT_SECTORS"], 2)).replace(
        "; @rsx-resolver-sector-table@", table(12 + LAYOUT["BOOT_SECTORS"], 2))
