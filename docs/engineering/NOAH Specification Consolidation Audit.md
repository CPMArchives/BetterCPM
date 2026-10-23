# NOAH specification consolidation audit

2026-10-23. Documentation review only; no NOAH implementation or test execution
is claimed. The [consolidated specification](NOAH%20Specification.md) is the
current behavioral baseline. This audit records why 80 chronological decision
sections became 17 subject sections without reopening settled choices.

## Findings and resolutions

| Finding | Resolution |
| --- | --- |
| Early sections still called SQ/CR selectors, batch scope, recovery names and authorization undecided after later acceptance | One normative command/options table and subject sections; obsolete open notes removed |
| First-wins duplicate sources conflicted with later accepted replacement prompts | Later Replace/Skip/All/Cancel policy governs both original and earlier accepted members; failure retains accepted version |
| Staged rebuild was confused with compaction | Separate safety copy from layout transformation; retain deleted material in layout-preserving updates; explicit COMPACT or a necessary from-scratch rebuild discards it |
| Spare-entry arithmetic ignored retained deleted versions and replacements | Capacity counts retained occupied entries and uses the reserved control entry/record rounding consistently |
| LBR inner-file compression was confused with ARK native methods | Separate opaque LBR storage from native ARK codec methods; historical ARK compatibility is required; the exact matrix is an implementation gate |
| LBR deleted-entry fields are undefined, so automatic payload relocation cannot promise recovery for all old files | D2 resolved: from-scratch rebuilds copy active members only; never guess deleted references |
| Generic “zero timestamp means unknown” wording can conflict with format defaults | Follow per-format raw/effective semantics; preserve raw member metadata and mark actual availability |
| Full verification seemed to require decoding every LBR member or an unsupported ARK codec | LBR tests stored files, ARK may retain safely bounded opaque methods with explicit limited-coverage warning |
| Successful rename was conflated with successful metadata/cleanup | Publication includes required metadata; cleanup-only failure leaves new file and warning; failed restore stops batch |
| COMPacting an empty REMOVE/ADD selection conflicted with explicit accepted no-match no-op | Preserve the agreed no-match no-op even for a combined request; standalone COMPACT remains available |
| Multiple source/archives and generated files could mutate their own selections | Freeze identities, deterministic drive/user/name order, exclude selected inputs and active artifacts, bounded-plan implementation gate |
| Source and expanded-output names could be mistaken for filesystem redirects | Member pattern matches stored name; destination DU is explicit/captured; validate embedded plain 8.3 names |
| Command-status and minimum TPA numbers were not established | Logical/text outcomes only until audited; measured ABI/memory gates, no assumed shell API or invented fit claims |
| Numerous small parser/UI omissions were left as prospective questions | Apply existing BetterCP/M conventions; explicit editorial defaults below |

## Routine editorial defaults applied

These complete the already chosen interface; they are not represented as new
human-approved feature decisions. They can be reviewed together in this diff:

- Case-insensitive exact switch names/documented aliases, full-tail rejection,
  idempotent identical switches; no arbitrary prefixes/last-wins parsing.
- One member/source expression and optional single destination in the documented
  forms; shared compound selectors provide multi-DU scope without new operand lists.
- CAPACITY/FORMAT spellings, usage/HELP/standalone VER behavior, existing-version
  and visual standards; no options that silently change irrelevant operations.
- Existing input library's immediate single-key, visible default-No, cancel and
  invalid-choice conventions; plain-console output and preflight paging.
- No-match reporting for read-only/codec operations and no-op updates; warning
  aggregation rather than success being overwritten by a later batch item.
- Current-DU then A0 overlay search; CRC-32 integrity choice; logical 32-bit stream
  offsets with per-format/host bounds; byte/register ABI and measured fit still gated.
- Failed required metadata application enters recovery; normal output ARC semantics
  follow the existing COPY contract, sources remain unchanged.
- Conservative refusal of unsafe structures, input changes, ambiguous publication
  state and invalid extracted names; no silent repair or new resident facility.

D1 was subsequently resolved: preserve historical CP/M ARK compatibility through
native ARK encodings, separately from standalone CP/M Crunch. Exact methods and
reference artifacts remain engineering qualification gates, not claimed coverage.
D3 was subsequently resolved: standalone EXPAND reports ordinary inputs as
`not compressed` and copies them unchanged under normal output safety rules.
Future transparent browsing with `V` is recorded separately from initial scope.
D2 was subsequently resolved: from-scratch LBR rebuilds discard deleted entries
and data, including when enlarging the directory. Ordinary layout-preserving
updates retain them. No substantive user-policy decisions remain open.
All other implementation details are section 16 engineering deliverables.

## Decision coverage map

