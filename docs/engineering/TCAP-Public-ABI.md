# TCAP public ABI and admission contract 1.0

Status: complete public design contract, 7 November 2026, based on merged
PR #661, main `790a19c2`. The identifiers and wire values below are assigned by
this design for a later implementation. They do not describe a shipped service.
No production source, carrier builder or utility is changed by this document.
Utility migrations, HELP delivery and release assignment remain deferred.

This is the authoritative public interface and admission contract. It supersedes
the [interface candidate](TCAP-Interface-Candidate.md) and the unresolved ABI and
admission choices in the earlier [semantic](TCAP-Semantic-Contract.md),
[owner](TCAP-Owner-Transaction-Design.md) and
[integration](TCAP-Integration-Design.md) designs. Their consumer semantics remain
applicable except for the explicit reconciliations below. The
[machine-readable tables](contracts/tcap-1.0.json) and the structural checker
must agree with this document. Neither structural checks nor private XTCP
qualification constitute runtime public-ABI conformance.

## Architecture, discovery and versioning

Users select the protocol their application expects: load M4SCRN and ADM3A,
run the ADM3A-configured application, unload ADM3A, then load ANSI and run the
ANSI-configured application. TCAP never chooses a personality for an application.
The backend renders that personality. Ordinary CP/M byte-stream I/O remains
usable without TCAP. There is no TCAP text-write operation or interception of
file writes. Existing Monitor operations 0–5, SCRN 1.1, SCX descriptor 1.0 and
Function 182 retain their meanings; Monitor 5 remains parser reset only.

The service identifier is exactly `TCAP`, service version 1.0. Lookup uses the
existing 20-byte Function 182 request, major 1, minimum minor 0 and the client's
required advertisement mask. Only the selected personality may advertise it,
as its second service alongside MCON. No new BDOS function, PDS field, global
address or third advertisement is assigned. Registry capacities are queried,
never hard-coded. Failed lookup uses Function 182's own status namespace, not
the TCAP result namespace, and permits legacy/plain operation as appropriate.

| Advertisement bit | Meaning |
| ---: | --- |
| 0 / 0001h | Discover and Admit; mandatory |
| 1 / 0002h | Begin/End semantic emphasis |
| 2 / 0004h | Fixed-cell takeover and Release |
| 3 / 0008h | Explicit Recover and matching-token DescribeSession |

Bits 1 or 2 require bit 3. A 1.0 provider emits no other advertisement bits.
Clients ignore unknown optional bits on newer advertisements but cannot require
or infer their meaning. A newer provider claiming compatibility must still
accept the exact 1.0 wire formats and return 1.0 records when requested. Different
request versions or lengths are Incompatible, with A only; silent prefix parsing
or larger-record negotiation is not part of 1.0. Unknown major lookup fails.
The rediscovery requirements of Function 182 still apply across every
resident-layout publication; a cached address is never a persistent handle.

`XTCP` 0.x, experimental MCON 1.3 and private Monitor 25/26/27 are not aliases.
Their token-only dispatcher is incompatible with the public request envelope.
No private package, including #661, becomes public-conforming by changing its ID.
All eight assigned selectors are recognized by the base public dispatcher. The
advertisement bits constrain which effects can be admitted, not whether a plain
Begin or an invalid-session cleanup can be decoded.

## Call, buffer and failure envelope

A is the selector; DE addresses the 32-byte request. Its operation must equal A.
Return A as status, preserving DE, IX, IY and entry SP, including all returning
failure paths. AF, BC, HL, alternate general registers and flags are scratch.
I, interrupt mode and entry interrupt-enable state are preserved on returning
calls; refresh register R is volatile. Integers are unsigned,
16/32-bit values little-endian; records may be unaligned. Calls are synchronous.
No caller pointer is retained. No interrupts, recursion or output-callback calls
are permitted. The core checks callback/reentry context before dereferencing DE;
ReentryRefused returns A only, writes nothing and preserves the outer call.

A qualified core owns the permitted caller-region map. The mandatory transient
region is [0100h, current usable TPA limit), excluding all live RSX/core storage.
Resident clients require a core-registered caller allocation; a client cannot
extend the region by passing its own bounds. No public ABI for registering those
allocations is introduced. Unsupported resident contexts return Unavailable.
All declared buffer extents must fit one permitted region, using checked wide
addition, without wrapping through zero. Page zero, hardware, owner allocations,
registry descriptors and protected recovery storage are excluded. The caller
must also avoid its executable code and live stack; CP/M cannot generally prove
those aliases. This is cooperation correctness, not memory isolation/security.

The request and every nonempty input/output/token extent must be pairwise
disjoint. Full declared capacities, not just the bytes to be written, are checked.
An absent pair is address=0, size=0. One zero with one nonzero is BadRequest.
For required output/token pairs, (0,0) is a size probe and returns BufferTooSmall.
Inputs require exact sizes. Output and token capacities may be larger; only the
specified 64/96/16 bytes are written and surplus bytes remain unchanged.

Validation order is deterministic:

1. Reject callback/interrupt/reentry context with ReentryRefused, or an
   unsupported caller context with Unavailable, A only without caller-memory access.
2. Validate the full envelope region, then exact major/minor/length. Failure
   returns A only; no request fields are written. An invalid address is
   BadRequest; an unsupported format is Incompatible.
3. Validate selector agreement, assigned selector, zero flags/reserved bytes,
   enum values and per-operation field applicability. Unknown selectors are
   Unsupported; invalid assigned-selector arguments are BadRequest.
4. Validate region membership and disjoint extents. Then check required input
   size, output capacity, token capacity, in that order. A size probe has no
   extent to overlap. Output shortage reports its required size; token shortage
   reports 16. All of these happen before input interpretation or display effects.
5. Validate input structure/version, reserved fields and token shape. Establish
   the trusted matching root/current issued validity before owner/session
   association, then compare live admission facts, then essential
   capability/geometry/policy requirements, then parser/session state, resources
   and exhaustion. Malformed data is BadRequest; unsupported record versions
   are Incompatible. Recovery/cleanup uses its token, not a fresh admission.

