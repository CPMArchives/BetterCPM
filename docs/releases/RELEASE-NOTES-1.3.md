# BetterCP/M 1.3

Published on 21 November 2026 from approved frozen source
`51e1092d01b2a23e6244faaa877a8c5c8d6eb388` as [v1.3](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.3).
The [publication record](evidence/1.3-publication/publication.json) pins the
published filenames, sizes and SHA-256 values; the published RELEASE manifest
records maintainer acceptance.

All eight ZIPs retain the approved frozen bytes. Release download filenames
omit `-candidate`; their embedded roots, candidate labels and historical pending
fields remain build-time records. Published release notes and acceptance metadata
supersede that release-status wording. No archives, published checksums or
historical qualification receipts are rewritten by this repository update.

- PDS 2.0 composes fixed HISTORY, MCL and VAR allocations at cold boot.
- HISTORY keeps its default capacity and behavior as an explicit owner.
- Optional MCL separates interactive commands with semicolons outside double
  quotes. STARTUP/SUBMIT semicolons remain literal.
- Optional VAR supplies case-insensitive session variables and one-pass
  `%NAME%` substitution (`%%` is a literal percent). Undefined/invalid/overflow
  expansion prevents dispatch. Values survive WBOOT and reset at cold boot.
- CONFIG F saves owner composition for the next cold boot; STAT MEM reports
  owner allocations and resulting maximum COM capacity.

Defaults keep MCL/VAR off, HISTORY at 192 bytes, and maximum COM at 57344 bytes
on cpmsim/Model II or 54272 on Model 4. Enabling MCL costs 128 persistent bytes;
VAR costs the chosen 128/256/512 bytes. Standing CCP space is 8704 bytes, 2048
more than 1.2/MCL stage; GET/POKE's editable area is correspondingly smaller.
COM execution reclaims the command environment.

Install a complete matching System package. Private CCP/RSX helpers and their
loaders must be rebuilt together; do not mix 1.2 and 1.3 private artifacts.
The saved configuration writes BCST2; older tools must not edit it. A true cold
boot initializes PDS 2.0, so no live history migration is needed. Keep matching
PDSCONF.OVL with CONFIG. Utilities and Documentation remain separate downloads. On cpmsim, mount the
matching Companion Utilities as C: so PATH can find HELP.LBR; the 332K System
does not include that archive. Model 4 and Model II include it on System.

NDR/PATH, SUBMIT/XSUB and TCAP compatibility are retained. HELP 1.0 (002)
and the matching NOAH 1.0 (022) COM/OVL pair repair protected-layout PATH lookup.
NDR state stays in NDR.RSX. FLOW, HISTORY.RSX, program-visible environment APIs,
live PDS resizing, timestamps and new ports are excluded.

See [focused acceptance](1.3-SCOPE-AND-ACCEPTANCE.md) and the
[implementation scope](../engineering/1.3-IMPLEMENTATION-SCOPE.md). Earlier
implementation tests retain their original scope; the [frozen review record](1.3-FROZEN-REVIEW.md) and publication record bind final acceptance.
