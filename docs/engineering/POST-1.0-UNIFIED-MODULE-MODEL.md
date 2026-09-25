# Post-1.0 Unified User-Facing Module Model

## Status

This document records an area for post-1.0 architectural investigation. It is
not an approved interface, file format, command name, filename convention, or
implementation requirement. It does not change the frozen BetterCP/M 1.0 RSX,
CPX, loader, carrier, reconstruction, or command contracts.

## Question

BetterCP/M exposes two extension mechanisms whose distinction is architecturally
important:

- an RSX occupies protected resident memory and remains callable while a
  transient program uses the TPA; and
- a CPX belongs to the reclaimable command environment and is reconstructed
  with that environment after a transient program returns.

These terms describe lifetime, placement, and reconstruction. A later release
should investigate whether ordinary users need to choose the corresponding
class-specific manager when installing a component, or whether one generic
module-management interface can inspect the object and delegate to the existing
RSX or CPX machinery.

The investigation must preserve four independent properties:

1. **Placement and lifetime:** how and where the component lives, currently RSX
   or CPX.
2. **Functional role:** what the component provides, such as commands, flow
   control, clock service, I/O service, or namespace service.
3. **Interoperability ABI:** the standardized interface used only where
   independently developed providers and consumers must communicate.
4. **Human-facing name:** an optional filename convention that helps a person
   recognize the component.

The governing principle is:

> RSX or CPX defines how and where a component lives. Its functional role
> describes what it provides. An ABI defines a standardized interface only
> where interoperability requires one. A filename may describe the component
> to a person but is not authoritative metadata.

## Candidate direction

A future generic module manager could identify the carrier from validated
on-disk contents, determine its placement and lifecycle class, and submit the
operation to the class-specific transactional manager. This would be a
user-interface layer over the existing mechanisms, not a replacement for their
different allocation, reconstruction, validation, or rollback rules.

The present BCPX and BRSX carriers already establish useful groundwork. They
have distinct signatures, versions, and module-class fields that a bounded
inspector can recognize before execution. A future design should first decide
whether these existing fields are sufficient. It must not add a second package
framework or duplicate authoritative metadata without a demonstrated need.

Possible later metadata includes module identity, carrier version, placement
class, implemented service ABI and version, capabilities, memory requirements,
or dependencies. None of those fields is approved by this proposal. Every byte
must have a concrete loader, interoperability, diagnostic, or user benefit.

## Functional roles and ABIs

Functional categories must remain independent of placement. A command package
or flow-control package could naturally be a CPX, while a clock or I/O provider
could naturally be an RSX because it must remain callable during transient
execution. A later implementation may choose differently when its actual
lifetime requires it.

A role does not by itself justify an ABI. Commands can use the established CPX
command-dispatch contract without inventing a separate resident-command ABI.
Flow-control facilities similarly need a dedicated ABI only if independent
components must invoke or replace them through a stable boundary. Clock support
is the counterexample already present in BetterCP/M: independently replaceable
hardware providers and consumers require the native TIME service contract.

The project should continue to define ABIs in response to demonstrated
interoperability boundaries rather than pre-allocating a hierarchy of plugin
classes.

## No fixed functional package regions

This investigation must not introduce Z-System-style fixed holes for RCP, FCP,
IOP, NDR, or other anticipated package categories. BetterCP/M charges protected
memory for the RSXs actually installed and reconstructs CPXs in the reclaimable
command environment. A functional label must not reserve a maximum-size region,
reduce the TPA while unused, or limit later components to categories predicted
in advance.

The useful part of specialized package vocabulary is the human description of
a role. Its memory-placement consequences are deliberately not imported.

## Filename conventions

A later distribution may adopt optional extensions such as `.CLK`, `.IOP`,
`.FCP`, or `.CMD` when real packages make them useful. These examples reserve
nothing and approve no vocabulary. In particular, an extension must not decide:

- whether the object is an RSX or CPX;
- where it is loaded;
- which interface it implements;
- how it is validated; or
- what behavior it provides.

Renaming a supported module must not change the meaning derived from its
validated contents. The loader must reject an unrecognized or inconsistent
carrier rather than infer its class from a suffix.

Arbitrary role-oriented extensions are not supported by the current persistent
profiles. CPX reconstruction records retain an eight-character stem and supply
`.CPX`; the RSX path similarly uses its class-specific filename convention.
Supporting another extension across WBOOT or cold boot would therefore require
an explicit profile-format and compatibility decision. It must not be presented
as a property of the 1.0 implementation.

The generic command name is also unresolved. `LOAD.COM` is the historical CP/M
utility that converts Intel HEX input into a COM image and remains in the
candidate BetterCP/M utility inventory. A future module manager must avoid an
ambiguous collision with that utility or make a deliberate compatibility
decision. The spelling `LOAD` in examples is illustrative only.

## Investigation questions

Before approving an implementation, answer these questions with measured costs
and compatibility evidence:

1. Can the generic inspector safely distinguish every supported BCPX and BRSX
   carrier using the existing header fields before invoking either manager?
2. Can the interface delegate to the current transactional managers without
   weakening validation, ordering, rollback, recovery, or reconstruction?
3. Is a generic interface materially simpler for users than the class-specific
   commands, and what command name avoids conflict with historical `LOAD.COM`?
4. Do role-oriented filename extensions provide enough benefit to justify
   changing persistent profile records and native build/package tooling?
5. Which functional roles have real interchangeable providers and consumers
   that require a service ABI? Roles without that requirement receive no new
   ABI.
6. What is the smallest self-description required, and can it extend the
   existing carriers compatibly rather than replace them?
7. What RAM, disk, native-toolchain, startup, recovery, and compatibility costs
   would the feature impose?

## Acceptance boundary

Recording this investigation creates no 1.0 work. BetterCP/M 1.0 continues to
use its frozen BCPX and BRSX carriers, class-specific managers, profiles, and
interfaces. Necessary 1.0 fixes must not be expanded into a generic module
framework.

A later proposal may advance only after it identifies concrete user workflows,
audits the then-current carriers and managers, resolves the command-name and
profile-format questions, and demonstrates that the common layer preserves the
distinct RSX and CPX lifecycle guarantees.
