# Date/time conventions and BetterCP/M compatibility

Research date: 2026-09-07; architecture updated 2026-09-25. Status: historical
compatibility investigation with the native callable `TIME` ABI and runtime-
separated `P2DOS.RSX` frontend now adopted. The user wants broad compatibility where
feasible, with interchangeable clock-provider RSXs. Current time is read from
the provider and is not shared PDS state.

## Compatibility classification

BetterCP/M 1.0 requires the separate `P2DOS.RSX` Functions 200/201 clock
frontend. Two BDOS 104/105 profiles are bounded optional 1.0 candidates after
that required frontend is complete and measured. DateStamper, ZSDOS/ZDDOS,
filesystem timestamps, and broader CP/M Plus, DOS+, Z80DOS, or P2DOS emulation
remain later work.

Existing utilities are qualification evidence only for the exact interface they
exercise. A shared clock backend does not establish compatibility with discovery
probes, filesystem stamp layouts, direct disk access, or unrelated services of
the originating operating system.

## Separate the interfaces

There are three independent contracts: reading/setting the system clock,
representing date/time to an application, and storing timestamps with files.
Supporting a clock call does not imply support for that system's file stamping,
identity probes, directory layouts, or full operating-system API.

## Historical families

### CP/M Plus (CP/M 3)

DRI documents BDOS 104 (set) and 105 (get). DE addresses a four-byte record:
little-endian 16-bit day count, BCD hour, BCD minute. Day 1 is 1978-01-01.
Get returns BCD seconds in A; set resets seconds to zero. Do not write an extra
seconds byte past a caller's four-byte buffer. This provides a clear public
compatibility contract, independent of our provider API.

