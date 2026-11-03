# P2DOS distribution, GPL declaration and clock RC scope

Base: merged PR #585, `663e1ff33e9c67b6f68b6bf1acf544fac64f401a`.
Prepared for maintainer review; **package freeze remains on hold**.

## Changes

P2DOS.RSX is selected in user 0 on both System Disks. It remains optional to
load after the native provider; neither P2DOS nor a clock provider is added to
startup. The carrier/source is unchanged. This resolves the mismatch between
the retained required-to-ship contract and the former inventory exclusion.

T104C3/T104Z8 (104/105 frontends) are explicitly deferred from this 1.0 RC.
They are not System/Utilities carrier members or release gates. Preserve their
source and historical qualification for later work; no ABI or implementation
is removed. Reconcile the roadmap, implementation contract and guides with
this release-scope decision rather than rewriting historical evidence.

LICENSE declares GPL-2.0-or-later for original BetterCP/M contributions,
including original documentation, tools and tests. COPYING is the complete,
unmodified GPLv2 text. NOTICE preserves third-party/derived/historical terms
and does not claim ownership or permission for those works. Each independent
package carries these files; the complete Source and cpmsim source kit also
retain them at their source root. No individual copyright-holder name or
copyright transfer is invented by the declaration.

[Montezuma permission investigation](Montezuma-Permission-Review-2026-11-03.md)
found historical separate-authorship/commercial-distribution evidence, but no
broad public redistribution grant in the bounded sources examined. Some scans
were available only through indexed text. The former blanket README assertion
is corrected to permission-unresolved. No third-party files are deleted,
relicensed or replaced; no contact was sent. That rights gate remains open.

## Measured construction and execution

The common build and independent System construction for both platforms pass.
The added P2DOS carrier is 668 bytes, SHA-256
`9c854dd4aa8afcf439ac28233a8c723cd2cc32888d2aa137ba1bf9e2c3e82a08`,
byte-identical to the earlier locally built carrier. Both images pass file
readback, filesystem and CONFIG fingerprint checks. Remaining allocation space:

| Target | User-0 files | Free bytes | Current execution evidence |
| --- | ---: | ---: | --- |
| cpmsim | 34 | 120,832 | Fresh boot and supplied-carrier native ABI/lifecycle probe pass |
| Model 4 | 30 | 589,824 | Host construction/readback pass; new-image manual execution pending |

The cpmsim probe executes the P2DOS from the new A0 image, with the diagnostic
on a private work disk. It checks absent, loaded, provider-unloaded/replaced and
frontend-unloaded behavior, A/HL results, DE/SP/IX/IY preservation, failed-GET
atomicity and warm reconstruction between transients. It uses the pinned
qualification-profile cpmsim binary in ordinary RAM mode, not a new ROM/XIP run.

[Summary and exact hashes](evidence/2026-11-03-p2dos-license/summary.json) and
[raw transcript, base64 with hash](evidence/2026-11-03-p2dos-license/cpmsim-transcript.json) retain the
local verification commit/tree. This identity is not the authoritative main or
future PR head. Original full local build reports and the first failed attempt
(with an older runtime lacking MOUNT.COM) remain preserved in the workspace.

Fifteen distribution gates, nine candidate-package gates, the controlled P2DOS
suite (including 21 provider-write failures), and 26 assembled provider sampling
checks pass. The GPL package regression reads every project notice back from
representative independently named archives; source and disk membership tests
retain third-party boundaries and no-default-load semantics.

To reproduce from an accepted source checkout, use a fresh output directory and
the pinned reconstructed simulator with its MOUNT/R/W guest tools:

```sh
python3 tools/build_complete_system.py
python3 tools/test_p2dos_rsx.py
python3 tools/test_clock_sampling.py
python3 tools/test_distribution.py
python3 tools/test_release_candidate_packaging.py
python3 tools/prepare_release_systems.py --output /new/systems --simulator /pinned/cpmsim
python3 tools/test_packaged_p2dos.py --image-dir /new/systems/z80pack --simulator /pinned/cpmsim --output /new/p2dos-probe
```

No new Model 4 runtime, final six-archive installation/acceptance or protected-XIP
qualification is asserted. These candidate images do not replace distribution
masters. Retain approved audit 003/general 007 deferrals and the closed 006
correction. Public release and package freeze remain separate decisions.
