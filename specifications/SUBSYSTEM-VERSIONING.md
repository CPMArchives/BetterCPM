# BetterCP/M subsystem versioning convention

Status: adopted

This specification defines how BetterCP/M identifies the versions of the
operating system and its independently evolving subsystems. It adds release
identification only; it does not change subsystem boundaries, interfaces, or
runtime behavior.

## Version identities

BetterCP/M has a system release version. Each completed subsystem also has an
implementation version. A subsystem that exposes a defined boundary to other
components, extensions, applications, or machine-specific code additionally
has an interface version.

- **System release version** identifies a complete BetterCP/M distribution.
- **Interface version** identifies a public contract: entry points, calling
  conventions, data structures, binary formats, or other externally observable
  requirements.
- **Implementation version** identifies a particular implementation of a
  subsystem, including compatible fixes and internal changes.

An implementation version may change without changing its interface version.
An interface version changes only when its public contract changes. Code must
not infer the version or presence of one subsystem from the BetterCP/M system
release version or from the version of another subsystem.

## Number format and increments

Released identities use `major.minor`. Development builds may append a third
patch number and a development suffix when useful, for example
`1.1.1-dev3`. The following rules apply independently to every identity:

- increment **major** for an incompatible public-interface or persisted-format
  change;
- increment **minor** for a backward-compatible interface addition, or for a
  material implementation release that preserves the interface;
- increment **patch** for a compatible corrective implementation release when
  patch-level tracking is needed;
- development suffixes identify prerelease iterations and are not interface
  versions.

An implementation supporting interface `1.0` must continue to satisfy the
complete `1.0` contract. A compatible extension may advertise a later minor
interface version. Consumers must reject an unsupported major version and must
not assume that an unknown minor addition is present.

## Ownership and reporting

The component that owns a public boundary owns its interface version. In
particular:

- the CCP owns the command-environment interface;
- the CPX facility owns the CPX interface and loadable-module format;
- the BDOS owns the BDOS entry and service interface;
- the RSX facility owns the RSX interface, chain rules, and loadable-module
  format;
- the BIOS owns the BIOS API presented to the system above it.

Build and regression records should report the system release plus the
interface and implementation versions of affected subsystems. A concise record
may take this form:

```text
BetterCP/M 0.3; CCP impl 1.1 / API 1.0; BDOS impl 1.1 / API 1.1;
BIOS impl 1.0 / API 1.0; CPX impl 1.0 / API 1.0;
RSX manager impl 1.0 / API 1.0
```

The normative current assignments are maintained in
`metadata/subsystem-versions.tsv`. Source banners, binary metadata, build
manifests, and release notes must agree with that matrix when they expose a
version. A change to a subsystem version and the corresponding matrix entry
belong in the same change set.

The build generates `src/bdos/versions.inc` from the fixed CCP, BDOS, and BIOS
rows. BetterCP/M BDOS Function 206 returns a pointer to that immutable
version-1 runtime descriptor for `VER /V`. CPX and RSX facility versions are
generated from the same matrix into their owning `CPX /V` and `RSX /V`
commands. Runtime commands must not carry hand-maintained version values.

## Scope

Only completed components receive released assignments. Planned facilities,
including the RTC BIOS extension and Extended Services RSX, remain unassigned
until their first interfaces and implementations are completed. Their eventual
initial versions need not match the versions of the BIOS, BDOS, or RSX facility
that hosts them.

The executable conformance utilities are separately released development
tools. Their existing per-utility versions remain independent of BetterCP/M
subsystem versions.