Every numbered section of the prior draft is accounted for below. Earlier text
is superseded by later accepted decisions where the conversation changed policy.
The original local draft is retained in the consolidation evidence archive;
SHA-256: `e69d53d4d63d59cb8781509ed4ee525f6a623c17e4f067439947ee4f53d175d1`.

| Prior section | Subject | Consolidated section |
| --- | --- | --- |
| 1 | Identity and initial format targets | 1 |
| 2 | LBR timestamp compatibility | 6 |
| 3 | Required operation scope | 1, 15 |
| 4 | Reusable format libraries and file access | 12 |
| 5 | Safe archive updates | 8, 9 |
| 6 | Replacement verification | 8 |
| 7 | Containers, compression and opaque preservation | 1, 8 |
| 8 | Extraction collisions | 7, 8 |
| 9 | Protected extraction destinations and skip reporting | 7, 11 |
| 10 | Recoverable failures | 10 |
| 11 | Skipped changes during archive updates | 5, 10 |
| 12 | LBR directory capacity | 5 |
| 13 | LBR directory sizing and explicit capacity | 5 |
| 14 | LBR automatic directory growth | 5 |
| 15 | Existing archive-member name collisions | 5, 7 |
| 16 | LBR deleted-data preservation and explicit compaction | 5 |
| 17 | Command operand ordering | 2 |
| 18 | Default operation | 2 |
| 19 | Extraction syntax and names | 2, 3 |
| 20 | Omitted extraction selector | 2, 3 |
| 21 | Integrity-test syntax and scope | 1, 2, 8 |
| 22 | ADD creates an absent archive | 2 |
| 23 | No source matches | 10 |
| 24 | Addition compression selectors — proposal under discussion | 1, 2, 4, 1, 4, 16 |
| 25 | Default addition storage | 4 |
| 26 | Compressed-member naming and future LZH | 4, 1, 4, 16 |
| 27 | Extraction and explicit expansion | 1, 4 |
| 28 | Expansion selection matches stored member names | 3, 4 |
| 29 | Mixed expanded extraction | 1, 4 |
| 30 | Format and codec recognition | 2, 4 |
| 31 | No automatic recursive expansion | 1, 4 |
| 32 | Protected archive files | 7 |
| 33 | Backup and final publication | 9 |
| 34 | Staging and backup file locations | 9 |
| 35 | Recovery filenames | 9 |
| 36 | Successful publication with failed backup cleanup | 9, 11 |
| 37 | Controlled cancellation | 10 |
| 38 | Unattended ordinary approval | 7, 10 |
| 39 | Quiet output | 11 |
| 40 | Member-selection patterns and DU boundaries | 3 |
| 41 | Extraction across multiple archives | 2, 3 |
| 42 | Archive processing order within a DU | 3 |
| 43 | Multi-archive LIST and DU ranges | 2, 3 |
| 44 | Archive traversal across DUs | 3 |
| 45 | Multi-archive TEST and COMPACT | 2, 10 |
| 46 | REMOVE requires an explicit member selector | 2 |
| 47 | ADD requires an explicit source selection | 2 |
| 48 | ADD self-inclusion and active recovery-file exclusions | 3 |
| 49 | ADD source filespec grammar | 3 |
| 50 | Multi-archive REMOVE | 2, 7, 10 |
| 51 | REMOVE with no matching members | 10 |
| 52 | ADD has one exact target archive | 3 |
| 53 | REMOVE confirmation | 7 |
| 54 | COMPACT confirmation | 7 |
| 55 | Protection-override selectors | 7 |
| 56 | Protected-object authorization frequency | 7 |
| 57 | Protection attributes survive authorized replacement | 6, 7, 9 |
| 58 | Protection defaults for newly extracted files | 6 |
| 59 | ADD preserves source files | 3 |
| 60 | Overlay packaging | 13 |
| 61 | Overlay compatibility and integrity | 13 |
| 62 | Handler and codec capability queries | 12 |
| 63 | Common member-information record | 6, 12 |
| 64 | Bounded member enumeration | 12 |
| 65 | Bounded member-data reads | 12 |
| 66 | Streaming codec interface and workspace | 12, 13 |
| 67 | Binary-safe file handling | 4 |
| 68 | Explicit compression that increases size | 4 |
| 69 | Embedded expansion filename validation | 4 |
| 70 | Extraction must not overwrite selected input archives | 3 |
| 71 | Restore caller drive and user area | 3 |
| 72 | Unreadable/corrupt archives in batch selections | 10 |
| 73 | Completion outcomes | 11 |
| 74 | Standalone expansion | 2, 4 |
| 75 | Standalone compression | 2, 4 |
| 76 | Standalone codec destination syntax | 2, 3 |
| 77 | Standalone codec source selection | 3 |
| 78 | Conflicting codec selections | 2 |
| 79 | Conflicting operation switches | 2 |
| 80 | Open decisions | 16, 17 |
