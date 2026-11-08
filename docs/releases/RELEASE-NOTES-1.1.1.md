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

The PATH storage format and six-entry limit are unchanged. Dot entries and
fixed entries resolving to the caller do not repeat the initial local search.
The CCP change adds four bytes within its existing allocation, without TPA loss.

Focused assembled-code lookup, dispatch, loader and PATH edit checks pass.
The public-prompt harness has been updated; final media qualification remains
pending. These changes belong to 1.1.1 rather than the 1.1 release baseline.

See the [numeric PATH contract](../engineering/Numeric-PATH-1.1.md).
