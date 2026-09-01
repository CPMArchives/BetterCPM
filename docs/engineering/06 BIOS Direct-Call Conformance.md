# Engineering Specification 06: BIOS Direct-Call Conformance

Status: Implemented and verified  
Date: 2026-09-01

## Result

The assembled 131-byte BIOS artifact is now executed through its published
17-entry jump table by a deterministic direct-call fixture. Verification no
longer stops at table shape or source inspection.

## Execution method

`tools/test_bios.py` loads `bios.bin` at its provisional `F000h` origin into
an isolated 64K address space and runs the actual Z80 instructions. Its
instruction runner deliberately implements only opcodes emitted by this small
fixture; encountering anything else fails the test. This is a bounded test
instrument, not a general Z80 emulator.

The platform-console stubs are test instrumentation. The fixture temporarily
changes their returned values in the isolated memory image so both status and
parity paths can be observed without modifying the built artifact.

## Verified behavior

- all 17 vector entries are three-byte `JP` instructions with in-image targets;
- incomplete `BOOT` and `WBOOT` are visibly non-returning stop loops;
- empty `CONST` returns `00h`;
- ready `CONST` normalizes a nonzero platform result to `FFh`;
- `CONIN` turns a fixture value of `C1h` into zero-parity `41h`;
- `CONOUT` transports the byte in C unchanged;
- an unassigned `READER` returns Ctrl-Z;
- `SETTRK`, `SETSEC`, and `SETDMA` persist their 16-bit BC values;
- `HOME` replaces the selected track with zero;
- `SELDSK` returns no DPH while drives remain unimplemented;
- `READ` and `WRITE` return failure rather than false success;
- the unassigned `LISTST` fixture reports not-ready;
- null-XLT `SECTRAN` returns BC unchanged in HL; and
- table-XLT `SECTRAN` returns the indexed physical-sector identifier.

The direct calls intentionally observe raw BIOS behavior. They do not add BDOS
echo, formatting, console-control, pending-input, or DMA policy.

## Verification

```sh
python3 tools/build_bios.py
python3 tools/test_bios.py
python3 tools/build_native_bios.py
```

Expected execution result:

```text
executed 17 BIOS-vector contracts from F000h binary
character transport, disk state, failure paths, and SECTRAN passed
```

The native and cross-built BIOS artifacts remain byte-identical.

## Next increment

Replace the build-only console stubs with a resident TRS-80 Model 4 platform
module sharing the already verified matrix-keyboard and video-console logic.
Test the resulting BIOS console entries in `trs80gp` without yet adding the
BIOS artifact to the boot loader's loaded system image.
