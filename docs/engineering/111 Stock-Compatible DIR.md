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
entry. A search with no visible match reports `NO FILE`.

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
The trs80gp boot test now requires exact four-column output. Focused physical
runs verify `DIR *.COM` selection and `DIR B:` against the independent drive-B
fixture while returning to `A0>`.
