# Engineering Specification 121: Runtime Subsystem Version Reporting

Status: implemented

`VER` remains the concise release query and prints `BetterCP/M 0.3`. `VER /V`
prints that release followed by the identity, API version, and implementation
version of the fixed CCP, BDOS, and BIOS components. CPX and RSX facility
versions belong to their respective managers and are reported by `CPX /V` and
`RSX /V`, not by the system-level command. The same VER implementation supplies
the resident `BASIC.CPX` command and ordinary `VER.COM` fallback.

## Single source of truth

`metadata/subsystem-versions.tsv` is authoritative. The generator
`tools/version_metadata.py` converts fixed-component rows into the
ZSM4-compatible `src/bdos/versions.inc` and generates manager-owned CPX/RSX
version strings from their respective rows. The version regression test compares
the checked-in include byte-for-byte with freshly rendered output, so a matrix
change cannot silently leave runtime reporting stale.

No version table is maintained in BASIC.CPX. BetterCP/M Function 206 returns
the protected descriptor address in `HL`; the command validates its `BV`
magic and format version before formatting its pointer-based records. String
pointers allow future patch numbers and development suffixes without changing
the descriptor format.

## Interface version

Function 206 is a backward-compatible BDOS interface addition. The BDOS API
and implementation versions therefore advance together from 1.0 to 1.1. The
current `BASIC.CPX` module advances from 0.1 to 0.2; the BCPX facility ABI
itself remains 1.0.

## Verification

- generated metadata matches the TSV matrix;
- native ZSM4 and host builds produce byte-identical BDOS and BASIC payloads;
- the BCPX v1 relocation directory remains within its fixed 512-byte header;
- physical `trs80gp` runs verify concise and verbose resident output and the
  transient verbose fallback.
