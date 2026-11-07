# TCAP interface candidate and design review closure

Status: binary-interface candidate for review, 7 November 2026. Completes the
[proposed integration package](TCAP-Integration-Design.md) with concrete record
shapes, operation/results and a cross-contract review. These are candidate
values and offsets for discussion, not allocations, implemented interfaces or
an accepted ABI. No implementation or prototype is authorized by this document.
HELP remains held; measured feasibility and release assignment remain open.

Baseline: source audit at main `d7c0e831` plus the integration design at
`822782c5`. This candidate does not depend on a claim that PR #652 is merged.

## Discovery and compatibility

Candidate public service spelling is `TCAP`, proposed ABI 1.0. It would be a
second advertisement on the selected personality, discovered with Function 182.
No such service is added here and no current carrier is claimed to supply it.
Any later authorized experiment must use an explicitly private identifier such
as `XTCP`, never imply compatibility with an allocated public service.
Repository source/build searches found no current TCAP/XTCP service declaration;
that is a collision check, not an allocation authority.

Proposed advertisement bits are bit 0 snapshot/admission, bit 1 semantic emphasis,
bit 2 takeover and bit 3 explicit session recovery. Bits 1/2 require bit 3 and
a qualified coordinator, not just a backend capable of changing styles. Unknown
advertisement bits are ignored; required unknown bits fail registry lookup.
All successful clients still check per-snapshot facts and admission. Existing
MCON/SCRN versions and masks remain independently required by TED.

An old core may discover an advertised candidate only if the provider is present,
but cannot satisfy enhanced eligibility without coordinator compatibility.
The provider must return unavailable/refused, not attempt new fixed entry points.
The future loader metadata rule must validate coordinator requirements before
publishing enhanced providers. This candidate assigns no metadata tag or internal
vector and does not reinterpret an existing service revision as that handshake.

## Candidate common request: 32 bytes

A selects the operation; DE points to the request. The operation at +4 must match
A. Return A as status; preserve DE, IX, IY and SP. Other registers and flags are
scratch. No carry-based status convention is implied. Bytes are unsigned and
words/dwords little-endian. Records may be unaligned. Calls are synchronous and
non-reentrant; no request, record or token pointer survives return.

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 1 | Request major, candidate 1. |
| 1 | 1 | Request minor, candidate 0. |
| 2 | 2 | Request length, exactly 32 for this candidate. |
| 4 | 1 | Operation, matching A. |
| 5 | 1 | Input flags; zero. |
| 6 | 1 | Rendering class: 0 console stream, 1 fixed cells. |
| 7 | 1 | Intent: 0 query, 1 interactive reader, 2 noninteractive text, 3 full-screen editor. |
| 8 | 2 | Input record address, or zero for no input. |
| 10 | 2 | Input length, or zero. |
| 12 | 2 | Output record address, or zero for no output. |
| 14 | 2 | Output capacity, or zero. |
| 16 | 2 | Token address, in/out as specified per operation, or zero. |
| 18 | 2 | Token capacity: 16 when used, zero otherwise. |
| 20 | 1 | Returned status, matching A when the envelope is valid. |
| 21 | 1 | Returned current session state. |
| 22 | 1 | Effects: bit 0 display mutation may have occurred; bit 1 recovery required; other bits zero. |
| 23 | 1 | Returned mode: 0 refused/none, 1 plain continuous, 2 logical-line, 3 spatial stream, 4 fixed takeover. |
| 24 | 2 | Required output size on buffer-too-small; otherwise zero. Token-too-small reports 16. |
| 26 | 6 | Reserved, zero input/output. |

Envelope result fields are outputs; prior contents are ignored. Validate the
request before any output buffer write or display effect. If the envelope itself
is unreadable/incompatible, return only A and make no memory-write guarantee.
For a valid envelope, always return status/state/effects, including errors.
Output records and tokens are unchanged on preflight rejection, including small
buffers. Exact input lengths are required. Larger output capacity is allowed,
but only the defined output bytes are written. No partial-record success exists.

This candidate intentionally rejects longer/different-minor requests rather than
promising forward parsing without a defined extension scheme. A future minor
may keep accepting exactly this request; clients require only a documented
minimum service minor, not guessed record offsets from a newer provider.

