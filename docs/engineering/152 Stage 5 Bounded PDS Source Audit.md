# 152 — Stage 5 Bounded PDS Source Audit

Date: 2026-09-25
Status: accepted Stage 5 evidence; no source-code change

## Result

The emitted 1.0 system already implements the bounded PDS needed by the reduced
release scope. It has one owner, command history, and needs no new allocator.
Architecture Specifications 18 and 29 now make that implementation the frozen
1.0 contract rather than a provisional step toward the broad allocator once
planned for 1.0.

## Source evidence

`src/system/layout.inc` fixes `LY_HIST` at `D504h`, `LY_SYS` at `D5C4h`, and the
exclusive TPA ceiling `LY_TPA` at `D501h`. `LY_PDSS` consequently evaluates to
`00C0h`, or 192 bytes. The PDS bridge publishes that region through the
version-1 Extension Control Block at `LY_SYS+80h`.

`src/ccp/ccp.mac` assigns ten bytes to the history header and owner-private
working state and uses the remaining 182 bytes for packed records:

| Offset | Bytes | Meaning |
| ---: | ---: | --- |
| 0 | 2 | `BH` signature |
| 2 | 1 | structure version 1 |
| 3 | 1 | record count |
| 4 | 2 | used-byte count |
| 6 | 4 | history-private working state |
| 10 | 182 | packed command records |

The same source validates the signature and version on CCP initialization and
resets an invalid object. WBOOT and command-environment reconstruction preserve
the allocation. `src/system/gateway.mac` clears the RSX profile on cold entry
but does not currently force a valid old history object to empty before the CCP
validates it. An unconditional cold-boot history reset remains a focused 1.0
implementation task.

The source audit also confirms that the RSX and CPX profiles, disk/configuration
state, service registry, clock-provider state, stacks and workspaces have other
natural owners. None requires an allocation in the 1.0 PDS.

## Memory proof

The exclusive TPA ceiling of `D501h` exposes 54,273 addressable bytes from
`0100h`. CP/M loads complete 128-byte records, so the largest image is 54,272
bytes: exactly 53 KiB. The fixed 192-byte PDS therefore satisfies the release
floor without a new memory trade-off.

## Focused verification

The repository builders and the existing PDS descriptor test were run against
this unchanged layout:

```text
python3 tools/build_fileloader.py
python3 tools/build_system.py
python3 tools/test_pds_descriptor.py
```

The descriptor test confirmed PDS ABI 1 publishes the unchanged 192-byte static
layout. No binary or assembly source was changed by Stage 5.

## Superseded planning assumptions

Engineering Specifications 130 and 131 remain useful measurements and history,
but their proposed 1–1.5 KiB base allocator and migration of fixed subsystem
state into it are not the 1.0 architecture. That broader work is deferred to a
later measured design. Physical relocation for ROM separation does not by
itself change semantic ownership.
