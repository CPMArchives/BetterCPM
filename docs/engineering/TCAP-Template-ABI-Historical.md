> Historical, unreleased experiment. The active implementation and contract are [TCAP 2.0](TCAP-Direct-ABI.md).

# TCAP 1.x protocol-template experiment (historical)

The combined personality/renderer redesign uses the explicitly revised
[TCAP 2.0 direct-operation ABI](TCAP-Direct-ABI.md). This template-based candidate
is retained as the historical portable-stack contract, not advertised by those
2.0 modules. Utility migrations and release assignment remain deferred.

Status: public integration candidate, 8 November 2026. This deliberately replaces
an unreleased, oversized transaction proposal. It does not claim binary
compatibility with that proposal or private XTAB/XTCP experiments. The
[historical contract](TCAP-Transaction-ABI-Historical.md) records the retired
wire formats. Utility migrations, HELP delivery and release assignment remain
deferred. Qualification status is recorded separately for each platform.
The [integration results](TCAP-Public-Integration-Results.md) record passing
source, installation and installed-disk lifecycles on cpmsim, Model 4 and Model II.
Their memory limit applies to the added TCAP layer, not the entire existing
RSX/personality/backend console subsystem.

## Architecture and lifetime

A personality defines the application's terminal protocol. A backend renders it.
Users load a backend, load the desired personality, run its configured application,
unload the personality, and select another. TCAP adds a small description to that
same personality. Existing Monitor 0–5, MCON, SCRN 1.1, SCX 1.0, Function 182 and
ordinary console output retain their meanings. TCAP adds no system hook, reserved
memory, counter, resident engine, ownership token or automatic recovery facility.

The complete added capability layer must stay within **1,280 bytes**, counting
extra resident allocation, metadata/alignment and application helper code/data.
Call-site and stack allowances are disclosed. Complete unload must restore the
original exact TPA boundary and maximum loadable COM size. There is zero permanent
TCAP allocation. Application paging, editing and parsing remain application-owned.

## Discovery and admission

The exact service ID is `TCAP`, version 1.0, advertisement capabilities zero.
It is the second callable advertisement beside MCON on a STATEFUL personality.
No new metadata format is introduced. The ordinary BRSX/checking machinery admits
the carrier, validates executable entry bounds and metadata, rejects duplicate
service IDs, binds the sole SCRN backend, and publishes the resident layout.

Application admission is read-only and completes before display output:

1. Resolve SCRN 1.1, MCON 1.1-or-newer and TCAP 1.0 through Function 182.
2. Verify output eligibility and that TCAP and MCON have the same provider index
   in the current layout. Reject a standalone or foreign-owner TCAP service
   without invoking its query.
3. Query, copy and validate the bounded terminal description. Known versions,
   lengths, masks, offsets and terminating zeros are required. Required basic
   operation bits must agree with the presence of their templates.
4. For backend-stream geometry, query SCRN operation 16, validate the six-byte
   SCX 1.0 header, and copy its rows/columns. Zero remains unknown.
5. Let the application assess its required operation mask and geometry before
   using controls. Optional strong emphasis may fall back to plain text.

The loader does not execute or interpret a TCAP query during carrier admission.
The client performs the table and selected-owner checks. This is cooperative
CP/M correctness, not memory isolation or authentication of arbitrary code.

CRT is eligible on the qualified backends. TTY is additionally eligible on
cpmsim, whose SCRN platform value 0002h identifies its shared Monitor output path.
BAT, discard and unqualified TTY routes are unavailable. No terminal input probe
is issued. Reopen after changing routing or resident layout. Transients may keep
a copied description within their normal execution lifetime; no persistent raw
service pointer or session identity is assigned.

## Provider query

A=0 queries the description, returning A=0 and HL pointing to its immutable
record. BC, DE, IX, IY and entry SP are preserved. AF/HL are scratch. Interrupt
state is unchanged. Any other selector returns A=255 with no memory writes or
output. The query retains no caller pointer, consumes no input, and makes no
backend or BDOS call. Calls are ordinary synchronous, serialized CP/M calls.

