# BetterCP/M 1.2 named directories

## Status and authority

Approved 1.2 implementation. This document records the decisions made in the
NDR workstream and the implementation's memory and interface boundaries.
It does not change the published 1.1/1.1.1 release identities or claim that new
release images have been qualified. Operator instructions are in
[Named Directories](../user/NDR.md).

## Scope

- Exactly 32 live entries in the supplied build; names have 1–8 letters/digits.
- Names are case insensitive and stored uppercase, space padded to eight bytes.
- Numeric directory syntax is reserved: all-digit names and A–P followed only
  by zero or more digits cannot be assigned, including out-of-domain numbers.
- Names are flat aliases for canonical drive/user locations, not a new
  filesystem hierarchy or a security mechanism. Drives cover A–P, users 0–31.
- Multiple names may refer to one DU. Reverse lookup uses the first live slot.
- Existing names must be deleted explicitly before reassignment.
- `NDR.RSX` owns the authoritative live table inside its allocation. Neither
  the PDS nor a second name map is involved. There are no loader arguments or
  runtime capacity changes. Rebuilding the capacity constant is separate work.
- Warm boot and normal stateful RSX reconstruction retain the table. Unload
  discards it and recovers the allocation. A fresh load starts empty; saved
  `.NDR` sets and an explicit startup command provide cold-boot persistence.

## Resolution and presentation

The provider exposes one name resolver. CCP and PATH use that same service;
saved sets are never consulted during ordinary resolution.

Before dispatch, CCP translates `NAME:` prefixes at command-token boundaries
and following an assignment separator. This covers navigation, qualified
commands and filename operands without adding a name map to individual utility
parsers. The ordinary numeric parsers continue to enforce their existing drive,
user and filespec policies. The working spelling is `Duu:` with a two-digit
user number. For example, `UTILS:TOOL` becomes `B00:TOOL`.

The original case of non-prefix text is preserved. A double-quoted token is
literal and is not expanded. Unknown names are left for the ordinary parser to
reject under its existing rules. Expansion cannot exceed the 127-byte command
buffer; overflow rejects the command before dispatch. Leading `:` and `.`
transient-dispatch prefixes remain intact. Bracket/compound named selectors and
name recognition inside an application's own interactive input are not defined
by this feature; ordinary numeric selector syntax remains available.

The main prompt displays `A0 [COMMANDS] >` when the current DU has a name.
Unnamed locations retain the numeric prompt. Other numeric DU reports do not
gain prompt annotations.

PATH.COM accepts a named operand with its colon. It resolves names immediately
and publishes only the existing numeric DU representation. For example:

```text
PATH $$ ROOT: B2: UTILS: C0:
```

with ROOT=A0 and UTILS=B0 stores `$$ A0: B2: B0: C0:`. Subsequent changes to
the namespace cannot retarget the stored list. Numeric and symbolic-current
PATH input continues to work with no NDR loaded. PATH edits remain staged and
atomic; an unresolved named operand cannot partially publish the list.

## Memory contract and benchmark

The target is 512 bytes for the complete protected NDR provider, allowing at
most 768 bytes. Reclaimable CCP growth is reported separately and is less
consequential than NDR's protected allocation. NDR.COM and file I/O are transient.

ZCPR3's documented NDR uses 18 bytes per entry (drive, user, eight name bytes,
eight password bytes), plus a terminator: 253 bytes for 14 entries and 577
bytes for 32. Its name/prompt lookup code is in the command processor, not in
that buffer. Source inspection suggests roughly 100–150 bytes for the basic
lookup/display paths with password checking disabled; this is an instruction
estimate, not a measured complete-build delta.

