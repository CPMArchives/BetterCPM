# Engineering Specification 94: CCP Wildcards and Stack Placement

## Decision

The CCP expands `*` in either default-FCB name or type field into `?` through
the end of that field. Existing `?` characters remain literal CP/M wildcard
bytes. Drive-qualified patterns such as `B:*.COM` combine this behavior with
the A: through P: drive encoding.

## Resident memory adjustment

Drive-prefix support exhausted the original CCP region at `ECFFh`. The BIOS's
private 512-byte physical-sector buffer remains at `ED00h..EEFFh`: `F400h` is
the Model 4 memory-mapped keyboard window and cannot be used as RAM. Instead,
the CCP's private 16-byte stack has moved to `D5F0h..D5FFh`, the reserved top
of the BDOS growth region immediately below Directory Services. This recovers
the bytes needed by wildcard parsing without changing the TPA or any public
entry point.

The remaining nine bytes come from the former guard after Directory Services:
that component ends at `E8D5h`, so the CCP now begins immediately afterward at
`E8D6h` rather than `E8E0h`. The composed build checks this exact boundary.

The historical `ED00h` placement remains documented because it caught earlier
component collisions and explains why wildcard completion required an explicit
map decision rather than an unchecked overflow.

## Verification

Focused parser cases cover `B:*.COM`, partial-field `AB*.D*`, preserved `?`,
bare drives, ordinary filenames, and the `P:` boundary. The Model 4 scanner
also translates Shift-minus and Shift-slash into `*` and `?`. Native CP/M and
cross builds must remain byte-identical before the resident image is booted and
exercised under `trs80gp`.

The exact independent compatibility command now passes physically:

```text
ENTRYTST /0014 A:AB*.C?M
0014  P  R  Use /0014 A:AB*.C?M
Summary: 1 pass, 0 fail, 0 error, 0 observations
```

This run also corrected an ENTRYTST harness contradiction: its documentation
required a second operand while its generic selector parser rejected every
second token. The parser now consumes only the selector and leaves later tokens
available to the operand-sensitive entry-state oracle.
