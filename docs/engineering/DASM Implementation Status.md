# DASM implementation and qualification status

Development checkpoint, 2026-10-25. This is **not release acceptance** and does
not supersede [the specification](DASM%20Specification.md). DASM, DSYM and DLINK are now provisional Utilities members; their final
release acceptance is still pending. No physical Model 4 hardware
qualification is claimed.

## Current source checkpoint (after qualified baseline)

The maintained source now additionally provides lexical symbol lookup/import,
alias preservation, exact duplicate coalescing, name/value conflict rejection,
and a generated 224-word reserved-vocabulary guard from the pinned ZSM4 source.
Internal identifiers are checked for collisions in the first 15 characters.
All names receive EQU declarations in generated source, including aliases and
symbols inside instruction operands; hexadecimal literals are unambiguous.

DASM preserves annotation case, rejects unsupported control bytes before edits,
validates control types and trailing arguments, and accepts shared exact DU
operands with users 0..31. Metadata accepts horizontal whitespace and CR/LF/CRLF;
syntax errors report a line number, and successful imports report imported and
coalesced counts. Symbol rebasing uses a validation pass before any value changes,
accepts an explicit + or - magnitude and refuses address overflow. Interruption
also poisons pending source output when Ctrl-C is declined or another key stops
listing, so a subsequent Z cannot publish an interrupted file.

The file state separates an open staged FCB from a retained staged identity.
Close and rename failures cannot close a stale renamed FCB. Every file close
selects its owning user, including input cleanup after errors; rejected or
read-only output requests leave no phantom pending transaction. DSYM now uses
shared single-DU parsing and restores the caller's user after each file operation,
with line-number and imported/coalesced/rejected diagnostics.

Logical origin is now selected with `Ohex`; the buffer bias is private. P and
explicit listing ranges accept the end-exclusive `10000`, reject overflow and
validate both bounds before changing PC or writing source. The final four bytes
at the top of the address space use literal DB output. Non-0100H origins use
ORG 100H plus PHASE/DEPHASE for a packed reconstruction. Native LINK drops a
one-byte absolute image; that case emits one explicit 1Ah padding byte after
the declared logical interval. All qualification comparisons retain the logical
length and validate padding separately. FFFF is a usable control,
comment and symbol address, with type/length zero as the table terminator.
The S classification also emits initialized DB bytes in exact reconstruction.
Automatic A/B analysis snapshots its control/symbol tables and restores them on
capacity or range refusal, including dense-label and dense-data campaigns.

Version-2 `.ALL` save/load now uses the descriptor described in
[DASM Session Format](DASM%20Session%20Format.md). It records logical origin and
length, canonical binary identity/logical CRC32 and three unique component
identities/physical record counts/CRCs. Saves preflight the descriptor destination,
publish new component generations and publish the descriptor last. Loads stage
all three validated tables before committing any. Fault tests cover each create,
write, close and rename, binary/component/descriptor corruption and cross-user
session save/load. Retained new scratch and component identities are reported.

The current host campaign passes **161 DASM, 73 DSYM and 40 DLINK full-core cases**, plus
**71 USQ regression cases** after the optional shared file-I/O hook was added.
These changes are not covered by the earlier native receipts below. They require
a fresh native build and both-platform campaign before acceptance.

## Implemented

- Preserved original SIG/M 91 DASM source, both mnemonic tables, binary,
  catalog, READ.ME and unsigned submission template under `third_party/dasm`,
  with byte counts, SHA-256 values and the maintainer's accepted historical
  redistribution/modification basis. Conn, Barker and Christensen remain credited.
- Maintained Zilog DASM adaptation and native `DSYM` converter. Munk z80asm is
  the host assembler; packaged **ZSM4 4.7 and DRI LINK 1.3** are the native
  toolchain. Their binaries, upstream versions and notices remain unchanged.
- Deterministic source preparation flattens includes, orders dependent arena
  definitions and expands reserved bytes for native/cross byte parity. Default
  output uses `.Z80`, `ASEG`, `ORG`, initialized bytes and `END`.
- Buffered instruction output permits literal DB fallback for truncated,
  unsupported and noncanonical encodings. ED aliases and ignored prefixes must
  not silently change bytes. ZSM4 numeric JR/DJNZ targets include `+($-$)`:
  ZSM4's expression evaluator otherwise treats a bare numeric target as an
  offset. This was found by native corpus testing, not host reassembly.
- Private 512-byte stack, BDOS wrapper, startup active-ceiling check with measured
  required/active bounds, early 16-bit read-only-drive-vector refusal, bounded
  8 KiB binary workspace, symbol/control/comment insertion limits, staged
  binary reload, guarded decoder/dump/search accesses and orderly `G` return.
