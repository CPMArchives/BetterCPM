# Post-1.0 Reclaimable Code, Overlays and Command Environment Review

## Status

Research agenda recorded 2026-10-12. These questions belong to the post-1.0
architectural retrospective; they approve no implementation, platform exclusion,
new ABI or change to the 1.0 memory and reconstruction contracts.

Read alongside the [unified module model investigation](POST-1.0-UNIFIED-MODULE-MODEL.md)
and [terminal architecture outline](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md).

## Broader use of disk overlays

The RSX manager already uses disk-loaded management helpers, consolidated for
1.0 into the fixed-slot R3PACK.RSX container. Installed RSX services themselves
remain protected and resident. Investigate whether this is a useful deliberate
pattern for additional system functionality rather than merely a compromise.

Questions:

- Which infrequently used BIOS, BDOS or extension functions could be loaded on
  demand? Compare configuration, installation and module management with hot
  console and ordinary file-I/O paths.
- How often would each operation load code, and can related operations share a
  loaded overlay or batch their work? Measure load frequency as well as bytes.
- What resident loader, protected window, scratch storage, state and dispatch
  overhead is required? Measure net permanent-memory savings rather than the
  size of code removed. A reserved window does not automatically become TPA.
- Which services must remain resident so the loader and essential error
  recovery never depend recursively on the missing overlay?
- What happens if the system disk is removed, the container is unavailable,
  media changes or reads fail? Define availability, integrity and recovery
  before broadening dependencies on external code.
- Would extensive overlays make actual floppy systems impractical? Is that an
  acceptable target tradeoff today, or can a usable floppy baseline coexist
  with a fast-storage configuration? Measure real floppy and fast-storage
  behavior rather than assume either result or abandon a platform in advance.
- Compare disk overlays with banked memory, ROM execution and optional resident
  caching on platforms that support them. Distinguish capacity gains from
  reduced latency and account for platform-specific machinery.

## Split resident services from reclaimable command support

Investigate whether portions of the core or existing RSXs are needed only at
command time and could become CPXs, leaving a smaller resident service behind.
Candidates include command parsing, help, status/configuration interfaces,
installation/removal preparation and terminal-provider selection. Active
terminal parsing, keyboard/reply handling, clock services used by applications,
ordinary disk services and essential reconstruction machinery need a separate
availability analysis; conversion is not presumed safe.

Questions:

- What is each routine's actual caller set and lifetime? Could a transient
  application, direct BIOS caller, interrupt or error path need it while the
  command environment has been reclaimed?
- How much protected resident memory would the split recover? Moving already
  reclaimable code does not create additional TPA.
- Which mutable state must survive outside the disposable CPX image, and how
  are ownership, cold/warm reset, unload and reload handled?
- How are live service pointers prevented from targeting reclaimed memory?
  What minimal resident machinery can reconstruct the command environment and
  recover if disk reload fails?
- Can management front ends share the existing CPX reconstruction mechanism
  without introducing a second loader or weakening RSX transaction guarantees?

## CPXs versus overlays

Both mechanisms reread code from disk. Compare their functional differences
rather than treating the names as fundamentally different technologies.

A command-time CPX yields its memory to a transient and is reconstructed when
control returns. A runtime overlay serves operations while the transient is
active, usually using a retained protected window. Command-time overlays may
be functionally similar to CPXs. Determine whether existing CPX machinery is
sufficient for those cases, and whether application-time services justify a
separate mechanism. Include placement, load timing, state persistence, call
availability and failure recovery in the comparison.

## Why retain runtime CPX modularity?

The entire CCP can be reclaimable and reloadable. CPXs therefore have no
inherent TPA advantage over an equivalently reclaimable monolithic command
processor. Assess their value in optional installation, independent development
and updates, selectable command environments and third-party packages against
metadata, dispatch, profile management, reconstruction and compatibility costs.

Compare at least:

1. A small CCP with standard and optional commands in runtime CPXs.
2. Standard commands integrated into the CCP, with CPXs only for genuinely
   optional or independently supplied extensions.
3. A build-generated monolithic command environment assembled from selected
   source modules, retaining source modularity without runtime package loading.

Questions:

- If RCP is always installed and changes in lockstep with the CCP, is its runtime
  separation still worth its cost?
- Can a monolithic build share common code more efficiently and reconstruct
  with fewer disk operations? What flexibility would it lose?
- Which real user or developer workflows require runtime package selection
  rather than build-time selection or standalone transient utilities?
- How do each arrangement's command-time footprint, application TPA, startup
  and warm-return costs, persistent state and recovery behavior compare?
- Could a shared source organization support multiple packaging choices without
  maintaining divergent command implementations?

## Review evidence and decision boundary

Inventory code and writable state by owner, caller, lifetime and memory class.
Measure rounded allocations, loader/window overhead, actual load counts and
latency on both supported platforms, plus disk-removal and failure behavior.
Use the existing 53 KiB unloaded-core TPA qualification as the comparison
baseline, retaining the established distinction between core memory and optional
loaded RSX costs. Investigate whether additional TPA can be recovered without
promising 54 KiB in advance.

The retrospective should present measured alternatives and explicit tradeoffs.
Recording these questions neither selects overlays as the general architecture
nor commits to removing CPXs or floppy support.
