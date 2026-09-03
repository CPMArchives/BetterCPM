# Engineering Specification 123: Unified BDOS Service Inventory

Status: replacement design inventory; implementation pending

## Purpose

BetterCP/M's current public BDOS dispatcher and filesystem service component
occupy 7,369 bytes together: 2,624 bytes in `dispatch.mac` and 4,745 bytes in
`directory.mac`. This is not justified by additional public functionality.
The CP/M 2.2 BDOS supplies the same base console, disk, directory, extent, and
record operations in approximately 3.5K.

The replacement BDOS shall therefore be a single state engine. Public function
handlers are policy adapters; they must not own private implementations of
directory traversal, FCB decoding, extent arithmetic, allocation, or physical
record transfer.

`metadata/bdos-service-inventory.tsv` is the machine-readable caller matrix
for this specification.

## Public compatibility surface

The unified engine must support the following filesystem and disk-state calls.
Functions 0 through 12 remain the character/console portion of the same BDOS,
not a separately linked filesystem layer.

| Function | Operation | Required shared services |
|---:|---|---|
| 13 | Reset Disk System | drive context, disk state |
| 14 | Select Disk | drive context |
| 15 | Open File | FCB view, directory iterator, extent service |
| 16 | Close File | FCB view, directory iterator, directory mutation, allocation |
| 17 | Search First | FCB view, directory iterator, cache transfer |
| 18 | Search Next | directory iterator, cache transfer |
| 19 | Delete File | FCB view, directory iterator, directory mutation, allocation |
| 20 | Read Sequential | FCB view, extent service, record mapping, transfer |
| 21 | Write Sequential | FCB view, extent service, allocation, record mapping, transfer |
| 22 | Make File | FCB view, directory iterator, directory mutation |
| 23 | Rename File | FCB view, directory iterator, directory mutation |
| 24 | Return Login Vector | disk state |
| 25 | Return Current Disk | disk state |
| 26 | Set DMA Address | call state |
| 27 | Get Allocation Address | drive context |
| 28 | Write Protect Disk | disk state |
| 29 | Return Read-Only Vector | disk state |
| 30 | Set File Attributes | FCB view, directory iterator, directory mutation |
| 31 | Get DPB Address | drive context |
| 32 | Get/Set User Code | call state |
| 33 | Read Random | FCB view, extent service, record mapping, transfer |
| 34 | Write Random | FCB view, extent service, allocation, record mapping, transfer |
| 35 | Compute File Size | FCB view, directory iterator, extent arithmetic |
| 36 | Set Random Record | FCB view, extent arithmetic |
| 37 | Reset Drive | drive context, disk state |
| 38, 39 | Reserved | common return |
| 40 | Write Random with Zero Fill | function 34 path plus block initialization |

## Universal services

### U01 — Public call frame

Input is the CP/M register contract (`C=function`, `DE=parameter`). It records
only state that must survive nested BIOS calls, switches to the private stack,
dispatches through the standard-function table, and returns CP/M aliases
`A=L` and `B=H` where required.

This service owns the private stack and common return/error exits. No public
handler may create a second call-frame convention.

### U02 — Drive resolver and context

Resolve FCB drive zero as the current drive, validate explicit drives, select
through BIOS `SELDSK`, and cache the active DPH/DPB fields. Reuse a valid
context until reset, media change, or selection of another drive invalidates
it.

The context contains only the currently selected drive's derived geometry.
Per-drive DPH, checksum, and allocation workspaces remain BIOS/system data;
the BDOS must not copy them into operation-specific structures.

### U03 — Disk-state manager

Own current drive, current user, DMA address, login vector, software read-only
vector, and selection restoration. It implements functions 13, 14, 24–29,
32, and 37 and supplies the state used by file calls.

### U04 — FCB view

Provide common accessors for:

- default or explicit drive;
- masked 8.3 filename and attribute bits;
- `EX`, `S1`, `S2`, and `RC`;
- sequential record `CR`;
- random record `R0..R2`;
- 8-bit or 16-bit allocation entries selected by the DPB.

The view operates on the caller's FCB. It does not copy the complete FCB into
a permanent private record. Temporary decoded extent/record values share one
scratch area and are recomputed when cheaper than retaining duplicates.

### U05 — Directory iterator

One iterator traverses physical directory records and their four entries. Its
configuration selects:

- exact, wildcard, or free-entry name matching;
- one user or the CP/M all-user search form;
- one logical extent or all extents;
- start, continuation, or restart position.

