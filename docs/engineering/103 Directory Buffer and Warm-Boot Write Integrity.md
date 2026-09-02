# Engineering Specification 103: Directory Buffer and Warm-Boot Write Integrity

Date: 2026-09-02

Runtime CPX testing exposed a latent resident-memory overlap. The directory
buffer remained at `F300h..F37Fh`, while BIOS growth had reached through
`F30Ah`. Loading directory data therefore overwrote the tail of the physical
write routine. The exact failure depended on the directory bytes and appeared
after WBOOT reconstruction as an ERA command that never returned.

The directory buffer now occupies `EC80h..ECFFh`, the protected 128-byte gap
between the command reloader and the `ED00h` physical-sector/module buffer.
All DPHs, BDOS/directory constants, and structural tests use this address.

The regression sequence uses a private writable disk copy, loads HELLO.CPX,
runs a transient command through WBOOT, deletes `HELLO.COM`, and requires a
subsequent DIR and command prompt. The instruction-level reloader test also
verifies the real BASIC and HELLO payloads, relocation, non-overlap, and link
order independently of physical emulation.
