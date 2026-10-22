# REN shared choice input qualification

## Scope

REN 1.0 Build 007 binds its confirmation, collision and failure choices to the
shared choice controller through `src/utilities/common/reninput.inc`.
The existing filename-entry editor is unchanged in this increment. Its legacy
append/backspace/Ctrl-U behavior needs a separate text-field compatibility
assessment; this record does not claim that every REN input uses the library.

The binding preserves BDOS Function 1 echo, case folding, silent invalid-input
retry for Y/N, repeated full collision/recovery questions, help, Ctrl-C abort,
and the existing `/C`, `/Y`, `/N`, `/Q`, `/QQ` and `/DRY` precedence.
Enter and ESC remain invalid responses, not defaults/cancellation aliases.
There is no extra acknowledgment or input flush. High-bit AND-5F aliases also
retain their historical interpretation; folded control bytes cannot become new
cancellation aliases. The caller retains all rename/protection/recovery logic.

## Artifact and memory

- Build 007: 5,856 bytes.
- SHA-256: `6c0803d299fbae7825e6ceb330235bd78ddfe0d9762a4ee1abcb5422f8506ba5`.
- Previous code: 5,549 bytes; increase: 307 transient bytes.
- Existing 128-byte stack unchanged; no resident allocation or new text buffer.
- The per-DU rename ledger starts 307 bytes later. Its existing capacity refusal
  remains in force; zero/one-entry ledger bounds are regression-tested.
- Only events/checks/choice modules are selected; text editor/renderers/word
  commands are excluded. The binding preserves BC/DE/HL/IX across controller use.
- Native ZSM4/LINK output is byte-identical to the cross-assembled artifact.

## Evidence

`tools/test_ren_shared_choice.py` replays 256 possible first input bytes through
three complete workflows (768 comparisons): confirmation, collision and injected
rename failure. It compares mutations, final file state and complete echoed
output against retained legacy read/prompt fragments in
`tools/fixtures/ren-legacy-choice.json`. The fixture records its source revision
and does not depend on future Git history or shallow-clone availability.

Existing compiled core, workflow, collision, failure and protection regressions
cover invalid names, filename editing/overflow, attributes, dry-run, quiet and
unattended precedence, target races, repair failures, multi-DU selection and
bounded rename-ledger refusal.

The real cpmsim campaign `tools/test_z80pack_ren.py` passed against the final
binary, using private copies of the qualified disk profile. It covers all
attributes and multiple extents, safe default protection, dry-run immutability,
invalid syntax, collision/help/edited replacement/confirmation, ledger rescan
safety, multiple DUs, payloads and version output.

`tools/test_model4_ren_shared_input.py` exercises native interactive prompts on
private media and passed with VRAM captures and independently inspected file state.
It verifies invalid physical CLEAR/ESC, Enter and X retain the confirmation; N
skips; Ctrl-C returns normally; collision help and an edited replacement lead
to a new confirmation; Y renames the source. Other file payloads and system
records remain unchanged, and independent filesystem checking passes.
Reports are `/private/tmp/bcpm-ren-shared-cpmsim/evidence.json`,
`/private/tmp/bcpm-ren-shared-native/result.json` and
`build/ren-shared-input/results.json`.
Fault-injected recovery remains a compiled-CPU qualification; ordinary native
interaction does not establish fault-injected physical I/O behavior.

The native builder now falls back to the current local cpmsim/tools layout and
supplies its sibling `srctools` helper path, matching the qualified ERA builder.
Old core/cpmsim version assertions now derive the expected banner from metadata.
