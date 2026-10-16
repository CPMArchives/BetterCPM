# Printer RSX prototype — 2026-10-16

## Result and scope

The isolated prototype demonstrates a compact optional printer transformation
payload behind a BIOS-owned binding. It is not installed in normal builds or
System Disks. No production ABI, specification semantics, or CONFIG behavior is
changed. Serial implementation is outside this printer prototype.

Run after the normal BIOS/BDOS builds:

```
python3 tools/prototype_printer_rsx.py
```

Sources are `tools/prototypes/printer-filter.mac` and the harness above.
Generated binaries, listings, experimental carrier and JSON measurements go to
ignored `build/audit/printer-prototype/`. The `.experimental` carrier is for
format and memory measurement, not a supported loadable printer extension.
The production manager does not yet recognize or bind PLST/PSET.

## Measured cost

| Component | Bytes |
| --- | ---: |
| BIOS gateway, raw jump, shared reset/publication store, binding word | 16 |
| Additional cold initialization CALL | 3 |
| Filter payload, including ordinary RSX chain header and settings service | 249 |
| Configuration and stream state within that payload | 6 |
| Two runtime callable descriptors | 20 |
| Rounded loaded module allocation | 512 |
| Experimental carrier including header/metadata | 797 |

The payload has 34 relocation words. The two illustrative services are PLST
(output) and PSET (inspect/update settings). PSET validates the complete tuple
before mutation and resets counters when applying a valid tuple. Its query
returns a private pointer usable only until a profile change; production CONFIG
must resolve again and should copy results rather than retain that pointer.

**19 permanent bytes is a primitive cost, not a complete integration quote.**
It excludes manager identity validation, target resolution, transaction
publication/rollback changes, raw-entry discovery and native ABI qualification.
It also excludes any new external BIOS descriptor/vector. The raw entry is a
fixed laboratory address, not a proposed public ABI. No BDOS modification was
needed for these tests.

The currently full Model 4 BIOS slot would overflow by 19 bytes if this primitive
were simply appended. Consequently the prototype does not yet establish 53K
whole-system fit. It identifies the minimum space-recovery target; manager costs
must also be measured before claiming integration fits. Optional allocation
reduces TPA by 512 bytes while loaded, in addition to the existing shared first-
RSX manager reserve where that reserve is not already present.

## Executed checks

The harness executes the existing built BDOS with laboratory BIOS binding code.
A deliberately destructive raw sink clobbers BC/DE/HL, checking preservation of
the filter's loop and stream state. Output transformations are observed through:

- direct BIOS LIST;
- BDOS Function 5;
- BDOS Function 2 printer echo;
- BDOS Function 9 printer echo.

Ten transformation cases cover raw byte passthrough across all 256 byte values,
CR/LF suppression, native controls, tab stops, simulated page advance, combined
modes, and page/tab widths of 1 and 255. Invalid mode/page/width updates leave
settings and counters unchanged.

Separate routing checks execute Model 4 BIOS routing, with only physical screen
output stubbed, and the assembled production cpmsim character-I/O include:
ordinary CRT console bypasses the filter, CON=LST passes through it exactly
once, and cpmsim LST=LPT emits at printer port 3. These are instruction-level
checks, not emulator boot or physical printer qualification.

An important finding is that Model 4 BIOCONOT jumps to the BIOLIST body rather
than through its public vector. A production implementation must retain
BIOLIST as the wrapper label and rename the raw body, so internal references
also enter the hook. The fixture retargets that internal jump in its private
memory image. Merely patching the public vector fails this routing test.

Lifecycle sequencing is exercised by the harness: detach to raw fallback, copy
live bytes and repair the carrier's relocation words, poison old storage,
publish the moved entry, and verify preserved column/settings state. It then
detaches and poisons the moved storage, verifying raw output after simulated
unload. This qualifies the primitive sequence, **not the production manager's
load/move/unload transactions**, failure rollback, interrupts or warm rebuild.

## Provisional semantics and limitations

These choices permit a bounded measurement; they are not newly frozen user
requirements:

- Mode bits select LF suppression, FF simulation and tab expansion independently.
- Page length and tab width accept 1..255; defaults are 66 and 8.
- CR counts one line and resets column. Immediately following LF does not count
  a second line, whether emitted in RAW mode or suppressed.
- LF without preceding CR counts one line but does not perform a carriage return.
- Simulated FF emits remaining page lines; at a page boundary it emits a full
  page. Generated LF/space bytes bypass filtering to avoid recursion.
- Columns wrap at 256; backspace and device-specific cursor controls do not
  update column state. Thus long lines or backspacing can produce incorrect tab
  stops. This bounded prototype is not yet the final tab implementation.
- Raw-output failure/readiness policy and LISTST integration are not qualified.
  State currently follows attempted output, with no success acknowledgment.

No new capabilities are advertised: this filter does not create a physical
printer backend or require one on a route that already emits output. Model 4
physical printer support, CONFIG persistence/startup loading and device
capability publication remain separate implementation work.

## Recommendation

The loaded cost is modest enough to continue. Next recover and measure space
for the permanent primitive, then extend the production manager using the
monitor binding's transaction discipline. Freeze counting/tab requirements and
qualify failed transactions, real profile reconstruction, both native builds
and fresh System Disks before enabling the feature. This prototype neither
completes the feature nor approves deferral.

## Scheduling decision — 2026-10-16

The maintainer has now deferred the printer RSX feature and CONFIG integration
to post-1.0. Earlier statements that no deferral was approved describe the audit
or prototype stage and are superseded for printer work. Preserve this evidence
for the [post-1.0 work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#printer-rsx-implementation-follow-up--2026-10-16).
The separate serial proposal remains undecided.
