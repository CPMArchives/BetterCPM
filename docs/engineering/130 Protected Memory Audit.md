# 130 — Protected Memory Audit

Date: 2026-09-10  
Status: measured design input; no layout change

## Purpose

This audit classifies every byte from the live dynamic gateway at `D501h`
through the Model 4 usable-RAM ceiling at `F400h`. Its purpose is to measure
whether the planned core Persistent Data Segment can be built while retaining
the default 53 KiB TPA.

`src/system/layout.inc` and the current emitted binaries are authoritative.
The audited span is 7,935 bytes and accounts exactly:

| Class | Bytes |
| --- | ---: |
| Executable code | 5,308 |
| Immutable tables, descriptors and messages | 365 |
| Mutable state | 1,028 |
| Stacks and transfer workspaces | 1,224 |
| Alignment/ABI padding | 10 |
| **Total** | **7,935** |

The 192-byte command-history PDS and three-byte dynamic gateway are included.
The reclaimable CCP/CPX command environment below `D501h` is excluded.

## Exact region audit

| Range | Bytes | Current contents | Classification |
| --- | ---: | --- | --- |
| `F000h–F3FFh` | 1,024 | Physical-sector, module and CONFIG overlay | Workspace |
| `EF80h–EFFFh` | 128 | Directory transfer buffer | Workspace |
| `EF57h–EF7Fh` | 41 | Active RSX count, four names and service words | Mutable; future PDS |
| `ED17h–EF56h` | 576 | Four live DPH/binding records, shared ALV and four CSVs | Mutable; future PDS |
| `EC86h–ED16h` | 145 | Protected file loader | 103 code, 6 immutable, 36 mutable FCB |
| `EA08h–EC85h` | 638 | BIOS and Model 4 platform support | 548 code, 74 immutable, 16 mutable |
| `E648h–EA07h` | 960 | Disk mapping, controller and drive definitions | 909 code, 16 immutable, 35 mutable |
| `E49Fh–E647h` | 425 | Extension controls, adapters and version service | 277 code, 143 immutable, 5 mutable |
| `D6BCh–E49Eh` | 3,555 | Unified BDOS slot | detailed below |
| `D5C4h–D6BBh` | 248 | Fixed system gateway and control data | detailed below |
| `D504h–D5C3h` | 192 | Current packed command history | Mutable; current PDS |
| `D501h–D503h` | 3 | Dynamic CP/M gateway | Executable code |

## Unified BDOS slot

The 3,555-byte BDOS slot contains a 3,548-byte binary and seven unused bytes:

| Range | Bytes | Contents | Classification |
| --- | ---: | --- | --- |
| `D6BCh–E42Ah` | 3,439 | Dispatcher and BDOS implementation | 3,316 code; 82-byte dispatch table and 41 bytes of messages |
| `E42Bh–E46Fh` | 69 | BDOS variables and cached filesystem context | Mutable state |
| `E470h–E497h` | 40 | Private BDOS stack | Workspace |
| `E498h–E49Eh` | 7 | Unused slot tail | Reclaimable padding |

The mutable tail includes current drive/user/DMA, login and read-only vectors,
cached DPH/DPB/ALV pointers and DPB fields, directory iterator/cache state,
random/sequential I/O scratch, console column/list state, and the current
one-byte pending input mechanism. Some fields must survive ordinary calls or
WBOOT; others are call-local scratch. The final PDS design must separate those
lifetimes rather than moving all 69 bytes indiscriminately.

Moving this state into the PDS improves ROMability and ownership, but is mostly
memory-neutral: bytes removed from the BDOS allocation reappear in the PDS.
Only the seven-byte slot tail is immediately recoverable.

## Fixed system gateway

The 248-byte system region is fully emitted:

| Contents | Bytes | Classification |
| --- | ---: | --- |
| Entry, WBOOT, COM handoff and initialization routines | 152 | Code |
| Fixed-position fill | 3 | ABI padding |
| System stack | 32 | Workspace |
| ECB magic and version | 3 | Immutable descriptor |
| Live ECB fields | 17 | Fixed mutable control block |
| CPX count, flags and filename reconstruction storage | 41 | Mutable; future PDS |

The ECB must remain reachable through a stable gateway, but the active CPX
profile belongs in the PDS. Its relocation saves no net RAM. The current CPX
table reservation should be replaced by a versioned capacity rather than
preserved as an accidental fixed layout.

## Other component detail

The extension region's 143 immutable bytes are primarily the version descriptor
and printable subsystem names/versions. A smaller numeric resident descriptor
with formatting in `SYSINFO.COM` could plausibly recover roughly 80–110 bytes
without removing version discovery.

The disk region contains 24 bytes of mutable physical-drive definitions and 11
bytes of controller/session state. The separate 576-byte table region is all
live writable data: four 80-byte DPH/binding/format records, a 128-byte ALV and
four 32-byte CSVs. Moving it into the PDS is required for the preferred ROMable
design, but does not itself change the total RAM cost. Normalizing repeated
fields and separating DPHs, format records and bindings may reduce the default
four-drive footprint while still permitting every configured drive to use a
different format.

