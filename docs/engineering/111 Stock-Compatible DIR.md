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
