# Engineering Specification 204: Native Installation Qualification

Item 5's fifth deliverable is complete. The native build produces the nine
frozen system products and a verified 161-record SYSTEM.SYS. Installation and
cold boot are qualified under z80pack/cpmsim and trs80gp/Model 4, with populated
filesystem preservation. The separate accepted cpmsim reproducibility work
remains a release-environment requirement.

## Native build procedure

Mount the supplied MM 800K source/tool disk as B: and its companion work disk
as C:, configure both bindings, and run `SUBMIT B:BUILD`. Sources and tools
remain on B:. Generated INCLUDE files and every output reside on C:, which
has sufficient free blocks. BUILD.SUB links the CCP at BB00h, BC01h and BD37h,
renames the first image CCPBASE.BIN, and invokes RLMBUILD and SYSBUILD.

The qualification harness first runs the same published commands in three
bounded stages: resident modules and RESPACK; reloaders, overlays and CCP
relocation; then SYSBUILD. It then runs the complete SUBMIT command. Each
stage retains its transcript and media; a failed run is not silently removed.
The harness stops on failure rather than continuing installation with an
unverified package.

Both native procedures produce the host reference exactly: 20,608 bytes,
161 CP/M records, SHA-256
`d75ba33ef738a84cb9d389cb3439d9db58fc104b924ec0b50161c9f30a4098e2`.
SYSBUILD also reopens and compares every output record natively.

## Corrections required by qualification

- The CCP recognizes the command-tail NUL terminator used by SUBMIT, avoiding
  scanning beyond a short command into stale bytes.
- The native export expands the same generated physical-sector tables as the
  host build, including tables in the work disk's RELOAD.INC. It retains the
  shared layout INCLUDE instead of duplicating that text in every source.
- Reserved CCP stack, file-loader FCB, disk vectors and reconstruction handoff
  storage use explicit zero bytes so host and native assemblers emit identical
  images. Their sizes and addresses are unchanged.
- SYSBUILD's output FCB is the full 36 bytes. Its reopen reset previously
  cleared two bytes of the adjacent expected header because the FCB was only
  34 bytes; a targeted mismatch probe identified header offset zero.
- SYSBUILD uses measured component lengths to clear CP/M record padding while
  retaining every payload byte. Header expansion space is explicitly zero.
- RESPACK tests BC explicitly after decrementing it. DEC BC does not update
  Z; its old padding loop returned after clearing only the first byte.

These corrections preserve the resident memory map and 53 KiB default TPA
floor. They change no public selector or request-block ABI.

## Installation evidence

`test_z80pack_sysgen_install.py` installs from an existing bootable source onto
a populated compatible raw disk, checks every byte outside the reserved area,
extracts the preserved sentinel file, and cold boots the result.
`test_z80pack_sysgen_refusal.py` configures an actual MM DATA target and proves
incompatible bootstrap geometry is rejected before confirmation or writes.

`test_sysgen_cross_format.py` qualifies both `SYSGEN A: B:` and
`SYSGEN SYSTEM.SYS B:` on Model 4, checks filesystem preservation, and cold
boots both installed disks. `test_sysgen_install.py --package PATH` additionally
installs the actual native-built package onto a populated compatible Model 4
disk. It verifies the installed payload with the documented destination-binding
normalization, preserves the filesystem, and cold boots the result.

trs80gp runs through the established LaunchServices adapter with a writable
working directory and bounded timeouts. Emulator startup failures are not
silently converted into passing platform evidence.

## Retained checks

The native build disk test verifies the exact work INCLUDE set, generated
sector-table expansion, CCPBASE.BIN naming, full SYSBUILD output FCB, raw-sector
ordering, source archives and resident packing. The native execution harness
requires byte-identical packages; linker fill is never accepted as a payload
difference. The fresh z80pack build also passes the ROM ownership, initialization,
packing and address-relocation checks.

Exact binaries, images, commands, source hashes, simulator hashes and transcripts
are retained under `build/test-results/item5-qualification/` for release
qualification. The reproducible cpmsim reconstruction and complete final
conformance campaign remain separately tracked release work.