Once step 2 succeeds, returning calls write only envelope +20..+25 on failure,
except documented partial-activation token delivery. Set required_size to zero
unless reporting BufferTooSmall. Request flags and +26..+31 must be zero;
old result bytes +20..+25 are ignored as inputs. Output records and token bytes
are otherwise unchanged on rejection. No diagnostic is printed by the service.
A bounded provider copy and revalidation precede effect; callers must not mutate
buffers during a call. Plain is never an escape from a partially applied effect.

Effects bit 0 means a display mutation may have occurred during this call; bit 1
means recovery is still required on return. Other bits are zero. Discover, Admit,
Describe and all preflight rejections have bit 0 clear. A rejected call during
RecoveryRequired still reports bit 1. Successful End/Release/Recover set bit 0,
even if the visible result happened to match. AlreadyRecovered has both clear.
State is the current public owner state; it exposes no token or capture storage.
Unused input/output/token pairs must be (0,0). Unused rendering_class/intent are
zero on End, Release, Recover and Describe. Discover has query intent 0..3;
Admit and activation obey the intent/use matrix below.

## Wire records

Each record with its own format prefix uses major/minor 1/0 and its table size.
Eligibility embeds a 64-byte snapshot: its +2 length is 64, not 96; its 96-byte
extent comes from the operation/input-length contract. The token has no
version prefix; it is interpreted only under service major 1. Reserved bytes
are zero input/output. All values not explicitly assigned are reserved.

### Wire record: request (32 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 1 | `major` |
| 1 | 1 | `minor` |
| 2 | 2 | `length` |
| 4 | 1 | `operation` |
| 5 | 1 | `flags` |
| 6 | 1 | `rendering_class` |
| 7 | 1 | `intent` |
| 8 | 2 | `input_address` |
| 10 | 2 | `input_length` |
| 12 | 2 | `output_address` |
| 14 | 2 | `output_capacity` |
| 16 | 2 | `token_address` |
| 18 | 2 | `token_capacity` |
| 20 | 1 | `status` |
| 21 | 1 | `state` |
| 22 | 1 | `effects` |
| 23 | 1 | `mode` |
| 24 | 2 | `required_size` |
| 26 | 6 | `reserved` |

### Wire record: snapshot (64 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 1 | `major` |
| 1 | 1 | `minor` |
| 2 | 2 | `length` |
| 4 | 4 | `owner_validity` |
| 8 | 2 | `generation` |
| 10 | 1 | `rendering_class` |
| 11 | 1 | `destination` |
| 12 | 1 | `interactivity` |
| 13 | 1 | `row_provenance` |
| 14 | 1 | `column_provenance` |
| 15 | 1 | `wrap` |
| 16 | 2 | `rows` |
| 18 | 2 | `columns` |
| 20 | 2 | `supported_operations` |
| 22 | 2 | `known_operations` |
| 24 | 1 | `physical_rendition` |
| 25 | 1 | `known_rendition` |
| 26 | 1 | `encoder_rendition` |
| 27 | 1 | `semantic_mapping` |
| 28 | 2 | `supported_cleanup` |
| 30 | 2 | `known_cleanup` |
| 32 | 4 | `route_cookie` |
| 36 | 4 | `policy_cookie` |
| 40 | 1 | `control_class` |
| 41 | 1 | `echo_class` |
| 42 | 1 | `plain_override` |
| 43 | 1 | `coordinator` |
| 44 | 2 | `stream_model` |
| 46 | 2 | `stream_revision` |
| 48 | 2 | `baseline` |
| 50 | 2 | `baseline_revision` |
| 52 | 2 | `routing_policy` |
| 54 | 2 | `routing_revision` |
| 56 | 2 | `fixed_model` |
| 58 | 2 | `fixed_revision` |
| 60 | 4 | `reserved` |

### Wire record: eligibility (96 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 64 | `snapshot` |
| 64 | 2 | `required_operations` |
| 66 | 2 | `required_cleanup` |
| 68 | 2 | `minimum_rows` |
| 70 | 2 | `maximum_rows` |
| 72 | 2 | `minimum_columns` |
| 74 | 2 | `maximum_columns` |
| 76 | 2 | `accepted_wrap` |
| 78 | 1 | `use` |
| 79 | 1 | `mode` |
| 80 | 2 | `model_revision` |
| 82 | 2 | `policy_flags` |
| 84 | 1 | `intent` |
| 85 | 11 | `reserved` |

### Wire record: token (16 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 4 | `owner_validity` |
| 4 | 4 | `session_serial` |
| 8 | 4 | `scope_serial` |
| 12 | 1 | `kind` |
| 13 | 3 | `reserved` |

### Wire record: provider_requirements (64 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 1 | `major` |
| 1 | 1 | `minor` |
| 2 | 2 | `length` |
| 4 | 2 | `entry_offset` |
| 6 | 2 | `owner_offset` |
| 8 | 2 | `owner_bytes` |
| 10 | 1 | `core_major` |
| 11 | 1 | `core_minor` |
| 12 | 2 | `core_gates` |
| 14 | 2 | `scx_operations` |
| 16 | 2 | `service_capabilities` |
| 18 | 2 | `routing_policy` |
| 20 | 2 | `routing_revision` |
| 22 | 2 | `stream_model` |
| 24 | 2 | `stream_revision` |
| 26 | 2 | `fixed_model` |
| 28 | 2 | `fixed_revision` |
| 30 | 2 | `baseline` |
| 32 | 2 | `baseline_revision` |
| 34 | 2 | `flags` |
| 36 | 28 | `reserved` |

### Wire record: owner_header (32 bytes)

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 4 | `magic` |
| 4 | 1 | `major` |
| 5 | 1 | `minor` |
| 6 | 2 | `length` |
| 8 | 4 | `owner_validity` |
| 12 | 16 | `build_identity` |
| 28 | 1 | `state` |
| 29 | 3 | `reserved` |

## Snapshot facts and model namespaces

