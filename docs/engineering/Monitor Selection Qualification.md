# Monitor selection and retained-service reconciliation

Implemented 14 October 2026 after PR 284. RSX implementation 1.5 keeps public
API 1.0. Production preparation now chooses the MCON entry for the prospective
layout, and the existing commit spine publishes it after validated movement.

## Shared preparation service

R3SLOTS retains pointer-union preparation at +0 and adds monitor selection at
+3. The private six-byte request contains normalized-facts, plan-record and
durable-target pointers. Candidate context construction and retained-member
preparation call the same service. No helper file or manager enlargement is
introduced. STATEFUL union preparation reuses the loaded overlay.

MCON version/class/platform and executable entry bounds are enforced by R3META.
The selector adds the entry offset to the prospective allocation base, checks
carry, and rejects a second provider before writing its durable target. The
25-byte preparation context reserves +23/+24 for that target, initialized to
zero. Finalization copies the prepared target into commit-request +35; zero
selects the basic backend. The word survives all preparation-overlay changes.

For every retained member, callable count and the canonical descriptor-tail
bounds must match its validated carrier/allocation. All ten bytes of each
normalized callable descriptor must match a live descriptor, independent of
metadata order. Added, removed or changed live/carrier services therefore fail
before detach. This applies to other callable services as well as MCON and
prevents a changed file from silently redefining a retained monitor.

No provider or BDOS callback occurs in selection or binding publication. All
fallible preparation reads finish before scheduler detach/movement. Removing
a monitor publishes the basic target; unrelated changes rebind a retained
monitor using its new base without resetting its parser/state.

## Footprint

| Component | Bytes | Existing limit |
| --- | ---: | ---: |
| Shared slot/selection overlay | 669 | 1,024 |
| Candidate context constructor | 476 | 1,012 |
| Retained preparer | 896 | 1,012 |
| Finalizer | 930 | 1,012 |
| Profile builder | 984 | 1,012 |
| Removal preparer | 966 | 1,012 |

R3PACK stays 15,360 bytes. Manager reservation stays 1KiB. No permanent BIOS or
BDOS growth occurs; unloaded TPA remains 53K. The two additional context bytes
use bounded caller-owned transaction scratch.

## Qualification

Production CPU transactions execute both Model 4 and cpmsim BIOS builds with
synthetic MCON providers. They cover initial binding, duplicate rejection,
missing preparation media, changed retained carrier entry, corrupt live count,
reserved byte, descriptor-tail pointer, entry and capabilities, unrelated loads
and unloads, retained movement/state preservation, monitor unload, self-retirement
at the warm-boot boundary and restoration of the core TPA. Rejections retain
binding, generation and live bytes. Synthetic callbacks establish lifecycle
behavior, not terminal rendering compatibility.

Existing carrier/metadata, pointer-union, coordinator, transactional Stage-3
STATEFUL movement and generation-publication campaigns pass. Coordinator fixtures
now materialize canonical retained descriptors; exact scratch-bound expectations
include the new two-byte context field.

Reproduce with build_rsx_runtime_overlays.py, test_monitor_selection.py
(and --z80pack-build for the host BIOS), test_rsxslots.py,
test_rsxcoordinator.py, test_rsx_stage3.py, test_monitor_metadata.py and
test_monitor_commit_publication.py. ROM and distribution gates qualify deployed
layouts on both platforms. Both final System Disks build and boot-qualify:
cpmsim has 22 files/178K free; trs80gp has 21 files/626K free. The unloaded
53K TPA and existing permanent ROM layout remain unchanged.

## Remaining work

Command-return sequence reset and explicit internal clear/home handling must be
integrated next. Then implement ADM-3A and VT52 RSXs with their dedicated test
utilities. The [developer guide](../programmers/Monitor%20RSX%20Development.md)
will gain worked examples when those providers exist. This stage does not claim
that either terminal personality has been implemented.
