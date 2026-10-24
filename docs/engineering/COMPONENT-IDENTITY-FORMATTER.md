# Shared component identity formatter

This increment builds on the revision-assignment tooling in PR #492. It
consolidates common utility, codec, DDT and BYE text formatting in
`tools/component_identity.py`. Current callers explicitly select legacy output;
no executable identity or revision assignment changes yet.

The default new formatter emits the adopted numeric syntax, for example
`DDT 1.9 (004)`. Development formatting is explicit and emits `(004-dev)`.
Revision 1000 uses four digits. The formatter validates names, versions, positive
integer revisions, safe identification descriptions and boolean development
state. It neither chooses an identity owner nor infers development status.
Callers must resolve RCP ownership or validate a baseline before supplying those
values. Unknown development status must not be silently supplied as false.

Numeric output always retains the independent revision even when checked
compatibility information is available; the runtime compatibility stamp belongs
to its own validation/provenance path. Legacy output temporarily preserves the
existing checked and resident decorations exactly. It refuses a development
flag rather than hiding it in legacy output.

All four existing formatting paths now delegate title generation to the shared
formatter; the complete identification block is shared by codecs, DDT and BYE.
The selected-input maps include the new helper, so future edits to it affect
consumer review. Common utilities still retain their current shorter legacy
block; switching them to the adopted complete block is executable migration work.

Eight new formatter tests plus the registry, selected-input, assignment and
BYE/DDT integration suites pass: 48 tests total. Before/after comparison checks
all ordinary utility titles, resident command titles, synthetic checked titles,
codec version/help text and DDT/BYE blocks. Real host assembly confirms DDT.COM
(6,528 bytes) and BYE.COM (1,081 bytes) remain byte-identical. This does not claim
checked binary or native execution qualification.

There is no environment switch or build-time default that silently enables the
new format. The next executable migration must explicitly choose numeric output,
assign each changed executable its next revision using the comparison workflow,
and account for current RCP-transient and checked-contract coupling. Frozen
artifacts and historical receipts retain their old output and identities.