Rendering classes are 0 console stream, 1 fixed cells. Intents are 0 query,
1 interactive reader, 2 noninteractive text, 3 full-screen editor. Destination
is 0 unknown, 1 display, 2 non-display; interactivity is 0 unknown, 1 suitable,
2 unsuitable. Dimension provenance is 0 unknown, 1 fixed viewport, 2 configured,
3 measured. Unknown dimensions and provenance must both be zero; known dimensions
are 1..65535. No truncation or substitution between stream and fixed geometry.

Wrap is 0 unknown, 1 delayed, 2 immediate, 3 fixed clamp. Control class is
0 unknown, 1 cooked model, 2 fixed model. Echo class is 0 unknown, 1 no possible
CRT alias under the admitted policy, 2 alias possible/unmodeled. Value 3 from the
candidate is reserved: no modeled-alias accounting extension is assigned here.
Plain override is 0/1. Coordinator is 0 unqualified, 1 qualified core contract 1.0.
A recognized stream model requires control class 1 and its matching wrap 1/2;
fixed model 1 requires control class 2 and wrap 3. Unknown stream control may
retain independently known wrap, but cannot report stream accounting supported.
Fixed snapshots do not report stream accounting supported.
A successful public Discover requires a nonzero issued owner validity and a
qualified matching root. It may still report unknown/unsupported display facts.

Operation bits 0..10 are, in order: position, literal cell, erase line, erase
screen, cursor visibility, clear/home, semantic emphasis, takeover, stream
accounting, qualified routing boundary, safe return coordinator (mask 07FFh).
Cleanup bits 0..2 are prior logical-rendition restoration, complete prompt
baseline, independent SCX save-slot preservation (mask 0007h). Supported masks
must be subsets of known masks; remaining bits are zero. Unknown and known-false
are different. Metadata rejection is not a capability bit.

Physical rendition bits use the existing SCX flag byte: bold 01h and reverse
20h are distinct; Model 4's known 60h reverse/conceal support is not bold support.
The encoder mask is not evidence of physical endpoint support. Semantic mapping
is 0 plain, 1 known bold, 2 known reverse. Positive mappings require the
corresponding known-supported physical bit, a coordinated nine-byte logical
rendition and qualified cleanup. Plain override forces mapping 0. Supported
operation bit 6 requires a positive mapping and its qualified routing/cleanup;
mapping 0 cannot report that bit supported. Unknown physical support may leave it
unknown, while an explicit plain policy can mark it known-unsupported. A mapping
must not move the cursor, change margins/visibility/wrap, or borrow SCX operation 23's single save slot.
Begin requests semantic strong emphasis, not explicit bold or color. A client
requiring bold accepts only observed mapping 1 with known bold support; the
full-snapshot live comparison prevents a later reverse substitution. No explicit
attribute-setting selector is assigned.
End restores all nine captured logical bytes, including unsupported stored
attributes, rather than reconstructing a mask or restoring an old cursor.

The applied strong record copies the prior nine bytes, clears faint (02h) and
conceal (40h), then sets bold (01h) for mapping 1 or reverse (20h) for mapping 2.
All other flags and both color records remain unchanged. No reverse toggle is
used. The profile must establish that this resulting rendition is readable;
unknown color/endpoint interactions are UnknownFact, known unreadable results
Unsupported, and ALLOW_PLAIN applies only under the ordinary fallback rules.
There is no silent color reset. Discover/Admit must not report positive semantic
support if that readability requirement is unqualified; activation checks the
current logical rendition again before capture/apply.

Cookies are opaque observations scoped by owner validity, not addresses,
permissions, monotonic counters or proof of every IOBYTE store. All fields are
recomputed from trusted live facts at Admit and activation. A well-formed client
snapshot differing from those facts is Stale; client assertions cannot upgrade
unknown facts. Managed route/geometry/model/plain-policy/profile changes rotate
validity while idle. An unmanaged change-and-revert may be unobservable and is
outside the qualified cooperative policy.

The following model and policy pairs are assigned; zero/zero means unknown,
and one zero with a nonzero partner is malformed. A nonzero unrecognized pair
is Incompatible when needed for the requested use, not an inferred known model.
Irrelevant stream/fixed model fields are zero for the other rendering class.

| Namespace | ID / revision | Exact meaning |
| --- | --- | --- |
| Stream | 1 / 1 | Delayed printable wrap; CR cancels pending wrap; LF preserves column and cancels pending wrap; BS cancels pending wrap and moves left with within-line clamp. |
| Stream | 2 / 1 | Immediate printable wrap; CR sets column zero; LF preserves column; BS at column zero moves to the previous row's last column, except at the physical top. |
| Fixed | 1 / 1 | Existing SCRN 1.1 position/literal-cell/erasure/visibility semantics, including fixed 24×80 viewport and clamping; SCX 1.0 supplies extended rendition/margin behavior. |
| Routing | 1 / 1 | Qualified pre-dispatch normal-console observation, cooperative clients, conservative echo policy, no asynchronous/direct-hardware route mutation guarantee. |
| Baseline | 1 / 1 | Renderer repair and explicit home, then exactly one ordinary cooked CR/LF on the admitted console, then infallible ownership retirement. |

For both stream models a printable byte is ASCII 20h..7Eh. CR sets column zero;
LF advances one row within full default margins, scrolling at the bottom. Tabs
are ordinary BDOS-expanded spaces to the next zero-origin eight-column stop;
cooked and modeled columns must agree. BS writes no glyph and never decreases
already consumed page space. No terminal queries, ESC sequences, high-bit bytes,
form feed or arbitrary raw controls are covered by these models. A consumer
encountering them must stop claiming spatial accounting, use a separately
qualified renderer, or take its documented fallback. TCAP does not sanitize TYPE.
An existing personality is certified for a model only after exact behavioral
qualification; these names do not certify current ADM3A, ANSI or VT52 by analogy.

Spatial content accounting starts after a client-owned ordinary CR/LF establishes
column zero and cancels pending wrap, with no authored emphasis open. Reset the
relative page row to zero, column to zero, pending-wrap false and content high
water to zero. A glyph marks its target row occupied; resolve delayed wrap before
that write. Immediate wrap advances after the write without marking the new blank
row occupied. LF marks the current row occupied (including an empty logical line)
then advances. CR and BS do not mark new content. The content count is the highest
occupied relative row plus one, never decreased by BS. Backspacing before the
page origin makes accounting unusable. Use checked arithmetic; do not wrap row
counters. Visible output and hidden replay use this identical transition function.

