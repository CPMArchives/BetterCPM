# Common Utility Query Qualification

The maintainer-directed query contract is now shared by BetterCP/M-owned
utilities: an exact, case-insensitive `/VER` token ignores other command-line
arguments and returns identification without command operations. Existing
`/HELP` support follows the same rule; where both queries are provided,
`/HELP` wins in either order. This does not add help screens to utilities
that do not yet provide them. See [version identification](../../specifications/UTILITY-VERSIONING.md)
and [help screens](../../specifications/UTILITY-HELP.md).

## Implementation boundary

`src/utilities/common/version.inc` implements the forgiving version recognizer
for the common transient wrapper, resident RCP dispatch, DUMP and the owned DDT
adaptation. It accepts space/TAB separators, matches whole tokens, preserves
span registers and emits no invalid-query-usage diagnostic. The slash must be
a literal slash; control 0Fh is not treated as its case-fold equivalent.
Compression commands dispatch help first using the same scanning code with a
five-byte keyword, then version. Their private-stack/early-return ABI is
unchanged. Each compression command is now 1.0 Build 004; other affected
metadata sequences advance once for the shared executable change, including
the RCP package. Historical reference binaries and adopted third-party tools
are unchanged.

PIP's existing bracketed S/Q string data and CONFIG's quoted startup/format
text remain literal data. Their existing parser boundaries distinguish those
strings from command options. PIP's pre-scan also accepts TAB separators; longer
branches were changed to absolute jumps where the added boundary checks exceed
the Z80 relative-branch range.

## Evidence and results

The [machine-readable record](Utility-Query-evidence.json) and
[logs/source snapshots](Utility-Query-evidence.tar.gz) retain the tested
artifact identities and evidence:

- 250 common transient/resident identity, forgiving-argument and pure
  fall-through checks. The six codecs use their separate full-Z80 harness
  because the small general test interpreter does not implement IY.
- 356 full-Z80 compression query/parser checks and 90 stock CP/M 2.2 query
  commands, including complete screens, ignored operands, repeated tokens,
  help/version precedence, exact-token boundaries and maximum-length tails.
- Exhaustive per-byte `/VER` matching and pre-private-stack qualification:
  peak 24 of 32 available bytes, with eight bytes remaining.
- Focused CONFIG command-line and saved IOBYTE tests, COPY shared input,
  DDT core/parity/query tests, DUMP reference/return tests, DUP invocation,
  ED invocation, ERA shared choice, PIP parsing/confirmation and SYSGEN
  invocation/shared-choice regressions.

No additional file operation is allowed on these query paths. Compression
checks additionally prove unchanged FCB/context/tail, drive/user, stack,
index/alternate registers and code. Existing operational tests remain
applicable; the query contract does not change ordinary command syntax.

The compression platform campaign separately binds final Build 004 commands
to exact System/Utilities disk images. The query evidence is not a substitute
for every other utility's platform/component acceptance. Earlier DDT and other
component receipts continue to qualify their original binary/image hashes;
changed artifacts require relevant reacceptance in the release checklist.