All ranges must fit within 0000h–FFFFh without wrapping, and within the supported
writable/readable caller region. Request, input, output and token ranges must not
overlap each other, provider allocations or protected state. No variable-length
strings, callback pointers or executable addresses occur in these records.
CP/M has no memory protection: validation is a correctness contract for cooperating
callers, not a security guarantee against arbitrary memory corruption.

## Candidate display snapshot: 64 bytes

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 1 | Snapshot major 1. |
| 1 | 1 | Snapshot minor 0. |
| 2 | 2 | Length 64. |
| 4 | 4 | Nonzero owner validity identity. |
| 8 | 2 | Observed resident-layout generation; never the sole identity. |
| 10 | 1 | Rendering class matching the request. |
| 11 | 1 | Destination: 0 unknown, 1 display, 2 non-display. |
| 12 | 1 | Interactivity: 0 unknown, 1 suitable for prompts/input, 2 unsuitable. |
| 13 | 1 | Row provenance: 0 unknown, 1 fixed viewport, 2 configured, 3 measured. |
| 14 | 1 | Column provenance, same values. |
| 15 | 1 | Wrap: 0 unknown, 1 delayed wrap, 2 immediate wrap, 3 fixed-cell clamp. |
| 16 | 2 | Rows; zero only when row provenance is unknown. |
| 18 | 2 | Columns; zero only when column provenance is unknown. |
| 20 | 2 | Supported-operation mask. |
| 22 | 2 | Known-operation mask; supported bits must be a subset. |
| 24 | 1 | Known-supported physical rendition mask, using SCX flag meanings. |
| 25 | 1 | Known physical-rendition mask; supported bits must be a subset. |
| 26 | 1 | Encoder rendition mask, distinct from physical support. |
| 27 | 1 | Semantic mapping: 0 plain, 1 known bold, 2 known reverse. |
| 28 | 2 | Supported cleanup mask. |
| 30 | 2 | Known cleanup mask; supported bits must be a subset. |
| 32 | 4 | Route observation cookie, meaningful only under owner identity. |
| 36 | 4 | Geometry/policy observation cookie, under the same identity. |
| 40 | 1 | Control model: 0 unknown, 1 documented cooked ASCII profile, 2 fixed-cell profile. |
| 41 | 1 | Echo: 0 unknown, 1 no possible CRT alias under admitted route, 2 alias possible/unmodeled, 3 qualified modeled alias. |
| 42 | 1 | Plain override: 0 disabled, 1 enabled. |
| 43 | 1 | Coordinator state: 0 unqualified/absent, 1 candidate-v1 qualified. |
| 44 | 20 | Reserved zero. |

Candidate operation-mask bits 0–10 are position, literal cell, erase line,
erase screen, visibility, clear/home, semantic emphasis, takeover, known stream
accounting model, qualified route boundary and safe return coordinator. All
higher bits are reserved zero. For each bit: known=0 means unknown; known=1 and
supported=0 means unsupported. Metadata incompatibility is a result, not an
invented capability bit. An encoder mask may be positive while all physical
style support remains unknown.

Candidate cleanup bits 0–2 are prior-rendition restoration, full prompt baseline
and independent SCX save-slot preservation. Unknown bits are reserved zero.
Emphasis requires all three; takeover requires the baseline and slot-preservation
guarantees plus its essential screen operations. A provider cannot advertise
full baseline on the strength of existing AN_RESET alone.

The cooked ASCII profile must document its tab origin/interval, CR, LF,
backspace, pending-wrap and screen-edge semantics; value 1 is not permission
to assume every personality implements one universal model. Eligibility also
requires the selected profile's published model to match the consumer counter.
The fixed-cell profile retains SCRN's clamp semantics. Geometry has its own
provenance; no live physical-size measurement is implied by a class tag.

Cookies are observations, not pointers or capabilities and not a global routing
event counter. Recompute/revalidate all live assumptions at activation. A cookie
must not be used to claim detection of IOBYTE change-and-revert between calls.
Relevant managed policy changes replace the validity identity at an idle
transition; no wrapping cookie alone keeps an admission valid.

