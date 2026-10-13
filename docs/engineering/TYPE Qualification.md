# TYPE / TYPE.COM qualification — 2026-10-13

Resident TYPE is implemented in RCP Build 007. TYPE.COM 1.0 Build 004 is
4,383 bytes, with SHA-256
`5ff8be0132f1c03809f007f7d98f468951da89818446fb7ce26806a042c1b7b1`.
Native ZSM4/LINK and cross assembly match byte-for-byte.

The [TYPE specification](TYPE%20Specification.md) defines the command contract.
This qualification covers the current 80-column, 24-row cpmsim and Model 4
consoles. There is no geometry-query facility in the current console ABI;
provider/configuration changes introducing other dimensions require requalification.

## Executable fixture coverage

- `test_resident_type.py`: relocated resident carriers, selectors, protected
  text, unique physical extents, EOF, errors, paging and caller restoration.
- `test_type_streaming.py`: standalone shared selection, all eight attribute
  combinations, banners, empty/multi-extent data, raw EOF before transformations,
  `/7`, `/T`, `/CTL`, record-boundary CR/LF, open/read failures and pure `/VER`.
- `test_type_paging.py`: every page-key alias, first/final page bounds,
  screen-width spillover, tabs/control expansion, exact-full-page EOF, changed
  source reconstruction, cross-file anchors and unrestricted replay history.
- `test_type_files.py`: current/previous/next boundaries, partial backward
  movement, final cross-file EOF, empty files, DU order and 32-bit row arithmetic.
- `test_type_limits.py`: checked 16-bit ordinal overflow before file opening;
  reserved stack guard and observed 30/128-byte stack use in the fixture.
- `test_utility_versions.py`: resident/transient identity, invalid `/VER`
  combinations and no-work query behavior.

All pass. Faults such as open/read failures are injected in the executable
fixture; physical media campaigns do not simulate failing hardware. Disk images
and source files remain unchanged by the command. Concurrent external changes
are not snapshotted; replay may show changed contents.

## Real platform campaigns

`test_resident_type_media.py` qualifies resident streaming and cpmsim forward
paging without TYPE.COM installed. Its `--transient` mode covers streaming
transformations and invalid syntax with the standalone utility.

`test_type_paging_media.py` and `test_model4_type_paging.py` qualify page-key
handling, reconstruction, final EOF and controlled quit.

`test_type_file_media.py --platform z80pack|model4` qualifies boundary jumps,
empty files, final cross-file pages and cooked BDOS tabs. Model 4 screen captures
verify banners on row zero and an initial raw TAB occupying eight columns after
clear/home. Complete source disk images compare byte-for-byte after navigation.
The harness waits for keyboard readiness after WBOOT before typing a second
command; no production keyboard change is included.

Tools retain invocation/transcript or screen captures, disposable media and
executable hashes. Pass a fresh `--report` directory, and for cpmsim supply
`--image-dir` pointing to a qualified `build/z80pack` runtime. Model 4 tools use
the existing LaunchServices wrapper. Native assembly uses
`build_native_type.py` with explicit simulator, boot/template disk and ZSM4/LINK
paths where local defaults differ.

## Ordinary output cancellation

`test_type_output_abort.py` separately qualifies real BDOS Ctrl-S/Ctrl-C for
resident and transient ordinary output. Ctrl-C triggers the normal WBOOT before
TYPE's cleanup can run. It retains the active displayed-file DU (A3 in the
campaign), while source disk contents and attributes remain unchanged. This is
the specified normal-BDOS behavior outside paged input, not controlled quit.

Normal completion and Ctrl-Q at a transient page prompt restore the caller DU.
Resident Ctrl-C at its forward-paging prompt also restores the caller. Transient
Ctrl-C at a page prompt is Next Page and does not warm boot.

## Memory and remaining integration

TYPE.COM is standalone and does not require RCP. Its added state is transient;
permanent BDOS/BIOS allocation and the unloaded 53K TPA remain unchanged.
Paged selection is limited to 65,535 unique files, with overflow rejected before
file opening. Page history has no fixed cache limit and uses 32-bit row anchors.
Backward reconstruction may be slow on floppy media.

TYPE implementation/qualification is complete for the current platforms.
Before automatic resident-to-transient handoff, perform the separately required
CCP/RCP/protected-state memory audit. Automatic handoff is not implemented by
this work. Final distribution/release qualification remains a system-wide task.
