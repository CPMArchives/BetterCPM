# DUP specification alignment — 2026-10-16

## Conclusion

DUP Build 003 is aligned with the current authoritative
[DUP specification](DUP%20Specification.md). No implementation change was found
necessary in this audit. Final release qualification remains separate.

A fresh assembly of current DUP source and includes matches the tested binary
byte-for-byte: **8,267 bytes**, SHA-256
`2c80876a4db2e2b0c4a0353b5ff945d45975b3b40af9a5955fc8cbf7650df4b1`.
The older command-line report's 8,247-byte figure was stale and is corrected.

## Contract-to-implementation review

| Contract | Implementation evidence |
| --- | --- |
| Interactive FORMAT/COPY/CHECK and direct equivalents | DMAIN, ASKDRV and dup-cli.inc supply operands to the same DFORMAT/DCOPY/DCHECK engines |
| Complete syntax validation before initialization | UV_CHECK and DCPARSE precede INIT; parser rejects DU selectors, filenames, extra options and COPY destination A |
| Standalone /VER | Version metadata and early version gate; current identity Build 003 |
| Physical system protection and distinct drives | DFORMAT/DCOPY reject physical drive 0 as destructive target; DCOPY rejects physical aliases |
| Binding-based format and backend validation | GETBIND, DFORMAT/STREAM and checked API operations; no file enumeration or silent geometry approximation |
| Destructive confirmation retained | DFORMAT and CPCONF require Y; direct invocation bypasses only selection menus |
| Immediate erased-payload verification | DTRACK invokes WALK mode 1 after WRTRY and counts verified surfaces |
| Source captured before destination destruction | COPYLP source WALK mode 2 precedes destination formatting/writing |
| Full copied-payload verification | CPWRITE follows writes with WALK mode 4 byte comparison; mismatch FEh |
| Bounded formatting retry | WRTRY permits three attempts, stops on write protection |
| Read-only CHECK and physical-sector counting | DCHECK uses WALK mode 0; WERROR increments word ERRORS and skips to SECEND |
| Binding restoration and reset | CLEANUP restores SAVED, clears CHANGED only after success, then resets drive aliases; RESTFAIL retains/retries saved binding |
| Interruption and direct return | BREAKCK/WABORT/STOPPED plus DCRUN one-shot dispatch and DCPAUSE gate |
| Runtime bounds | 51K guard; 32-sector FORMAT limit; 64-record COPY surface limit; bounded track stream and packed sector sizes |
| Machine-specific operations behind backend | Standard BIOS calls and disk-control API; optional advertised fast-format entry uses the same formatter contract |

The interactive `BetterCP/M 2.2 Disk Utility Program version 1.14` title is
explicitly retained by specification sections 10–11. It is not a missing /VER
conversion: `/VER` prints the metadata-owned BetterCP/M DUP 1.0 Build 003 identity.

## Fresh focused qualification

Passed in this audit:

- `test_dup_command_line.py`: valid/invalid syntax, shared dispatch, one-shot
  return and standalone/combined version behavior.
- `test_dup_operations.py copy --direct`: Model 4 declined confirmation,
  destination binding restoration, successful copy and independent physical
  payload comparison, source/system preservation, CHECK and command return.
- `test_z80pack_dup_command_line.py`: declined FORMAT/COPY, protected FORMAT,
  successful copy payload equality and read-only CHECK.
- `test_z80pack_dup_format.py --direct`: complete uniform target formatting,
  erased-payload verification and command return.
- `test_z80pack_dup_format.py --unsupported --direct`: mixed-sector rejection
  without changing target bytes.

cpmsim checks use disposable copies derived from the current Build 011 qualified
System Disk, with startup disabled only in the fixture to prevent SUBMIT startup
writes from confounding the source-preservation assertion. The tested DUP is
installed explicitly; CONFIG and FDF are supplied for the mixed-format setup.
The initial older development-image runs are not counted as passing evidence.
No user's disks or release images were modified.

## Limits of this check

This is a source/contract audit plus focused regression qualification. It does
not repeat the full historical Model 4 mixed/error/interruption matrix, every
FORMAT topology or native build. Retained broader evidence remains in
[backend closure](202%20DUP%20Backend%20Capability%20Closure.md) and
[command-line qualification](DUP%20Command-Line%20Qualification.md). Final
exact-artifact release qualification is still required; no broader completion
claim is inferred from these focused passes.
