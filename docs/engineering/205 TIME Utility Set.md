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

## FreHD lifecycle qualification

`test_frehd_clock_lifecycle.py` separates recovery and warm-boot cases into
bounded runs. The recovery case removes FREHDCLK while P2DOS remains resident,
checks claimed failure and failed-GET buffer atomicity, confirms the remaining
profile, reloads FREHDCLK, and verifies recovery and provider identification.
The shared native probe checks A/HL results and DE/SP/IX/IY preservation on
both supported platforms. No OS or provider change is required.

The original combined run reached its 180-second limit after eleven stages;
its verified warm-boot and failure-stage captures are retained separately.
The shorter eight-stage recovery run passes completely. Its report retains
the warm-stage captures and original invocation alongside the new media,
probe, per-command captures and hashes. A full combined-run pass is not claimed.
Use `--case warm` with a new report directory for an independent warm rerun.

Each native probe result must appear immediately before the prompt because
return redraws its command line. Other checks use the complete `A0>command`
marker so a word inside a diagnostic cannot be mistaken for the command echo.
Coherent sampling, rollover and other remaining Item 6 checks are still pending.

## P2DOS frontend qualification closure

The focused `test_p2dos_rsx.py` now injects every assigned native failure status
(1, 2, 3, 4, 5, 6 and 8) after a controlled provider writes one, three or all five
bytes of private output. All 21 cases return FEh/00FEh, preserve the caller's
five-byte GET buffer and both guard bytes, and retain DE/SP/IX. Each case also
confirms that the provider actually wrote the private output and received GET.
A subsequent call resolves another provider and publishes its complete sample.

Together with prior success, lookup failure, SET and per-call discovery tests,
and actual two-platform lifecycle/register qualification, this closes the
required P2DOS.RSX frontend checks. P2DOS remains 140 code bytes in a 256-byte
allocation. No frontend or resident OS implementation change is required.
Native provider coherence/rollover checks and other Item 6 work remain pending;
frontend completion does not claim those provider tests have passed.

## Provider sampling and rollover closure

`test_clock_sampling.py` executes the actual assembled provider routines against
controlled RTC ports. All 26 recorded checks pass. ZPRTC tests binary and BCD
mode, seconds crossing midnight and minute boundaries, month/year transitions,
leap-day and non-leap February boundaries, acceptance on the fourth attempt,
and failure after exactly four incoherent attempts. Rejected samples leave the
caller buffer unchanged; the provider never toggles the shared clock mode.

FreHD tests both sides of those calendar boundaries using the documented
command-1 latched six-byte response. The fixture changes its live clock during
transfer while preserving the response snapshot; the provider publishes the
correct day count and packed-BCD fields and restores the normal map/I/O latch.
This verifies provider behavior under the established FreHD snapshot contract,
not the internal implementation of physical clock firmware.

The focused CPU runner adds controlled IN/OUT, INIR, BIT 7,A and INC H support.
Its BIOS listing reader tolerates non-UTF-8 source-header bytes, as other
listing readers already do. The complete BIOS-vector regression and existing
TIME/P2DOS focused checks pass. No OS or provider source change is needed.
Sampling/rollover qualification is complete; final attribute qualification
and the optional 104/105 admission decision remain in Item 6.
