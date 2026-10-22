# COPY shared input qualification

## Scope and compatibility

COPY 1.0 Build 005 binds overwrite choices, verification recovery choices and
the collision replacement-name field to the shared input library through
`src/utilities/common/copyinput.inc`. The transient-only build adds the modules;
resident RCP and MOVE keep their existing behavior.

COPY's contract differs deliberately from REN and from the standard text editor:

- Choices poll raw BDOS 6, ignoring no-key, CR and LF. Ctrl-C aborts.
- Lowercase ASCII folds to uppercase. Every other response, including ESC and
  unknown high bytes, retains its old echo/help path and full item repaint.
- Overwrite choices retain Y/N/O/S/R/? meanings. Verification retains R/S/?.
  Only application code changes overwrite/skip-all state, retries or cleans up.
- Unknown choices map to the controller's explicit help member, with the original
  byte retained for the caller's echo/dispatch. No invalid input disappears.
- The replacement field retains its 126-byte limit, BS/DEL deletion, CR/LF
  submission, Ctrl-C abort, exact-name validation and blank-to-collision action.
- Ctrl-U remains a literal candidate byte, subject to filename validation; it
  does not clear the field. The adapter uses `UA_PUT` for that byte.
- Overflow stays sticky after backspace. Refused bytes are not echoed. A
  backspace at empty input does not echo; other backspaces use the original
  BS/space/BS output. No new redraw, default, acknowledgment or input flush.

`UA_PUT` is a literal-append entry label in the existing append engine. Adding
that label emits no bytes. Rebuilding REN still produces exactly Build 008's
5,884 bytes and SHA-256
`0620802d918ab803e5b17988b8dd5a28459ecf22b857afd4fcbb7d4d5a1a0331`.

## Artifact and memory

| Item | Value |
| --- | --- |
| COPY | 1.0 Build 005 |
| Bytes | 12,010 |
| SHA-256 | `a6ce4f242ccacc175204ecaffdbb5d2e6d01e074883b018465853754b2581289` |
| Previous Build 004 | 11,703 bytes |
| Increase | 307 transient bytes |
| Resident allocation | None |
| New input state | Six choice/binding bytes, one old-length byte, one capacity byte |
| Existing field storage | Reuse CTRBUF/CTRLEN/CTROVER/CTRCHAR |

The standard editor, text controller, word module and field renderer are omitted.
There is no additional text buffer or new fixed stack reservation. Native
ZSM4/LINK reproduces COPY and all five sibling transient outputs byte for byte.
The native builder now finds the current local cpmsim/tools layout and supplies
its sibling `srctools` helper path, as the ERA/REN builders already do.

MOVE has no interactive prompts in its current implementation and does not link
this binding. Its 5,201-byte output differs from the preceding artifact only in
the unused embedded COPY identity string (004 to 005). Its command code, source
deletion rules and noninteractive collision policy are unchanged. The other
RCP-derived images also contain shared identity data; those changes do not imply
that resident RCP was modified. MOVE receives no new input capabilities.

## Evidence and limits

`tools/test_copy_shared_input.py` compares all 256 first bytes for overwrite,
verification and replacement-name input, plus six editing/boundary sequences:
774 cases. It compares echoed bytes, consumed and remaining input, selected
action, policy flags, length, overflow, candidate bytes and field-buffer guards against retained
legacy fragments in `tools/fixtures/copy-legacy-input.json`. The fake BDOS
deliberately clobbers general registers. Six scoped version/purity cases also
pass. Actions stop at dispatch: file mutation
and cleanup are qualified separately on actual emulator media.

Mapping, filespec/options, allocation/decimal-reporting and 70 resident-relocation
and transient COPY/MOVE operand-boundary checks passed. Native assembly parity
was checked for all generated transient binaries. This is a scoped regression
campaign, not a new claim of whole-release acceptance.

Actual cpmsim reports:

- `/private/tmp/bcpm-copy-shared-interactive/evidence.json`: Y/N/O/S/R/help,
  invalid response, session reset, batch, SUBMIT interactivity, rename validation,
  edit/backspace, blank/abort, source/batch overlap and RO preservation. Additional
  cases reject literal Ctrl-U and sticky overflow, then accept a DEL-corrected
  lowercase name and independently verify its payload.
- `/private/tmp/bcpm-copy-shared-verify/evidence.json`: normal verification,
  invalid options, injected verification failure, help/skip/abort cleanup,
  batch continuation, no-/V behavior and retry success. Fault injection changes
  only private test binaries; production continuation/cleanup paths execute.

Native Model 4 interaction/media checks use private disks and retain screen and
payload evidence. Their exact completed case list is recorded with the native
campaign, rather than treating unselected cases as passes.


Completed native campaigns:

- `/private/tmp/bcpm-copy-shared-native/evidence.json`: eight passing cases:
  interactive choices, overwrite-all, skip-all, collision abort, replacement-name
  validation/conflict/blank, replacement collision with an existing file,
  replacement-name abort and verification retry.
- `/private/tmp/bcpm-copy-shared-native-recovery/evidence.json`: two passing
  cases: verification help/skip and help/abort, including native destination
  cleanup and preservation of source data/attributes.

Native reports retain per-case captures, original/current private media, tested
binary hashes and independent payload/attribute checks. Controlled verification
failures use the existing private shim; they are not claims of real hardware
failure injection. The first campaign invocation included an extra nonexistent
case name; the harness correctly rejected final accounting after the eight real
cases passed. Corrected selection with `--resume` verified the same binary hash
and completed evidence before writing the final PASS record. No emulator or
production-code failure was waived.