## Candidate eligibility record: 96 bytes

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 64 | Copied snapshot. |
| 64 | 2 | Required-operation mask. |
| 66 | 2 | Required-cleanup mask. |
| 68 | 2 | Minimum rows. |
| 70 | 2 | Maximum rows. |
| 72 | 2 | Minimum columns. |
| 74 | 2 | Maximum columns. |
| 76 | 2 | Accepted wrap mask: bits 0/1/2 represent delayed/immediate/clamp; zero means no spatial wrap requirement. |
| 78 | 1 | Requested use: 0 plain reader, 1 spatial reader, 2 emphasis, 3 takeover. |
| 79 | 1 | Resolved mode; input zero for Admit, returned mode for activation. |
| 80 | 2 | Required known control-model revision; zero for plain use, candidate 1 for a matched spatial/fixed model. |
| 82 | 14 | Reserved zero. |

Admit receives a candidate snapshot plus constraints, validates them against the
current profile and returns a separate normalized eligibility record. It retains
nothing. For a non-spatial dimension, minimum and maximum are both zero; otherwise
1≤minimum≤maximum≤65535. Spatial stream height minimum is at least 2. TED requests
the existing exact 24×80 fixed viewport; a larger physical display changes neither
that descriptor nor TED's layout. A partial-known geometry cannot satisfy spatial
requirements. If current live facts differ, return stale rather than silently
relaxing required constraints.

Required masks and bounds describe essentials. Plain reader use can succeed with
unknown dimensions. Spatial use with unknown/unmodeled facts returns refused;
the binding then submits a separate plain-reader admission for logical-line or
continuous fallback. Do not return spatial success with plain mode. Emphasis
may return plain/no token only when no essential screen takeover was requested.
User plain override suppresses optional styling; it does not turn TED into a
plain-console editor. TYPE/HELP still own prompt text, logical-line budget and
restart behavior.

## Candidate token: 16 bytes

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 4 | Owner validity identity. |
| 4 | 4 | Session serial. |
| 8 | 4 | Scope serial: zero for takeover token, nonzero for emphasis token. |
| 12 | 1 | Kind: 1 takeover, 2 emphasis. |
| 13 | 3 | Reserved zero. |

An all-zero token requests creation for ActivateTakeover or emphasis-only Begin.
Begin inside takeover accepts its matching takeover token and returns a distinct
emphasis token in the caller's token buffer. The caller preserves its takeover
token separately. End consumes an emphasis token logically, not by relying on
caller memory erasure. Release consumes the takeover. No other numeric zero or
kind authorizes recovery of an unrelated session.

Serials and validity identities never wrap. Refuse activation at exhaustion,
without changing the display. The allocator survives provider unload and is
costed as fixed state; snapshot cookie values cannot substitute for it. Scope
serials continue increasing across scope-only sessions and across successive
scopes within a takeover under one validity identity. Manager publication while
idle replaces validity; all older tokens/admissions fail even at a reused address.

Keep a tombstone for the most recently successfully recovered session sufficient
to recognize repeat Recover before a newer activation or validity transition.
Only that repeat returns already-recovered without output. A new activation
invalidates the tombstone; an older token cannot recover the new session. Normal
End/Release does not create a recovered-session tombstone. This is bounded owner
state with a measured cost, not an unbounded retired-handle table.

## Candidate operation and buffer table

Candidate local values below are not allocated public selectors.

| Value | Operation | Input | Output | Token |
| --- | --- | --- | --- | --- |
| 00h | Discover | none | 64-byte snapshot | none |
| 01h | Admit | 96-byte constraints/snapshot | 96-byte normalized eligibility | none |
| 02h | BeginEmphasis | 96-byte eligibility | none | zero or matching takeover in; emphasis out on success |
| 03h | ActivateTakeover | 96-byte eligibility | none | zero in; takeover out on success |
| 04h | EndEmphasis | none | none | matching emphasis in; unchanged bytes out |
| 05h | Release | none | none | matching takeover in; unchanged bytes out |
| 06h | Recover | none | none | matching active/recovery-required or repeat-recovered session in |
| 07h | DescribeSession | none | none | matching token in; state/effects returned in request |

A plain Begin returns plain with the zero token unchanged and creates no ownership.
Preflight rejection preserves any existing valid token and capture. After a partial
apply, return the newly created token and recovery-required state so the client
can identify its obligation; never leave a partially active scope with only a
zero token. Internal command-return recovery must still work if no client receives
a token due to abort. Public Recover cannot perform the unsafe return-path BDOS
coordination from inside a callback: it either runs through a qualified safe
coordinator entry or returns recovery-required, retaining the obligation.

