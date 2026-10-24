# NOAH LBR integrity and extraction increment

This follows the [reader foundation](../programmers/Archive%20Read%20Library.md).
Build 002 is recorded here; the later [selector/overwrite increment](NOAH%20Selectors%20and%20Overwrite.md) extends its command scope.
It implements another bounded part of the [NOAH specification](NOAH%20Specification.md),
not full release conformance. NOAH remains a development command outside the
Utilities Disk build. No resident code, BIOS/BDOS service or TPA boundary changes.

## Implemented command scope

```text
NOAH [/LIST] [drive:]archive
NOAH /TEST [drive:]archive
NOAH /T [drive:]archive
NOAH /EXTRACT [drive:]archive [destination-drive:]
NOAH /X [drive:]archive [destination-drive:]
```

One exact archive, current user area, all active members. Destination defaults to
logged drive/current user, not the archive's drive. `/VER` and `/HELP` ignore other arguments; `/HELP` takes precedence. Existing outputs are explicitly reported/skipped; overwrite prompts,
`/Y`, `/R`, `/SYS`, member filters and full DU/batch selectors are not implemented
in this increment. Unsupported forms are rejected before archive I/O. Their final
specified behavior is unchanged; the current development subset is not a silent
replacement for that contract.

## Integrity library

Include `lbraudit.inc` / `lbraudit.mac` after `archive.inc` / `lbr.mac`; emit
`LBR_AUDIT_CODE` once after `LBR_CODE`. `LBR_AUDIT` takes IX=the configured LBR
context and IY=224 bytes of separate caller-owned audit workspace. Both pointers,
the alternate bank and SP are preserved. Normal primary scratch registers may
change. Workspace/context/code must not overlap. The audit uses the reader's
callback; it owns no file handle and performs no screen or disk write operations.

The audit restarts library state, validates each active entry using the reader,
then checks case-normalized duplicate names and pairwise overlaps of physical
member extents. Empty members have no occupied extent. Deleted entries are opaque
and excluded. No whole-directory allocation is required: enumeration order is
retained and earlier entries are reread for comparisons. Directory reads are
quadratic in active member count; performance on large libraries remains a
qualification gate, not a constant-time claim.

CRC uses XMODEM/CCITT polynomial 1021h, initial zero, no reflection/final XOR.
Directory coverage is every directory byte with control-entry CRC bytes 16–17
zeroed. Member coverage includes every stored byte, including explicit padding.
Nonzero recorded CRC mismatch returns `AS_CHECK`. Duplicate names and overlaps
return `AS_DUPLICATE` and `AS_OVERLAP`. Read/truncation errors remain distinct.
All are sticky library errors until CLOSE or OPEN.

Zero recorded CRC is inherently ambiguous: it can indicate an omitted CRC or a
mathematically zero CRC. It is counted as unavailable/ambiguous, never fabricated
as a verified checksum or treated as corruption solely for being zero. The audit
still reads that member's entire physical extent. `LA_CHECKED` and `LA_UNCHECKED`
are 32-bit counts including the directory. NC means structural/readability checks
and all advertised nonzero CRC comparisons completed; callers must inspect/report
coverage before calling the result a full checksum pass. Old archives with garbage
nonzero directory CRCs are conservatively rejected by the current audit; historical
compatibility fixtures/policy qualification remain pending before release.

`LBR_CRC16` is also callable: HL=bytes, BC=count, DE=initial value, DE=result.
It supports incremental calculations and zero-length spans. Include definitions
are authoritative for layouts and error values. Timestamp words remain raw LUDEF
metadata; no inner compressed-file format is decoded by LBR TEST.

## Extraction transaction

1. Audit the whole archive before any MAKE. Report overall CRC coverage; report
   each member's ambiguous/unavailable CRC as applicable.
2. For each member, reject an existing destination by reporting a skip. This
   protects ordinary/protected files and the source archive itself.
3. Search 00–99 using the first six basename characters, or the full shorter
   basename, plus two digits. Both TMP and BAK must be absent in the destination
   DU and neither name may equal the final output. Preexisting recovery files
   are not modified. CP/M single-task search/MAKE semantics are assumed; no
   exclusive-create or power-failure atomicity is claimed.
