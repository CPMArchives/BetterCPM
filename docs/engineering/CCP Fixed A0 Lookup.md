# CCP fixed A0 command lookup

## Admitted 1.0 behavior

Unqualified transient command names search the caller's current drive/user
first, then drive A, user 0. The current-DU program has precedence. The
force-transient prefixes `:NAME` and `.NAME` use the same search order.
An explicit drive and/or user qualifier confines lookup to that location.
In particular, `B:NAME` means B in the caller's current user; `5:NAME`
means user 5 on the caller's current drive.

A program found on A0 executes in the original caller's DU. The default FCBs
and command tail describe the user's original arguments. Finding a program
commits to that image: read failure, oversize rejection or other load failure
does not restart lookup elsewhere. Missing programs retain the existing
unknown-command diagnostic. Media failures retain existing BDOS recovery;
this change does not suppress disk-error prompts or create a new error policy.

This is a fixed CCP policy, not a configurable path facility. General system
paths remain post-1.0 work. No BDOS, BIOS, CPX descriptor or protected-data
structure changes are required.

## Implementation

`CCP_LOPEN` owns the two Open attempts. It accepts the standard Open result
in A, not carry (which is not the public Open success/missing discriminator).
After a current-DU miss, the FCB drive byte and accepted-user flag identify
explicit qualifiers. Tentative drive-letter parsing and force-transient
prefixes do not accidentally count as explicit qualifiers.

For fallback, the existing saved-user/restore mechanism selects user 0 and
encodes drive A in the FCB. Bytes 12–35 are cleared before retrying Open.
The existing protected loader receives the opened FCB; caller context is
restored before CPX shutdown and program entry. Failure restores it as well.

The CCP grows from 5,376 to 5,437 bytes (+61). Rounded allocation rises from
5,376 to 5,632 bytes (+256). The 1,024-byte relocation header plus payload is
6,461 bytes, within the existing 6,656-byte boot carrier. There are 488
relocations. BDOS growth is zero. The CCP remains reclaimable by transients.

## Qualification

- Nine assembled lookup-provider cases cover current-DU success, fallback
  success/missing, both force prefixes, drive/user qualifiers, and restoration.
  Carry is deliberately set by the first Open provider to guard the public
  result convention.
- Existing CCP parsing, transient preparation, EOF/error/oversize handling,
  and disk-backed reconstruction with zero, one and two CPXs pass.
- Native ZSM4/LINK assembly matches the host binary byte for byte.
- Six public-command cases pass on each platform: A0-only lookup, both force
  prefixes, current-DU precedence, an explicitly qualified miss, and an absent
  program. Probes verify caller A3 on Model 4 and caller B3 on z80pack before
  printing success; the prompt retains that DU afterward.
- Evidence: `/private/tmp/ccp-a0-z80pack-final-20261010` and
  `/private/tmp/ccp-a0-model4-final-20261010`. Model 4 captures were verified
  after correcting the harness's zero-based capture numbering and accounting
  for command-line erasure during CCP reconstruction.
- The CCP payload SHA-256 is
  `3749d67267b33d6e0996203998f7efdf64b7f647e7223dc37a1d133f526b43db`.

The reloader unit fixture now compacts its simulated physical-sector source
addresses so the final source sector cannot overlap the larger CCP destination.
The older COM-boundary emulator harness now uses the established macOS
LaunchServices wrapper; direct launch caused an application-registration abort.
