# Component revision tracking

Status: policy accepted by the maintainer, 2026-10-24; implementation pending.

This policy governs future independent revision tracking. It supersedes older
build-counter terminology and identification rules where they conflict. It does
not renumber existing artifacts, alter historical qualification records, or
declare a new core or package release.

## Identities

Each independently tracked component has a version and a positive integer
revision. A subsystem exposing a public contract additionally has an API version.
An API has no separate revision counter. Git source commits are provenance,
not independent component revisions or compilation counters.

Revisions increase monotonically across version changes. Display uses at least
three digits, without rollover at 999. Normal utility output uses, for example,
`DDT 1.0 (002)`, followed by the established utility identification block.
This example specifies formatting; it does not assign a new identity.

## Assignment and affected inputs

Assign one new revision when accepting changed executable work for publication
in the repository. One change set advances each affected component once,
regardless of compilation count. Identical rebuilds and documentation/test-only
changes do not advance executable revisions. A version change does not reset
the revision sequence.

Maintain source and build dependencies for each component. Shared-input changes
trigger examination and rebuilding of consumers; unrelated repository changes
do not advance their revisions. An affected component whose executable remains
identical needs no advance. Compare candidate and reference artifacts using
the existing revision value before generating final artifacts with a new value;
the generated counter must not trigger a further increment. Preserve the actual
qualified reference bytes and checksums.

Relevant inputs include source generators, shared includes, selected metadata,
configuration and build tools. Dependency selection must be granular: reading
one registry entry must not make every other entry an executable dependency.
Automation identifies affected components and checks revision updates; ordinary
compilation never increments counters automatically.

## Variants and toolchains

Use one revision sequence per component. Record target and profile separately.
A Model 4 BIOS change advances BIOS; unchanged variants may retain their prior
artifacts and identities. Consequently, a disk manifest records the identity of
the artifact actually included, rather than copying the latest registry row.

Record toolchain identities and build configuration in build manifests. If a
toolchain or configuration change changes an executable being published,
advance that component's revision. Identical executable bytes need no advance.
Different targets/profiles remain distinguishable by their manifest fields and
artifact checksums even where they share a version and revision.

## Development builds

When relevant inputs differ from the recorded inputs for an assigned revision,
append `-dev`, for example `DDT 1.0 (002-dev)`. This includes committed changes
awaiting revision assignment as well as uncommitted relevant changes. Unrelated
working-tree changes do not mark the component as modified. Build reports carry
a full input fingerprint to distinguish builds sharing the visible suffix;
the suffix alone is not an exact development identity.

## Registry and build preparation

Maintain one authoritative component registry for version, revision, optional
API version and dependency ownership. Generate banners, module-header version
fields and assembler includes from it. Native and cross builds consume the same
prepared identities. Native source disks include prepared metadata so building
does not require Git.

Keep the current repository commit outside ordinary executable banners and
embedded revision data. Record it in the build manifest, with relevant input
fingerprints for modified builds. Embedding HEAD into every executable would
change unrelated binaries after each commit. A cached artifact retains its
original build provenance when reused in a later disk assembly.

Checked carrier compatibility identifiers retain their separate runtime role.
They must not replace component revisions in utility identification. Their
dependency effects require examination during implementation; broad checked
input closures are not a substitute for independent component tracking.

## Tracking boundaries and initial ownership

Track the five subsystems, standalone utilities and independently loadable
modules independently. Internal helpers inherit their owning component's
identity; manifests still record checksums for each artifact. Shared libraries
affect consumers and receive independent user-facing revisions only when
distributed independently.

| Source/product family | Initial identity owner | Treatment |
| --- | --- | --- |
| BDOS service implementation | BDOS | Independent subsystem |
| Platform BIOS, boot stages and hardware initialization | BIOS | Platform recorded separately |
| CCP, CCP reload and command-loading machinery | CCP | Internal products inherit CCP identity |
| CPX facility and carrier handling | CPX facility | Separate from CPX.COM and RCP.CPX |
| RSX facility, loaders and resolvers | RSX facility | Internal products inherit RSX identity |
| R3PACK.RSX and its fifteen helper slots | RSX facility | Container/helper checksums recorded separately |
| CPX.COM and RSX.COM | Respective utility | Independent of facility version |
| RCP.CPX | RCP | Resident commands share package identity |
| Independent transient commands | Respective utility | Shared source dependencies still apply |
| Clock/terminal providers, screen backends, BATCHIO.RSX | Respective loadable module | Independent module identities |
| Shared UI, query, codec and file adapters | Consuming components | No separate counter while not independently distributed |
| Configuration data, catalogs and startup scripts | Disk/build manifest | Record exact inputs and checksums |

This is the accepted initial ownership map, not a completed file-level dependency
registry. Mixed subsystem sources and shared boot/loading machinery require
explicit attribution during implementation. Carrier schema/API versions must
not be mistaken for implementation versions.

## Migration

Preserve existing utility counters numerically. Rename their meaning from build
to revision without claiming compilation counts. Start newly tracked components
at 001 and record when tracking began; do not reconstruct unsupported history.
Audit conflicting existing identities individually before selecting canonical
values. In particular, RCP's central utility identity and carrier version differ.

Preserve frozen core 1.0 at
`3b2d2d7f4fe0472438465165f11fb550d79c8662`, its component combination and all
historical qualification records. Later revision tracking must not rewrite them.
Verify current repository state when implementing migration; this document does
not assign starting values to components added or changed elsewhere.

## Core development reporting

Until another core is explicitly frozen and named, report
`BetterCP/M development (after core 1.0)` for development beyond the baseline.
Reserve unqualified Core 1.0 identification for the frozen combination. Package
1.0 remains independently in progress; its core selection remains undecided.

## Build and release manifests

Generate manifests from actual artifacts and their build records. Include:

- exact core identity or explicit development status;
- included component versions/revisions and applicable API versions;
- full repository source commits and relevant input fingerprints;
- target/profile, configuration, toolchain identities and artifact checksums.

Avoid circular provenance/checksums through this order:

1. Build components and record their identities, provenance and checksums.
2. Assemble the disk, optionally including a component inventory.
3. Write an external disk manifest containing the completed disk checksum.
4. Reference exact disk manifests and their checksums from the package manifest.

An on-disk inventory must not claim to contain its enclosing disk's final
checksum. Build output, generated fingerprints and final manifest checksums
must not feed back into their own identity inputs.

Frozen System and Utilities disks are immutable. A replacement receives a new
disk revision; updating a utility never silently changes an existing disk or
package release. Do not infer qualification from a version or checksum alone.

## Implementation review boundary

Before changing counters or executable output, review the file-level dependency
map, migration conflicts, variant handling and development fingerprint rules.
Then qualify generated metadata and native/cross identities with focused tests.
This policy record itself changes no executable or frozen artifact.
