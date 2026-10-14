# Monitor transaction commit spine

Implemented 14 October 2026 after PR 282. RSX implementation 1.3 retains public
API 1.0. This stage installs the safe detach/publication machinery; it does not
yet select or enable a real MCON provider.

## Installed transaction behavior

The finalizer reserves a 37-byte mode-one commit request, including the target
word at +35. Until monitor preparation is implemented, production requests
explicitly publish the basic backend address obtained from the immutable
MONRAW vector. No callback is executed while constructing this field.

After all scheduler validation succeeds, RS_PREPARE calls MONBASE before any
movement, including for zero-member profiles. Validation failures retain the
old binding and allocations. The publisher consumes the prepared target and
stores it alongside persistent profile publication before the commit engine's
final generation store. Neither detach nor publication performs disk I/O,
allocates memory or invokes a provider.

The publisher resolves the writable binding through the private BIOS API 1.7
trampoline layout: MONCALL is JP MC_CALL, and MC_CALL begins LD HL,(MP_MON).
This avoids embedding a platform-specific RAM address and also works after ROM
relocation. This instruction layout is now an internal manager dependency;
changes must update the publisher and its qualification together.

The legacy mode-zero commit path does not read request bytes +35/+36 or invoke
the persistent publisher. Scheduler validation/detach is shared. Test fixtures
now include the real BIOS hook primitives rather than an uninitialized vector.

## Size and validation

Scheduler: 496 bytes, exactly its existing region. Publisher: 107 bytes after the request-storage overlap fix,
continuation offsets unchanged. Finalizer: 914 bytes, within its 1,012-byte
prefix. Commit engine: unchanged at 1,007 bytes. R3PACK remains 15,360 bytes
and the manager reservation remains 1KiB. No permanent BIOS/BDOS growth or
change to the 53K unloaded TPA occurs in this stage.

Production CPU tests prove binding publication precedes the observed generation
write, a rejected transaction preserves the original binding and data, and mode
zero never reads the extended bytes. Existing upward/downward STATEFUL movement,
snapshot/commit, candidate and retained-member preparation campaigns pass.
The prepared Stage-3 load/removal campaign forces retained STATEFUL relocation
and verifies that only declared pointer/header words change.
Isolated binding probes now assemble the production scheduler and publisher.

The cpmsim ROM build classifies all 711 RSX-overlay address words, including the
two added BIOS-vector references. Permanent ROM layout is unchanged: 462 bytes
remain spare. Real ROM boot/RSX lifecycle and two-platform distribution checks
pass: cpmsim has 22 files and 178K free; trs80gp has 21 files and 626K free.

## Remaining work

Preparation must recognize MCON 1.0, enforce STATEFUL class, validate matching
platform capabilities and entry bounds, reject duplicates, and reconcile
retained live service facts with validated carrier facts. Store the prospective
address durably across overlay replacements, including unload/self-retirement
and moves caused by unrelated providers. Only then replace the finalizer's
basic-target default with the prepared target. Warm-return sequence reset,
internal clear/home migration, ADM-3A/VT52 providers and their test utilities
remain pending. Do not describe this intermediate stage as installed monitor
support.


## Resolver restoration regression

Expanded ADMTST exposed a post-commit failure: a provider could be installed
and listed, while Function 182 could not resolve MCON. The publisher's RT_REQ
word overlapped the first byte of fixed RT_CONT. Moving RT_REQ after RT_IMAGE
adds two helper bytes, stays within the existing move overlay, and preserves
the continuation offsets and permanent memory layout.

The publication test now checks that publication leaves continuation code
unchanged and executes its prefetched-resolver copy. The actual ADM3A lifecycle
check now invokes the real Function-182 gateway after installation, verifying
that its entry matches the published monitor binding. Existing selection,
movement and unload checks also pass with the correction.


A native trs80gp run of the corrected helper and expanded ADMTST reached its
keyboard-success message, then unloaded ADM3A and returned to the CCP. The
previous private run with the overlapping helper loaded/listed ADM3A but could
not look up MCON. This actual-emulator before/after agrees with the new resolver
restoration and post-transaction service-lookup regression checks.
