# Engineering Specification 115: Stock-Compatible SAVE

Date: 2026-09-03

## Contract

`SAVE n filename` copies `n` decimal 256-byte pages beginning at 0100H to an
ordinary CP/M file. The accepted range is 0 through 255. The filename must be
an exact, unambiguous 8.3 name; BetterCP/M additionally accepts a DU-qualified
target. An existing destination is deleted and replaced, matching the original
CCP's destructive overwrite order. Allocation or close failure reports
`NO SPACE`, and zero pages creates a valid empty file.

## Why SAVE has no transient fallback

SAVE belongs in `BASIC.CPX`. Loading a hypothetical `SAVE.COM` at 0100H would
overwrite the beginning of the TPA image before it could be saved, so such a
program could not preserve the resident command's semantics. The CPX command
is reconstructed with the command environment after transient execution and
can inspect the otherwise untouched TPA when the prompt returns.

## Verification

`tools/test_save_compatibility.py` uses disposable writable DMKs to verify
page length, zero-page creation, destination replacement, drive-qualified
output, invalid counts and filenames, and full-directory `NO SPACE` reporting.

The present MM 790K DPB advertises DSM 394 although only blocks 0 through 389
fit after the reserved tracks in the generated image. Allocation-exhaustion
testing must not use those five phantom blocks as evidence; that pre-existing
geometry discrepancy requires its own correction and regression test.
