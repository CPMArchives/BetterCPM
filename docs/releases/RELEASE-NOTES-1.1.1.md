# BetterCP/M 1.1.1 release notes

Status: Planned; changes implemented locally, not yet published or qualified
on final release media.

## Command search and PATH

- Unqualified transient commands always search the current drive/user before
  the configured PATH. A PATH containing only `D0:` no longer prevents a local
  `PATH.COM` from being found. A local match takes precedence, including when
  loading it fails. Explicit qualifiers retain exact lookup.
- PATH `/A location` and `/ADD location` append one entry to the list.
- PATH `/D location` and `/DEL location` remove one matching entry while
  preserving the order of the others.
- Invalid edits, duplicate additions, capacity overflow, absent deletions and
  deletion of the final entry leave the live list unchanged. Whole-list
  replacement, `/DEFAULT`, `/H`, `/HELP` and `/VER` remain supported.

Z-System symbolic entries replace the dot entry: `$$` means current drive/user,
`$0` means current drive/user 0, and `A$` means drive A/current user. Trailing
colons are optional; PATH displays `$$: A0:` for the default. A lone dollar and
a dot are rejected. Double literal dollars in SUBMIT source files.

The PATH allocation and six-entry limit are unchanged, but the encoding and
capability flag are revised. Ship matching kernel, CCP and PATH.COM builds;
old and new utilities reject incompatible kernel capabilities. Entries resolving
to the caller do not repeat the initial local search. The CCP occupies 5,593
bytes within its existing 5,632-byte allocation, without TPA loss.

Focused assembled-code lookup, dispatch, loader and PATH edit checks pass.
The public-prompt harness has been updated; final media qualification remains
pending. These changes belong to 1.1.1 rather than the 1.1 release baseline.

See the [numeric PATH contract](../engineering/Numeric-PATH-1.1.md).

## Console personality activation

Loading ADM3A, VT52 or ANSI moves the cursor to column 1 of the last row of
the supported 80x24 screen. It preserves the displayed cells. The CCP's normal
return CR/LF then scrolls a blank row for the prompt, including when the load
command was entered on the last row. This replaces the misleading jump to the
top of the old display. No cursor-position query or screen clear is used.

The operation is a fresh-load initializer. Ordinary warm returns and retained
STATEFUL relocation do not repeat it. Explicit application cursor-home and
clear operations retain their existing behavior. The change applies to cpmsim,
Model 4 and Model II, with no increase in resident allocations.

Assembled-code checks cover all nine personality/platform combinations:
activation leaves screen cells intact, the return newline scrolls to a blank
bottom row, and explicit home remains available. cpmsim module budgets remain
1,247 bytes for ADM3A/VT52 and 1,759 bytes for ANSI, including caller allowances.
Final release-media qualification remains pending.

## STAT operand case handling

STAT now folds operand letters to uppercase before parsing. The CCP preserves
the original command-tail case, and 1.1 STAT incorrectly rejected lowercase
drive operands such as `STAT b:` as invalid filespecs. Lowercase and mixed-case
drive/user prefixes, filenames, attributes, device names and keywords now use
the same parser behavior as uppercase operands. Help/version and invalid-option
query paths retain their existing command-tail preservation.

Bare STAT continues to report logged-in drives. Explicit `STAT B:` selects
and logs in B before querying its free space, then restores the caller's drive
and user. Regression checks execute the assembled COM with a recording BDOS
for lowercase and uppercase drive/user, filename and keyword operands, context
restoration, invalid-option isolation and query precedence. Existing filespec
parser checks pass.
