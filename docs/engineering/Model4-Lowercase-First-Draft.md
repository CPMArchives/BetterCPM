# Model 4 lowercase correction — first implementation draft

Status: engineering draft, 2026-11-03. Native qualification and release
acceptance are pending. Branch: `codex/model4-lowercase-draft`, based on
`fb062255d3ea465cf8ba6a9b77ac0f4a4aac5c32` (PR #565 evidence head).
The production sources at that parent match candidate
`6d6c103507ce8558700b3b8e412ac500de361226`.

## Implemented behavior

The correction remains in the Model 4 matrix translator. It adds lowercase and
software CAPS state while retaining the existing ordinary-key scanner and
physical-key identity rule. No CCP, BDOS, or general console redesign is involved.

At `KEYBASE+128` (`F480h`), bits 0/1 are left/right Shift, bit 2 is Control,
bit 3 is the momentary CAPS contact, and bits 4..6 are function keys. Letters
use the following rule; other matrix positions retain their previous mappings.

| Caps Lock | Neither Shift | Either/both Shift | Control, with any Shift |
|---|---|---|---|
| Off, initial state | a..z | A..Z | 01h..1Ah |
| On | A..Z | A..Z | 01h..1Ah |

This implements the case policy reviewed against Montezuma Micro CP/M and
LS-DOS. It does not transplant either operating system's complete scanner.
Both CAPS edges receive a bounded, nominal 15 ms confirmation delay. Only a
confirmed press toggles case; a confirmed release rearms it. CAPS is polled
before ordinary keys, so it works with a letter held. Repeated scans of that
held letter do not queue a second character, and its already captured byte
keeps its original case.

`M4_KSTATE` packs the confirmed CAPS contact in bit 3 and the lowercase mask
in bit 5. Its initial value is `20h`. Successive press/release pairs produce
`20h -> 08h -> 00h -> 28h -> 20h`. `M4_INIT` preserves this state because it
also serves screen clearing. The delay is nominal instruction timing at
4.05504 MHz; hardware wait states and contact behavior remain native/physical
qualification items. Ordinary-key debounce/release behavior is preserved;
this draft does not add a timed ordinary-key debounce algorithm.

`M4_KEYFD` handles Control before case. Only connected A..Z positions receive
the lowercase mask. `@` and synthetic `[`..`_` matrix slots are excluded.
The editor keys, shifted punctuation, Shift-0, either Shift key,
Control-CLEAR/DEL, BREAK, and Montezuma punctuation chords retain their mappings.
`M4_IN` retains one pending character and compares physical identity, using
`FFh` as the empty identity so slot zero (`@`) remains usable. `M4_ROWS`
establishes `D=0` on every scanner return; the queue clear and Control-table
lookup use that invariant.

## Space and compatibility

The real assembler emits **757 bytes in the existing 757-byte BIOS region**,
`E991h..EC85h`. There is no spare byte and no allocation or TPA expansion.

| Change | Bytes relative to parent |
|---|---:|
| Model 4 keyboard and state, `M4_IN` through console state | +25 |
| Model 4 two-sector overlay fetch and wrappers | -8 |
| Other BIOS code, including final padding | -17 |
| Total | 0 |

Production edits affect three files:

- `src/platform/trs80m4/m4cons.inc`: case, CAPS and compact input handling.
- `src/platform/trs80m4/reload.inc`: factor two-sector reads into `M4_ONE`,
  fall through for the second successful read, and share the configuration
  destination setup. Both sector triples remain arbitrary; first/second read
  failures still return immediately. The RSX selector and IX are preserved.
- `src/bios/bios.mac`: shorter branches, shared exact-zero return, shared
  reader/punch RET, flag-producing LISTST, and a common 128-byte transfer count.
  `BIO_SLOT` addresses all eight 128-byte records in a 1024-byte buffer.

The slot calculation requires a 1024-byte-aligned physical buffer. It derives
the high byte from `BIO_PHYBF`, and the host BIOS builder rejects misalignment.
No disk geometry, transfer size or feature is removed. Monitor helpers stay
outside the region replaced by the cpmsim character adapter. `MONCALL` remains
a JP to `MC_CALL`, whose first instruction is `LD HL,(MP_MON)`, as existing
API 1.7 clients require.

Public/private vector offsets, Model 4 disk-state addresses `EA8Eh..EA99h`, and
the Model 4 monitor binding at `EC84h` are unchanged. Console state now occupies
`EBBFh..EBC4h`; regenerated M4SCRN binds cursor `EBC0h` and column `EBC2h`.
The ownership inventory includes six mutable console bytes rather than five,
because the former padding byte now has state. This adds one byte to the
documented future ROM relocation accounting, within the existing RAM BIOS size.

The shared BIOS compaction also changes the default cpmsim BIOS binary.
Its twelve-byte disk state moves to `EB64h..EB6Fh` and its monitor binding
to `EBFEh..EBFFh`. Generated bindings and the ownership inventory follow those
addresses. Its public vector contract is unchanged, but its previous binary
identity and validation cannot be attributed to this draft automatically.

The Model 4 BDOS, CCP, disk module, extensions, boot sector and stage-one
loader binaries compare byte-for-byte with the parent checkout's build products.
All 563 changed bytes in the 6588-byte resident are within its BIOS region.
Screen providers have been regenerated. Official component version/revision
assignment remains a release preparation decision; this draft is identified
by its source branch and binary hashes, not as an accepted release candidate.

## Verification performed

The following are instruction-level or host build checks, not native hardware
passes. The focused regression executes the assembled production BIOS.

| Check | Result |
|---|---|
| Complete Model 4 system and provider build | PASS; BIOS 757/757 |
| All 56 key positions, 256 modifier bytes, four CAPS states | 57,344 PASS |
| Full matrix scanning and zero-scratch invariant | 448 key scans plus empty scan PASS |
| CAPS stable/transient samples, unrelated modifier noise, held letters, screen clear | PASS |
| Deterministic pending-key/rollover/release traces | 4,096 PASS |
| All eight physical buffer slots | PASS |
| Arbitrary two-sector tables and first/second read errors, mocked physical I/O | 1,536 PASS |
| RSX selector success/error paths and balanced stack | 768 PASS |
| Console/list routing across all IOBYTE values and four provider return values | 5,120 PASS |
| Existing 17 BIOS-vector contracts, all 80 reads/writes, failures and SECTRAN | PASS |
| Production monitor hooks, Model 4 and default cpmsim | PASS |
| M4SCRN/ANSISCRN at both relocation addresses | PASS |
| BIOS overflow, stale BIOS/disk rejection, reproducible rebuild | PASS |
| Model 4 and default cpmsim ROM/RAM ownership checks | PASS |
| Registry projections | PASS |
| `M4_EDITOR_KEYS=0` physical-read diagnostic | Assembles, 453/512 bytes |

`tools/test_bios_build.py` now copies its required metadata into the disposable
fixture. The bounded Z80 runner adds generic BIT support. The keyboard helper
types requested uppercase commands with actual Shift, and offers
`preserve_case=True`. The native modifier diagnostic now covers lowercase,
all Shift/Control combinations with both lock states, CAPS during held input,
and the prior punctuation/editor cases. The overlap diagnostic expects its
unshifted physical A/B input as lowercase.

One unrelated check remains failing: `tools/test_subsystem_versions.py` expects
the literal banner in `src/cpx/rcp.mac`, which now contains the generated
`@rcp-version@` placeholder. The same failure was reproduced in the untouched
parent checkout. It is not counted as a passing check or changed in this draft.

## Reproduce and finish qualification

On a fresh worktree, the existing complete-build script needs two bootstrap
artifacts before its first utility pass. Build `boot.bin` with the existing
`build_trs80_boot.assemble` helper and run `tools/build_rsxselect.py`, then:

```sh
python3 -B tools/build_complete_system.py
python3 -B tools/test_model4_keyboard_case.py
python3 -B tools/test_bios.py
python3 -B tools/test_monitor_bios_hooks.py
python3 -B tools/test_ccpreload.py
python3 -B tools/test_bios_build.py
```

For the additional cpmsim/provider checks:

```sh
python3 -B tools/build_z80pack_boot.py --resident-only --ram-only --system-tracks-only
python3 -B tools/test_monitor_bios_hooks.py --z80pack-build build/z80pack
python3 -B tools/test_rom_ownership_inventory.py --platform z80pack --listing-root build/z80pack
python3 -B tools/test_screen_backends.py
```

The screen test requires pyte; this run used the existing parent qualification
installation at `build/rc564-conformance/python-deps` via PYTHONPATH.

The attempted native modifier test assembled its probe and prepared private
media, then stopped before launching trs80gp. The host returned LaunchServices
`1100` (`BOOTSTRAP_NOT_PRIVILEGED`). From a normal Terminal in this worktree,
using a fresh report directory:

```sh
python3 -B tools/test_model4_keyboard_modifiers.py --report build/case-native-terminal-1
python3 -B tools/test_trs80_keyboard_overlap.py
```

Before release acceptance:

1. Review the three production edits and the scratch-register/alignment
   contracts; assign the new component/candidate identity.
2. Complete those native keyboard tests. Manually check lower/uppercase at the
   CCP, mixed-case TED editing/save/reopen, and distinct lowercase/uppercase
   SEARCH patterns. Exercise warm boot, screen clear and shipped terminal providers.
3. Re-run the reviewed Model 4 conformance batch on a newly identified
   distribution image, covering disk transfer, warm reload and overlay paths.
   The earlier 269 native passes remain evidence for the earlier candidate.
4. Requalify affected cpmsim character, monitor, disk-state binding and reload
   paths because its BIOS binary changed. Retain the 627-card reconciliation
   and profile differences 0020/0493/0494 as historical evidence, not fresh passes.
5. Treat physical contact/timing qualification separately from emulator results.

## Candidate preservation

The original checkout and its evidence are unchanged. The previously validated
distribution disk remains at
`../BetterCPM-release-push/build/rc564-systems/trs80gp/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`.
Its SHA-256 was rechecked as
`4105ff45e411e25c0f3cd6024b970ddc231e6287086a553933e1fb577aaf2467`.

This worktree's draft development image is a separate product, not that
distribution disk. Current hashes are recorded in
`Model4-Lowercase-First-Draft.json`. No PR or release acceptance is implied.
