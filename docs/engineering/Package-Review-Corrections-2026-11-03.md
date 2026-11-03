# Package review corrections and remaining decisions

Base: `91c91f7b06569ef9aca6e534f431f22cf0c9aaf8`. Package freeze remains on hold.
These changes are proposed for review; no merge or candidate acceptance is implied.

## Implemented review corrections

- Reconcile current System monitor/host-tool descriptions, NOAH companion scope,
  BATCHIO placement and Model 4 startup order without changing disk membership.
- Describe the complete pinned runtime profile and System-only cpmsim setup.
  Include the local reconstruction notes and both native-tool operator guides
  where their independent downloads refer to them. Label external Source and
  Documentation references; omit stale generated editions as before.
- Disclose the accepted corrupt-history risk and bounded compatibility/keyboard
  evidence. Preserve the 003/general 007 deferrals and #583/#584 scopes.
- Retain the matching CP/M Tools source/build/test/documentation subtree at
  `3e5eee55cac154e125659aadaa865b2c66e7d06a`. Its 66 files preserve upstream bytes;
  the source manifest maps all seven unchanged binaries to upstream build blobs.
  Package and full Utilities-source assembly reject missing/changed source.
  This does not add those seven programs to System or Utilities disks.

## Recommendations at the time of PR #585

The maintainer subsequently approved preparing P2DOS on both System Disks,
GPL-2.0-or-later for original work, and explicit 104/105 deferral for review.
The current proposal and measurements are in
[P2DOS and licensing release-scope follow-up](P2DOS-License-Scope-2026-11-03.md).
The recommendations below retain their earlier historical scope.

**Clock scope.** Keep P2DOS’s retained 1.0 ship requirement. Recommend distributing
P2DOS.RSX on both System disks, optional to load and absent from default startup,
after measuring available capacity and qualifying the exact updated images.
If capacity is insufficient, return a placement proposal rather than removing
another member. Defer T104C3/T104Z8 from this RC explicitly: revise the admitted
component disposition and current documentation together, preserving historical
qualification. This is a release-scope choice, not a claim those adapters failed.
Do not include any of these carriers until the distribution decision is approved.

**Original-work license.** Recommend GPL-2.0-or-later for maintainer-controlled
original BetterCP/M code and original documentation, with explicit per-work
exclusions. This is a policy recommendation for consistent source sharing with
the existing TED, ZSM4 and CP/M Tools ecosystem, not a conclusion that merely
bundling separate GPL programs forces the independently written OS to use GPL.
A permissive license for independently owned original code remains an alternative
if that is the maintainer’s preference. Confirm ownership/contributor authority
and intended copyright text before adding a grant. Retain third-party terms;
do not apply a blanket new grant to historical imports or adapted source.
See the [GNU licensing FAQ](https://www.gnu.org/licenses/gpl-faq.en.html).
No project license is selected or applied by this change.

**Montezuma material.** First obtain or identify a specific documented permission
covering the selected catalog data and original utility/reference material.
The retained [DRI CP/M permission](https://www.cpm.z80.de/license.html) alone does
not establish rights to independently owned additions. Do not certify a grant
from the existing README assertion. If evidence remains unavailable, prepare a
separate proposal to exclude nonessential historical binaries/listings from
public payloads and independently reconstruct the required format data from
verified technical facts. Check all build/test/source closures and catalog/media
behavior before that proposal; do not remove catalog inputs or change supported
formats here. Rights/source clearance and package freeze remain unresolved.

## Validation scope

The isolated local verification snapshot matched main’s complete Git tree
`837b8d44e0bacbdf98a20674b1ed30cff50c44a0` before changes. Its local commit is a
verification snapshot, not the authoritative remote commit. Source file Git
blob/SHA-256 checks, seven binary mapping checks, tamper regressions, existing
candidate-packaging regressions and nested source/archive readback are used for
this patch. Fresh guest/runtime campaigns and the final six-archive candidate
remain separate; no fresh seven-program native rebuild is claimed.