Source: [DRI Programmer's Guide, functions 104/105](https://rvbelzen.tripod.com/cpm3-prg/cpm3pg3b.htm).

### P2DOS

A contemporary published source-listing excerpt documents 200=get and 201=set,
using a five-byte day-count/hour/minute/second record (time fields BCD), with
clock service supplied through P2BIOS. This is not the same buffer contract as
CP/M Plus, despite their related representations.

Source: [Micro Cornucopia 29, April–May 1986, P2DOS source excerpt](https://bitsavers.trailing-edge.com/magazines/Micro_Cornucopia/Micro_Cornucopia_29_Apr86.pdf).

### ZSDOS/ZDDOS and DateStamper calendar representation

The ZSDOS designers describe clock calls 98=get and 99=set using six BCD bytes:
year, month, day, hour, minute, second. Their stated two-digit-year window is
1978–2077. File-stamp calls 102/103 use three five-byte calendar fields, omitting
seconds, with conversions performed by the stamping module. ZDDOS embeds
DateStamper support; ZSDOS permits external stamping implementations.

Source: [ZSDOS designers' article, The Computer Journal 37, pp. 40–41](https://www.jaysage.org/tcj/tcj_37_OCR.pdf).

The ZSDOS manual supplies a particularly relevant precedent for our provider
library: CLOCKS.DAT holds clock drivers, STAMPS.DAT stamping routines, and
TESTCLOK tests a selected driver. SETUPZST offers DateStamper, P2DOS and combined
stamping arrangements. It also documents clock/stamping installation in RSX
mode. These are historical modules, not binaries compatible with BetterCP/M's
BRSX loader. Their reported sizes cannot serve as our memory estimate.

Source: [ZSDOS 1.0 manual, sections 3.2–3.4 and appendix A](https://www.661.org/p112/files/zsdos.pdf).

### Native DateStamper discovery

Contemporary application code probes BDOS 12 with E='D', checks for CP/M 2.2
and H='D', and retains the returned DE clock pointer. Thus numbered clock calls
alone will not satisfy every DateStamper-aware application. The complete callable
clock-entry contract still needs original driver/source verification before
implementing this path. Do not advertise the signature prematurely.

Source: [The Computer Journal 36, p. 41, environment-probe example](https://www.jaysage.org/tcj/tcj_36_OCR.pdf).

### DOS+ 2.5 and Z80DOS 2.4 clock profiles

Original source corrects the earlier assumption that DOS+ and Z80DOS share one
104/105 record. DOS+ 2.5 deliberately follows the CP/M 3 clock-call convention:
Function 104 reads four bytes and resets seconds to zero; Function 105 writes
four bytes and returns BCD seconds in A. If its timer is disabled, GET returns
A=0FFh without changing the caller's buffer. DOS+ file timestamps remain a
different and CP/M-3-incompatible contract.

Z80DOS 2.4 instead reads or writes a five-byte day-count/hour/minute/second
record and documents A=00h for GET. Its Function-12 result remains CP/M 2.2 in
A and adds the Z80DOS identifier 38h in D. Both clock profiles use day 1 as
1978-01-01 and packed-BCD time fields.

Sources: [DOS+ 2.5 source](https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/bdos/dosplsor.ark),
[Z80DOS 2.4 source and documentation](https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/bdos/z80d24sr.lbr), and
[The Computer Journal 37, p. 40](https://www.jaysage.org/tcj/tcj_37_OCR.pdf).

The profiles cannot be selected safely from the 104/105 call itself. The call
has no buffer length, and applications do not identify their convention
consistently. A five-byte GET can overwrite a CP/M 3 or DOS+ caller's four-byte
buffer. A conforming implementation therefore uses separate mutually exclusive
frontends and never guesses from register contents or adjacent memory.

### Representative 104/105 callers

`DATE501.COM` calls 104/105 without detecting the operating system and assumes a
five-byte record. It is an exact qualification target for the Z80DOS profile.
Its date, hour, and minute also work through a four-byte frontend, but it ignores
seconds returned in A, so seconds are not correct under CP/M 3/DOS+ semantics.

`SCTIME.COM` accepts Function-12 versions at or above CP/M 2.2, calls Function
105 with five bytes of storage, and writes returned A over the fifth byte. It is
a useful four-byte-profile qualification target and requires no SCB or file
timestamp behavior for its purpose of setting SuperCalc's date. Under Z80DOS it
overwrites the fifth byte with the documented A=00h, which is immaterial to that
date-only purpose.

DOS+ `TIME.COM` is an intentional boundary case. It requires either a DOS+
version result or DOS+ Function 210 identification. BetterCP/M shall not add
that identity behavior merely to run the utility.

Sources: [DATE501 source](https://ftpmirror.infania.net/sites/www.seasip.info/Cpm/2000/date501.mac)
and [CP/M Year 2000 utility notes](https://ftpmirror.infania.net/sites/www.seasip.info/Cpm/2000/fixes.html).

## Disk formats and host interoperability

cpmtools' own filesystem documentation describes CP/M Plus/P2DOS timestamps in
every fourth directory entry. Each file has two four-byte timestamps; CP/M Plus
can select access rather than creation for the first field. This uses 25% of
directory entries, not 25% of total disk capacity.

DateStamper instead uses !!!TIME&.DAT in the first directory slot and initial
allocation blocks. Its 16-byte record per directory entry contains create,
access and modify fields plus identification/checksum information. Calendar
fields have two-digit BCD years. cpmtools documents a year interpretation pivot
that differs from the ZSDOS article's window; compatibility must explicitly handle
that distinction, not rely on an implicit century guess.

Source: [cpmtools cpm(5) source](https://sources.debian.org/src/cpmtools/2.23-4/cpm.5.in).

## Feasibility and current conflicts

Broad support is feasible in principle with one provider supplying time and
small application-ABI adapters. It does not require a separate physical clock
driver for each historical API. File-stamp support is a larger, separate task:
correct metadata placement, create/access/modify semantics, error handling,
copying and directory maintenance all require validation.

Concrete collision: BetterCP/M currently assigns BDOS 200 to CPX control
(src/system/extens.mac, EX_ENTRY); P2DOS assigns 200 to get-time. Blindly
installing both is ambiguous. Architecture Specification 25 resolves the
namespace decision by assigning BetterCP/M private services to 176-199 and
restoring 200/201 to their inherited P2DOS get/set meanings. Stage 6 migrates
private services, rebuilds their clients, and supplies the separate `P2DOS.RSX`
frontend for 200/201. Do not infer the caller's intent from accidental pointer
or register values. This study does not itself implement that migration or
frontend.

The ordinary unified BDOS returns its unsupported result for functions 41–199;
98/99 and 104/105 compatibility therefore also require routing through the
appropriate extension path, not just adding conversions to TIME.COM.

The adopted 1.0 native service is the callable `TIME` ABI. It uses the compact
five-byte day-count, hour, minute and second record historically associated
with P2DOS, but does not adopt the P2DOS selectors as its native entry.
Hardware-backed providers are STATELESS and allocate no PDS block. The
authoritative clock is sampled on demand; no stale or continuously advancing
PDS copy is maintained. Device reads must provide a coherent snapshot across
rollover.

P2DOS compatibility is the separate `P2DOS.RSX` frontend, which owns Functions
200/201 and calls the native service. This lets one hardware provider serve
native clients and multiple later compatibility APIs without duplicating device
code.

After `P2DOS.RSX` is complete and measured, two mutually exclusive 104/105
frontends may reuse that pattern. Each resolves TIME for every request, invokes
the returned address immediately, retains no provider pointer, and translates
through private five-byte scratch. The four-byte frontend never writes the
caller's fifth byte; its SET supplies zero seconds. The five-byte frontend copies
the complete record and returns A=00h on GET. Neither changes Function 12.

Current estimates are 120-220 resident bytes and a 650-800-byte packaged RSX
per profile, with no PDS allocation and only one profile loaded at a time. These
are estimates until implementation. Admission to 1.0 requires actual measurement
after `P2DOS.RSX` and must not threaten the schedule or 53 KiB TPA floor.

Missing-provider GET leaves the caller's buffer unchanged. The four-byte profile
may return A=0FFh, matching documented DOS+ disabled-timer behavior, but this is
a BetterCP/M frontend rule rather than a CP/M 3 claim. Historical SET supplies no
portable failure result, so a failed SET remains externally a no-op; the native
TIME statuses remain internal to the adapter.

The exact provider request, errors, platform findings and qualification contract
are normative in `docs/architecture/22 Clock Provider ABI.txt`.

## Work required before promising compatibility

- Obtain the original DateStamper clock-entry definition. The Z80DOS 2.4 and
  DOS+ 2.5 104/105 definitions are now verified from original source.
- Inventory discovery/version probes used by actual legacy time utilities; do
  not impersonate an entire OS just to make its clock calls discoverable.
- Complete the adopted Stage-6 private-service migration away from BDOS 200/201,
  migrate the registry gateway to Function 182, and implement `P2DOS.RSX`
  against the native `TIME` service.
- Implement and measure optional adapters against the TPA budget only after
  `P2DOS.RSX` establishes their common pattern.
- Test four-byte and five-byte GET/SET separately, including guard bytes after
  the four-byte caller buffer, BCD validity, midnight, leap dates, set/read
  consistency, missing and read-only providers, unload, WBOOT, and provider
  relocation between calls. Qualify SCTIME against the four-byte profile and
  DATE501 against the five-byte profile, and prevent simultaneous ambiguous
  configuration of both frontends.
- Qualify each file-stamp scheme separately using prepared disposable media,
  legacy readers/writers and cpmtools round trips. Clock API compatibility alone
  must never be reported as complete filesystem timestamp compatibility.

Only P2DOS clock-call compatibility is a required 1.0 frontend. The two 104/105
profiles are bounded optional candidates and all other historical families are
later work. No optional adapter is a release-qualification gap unless it is
explicitly admitted to the distribution; if admitted, qualify and document only
the exact utilities and interface profile actually demonstrated.
