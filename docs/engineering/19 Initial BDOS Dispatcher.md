# Engineering Specification 19: Initial BDOS Dispatcher

## Milestone

BetterCP/M now has its first independently buildable BDOS call dispatcher.
The provisional entry at `E600h` accepts the CP/M register convention—function
number in `C` and parameter address in `DE`—and exposes function 15 (Open File)
through the grouped and wildcard-aware directory engine.

This is the callable BDOS boundary, but not yet the page-zero gateway. Address
`0005h` is deliberately untouched until the resident CCP/BDOS/BIOS image and
boot initialization path are defined together.

## Initial contract

The implemented slice has deliberately narrow state:

- function 15 operates as current user 0;
- the FCB may select the current/default drive, presently drive A;
- the current drive must have completed its boot-time login;
- the dispatcher clears FCB `S2` before Open, as required at this boundary;
- success returns the directory slot (0..3), and no match returns `FFh`;
- normal returns provide the CP/M aliases `A=L` and `B=H`; and
- unsupported returning functions explicitly return `FFh` rather than falling
  into an accidental implementation path.

The directory engine now distinguishes a storage failure from a slot result by
setting carry. The dispatcher maps that condition to `FFh` provisionally. This
is intentional scaffolding, not the final CP/M disk-error interaction policy.

## Stack boundary

The dispatcher saves the caller's stack pointer, runs on a private 64-byte
stack, and restores the exact caller stack before returning. The placement and
size are provisional, but establishing ownership now prevents deeper BDOS call
graphs from silently consuming application stack space.

The dated patch comment beside this stack records why the boundary was added at
this point in development; its history should remain visible while placement is
still evolving.

## Verification

The executable test initializes drive A, calls both the directory engine and
the dispatcher, and verifies:

- function 15 activates an exact FCB and returns its directory slot;
- `S2` is cleared while the caller's `CR` is preserved;
- `A/L` and `B/H` return aliases are correct;
- the caller's stack pointer is restored exactly;
- a missing file and an unsupported function return `FFh`; and
- a simulated storage failure cannot be confused with slot success.

Native CP/M ZSM4/Digital Research LINK and the host cross assembler must
produce byte-identical dispatcher binaries. The dispatcher is 123 bytes at
this milestone, including its provisional private stack. The directory engine
is 869 bytes after adding its explicit Open internal-error return.

## Deferred work

This increment does not yet provide mutable user/drive state, explicit-drive
selection and restoration, a final disk-error presentation, installation at
page zero, or a bootable resident system containing this BDOS.

## Next increment

Define and test the page-zero `CALL 0005h` gateway, resident component layout,
and initialization transfer that logs in the default drive before applications
can enter BDOS. This will turn the isolated dispatcher into a system-call path
without prematurely implementing the full BDOS function set.
