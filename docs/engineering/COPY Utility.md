# COPY Utility: Incremental Implementation and Qualification

## Agreed common functionality

The CPX and transient COPY should provide the ordinary copy operations,
including wildcard/multiple-file copying, explicit overwrite control and
attribute preservation. Implement and qualify these in bounded increments.
Richer transient-only syntax and any CPX-to-transient handoff contract remain
separate design work; no handoff ABI is introduced by this increment.

## Current assessment — 2026-10-08

The implementation is shared in `src/cpx/rcp.mac`; `build_rcp_transients.py`
builds COPY.COM from the same command body. Both source/destination and
`destination:=source` forms support explicit drive/user qualifiers and copy
one exact filename. Existing destinations and exact self-copies are refused.
R/O, SYS and ARC attributes are already copied after a successful destination
close. Prior native qualification covers all eight attribute combinations in
CPX and transient profiles. MOVE uses the same engine and erases its source
only after successful copy/close and attribute handling.

Remaining implementation includes source wildcards/multiple files and an
explicit overwrite option. Destination DU shorthand is implemented below. These are not
claimed complete by the parser correction below. Destination wildcard renaming,
concatenation, device transfers, transformations and the handoff proposal need
separate contracts before implementation.

## Exact-filespec correction — passed targeted checks 2026-10-08

The existing FCB parser silently truncated names longer than eight characters
and extensions longer than three. Thus an overlong source could select an
existing shorter filename, or an overlong destination could create a file
with a different name. COPY/MOVE now validate exact operands before FCB parsing
or file operations. Reject empty names, excessive field lengths, multiple
dots, embedded spaces/control bytes, wildcard operands and embedded colon or
assignment delimiters. A name without an extension, including a trailing dot,
remains valid. DU selection is restored on rejection.

`tools/test_copy_filespec.py` executes the actual validator in both relocated
CPX and transient builds at exact 8.3 boundaries and malformed inputs.
`tools/test_z80pack_copy_filespec.py --report <new-directory>` exercises five
invalid commands per profile, requiring the existing usage diagnostic and
byte-for-byte preservation of all disks. Maximum-width valid source names
still copy their exact payload. CPX cases remove COPY.COM, preventing fallback
from concealing a CPX failure; transient cases unload RCP. The report preserves
binaries, transcripts, runtime media and hash evidence.

Shared code grows from 3,047 to 3,127 bytes (+80). The rounded RCP allocation
rises from 3,072 to 3,328 bytes (+256), affecting available transient memory
while loaded. COPY.COM and the other currently untrimmed RCP-derived transients
also become 3,127 bytes. This is a utility/CPX change; resident BIOS/BDOS code
and their fixed capacities are unchanged. Model 4 qualification and broader
COPY feature qualification remain open.

## Destination DU shorthand — passed targeted checks 2026-10-08

An exact source may be copied to a destination drive/user alone, retaining its
filename: `COPY B1:SOURCE.DAT B3:`. Drive-only destinations use the caller's
current user; combined destinations support users through 31. A missing
source filename is still invalid. Exact self-copy and existing-destination
checks apply after inheriting the name, before destructive work.

The shared parser clears the destination FCB normally and copies only the
source's eleven filename bytes when the destination is just a DU. Effective
source/destination drive and user remain separately captured. Existing data
copying, close ordering and final attribute preservation are unchanged.
The assignment form retains its existing `:=` separator: a DU-only destination
can be written `COPY B4::=B1:SOURCE.DAT` (destination `B4:` plus separator `:=`).
The ordinary source-first form is the simpler spelling. This does not change
the existing meaning of an extensionless destination such as `B:=source`.

`tools/test_z80pack_copy_du.py --report <new-directory>` checks both profiles:
CPX cases have no COPY.COM; transient cases unload RCP. Native transfers to
users 0/3/4/31 retain exact payload and all three source attributes, preserve
source metadata, and return to A0. Self-copy, existing destination, absent
source name and out-of-range destination user all preserve the complete disk
set. Exact-filespec boundary checks and the native malformed-name campaign
remain passing after this parser change.

Shared code grows from 3,127 to 3,153 bytes (+26); RCP allocation remains
3,328 bytes. BIOS/BDOS code is unchanged. Wildcard/multiple-file support,
explicit overwrite control and final two-platform COPY qualification remain.
Handoff remains separate until the agreed common resident COPY work is done.
