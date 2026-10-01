# Engineering Specification 191: Native CONFIG FDB Selection

## Result

CONFIG now keeps the validated binary catalogue in its transient workspace and
uses it for the complete interactive format-selection path. The utility no
longer calls the legacy text loader at startup. Format pages print the FDB's
fixed display descriptions, a selected entry is decoded through the native
binding constructor, and the resulting binding follows the existing physical-
compatibility and BIOS submission transaction.

The logical-drive list also identifies current bindings through the FDB. It
constructs each supported descriptor's normalized binding and compares the 63
format bytes with the live binding, preserving the existing `Custom` and
`Undefined disk drive` results. Because FDB mixed-sector and cylinder-track
extensions already construct their normalized live representations, this path
does not need the legacy name-dependent SUPER normalization fallback.

Unsupported required extensions remain visible in the catalogue but refuse
selection through the established `Invalid or unsupported setting` path. No
binding is partially submitted.

CONFIG is 11,554 bytes, leaving 4,062 bytes below its 15,616-byte transient
ceiling. This change does not affect resident memory or the 53 KiB TPA floor.

## Focused evidence

`tools/test_config_fdb_runtime.py` boots a fresh z80pack release image under
cpmsim, enters CONFIG's disk-format menu, requires the canonical FDB description
`Access Matrix 40T SS`, selects it for B:, attaches it to physical drive 1, and
requires CONFIG's successful live-change message before exiting normally.

The native reader test continues to prove exact binding construction for all
107 admitted descriptors. The disposable trs80gp utility harness was updated
to carry `DISK.FDB` and expect canonical FDB ordering. Two bounded invocations
terminated before producing their first captured screen. The preserved macOS
report `trs80gp-2026-10-01-235758.ips` records launch at 23:57:58.4982 and an
abort at 23:57:58.6325, approximately 0.13 seconds later. Its faulting
main-thread stack passes through `_RegisterApplication`, `GetCurrentProcess`,
`_NSInitializeAppContext`, and `NSApplicationMain`. The emulator therefore
failed during macOS application registration, before emulation or BetterCP/M
execution. This is a host-emulator startup failure rather than a CONFIG/FDB
result. Functional TRS-80 qualification remains for the bounded cross-platform
closure step.

## Remaining Step 4 boundary

Legacy parsing routines remain in the shared utility include even though CONFIG
no longer calls them; DUP and SYSGEN still use the shared source. Release media
also still carry `DISK.FDF`. The next increment must separate or conditionally
omit CONFIG's dead text-reader code, stop packaging the runtime text catalogue,
and complete available cross-platform and negative catalogue qualification.
