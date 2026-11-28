# RomWBW shared configuration and portable utilities

28 November 2026; macOS ARM64, pinned romwbw_emu 1.51 and RomWBW 3.5.1.
This is focused engineering acceptance, not platform release qualification.

The shared CONFIG now uses the RomWBW block backend. Startup commands and PDS
choices use the common editor, validator and pending/cold-boot policy. IOBYTE
and B's binding share the checksummed BWCF version-2 record and preserve each
other when saved. CONFIG mirrors saved BCST/PDS writes into the checked system
package. SYSGEN preserves startup/PDS/IOBYTE while unbinding the installed B.

| Evidence | Coverage |
| --- | --- |
| `config-result.json`, `config-edit.txt` | Shared menu, confirmed startup/IOBYTE save, live values unchanged, block save preserves IOBYTE, PDS pending edits and save. |
| `config-cold.txt`, `config-installed.txt` | Cold activation, MCL across two transients, native installation with edited settings, installed startup/PDS/IOBYTE and B unbinding. |
| `utility-result.json`, `utilities.txt` | All 30 shipped portable COM version queries; PIP/COMPARE binary copy; host-matched MD5; NOAH add/test/extract; ERA; TIME without provider; STAT memory; two-command SUBMIT. |
| `install-result.json`, `install.txt`, `installed-boot.txt` | Larger utility image installed and verified, every manifest file independently extracted and hashed, installed boot and RSX lifecycle. The result also records the existing refusal, persistence and injected-I/O checks. |
| `regression-result.json`, `system.txt` | Original 15 boot/BIOS/BDOS/TPA/RSX/geometry checks repeated on the expanded image. |
| `build.json` | Exact candidate identity, component hashes, system-image hash, layout and resident bounds. |

The source and destination images are private copies. The host reader verifies
the full CP/M-record-padded contents of both binary utility fixtures and every
installed manifest file. The shared-profile suite (11 tests), component input
suite (14), registry suite (9), and release-heading suite (2) also pass.
Retained transcripts normalize line endings, trailing whitespace and workspace
paths; raw PTY output stays in the corresponding build directories.

The image includes HELP.COM/HELP.LBR, NOAH's overlay and the portable NDR and
BATCHIO providers. Floppy FDB/DUP/SYSBUILD are excluded; CONFIG/SYSGEN use the
fixed hd512 backend. Wider functional qualification of each utility, native
toolchain sessions, screen personalities, SYSTEM.SYS import/export, formatting,
release packaging and physical hardware remain separate work. HBIOS is supplied
by the emulator's C++ implementation. Banked RSX execution remains deferred.
