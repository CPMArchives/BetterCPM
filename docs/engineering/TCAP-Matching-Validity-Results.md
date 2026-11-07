# TCAP matching-system admission and global validity experiment

Status: bounded experimental implementation and CPU evidence, 7 November 2026.
Follows [transaction/return-path qualification](TCAP-System-Paths-Results.md),
PR #657. The public TCAP request ABI remains a proposal. Utility migrations,
HELP delivery and release assignment remain deferred.

## Decisions and result

The private candidate now has a **permanent coordinator**, positive
matching-system admission, and a boot-global validity allocator. The root is
outside every RSX allocation. It survives owner movement, unload and warm entry;
only true cold entry begins a new lifetime. The candidate does not substitute a
resident-layout generation or build identity for a validity identity.

| Identity | Size | Purpose |
| --- | ---: | --- |
| Private source-closure build identity | 16 bytes | Compatibility of the core, manager, command carriers and owner code |
| Owner validity | 4 bytes | Non-reusing namespace within one boot lifetime, replaced by managed idle publication |
| Resident-layout generation | 2 bytes | Publication marker and discovery-address lifetime; not an identity allocator |
| Owner session/scope serials | 4 bytes each | Distinguish sessions/scopes within a validity identity |

The root allocates nonzero validity values monotonically, including FFFFFFFFh
as the final value. It refuses the next reservation without changing its counter
or destination. No wrap, free list or provider-owned reset exists. A failed
preparation can burn a reservation; it cannot return it to the pool or change
the old owner's validity. This preserves the old profile on abort.

A prepared validity is copied into the prospective owner during **infallible
persistent publication**, before Monitor binding and the final generation marker.
The campaign executes the real scheduler/mover/commit engine and a staged
publisher whose body resides in the permanent root. It verifies write ordering,
not just the resulting values. Retained STATEFUL movement gets a new validity;
a fresh load at a previously used address cannot recreate an old session token,
even with identical local serials. Unload leaves the allocator intact.

Cold boot invalidates all clients, as already specified by the
[integration design](TCAP-Integration-Design.md). Handle persistence across cold
boot is unsupported. This is not a persistent identity service across power loss.
Reservations/publication are serialized by the manager; the private allocator
is not callable from interrupts or output callbacks.

## Matching-system admission

A source-closure identity includes the experimental contract/placement policy,
assembler hash, reviewed campaign dependencies, and core/manager/command/provider
sources. A sealed manifest separately records SHA-256 hashes of the complete
resident image, permanent gateway/root and all required artifacts. Missing,
extra or altered artifacts fail the build/package gate. This uses the same
source-closure principle as the existing checked-build machinery, without
claiming to issue a production checked-profile identity.

The CPU-side artifact gate requires eight roles:

1. BIOS routing/Monitor image.
2. CCP carrier payload.
3. Model 4 reloader.
4. Maintained stage 2 source payload.
5. Metadata validator.
6. Transaction finalizer.
7. Commit engine.
8. Persistent publisher.

The private envelope contains role, 16-byte identity, length, CRC-16/CCITT and
payload. The caller supplies the exclusive buffer end and a readable fixed
21-byte header. The root pins each role's expected length/CRC, checks identity,
checks exact buffer extent without wrap, then computes the payload CRC. A
caller-supplied checksum cannot replace the trusted pin. A successful check
sets only that role's admission bit; rejection does not authorize replacement.
Every required role must pass before TCAP admission or validity reservation.

The modified **actual metadata validator** admits private MCON 1.3 only with the
complete matched root and the owner payload's matching embedded identity. It
also reserves experimental XTCP 0.4 in this private candidate: earlier prototype
versions are rejected, rather than slipping through the opaque-service path.
Ordinary legacy MCON 1.2 remains admissible without enabling TCAP. Existing
ADM-3A/VT52/ANSI byte-stream and backend behavior remain intact.

Every private XTCP entry checks matching root admission and nonzero issued
validity. The owner image starts with zero validity, so direct installation of
cold bytes cannot create a portable session. The shipped metadata validator
still rejects MCON 1.3; no production admission rule or public operation allocation
is changed by this work. Private Monitor operations 25/26/27 retain the meanings
from the preceding experiment.

SHA-256 sealing and CRC checks serve build compatibility and accidental-corruption
detection. They are not authentication against hostile software with arbitrary
CP/M memory access. The root gate validates bytes before a caller loads them;
it does not itself read files, copy code into final allocations or execute it.

## Permanent placement and storage cost