During takeover, optional emphasis plain fallback leaves the takeover token
unchanged. The caller must distinguish that result from scope activation and
must not End the takeover as though it were an emphasis token.

## Candidate result and state tables

| Value | Result | Effect contract |
| --- | --- | --- |
| 00h | Success | Requested effect completed; inspect state/token. |
| 01h | Plain | No new emphasis scope; existing takeover, if any, remains active. |
| 02h | Already recovered | Exact supported repeat; no output or mutation. |
| 03h | Unavailable | Missing optional facility/coordinator; no new mutation. |
| 04h | Unsupported | Known essential operation unavailable. |
| 05h | Unknown fact | Required route, geometry or support is unknown. |
| 06h | Incompatible | Unsupported metadata/request version. |
| 07h | Bad request | Invalid fields/ranges/overlap, no mutation. |
| 08h | Buffer too small | Required size returned; no partial output record. |
| 09h | Unusable geometry | Known size/model outside constraints. |
| 0Ah | Stale | Admission/binding validity changed; rediscover. |
| 0Bh | Parser busy | Incomplete sequence preserved; existing scope remains active. |
| 0Ch | Scope state | Second begin or wrong/retired emphasis token. |
| 0Dh | Invalid session | Unknown/retired/incorrect takeover/session identity. |
| 0Eh | Scope active | Release refused until End or Recover. |
| 0Fh | Resource unavailable | Could not reserve required ownership/recovery state. |
| 10h | Session busy | Profile mutation or incompatible activation refused. |
| 11h | Reentry refused | No recursive effect; preserve outer operation state. |
| 12h | Recovery required | Partial effect/observed conflict; enhanced operations blocked. |
| 13h | Recovery failed | Baseline not established; retain obligation and safe system failure disposition. |
| 14h | Identity exhausted | No wrap/reuse; plain/legacy operation remains available. |

All other values are reserved. The request effects bits distinguish successful
normal display changes from preflight rejection and partial-effect failures.
A successful End sets mutation-possible even if the restored value happened to
match visually. A read-only discovery never sets it. Error reporting must not
print automatically into a takeover or span; the caller closes/recovers first.

Candidate states 0–5 are Idle, EmphasisOnly, Takeover, TakeoverWithEmphasis,
Recovering and RecoveryRequired. DescribeSession requires a matching identity;
it cannot enumerate unrelated ownership. A retired recovered token can report
Idle/already-recovered only under the bounded tombstone rule.

## Cross-contract review and reconciliations

| Review issue | Required interpretation across the package |
| --- | --- |
| Read-only admission versus token allocation | Admit copies eligibility only. Live serial/capture/resource reservation happens at activation, before mutation. |
| Plain Begin inside a takeover | No new token/scope; existing takeover ownership is preserved. |
| Lost/partial activation result | Persistent owner is armed first; coordinator can recover even if transient never sees a token. |
| Repeat recovery versus stale handles | Bounded tombstone recognizes only the latest recovered session until new activation/validity. Never reset a later session. |
| Public callback versus safe coordinator | No callable operation recursively invokes BDOS. Full baseline runs only through the qualified safe entry context. |
| CRT LIST alias | Guarantee no TCAP-added style bytes, not visually independent rendering or one glyph per source byte. |
| Active manager movement | Initial implementation direction rejects it; semantic descriptions of possible rebinding are future extensions, not initial support. |
| Geometry/model knowledge | Fixed 80×24 and host encoding masks do not establish stream dimensions or physical style support. |
| Prior rendition and prompt baseline | End restores the captured logical rendition; abnormal recovery establishes defaults and the admitted prompt-start policy. |
| Metadata capacity | Optional second personality advertisement fits current declared capacity; it does not create a third service or a fixed registry table. |
| Small fixed records versus memory policy | Record sizes are candidate data sizes only, not code, stack, allocation or unloaded-TPA measurements. |

This closes the documentation-only interface design pass. The remaining acceptance
items are engineering approval of candidate values/records, actual source placement
and memory measurements, safe coordinator/manager integration, and runtime/native
qualification. They require a separately authorized implementation campaign.
Publishing or merging this candidate does not freeze the public service or declare
TCAP delivered. No further prose-only phase is asserted to substitute for those
measurements, and HELP's hold is unchanged.
