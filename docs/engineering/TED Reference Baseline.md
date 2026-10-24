# TED Reference Baseline

Status: upstream source pinned; WordStar oracle baseline incomplete. This is a
development record, not a compatibility acceptance.

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

## WordStar comparison authority

The adopted reference remains MicroPro WordStar 3.3 for CP/M, non-document mode,
and the [1983 WordStar 3.3 Reference Manual](https://www.bitsavers.org/pdf/microPro/Wordstar_3.3/Wordstar_3.3_Reference_Manual_1983.pdf).
The manual's bibliographic identity was located independently at Bitsavers.
The primary download returned HTTP 403 on both www and bare-host attempts;
there is no claimed local hash or completed manual review from those attempts.

No independently sourced CP/M 3.3 binary has yet been pinned or executed for
this adaptation. The adjacent CP/M compatibility investigation's WordStar
artifact is **3.00**, so it cannot silently substitute for the adopted 3.3
oracle. No proprietary WordStar binary, manual copy or screen image is included
in this repository. Do not label existing TED bindings WordStar-compatible on
the strength of upstream's “WordStar-like” description.

Required next evidence: exact binary/container hashes, acquisition provenance,
installation/terminal patch settings, manual artifact hash/edition, command
fixtures covering the entire specification matrix, and explicit dispositions
for every safety/preservation override. Until then T02 remains NOT RUN.

## Toolchain boundary

The host cross assembler is Udo Munk's `z80asm` 2.1. Native checks invoke the
existing external ZSM4 4.7 and DRI LINK 1.3 from the Utilities disk on disposable
media. Neither assembler nor linker is incorporated into BetterCP/M-owned
version/revision numbering. The module flattener emits maintained instructions,
not assembled instruction-byte tables; the native and cross outputs must agree
before any runtime smoke-test result is accepted.