Thus exact-width text plus CR/LF consumes one row under model 1 and two under
model 2. With R rows, at most R−1 content rows may be occupied. Prompt text fits
in C−1 cells and occupies the next unoccupied row: reuse a modeled empty row
already at column zero, otherwise use CR/LF once. Never add an unconditional
newline after immediate wrap. R and C must both be at least two for spatial use;
clear/home is optional and must be explicitly requested if used. Prompt wording,
keys, logical-line budgets, source replay and changed-file policy remain consumer
work, not TCAP state. Host resize without qualified notification requires explicit
refresh/restart and invalidates spatial anchors; viewport geometry is not a
measurement of physical host size.

### Fixed-cell emphasis uses a defined styled writer

Legacy SCRN operation 7 remains a literal-byte write with its own normal/reverse
bit; it does not acquire semantic rendition because TCAP is loaded. A fixed
client wanting EmphasisFixed uses the existing SCX styled-ASCII operation 21,
not operation 7 for those glyphs. Because SCX 21 has delayed stream wrapping,
fixed model 1/1 specifies this serialized binding for each printable ASCII cell:
position explicitly at (row,column), emit one styled glyph with SCX 21, then
position at (row,min(column+1,79)). Both positions use existing SCRN operation 6.
This cancels pending wrap before the glyph and after the last cell, preserving
the fixed writer's row and clamp semantics, including bottom-right without an
extra glyph/scroll. It assigns no new backend operation and does not alter legacy
SCRN behavior. All three calls must be qualified for that backend/endpoint;
a failed call requires session recovery before rendering continues. No atomic
screen-content rollback is promised. Non-ASCII literal cells remain outside
semantic emphasis. Stream emphasis still emits its text through normal BDOS.
This binding is a future consumer obligation, not a TED migration in this change.

## Admission algorithm and resolved modes

Eligibility contains the complete snapshot, explicit essential masks, paired
geometry bounds, a wrap acceptance mask, use, resolved mode, required model
revision, policy flags and intent. Its snapshot class and intent must match the
request. Admit input mode is zero. Activation requires the exact normalized mode
returned by Admit. All other constraints remain unchanged in the normalized copy.

Use is 0 plain reader (stream, intent 1/2), 1 spatial reader (stream, intent 1),
2 semantic emphasis (stream intent 1/2, or fixed intent 3), 3 takeover (fixed,
intent 3). Intent zero is only a query/unused value. Each dimension is either
(min,max)=(0,0), meaning no constraint, or 1≤min≤max≤65535. A spatial reader
requires nonzero bounds with minimum rows and columns ≥2. Takeover requires
exact (24,24) rows and (80,80) columns. A known value outside any explicit bound
is UnusableGeometry; an unknown required value is UnknownFact. A nonzero wrap
mask requires known wrap in its accepted set; bits 0/1/2 mean delayed/immediate/
clamp. Unknown mask bits or impossible min/max pairs are BadRequest.

Required model_revision is zero for plain use, 1 for spatial/takeover, and 1
for emphasis with an explicit accounting requirement (otherwise zero). It refers to the
selected class's model. An explicit stream-accounting requirement requires a
known assigned stream model/revision. Fixed model 1/1 is required for takeover.
Admit in RecoveryRequired returns RecoveryRequired with no eligibility output.
Plain eligibility never authorizes printing inside an unrelated active session;
the caller must respect the returned state and its own ownership.
Required masks may contain only assigned operation/cleanup bits (otherwise
BadRequest). Cleanup bit 0 refers to emphasis End, not a request to change
Release from baseline recovery to prior-session restoration.
Each explicitly required operation/cleanup bit is essential: unknown returns
UnknownFact, known-false Unsupported. Destination non-display refuses spatial
or takeover with Unsupported; unknown destination/interactivity required for
those uses is UnknownFact. They require interactivity 1. Plain use never creates
ownership: interactivity 1 selects LogicalLines, otherwise Continuous, including
unknown routes. No key waits or spatial claims are authorized by Continuous.

After live snapshot comparison and explicit constraints, add these implicit
requirements; they are not silently written into the caller's essential masks:

| Use | Implicit operation mask | Implicit cleanup mask | Additional conditions |
| --- | --- | --- | --- |
| Plain reader | 0000h | 0000h | No scope/session |
| Spatial reader | 0300h | 0000h | Known complete stream model, geometry, full normal margins/parser state; routing 1/1; echo class 1 regardless of current ^P setting |
| Emphasis | 0640h | 0007h | Known display and supported mapping; routing 1/1 and baseline 1/1; no requirement for stream geometry or interactivity |
| Takeover | 06BFh | 0006h | Qualified SCRN/SCX path, fixed model 1/1, routing 1/1, baseline 1/1, 24×80 fit |

Policy flag bit 0 is ALLOW_PLAIN; all other bits are zero. It is permitted only
for use 2. It relaxes only the implicit emphasis requirements, never an explicit
essential mask, explicit geometry constraint or token requirement. A HELP-like
optional request therefore uses use 2, ALLOW_PLAIN, and no essential emphasis bit.
If explicit requirements pass but implicit emphasis cannot be established, Admit
returns Plain and a normalized plain mode. Without ALLOW_PLAIN return the relevant
Unavailable/Unsupported/UnknownFact/Incompatible result. Takeover never falls back
to a plain editor. A caller refusing spatial admission submits a separate plain
reader request; spatial success is not silently converted to logical-line mode.

Modes are 0 None, 1 Continuous, 2 LogicalLines, 3 SpatialStream, 4 FixedTakeover,
5 EmphasisStream, 6 EmphasisFixed. Modes 5/6 distinguish style eligibility from
geometry/accounting eligibility. Enhanced Admit returns Success with mode 3, 4,
5 or 6 for the corresponding use. Optional plain emphasis resolves to mode 1/2
for stream and mode 4 for fixed-within-takeover; it confers no takeover itself.
Fixed Begin always requires a matching active takeover token, including a plain
result. Discover returns mode 0. Token cleanup uses its captured mode; it never
trusts a newly supplied class/intent.

