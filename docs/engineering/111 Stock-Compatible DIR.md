# Engineering Specification 111: Stock-Compatible DIR

## Milestone

The default `DIR` supplied by `BASIC.CPX` now reproduces the CP/M 2.2 CCP's
ordinary directory selection and four-column presentation instead of the
proof implementation's one-name-per-line diagnostic output.

## Baseline contract

The supported baseline forms are:

```text
DIR
DIR B:
DIR *.COM
```

`DIR` searches the current drive and user. A drive or BetterCP/M DU qualifier
temporarily selects another directory without changing the caller's active DU.
An 8.3 pattern accepts CP/M `*` and `?` wildcards.

Only files with Directory status are shown. The high bit of the second
file-type byte is the CP/M System attribute and suppresses that directory
entry. As in the original CP/M 2.2 CCP, `NO FILE` means that BDOS found no
matching directory entry at all. If the pattern matches only SYS entries,
those entries remain invisible and no `NO FILE` message is printed.

## Presentation

Entries retain their space-padded 8.3 fields and are emitted four per
80-column row:

```text
A: HELLO    COM : CPX      COM : RSX      COM : RSXTEST  COM
A: BASIC    CPX : HELLO    CPX : HELLO    RSX
```

The drive prefix appears at the start of every row; subsequent entries use the
stock ` : ` separator. Directory order is the order returned by BDOS Search
First/Search Next and is not alphabetically rewritten.

## Extent handling

DIR shall print a file once even when it occupies multiple directory extents.
The implementation obtains the active DPB through Function 31, reads EXM, and
prints only the entry belonging to the first physical extent group. It does
not assume that EXM is zero merely because the current development format has
that value.

## Extensions

The existing BetterCP/M forms remain additive:

```text
DIR 5:
DIR B5:
DIR B5:*.COM
```

Named DU syntax will use the future common resolver and is not privately
implemented by BASIC.CPX.

## Verification

Native ZSM4 and cross assembly produce byte-identical `BASIC.CPX` payloads.
The trs80gp boot test requires exact four-column output. The focused physical
suite constructs three DMK files and verifies exact selection, an empty search,
stock SYS-only suppression, one display for a 20K multi-extent file, temporary
drive qualification, and combined `C3:` selection while returning to `A0>`.

The ordinary no-argument form exercises the all-wildcard path on every boot.
Explicit `*` and `?` parsing is also part of the implementation; automated
injection of shifted Model 4 punctuation remains unsuitable as reference
evidence because trs80gp may observe the underlying unshifted key as well.


## Bounded wildcard grammar — 2026-10-09

RCP DIR and the shared DIR.COM body now validate the operand with COPY's
bounded 8.3 lexer before expanding it into an FCB. A question mark consumes
one position; a terminal star run fills the remaining field. Adjacent terminal
stars collapse, while literals or question marks after a star run are rejected.
Malformed input reports `Invalid filespec.` and restores the caller DU.

Qualification exposed an existing transient-builder defect: entry lookup
matched a CALL instruction when the actual label had a trailing comment.
For DIR, that target was inside the overwritten startup header. The builder
now requires a colon-bearing label and permits its trailing comment. All
transient wrappers consequently target their actual routine entries; this
also removes their dependency on dispatch-side CALL/SCF/RET sequences.

The shared body grows from 3,743 to 3,795 bytes (+52); its rounded CPX allocation
remains 3,840 bytes. DIR.COM is 3,795 bytes. BDOS, BIOS and CCP are unchanged.
Native ZSM4/LINK and host builds match for all six generated transients.

`tools/test_dir_filespec.py` checks entry labels and rejects malformed operands
before FCB expansion or a BDOS search. `tools/test_z80pack_dir_filespec.py`
qualifies 28 cases across CPX-only and transient profiles: accepted wildcard
forms, rejected suffixes and overlong fields, temporary B1 selection with A0
restoration, SYS suppression, and one listing for a 20K EXM=1 file. All mounted
disk images remain byte-identical. COPY lexer and positional mapping tests
also pass after the shared change.

Evidence: `/private/tmp/dir-bounded-wildcards-fixed-20261009/evidence.json`
and `build/utilities/NATIVE-RCP-TRANSIENT-BUILD.LOG`. The user-guide source
records the grammar; exported DOCX/PDF files were not regenerated.
