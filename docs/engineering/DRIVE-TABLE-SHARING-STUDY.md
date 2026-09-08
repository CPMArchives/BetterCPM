# Drive-table sharing study

2026-09-08. Source inspection and storage estimates, not an implemented layout.

Subsequent decision: prefer independent format records for 1.0, budgeting
for every configured drive to have a distinct format. The sharing proposal
below is retained as analysis, not the selected implementation. See
[CONFIG startup decisions](CONFIG-STARTUP-SETTINGS-DECISIONS.md).

## Existing storage

`src/bios/tables.mac` allocates four 80-byte records: a 16-byte DPH followed
by a 64-byte binding. Binding byte 0 is the physical-device number; bytes
1–63 describe the format, including the DPB, geometry, sector IDs, mixed-size
map and three reserved bytes. B–D have identical format bytes. A differs.
There is one shared 128-byte ALV and four independent 32-byte CSVs.
`src/bios/disk.mac` supplies four six-byte physical records. Total: 600 bytes.

BDOS already copies only the active DPB into its working context and rebuilds
the shared ALV on a logical-drive context switch. Sharing the ALV saves memory
but can require a directory scan when switching drives. This behavior is not
an additional saving available from the proposed change.

## Candidate layout

- Fixed A–P pointer index: 32 bytes.
- Each configured logical drive: 16-byte DPH, one physical-device byte and
  a two-byte format pointer: 19 bytes.
- Each distinct format: 63 bytes, retaining today's fields and reserved bytes.
- Each drive: independent CSV sized by DPB CKS.
- Shared ALV: at least ceil((maximum DSM + 1)/8) bytes across allowed formats.
- Physical records: currently six bytes each; future non-floppy drivers need
  their own state and are not priced by this floppy-specific number.

Formula: 32 + 19*N + 63*F + sum(CKS) + ALV capacity + 6*P.
N=configured logical drives, F=distinct formats, P=physical floppy records.
No pool-management metadata, new instructions, alignment or scratch space is
included: this is a payload estimate, not a promised net TPA saving.

| Logical drives | Distinct formats | Physical records | Current layout plus index | Shared-format payload |
| --- | --- | --- | --- | --- |
| 4 | 2 | 4 | 632 | 514 |
| 8 | 2 | 4 | 1080 | 718 |
| 16 | 2 | 4 | 1976 | 1126 |
| 16 | 2 | 16 | 2048 | 1198 |
| 16 | 16 | 16 | 2048 | 2080 |

All rows retain 32 CSV bytes per drive and 128 shared ALV bytes. These match
current provisioned capacity, not an arbitrary large-disk implementation.
The four-drive candidate saves 86 bytes against today's actual 600 bytes,
after adding the new index. Sharing every-unique formats loses 32 bytes
against the indexed unshared layout because of the extra format pointers.

## Which data can share

Format parameters can share only while treated as immutable. CONFIG changing
one logical drive must locate or create another format record and repoint
that drive; it must never edit a record still used by another drive. Scan
registered drives to find references rather than necessarily keeping a second
reference-count table. Reclaim a format only when no drive references it.

DPHs contain per-drive scratch and state pointers and remain independent.
CSVs describe directory contents, not format identity; equal formats or
physical aliases do not justify sharing them. A fixed-media format with CKS=0
needs no CSV, but removable SD media must not automatically be classified as
fixed merely because the transport resembles a hard disk.

The current default DSM values 389 and 399 require 49 and 50 ALV bytes;
50 would cover the defaults. Retaining 128 supports the current 1024-block
limit and avoids silently losing CONFIG format choices. Supporting all allowed
CKS values requires capacity for them, even if cold-boot defaults use less.
Exact-sized pools must either have spare capacity, a supported resize path,
or reject a reconfiguration cleanly. Default-only measurements must not be
presented as full-capability memory requirements.

## Integration required before implementation

`DC_LOG` currently indexes four records with an 80-byte stride. BIOS physical
validation and binding update/read paths also assume that stride and inline
64-byte bindings. CONFIG, DUP and FDF interfaces use these binding fields.
Keep a decoded binding request interface if useful, synthesizing it from the
new internal representation, but version the discovery descriptor whose
exposed table layout would change. `tools/sysgen_image.py` and SYSGEN tests
recognize ABI 5 and the old layout: persistence must serialize definitions
and rebuild pointers at cold boot, not save accidental runtime addresses.

Recommendation: use the full sparse A–P index and investigate a shared,
immutable format pool with independent drive state. Retain the existing ALV
capacity until a separate capacity policy is agreed. Measure new code and
pool overhead before adopting it; a small four-drive system has only an
86-byte gross margin, whereas sixteen drives sharing two formats has a much
larger margin. Runtime driver loading is outside this study and remains
post-1.0 work.