Admit writes 96 bytes on Success or Plain and does not allocate a serial, session,
lease, tombstone or retained admission. Begin/Activate revalidate every live fact
and recompute the normalized decision; a changed decision is Stale, not a quiet
style downgrade. Eligibility is a stateless observation, not a consumable handle.
It can be reused between emphasis-only scopes while facts remain unchanged.
Clients must refresh after takeover Release or Recover, but the provider cannot
prove that an identical copied observation was freshly obtained. Replay protection
belongs to owner/session/scope identities, not a fictitious consumed-admission bit.
This replaces the candidate's contradictory “retired admission” requirement.

## Operations, tokens and state

| Selector | Operation | Input bytes | Output bytes | Token |
| ---: | --- | ---: | ---: | --- |
| 00h | Discover | 0 | 64 | none |
| 01h | Admit | 96 | 96 | none |
| 02h | BeginEmphasis | 96 | 0 | 16 bytes |
| 03h | ActivateTakeover | 96 | 0 | 16 bytes |
| 04h | EndEmphasis | 0 | 0 | 16 bytes |
| 05h | Release | 0 | 0 | 16 bytes |
| 06h | Recover | 0 | 0 | 16 bytes |
| 07h | DescribeSession | 0 | 0 | 16 bytes |

| Result | Name |
| ---: | --- |
| 00h | Success |
| 01h | Plain |
| 02h | AlreadyRecovered |
| 03h | Unavailable |
| 04h | Unsupported |
| 05h | UnknownFact |
| 06h | Incompatible |
| 07h | BadRequest |
| 08h | BufferTooSmall |
| 09h | UnusableGeometry |
| 0Ah | Stale |
| 0Bh | ParserBusy |
| 0Ch | ScopeState |
| 0Dh | InvalidSession |
| 0Eh | ScopeActive |
| 0Fh | ResourceUnavailable |
| 10h | SessionBusy |
| 11h | ReentryRefused |
| 12h | RecoveryRequired |
| 13h | RecoveryFailed |
| 14h | IdentityExhausted |

| State | Name |
| ---: | --- |
| 00h | Idle |
| 01h | EmphasisOnly |
| 02h | Takeover |
| 03h | TakeoverWithEmphasis |
| 04h | Recovering |
| 05h | RecoveryRequired |
| FFh | Unobservable |

| Mode | Name |
| ---: | --- |
| 00h | None |
| 01h | Continuous |
| 02h | LogicalLines |
| 03h | SpatialStream |
| 04h | FixedTakeover |
| 05h | EmphasisStream |
| 06h | EmphasisFixed |

Discover writes a 64-byte snapshot only on Success. Admit writes eligibility only
on Success/Plain. Other operations have no output record. Begin/Activate take
96-byte normalized eligibility. Cleanup/Describe take no admission input. End,
Release, Recover and Describe never overwrite token bytes. Begin/Activate write
exactly 16 token bytes on Success or a returning partial-activation failure.

An all-zero token requests a new stream emphasis-only session or takeover.
Activate requires zero input, not an existing session token. Fixed Begin requires
a current takeover token; a stream Begin cannot borrow a fixed takeover token
(BadRequest). Tokens have
nonzero validity and session serial; kind 1 takeover has scope serial zero,
kind 2 emphasis has nonzero scope serial. Other shapes are BadRequest, except an
all-zero token where an existing token is required is InvalidSession. A different
owner validity is Stale. An unknown/retired session is InvalidSession; wrong or
retired emphasis within the current session is ScopeState. A token's numbers
are not addresses and may not appear in pointer-repair lists.

Session and scope counters increase without reuse within a validity namespace.
They may reset only when a new validity is published; clients do no arithmetic
on their opaque values.

Activation reserves all resources and serials, arms resident recovery, then changes
presentation. No transient pointer survives return. Exhausted serials return
IdentityExhausted before mutation, never wrap. An activation that has armed state
but cannot complete returns RecoveryRequired, its identifying token and effects
03h; if the transient aborts before receiving it, internal recovery still works.
A complete rollback may instead return the underlying error with unchanged token
and no retained ownership; it must not claim Plain after leaving any effect.

Begin within takeover takes the separately preserved takeover token and writes a
new emphasis token into the supplied token buffer on Success. The caller keeps
its original takeover token elsewhere. Plain leaves the token unchanged, creates
no scope and returns the admitted plain mode; it never calls End on that token.
Second Begin while emphasis exists returns ScopeState. An unrelated activation
while any portable session exists returns SessionBusy. Incomplete parser state at Begin, Activate or End
returns ParserBusy without discarding the sequence or replacing a capture.

End requires kind 2 (a takeover token yields ScopeState); Release requires kind 1
(an emphasis token yields InvalidSession). End restores only rendition. EmphasisOnly → Idle retires that session;
TakeoverWithEmphasis → Takeover retires only the scope. Release requires a current
takeover token, no open scope (else ScopeActive), and successful baseline 1/1.
Release and Recover deliberately perform baseline parser repair; they are not
blocked by ParserBusy once their token/state preconditions pass.
Recover accepts the current takeover token or the current live emphasis token,
repairs the whole session, and retires both scope and takeover. A retired child
scope cannot recover later work even within the same takeover. Describe succeeds
read-only for matching active/RecoveryRequired tokens; effects bit 1 still reports
a retained recovery obligation. It does not discover another session's handles.

Recovering is internal during a serialized call; it must not be returned as a
successful new usable state. A failed/partial cleanup retains RecoveryRequired,
returns RecoveryRequired or RecoveryFailed as appropriate, and blocks Begin,
Activate and profile publication. Recover may retry; Describe may report it.
When trustworthy owner state cannot be observed, state FFh is Unobservable,
never an invented Idle. Missing root/gates yield Unavailable; incompatible trusted
metadata yields Incompatible, with no output record. Effects bit 1 is set when a
trusted root still knows an outstanding obligation.

