BetterCP/M 1.3 - Altair Z80 / Tarbell

Use a Z80 CPU, 64 KiB RAM, 88-2SIO console and Tarbell 1011D controller.
The package qualifies this configuration under the pinned z80pack emulator.
Physical hardware and the original 8080 CPU are not qualified.

A: System; B: writable work disk; C:/D: mounted Utilities disks.
There are three Utilities disks. Mount the volumes required by your task.
STARTUP.SUB sets PATH C0: D0:. Programs and their overlays stay together.
The default complete-record COM limit is 57344 bytes; optional RSXs and
CONFIG memory owners reduce available space while enabled.

  HELP          Command reference (mount Utilities-1)
  STAT MEM      Memory use
  CONFIG        Saved cold-boot and live configuration
  SYSGEN SYSTEM.SYS B:   Install onto a disposable formatted work disk
  DUP /CHECK B:         Read-check every sector
  DUP /FORMAT B:        Erase every sector (confirmation required)
  DUP /COPY A: B:       Copy and verify a complete disk (confirmation required)
  RSX LOAD C:ANSI         Enable ANSI screen support (Utilities-1)
  BYE           Exit the emulator with confirmation

All images are 256256-byte raw files: 77 tracks, 26 sectors per track,
128 bytes per sector, sector IDs 1-26, no skew. ALTRB77 reserves eight
tracks and supplies 224 allocation blocks, including two directory blocks.
There are 64 directory entries. The host diskdefs uses an equivalent linear
record view to avoid the LibDsk odd-track geometry bug.

A: must be writable: SUBMIT and RSX operations use temporary files.
Back up your disk images before CONFIG saves or disk-management operations.
Change images only while the emulator is stopped; restart afterward.
Geometry changes, other disk formats, double density, graphics, modems and
additional serial channels are outside this release configuration.

For complete installation and offline build instructions, read the host
package's ALTAIR-INSTALLATION.md. The matching source package includes the
pinned emulator and assembler sources, third-party source offers and licenses.
