# Catalogue to runtime drive bindings

CONFIG's menu and named command-line assignment, and FDB's editor Apply action,
convert a temporary cylinder-unit binding to surface-track units before asking
BIOS to validate and commit it. Name lookup compares the corresponding runtime representation while retaining
recognition of an unchanged bootstrap cylinder binding. An altered allocation
record still displays Custom. The catalogue descriptor and working editor
retain their original cylinder semantics. BIOS capability checks are unchanged.

A representable two-sided, alternating, forward, default-ID cylinder definition
uses half its original SPT and twice its original OFF at runtime. DSM, allocation
parameters, physical selector, encoding, inversion and sector maps are unchanged.
The conversion rejects zero or odd SPT, OFF above 32767, single-sided cylinder
bindings and nondefault addressing topology before changing any binding bytes.
Surface-track definitions are unchanged, and repeating the conversion is safe.

For BCPM780 this yields SPT=40, OFF=4 and DSM=389, preserving the directory at
byte 20480 and the original allocation bounds and sector order. This resolves
CONFIG's prior rejection of the catalogue's bootstrap cylinder representation.

## Verification

- `tools/test_native_fdb_reader.py` checks all 108 original binding encodings,
  exact BCPM780 conversion, catalogue preservation, unchanged surface bindings,
  repeated application and bounded refusal cases.
- `tools/test_config_logical_cli.py` checks conversion at the named assignment
  boundary and that refusal leaves the active binding and reset state unchanged.
- `tools/test_fdb_editor.py` checks the shared editor Apply path, preserving the
  other drives and original catalogue. Existing capture/edit/apply tests remain.
- Session and round-trip tests cover recoverable replacement and native binary/
  text identity. Current FDB.COM is 19704 bytes; measured stack use is 34 bytes
  and the standard TPA margin remains 3328 bytes.
- `tools/qualify_fdb_session.py --config-read` imports and saves entry 109, then
  selects its display name through freshly built CONFIG and reads KNOWN.TXT
  through B:. It checks successful assignment, catalogue/source readback and
  byte identity of reserved system tracks. Run independently on both targets.

The CONFIG build helper accepts a qualified build root for generated resident
fingerprint and I/O configuration records; utility source always comes from the
current checkout. This allows isolated platform tests without replacing release
candidates. Full installation/cold-boot qualification is coordinated separately.
The 1.0 package freeze remains on hold.