## Terminal record

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 2 | ASCII `TC` |
| 2 | 1 | Record version, exactly 1 |
| 3 | 1 | Complete record length, 16–128 |
| 4 | 1 | Rows; zero means unknown |
| 5 | 1 | Columns; zero means unknown |
| 6 | 1 | Operations: clear=1, position=2, erase line=4, strong=8 |
| 7 | 1 | Strong mapping: plain=0, bold=1, reverse=2 |
| 8 | 1 | Clear template offset |
| 9 | 1 | Position template offset |
| 10 | 1 | Erase-line template offset |
| 11 | 1 | Strong-begin template offset |
| 12 | 1 | Strong-end template offset |
| 13 | 1 | Initialize-to-normal template offset |
| 14 | 1 | Deinitialize-to-normal template offset |
| 15 | 1 | Geometry: unknown=0, fixed personality viewport=1, backend SCX stream=2 |
| 16 | variable | Zero-terminated templates |

Offsets are relative to the record start. Zero means absent/empty; a nonzero
offset must be within [16,length), with a terminating zero before the record end.
No external pointers are present. Unknown high operation bits, record versions,
geometry kinds or strong mappings are malformed. Strong mapping zero declares
plain fallback; nonzero mappings require a matched begin/end pair and bit 8.
Geometry kind zero has unknown dimensions; kind one declares its documented
fixed viewport; kind two has zero dimensions in the immutable provider record
and receives actual backend-stream dimensions in the client snapshot.

Template tokens 1/2 emit zero-based row/column plus 32. Tokens 3/4 emit one-based
decimal row/column, without leading zeros. Other nonzero bytes are literals.
Coordinate tokens belong only in position templates. Byte-coordinate templates
require known dimensions no greater than 224. Coordinates accepted by the helper
are zero-based 0–254, additionally bounded by every known dimension. No wraparound
or automatic 80×24 substitution is permitted.

## Application library

historical `src/utilities/common/tcap.inc` (not shipped by the direct implementation) supplies:

- `TC_OPEN`: discover/admit without output and copy to private `TC_TABLE`.
- `TC_EMIT`: A=slot 0–6 in the order clear, position, erase line, strong begin,
  strong end, initialize, deinitialize; B/C hold zero-based row/column for position.
  Every emitted byte uses ordinary BDOS Function 2. Text uses ordinary console I/O.

Results: 0 success/plain fallback, 1 unavailable, 2 malformed description, 3
unsupported operation or bad argument. AF/BC/DE/HL are scratch; IX/IY and SP are
preserved. Failed discovery invalidates the snapshot. Emit refuses an invalid
snapshot or ineligible route. Missing clear/position/erase capability is refused;
missing strong emphasis succeeds without controls. No caller address is retained
by a provider. Helper state belongs entirely to its application and is not
reentrant or suitable for interrupt calls.

Current ADM3A uses reverse video and its fixed 80×24 viewport. ANSI uses reverse
video as a portable strong mapping across the three backends and obtains stream
geometry through SCX. On cpmsim that geometry is unknown; on Model 4/II it is
80×24. VT52 has its fixed 80×24 viewport and readable plain emphasis. Model 4
does not advertise bold or italics through these profiles. Encodable controls
are not evidence of a physical host terminal's attribute/geometry support.

Initialization and deinitialization establish a normal baseline. Applications
balance emphasis and perform exit cleanup. Arbitrary prior rendition, nested
scopes, saved screens and abandoned-session restoration are not promised.
Monitor 5 remains parser reset only. TED may separately use existing qualified
SCRN/SCX fixed-cell and save/restore operations after checking their contracts;
its editor state and restoration policy do not become resident TCAP machinery.

The historical example `src/examples/tcap-demo.mac` is a qualification consumer, not
a migration of TYPE, TED or HELP. The [Z-System benchmark](TCAP-ZSystem-Benchmark.md)
and [memory design](TCAP-Memory-Redesign.md) explain the allocation model.
