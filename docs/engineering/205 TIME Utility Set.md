# Engineering Specification 205: TIME Utility SET

TIME.COM accepts the native TIME ABI 1.0 canonical record for SET without
requiring P2DOS.RSX. It remains a transient utility and adds no resident OS
memory or new public ABI.

## Command syntax

```
TIME
TIME /PROVIDER
TIME /SET LL HH HR MN SC
```

SET takes exactly five two-digit hexadecimal bytes separated by single spaces:
little-endian day-count low and high bytes, followed by packed-BCD hour,
minute and second. Keywords and hexadecimal letters are case-insensitive.
Leading spaces are accepted; extra arguments or trailing spaces are rejected.
For example, `TIME /SET 01 00 12 34 56` requests day 1 (1978-01-01) at 12:34:56.
Calendar-style SET input is not supplied by this increment.

The utility rejects malformed hexadecimal bytes, nondecimal BCD nibbles,
hours above 23, and minutes or seconds above 59 before service discovery.
The provider remains responsible for complete request validation, hardware
range validation, and ensuring a failed request does not modify the clock.

## Dispatch and results

The utility discovers TIME ABI 1.0 through Function 182 and sends a ten-byte
request: version 1, length 10, operation 1, zero flags, the five-byte record,
and zero reserved byte. It calls the provider even when SET capability is
absent, allowing the native SET_UNSUPPORTED contract to supply the result.

Success prints `Clock set.` Unsupported SET, invalid clock records, missing
service and other provider failures have separate diagnostics. Locally
malformed input prints usage. No successful SET is inferred from GET or from
capability flags. GET and provider-information operations remain available.

## Focused verification

`test_time_set.py` executes the assembled parser and dispatch code with
controlled registry and provider entries. It covers canonical record layout,
case handling, boundary values, malformed bytes and BCD, range rejection,
rejection before discovery, SET success and failure routing, missing service,
stack balance, and GET/provider parsing regressions.

`test_time_errors.py` verifies native status-to-message routing.
`test_time_artifacts.py` retains the existing utility/provider artifact checks.
These checks do not replace real FreHD/z80pack provider or full console
qualification; those remain in Item 6.