The BIOS contains 56 bytes of immutable keyboard translation data, 18 bytes of
immutable reload-sector tables, 12 bytes of disk-selection state and four bytes
of console state. The protected file loader's 36-byte FCB is scratch storage,
not persistent configuration.

The 1,024-byte top workspace has two distinct peak uses. Ordinary disk I/O
needs one 512-byte physical-sector buffer. Command/extension reconstruction and
the CONFIG overlay can use the full kilobyte. The upper 512 bytes are therefore
the strongest recovery candidate: reconstruction already occurs while the
command environment is disposable, so a redesigned loader may borrow suitable
TPA or overlay storage instead of reserving the second half permanently. RSX
loading from a running transient requires an explicit non-overlap plan before
this saving can be claimed.

## Revised PDS ownership and sizing consequence

The architectural review following this audit changed the ownership model.
Optional feature data is no longer budgeted into the base PDS merely because it
must survive transient execution. HISTORY.RSX owns command records and NDR.RSX
owns the live named-directory register. Security and batch/flow state are likely
to belong to their implementing resident modules, subject to their individual
designs. The PDS retains only core state and small reconstruction/service-
discovery records.

The current 192-byte PDS is entirely command-history state. Moving history into
HISTORY.RSX therefore removes those 192 bytes from the base inventory; it must
not be counted as an existing contribution toward the new base PDS.

Using current measured structures, a four-drive base is approximately:

| Base PDS item | Planning bytes |
| --- | ---: |
| Four drive records, shared ALV, four CSVs, physical definitions and disk session state | 623 |
| Search path | up to 64 |
| Current RSX and CPX reconstruction records | 82 |
| Descriptor and allocator metadata | 48-64 |
| Core settings | 24-32 |
| **Subtotal before alignment/reserve** | **841-865** |

This leaves 159-183 bytes in a 1,024-byte profile. That is sufficient to make
1 KiB a credible constrained target, but the margin must also absorb registry
generation/descriptor state, alignment and ABI evolution. A 1.25 KiB
default is therefore the preferred planning target; 1.5 KiB remains the
fallback if concrete version-1 layouts exhaust the smaller budget.

The service registry keeps only its descriptor and generation in the PDS.
Validated service advertisements are materialized in loader-owned storage inside
each provider's RSX allocation, so installed services do not create a flat PDS
table. Bulk feature state also remains in its RSX.

The accepted TIME provider ABI removes canonical current time and provider
binding from the base PDS. Hardware-backed providers read their authoritative
clock on demand and are discovered through the resident-service registry. A
software-maintained clock owns its state inside its stateful RSX.

Drive count remains the principal configurable PDS cost. With the current
shared 128-byte ALV, the measured model is `118*N + 151` bytes: 623 bytes for
four drives, 1,095 for eight and 2,039 for sixteen. If every drive instead owns
a fixed 128-byte ALV, the model is `246*N + 23`: 1,007, 1,991 and 3,959 bytes.
Geometry-sized ALVs and normalized records should reduce the latter cost. A
larger drive profile therefore selects a larger PDS and accepts less TPA.

Several base allocations replace existing mutable allocations rather than add
wholly new memory: CPX and RSX tables, drive tables, portions of BDOS/BIOS
session state and descriptor live-layout fields. Relocation improves ROMability
and ownership but saves RAM only when the old allocation disappears or the new
representation is smaller.

Immediately visible recovery is smaller:

| Candidate | Plausible recovery |
| --- | ---: |
| Second half of permanent module/physical buffer | up to 512 bytes |
| Compact resident version metadata | roughly 80–110 bytes |
| Existing fixed padding | 10 bytes |
| Normalize four-drive records | unknown; measure after defining records |
| File-loader and reconstruction scratch overlays | tens of bytes |

Preserving 53 KiB is therefore realistic, but not yet proved. The first
approximately 600 bytes have credible recovery paths. The remaining few hundred
bytes require a concrete PDS ABI, normalized drive structures, lifetime-based
workspace overlays, and probably modest code compaction. Merely moving mutable
objects into a contiguous PDS cannot be counted as a saving.

## Required next measurements

1. Define the version-1 PDS descriptor and every default allocation record.
2. Give PATH, disk state, service-registry descriptor, CPX and RSX records explicit
   capacities and byte layouts; size optional feature data within its RSX.
3. Separate persistent BDOS state from call-local scratch.
4. Normalize the live DPH, format and logical/physical binding structures and
   measure four- and sixteen-drive profiles.
5. Prove whether the upper 512-byte module workspace can be borrowed safely for
   WBOOT reconstruction, runtime RSX loading and CONFIG operations.
6. Rebuild and publish an exact default memory map; acceptance requires at
   least 54,272 loadable bytes, preserving the 53 KiB COM ceiling.
