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
