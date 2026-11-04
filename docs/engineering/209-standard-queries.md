# FDB standard identification and help

FDB now adopts the common exact, case-insensitive `/VER`, `/H` and `/HELP`
contract. Queries anywhere in the bounded tail ignore other arguments; help
wins over version in either order. Space and TAB separators are accepted.
Longer tokens and embedded slashes are ordinary parser input. Query handling
precedes file access, drive/user and DMA operations, console setup and the
interactive memory check. It preserves the original tail, FCBs, working state,
caller registers and return path. No-argument invocation retains the spec 209
workbench behavior rather than becoming an operand-required utility.

## Identity and inputs

FDB previously had no component registry entry or standard query interface.
The initial identity is `FDB 1.0 (001)`, with numeric revision formatting from
the accepted component policy. FDB.COM and its matching internal FDBVIEW.OVL
belong to the same component. Its selected file-level closure covers the
converter, session/editor/exchange/viewer sources, shared query and monitor
includes, generator and component identity helpers. Assembler identity and
layout configuration are recorded; target variants have separate baselines.
No other component revision is assigned by this change.

Automatic display selection compares those initial baselines; it is not
forced to assigned mode. Selected input changes produce `-dev`; unrelated
component revision changes do not. Build reports bind COM and companion
hashes to the input record. These assignments do not approve package release.
**Release promotion remains HOLD.** Existing frozen archives are unchanged.

## Presentation and memory

Version output uses the standard four-line compact identification block.
Both help aliases produce the same 15-line, at most 67-column ASCII screen,
with CR/LF, the implied corner, purpose, positional syntax, four command forms
and aligned final query options. No ANSI, terminal backend, paging, full border
or separate example section is used. The command forms explain workbench
startup/named opening and binary/text conversion rather than suggesting that
the interactive editor has extra operational switches. Malformed converter
syntax retains short usage and adds `Use FDB /HELP for help.`

The resident image ends at 35FCh, below the 3600h import arena; the editor's
upper bound remains D107h. Entry-only query code/text uses load-time bytes in
the import arena before it is repurposed. It is never referenced once normal
session/converter work starts. The builder checks its bounds separately.
Removing obsolete UI padding accommodates the short-usage hint without moving
the fixed editor or shrinking its workspace. The matching viewer is regenerated.

## Validation

`test_fdb_queries.py` executes the real assembled entry on the full Z80 core:
47 query/fall-through cases and two exact short-syntax cases, full screens,
case/TAB/maximum-tail handling, precedence, token boundaries, console-only
BDOS, unchanged files/FCBs/context/DU/DMA/tail, main/alternate/index registers
and caller SP. Query stack peak is 24 of 512 bytes. Temporary input copies
verify automatic identity behavior for both targets and independence from
unrelated registry rows.

Existing 40-case converter, 50-case session and nine-case editor regressions
pass, including original catalogue bytes, recoverable saves and viewer paths.
Component registry/input/development/identity/revision tests and projection
checks pass. Registry import tests now treat historical revisions as monotonic
lower bounds, permitting accepted component advances instead of requiring
obsolete exact counters.

`qualify_fdb_queries.py` stages only the new pair into private copies of the
qualified complete System images. On cpmsim and Model 4 it checks six native
queries (all aliases, both precedence orders, ignored operands and mixed case),
all four displayed command forms, and the normal 108-entry native binary/text
round trip with an independent host cross-check. Model 4 runs at normal 50 KiB
with both console extensions still loaded. All shipped files and reserved
tracks are audited against the explicit new-pair fixture. The original media
and frozen packages are never modified.

Final artifact identities, build records, results, native captures/transcripts
and regression logs accompany this report in the
[review evidence directory](../reviews/2026-11-04-fdb-queries/).