The bounded recovery tombstone identifies only the most recently successfully
recovered session and the token kinds/scope serial live at that recovery. Thus
recovering TakeoverWithEmphasis can recognize either its takeover or its active
emphasis token on a repeat; an earlier ended scope is excluded. Repeat Recover
returns AlreadyRecovered, Idle, effects zero, and emits nothing. Describe of that
exact tombstone also returns AlreadyRecovered. End/Release create no tombstone.
A new activation discards it when resident ownership is armed, including a
partial activation failure; any validity publication also discards it. A rejected or
plain Begin is not a new activation. Token bytes alone are never evidence that
state remains active; the owner enforces retirement.

Validity values come from one boot-global, non-reusing unsigned 32-bit allocator.
Zero is never issued. FFFFFFFFh is the last value; the next reservation fails
without changing its destination. Failed preparation may burn a value. The
allocator survives provider unload, all-provider removal and warm reconstruction;
it is independent of the 16-byte build identity and 16-bit layout generation.
Managed idle publication rotates validity even for retained STATEFUL relocation
or an unchanged final address. No public allocator/reset API exists. Cold boot
starts a new lifetime: persistent tokens across cold boot are unsupported.

## Recovery and route contract

Baseline 1/1 requires an empty personality parser, nine zero default logical
rendition bytes with backend agreement, full default margins, normal visible
console cursor and no pending wrap. TCAP never borrows the single SCX operation-23 save slot; client
changes to that slot remain the client's responsibility. It restores no screen
image, file/DU state, decoder state or general host-terminal modes.

The safe coordinator verifies the original admitted endpoint is still valid,
performs renderer repair without BDOS recursion, explicitly homes to (0,0) after
restoring margins, then emits CR followed by LF
through ordinary BDOS console output on its own qualified stack. This sets cooked
column zero and the logical row following home without clearing the screen
(endpoint scrolling applies if necessary). Baseline 1 does not preserve the
departing cursor row; implementations cannot choose a different start position
under the same baseline ID. These
two baseline text bytes may be echoed to LIST normally; Begin/End themselves add
no text and no TCAP presentation-control bytes ever enter file/LIST streams.
Full baseline retirement follows the successful LF as an infallible step.

Recovery phase progress is resident, not transient. Completed renderer work and
completed CR/LF bytes are not repeated on a supported retry. Profiles must qualify
synchronous byte completion or a defined fatal disposition for indeterminate
partial transport output; “terminal probably reset” is not Success. A missing or
failed reloader before the coordinator is reachable is a fatal platform stop,
not a completed baseline or guaranteed readable diagnostic.

All rendering callbacks, including the pre-dispatch route observer, are BDOS-free.
A public Release/Recover can invoke the safe coordinator only from a qualified
non-BDOS callback context; otherwise return ReentryRefused A only. Internal warm
return has separate core authority and does not need a client token. Recovery
precedes reconstruction diagnostics, CPX/startup output and the prompt. A late
pre-prompt check is an idempotent guard, not the sole recovery point.

Routing policy 1/1 observes before the ordinary BIOS CONOUT decision, including
sink/bypass routes, and preserves the ordinary byte's routing and printer echo.
It requires cooperative clients not to change IOBYTE or issue unmanaged
presentation controls while owning a session. Qualified SCRN/SCX fixed-cell
operations remain allowed during takeover; raw state writes bypassing the
coordinated owner, and uncoordinated rendition changes during emphasis, do not. Arbitrary asynchronous
or direct-hardware changes, including undetected change-and-revert, are excluded.
An observed unmanaged mismatch repairs through the old valid renderer when safe
and latches RecoveryRequired; it does not redirect cleanup to a new endpoint.
If the original endpoint cannot support baseline CR/LF, retain the obligation and
return RecoveryFailed/use the platform's safe stop path. Do not silently restore
IOBYTE or claim a new endpoint is the old one. A later safe retry may complete.

^P remains operational. Spatial stream admission requires echo class 1 across
all allowed toggles, not merely ^P currently off. Emphasis may tolerate aliasing:
LIST gets ordinary bytes without TCAP-added style controls, but an aliased CRT
can show duplicated styled glyphs. This is not visually independent printing.
Normal diagnostics inside an active authored scope/takeover are the caller's
responsibility: close/recover before printing them. Busy manager paths return
errors without emitting such diagnostics themselves.

Envelope mode is zero on Discover and ordinary failures. Admit Success/Plain
returns its normalized mode. Successful Begin/Activate returns 5/6/4 as admitted;
plain Begin returns its plain mode without creating ownership. Successful End
returns mode 4 when takeover remains, otherwise zero. Successful Release/Recover
and AlreadyRecovered return zero. Describe returns the captured active mode,
including RecoveryRequired. Returning partial-effect RecoveryRequired/Failed
also returns the captured mode when associated with that caller's valid token;
these results are not a new eligibility decision.

## Carrier and system admission: fail closed before publication

The public carrier remains BRSX version 2, STATEFUL, with its existing eight-byte
runtime header and MCON backend word at payload +12. Public integration uses
MCON 1.4 with portable-backend advertisement flags 0004h: operations 0–5 remain
compatible with MCON 1.2, and SCRN 1.1/SCX 1.0
with operation mask 00FFh remain required. The dependency is explicitly SCRN
1.1, not an inference of SCRN minor = MCON minor minus one. MCON 1.3 remains private. Public
integration does not allocate Monitor 25/26/27. An old loader already rejects
MCON 1.4; the metadata-major rule below provides an independent fail-closed gate.

Public TCAP uses BMET **3.0**, header length 12, not a new record smuggled into
BMET 1.0 or 2.0. Its header is +0 signature `BMET` (4 bytes), +4 major 3,
+5 minor 0, +6 length 12, +7 record count, +8 total length word and +10 reserved
zero word. Each record has type/length bytes followed by exactly length payload
bytes. The existing BRSX prefix/checksum/relocation rules remain intact.
A new validator must reject `TCAP` in BMET 1/2 and MCON 1.4 without this contract.
It continues to accept ordinary supported legacy carriers without TCAP. Merely
finding an opaque `TCAP` advertisement on an old core is not qualification.

