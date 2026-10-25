# TED Reference Baseline

Status: upstream and WordStar comparison artifacts pinned. The user-agreed
interface is TED behavior with selected WordStar command sequences, not full
WordStar emulation. Qualification is a separate record.

## TED upstream

- Author: Hector Peraza; [upstream repository](https://github.com/hperaza/TED).
- Commit: `7da2e1e39ae4cb57b45d84cf715b88fabbeadd17` (2024-04-07).
- License: GPL version 2 or later, retained verbatim in `third_party/ted/LICENSE`
  and `src/utilities/ted/COPYING`; source copyright notices are retained.
- Complete immutable snapshot: `third_party/ted/`. No upstream file was edited.
- Original git archive: `third_party/ted/upstream.tar`, SHA-256
  `2f6b6b5a840a573d1999083b66b5da1ada26cecc2fdc323fa81f5240fdda8562`.
- `third_party/ted/provenance.json` records every archived file and its SHA-256.
  `tools/build_ted.py` verifies archive membership, archive bytes and every
  extracted reference file before preparing assembly source.
- Maintained CP/M modules are in `src/utilities/ted/`; RSX180 code and the
  upstream `syslib.lib` are retained only in the immutable reference snapshot
  and are not linked into the CP/M development executable.

## WordStar comparison evidence and authority

The 1983 MicroPro WordStar 3.3 Reference Manual was obtained through the
[Bitsavers mirror](http://ftpmirror.your.org/pub/misc/bitsavers/pdf/microPro/Wordstar_3.3/Wordstar_3.3_Reference_Manual_1983.pdf)
after primary-host access failed. SHA-256:
`3e19f78bad332884d84c3463c5c5ddaedb27cfacc5258ee2b8a981a1adcfe649`;
7,321,205 bytes. PDF pages 81–82 define the word separators; the scanned
punctuation was visually checked because OCR omitted some marks.

The independently sourced [Kaypro CP/M WordStar 3.30 archive](http://www.retroarchive.org/cpm/text/Wskpro33.zip)
has SHA-256 `b98ffd19ca75bf6e358f01a78313d744440a48cdb829858b096badb748850cd4`.
WS.COM is 17,920 bytes, SHA-256
`1e14315ccec62f0ef74d797c86e99c2213e14d45782cc396108bf22bf105fc9a`.
It identifies Release 3.30, Kaypro 4u. No installation patch was applied.
Non-document mode was selected explicitly with N on disposable cpmsim media.
Seven saved-byte observations using our own input text establish punctuation,
hyphen and underscore word behavior. Provenance, overlay hashes and derived
fixtures are in `metadata/ted-wordstar33-fixtures.json`.

Proprietary binaries, overlays, manual copies and screenshots remain outside
the repository and distributable source companion. The derived fixtures are
limited evidence, not a complete WordStar command compatibility claim.

The later user review supersedes the original WordStar-emulation proposal:
TED source/docs govern existing operations, while the specification defines
three bounded word-operation additions. There is no ^Q prefix or repeat-find.
The WordStar fixtures contain their original oracle setup keys; those are not
TED bindings. Qualification tests exercise the agreed TED bindings separately.

## Toolchain boundary

The host cross assembler is Udo Munk's `z80asm` 2.1. Native checks invoke the
existing external ZSM4 4.7 and DRI LINK 1.3 from the Utilities disk on disposable
media. Neither assembler nor linker is incorporated into BetterCP/M-owned
version/revision numbering. The module flattener emits maintained instructions,
not assembled instruction-byte tables; the native and cross outputs must agree
before any runtime smoke-test result is accepted.
