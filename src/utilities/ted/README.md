# TED adaptation — development foundation

This directory is an incomplete adaptation of Hector Peraza's TED, under
GPL-2.0-or-later. It is **not** the editor specified in
[the adopted specification](../../../docs/engineering/TED%20Specification.md)
yet. Do not use it to edit valuable files. No `TED.COM` is distributed.

The immutable complete upstream snapshot, original build files, documentation,
license, git archive and per-file hashes are in `third_party/ted/`. Maintained
assembly files retain their upstream copyright/license notices. `COPYING`
contains the GPL. The adaptation is registered as pending, without an assigned
public executable revision; ZSM4 and LINK remain external components.

## Implemented foundation

- Deterministic module flattening preserves public linkage and gives private
  symbols module-specific names. Both assemblers consume the same instructions.
  Reserved storage and terminal-patch-area holes are materialized explicitly.
- Capture the active gateway ceiling before interactive initialization. Reserve
  the full 2048-byte map below all 516-byte cache buffers. Check subtraction
  before cache allocation. The static private stack is provisionally 1024 bytes.
- Select an absent `TEW00000.$$$` through `TEW00999.$$$`, using exact-name,
  wildcard-extent directory searches and private search DMA. Do not erase an
  existing workspace. Acquire ownership only after MAKE succeeds. Failed startup
  cannot close or delete a workspace belonging to another session.
- Refuse cleanup after a failed workspace close. Fatal errors retain workspace
  files. Exit restores the normal 0080h DMA address.
- Refuse existing destinations in the low-level output adapter. The legacy W
  command is interlocked: it reports that the publisher is unavailable, returns
  failure, and does not clear dirty state. Its old body remains visibly separate
  as unreachable reference code for the serializer refactoring.

## Build and bounded checks

```sh
python3 tools/build_ted.py
python3 tools/test_ted_foundation.py --output build/ted-foundation.json
python3 tools/build_native_ted.py --system SYSTEM_ROOT --utilities UTILITIES_DIR --output NEW_EVIDENCE_DIR
```

`build_ted.py` writes only `TEDDEV.COM` under `build/ted-development/`, never
`build/utilities/TED.COM`. Native builds use the pinned external ZSM4/LINK on
private disk copies. Their output is compared over the exact executable length;
only verified final-record 1Ah padding is excluded. The native startup test
uses the **legacy TED prompt**, not a WordStar-compatible editing session.

## Work still required

The upstream 162-byte line representation, space/tab transformations, newline
handling, prefix bindings, prompts and publication lifecycle are not accepted
implementations of the specification. WordStar compatibility, exact text
preservation, 4095-byte lines, all-DU operation, staged publication/rollback,
recovery, terminal preflight and both-platform T01–T12 qualification remain
required. The arithmetic startup threshold is not a qualified minimum TPA or a
native stack measurement. Keep the Utilities builder's TED entry pending.
