# FDB.COM 1.01 usability backlog

Reviewed 4 November 2026 against main
`066336cdc1d28cc2d4b2b7c44e1c1756a3cd9fde`. These are deferred **1.01**
items, not implementation changes or new 1.0 release requirements. Preserve
the 1.0 code, interfaces, component identities, qualified media and packages.

The review covers source selection, listing, details/comparison, editor input,
validation, applying, saving and recovery prompts. Nine focused probes execute
the assembled program on the full Z80 core with modeled BDOS; transcripts and
the runner are in [review evidence](evidence/2026-11-04-fdb-usability/).
Every probe preserves its original files. The filter probe intentionally
retains a **failed 80-column assertion (94 columns)** as a finding, not a pass.
These probes are not new cpmsim or Model 4 native qualification.

## Navigation and input

- [ ] **FDU-01 — Standard paging aliases (already recorded in PR #615).**
  Accept `,`/`<` for previous and `.`/`>` for next, and display
  `,< Previous   .> Next` consistently in editor/details/comparison maps.
  Retain the original backlog item's platform and state-preservation checks.

- [ ] **FDU-02 — Bound map navigation and show where the user is.**
  In details for ten-slot MMI012, two `>` commands reach a screen containing
  only `17 absent` through `24 absent`. `VMAPNEXT` limits the offset against
  255 rather than the selected map length; the editor already uses its count.
  Show the visible range and total; stop at the last relevant chunk. Comparisons
  must use the longer map so genuine one-sided slots remain visible. In
  differences-only mode distinguish an empty chunk from no differences in the
  complete comparison. Verify first/last/partial chunks and unequal map sizes.
  Evidence: `past-map-end.txt`; [viewer](../../src/utilities/disk/fdbview.inc),
  `VMAPNEXT`, `VMAPS`, `VMAPFETCH`.

- [ ] **FDU-03 — Give local feedback instead of silently losing context.**
  An unsupported viewer key such as `Z` repeats the sector-map block and prompt
  without a reason; multi-character choices go directly to the main menu via
  `ASKCHOICE`. Report the invalid choice and retry the same prompt without
  appending duplicate maps or discarding the selected source/comparison step.
  Preserve valid cancellation and page controls. Verify empty, unsupported,
  and multi-character answers separately.
  Evidence: `unknown-viewer-key.txt`; [session](../../src/utilities/disk/fdbsession.inc),
  `ASKCHOICE`; viewer `VIEWPROMPT`/`VPAGE`.

- [ ] **FDU-04 — Make field limits, editing and overflow recovery usable.**
  The list-filter prompt plus 32 echoed characters occupies 94 columns.
  Entering a 33rd character sets an overflow state in which Backspace/DEL no
  longer repairs the answer; Return reports `Invalid filename or ID` even for
  a filter and returns to the main menu. Keep prompt plus echoed input within
  the supported screen width, identify field-specific limits, and permit a
  local correction or explicit cancellation. Review the editor's generic
  `Value:`/`New value:` prompts alongside this work: show the selected field,
  current value, accepted range/base and text length instead of requiring
  users to infer them from another row. Preserve safe draining of excess input
  so trailing characters cannot become independent commands.
  Evidence: `overlong-filter-backspace.txt`; session `ASKOVER`/`ASKBACK`;
  [editor](../../src/utilities/disk/fdbdrive.inc), `EDNUM`/`EDEDITTEXT`.

- [ ] **FDU-05 — Make displayed and accepted filenames consistent.**
  The header displays `A0:DISK.FDB`, but entering that exact name at F/Open
  produces `Invalid filename or ID`: `PARSENAME` accepts a single-letter drive
  prefix, not that displayed drive/user form. Agree the intended 1.01 DU/name
  grammar before changing it; make defaults copyable, state any restrictions,
  and retry invalid input locally. Do not silently switch user areas or broaden
  filename semantics as part of a cosmetic change.
  Evidence: `displayed-du-filename.txt`; session `SHOWNAME`/`PARSENAME`.

## Decisions and diagnostics

- [ ] **FDU-06 — Explain save defaults, especially for Untitled.**
  N followed by S offers `Return for displayed default` despite having no
  default; Return then produces the generic invalid-name error. Require a
  filename explicitly for Untitled. Otherwise show the complete current
  destination at the input prompt, including after editor screens have cleared
  the catalogue header. Keep replacement confirmation and cancelled-save
  preservation intact.
  Evidence: `untitled-save-default.txt`; session `DOSAVE`/`SHOWCONFIRM`.

- [ ] **FDU-07 — Describe the operation and failing object accurately.**
  D/Details with an unknown ID says `No matching entries. Nothing imported.`
  Missing FDBVIEW.OVL says only `FDB: file operation failed`; mismatched viewer
  tokens/checksums use the invalid-catalogue path. Distinguish source lookup,
  missing/unreadable/mismatched viewer, catalogue and file-operation failures
  where the cause is known. Explain how to obtain the matching COM/OVL pair.
  Recovery messages should name the actual destination, backup and temporary
  files and distinguish pre-existing recovery files from files retained by this
  attempt; never suggest deleting a backup without establishing its state.
  Evidence: `missing-detail-id.txt`, `missing-viewer.txt`; session `NOIMPORT`,
  `RECFILES`; [viewer loader](../../src/utilities/disk/fdbviewload.inc),
  `STARTVIEW`/`VIEWLOADED`; recovery-message wording is source-reviewed.

- [ ] **FDU-08 — Make validation failures actionable.**
  Changing MMI012's logical-track unit to cylinder and validating displays the
  maximum DSM of 389, but V reports only `Invalid working format. Correct the
  fields and validate again.` The conflicting DSM remains on another page.
  Name the failing field/rule, current value and allowed range or relationship;
  identify the page/slot where it can be corrected. Similarly separate invalid
  field selection, unavailable binding and malformed numeric input instead of
  `Invalid selection, binding or field.` Retain editable temporary inconsistency;
  do not silently rewrite user choices to make validation pass.
  Evidence: `generic-validation.txt`; editor `EDERROR`, `EDCHECKFAIL`, `EDMAKE`.

- [ ] **FDU-09 — Distinguish unchanged, pending, catalogued and written state.**
  A new blank working format and the main catalogue can both display
  `Unmodified`, yet quitting asks `Working format pending: S Save...`.
  `EDDIRTY`, `EDPENDING` and catalogue `DIRTY` describe different objects/stages.
  Show pending editor work in the main menu and use explicit labels for putting
  it into the RAM catalogue, writing that catalogue to disk, and applying to an
  active drive. Make quit/discard consequences clear without treating
  `Unmodified` as proof that a definition is already saved.
  Evidence: `pending-unmodified.txt`; editor `EDSTART`, `EDSTATE`, `EDSAVE`,
  `EDEXITCHECK`; session `SHOWSTATE`.

- [ ] **FDU-10 — Make drive-apply confirmation reviewable.**
  Source review finds that the final confirmation names only the logical drive
  letter and says `Apply working format to this drive (Y/N)?`. Show its physical
  selector, current binding and proposed format identity/important geometry so
  the user can check the target before approving. State that application changes
  the active binding, not media contents or saved cold-boot defaults. Retain
  A-drive protection, physical-selector preservation and validation; verify
  cancellation leaves the old binding intact. Source: editor `EDAPPLY`,
  `EDSETDRIVE`, `EDCONFIRM` (not a new runtime reproduction).

## Acceptance for the deferred implementation

Add focused checks for each item, including the failing width assertion above,
and exercise the affected paths on cpmsim and Model 4 with the actual matching
viewer. Verify selection/editor/catalogue state, file bytes, recovery files and
drive bindings after invalid input, cancellation and failed operations. Keep
displayed paging ranges and defaults consistent with actual behavior. Continue
the existing round-trip, catalogue, editor and recoverable-save regressions.
This backlog review itself implements none of these changes.
