# Engineering Specification 105: Directory-Visible Extension Files

## Status

Implemented.

## Decision

`BASIC.CPX`, `HELLO.CPX`, and `HELLO.RSX` are ordinary user-zero CP/M files.
They appear in `DIR`, may be copied or replaced using normal filesystem tools,
and are no longer duplicated in fixed command-track slots.

The CCP remains a bootstrap image in reserved sectors. This is a separate
bootstrap decision: WBOOT can obtain the CCP without depending upon a command
environment, while optional extensions are discovered by filename.

## Protected file-loader service

A fixed service at `D000h` sits between the BDOS and directory components. Its
three provisional vectors open an eight-character filename stem as `.CPX` or
`.RSX`, read the next four 128-byte CP/M records as a 512-byte module unit, and
reopen the current file at record zero. A short final unit is accepted after at
least one record and is never confused with a missing header.

The service calls resident directory operations directly. It requires neither
the CCP nor a CPX, so cold boot and WBOOT can reconstruct the command
environment after its former memory has been overwritten.

## Persistent reconstruction data

Each active CPX reconstruction record now contains an eight-character,
space-padded filename stem rather than a physical system-slot number. Runtime
addresses continue to be calculated on every reconstruction. The initial
known-module manager writes `BASIC` and `HELLO` records in canonical order.

`CPX LOAD HELLO` and `CPX LOAD HELLO.CPX` are equivalent, as are their unload
forms. `RSX LOAD HELLO` and `RSX LOAD HELLO.RSX` are likewise equivalent.

## Compatibility and proof

The fixed-slot implementation is retained in Engineering Specifications
99–104 as development history. Its extension payloads have been removed from
the generated disk's reserved command area.

Automated physical tests verify:

- all three extension files appear in `DIR`;
- cold boot loads default `BASIC.CPX` by filename;
- `HELLO.CPX` loads, chains, survives command reconstruction, and unloads;
- transient fallback works after CPX removal;
- `HELLO.RSX` loads from its ordinary file, intercepts Function 201, survives
  WBOOT, and unloads with the TPA boundary restored; and
- explicit `.CPX` and `.RSX` command spellings work.
