# 160 — Dynamic Gateway RAM Ownership

Date: 2026-09-27  
Status: inventory correction implemented

## Finding

The initial ROM-profile placement pass found that the three-byte gateway at
`D501h` had retained its historical classification as executable code. That
classification was incomplete: `SYS_INIT` writes a `JP` opcode and rewrites the
target to the fixed BDOS entry or the first active RSX. Warm reconstruction may
therefore change the gateway even though its address remains stable.

The gateway cannot be part of the immutable image. It is fixed subsystem state
owned jointly by the system gateway and RSX chain, executable from RAM, created
during cold initialization and rebuilt after command-environment reconstruction.

## Correction

`metadata/rom-ram-ownership.tsv` now records `D501h..D503h` explicitly. The
historical relocation measurements remain 2,252 bytes on TRS-80 and 2,251 on
z80pack because the gateway was already at its required RAM address. The full
high-memory RAM requirements are 2,255 and 2,254 bytes respectively.

The inventory test enforces both totals. This correction assigns no new address,
changes no binary and does not begin the remaining ROM/RAM relocation.
