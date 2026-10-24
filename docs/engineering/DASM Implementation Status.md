# DASM implementation and qualification status

Development checkpoint, 2026-10-25. This is **not release acceptance** and does
not supersede [the specification](DASM%20Specification.md). DASM and DSYM are
not yet added to release Utilities Disk images. No physical Model 4 hardware
qualification is claimed.

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
- Private 512-byte stack, BDOS wrapper, startup active-ceiling check, bounded
  8 KiB binary workspace, symbol/control/comment insertion limits, staged
  binary reload, guarded decoder/dump/search accesses and orderly `G` return.
- Confirmed Ctrl-C abort closes and retains staged output without publishing,
  checks close failure, restores caller state and exits. Restart is refused
  while an ASM transaction is pending. Non-Ctrl-C interruption and the wider
  console-cancellation matrix still require qualification.
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
- DSYM accepts the observed LINK 1.3 four-hex-digit/name pairs, case folds,
  sorts names, coalesces identical duplicates and rejects conflicting names,
  malformed input, overlength identifiers and more than 255 unique names.
  Aliases and values 0000/FFFF survive conversion. New-only `.DSY` publication
  prevents replacement of the `.SYM` input or an existing output.
- Host reference converter `tools/dsym_reference.py` implements that identified
  dialect, with exclusive output creation. It does not parse REL objects,
  arbitrary listings or unresolved external symbols.

## Development command contract

All numeric command arguments below use hexadecimal, as upstream does. The
loaded binary is explicitly named with `.COM`; other arbitrary input suffixes
are not yet accepted. A minimal reconstruction is:

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

`DSYM INPUT.SYM [destination-drive:]` writes `INPUT.DSY`; load it with
`RINPUT.DSY` after loading the binary. Its source is the final LINK symbol
file, not an assembler-relative symbol table. A default LINK fixture with
CSEG and DSEG yielded `0100 START<TAB>0104 HELLO<TAB><CRLF>` and linked bytes
`11 04 01 C9 00`; conversion must preserve those final addresses.

| Commands | Current behavior |
| --- | --- |
| H, ?, DS, C, ; | Inherited help/statistics/table inspection; broader UI qualification pending |
| L, QL, D, F | Retained listing/dump/search with input bounds; pagination/cancel campaign pending |
| A, B | Inherited data recognition and automatic symbol generation, bounded insertion; broader behavioral qualification pending |
| E, K, ;address,text | Symbol/comment editing retained with validation; reserved-word rules and full atomic-validation audit pending |
| Caddress,type | Control classifications retained; import ordering/collision work pending |
| O, I | Inherited offset/rebase workflow; wrap-safe logical-address redesign pending |
| P, Sname.ASM, Z | Absolute source prologue, staged listing output and explicit publication |
| R/S .SYM/.CTL/.DOC | Individual component operations; import normalization/order/collision requirements incomplete |
| R .DSY | Canonical native converter output |
| R/S .ALL | Explicitly refused: descriptor-based session transaction is not implemented |
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

## Measured development layout

The current DASM image is 14,080 bytes, SHA-256
`73049f2e30b85bccd31f79ee453f1994abbae43d37c18306bd121a084eaf00f8`.
Its arena declarations place control storage at 3800..3DFF, live symbol storage at
3E00..4DFF, input at 4F00..6EFF, comments at 6F00..76FF and temporary staging
at 7700..96FF. The startup check therefore requires active BDOS entry/ceiling
word 0006H to be at least **9800H**, including the 256-byte margin. This is a
fixed-capacity implementation; it refuses a smaller TPA rather than shrinking
its arenas. The symbol insertion guard ends at INITOFF (4E00H), preserving the unused
4E00..4EFF gap and the declared 4 KiB symbol budget.

Full-core edge tests accept an 8,192-byte file, refuse 8,193 bytes, reject
zero/overlong logical lengths, accept the exact 9800H startup ceiling and refuse
97FFH. A resident-memory canary from the supplied ceiling through D7FFH must
remain untouched in every command campaign. This supplements, rather than
replaces, the required resident-module campaign on real platform media.

DSYM is 7,158 bytes, SHA-256
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

1. Complete validated metadata normalization, name/conflict/reserved-word rules,
   ordering and line-number diagnostics. Audit invalid edit/rebase commands for
   mutation before complete validation. Complete multi-role alias protection.
2. Implement session descriptor publication last, unique component generations,
   binary/component hashes and all-or-nothing validated load. Keep `.ALL`
   unavailable until this exists; individual safe saves are not a substitute.
3. Complete wrap-safe logical addressing, empty-input policy, cancellation and
   restart recovery, exact capacity edges, resident-module canaries and active
   TPA diagnostics on both platform personalities.
4. Add verified LINK success evidence: failed LINK runs still emit valid-looking
   SYM pairs, including unresolved names at 0000H. Current DSYM cannot detect
   that from SYM alone. Extend DSYM to the shared drive/user grammar and line/count diagnostics;
   qualify multi-module exports, absolute equates, long-name/significance and
   unresolved-external negative fixtures against native LINK.
5. Complete the specified full file-failure/media-full/recovery matrix and
   terminal interaction campaign on both targets. The automated BDOS fault
   harness does not replace actual filesystem/emulator tests.
6. The [baseline functional receipts](DASM%20Development%20Qualification.md) bind
   the current candidate on fresh current System pairs. Requalify after the
   remaining implementation changes, then integrate owned DASM/DSYM version
   metadata, notices, source package and
   disk manifests/builders. Rebuild and qualify actual Utilities Disk artifacts.

These are outstanding requirements, not silently relaxed acceptance criteria.