BMET 3.0 is assigned here only for public TCAP providers. Its first record is
exactly one type 4, length 18: existing binding schema 1, binding class 1
(matching-system), and nonzero 16-byte build identity. “Public service” does not
mean a build-independent binary. Its second record is exactly one type 5,
length 64, the provider_requirements record above. Remaining records are exactly
two type-2 callable advertisements, MCON 1.4 and TCAP 1.0, plus at most one
ordinary type-1 numeric-service list and one type-3 runtime-pointer list.
Unknown, duplicate or reordered mandatory records are rejected. The two callable entries are distinct and both lie at payload offsets ≥14,
outside the owner data region. They cannot share an A=0 entry with incompatible
MCON and TCAP argument formats. No optional
unknown-type rule is introduced. Metadata must still fit strictly below 512 bytes,
with consistent count/extent, and existing pointer/count/capacity bounds apply.

Provider requirements are exact version/length 1/0/64. entry_offset equals the
TCAP advertisement's entry offset. service_capabilities equals its mask, including
mandatory bit 0 and the bit-1/2 dependency on bit 3. core_major/minor is 1/0,
core_gates exactly 003Fh, scx_operations exactly 00FFh. routing_policy/revision
and baseline/revision are 1/1. A supported stream model is 1/1 or 2/1, or 0/0
when unknown; fixed model is 1/1. Unknown stream geometry/model does not prevent
plain/emphasis eligibility, but never establishes spatial support. flags and
reserved bytes are zero. Recognized semantic models require independent profile
qualification, not just the presence of these numeric values in metadata.

owner_offset identifies the 32-byte owner_header, beginning within the payload,
with magic `TCOW`, version 1/0, length 32, matching 16-byte build_identity,
initial validity zero, initial Idle and zero reserved bytes. owner_bytes is at
least 32 and bounds the entire contiguous private mutable owner state. The header
must fit the payload; an additional zero-initialized private tail may extend into
its own allocation, but never the runtime header, backend word, callable code
entry, descriptor tail or another allocation. The matched build manifest supplies
the verified image/data boundaries. Relative offsets are not repaired as pointers;
validity/build IDs are never pointer slots. Real private pointers follow the
existing static/runtime repair union rules. Public layout assigns only this
header, not a general nesting stack or implementation-specific capture fields.

The trusted permanent core contract has six gates:

| Bit | Required proof |
| ---: | --- |
| 0 | Pre-dispatch routing observation, including bypass/sink paths |
| 1 | Early warm/reloader recovery and idempotent pre-prompt guard |
| 2 | Safe returning public Release/Recover context and progress handling |
| 3 | Serialized idle-only manager/profile/policy publication |
| 4 | Boot-global validity reservation/publication and exhaustion handling |
| 5 | Complete matching-system executable inventory and load-front-door checks |

These bits are required evidence in a trusted platform/build qualification
manifest, not a provider's assertion that grants itself privileges. The root is
outside optional allocations, survives unload/warm return and is established
from the platform's verified cold chain. Core identity and admitted artifact
inventory must match the carrier binding. No public fixed root address, third
service, provider-supplied root pointer or unvalidated probe call is introduced.
Internal owner/coordinator entry wiring is matched-build-private and sealed with
that inventory; it cannot change the public calling convention or callback rules.

The manifest identifies every executable role that can admit, publish, route or
recover TCAP: resident routing/root, command return/reload paths, metadata and
manager overlays, finalizer/publisher/commit, staged readers/cache workers and
owner/backend qualifying images. Platforms explicitly declare nonexecuted roles;
Model 4 excluding stage 2 does not qualify a platform that executes it. Lengths,
identities and trusted checksums/hashes are verified before copying/executing at
every load front door, including reads after initial inventory admission and warm
cache reconstruction. A checksum supplied only by the candidate is not a trusted
pin. Unknown/missing/mismatched required roles prohibit admission and reservation.
Checks detect mismatch/corruption, not malicious arbitrary-memory software.

The complete publication sequence is:

1. Inspect trusted current ownership and reject active/Recovering/RecoveryRequired
   profile mutation before filesystem preparation or candidate reads.
2. Validate BRSX, BMET, identities, entry/data extents, repair lists, duplicate
   services and discoverable registry capacity, without executing candidate code.
3. Verify the trusted root, all required executable roles and qualified backend
   descriptor/profile facts. Read-only descriptor calls use only already-validated
   code. Validate SCRN/SCX versions and full mask; keep physical style knowledge
   separate from encoding and fixed geometry separate from stream geometry.
4. Recheck ownership and serialize activation against publication.
   Profile mutation includes policy/geometry changes and unrelated compaction.
5. If the prospective profile has a TCAP owner, reserve a fresh nonzero validity
   into durable transaction scratch before live movement. With no prospective
   owner, reserve nothing; removal remains possible at namespace exhaustion. A failed plan burns it; never recycle it or overwrite the old owner.
6. Perform only validated infallible movement/repair/publication. Write prepared
   validity into the new owner, publish its complete binding/registry, then the
   resident generation last. No terminal callback, BDOS I/O or new fallible read
   is inserted into that commit interval.
7. On preparation failure preserve old binding, profile, TPA, generation and
   live owner state. A separately requested successful recovery is not rolled
   back or resurrected by a later failed transaction. Busy errors do not print.

Cold carrier bytes require zero validity/Idle. Retained live or cache snapshots
are a different validation path: nonzero validity is accepted only when bound to
the currently trusted live owner, build, current-boot profile and generation,
with ownership already recovered before reconstruction. An old/offline snapshot
cannot mint validity or resurrect a prior session. Warm reconstruction that
retains the same profile keeps the allocator; any actual profile publication
uses the fresh-validity sequence above. Cold boot does not revive old cached
handles.

Each public entry additionally checks its admitted matching root and current
issued validity. Discover/Admit cannot enable a cold zero-validity image copied
by hand. Successful metadata admission alone does not certify every dynamic
route, geometry, echo or cleanup requirement. Activation checks both layers.
An observed policy invalidation requires idle validity refresh before new
admission. Cleanup must not depend on obtaining that successor value: complete
recovery even at allocator exhaustion, then keep enhancement disabled if a new
validity cannot be issued. Ordinary legacy/plain I/O remains available. Unknown
or lost trusted owner state follows the safe failure disposition, never guessed
callbacks or a forgotten outstanding obligation.

