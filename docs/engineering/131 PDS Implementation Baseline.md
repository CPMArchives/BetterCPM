# 131 — PDS Implementation Baseline

Date: 2026-09-11  
Status: Stage 0 implementation baseline

## Purpose

This records the last layout before the versioned PDS ABI is introduced. Later
PDS, resident-service and ROMability work is measured against this checkpoint.
The baseline is descriptive; it creates no new ABI.

## Current memory contract

| Range | Bytes | Owner |
| --- | ---: | --- |
| `F400h–FFFFh` | 3,072 | Platform-reserved memory |
| `F000h–F3FFh` | 1,024 | Shared physical/module buffers |
| `EF80h–EFFFh` | 128 | Directory transfer buffer |
| `EF57h–EF7Fh` | 41 | Active RSX reconstruction table |
| `ED17h–EF56h` | 576 | Drive tables and disk workspace |
| `EC86h–ED16h` | 145 | Protected file services |
| `EA08h–EC85h` | 638 | BIOS |
| `E648h–EA07h` | 960 | Disk and extension support |
| `E49Fh–E647h` | 425 | Protected loader/extension services |
| `D6BCh–E49Eh` | 3,555 | BDOS and private state |
| `D5C4h–D6BBh` | 248 | System gateway, ECB and CPX profile |
| `D504h–D5C3h` | 192 | Current command-history PDS |
| `D501h–D503h` | 3 | Dynamic CP/M gateway |
| `C901h–D500h` | 3,072 | Default loaded CPX allocation |
| `B401h–C900h` | 5,376 | CCP image |
| `0100h–B400h` | 45,825 | TPA below the command environment |
| `0000h–00FFh` | 256 | CP/M page zero |

The live exclusive TPA ceiling is `D501h`, exposing 54,273 bytes beginning at
`0100h`. The largest complete-record COM file is 54,272 bytes, exactly 53 KiB.
Installed RSXs lower that ceiling by their allocated size. CPXs and the CCP are
reclaimable while a transient executes.

## Current PDS implementation

The only current PDS allocation is the 192-byte packed command-history area at
`D504h–D5C3h`. It contains a ten-byte control area and 182 bytes of records.
This is an implementation fact, not the planned general PDS ABI. HISTORY.RSX
will eventually own these records.

## Regression boundary

The focused system regression now seeds a valid history record before WBOOT,
allows the reconstructed CCP to execute commands, and verifies that the
original record remains intact. Existing tests cover the dynamic gateway,
53-KiB load boundary, CCP/CPX reconstruction, RSX preservation, BIOS and BDOS.

Stage 1 may add symbolic interfaces and a versioned descriptor, but must retain
this physical layout, the 192-byte history capacity, the 53-KiB COM ceiling and
observable command behavior.
