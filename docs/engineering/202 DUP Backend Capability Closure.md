# Engineering Specification 202: DUP Backend Capability Closure

## Result

The retained DUP qualification now exercises the supported and unsupported
backend boundaries on both BetterCP/M 1.0 platforms. The Model 4 matrix uses
private DMK images and covers ordinary and matching-format copies,
mixed-sector FDF copies, source CRC errors, destination write protection, and
interruption. Every case checks binding restoration, source and system-media
preservation, and return to the command environment. Successful copies also
compare the resulting physical-sector payloads and run DUP's check operation.

The z80pack matrix formats and verifies a complete uniform raw image. Its
mixed-sector case loads FDF.RSX, installs an MM SUPER binding, and proves that
the raw backend returns unsupported before changing any target byte. This is
the intended capability boundary: z80pack accepts the normalized binding for
ordinary access but its raw formatter does not implement mixed physical-sector
write-track streams.

## Qualification-fixture corrections

The Model 4 matrix had retained provisional Function 207 in its synthetic
binding probe after disk configuration moved to production Function 181. Its
mixed-sector medium also installed FDF.RSX without the fifteen Stage-3
transaction overlays needed by Function 177 to construct an RSX profile. The
released system images already contain those overlays. Updating the fixture
restores the production call path without changing DUP or any resident code.

## Evidence

The following cases pass from current source:

- `test_dup_operations.py copy`
- `test_dup_operations.py same`
- `test_dup_operations.py mixed`
- `test_dup_operations.py bad`
- `test_dup_operations.py protected`
- `test_dup_operations.py abort`
- `test_z80pack_dup_format.py`
- `test_z80pack_dup_format.py --unsupported`

The z80pack system-image builder also completes with the 53 KiB TPA and ROM/RAM
layout gates intact. DUP backend-capability closure is therefore complete.
Native installation and final two-platform release qualification remain the
last Item 5 deliverable.