## Review oracles and conformance boundary

These are normative acceptance cases, not tests run against a public provider.
The structural checker verifies wire-table consistency only. Public conformance
requires implementation and runtime qualification of these cases on every claimed
platform/profile; the private package's 516 checks are reusable evidence for its
own implementation, not an automatic public conformance certificate.

| Case | Required result/observation |
| --- | --- |
| No service / old major | Function 182 failure; no guessed entry or private XTCP call |
| Request 31/33 bytes, minor 1, wraparound region, forbidden page zero | Incompatible for format; BadRequest for region; no effect; envelope-write rules above |
| Valid envelope with overlapping buffers, reserved bit, mismatched selector | BadRequest; only envelope results change |
| Output/token size probe | BufferTooSmall with 64/96/16; no partial output/capture |
| Unknown geometry with plain interactive use | Success/LogicalLines, no spatial promise |
| Same geometry with required spatial use | UnknownFact; separate plain admission required |
| Fixed viewport 24×80 but unknown host stream size | Does not create stream dimensions; takeover still needs qualified physical fit |
| Exact-width text plus CR/LF | Model 1 consumes one content row, model 2 two; replay identical |
| Width one or a prompt needing C cells | No spatial fit claim; refuse/fallback before unsafe prompt |
| ^P off but LIST can alias CRT | Spatial refusal; optional emphasis may remain eligible without style bytes on LIST |
| Encoder bold only, physical bold unknown | No bold mapping claim; optional use Plain only if explicit essentials pass |
| Reverse mapping, no geometry | EmphasisStream mode 5 possible; not SpatialStream mode 3 |
| Plain override + essential emphasis bit | Unsupported, not relaxed by ALLOW_PLAIN |
| Optional plain Begin inside takeover | Original takeover token unchanged; no scope or End obligation |
| Second Begin, stale/wrong token, parser busy End | No capture replacement; active state/correct token survives |
| End within takeover | Restore rendition only; state Takeover and original takeover token remains valid |
| Styled fixed-cell text at bottom-right | Position, SCX 21, clamped reposition; no inherited delayed-wrap scroll, no change to literal SCRN 7 |
| Strong over prior faint/conceal/colors | Clear only faint/conceal, set selected strong bit, preserve colors/other flags; refuse unknown/unreadable resulting mapping |
| Release with active scope | ScopeActive, no reset or retirement |
| Partial activation/aborted transient | Resident obligation armed first; returning failure delivers token when possible |
| Callback public Recover/reentrant alias of outer request | A=ReentryRefused only; no outer-state/buffer overwrite or recursive BDOS |
| Warm return with active ownership | Renderer repair, safe cooked CR/LF, retire before diagnostics/prompt |
| Repeat recovery / earlier ended child token | Exact tombstone AlreadyRecovered with no output; ended child cannot reset later work |
| Route moved to another endpoint | No cleanup through that new endpoint; retain obligation/fail safely if original baseline cannot complete |
| Invalidated policy and exhausted successor validity | Cleanup completes if possible; new enhancement remains disabled; no identity reuse |
| MCON 1.2 plus forged TCAP / TCAP in BMET 1/2 / wrong build / zero-validity image | Reject public admission; old cores never qualify by advertisement alone |
| Required role corrupt on a later read | Reject before copy/execute even if its admission bit was previously set |
| Managed mutation while active, including unrelated removal | Side-effect-free busy rejection before preparation and again at serialized boundary |
| Late preparation failure after reservation | Old published profile intact; reservation burned; retry gets a fresh value |
| Same-address reload, generation wrap, all-provider unload | Old token invalid; boot-global allocator not reset by unload/warm return |
| True cold boot / fatal pre-coordinator loader failure | No cross-boot handles; fatal stop does not claim completed prompt recovery |

The next work is public-provider/core implementation and measured qualification:
BMET 3 validation, public envelope/record handling, model/policy fact construction,
full activation/cleanup state machine and per-platform safe entry integration.
The private reference's 1 KiB permanent reservation, 232 relocation words and
1 KiB overlay fits are not evidence that these additional public handlers fit.
Measure code, optional page-rounded storage, first-provider overhead and stack
again; do not silently widen limits or change protected memory policy.

No further service-selector, wire-layout, fallback, model-ID, metadata-binding or
admission-policy design decision is left open by this contract. Runtime readiness,
platform qualification, production packaging/activation, consumer migrations,
HELP's hold and release assignment remain distinct later work.

## Reconciliation with the unallocated candidate

| Candidate ambiguity | Public 1.0 resolution |
| --- | --- |
| Advertised spelling without loader handshake | Public TCAP / MCON 1.4, mandatory BMET 3 binding and core gates; no private-ID promotion |
| Reserved snapshot tail | Assigned model, routing and baseline ID/revision pairs; last four bytes remain zero |
| Reserved eligibility tail | ALLOW_PLAIN policy flags and echoed intent, with eleven zero bytes remaining |
| Style success called spatial mode | Separate EmphasisStream/EmphasisFixed modes 5/6; dimensions may remain unknown |
| Read-only admissions described as consumed | Stateless observations with revalidation; tokens enforce retirement; freshness discipline is explicit |
| Implicit fallback versus essential masks | Only implicit emphasis requirements are optional; explicit essentials never relax |
| Qualified CRT echo model left unspecified | No modeled-alias extension assigned; initial spatial policy requires no possible alias |
| Unobservable owner state reported as Idle | FFh sentinel, with no invented baseline or positive record |
| Partial activation versus recovery tombstone | Arming new ownership invalidates the old tombstone, including partial failures |
| Per-profile prompt start undecided | Baseline 1/1 uses renderer repair, explicit home, one safe cooked CR/LF and retirement |

All changed values were previously unallocated candidates. This is not an ABI
upgrade of an implemented public service and requires no utility migration now.
