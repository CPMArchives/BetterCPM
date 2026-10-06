# Optional 104/105 clock frontends — candidate implementation

## Status and boundary

The first bounded increment implements `T104C3.RSX` and `T104Z8.RSX` as
BRSX-v2 candidates. Neither is admitted to the 1.0 inventory, installed in a
release image, or added to the default profile. BIOS and BDOS are unchanged.
The governing contract is Architecture Specification 22, section 7.

These modules supply only historical clock calls. They do not claim broader
CP/M 3, DOS+ or Z80DOS compatibility.

## Implemented contract

Both intercept Function 104 SET and Function 105 GET. Every claimed call
resolves native TIME through Function 182, using private request storage.
No provider entry point survives the call. Unclaimed functions chain unchanged.

- T104C3 copies exactly four bytes. GET returns BCD seconds in A; SET supplies
  zero seconds to the native five-byte TIME request.
- T104Z8 copies five bytes. Successful GET and SET return A=0.
- Both return HL=0 on success. A claimed failure returns A=FEh and HL=00FEh;
  failed GET leaves caller output unchanged. This uses the existing P2DOS
  minimal failure convention, pending historical-client qualification.

The implementation shares source in `src/rsx/clock104.inc`, selected by two
8.3-compatible wrapper sources. Private request buffers are mutable RSX state;
code and lookup constants require no runtime patching beyond normal relocation
and chain publication.

## Measurements and evidence

Reproduce the candidate build and CPU-level checks with:

```sh
python3 tools/build_clock104_rsx.py
python3 tools/test_clock104_rsx.py
```

| Candidate | Resident bytes | Allocation | Relocations | Carrier bytes |
| --- | ---: | ---: | ---: | ---: |
| T104C3 | 149 | 256 | 14 | 677 |
| T104Z8 | 140 | 256 | 12 | 668 |

Linked code SHA-256:

- T104C3: `4b6922f5db7108fbae897dbb346b0576d4a41b8cfffd8715fb6065c7e1dc6908`
- T104Z8: `37c5917a951ef93cd888d8893881be9abb390c489f1f77465fca44d0d1102db6`

Each build assembles at 8000h and 8101h and derives relocation offsets from the
resulting binaries. The contract test executes the actual carrier code in the
existing Z80 test interpreter against controlled registry/provider fixtures.
It verifies four/five-byte guards, seconds return/reset, native operation
selection, success and unsupported SET, missing service, provider replacement,
21 partial-output failure cases per candidate, caller input preservation,
DE/IX/IY and stack preservation, and chaining of Functions 12, 200 and 201.
These checks are not a substitute for historical clients or native RSX loading.

A first assembly exposed an eight-significant-character label collision.
Shortening the shared prefix fixed the collision; both alternate builds and
CPU contract tests then passed. This was a source-label issue, not an OS defect.

## Remaining admission gates

1. Qualify native mutual-exclusion behavior in both load orders and applicable
   saved/cold profile paths. The shared LOAD coordinator now rejects conflicting
   exact stems before file I/O; the CPU-level evidence is recorded below.
2. Qualify real native load/unload, provider disappearance/replacement, WBOOT,
   and coexistence with P2DOS through the applicable platform paths.
3. Run the agreed four-byte SCTIME and five-byte DATE501 historical clients;
   verify exact ABI expectations and failure behavior independently.
4. Record final sizes and default-profile TPA, then make the explicit admission
   or deferral decision. Any required loader correction must stay narrowly
   bounded; these optional candidates do not justify architectural expansion.

Item 6 remains open solely for this optional admission decision. No release
requirement is added by this candidate implementation.

## Shared LOAD exclusion increment

`R3COORD` now compares the exact canonical eight-byte candidate name against
T104C3 and T104Z8. For either candidate, it scans the bounded persistent active
name list and rejects the opposite stem before opening the candidate file.
Function 177's shared LOAD path owns this check, so calling the API directly
does not bypass it. No general dependency tracking is introduced. Normal
same-name duplicate validation remains the prospective builder's job.

The prospective builder measured 1,012 bytes before this change, with no spare
capacity. The load coordinator measured 707 bytes and now measures 808 bytes,
leaving 204 bytes in its 1,012-byte execution slot. Its released overlay remains
1,024 bytes. No permanent resident allocation or default TPA changes.

Reproduce the bounded checks:

```sh
python3 tools/build_rsx_runtime_overlays.py
python3 tools/test_clock104_exclusion.py
python3 tools/test_rsxcoordinator.py
python3 tools/test_rsx_runtime_overlays.py
python3 tools/test_clock104_rsx.py
```

All pass. The new exclusion test exercises 45 cases: both directions, every
position in each one-to-four-entry list, empty/same-name/unrelated profiles,
nonexact names and invalid clock-profile counts. It also runs the production
coordinator entry for both conflicting LOAD orders, asserting FFh, no file open,
no candidate-length publication and unchanged live profile/memory.

This proves the shared coordinator check, not complete emulator qualification.
Native lifecycle, reconstruction/cold behavior and historical clients remain
admission gates. Neither frontend is added to distribution media by this change.
