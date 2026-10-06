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

## z80pack provider qualification

`test_z80pack_time.py` runs the built utility under cpmsim with the actual
ZPRTC provider. It verifies missing-service reporting before loading ZPRTC,
provider name and read-only capability display, GET before and after rejected
SET, malformed-input usage, and return to a working CCP. The two GET samples
remain monotonic and within 30 seconds, showing the rejected request did not
replace the current clock with the requested 1978 date.

TIME.COM uses the current Function-177 version-2 enumeration request for the
provider name. Its obsolete version-1 request caused a blank provider name;
correcting the utility request restores identification without an OS change.

The harness retains its private media, transcript, utility and simulator hashes,
commands and sampled times. A report directory is never overwritten implicitly.
This increment qualifies the z80pack client path; FreHD and provider lifecycle
qualification remain separate Item 6 work.

## FreHD provider qualification

`test_frehd_time.py` installs the current TIME.COM in private Model 4 media and
uses the established LaunchServices adapter. It verifies FreHD GET, provider
identification and read-only capability reporting, SET_UNSUPPORTED rather than
success, and return to a working CCP. It retains media, command arguments,
screen captures and input hashes without overwriting prior reports.

A capture immediately after provider loading isolated an input-timing failure:
the earlier three-second delay typed TIME before that transition was ready.
The measured eight-second delay allows the command to run. This harness
correction requires no provider or OS implementation change. Each launch has
a 90-second timeout. Provider lifecycle and rollover qualification remain
separate Item 6 work.

## z80pack lifecycle qualification

`test_z80pack_clock_lifecycle.py` exercises the actual resident chain with a
native probe. It checks Functions 200/201 when P2DOS is absent, when its provider
is present, and when P2DOS remains resident after the provider is removed.
Expected results are FFh/00FFh for absent frontend, 00h/0000h for successful
GET, and FEh/00FEh for claimed failures including unsupported SET. The probe
checks DE, SP, IX and IY preservation and failed-GET buffer atomicity.

Explicit WARM preserves working native and P2DOS clock calls. Removing ZPRTC
leaves P2DOS listed and causes graceful service-unavailable behavior. Loading
ECHO and then a new ZPRTC instance changes the chain layout; the still-resident
P2DOS recovers without reload. Removing P2DOS leaves native TIME available.
Subsequent provider and frontend reloads also succeed.

The harness retains media, probe source/listing, commands, transcript and hashes.
This qualifies replacement by a new instance of the same provider, not a switch
between different provider implementations. FreHD lifecycle, coherent sampling,
rollover boundaries and the remaining P2DOS matrix are still separate checks.
No dependency manager or implementation change is required by these results.
