# Engineering Specification 146: Stage 3 Carrier Coordinator

## Status

This increment implements and qualifies the first end-to-end Function 202
transaction coordinator slice. `R3COORD.RSX` loads and normalizes one requested
carrier without changing the active reconstruction table, live RSX images,
published chain, generation, or TPA ceiling. Production Function 202 dispatch
does not select it yet.

## Request and workspace

The coordinator accepts only a version-2 LOAD request. It takes the filename
stem and caller-owned workspace bounds directly from the public 18-byte
Function 202 request. The low bound must be at or above `0103h`, the range must
be nonempty, and every 512-byte stream transfer must end at or below the high
exclusive bound.

The named BRSX carrier begins at the low bound. The coordinator reads its fixed
header, derives the exact carrier length from the v2 metadata envelope, and
loads only the complete 512-byte transfers needed
to cover that length. It reserves the next 26 bytes for normalized facts and
20 bytes for the maximum two callable descriptors. Arithmetic overflow,
insufficient workspace, invalid framing, and a short stream all fail before
the preparation result becomes public.

## Validation phases

The coordinator loads `R3CARR.RSX` and `R3META.RSX` successively into the
shared CONFIG slot. The first validates and publishes fixed carrier facts; the
second validates metadata and completes the normalized record. Only after both
phases report completion does the coordinator copy the primary numeric service
to the public request and return the facts address in HL.

The coordinator occupies the one-kilobyte RSX manager slot. Its private file is
padded through byte 1020 and restores the fixed BDOS gateway in the final three
bytes, so CALL 5 remains valid while this phase is resident.

## Qualification

The focused Z80 test streams the real `STATEFUL.RSX` and converted stateless
`HELLO.RSX` v2 carriers through named file stubs, then checks the normalized
facts and returned service. It rejects a corrupted payload, insufficient
workspace, and unsupported UNLOAD operation. A sentinel-covered live RSX range
remains byte-for-byte unchanged in every case.

Both platform image builders install `R3COORD.RSX`. The next increment extends
the coordinator from one-carrier normalization into prospective-profile
construction and commit-ready snapshot preparation; selection from production
Function 202 remains a later, separately qualified handoff.