It returns the directory slot, entry address, and containing sector state.
Search First/Next preserve their required continuation fields; all other
operations use the same iterator without preserving a private scan engine.

The current separate loops in Size, Attributes, Rename, Delete, Make, Search,
Find, Open, and allocation reconstruction are replacement targets, not
services to retain.

### U06 — Directory cache and mutation

Own exactly one 128-byte directory-sector buffer. Load, expose, mark dirty,
and write the current sector. Creation, deletion, rename, attribute update,
extent close, and allocation-map reconstruction all operate on this cache.

Read-only checks occur before the first mutation. CP/M-compatible within-call
failure behavior is required; a general transaction journal or crash-atomic
filesystem is not part of the CP/M 2.2 contract. Any retained rollback state
must be justified by a named compatibility test and share the common scratch
area.

### U07 — Allocation service

Rebuild, query, set, and clear the active allocation vector; reserve directory
blocks from `AL0/AL1`; find a free block; and read or write 8-bit/16-bit FCB
allocation entries. All allocating operations use this one implementation.

The service must distinguish "directory full", "data allocation exhausted",
and physical I/O failure where CP/M exposes different results.

### U08 — Extent service

Convert `EX/S2`, `EXM`, `RC`, and `CR` into a logical extent and record. Find,
activate, create, advance, and close an extent while maintaining the caller's
FCB exactly as CP/M requires.

Open, Close, sequential I/O, random I/O, and Compute File Size share this
arithmetic. There must be no separate random-versus-sequential extent model.

### U09 — Record mapper and transfer

Map a logical 128-byte record through allocation block, `BSH/BLM`, `SPT`,
reserved-track offset, and `SECTRAN`, then call BIOS `SETTRK`, `SETSEC`,
`SETDMA`, and `READ` or `WRITE`.

Sequential and random calls share the mapper. Function 40 adds block
initialization before publishing a newly allocated block; it does not own a
second write engine.

### U10 — Result and recovery mapper

Translate internal outcomes to the precise CP/M return family, restore any
temporarily selected drive and DMA state, and terminate through U01. Internal
status may distinguish physical failure from ordinary EOF/no-match even when
the public CP/M result aliases them.

## State inventory

### Protected persistent state

Only state required between independent BDOS calls belongs here:

- current drive and user;
- current DMA address;
- login and read-only vectors;
- active drive context identity and pointers;
- Search First/Next continuation;
- console column and printer-echo state;
- installed-RSX chain head and gateway metadata (owned at the system edge).

### Per-call scratch

All other filesystem temporaries must overlay one scratch region, subject to
the actual nested call graph. This includes FCB pointers, decoded records,
match configuration, iterator counters, dirty flags, candidate allocation
blocks, and old-entry copies needed during one mutation.

The current operation-prefixed families (`DIR_Q*`, `DIR_Z*`, `DIR_A*`,
`DIR_N*`, `DIR_D*`, `DIR_M*`, `DIR_W*`, `DIR_R*`, `DIR_C*`, and `DIR_X*`)
are evidence of incremental construction. They are not separate persistent
state classes in the replacement.

### External workspaces

The active drive's DPH/DPB, CSV, and ALV remain protected system workspaces.
The physical-sector buffer belongs below the BIOS interface. A temporary CPX
or RSX module buffer is not BDOS filesystem state and must not be charged to
the minimal resident BDOS.

## Size budget

| Item | Maximum release target |
|---|---:|
| Complete standard BDOS, functions 0–40 | 3,584 bytes |
| Preferred Z80 implementation | 3,072–3,328 bytes |
| Private stack and per-call scratch | included above |
| DPH/DPB and per-drive CSV/ALV | reported separately as system workspace |
| CPX/RSX installation machinery | excluded; temporary overlay |

The build must report code, persistent data, per-call scratch, and external
workspace independently. Passing functional tests does not waive this budget.

## Replacement order

1. Implement U01–U04 and the disk-state calls in the new component.
2. Implement U05/U06 and move Search, Open, Make, Delete, Rename, Attributes,
   and Size onto the shared iterator.
3. Implement U07–U09 and move sequential/random I/O onto the shared path.
4. Implement U10 and run the binary-level function suite against both cores.
5. Switch the system build only after all functions pass and the replacement
   meets the 3.5K hard ceiling.
6. Remove `directory.mac` and the private D600h service-vector ABI.

