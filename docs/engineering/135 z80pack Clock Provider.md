# Engineering Specification 135: z80pack Clock Provider

## Scope

`ZPRTC.RSX` implements BetterCP/M `TIME` ABI 1.0 using the clock interface in
z80pack/cpmsim. It is a read-only, hardware-backed, stateless provider. The
portable `TIME.COM` utility is shared unchanged with other providers.

## Hardware interface

Port 25 is the command and mode port. Reading it returns zero when clock fields
use packed BCD and one when they use binary. Writing commands 0 through 4
selects seconds, minutes, hours, and the low and high bytes of the CP/M day
count. The selected value is read from port 26. Command 255 toggles the mode;
the provider never issues it and therefore never changes shared emulator state.

The day count is binary in either mode and uses the CP/M epoch. Binary clock
fields are converted locally to the five-byte native `TIME` representation.

## Coherent sampling

The interface samples each field independently. The provider reads seconds,
then the day and remaining time fields, then seconds again. A changed seconds
value discards the sample and retries, up to four attempts. Thus a minute or
midnight transition cannot produce a mixed timestamp and hardware failure
cannot cause an unbounded wait.

## Registry publication

The BRSX-v2 carrier advertises `TIME` 1.0 through the central Function 208
resolver. It contains 271 bytes of code in a 512-byte provider allocation and
does not intercept the registry function itself.

## Use

The z80pack system disk contains `ZPRTC.RSX` and `TIME.COM`:

```text
RSX LOAD ZPRTC
TIME
TIME /PROVIDER
```

The provider supports dates through 2099. z80pack's intentional historical
leap-year calculation is not Gregorian-correct for 2100.
