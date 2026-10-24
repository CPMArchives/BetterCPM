# TED Qualification — development foundation

**TED is not implemented to the adopted specification and is not qualified for
release.** This record covers a bounded implementation foundation only. There
is no accepted `TED.COM`, no WordStar compatibility claim, and no TED addition
to either Utilities image. The specification's acceptance requirements remain
unchanged.

## Implemented and checked

The pinned upstream and maintained source layout are described in
[TED Reference Baseline](TED%20Reference%20Baseline.md) and
[the source README](../../src/utilities/ted/README.md).

`tools/test_ted_foundation.py` executes the assembled development executable on
an independent Z80 core with a deliberately register-clobbering BDOS model.
Its 21 cases cover startup at/below the arithmetic memory threshold; active
ceilings 8000h, CA01h, CF01h and D500h; protected-memory sentinels; collision
skipping and all-1000-name exhaustion; preservation of unrelated EDITOR.TMP;
MAKE/CLOSE/DELETE errors; random workspace read/write failures; an existing
output refusal; save-command interlocking without dirty-state clearance; and
allocator-subtraction underflow.

A 41,000-byte fixture contains 500 distinct 80-byte lines. At the lowest
admitted ceiling it is read and printed in order with exactly one 516-byte
cache, exercising real compiled eviction/reload paths and workspace records.
Original input bytes remain intact. This is a cache-content test, **not** a
preserving editor save/reopen round trip. BDOS failures here are synthetic;
real directory/data-full media are not covered.

For this development payload:

| Property | Value | Meaning |
|---|---:|---|
| Executable length | 12,648 bytes | Cross payload, excluding CP/M padding |
| First free address | 3268h | After prepared static data |
| Reserved block map | 2,048 bytes | Entire supported map reserved below cache |
| Minimum admitted cache | 516 bytes | One complete upstream cache buffer |
| Arithmetic minimum ceiling | 3C6Ch | Static end plus 2,564-byte heap |
| Private stack | 1,024 bytes | Provisional; native worst-case measurement pending |

Payload SHA-256:
`15f750e41babe5486030b4d47106a84ac4a120367279f2eef9fd2a02d29f5c43`.
The arithmetic threshold is **not a qualified minimum TPA**. The boundary
checks do not establish native BDOS/BIOS stack high-water or the requirements of
the future renderer, publisher and long-line engine.

## Native bounded gate

`tools/build_native_ted.py` assembles maintained instructions using ZSM4/LINK on
private copies of System/Utilities/work media, compares the complete logical
COM payload with the cross build, and enters `EX` at the legacy `TED>` prompt.
A separate post-exit program verifies resumed CCP execution. The Model 4 run
uses physical keyboard-matrix events; z80pack uses its terminal input stream.
Both retain source, executable, console, disk and execution-hash evidence.

Both native gates passed for the payload above:

| Platform | ZSM4/LINK build | Exact payload parity | Legacy prompt / CCP resumption |
|---|---|---|---|
| z80pack | PASS | PASS | PASS |
| Model 4 / trs80gp | PASS | PASS | PASS |

The receipts, complete input hashes, native source/output files, console and
private disk images are preserved in `TED-Foundation-Evidence.tar.gz` (SHA-256
`784deaf3de5efb04d3f9b0386a73b046adc4b677f5ee4909840e17b655c46b1c`). Its manifest covers 80 files.
Final native results and the evidence archive are recorded in
`TED-Foundation.json`. These are startup/build smoke tests, not full-screen
editing qualification. The existing ADM3A startup modules are sufficient for
these plain-text legacy-prompt tests; this does not qualify the required ANSI
configuration or screen behavior.

## Required release gates still open

| Gate | Status | Missing acceptance |
|---|---|---|
| T01 | PARTIAL | Upstream pinned; development build/parity gate separate; final GPL source companion pending |
| T02 | NOT RUN | Pinned CP/M WordStar 3.3 oracle and full command/prefix fixtures |
| T03 | NOT RUN | Exact terminators, whitespace, TABs, EOF/padding, rejection and save round trips |
| T04 | NOT RUN | 4095-byte lines and bounded split/join/block/replace handling |
| T05 | PARTIAL | Single-cache paging exercised; transactional edits, limits and cancellation pending |
| T06 | NOT RUN | All DU grammar, extents, attributes, aliases and protection decisions |
| T07 | NOT RUN | Staged publisher S0–S8, readback, rollback and ambiguity fault matrix |
| T08 | NOT RUN | Real directory-full/data-full/workspace-full media |
| T09 | PARTIAL | Compiled startup/cache boundary tests; native stack/canaries and final memory map pending |
| T10 | NOT RUN | Installed Utilities B: full editor qualification on z80pack |
| T11 | NOT RUN | Model 4 80x24 VRAM, complete editing commands and physical key matrix |
| T12 | NOT RUN | Final paired images, membership, source companions and complete reruns |

Physical hardware: **NOT RUN**. No ROM/XIP or checked-profile editor acceptance
is claimed.

## Next implementation sequence

1. Freeze the independent WordStar 3.3 oracle, command fixtures and intentional
   safety/preservation differences. The adjacent compatibility corpus's 3.00
   installation is not an accepted replacement oracle.
2. Replace the upstream byte-length/line codec and editing representation with
   bounded chunks carrying exact text and terminator metadata. Preserve literal
   TABs/trailing spaces and CP/M EOF suffixes. Stage load/edit/block operations
   before committing mutations; retain 4095-byte line limits without per-page
   4096-byte buffers.
3. Implement shared exact DU parsing, workspace format/ownership/recovery,
   physical-extent attribute capture, and one checked S0–S8 publisher. Complete
   its failure matrix before removing the save interlock.
4. Implement the complete WordStar dispatcher, opening screen, shared prompts,
   search/replace and byte-range blocks on the preserving engine. Replace
   conflicting legacy bindings and qualify physical aliases and ANSI preflight.
5. Complete native stack/memory measurements and T01–T12 on both exact final
   paired disk generations; only then enable TED membership and produce the GPL
   corresponding-source companion and distribution manuals.

## Test-run dispositions

- Initial cross build assumed a leading 256-byte zero prefix. Udo Munk's output
  for this source begins at the requested origin; the builder now handles both
  forms. This was a harness assertion failure, not a guest failure.
- The first expanded cache test exposed the guest exit DMA-restoration defect.
  The exit adapter was corrected and the complete 21-case suite rerun.
- A Model 4 run using superseded source was explicitly stopped on its private
  disposable media after that correction. It supplies no acceptance evidence.
- The first random-I/O failure assertion assumed an unpadded decimal error
  code. It was corrected to accept the actual zero-padded error display; the
  guest retained its workspace as expected and the complete suite passed.
- Python bytecode compilation initially tried an unwritable host cache; rerun
  with a private temporary cache passed. Registry projections and the registry,
  dependency-map and development-identity tests passed.
- WordStar manual acquisition: both primary Bitsavers host aliases returned
  HTTP 403; the Computer History Museum mirror timed out. No unread manual or
  unpinned oracle was treated as compatibility evidence.
