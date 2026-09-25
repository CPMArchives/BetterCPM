# Stage 4 disk-state source audit

## Status

This audit records the source evidence used to adopt Architecture Specification
28. It distinguishes current implementation from the accepted 1.0 contract;
it is not itself a claim that the later FDB and expanded CONFIG persistence work
is already implemented.

## Current active representation

`src/bios/tables.mac` supplies four 80-byte logical records. Each consists of a
16-byte DPH followed by a complete 64-byte normalized binding. `DC_LOG` in
`src/bios/disk.mac` locates them with that stride. Physical configuration uses
four six-byte records. These BIOS-owned records are the current active authority.

The Model 4 and z80pack setters validate a complete logical request before
copying its 64 bytes into the selected binding. CONFIG's format workbench edits
`EDCOPY` and calls the setter only when the operator applies the record. CONFIG
and the BIOS invalidate disk context after a successful replacement.

No active FDB pointer or stable FDB identity exists in these records today.
The current utility path parses the historical `DISK.FDF` text into transient
`BIND` storage and copies normalized bytes into the BIOS. The production FDB
compiler and reader remain implementation work.

## Physical changes and capability removal

CONFIG currently applies an accepted physical field and then scans B through D.
`PHCLEAN` explicitly unconfigures bindings which no longer fit the physical
track/side limits and displays an invalidation message. Drive A is protected.
This is a deliberate physical-first workflow, so Architecture Specification 28
permits confirmed explicit invalidation rather than requiring every such change
to be rejected.

FDF.RSX intercepts its managed unload, selects A, detaches dependent B-D aliases,
invalidates disk state and only then leaves the chain. This supplies the general
rule that capability removal must either fail or detach all dependencies before
the provider disappears.

## Alias and filesystem invalidation

Multiple logical records may name one physical slot. `DC_RESET` conservatively
invokes BDOS Function 37 with `FFFFh`, invalidating every logical context. CONFIG
also has a one-drive reset path after a logical replacement. Exact invalidation
is optional; correctness requires at least every logical alias of the changed
slot and all filesystem state derived from a replaced binding.

## CONFIG H persistence

CONFIG H currently invokes the included save-current-configuration implementation
in `src/utilities/disk/sysgen.inc`. It:

1. loads and validates build-matched `A:SYSGEN.DAT`;
2. reads the installed system records;
3. merges only the editable physical and 64-byte logical binding bytes;
4. obtains live records through the public disk-control API;
5. writes only changed 128-byte system records;
6. rereads each record and verifies it; and
7. attempts to restore the original records after an ordinary write/verify
   failure.

The source explicitly states that this rollback does not protect against loss
of power. Architecture Specification 28 preserves the implemented verified-write
contract and defers redundant-slot or journal design.

The broader two-scope CONFIG H design remains unimplemented. It must preserve
saved defaults separately from temporary active settings and must not be
implemented by dumping all live RAM.

## Bootstrapping and FDB provenance

`SYSGEN` patches the destination's physical-drive-zero record and complete A:
binding into the installed system package. The bootstrap copy changes the
double-sided logical-track representation where required. This proves that the
boot binding must remain self-contained: BetterCP/M cannot resolve A:'s format
from a catalogue stored in A:'s filesystem before it can read that filesystem.

FDB v1 specifies an eight-byte descriptor ID and a whole-file CRC. It does not
yet specify a per-descriptor semantic revision or fingerprint. The whole-file
CRC is unsuitable because changing an unrelated format changes it. The FDB
implementation specification must define a canonical per-descriptor fingerprint
covering the descriptor and every referenced semantic extension if provenance
checking is implemented.

That provenance is diagnostic. A missing or changed catalogue entry does not
invalidate an independently valid installed binding. Explicit CONFIG migration
is the only operation that replaces its semantics.

## DUP and SYSGEN

DUP obtains complete bindings through the disk-control API and keeps private
copies while formatting or copying. It validates hardware and format support
before confirmation and destructive I/O and restores temporary bindings on
exit. SYSGEN obtains the destination through the same API and separately checks
the reserved system area before writing.

Because CP/M runs one transient at a time, CONFIG cannot alter the binding while
DUP or SYSGEN is executing. A publication-generation freshness check would add
state without closing a real race. The utilities instead validate their private
copies immediately before the first write.

## Accepted corrections to the original handoff

The repository audit made these changes to the Chat-produced proposal:

- normalized bindings remain operational authority; FDB identity is provenance;
- synchronous validated record transitions replace publication generations;
- physical edits may explicitly unconfigure confirmed non-system dependencies;
- managed capability removal may explicitly detach dependent bindings;
- CONFIG H promises verified rollback for ordinary errors, not power-loss
  atomicity; and
- configuration source remains a conceptual domain without a duplicate resident
  session-intent copy.

These corrections retain the original separation among configuration source,
active state and observed state while fitting the actual 1.0 execution model and
53 KiB TPA constraint.

## Implementation consequences

Later FDF/FDB and CONFIG work shall:

- compile and read FDB v1 without making the catalogue resident;
- create complete self-contained normalized bindings;
- define optional ID/fingerprint provenance without making it a boot dependency;
- preserve platform scope in installed settings;
- validate every affected record before an externally visible update;
- invalidate every alias and derived filesystem object affected by the update;
- retain the two CONFIG H save scopes without duplicating active disk intent in
  permanent RAM; and
- document recovery from interrupted installed-system writes without claiming
  power-failure atomicity.

