# Engineering Specification 114: Stock-Compatible TYPE

Date: 2026-09-03

## Compatibility baseline

BetterCP/M supplies TYPE through the default `BASIC.CPX` and as an ordinary
`TYPE.COM` fallback. Both forms implement the CP/M 2.2 behavior:

```text
TYPE filename.typ
```

TYPE requires one exact, unambiguous filename. Wildcards, missing operands,
unmatched files, unknown options, and trailing operands report a command
error (`?`). A drive-qualified operand reads that drive without changing the
caller's current drive/user.

After a successful open, TYPE starts on a fresh line and sends every byte to
the cooked console output service. Dollar signs and other printable bytes are
therefore literal data rather than BDOS string delimiters. Display stops at
the first CP/M text EOF byte (`1Ah`) or at sequential end-of-file. An abnormal
sequential-read result reports `READ ERROR`.

The shared cooked-console path supplies the documented interactive controls:

- `Ctrl-S` freezes scrolling until the next key;
- the resume key is consumed;
- `Ctrl-P` continues to control printer echo; and
- `Ctrl-C` aborts through the normal warm-boot path.

## BetterCP/M paging extension

The optional form is:

```text
TYPE filename.typ /P
```

`/P` pauses after 23 completed output lines and displays `--More--`. Space
erases the marker and continues. Other ordinary keys are ignored; `Ctrl-C`
still aborts. The counter is based on line-feed bytes, so TYPE does not alter
or reinterpret the file's literal line endings.

Ordinary TYPE does not page and produces no extension-specific output.

## Transient fallback and builds

The normal BetterCP/M disk includes `TYPE.COM`. If `BASIC.CPX` is unloaded,
the same command therefore resolves to the transient implementation.

`tools/build_type.py` creates the cross build. `tools/build_native_type.py`
assembles and links the same source using ZSM4 and LINK under native CP/M and
requires the two executables to be byte-identical.

## Verification

`tools/test_type_compatibility.py` uses disposable physical DMKs under
`trs80gp` and verifies:

- literal text, including a dollar sign;
- termination at `1Ah` without displaying following bytes;
- drive qualification and current-DU preservation;
- missing-file and wildcard rejection;
- a first-page `/P` stop and Space continuation through the final line; and
- transient TYPE.COM after unloading `BASIC.CPX`.

The existing cooked-console suite independently verifies Ctrl-S resume,
Ctrl-C warm boot, printer echo, and preservation of ordinary type-ahead.
