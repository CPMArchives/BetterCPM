# Engineering Specification 120: BRSX Version 1 Module Format

## Status

Implemented general module format and filename-driven runtime loader. The
dispatch and management interfaces remain provisional until initialization,
shutdown, bypass, dependency, and saved-profile contracts are completed.

## Purpose

`BRSX` version 1 replaces the single-module `BRX1` proof. An RSX is now an
ordinary `.RSX` file whose identity, ABI, allocation, entries, relocation
records, advertised services, and payload integrity can be checked without
hard-coded knowledge of the module.

## Carrier layout

The first 512-byte record is the header. Words are little-endian.

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | `BRSX` signature |
| 4 | 1 | format version: 1 |
| 5 | 1 | module class: 2 (RSX) |
| 6 | 1 | required ABI major: 1 |
| 7 | 1 | required ABI minor: 0 |
| 8 | 2 | flags; zero in version 1 |
| 10 | 2 | linked base |
| 12 | 2 | code size |
| 14 | 2 | protected, page-rounded allocation |
| 16 | 2 | dispatch-entry offset |
| 18 | 2 | initialization offset or `FFFFh` |
| 20 | 2 | shutdown offset or `FFFFh` |
| 22 | 2 | relocation-word count |
| 24 | 2 | header size: 512 |
| 26 | 2 | payload offset: 512 |
| 28 | 2 | relocation-table offset: 48 |
| 30 | 2 | service-metadata offset |
| 32 | 8 | space-padded module stem |
| 40 | 2 | module major and minor version bytes |
| 42 | 1 | advertised service count |
| 43 | 1 | reserved |
| 44 | 2 | additive checksum of the linked code bytes |
| 46 | 2 | primary service number, or `FFFFh` |
| 48 | 2n | relocation word offsets |

The linked code follows at offset 512. One byte per advertised service follows
at the metadata offset. No trailing data is permitted by the version-1 build
contract.

The runtime image begins with the existing four-byte chain header: the next
dispatch address at offset zero and this module's dispatch address at offset
two. Public entries in the carrier are offsets, not runtime addresses.

## Runtime management

The protected manager at `D100h` maintains up to four ordered active filename
stems in persistent protected memory. Experimental BDOS Function 202 accepts a
versioned request block for enumeration, load, unload, and query. `RSX.COM`
therefore accepts any syntactically valid stem, with an optional `.RSX`
suffix; it contains no table of known modules.

Before publishing a changed chain, the manager validates every named header.
It then allocates modules downward, reads their code, verifies the payload
checksum, applies relocation words, links the ordered dispatch chain, moves
the compatibility gateway, and publishes the new TPA ceiling. An ordinary
WBOOT preserves this protected chain and reconstructs the reclaimable CPXs and
CCP beneath it. Cold boot explicitly initializes the current active RSX table
from the presently empty saved profile.

## Physical proof

`HELLO.RSX` advertises Function 201 and deliberately reserves 1K. `ECHO.RSX`
advertises Function 203 and reserves one 256-byte page. `RSX2TST.COM` invokes
both services only through `CALL 0005h`.

The automated Model 4 test verifies empty enumeration, both filename forms,
ordered two-module chaining, WBOOT persistence, removal of the first module
while the second continues to work, and restoration of 47K after the last
unload. Both module code images and all RSX utilities are byte-identical when
assembled with native ZSM4/LINK and with the cross-build.

## Deferred production work

Version 1 reserves fields for initialization and shutdown but does not yet
invoke them. Dependency declarations, ordering constraints beyond explicit
load order, a core-BDOS bypass ABI, saved cold-boot profiles, transactional
rollback after physical read failure, and removal of the four-module
bring-up limit remain later milestones.
