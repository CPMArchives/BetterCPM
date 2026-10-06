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

1. Enforce mutual exclusion in both load orders, including direct profile
   construction and saved/cold profiles. The existing loader does not yet
   supply this guarantee: do not load both candidates together.
2. Qualify real native load/unload, provider disappearance/replacement, WBOOT,
   and coexistence with P2DOS through the applicable platform paths.
3. Run the agreed four-byte SCTIME and five-byte DATE501 historical clients;
   verify exact ABI expectations and failure behavior independently.
4. Record final sizes and default-profile TPA, then make the explicit admission
   or deferral decision. Any required loader correction must stay narrowly
   bounded; these optional candidates do not justify architectural expansion.

Item 6 remains open solely for this optional admission decision. No release
requirement is added by this candidate implementation.
