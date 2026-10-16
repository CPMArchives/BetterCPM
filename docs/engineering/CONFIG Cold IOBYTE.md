# CONFIG disk-boot IOBYTE — Build 011

## Supported behavior

The maintainer approved patching the existing cold-store operand rather than
adding resident initialization logic. Menu K and standalone `/IOBYTE=decimal`
confirm and save this setting immediately. STAT remains the live interface.
`/SHOW` prints separate live and saved disk-boot values. `/DEFAULT` remains
startup-command-only. Printer transformations and serial configuration remain
open proposals; this implementation does not defer them.

Decimal 85 is 55h (CRT/PTR/PTP/CRT); decimal 149 is the compiled 95h
(CRT/PTR/PTP/LPT). CON must remain CRT. Changed routes require the running
platform's advertised endpoint; unchanged placeholder routes are preserved.
149 explicitly restores compiled factory routes without claiming that each
placeholder is a working physical device. Malformed requests fail before INIT.

## Operand ownership and metadata

`IO_COLD` labels the existing `LD A,095H` in Model 4 stage one and cpmsim
PL_INIT. Labels add no bytes. The builder takes the operand's address from the
assembly listing and checks the exact instruction pair `3E 95 32 03 00`.
It does not search an image for a byte or guess an offset.

Each descriptor contains ten bytes:

| Offset | Size | Meaning |
| --- | --- | --- |
| 0 | 2 | Qualified logical records per track, little endian |
| 2 | 1 | Absolute protected logical record number |
| 3 | 1 | Operand offset within its 128-byte record |
| 4 | 2 | Operand offset in the resident carrier, or FFFFh for stage one |
| 6 | 4 | CRC-32/ISO-HDLC of the original containing record |

A zero records-per-track word ends the table. Ambiguous geometry descriptors,
missing/duplicate symbols, instruction changes and out-of-record operands fail
the build. The two existing qualified profiles have distinct geometries. This
is a private transient build contract, not a BIOS/BDOS ABI extension.

Distribution qualification independently computes the descriptor from installed
bytes and build symbols and requires exactly one matching descriptor in CONFIG.
The core carrier's existing 20-byte validation descriptors remain unchanged.

## Validation and writes

Read and retain the original record. Validate CON=CRT in its stored value,
normalize only the operand to compiled 95h in a private copy, and check the
whole record's CRC against the build descriptor. Check selected routes against
the character capability query before asking for Y/N. No failure before Y
writes the disk or changes live IOBYTE.

After confirmation, change only the operand, write its record, then compare all
128 bytes on readback. An ordinary failure restores and verifies the original
record; a failed restoration reports possible damage. This is not power-loss
atomic. Physical-sector read/modify/write remains the existing BIOS operation.
A power failure may require another boot disk or reconstruction of the image.

CONFIG save-all preserves the saved operand. For cpmsim, immutable-carrier CRC
validation normalizes that one operand to 95h and checks its console selection;
it restores the original carrier before merging active settings. Model 4's
operand is outside that carrier. Other bytes are not newly excluded from CRC.

SYSGEN already copies installed loaders and carrier payloads; its existing
binding patches do not target this operand. A package retains the value embedded
in its payload. Fresh builds still compile 95h; this is not the later planned
SYSGEN disk-to-package export feature.

## Boot profiles and limits

This setting applies to the disk's existing cold-entry instructions. Warm boot,
COM return and RSX reconstruction preserve live IOBYTE. Saving never changes
address 0003h in the current session.

An immutable ROM initializes from its own firmware. CONFIG does not rewrite ROM
and must not imply a saved disk byte alters that firmware. Rebuild a ROM to
change its compiled default. The patch is qualified for the current disk-boot
profiles, not unknown platforms or arbitrarily changed boot geometries; unknown
records/builds are refused.

Keeping CON=CRT avoids a configurable unusable-console route on the qualified
platforms. This is validation, not a new recovery gesture or firmware fallback.

## Transient memory

Private CONFIG buffers are moved from program storage into A800h–ABDFh:

| Range | Owner |
| --- | --- |
| A800h–A87Eh | Command text, or mutually exclusive edit-parser scratch |
| A880h–A97Fh | Saved logical bindings for /SHOW |
| A980h–A997h | Saved physical profiles for /SHOW |
| A9A0h–AA9Fh | Pending startup record |
| AAA0h–AADFh | Private format-workbench binding |
| AAE0h–AB5Fh | Submitted-command test buffer |
| AB60h–ABDFh | Counted startup-command input; initialized before use |

These do not overlap the catalogue, save/rollback buffers, track stream or
3E00h–3FFFh stack. The entry guard requires a BDOS boundary at or above AC00h
(43K address-space requirement); identity requests still return before it.
No system layout, loaded RSX policy, or 53K unloaded TPA boundary changes.
Final dual-profile CONFIG is 15,450 bytes, leaving 166 below its 3D00h-byte cap.
DUP remains byte-identical to its preceding build.

## Qualification

- `test_iobyte_config_metadata.py`: symbol/encoding/range checks, ambiguity,
  independent distribution descriptor gate and disjoint scratch spans.
- `test_config_iobyte.py`: parsing before I/O, memory boundary, CRC/read/capability
  rejection, factory restoration, exact-byte writes, declined save, write and
  readback failures, verified rollback and reported rollback failure.
- Native ZSM4/LINK matches the cross-assembled dual-profile binary.
- `test_config_save_all.py` passes Model 4 combined active/pending saves,
  cold inspection and recoverable-write rollback after scratch relocation;
  evidence: `build/test-results/config-save-all`.
- cpmsim: `build/config-iobyte/run-upikfs6j`; saved byte changes alone, live and
  active drive state are preserved, cold and subsequent warm boots retain the
  new byte, /SHOW remains CRC-valid, save-all preserves it, and menu K shares
  the save path. Corruption and decline leave the whole image unchanged.
- Model 4: `build/test-results/config-iobyte-model4/run-nljsllcn`; real keyboard
  invocation changes exactly logical disk byte 513, leaves live IOBYTE at 95h,
  and an actual next cold boot runs a probe expecting 55h without another write.

Focused qualification is separate from final release validation. Fresh System
Disk evidence is recorded in the CONFIG alignment ledger.
