# PIP read-only confirmation shared input qualification

## Scope

PIP 1.0 Build 028 uses the shared one-key confirmation binding only at
`DESTINATION IS R/O, DELETE (Y/N)?`. The existing caller prints the prompt;
`pipinput.inc` supplies one cooked BDOS 1 read with the historical AND-DF
folding. Only Y/y approves. Every other byte declines immediately, with the
existing echo and `**NOT DELETED**`/cleanup behavior. No retry, new default,
input flush, acknowledgment or cancellation alias is introduced. `[W]` still
bypasses this confirmation.

The PIP command loop remains BDOS buffered input. HEX correction/EOF dialogue,
reader control, device input and transfer polling remain their historical
interfaces. They are not ordinary fields to replace with a generic editor.
The public INP/OUT patch entry bytes at 0103h/0106h/0109h are unchanged.

## Artifact and cost

- PIP 1.0 Build 028: 14,477 bytes, previously 14,253 (+224 transient bytes).
- SHA-256: `1fdcf10af932e726b51d88e253fb5291ec3eece5c56c982fc53b1197394181fb`.
- Native ZSM4/LINK output is byte-identical to the cross build.
- Existing 128-byte stack unchanged; no resident allocation or new input buffer.
- Select events/checks/choice and the existing one-key compatibility adapter;
  exclude text editor, append engine, word commands and screen renderer.
- The shared confirmation module's echo-policy comment was clarified; its
  emitted code is unchanged for existing DUP/SYSGEN consumers.

The native builder now falls back to the current local cpmsim/tools paths and
includes the sibling `srctools` helper in PATH, matching other qualified builders.
The parser test's stale fixed Build 026 assertion now uses version metadata.

## Compiled checks

`tools/test_pip_shared_confirmation.py` compares 258 complete transfers against
the retained pre-migration approval-read fragment: all 256 possible answers
through verified protected replacement, plus W and WV bypass. It compares full
output, filesystem mutation, BDOS call sequence and writes, verifies exactly one
read when required and no leftover temporary file, and preserves the caller DU
and DMA through the existing transfer fixture.

Another 256 direct controller cases clobber ordinary registers at the console
call and verify one read, no typeahead consumption, balanced stack and the
expected approval result. Six scoped version/purity cases pass. Stack tracking
in the complete compared transfers observes a maximum of 16 of the existing
128 bytes; this is not a claim about all possible PIP modes or interrupts.

Parser/interactive command-loop, transaction/fault cleanup, device text input,
HEX correction/EOF dialogue, wildcard and logical-device/patch-ABI regressions
passed against Build 028. These retain the explicit distinction between the
shared approval prompt and PIP's command/data protocols.

## Actual media checks

`tools/test_pip_shared_media.py` passed on both platforms:

- `/private/tmp/bcpm-pip-shared-cpmsim-final/result.json`: N and X each preserve
  the old payload and RO attribute; lowercase y replaces it; WV bypasses the
  question. Payload/attribute checks occur after each decision. Source and other
  target data survive, temporary files are removed, and filesystem checking
  passes.
- `/private/tmp/bcpm-pip-shared-native-final/result.json`: native keyboard input
  reaches repeated RO questions, N/X decline, Y approves and WV runs without a
  question. Eight VRAM captures and final independent inspection verify the two
  intended replacements, source/unrelated payload preservation, RO removal,
  unchanged system records, no staging files and a clean filesystem.

The first media fixture used underscores, which historical PIP treats as
assignment syntax. The command was correctly rejected before the confirmation;
that fixture run is not passing evidence. Corrected exact filenames were used
for both final campaigns. Only the private batch process was stopped; daily
emulator media were not touched.

The broader remaining-consumer inventory and CONFIG size gate are recorded in
[Shared Input Remaining Consumer Audit](Shared%20Input%20Remaining%20Consumer%20Audit.md).
