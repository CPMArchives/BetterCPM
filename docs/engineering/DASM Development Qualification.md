# DASM development qualification

This is a functional development campaign, **not full specification acceptance
or Utilities Disk release acceptance**. See the outstanding requirements in
[DASM Implementation Status](DASM%20Implementation%20Status.md). DASM/DSYM are
not added to release disk manifests by this checkpoint.

The tested DASM candidate is 14,080 bytes, SHA-256
`73049f2e30b85bccd31f79ee453f1994abbae43d37c18306bd121a084eaf00f8`.
DSYM is 7,158 bytes, SHA-256
`14633f5eb500f2b9955a901d97d386b46fda51dd699e4253ebe7aaa07a22ac94`.
Native tool identities remain unmodified ZSM4 4.7 and DRI LINK 1.3.

## Current paired media

Fresh default System disks were built and booted from repository revision
`370060c2c289`, including the current BDOS extent handling and development
identity. Their filesystem, installed-file, configuration-fingerprint and boot
checks pass. The boot validator initially expected the old concise frozen-core
identity; it was corrected to match the existing development identity, with
14 distribution failure-gate tests passing. No System runtime behavior was
changed for this qualification.

| Target | Fresh System SHA-256 |
| --- | --- |
| z80pack/cpmsim | `b9a616bafec41dc4c3206e5054712c88ead80624fde0e56b5899c09d1be7c7d1` |
| Model 4/trs80gp | `578bc34cb377537e47a7e9bb1f019b20ffd9b98abc36e8acee74dfb56056eb43` |

The fresh Model 4 boot reports **50K TPA available** after the normal M4SCRN
and ADM3A startup. The cpmsim boot reports **53K** before its separate provider
probe (51K with ZPRTC loaded). These are the platform manager's rounded KiB
diagnostics, not a claimed exact byte-level ceiling. DASM's checked fixed layout
requires 9800H as its exclusive active ceiling, and its functional input limit
is 8 KiB. The scripted harness installs its interceptor near A000H, below the
reported normal ceiling, further reducing the active ceiling during the tests.

The pinned Utilities B: images supply the existing external toolchain. These
campaigns use disposable copies; original System and Utilities images must
remain byte-identical. No physical Model 4 hardware result is claimed.

## Campaign contracts

1. **Native integration:** build DASM and DSYM with ZSM4/LINK, compare each
   executable to the host build (accounting only for explicit 1Ah final-record
   padding), build/link a code/data fixture, convert its final LINK symbols,
   load them into DASM, generate source and reassemble/link the five logical
   bytes. Assembly errors or unresolved symbols fail the gate.
2. **Opcode/data reconstruction:** compare every logical byte of eight fixtures
   covering base, CB, ED, DD, FD, DD-CB, FD-CB and raw data. The scripted run
   reloads all eight inputs in one DASM session. This reduces test-media space
   and exercises per-input cleanup; it does not prove every possible byte stream.
3. **Capacity/extent reconstruction:** load 8,192 zero bytes, generate source
   spanning multiple CP/M extents, and reconstruct exactly 8,192 bytes with the
   native toolchain. The input file is disassembled, never executed.
4. **Independent full-core command tests:** 43 DASM campaigns and 25 DSYM cases,
   including hostile BDOS register clobbering, file-operation fault injection,
   existing-file/backup preservation, cancellation and restart safety, binary
   limits, TPA cutoffs, resident canaries and rejected metadata retention.
   The shared USQ test helper change also passes 71 USQ command regressions.

The Model 4 functional campaigns use a test-only function-10 line-input
wrapper. It lowers the active TPA ceiling to its interceptor, calls the
unchanged original DASM entry, chains every file request to real BetterCP/M,
then restores the original BDOS vector on return. The disassembler core differs
only in its entry jump. Native/cross parity is checked on the standalone core,
not the wrapper. Keyboard, backspace, pagination and the terminal cancellation
matrix are separate outstanding acceptance work.

Early diagnostic runs against older System snapshots and superseded binaries
are not acceptance evidence for the current pair. Failed keystroke-driven
runs likewise carry no PASS verdict.

## Reproduction

Use new output directories and explicit current System and Utilities roots:

```text
python3 tools/qualify_dasm.py --system SYSTEM_ROOT --utilities UTILITIES_ROOT --output INTEGRATION
python3 tools/qualify_dasm_corpus.py --system SYSTEM_ROOT --utilities UTILITIES_ROOT --output CORPUS
python3 tools/qualify_dasm_corpus.py --system SYSTEM_ROOT --utilities UTILITIES_ROOT --output CAPACITY --capacity-only
```

`--scripted-input` additionally selects the single-session input wrapper on
z80pack, permitting the same reload workload as Model 4. Serial interactive
z80pack reconstruction is also checked separately. Full-core tests and build
recipes are listed in the implementation-status document.

## Results and retained evidence

| Gate | z80pack | Model 4 |
| --- | --- | --- |
| Native DASM/DSYM build and standalone byte parity | PASS | PASS |
| Symbol conversion and five-byte reconstruction | PASS | PASS |
| Eight opcode/data corpora, including one-session reload | PASS | PASS |
| 8 KiB input / 49,280-byte source / multi-extent reconstruction | PASS | PASS |
| Original paired media unchanged and work filesystem checks | PASS | PASS |

The [machine-readable receipt](DASM-Development-Qualification.json) records
exact candidate/media/tool/output hashes. The [evidence archive](DASM-Development-Evidence.tar.gz)
retains 368 files: prepared native sources, generated assembly, REL/COM output,
symbol conversion, console diagnostics, link maps, host test logs, source/tool
snapshots and the paired System reports. The archive has an internal SHA-256
manifest; its external hash and length are bound by the receipt. Native LINK
record padding is checked separately from every declared logical byte.

### LINK report ambiguity discovered by negative probes

Native ZSM4 accepts two distinct 12-character PUBLIC source names, but LINK
reduces `LONGSYMBOLAA` and `LONGSYMBOLBB` to `LONGSY` and reports a multiple
definition. It nevertheless writes a syntactically valid `.SYM` file. An
unresolved `MISSING` likewise produces `0000 MISSIN` in `.SYM`, alongside valid
symbols. Zero is also a legal resolved absolute value, so these failures cannot
be identified from symbol-file syntax or addresses alone. The probe inputs,
console output and resulting files are retained in the archive.

This baseline DSYM only validates the symbol-file grammar. A successful DSYM
conversion **does not certify a successful LINK**. A verified native LINK
log/receipt workflow is required before the specification's failed-build
rejection requirement can be accepted. Native integration above used a known
successful build and independently checked its LINK diagnostics and bytes.

The probes also establish that a same-value EQU definition followed by a code
label is accepted by the pinned ZSM4; this informs the remaining alias/interior
symbol source-generation work. Neither finding changes external tool versions.
