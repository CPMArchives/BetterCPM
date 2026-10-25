# TED implementation pause — 2026-10-25

Historical pause checkpoint. The user subsequently requested resumption; see TED Qualification.md for current status. Do not treat this checkpoint as qualified. Last previously pushed commit: 42a0859. At the pause this WIP checkpoint was intentionally local and incomplete. The later push includes it as historical context, not as acceptance.

## Scope and implementation

The specification contains the agreed key bindings. Keep TED behavior, with only the approved small word-navigation/deletion additions. No undo, persistent block marks, Q prefix, repeat-find or KD. K C/V/Y prompt line numbers and invoke line operations; K R/W/S/X/Q invoke TED file operations. Z returns to command mode; C pages down; O next tab stop; U screen top/bottom; retain Q/L/N; W unused; underscore redraw. Preserve modal screen/browse/command behavior and overwrite-mode Backspace blanking; insert-mode Backspace deletes, and line-start Backspace joins.

Live modules: text, publisher, workspace, commands, search, frontend, operations, inline, lines, stack. Obsolete lossy legacy engine is no longer linked into the live COM; immutable third_party/ted stays untouched. Builder emits TED.COM, identical TEDDEV.COM, native TEDNAT.MAC, map/listing and component build report. About 30 KB payload after eliminating unused legacy engine.

Storage uses immutable disk checkpoints, checked staged publication, retained unique backups, 24-bit offsets and one 512-byte cache. One 4095-byte dirty line is buffered in RAM; flush on structural operation/save, retaining RAM edits on failure. Recovery is last committed checkpoint, not keystroke autosave. Lines composer supports eight segments and adds only necessary whole-line boundary separators. All live buffers and private 2048-byte stack lie below TED_END; exclusive word6 ceiling is checked before using private stack. Stack low guard and inline RAM guard are 32 bytes each.

Initial TED 1.0 revision 001 metadata is assigned, but input baselines are NOT installed; current builds remain development identity. Do not claim public release or qualification. External ZSM4/LINK remain excluded from owned version numbering.

## Confirmed upstream defects addressed

Erase-before-create save; fixed EDITOR.TMP collision; trailing-space removal/overlong truncation; R restoring old modified flag and range W clearing it. Tests also caught adaptation-specific zero-count LDIR and keyboard buffering issues. Do not conflate these with upstream bugs or intentional TED overwrite behavior.

## Evidence and exact limits

Latest reruns: compiled text 140 PASS, publisher 178 PASS. Prior current command suite 100 PASS, frontend 19 PASS, workspace 41 PASS; rerun all against final frozen source. Earlier native API campaigns and interactive campaigns passed, but hashes predate the final source: do not relabel as final acceptance.

/private/tmp/ted-native-capacity-cpm-1/report.json: PASS native ZSM4/LINK parity, storage/recovery/publisher plus actual full-data, one-free-block and full-directory failure tests under z80pack. API probe stack high water 34 of 2048 bytes; not a full UI stack measurement.

/private/tmp/ted-native-capacity-m4-1: INTERRUPTED on user pause, no PASS. Stopped only controller PID48361 and its disposable emulator PID48379. Other user emulators were left alone. Restart in a fresh output directory when resuming.

Earlier Model4 buffered UI campaign /private/tmp/ted-editor-m4-buffered-1 passed startup/edit/save/exit, but with older 39826-byte payload. Engine /private/tmp/ted-engine-native-1 passed both platforms on earlier source. Full editor campaign script tools/qualify_ted_editor.py currently exercises only one edit, K S replacement and K Q exit. It does NOT yet qualify every command group or final installed media.

A local ignored backup build/ted-pause-20261025/private-evidence.tar.gz preserves private temp campaigns, system images, and research artifacts. It includes copyrighted WordStar references: do NOT commit/distribute it. Test JSON snapshots copied beside it. Frozen system pair originally /private/tmp/dasm-fresh-systems/release-370060c2c289-8856bd3f4c44; existing Utilities images build/dasm-qualified-utilities. Emulator/tool paths and conventions are in the campaign scripts. Native tools external third_party/zsm4/ZSM4.COM and third_party/dri-link/LINK.COM. Host assembler ~/bin/z80asm.

## Remaining before completion and push

1. Finish Model4 real-capacity API campaign; fix any failures. Native UI qualification should additionally measure stack/inline guards, cover prompted C/V/Y and R/W/X, cancel/failure paths, and files larger than TPA on both platforms. Do not claim physical hardware testing.
2. Inspect retained TED command-language gaps: search-index displacement and command-field history/editing keys are not fully ported. Preserve existing semantics rather than add new features. Add guard checks and appropriate edge cases to tests.
3. Model4 raw arrow bytes collide with control commands (up=K, down=J etc). Use primary control navigation, document that optional physical arrows cannot all be distinguished through existing public ASCII API; do not change OS ABI/matrix to hide this.
4. Add Utilities Disk integration, TED.TXT/COPY notices, deterministic GPL source companion and exact-binary/image-bound qualification. Existing disk builder still lacks TED. Preserve old receipts; new image hashes do not inherit old image-bound qualification.
5. Freeze source and README, install only initial TED input reference baselines without bumping other components; stable assigned 001 payload then native ZSM4/LINK parity and final tests on both platforms.
6. Record current qualification separately from historical TED foundation receipt. Current docs/engineering/TED Qualification.md still describes foundation; do not overwrite historical evidence as if current.
7. Commit final implementation/evidence, push everything as previously authorized, verify remote and clean status. Pause checkpoint itself is not pushed.

Do not edit synced parent sources/ or pinned upstream. No subagents authorized. User-facing updates should distinguish confirmed tests from outstanding qualification.