| Item | Previous reference | Private matched candidate |
| --- | ---: | ---: |
| Fixed resident span | 6,588 bytes | 7,100 bytes |
| Gateway plus permanent root | 248 bytes | 760 bytes, exactly its region |
| Root portion | None | 512 bytes, including code, identity, pins, counter and scratch |
| Unloaded TPA, record-aligned | 54,272 bytes | 53,760 bytes |
| Resident boot sectors | 13 | 14 |
| Boot-volume DPB OFF / DSM | 2 / 389 | 3 / 384 |
| Optional owner allocation | 2,304 bytes | 2,304 bytes |
| Owner static relocations | 231/232 | 232/232 |
| Metadata overlay | Previous shipped rules | 1,021/1,024 bytes |
| Publisher overlay slot | 107 bytes | 107 bytes; body dispatches to permanent root |

The new private bases are SYS=D3C4h, history=D304h, TPA=D301h and RSX=CF04h.
BDOS, BIOS, file loader, tables and upper resident limits retain their addresses;
all dependent staged components are rebuilt together. Existing packed-image,
COM-handoff-offset and overlap checks pass. The PDS/history size remains 192
bytes, rather than hiding root state inside history or an optional allocation.
The ordinary ANSI personality's optional-allocation delta remains 768 bytes;
the additional permanent cost is 512 bytes regardless of whether TCAP is loaded.

The extra resident sector moves the last command sector into cylinder 2. The
old two-track reserved area ends at sector 40; the candidate needs sector 41.
The private boot-volume table therefore reserves three tracks (60 sectors) and
reduces DSM to 384. That costs **10,240 bytes of boot-volume data capacity**.
Other data-drive DPBs are unchanged. A historical test reader keyed only by
side/sector aliased the new cylinder; the campaign now uses a controlled
track/side/sector service and verifies all thirteen command-sector keys are
unique. This is a real placement consequence, not a test failure to suppress.

This layout is **incompatible with existing OFF=2 system disks**. No disk image,
filesystem contents, distribution manifest or installed system is changed.
The reference layout is experimental; these measured costs do not assign TCAP
to a release or approve a new production disk format.

## Evidence and reproducibility

Run the [matching/validity campaign](../../tools/prototypes/tcap/README.md#matching-system-and-global-validity-follow-up).
The [report](evidence/tcap-matching-validity/report.json),
[sealed manifest](evidence/tcap-matching-validity/manifest.json) and
[generated root/layout/publisher patch](evidence/tcap-matching-validity/permanent-root.patch)
record the private source closure, sizes and executed cases. Generated binaries
and assembly listings stay under `build/tcap-matching-validity/`.

Across two backends and two owner origins, the campaign repeats 412 prior named
checks and adds 76 allocator/lifecycle/publication checks: **488 in total**.
The new checks include multi-byte carries, final issuance and exhaustion, actual
cold/warm entry boundaries, burned reservations, failed real commit, publication
ordering, actual STATEFUL movement, actual empty-profile unload and fresh
same-address reload. The stale token's local serials deliberately equal the new
token's serials; its validity differs and it cannot end the new active scope.

Additional checks include:

- 200 CPU gate rejections covering role, every identity byte, pinned length/CRC,
  corrupt payload and short/long buffers; every missing role prevents allocation.
- Sealed SHA-256 closure rejection for missing/altered artifacts and changed
  root/resident images.
- Actual carrier normalization and metadata acceptance/rejection, including every
  absent system role, old prototype versions, foreign owner identity with a
  recomputed valid carrier checksum, and ordinary legacy MCON admission.
- The existing full commit/scheduler/mover regression; ten full reloader cases
  with controlled reads/files/resets and synthetic CPXs; 108 actual legacy
  personality/backend probes.
- Third-origin owner relocation, alternate-origin CCP relocation, original
  reloader/overlay budgets and the enlarged packed resident-region checks.

Observed BDOS private-stack depths remain 26/40 bytes for Model 4 and 34/40 for
the ANSI-host fixture. System-entry tests observe two bytes on the protected
system stack before their next-phase stop. These are observed component depths,
not whole-system worst cases or live/native evidence.

## Remaining integration boundary

Follow-up: [native-reference manager/loader integration](TCAP-Native-Manager-Integration.md)
now exercises manager-produced reservations, the real commit path and executable
loading gates together. It measures the larger permanent/transient footprint and
keeps media, checked-profile and public-ABI qualification separate. The limitations
below describe this earlier experiment.


The two mechanisms are implemented and qualified together **in the private
campaign**, including positive metadata admission and real commit publication.
This does not make an installable TCAP system. The campaign explicitly constructs
the prepared validity record; the full finalizer and context producers must be
extended to construct/reserve that record on every relevant managed transition.
The eight-role gate must also be wired into every actual file-reader copy/execute
front door before activation, including later command reconstruction. No caller
may bypass it after a successful initial check.

The CPU gate is tested against actual generated artifacts; invoking it directly
is not an end-to-end checked boot or disk-loading claim. Stage 2 still uses the
reference experiment's explicit checked-helper bindings. Full checked cpmsim,
native/ROM/Model II, real filesystem stack depth, media installation and timing
qualification remain open, as does the complete public request ABI. No utility
has been migrated and no release has been assigned.
