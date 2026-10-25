# BetterCP/M TED adaptation

Hector Peraza's TED is adapted under GPL-2.0-or-later. The complete immutable
upstream snapshot is in `third_party/ted/`, pinned at
`7da2e1e39ae4cb57b45d84cf715b88fabbeadd17`. `COPYING` contains the GPL;
original source notices remain intact. BetterCP/M's adaptation identity is
TED 1.0 revision 001; build records and qualification are separate.

The agreed interface retains TED's screen, browse and command modes. WordStar
sequences dispatch TED line-range/file operations; only word-left, word-right
and delete-word are added. There is no ^Q prefix, persistent block marking,
undo, repeat-find or new opening screen. See the command matrix in
[the specification](../../../docs/engineering/TED%20Specification.md).

## Storage and interaction

- `text.mac` validates streamed physical records without rewriting text.
- `workspace.mac` keeps an immutable, checked checkpoint with literal byte
  segments, 24-bit offsets and a single 512-byte random-read page cache.
- `inline.mac` buffers one dirty line, at most 4095 bytes. Ordinary typing has
  no per-character checkpoint writes. Leaving that editing line for another
  edit, larger operations and saving flush it through a verified transaction.
  A failed flush retains the RAM text. Recovery restores the last committed
  checkpoint; it is not per-keystroke automatic saving.
- `publisher.mac` implements staged writes, checked close/readback, original
  identity/attribute checks, unique retained backup and bounded rollback.
  Publication never erases a destination to make room for its replacement.
- `lines.mac` composes whole-line transfers with at most eight segments and
  supplies only required separators at new boundaries.
- `commands.mac`, `search.mac` and `operations.mac` adapt TED operation semantics
  to preserving storage. The obsolete lossy record engine remains separately
  identifiable in the maintained upstream modules and is not linked into the live COM.
- `frontend.mac` uses callable SCRN 1.1 and MCON 1.2, explicitly loaded before
  TED. Rendering queues input at row and disk-read boundaries; publication
  queues input without allowing a late cancellation. No app-driven extension loading, terminal query, video-memory access or
  keyboard-matrix access occurs. The private stack is 2048 bytes with a 32-byte
  low canary. Every live buffer is statically bounded below `TED_END`.

Retain TAB, spaces, original terminators and no-final-newline. No-edit full-file
writes retain every physical EOF-padding record. Changed text receives only
necessary final-record 1Ah padding. Unsupported text and overlong lines are
refused with diagnostics before replacing the active document.

The checkpoint header records the identity at checkpoint time. Naming a newly
saved unnamed document may leave its earlier checkpoint unnamed until the next
checkpoint; recovering it therefore requires an explicit output filename.
No pre-existing checkpoint is deleted merely because its format is recognized.

## Build and validation

```
python3 tools/build_ted.py --output build/utilities
python3 tools/test_ted_text.py --output build/ted-text.json
python3 tools/test_ted_publisher.py --output build/ted-publisher.json
python3 tools/test_ted_workspace.py --output build/ted-workspace.json
python3 tools/test_ted_commands.py --output build/ted-commands.json
python3 tools/test_ted_frontend.py
```

The builder verifies every pinned upstream file, flattens module-local symbols,
materializes reserved bytes and emits TED.COM, TEDDEV.COM, native TEDNAT.MAC,
a listing, source map and component build record. Identical native source is
assembled with external ZSM4/LINK; their versions remain outside BetterCP/M
owned numbering. A build or assigned identity does not assert qualification.

`qualify_ted_engine.py` checks native storage/recovery APIs;
`qualify_ted_editor.py` checks actual full-editor terminal interaction. Both use
disposable copies of paired media and bind evidence to source/payload hashes.
The original foundation receipt remains historical and does not qualify this
later implementation. Current acceptance is recorded in
[TED Qualification](../../../docs/engineering/TED%20Qualification.md).
