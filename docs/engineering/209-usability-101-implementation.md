# FDB 1.01 usability implementation

Branch: `feature/fdb-101-usability`, based on main `6db135a8` (PR #618).
**Acceptance status: pending Model 4 interactive qualification.** Host tests,
cpmsim interactive/query/round-trip and Model 4 query/round-trip pass. The Mac
is locked; computer-use inspection of the stalled interactive emulator is
unavailable. Timed boot diagnostics are retained, without claiming a native
interactive pass. PR #619 remains draft until that gate passes.

This implements FDU-01–10 from [the review backlog](209-usability-101.md).
The shipped 1.0 media, six frozen ZIPs, component baselines and release records
are preserved. No tagging, publication or promotion is part of this work.

## Behavior

- Maps accept comma/less-than and period/greater-than with the standard prompt,
  inclusive range and total. Navigation stops at the last relevant chunk;
  comparison retains one-sided slots. Empty difference chunks are identified,
  including the final partial chunk of a 255-slot map.
- Invalid choices and missing IDs retry locally. A failed second comparison
  selection retains the first. Input has a separate echo line, a 32-character
  ceiling, bell on excess input, working Backspace/DEL, and BREAK/ESC cancellation.
- Filename prompts accept the displayed DU form only for the current user.
  No user-area switch is performed. Ordinary drive prefixes and names such as
  `A1.FDB` remain valid. Untitled requires a name; named saves show the default.
- Numeric edits show the selected field/current value and accepted range/base.
  Validation identifies block/extent, numbering, directory and allocation rules;
  SPT and DSM geometry mismatches show current/expected or allowed maximum and
  page-3 correction fields. Edits remain staged; validation does not repair them.
- Viewer failures distinguish unavailable from mismatched/damaged pairs. File
  errors identify the object. Recovery paths name destination, backup and temp,
  distinguish pre-existing recovery files and preserve them.
- Pending editor work, the RAM catalogue, disk writes and active-drive changes
  are distinct. Apply confirmation shows the logical and physical target,
  current/proposed runtime SPT and working identity. It explicitly limits the
  operation to the active binding. A remains protected; B–D retain physical
  selectors; cancellation leaves the entire public binding/configuration state
  unchanged.

## Memory and compatibility

The standard interactive requirement stays 53 KiB, with the original 512-byte
private stack, 1300-byte source line and 255-slot maps. Entry-only queries run
in the normal Model 4 50 KiB configuration. COM and OVL remain a matched pair.

The resident block ends at `35F7h`; relocated editor ends at `D3F1h`. The viewer
is 4736 bytes at `A500h`, ending at `B780h`; its final EOF-read record remains
below `B800h`. The builder rejects a viewer that encroaches on that record.
Sector-size parsing uses dedicated scratch at `B800h` for a session or `C700h`
for conversion, so later text lines cannot destroy a pending mixed-size map.
Accepted object pools end below `B6F8h` / `BDF8h`, respectively.

The line buffer is reused only after source parsing for interactive reference,
answer, selection and directory/rename scratch. Output at `LINE+475` is disjoint
from these fields. The editor temporary source name reuses OUTPUT while INPUT
continues to own the live source. Full-size mixed-map read/edit/write regression
and external FDF source identity checks cover these lifetimes. The host suite
also checks arena boundaries and measured stack use (34 of 512 bytes).

FDB advances independently to version 1.01, revision 002. Automatic identity
selection intentionally reports `FDB 1.01 (002-dev)` because no 1.01 release
baseline is established. Both target builds produce identical COM/OVL bytes.
The 1.0 baseline remains authoritative for the frozen 1.0 release.

## Validation

Host: 40 converter cases; 50 catalogue/import/export/recoverable-save cases;
9 editor cases; 24 usability cases; 47 query/fall-through and two syntax cases;
52 component-policy tests and registry projection check. The original 108-entry
catalogue round-trips byte-for-byte. Console width is at most 80 columns.

Native qualification uses private copies of the qualified full System disks,
substituting only the new COM/OVL pair. Six query/help combinations and both
conversion directions are checked. Interactive qualification exercises invalid
DU input, overflow editing, bounded paging, comparison retry/empty differences,
pre-existing backup preservation, Untitled cancellation, validation/correction,
apply cancellation, actual B–D application, a 109-entry verified save and single
FDB/FDF exports. Public state snapshots prove only the requested B–D DSM fields
change; A, physical selectors and cold configuration remain unchanged. Every
file in that explicit new-pair fixture and its reserved tracks is audited after
each run. The source System images are never written.

On Model 4, interactive qualification unloads ADM3A and M4SCRN to obtain 53 KiB,
then restores the unmodified shipped STARTUP sequence, checks both modules and
50 KiB, and reads a file. Queries use normal startup at 50 KiB.

See [partial qualification record](../reviews/2026-11-04-fdb-101/qualification.json)
and [retained evidence](../reviews/2026-11-04-fdb-101/evidence.tar.gz).
Resume the unchanged final pair on fresh private Model 4 media after unlocking
the desktop; complete all interactive postconditions and restoration checks
before closing the backlog or marking the PR ready. In the current workspace:

```
BETTERCPM_TRS80GP_DIRECT=1 python3 tools/qualify_fdb_usability.py \
  --target trs80gp \
  --baseline ../fdb101-qualification-20261104/qualified-queries-model4/baseline \
  --output ../fdb101-qualification-20261104/qualified-ui-model4-unlocked
```

Use a new output directory for each attempt. The matching pair is fixed in the
baseline receipt; do not replace it or rebuild any 1.0 package. After PASS,
update the retained record/archive and this acceptance status, close FDU-01–10,
and mark PR #619 ready. The test runner restores the shipped console sequence
and checks the resulting 50 KiB state before success.

| Backlog | Focused coverage |
| --- | --- |
| FDU-01–02 | Alias/boundary/range checks; unequal maps; empty last 255-slot chunk; native paging and empty differences. |
| FDU-03 | Unsupported and multi-character choices; failed second-source retry; native missing-ID retry. |
| FDU-04 | Full filter plus overflow, Backspace and DEL; maximum 80 columns; native correction and numeric retry. |
| FDU-05 | Current user 0/15, rejected other user, digit filename; native displayed-DU acceptance/rejection. |
| FDU-06 | Named default and blank Untitled; native cancellation leaves files intact. |
| FDU-07 | Missing/damaged viewer, named recovery and 50-case fault recovery suite; native pre-existing backup preserved. |
| FDU-08 | DSM/SPT pairs, block/extent, directory and numbering rules; native invalid number and cylinder correction/validation. |
| FDU-09 | Pending state and required identity; native add-to-RAM, verified write and exports. |
| FDU-10 | Rejected A and cancelled apply; native public snapshots before/cancel/confirmed B–D updates. |

## Trial dispositions

Early native runs are retained outside the accepted set. They are not counted
as final qualification: intermediate binaries preceded final diagnostics and
scratch placement; a Ctrl-C script sent cancellation before output completed;
the cylinder-format script initially corrected DSM but omitted SPT; one script
used I on page 3 (CKS) rather than page 1 (ID); a backup postcondition initially
assumed padded length rather than the filesystem's exact stored length.
Two superseded Model 4 query runs were explicitly stopped for source changes.
Model 4 UI trials also lost early command characters during CCP return/input
initialization. The bounded diagnostic captured an empty command instead of
FDB. The final driver clears probe screens, waits for an empty prompt and uses
the existing native qualification settling interval before the next command.
Extra timed launch captures are retained separately from acceptance frames.
The final native runs use fresh directories and the exact reported COM/OVL hashes.