- Confirmed Ctrl-C abort closes and retains staged output without publishing,
  checks close failure, restores caller state and exits. Restart is refused
  while an ASM transaction is pending. Ordinary-key interruption and declined Ctrl-C invalidate pending source output.
  The wider native console-cancellation matrix still requires qualification.
- Binary reads retain all physical CP/M record bytes, including 00/1A/FF.
  `Nhex` explicitly chooses a nonzero logical length up to the readable extent.
- DASM resolves drive/user/name identities. Individual output saves reject
  the loaded binary as a destination, refuse read-only replacement, reserve
  unused scratch names, check writes and close, retain a unique old-file backup
  and publish by rename. Failure after backup rename retains both recovery
  identities rather than erasing the only complete old copy.
- Metadata reads stage complete tables and commit after successful validation
  and close. Malformed records, oversized tables and meaningful data after a
  text terminator are rejected. Arbitrary comment-assembly injection is refused.
- DSYM accepts complete checked LINK 1.3 reports, case folds,
  sorts names, coalesces identical duplicates and rejects conflicting names,
  malformed input, overlength identifiers and more than 255 unique names.
  Aliases and values 0000/FFFF survive conversion. New-only `.DSY` publication
  prevents replacement of the `.SYM` input or an existing output.
- Host reference converter `tools/dsym_reference.py` implements that identified
  dialect, with exclusive output creation. It does not parse REL objects or arbitrary listings. Its public command requires a
  complete report; the bare-pair helper is only an internal reference grammar.

## Development command contract

All numeric command arguments below use hexadecimal, as upstream does. The
startup binary operand may use any exact 8.3 suffix; interactive R uses `.COM`
to select binary input. Empty binary input is refused explicitly. A minimal reconstruction is:

```text
DASM
RINPUT.COM
N5
SOUTPUT.ASM
P100,105
QL100,105
Z
G
B:ZSM4 OUTPUT=OUTPUT.ASM
B:LINK OUTPUT[A]
```

`DSYM [DU:]INPUT.LOG [destination-DU:]` writes `INPUT.DSY`; load it with
`RINPUT.DSY` after loading the binary. Its source is a complete DLINK final-address report, as described in
[DASM Symbol Conversion](DASM%20Symbol%20Conversion.md). A bare SYM is refused. A default LINK fixture with
CSEG and DSEG yielded `0100 START<TAB>0104 HELLO<TAB><CRLF>` and linked bytes
`11 04 01 C9 00`; conversion must preserve those final addresses.

| Commands | Current behavior |
| --- | --- |
| H, ?, DS, C, ; | Inherited help/statistics/table inspection; broader UI qualification pending |
| L, QL, D, F | Retained listing/dump/search with input bounds; pagination/cancel campaign pending |
| A, B | Inherited data recognition and automatic symbol generation, bounded insertion; broader behavioral qualification pending |
| E, K, ;address,text | Symbol/comment editing retained with validation; reserved-word validation implemented; remaining atomic-validation audit pending |
| Caddress,type | Control classifications retained; imports sorted with conflict rejection |
| O, I | Checked logical origin; two-pass signed-magnitude symbol rebasing |
| P, Sname.ASM, Z | Absolute source prologue, staged listing output and explicit publication |
| R/S .SYM/.CTL/.DOC | Individual component operations; normalized/sorted imports; remaining session work pending |
| R .DSY | Canonical native converter output |
| R/S .ALL | Versioned, checksummed descriptor; unique components; validated staged load |
| U | Fixed comment arena only; arbitrary relocation refused |
| X | Restart refuses a pending output transaction |
| G | New orderly return restoring caller stack, DMA and user state |
| Nhex | New explicit logical input length, 1..8192 bytes |
| /VER, /HELP | Noncreating startup identity/usage queries; detailed interactive help is H |

## Reproduction and test tools

From the repository root:

```text
python3 tools/build_dasm.py
python3 tools/build_dsym.py
python3 tools/test_dasm.py
python3 tools/test_dsym.py
python3 tools/test_dlink.py
python3 tools/test_usq_com.py
python3 tools/qualify_dasm.py --system SYSTEM_ROOT --utilities UTILITIES_ROOT --output NEW_OUTPUT
python3 tools/qualify_dasm_corpus.py --system SYSTEM_ROOT --utilities UTILITIES_ROOT --output NEW_OUTPUT
```

On Model 4, a temporary test-only wrapper supplies BDOS function-10 input,
lowers the active TPA ceiling to its interceptor, and restores the original
BDOS vector on return. The disassembler core differs only in its entry jump;
its original entry is called by the wrapper. All file operations use real
BetterCP/M. The wrapper itself has a native z80pack reconstruction smoke test.
This avoids timing-dependent physical-key injection and does not qualify the
keyboard, terminal line editor or cancellation.

