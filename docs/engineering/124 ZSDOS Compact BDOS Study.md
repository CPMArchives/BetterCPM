# ZSDOS Compact BDOS Study

## Purpose

BetterCP/M's replacement BDOS reached 3,156 bytes before console functions,
complete Close semantics, and extent creation were finished.  ZSDOS 1.1 is a
particularly useful control implementation because it is a Z80-native,
CP/M 2.2-compatible enhanced BDOS constrained to the same fourteen-page
(3,584-byte) envelope.

This study concerns architecture and size discipline.  BetterCP/M must not
copy GPL implementation text into code unless the project deliberately adopts
compatible licensing.

## Reference implementation

The 1999 General Public Release contains `ZSDOS-GP.Z80`, `ZSDOS.LIB`, its
README, and GPLv2 license:

- <https://www.gaby.de/ftp/pub/cpm/znode51/specials/zsdossrc/zsdos.htm>
- `zsdos1.zip` from that directory

The distributed ZSDOS configuration sets `ZS`, command-line retype, unrolled
shifts, and user-path support true.  Its source reserves high state at offset
`0DF1H` and ends at `0E00H`.  Thus code and resident state together occupy
exactly fourteen pages.

## What ZSDOS fits in fourteen pages

The source dispatches the complete standard function range 0 through 40 and
also includes configurable enhancements.  The default ZSDOS build includes:

- console, reader, punch, list, direct-console, string, and buffered-console
  services;
- the complete CP/M 2.2 filesystem, including Close, extent rollover, missing
  extent creation, sequential/random I/O, and zero-filled random write;
- public files and a disk/user search path;
- enhanced buffered-console editing and type-ahead;
- retained read-only and login state;
- archive-attribute handling and improved error handling;
- external clock and timestamp vectors;
- additional error-mode, DMA-query, version, time, flag, and stamp functions.

The enhanced command processor, named-directory database, resident commands,
flow control, and most policy live outside the BDOS.  This matches
BetterCP/M's modular CCP/CPX/RSX direction.

## Structural techniques worth adopting

### One call frame and one live FCB pointer

ZSDOS moves the caller's FCB address into `IX` once at entry.  Filesystem
routines then use fixed indexed offsets.  BetterCP/M repeatedly stores an FCB
pointer, reloads it, adds offsets, and maintains several operation-specific
FCB globals.  A single call-frame FCB register can remove both code and state.

### One search state machine

ZSDOS's `SEARCH` accepts a comparison length and retains one directory cursor.
Open, Close, Make, Search First/Next, Rename, attributes, and path/public-file
logic configure or reuse it.  BetterCP/M has a shared iterator, but surrounds
it with repeated blocks that initialize eight separate iterator fields.
Replace those blocks with compact search-mode entry points or a packed mode
byte.

### One read/write pipeline

ZSDOS treats sequential and random operations as adapters around one active
FCB and one read/write flag.  `OPENEX` performs the common transition:

1. close a dirty current extent;
2. calculate the next extent;
3. search for it;
4. open it for reads or create it for writes.

The write path then allocates, optionally zero-fills, maps, transfers, and
updates record state.  BetterCP/M currently has shared mapping but has not yet
made extent transition the center of all four read/write functions.

### Make modified state explicit

ZSDOS keeps a modified flag in the FCB's S2 byte.  The allocator changes the
FCB map and clears the unmodified bit; Close validates and publishes the map.
This eliminates a separate large authentication copy.  BetterCP/M currently
reserves 31 bytes (`UB_CSAVE`) and considerable comparison/restoration code
while still rejecting allocator-produced map changes.

### Reuse the directory buffer

ZSDOS uses the directory buffer as the 128-byte zero-fill source and restores
the user's DMA afterward.  BetterCP/M Function 40 now independently arrived
at the same technique.  This is validated as the correct compact design.

### Prefer compact state over generalized state

ZSDOS holds one selected-drive DPB copy and a small set of flags/counters.
BetterCP/M's iterator alone uses numerous byte and word fields.  Generality is
valuable only when it deletes more client code than it costs; current size
suggests that threshold has not been met in several services.

### Make fall-through and return conventions do work

ZSDOS deliberately arranges related functions to share tails, fall through,
or push a common return path.  It also copies the byte argument to registers
once so simple functions can jump directly to BIOS entries.  BetterCP/M's
uniform public return convention is sound, but many internal paths still pay
for full setup and teardown independently.

## BetterCP/M size evidence

The 3,156-byte checkpoint ends at `CD54H`.  Approximate major spans from the
assembler listing are:

| Span | Bytes | Observation |
| --- | ---: | --- |
| entry/table/basic state | 302 | Functions 1--11 are still stubs |
| iterator and Open | 433 | repeated mode initialization is visible |
| Close | 137 | incomplete despite a 31-byte saved FCB image elsewhere |
| Make/Delete/Rename/Attr | 556 | four clients repeat validation/setup |
| Size/random conversion | 195 | candidates for common extent arithmetic |
| record I/O and mapping | 705 | still lacks common extent transition |
| allocation services | 288 | scan and bit operations are separate passes |
| directory cache/geometry | 203 | repeats divide/position arithmetic |
| resident variables/stack | 137 | includes 31-byte Close save and 48-byte stack |

These are diagnostic boundaries, not independent deletion targets.  The main
savings must come from changing data flow across boundaries.

## Refactoring direction

Before adding another BDOS feature:

1. Make one active FCB pointer part of the entry frame, preferably in `IX`.
2. Define one compact search initializer parameterized by length and mode.
3. Replace the provisional Close snapshot with an FCB modified-bit protocol
   and allocator-owned map updates.
4. Implement one `OPENEX`-style extent transition used by sequential and
   random reads/writes.
5. Merge record decode, allocation-slot selection, and physical mapping so
   they do not repeatedly walk the FCB and DPB.
6. Re-measure before implementing functions 1--11 and final error semantics.

The target is credible.  ZSDOS demonstrates that the fourteen-page limit can
include more capability than BetterCP/M's base BDOS requires.  Reaching it,
however, requires a compact state machine rather than further local trimming
of the present structure.

## Completed structural recovery checkpoint (2026-09-04)

After functions 0 through 40 were complete, the unified image occupied 3,503
bytes. The next pass treated 3,203 bytes as an acceptance ceiling and made the
following cross-cutting changes:

- copied the selected DPB into one packed drive context, eliminating repeated
  DPH/DPB traversal throughout Open, mapping, allocation, and directory I/O;
- packed directory record and slot state into one directory-entry cursor;
- made buffered console input use the active IX parameter frame instead of
  three duplicate pointer/length variables;
- removed redundant saved-parameter and Rename-FCB state;
- combined the 8-bit and 16-bit allocation-map scanners;
- replaced table-driven bit masks with compact rotate-based generation;
- simplified random-record decoding and removed an unused allocation-clear
  layer in favor of authoritative allocation reconstruction after Delete;
- separated stronger-than-CP/M Delete, Rename, Close, and validation policy
  from the mandatory base contract.

The resulting functions-0-through-40 image is 3,201 bytes, a reduction of 302
bytes from the completed 3,503-byte baseline and 383 bytes below the fourteen-
page hard ceiling. Native and cross assembly are byte-identical, and the
unified console, disk, directory, allocation, extent, and record-transfer test
suite passes.

Potential stronger filesystem policy is recorded separately in Architecture
Specification 16, `Optional Filesystem Safety RSX.txt`. That note is a design
option, not a commitment to ship the RSX.
