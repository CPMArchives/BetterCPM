# REN replacement-name shared input qualification

## Scope and policy

REN 1.0 Build 008 extracts the replacement-name editor into
`src/utilities/common/ui/append.inc`, an independently selectable, I/O-free
compatibility event engine. This replaces the inline editing algorithm in
`renflow.inc`; it does not add a second editor buffer or new input behavior.

The standard editor has different cursor, ESC, character-filtering and overflow
semantics, so this compatibility profile preserves REN's existing contract:

- Append only, with BS/DEL removing the last byte and Ctrl-U clearing the line.
- Ctrl-C aborts; CR submits even an empty candidate.
- The caller retains cooked BDOS 1 echo and ASCII-only uppercase conversion.
- REN's existing 31-byte capacity, filename validation, invalid-name reprompt,
  blank-to-collision action and rename/attribute/ledger policies are unchanged.
- Excess input sets sticky overflow. Backspace does not make a previously
  truncated name valid; clear or reinitialization resets overflow.
- Other bytes, including ESC, retain their old path through filename validation.
  No ESC cancellation alias, WordStar cursor commands, redraw, new defaults,
  acknowledgment key or input flush is introduced.

New fields should use the standard editor. This extraction is not a new
system-wide editing default. The developer guide documents the compatibility
engine's caller-owned state and event contracts.

## Final artifact and costs

| Item | Value |
| --- | --- |
| Utility | REN 1.0 Build 008 |
| Size | 5,884 bytes |
| SHA-256 | `0620802d918ab803e5b17988b8dd5a28459ecf22b857afd4fcbb7d4d5a1a0331` |
| Previous Build 007 | 5,856 bytes |
| Increment | 28 transient bytes |
| New state | One capacity byte; existing buffer, length and overflow are reused |
| Stack | Existing 128 bytes, unchanged |
| Resident allocation | None |

Native ZSM4/LINK and cross-assembler binaries are byte-identical. The bounded
per-DU ledger begins 28 bytes later; existing zero/one-entry capacity refusal
checks pass. Standard editor, word commands, text controller and field renderer
remain excluded. REN still selects the previously qualified choice controller.

## Compiled checks

`tools/test_ren_shared_name.py` compares 268 complete rename workflows against
the retained Build 007 input loop in `tools/fixtures/ren-legacy-name.inc`:
all 256 possible first bytes plus lowercase, BS/DEL, Ctrl-U, empty input,
Ctrl-C, overflow, sticky overflow after backspace, overflow cleared by Ctrl-U,
invalid-name retry, literal ESC and backspace at empty input.

It separately tests 3,072 guarded raw-engine sequences at capacities 1, 31 and
255, comparing event, length, content, overflow and both buffer guards after
each input. It checks invalid zero-capacity initialization and reinitialization
of an overflowed field. These tests use the actual linked REN state aliases
as well as isolated module instances for larger capacities.

The 768 full choice-workflow differential checks were rerun against Build 008.
Core, workflow, collision, failure and protection regressions passed, covering
caller DU restoration, selection, help, retries, target races, attributes,
ledger refusal and option precedence. Fault recovery is CPU-qualified;
ordinary native media checks do not imply injected physical I/O-fault coverage.

## Actual platform checks

The real cpmsim campaign passed on private disk copies:
`/private/tmp/bcpm-ren-name-cpmsim/evidence.json`. It covers attributes and
multiple extents, safe defaults, dry-run immutability, malformed syntax,
collision/help/edited replacement/confirmation, ledger and multi-DU behavior,
payloads and version output.

The native Model 4 campaign passed:
`/private/tmp/bcpm-ren-name-native/result.json`. Thirteen VRAM captures document
confirmation invalid-key handling, decline, Ctrl-C, collision help, invalid-name
reprompt, sticky overflow after backspace, clearing an overflowed line with
Ctrl-U, lowercase normalization, backspace correction and final authorization.
Independent disk inspection verifies the intended renamed payload, preservation
of other file payloads and system records, and a clean filesystem.

The existing cooked echo presentation is preserved, including its treatment of
control characters; this extraction is not a screen-rendering redesign. Daily
emulator media were not used. Compiled reports and retained baseline expansions
are under `build/ren-shared-name/` and `build/ren-shared-input/`.