The native runners need cpmtools, the existing BetterCP/M disposable System
artifact reports, the packaged Utilities images containing ZSM4/LINK, z80pack
and/or trs80gp. Pass explicit artifact roots: the development default is a
local checkpoint path and is not a portable release dependency. On macOS the
Model 4 runner uses the existing LaunchServices helper. Every run copies the
media, records tool/media/output hashes, checks extracted results and verifies
that the original System and Utilities images are unchanged.

The full-core harness deliberately clobbers BDOS-volatile registers and can
inject make/read/write/close/rename failures. It exercises compiled COM code,
not a Python implementation of DASM or DSYM. The corpus enumerates byte values
in base, CB, ED, DD, FD, DD-CB and FD-CB contexts, plus raw data. This is broad
reconstruction coverage, **not every possible instruction stream**.

## Measured qualified-baseline layout

The qualified baseline DASM image is 14,080 bytes, SHA-256
`73049f2e30b85bccd31f79ee453f1994abbae43d37c18306bd121a084eaf00f8`.
Its arena declarations place control storage at 3800..3DFF, live symbol storage at
3E00..4DFF, input at 4F00..6EFF, comments at 6F00..76FF and temporary staging
at 7700..96FF. The startup check therefore requires active BDOS entry/ceiling
word 0006H to be at least **9800H**, including the 256-byte margin. This is a
fixed-capacity implementation; it refuses a smaller TPA rather than shrinking
its arenas. In that baseline, the symbol insertion guard ends at INITOFF (4E00H), preserving the unused
4E00..4EFF gap and the declared 4 KiB symbol budget.

Full-core edge tests accept an 8,192-byte file, refuse 8,193 bytes, reject
zero/overlong logical lengths, accept the exact 9800H startup ceiling and refuse
97FFH. A resident-memory canary from the supplied ceiling through D7FFH must
remain untouched in every command campaign. This supplements, rather than
replaces, the required resident-module campaign on real platform media.

The qualified-baseline DSYM is 7,158 bytes, SHA-256
`14633f5eb500f2b9955a901d97d386b46fda51dd699e4253ebe7aaa07a22ac94`.
Its fixed table holds at most 255 names of at most 12 characters; it makes its
own active-TPA check before opening files.

## Historical baseline

The reference build is kept separate (`build_dasm.py --reference`). With the
current host assembler it produces 9,472 bytes, SHA-256
`5cba8033e8f0b0cf935d62b8ae5f15714a600450d45893e0da8877f311a9c276`.
There are 291 differing bytes against the archived 9,472-byte COM, all at
absolute addresses 24DD..25FF. The first difference is precisely upstream
`RELEND`, the beginning of mutable reserved variables. The range also contains
`INBUF`, reserved stack storage and the last page's padding. Host bytes there
are FF; archived bytes are 00 except one 4B. All preceding instruction and
initialized data bytes match. This reproduces the executable portion, **not**
the archived COM byte-for-byte; the archived binary remains unmodified.

## Remaining acceptance work, in priority order

1. Native qualification of the current metadata, origin/range and session
   implementation. Complete diagnostic precision for conflicts found during
   metadata sorting and the remaining automatic-analysis edge audit.
2. Run the session publication-state and corrupted-component cases on actual
   filesystem/emulator media, beyond the independent full-core fault model.
3. Complete resident-module canaries, active TPA diagnostics and ordinary console
   cancellation/pagination/backspace on both platform personalities.
4. Qualify the new DLINK capture and strict DSYM report workflow on both targets.
   The native z80pack multi-module/negative campaign passes. Complete its Model 4
   campaign and the remaining native caller-state/media-failure witnesses.
5. Complete the specified full file-failure/media-full/recovery matrix and
   terminal interaction campaign on both targets. The automated BDOS fault
   harness does not replace actual filesystem/emulator tests.
6. The [baseline functional receipts](DASM%20Development%20Qualification.md) bind
   the current candidate on fresh current System pairs. Requalify after the
   remaining implementation changes, retain the new owned numeric identities, notices and complete source package.
   Rebuild and qualify the actual provisional Utilities artifacts.

These are outstanding requirements, not silently relaxed acceptance criteria.

### Direct-console cancellation correction

DASM work output and confirmed break input use BDOS direct-console function 6, so cooked-console Ctrl-C cannot bypass staged-output cleanup during a listing. DSYM polls for cancellation during input and output; DLINK intercepts child console input, status and output, and refuses to publish a successful log after cancellation. Cleanup restores caller state before diagnostic output. The CP/M command-line editor remains the operating system’s function 10. Final packaged native console qualification is recorded separately.

### Input-buffer and stack boundary

The command buffer reserves the maximum 80 characters, count and size bytes, and the trailing BDOS carriage return. A full-length command previously wrote its carriage return into the first private-stack byte; the added guard test detects that case. Across all 161 host campaigns the measured private-stack high-water mark is 44 of 512 bytes, with the bottom 32 bytes unchanged. This is observed test coverage, not a proof about arbitrary future code or BIOS stack use.
