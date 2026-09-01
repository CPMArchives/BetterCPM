# Engineering Specification 21: Basic BDOS State Functions

## Milestone

The resident BetterCP/M call path now implements the first non-file BDOS
functions required by ordinary CP/M programs:

| Function | Contract implemented |
| ---: | --- |
| 12 | Return CP/M version `0022h` in `HL` |
| 25 | Return current default drive (`0` for A) |
| 26 | Set the persistent DMA address from `DE` |
| 32 | Get the current user with `E=FFh`, or select `E modulo 32` |

Function 15 remains the first file operation. Unsupported returning functions
continue to return `FFh` explicitly.

## Compatibility basis

These contracts follow the BetterCP/M CP/M 2.2 Compatibility Ledger rather
than being inferred from convenient implementation behavior. In particular,
function 32 selects the BDOS user number modulo 32. This is wider than the
values accepted by the traditional CCP `USER` command and is compatibility-
visible behavior.

The set form of function 32 and function 26 have no guaranteed application-
visible result. BetterCP/M currently returns zero deterministically, but this
is not promoted to a compatibility promise.

## State ownership

The dispatcher now owns three independent initial state values:

- current user: 0;
- current/default drive: A; and
- current DMA address: `0080h`.

Changing the user does not change the drive or DMA address. Setting the DMA
address does not affect identity calls. The selected DMA persists across
non-resetting calls; later file-transfer functions must consume this state.

Only drive A is presently selectable because function 14 is not yet
implemented. Function 25 nevertheless reports live BDOS state rather than a
literal result, so drive selection can be added without changing its contract.

## Verification

Direct-dispatcher tests verify version and register aliases, drive A, DMA
persistence, modulo-32 user selection and query, independence of DMA and user
state, and explicit rejection of an unsupported selector.

The composed resident test invokes all five implemented functions—12, 15, 25,
26, and 32—through an application fragment containing `CALL 0005h`. Native
CP/M ZSM4/Digital Research LINK and the host assembler must produce the same
178-byte BDOS binary.

## Deferred work

The DMA address is state for future disk transfers; function 15 does not copy
directory data to DMA. Reset and warm-start transitions do not yet restore the
default DMA because those paths remain scaffolds. Current-drive selection,
login-vector reporting, and disk reset also remain unimplemented.

## Next increment

Engineering Specification 22 completes this increment with function 14,
login-before-commit selection of the available drive A, and coherent function
25 reporting. The next increment can define disk reset and login-vector state.
