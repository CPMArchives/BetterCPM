# Date/time conventions and BetterCP/M compatibility

Research date: 2026-09-07. Status: design investigation; no new API numbers or
on-disk format have been adopted. The user wants broad compatibility where
feasible, with interchangeable clock-provider RSXs and shared time state in
persistent DATA.

## Confirmed compatibility targets

The user has approved DateStamper, ZSDOS/ZDDOS, P2DOS, CP/M Plus, and DOS+/Z80DOS
as the baseline. Existing utilities must run unmodified. Prioritize DateStamper
and ZSDOS/ZDDOS; relative historical popularity has not been quantified in this
study. The other three remain baseline targets, not merely optional future work.
Acceptance includes applicable discovery, clock and file-stamp contracts. Record
version differences, direct disk-access assumptions and unresolved conflicts per
utility rather than claiming universal compatibility from a shared clock backend.

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

### DOS+ 2.5 / Z80DOS variants

The contemporary ZSDOS article identifies DOS+ 2.5 as a separate directory-stamp
layout: creation date only, with modification and access dates/times. It shares
the one-stamp-entry-per-three-file-entries arrangement with P2DOS, but the fields
are not interchangeable. Exact Z80DOS/DOS+ clock-buffer and return conventions
remain to be checked against original sources; do not assume identical semantics
merely because reference summaries associate them with calls 104/105.

Source: [The Computer Journal 37, p. 40](https://www.jaysage.org/tcj/tcj_37_OCR.pdf).

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
(src/system/extensions.mac, EX_ENTRY); P2DOS assigns 200 to get-time. Blindly
installing both is ambiguous. Review our private extension namespace before
core freeze. Options are relocating/multiplexing BetterCP/M's private services
with rebuilt clients, or an explicit P2DOS compatibility mode. Do not infer the
caller's intent from accidental pointer or register values. No migration is
approved or implemented by this study.

The ordinary unified BDOS returns its unsupported result for functions 41–199;
98/99 and 104/105 compatibility therefore also require routing through the
appropriate extension path, not just adding conversions to TIME.COM.

Recommend one canonical RAM time record with explicit validity and a full year
(or unambiguous day count), accessed through stable gateways. Convert at the
legacy API boundary, rejecting unrepresentable dates according to a specified
policy. Preserve the current time, a retained stale sample, and availability as
distinct states. Device reads must provide a coherent snapshot across rollover.
Do not expose pointers into an unloadable provider; a legacy pointer interface
needs a stable entry that remains safe after unload.

## Work required before promising compatibility

- Obtain original DateStamper clock-entry and Z80DOS/DOS+ interface definitions.
- Inventory discovery/version probes used by actual legacy time utilities; do
  not impersonate an entire OS just to make its clock calls discoverable.
- Resolve BDOS 200 and publish exact register, buffer, error and date-range rules.
- Implement and measure optional adapters against the TPA budget.
- Test buffer bounds (especially four versus five bytes), BCD validity, midnight,
  leap dates, century windows, set/read consistency, missing clocks and unload.
- Qualify each file-stamp scheme separately using prepared disposable media,
  legacy readers/writers and cpmtools round trips. Clock API compatibility alone
  must never be reported as complete filesystem timestamp compatibility.

The five agreed families establish the compatibility scope. Their implementation
need not impose every adapter or hardware provider's memory cost on every user.
Measure the selected modules and state explicitly which combinations are required
for each legacy utility. Unresolved contracts remain release-qualification gaps.