References: [ZCPR3 installation manual, sections 3.3.13 and 5.4](https://oldcomputers-ddns.org/public/pub/manuals/zcpr/zcpr3_installation_manual.pdf),
[ZCPR 3.3 source, DIRSCAN/DU2DIR/prompt](https://www.df.lth.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/zcpr33/zcpr33/zcpr33.z80.txt).

Current measured accounting:

| Component | Bytes |
| --- | ---: |
| 32 entries × (eight name bytes + separate drive/user bytes) | 320 |
| Provider code and eight-byte runtime header | 158 |
| Callable descriptor | 10 |
| Explicit in-allocation cache footer | 10 |
| Remaining page padding | 14 |
| **Protected NDR allocation** | **512** |
| Additional reclaimable CCP allocation against v1.1.1 | 256 |
| Additional protected BDOS/BIOS/PDS allocation | 0 |

Separate drive/user bytes are intentional: 16 drives × 32 users cannot fit in
one byte. RCP.CPX is unchanged. The inline-footer flag prevents another cache
page being charged to NDR. The production manager test verifies an actual
512-byte marginal TPA charge and complete recovery on unload.

There is also the existing shared 1024-byte RSX manager/resolver area whenever
the profile is nonempty. Thus loading NDR as the first RSX costs 1536 bytes;
adding it to an already active profile costs 512. Removing the final RSX
releases that existing shared area too. It is not an NDR-specific addition.

CCP grows from 5593 to 5885 emitted bytes, with allocation increasing from 5632
to 5888. RAW/POKE scratch and the stack are trailing write-before-read storage;
their allocation remains, but their zero bytes are omitted from the carrier.
The unchecked bootstrap carrier is 6654 bytes and fits its existing 6656-byte
disk slot. Neither reserved tracks nor the filesystem boundary changes.

## Callable service ABI 1.0

Discover service `NDR ` through public Function 182. Refresh discovery after
any manager operation; never retain a callable address across reconstruction.
The provider is STATEFUL, has no runtime-created pointer slots, and uses only
the existing public chain/service interfaces. Its payload is platform independent.

| A on entry | Inputs | Success result |
| ---: | --- | --- |
| 0 | HL points to a name; B is its exact length, 1–8 | DE is drive 1–16 and user 0–31 |
| 1 | D is drive 1–16; E is user 0–31 | HL points to the first matching eight-byte name |
| 2 | HL points to a writable 320-byte buffer | Copies a complete snapshot |
| 3 | HL points to a validated 320-byte candidate | Replaces the complete table |

A=0 means success; A=FF means missing name/DU or unsupported operation.
BC, DE, HL and flags are scratch. Reverse-lookup pointers are borrowed and
must not survive a manager operation. Snapshot/replacement callers supply the
complete valid buffer. Replacement is a trusted management operation:
NDR.COM validates characters, padding, reserved names, duplicates and DU ranges
before calling it. The copy makes no BDOS calls and has no recoverable failure
path. The ABI is not an access-control boundary.

Each entry is eight name bytes, drive 1–16, user 0–31. An unused entry consists
of ten zero bytes. There is no separate live count or duplicate resident index.

## Saved sets and management

`NDR.COM` lists assignments and their in-use count, assigns, deletes, clears,
loads and saves. Command tails accept ordinary leading blanks and case-insensitive
operation keywords. Successful loads are reported separately from unsaved edits.
It provides standard
`/H`, `/HELP`, and `/VER` queries. All edits use a transient snapshot and publish
only a complete validated candidate. File operations restore the caller's user.

A set is exactly three 128-byte CP/M records. Bytes 0–7 are `BNDR`, format 1,
capacity 32, name width 8, entry width 10. Bytes 8–63 are zero. Bytes 64–383 are
the table. Load verifies the header, reserved bytes, every entry, uniqueness,
and exact logical EOF before publishing. Unsupported/incomplete/invalid sets
leave the live namespace unchanged. Save creates a new file and refuses to
overwrite an existing one; failed writes remove the incomplete new file.

## Qualification boundary

Focused execution checks cover management, limits, bad names, saved-set
validation, returning disk errors, table relocation, prompts, shell translation,
command qualification, quoted text, overflow, absence and PATH capture. Existing
CCP/PATH regression checks and the Model 4 disk reloader tests remain required.
The production RSX-manager fixture additionally covers first/marginal loading,
offline reconstruction, unload/reload and allocation recovery.

The same source is assembled and exercised under the default Model 4 layout,
checked cpmsim-fullram and checked Model II-fullram profiles. This is component
and execution-fixture qualification, not a claim that new 1.2 release media or
real hardware have been qualified. Evidence is under
[NDR implementation checks](evidence/ndr-1.2/README.md).
