# DUMP initial baseline qualification

Date: 2026-10-21. DUMP 1.0 Build 001 implements the
[initial DRI-compatible specification](DUMP%20Specification.md). The only
extension is standalone `/VER`, using the finalized visual identity. DU syntax,
ASCII columns, ranges, paging and other enhancements remain excluded.

## Artifact and build

`src/utilities/dump.mac` is native Z80/ZSM4 source. `tools/build_dump.py` emits
`build/utilities/DUMP.COM`; `tools/build_utilities.py` includes it in the command
collection. The Utilities disk has not yet been assembled. The System Disks,
BIOS, BDOS and CCP are unchanged.

- Length: 599 bytes, including the transient private stack.
- SHA-256: `9d2746c0134cf42073cada387823fed835b1dce41f58d2ae4177b59c865bac13`.
- Native `tools/build_native_dump.py` assembles with ZSM4 and links with DRI
  LINK under CP/M on disposable cpmsim disks: all 599 bytes match the cross build.
- Version/build are owned by `metadata/utility-versions.tsv`.
- Only the shared `/VER` recognizer is reused; DUMP restores its caller stack
  and returns directly for version/error/ordinary completion. It does not use
  the common warm-boot version wrapper.

## Executed checks

`tools/test_dump.py` passes 19 cases. It executes both the retained DRI binary
and the actual BetterCP/M binary against the same public BDOS fixture. The
fixture deliberately clobbers BC/DE/HL across services. It compares byte streams,
record consumption, status calls, drive-qualified FCB use and stack-balanced
return. Cases include empty input, one/multiple records, all byte values,
embedded 1Ah/final-record padding, missing input, 64K offset wrap, interruption
before the first/second line without consuming the key, nonzero read results,
case/space version requests, invalid mixed `/VER` forms, and longer non-version
tokens. Version requests call only string output and perform no file access.
These are controlled compiled-code checks, not real peripheral certification.

`tools/test_dump_live.py --baseline <V052-z80pack-directory>` passes on a private
copy of the accepted V052 image, SHA-256
`6823e809d2e52ab978bd37646b9f201ff3a074fc910fdd0ec1df780030e8fae2`.
It checks visual version output, exact 256-byte hex output, empty and missing
files, and A0:DUMP invoked from A3 against user-3 input. Caller user is preserved,
input payloads and the immutable reference image remain unchanged, and an
independent filesystem check passes. No user daily disk is modified.

The initial live harness used an undefined host disk-format name and stopped
before launching the guest. The corrected run uses the baseline's supplied
`bettercpm-default` disk definition. The native builder's initial import typo
likewise ran no guest build; the corrected native build passes. These are
harness attempts, not product defects or inferred passes.

Runner syntax and repository whitespace checks pass. A native Model 4 guest run
and final Utilities Disk acceptance remain separate qualification work; this
record does not extend prior core/System Disk acceptance to new artifacts.

## References and retained evidence

`third_party/dri-dump` retains the original DRI source/executable, hashes,
permission correspondence and provenance limits. The binary is the differential
oracle; source/binary build equivalence is not asserted. Neither historical
artifact is substituted for BetterCP/M's production implementation.

The durable archive is
`validation-evidence/BetterCPM-DUMP-Build001-evidence.tar.gz` in the local CP/M
project workspace, SHA-256
`71c0709f94423c5b4bdfd3535218135797ea17b0ffecd2b7a755ac05a47cab71`.
It retains runner/source copies, compiled outputs, native build transcript,
live transcript/private media, result records and excluded live harness attempt.
All archived files were reopened and matched to the included SHA-256 manifest.