4. MAKE only the selected TMP. Stream logical member bytes in bounded chunks;
   explicit LUDEF padding is omitted, and a partial CP/M output record is filled
   with 1Ah. Real 1Ah inside logical member content is preserved. Empty members
   create zero-record files.
5. Close TMP, reopen it through a separate FCB, restart the selected source member
   and compare all output records byte-for-byte against a second source read,
   including required output padding. Require physical EOF immediately after
   the expected output records. This compares the intended source to readback,
   not a temporary file's checksum against itself. It is not a source locking or
   malicious concurrent-change guarantee; further source-stability qualification
   remains part of full NOAH acceptance.
6. Close verification input, check cancellation, recheck final absence, then
   rename the verified TMP. No original target is renamed/deleted in this subset.
   Publication failure or a newly appearing target retains/reports the verified
   TMP; the existing target remains untouched.

On write, readback or verification failure, close and delete only the temporary
created by this operation. A cleanup close/delete failure preserves/reports the
remaining TMP name. No other recovery file is commandeered. Stop after a member
failure and account remaining members as unprocessed; Retry/Skip/Abort interaction
is a future integration gate. Completed earlier outputs remain completed.

Ctrl-C is polled at archive read boundaries (including preflight), before member
work, between write/verification chunks and immediately before publication.
Cancellation cleans partial staging and reports cancellation/unprocessed work.
No poll interrupts the final rename operation. The CLI wrapper tracks cancellation
separately from ordinary callback I/O failure; the reusable audit has no console
dependency. Invalid command forms, bad preflight and preflight cancellation create
no output files.

New outputs use ordinary CP/M writable/non-system creation. The existing OS's ARC
behavior is retained; sources are unchanged. `AC_GET_STAMP` / `AC_SET_STAMP` return
C/`AS_UNSUPPORTED` with no mutation because this CP/M 2.2 adapter has no filesystem
timestamp API. When a member advertises timestamp data, extraction explicitly
reports that it was not restored. These are unsupported capability results, not
dummy success calls. Raw archive dates are preserved; no current date is invented.

## Checks and limits

```text
python3 tools/test_lbr.py
python3 tools/test_noah.py
python3 tools/test_noah_cpm.py
```

The full Z80-core harness tests real assembled code with an independent Python
LUDEF fixture writer and Python `binascii.crc_hqx` CRC oracle. It checks corruption
in directory/data/pad bytes, duplicate names, overlaps, missing CRC coverage,
register/context guards, immutable code and callbacks that destroy scratch
registers. Extraction fault cases include partial writes, reopening/readback
failure, modified/truncated/extended temporaries, close failures, late target
appearance, rename/cleanup failure, namespace exhaustion and controlled Ctrl-C.
Input and preexisting recovery-file contents are independently checked afterward.
Builds are deterministic.

The separate stock CP/M 2.2 smoke uses private copies of emulator disks and checks
outputs afterward through cpmtools. Seven commands cover TEST, extraction,
collisions, CRC rejection, empty files, sequential extent rollover and >64K binary
content. It exposed and fixed an adapter error: DRI function 35 has no defined
accumulator result. The adapter now clears R0–R2 and consumes the FCB result;
a missing result cannot describe a valid nonempty LBR directory. The fault harness
also returns FFh on successful function 35 to prevent that assumption recurring.

This is stock CP/M execution on cpmsim, not BetterCP/M or native Model 4 release
qualification. Native ZSM4 expansion, BetterCP/M platform runs, independent
historical LBR artifacts/tools, early garbage-CRC compatibility, full metadata,
overwrite/protection/recovery UI, selectors, ARK, compression integration, archive
updates and NOAH.OVL remain pending. The overall specification and the archive
library's future capability/write interfaces are not declared complete.

Current measurements: 1,560 reader/audit code bytes, 138-byte reader context,
224-byte audit workspace and 7,060-byte NOAH.COM (Build 003). Maximum observed
command-stack use is 30 bytes with BDOS intercepted; native BDOS/BIOS stack
qualification remains separate. The machine-readable [check record](NOAH-LBR-Integrity-Extraction-Checks.json)
retains source/binary hashes and coverage accounting.

After integration with the common query contract, all 123 library cases,
90 command/adapter cases and seven stock CP/M commands pass for Build 003.
The build-number table preserves main’s existing compression Build 004 entries.
