# BetterCP/M RSX and CPX Programmer's Guide

Status: Initial working draft  
Date: 2026-09-02

This guide describes how resident extensions and command-processor
extensions fit into BetterCP/M. It records the decisions already made and
identifies interfaces that remain provisional. It is intended to become the
programming reference for extension authors as the loader and module formats
are implemented.

## 1. Two extension classes

BetterCP/M defines two distinct kinds of extension.

### 1.1 Resident System Extension (RSX)

An RSX intercepts, supplements, or provides operating-system services. Its
normal boundary is the BDOS call path. Possible RSXs include foreign
filesystem translators, networking, print spooling, device services,
redirection, auditing, and other facilities that must be available to
applications independently of the current command processor.

An RSX is not a command-language package. An RSX may expose management
operations used by commands, but its defining role is service extension.

### 1.2 Command Processor Extension (CPX)

A CPX extends command interpretation. Possible CPXs include aliases,
additional commands, command search rules, named-directory facilities,
command history, and ZEX-like scripting with conditionals and control flow.

A CPX does not become an RSX merely because it is memory-resident. Its
lifetime and interface belong to the command environment, not to BDOS
service dispatch.

## 2. Memory organization

The intended high-to-low ordering is:

```text
High memory
BIOS and hardware-dependent resident state
Core BDOS and System Services
Persistent system DATA
RSX chain
Dynamic CP/M compatibility gateway
CPX chain
CCP core
Transient Program Area
Low memory
```

The BIOS and core BDOS remain fixed. Persistent system DATA and installed
RSXs occupy protected memory below them. The dynamic gateway is the lowest
protected address and therefore the exclusive TPA ceiling advertised through
the jump at `0005h`. CPXs and the CCP occupy reclaimable command-environment
memory below that gateway and may be overwritten by a transient program.

Extension space is charged according to the modules actually configured.
BetterCP/M shall not permanently reserve the maximum possible RSX or CPX
footprint. Installed RSXs reduce the TPA because they must remain callable by
transient programs. CPXs do not reduce the transient TPA because WBOOT can
reconstruct them.

The fixed system begins at `C000h` and publishes the active layout through a
versioned descriptor at `C080h`. With no RSXs, the first movable three-byte
compatibility gateway occupies `BFFDh..BFFFh`. The current 1,116-byte CCP
rounds to five pages and is calculated at `BAFDh`; its address is not an ABI.
The Model 4 WBOOT reloader reads the persistent CPX reconstruction table,
loads and links each relocatable CPX below `BFFDh`, and then calculates,
restores, and relocates the CCP beneath the CPXs. Page zero advertises the
dynamic gateway at `BFFDh` as the exclusive TPA ceiling.

## 3. Fundamental address rule

The saved RSX and CPX profiles are persistent configuration; their current
memory addresses are not. Persistent DATA also contains the active RSX table
and the active CPX reconstruction table. The latter records which CPXs WBOOT
must restore, not where their overlay images previously happened to reside.

Extension code must therefore be relocatable or position-independent. An
extension must not publish an address that it expects to remain valid after
the extension configuration changes. Raw pointers into an old RSX, CPX, or
CCP image expire when the affected region is reconstructed.

Loading or unloading an RSX can move the dynamic gateway and requires the
CPXs and CCP below it to be reconstructed. Loading or unloading a CPX can
move later CPXs and the CCP, but does not change the transient TPA ceiling:
the entire command environment remains reclaimable.

## 4. Dynamic configuration

Like Z-System packages, BetterCP/M RSXs and CPXs are intended to be loadable
and unloadable when needed. A change is performed as a transactional rebuild,
not by shifting executing code in place.

The planned sequence is:

1. An installer requests a new ordered RSX and CPX configuration.
2. BetterCP/M locates every requested module and validates its type, ABI,
   size, dependencies, and relocation information.
3. It computes the complete prospective memory map and TPA ceiling without
   altering the running system.
4. It rejects the request if the configuration is invalid or cannot fit.
5. Extensions that retain migratable state are asked to export that state.
6. A controlled RSX reconfiguration reconstructs the protected RSX region
   and moves the dynamic compatibility gateway.
7. Warm boot normally preserves the active RSXs and gateway, and relocates
   and loads the active CPX set from its persistent reconstruction table.
8. It reloads the CCP beneath the CPXs.
9. It initializes the chains, imports approved state, and publishes the new
   TPA ceiling only after reconstruction succeeds.

Failure before publication leaves the former configuration active. Failure
during reconstruction must enter a defined recovery path rather than expose
a partially linked chain.

An RSX-only change necessarily reconstructs the CPX and CCP regions because
the gateway and their addresses may change. A CPX-only change leaves the RSX
chain and gateway in place, but reconstructs the affected CPXs and CCP
beneath it. An ordinary WBOOT preserves RSXs and restores the complete command
environment from the active CPX reconstruction table.

Configuration changes shall occur from a controlled command or warm-boot
path. They shall not relocate the command environment while arbitrary
transient application code is executing.

## 5. Module file information

The final on-disk module format is not yet defined. It is expected to contain
at least:

- a file signature and module-format version;
- module class: RSX or CPX;
- module name and module version;
- required BetterCP/M ABI version;
- required and optional capabilities;
- code, data, workspace, and alignment requirements;
- initialization and shutdown entry offsets;
- dispatch entry offsets;
- relocation records or a declaration of position independence;
- dependency and ordering information;
- state-export and state-import entry offsets, when supported; and
- integrity information sufficient to reject a damaged module.

Entry points should be stored as offsets within the module image until the
loader relocates the module. The file format must be practical to produce
with a native CP/M toolchain. BetterCP/M source modules should remain
assemble-able with ZSM4; cross-build tooling may generate the same module
image when it produces byte-identical results.

## 6. RSX execution model

The final RSX ABI has not yet been implemented. The architecture requires the
BDOS entry path to permit an ordered RSX chain before control reaches the
core BDOS dispatcher.

An RSX must be able to:

- recognize calls that it owns;
- handle, modify, or reject an owned request;
- pass an unowned request to the next RSX or core BDOS;
- invoke defined lower-level services without recursively intercepting itself;
- distinguish initialization and shutdown from ordinary dispatch; and
- preserve the application-visible CP/M calling convention unless an
  explicitly BetterCP/M-specific service defines otherwise.

The exact register convention, call-frame representation, chaining order,
reentrancy rules, error propagation, and bypass interface remain to be
specified before the first RSX is implemented.

RSXs remain part of the system-service environment when the CCP and CPXs are
reloaded. They must not depend upon private CCP or CPX data.

## 7. CPX execution model

### 7.1 Implemented bring-up dispatcher

The current CCP implements a small forward chain. Its four-byte in-memory
header is:

```text
offset  size  meaning
0       2     address of next CPX header, or zero
2       2     command-entry address
```

The command-entry contract is presently:

- `DE` points to the upper-case command text;
- `B` contains the command length;
- carry set on return means that the CPX handled the command;
- carry clear means that the CPX declined it; and
- `SP`, `IX`, `IY`, and the command buffer must be preserved.

Ordinary registers other than those explicitly preserved may be changed.
Core compatibility-resident commands are recognized before CPX dispatch. If
all CPXs decline a command, the CCP performs its normal `.COM` lookup.

This interface is executable and tested, but CPX header addresses are active
configuration details. The chain-head field has a stable location in the
versioned descriptor. There is not yet an on-disk CPX
loader, installer, removal command, discovery call, or ABI-version check.

### 7.2 Planned relocatable CPXs

A loadable CPX will use offsets in its file header and will be relocated to
the address selected during command-environment reconstruction. A CPX must
not assume that it will return to the same address after warm boot.

The final CPX ABI must additionally define:

- initialization and shutdown calls;
- access to the CCP command context through a versioned interface;
- whether and how a CPX may replace or filter core commands;
- facilities for invoking another command without uncontrolled recursion;
- parser ownership for compound commands and scripts;
- error and abort propagation;
- output and diagnostic conventions; and
- capability discovery by other CPXs and transient utilities.

## 8. State and relocation

Most extension state should be reconstructible from configuration or disk
files. An extension should prefer reinitialization over retaining opaque
memory across relocation.

If an extension genuinely requires state migration, it shall use explicit
export and import operations. Exported state must not contain unrelocated raw
pointers. The module format or ABI must describe the state version so that a
new module version can reject or translate incompatible state.

RSX state is independent of the command environment. CPX state belongs to the
configured command environment. Unloading an extension normally discards its
private state after its shutdown operation completes.

An extension must not retain pointers to:

- another extension's private image;
- a CCP-private buffer;
- transient-program memory after the transient has terminated; or
- temporary loader storage after initialization.

Shared information must be obtained through a documented, versioned
interface or a capability specifically designed to survive reconstruction.

## 9. Ordering and dependencies

Chain order is observable whenever more than one extension can recognize the
same operation. Configuration must therefore preserve an explicit order.

A module may declare that it:

- requires another named module or capability;
- must precede or follow another module class or capability;
- conflicts with a module or capability; or
- can operate in any order.

The loader must reject dependency cycles, unsatisfied requirements, and
irreconcilable ordering constraints before modifying the active system.

The initial CPX dispatcher gives required core CCP commands precedence over
CPXs. A future facility that intentionally overrides core commands must be
explicitly configured rather than arising accidentally from chain order.

## 10. Resource accounting

Every module shall declare or permit the loader to determine its complete
resident cost. This includes code, initialized data, uninitialized workspace,
alignment padding, headers, chain links, and any loader-maintained state.

Before activation, the installer should report:

- the old and proposed RSX footprints;
- the old and proposed CPX footprints;
- the old and proposed CCP base;
- the old and proposed TPA ceiling; and
- whether the change requires state loss or a full extension rebuild.

No module may be activated if doing so would overlap the TPA, another resident
component, hardware-mapped memory, or a compatibility-visible reserved area.

## 11. Compatibility and failure rules

An installed extension must not silently change behavior required by the
CP/M 2.2 compatibility contract unless the user has explicitly selected an
incompatible environment.

Unknown BDOS calls and unrecognized commands must continue through their
chains. A module must never claim an operation merely because it does not
understand it.

Initialization must either succeed completely or leave the extension absent.
Shutdown must release owned hooks and resources. A damaged or incompatible
module must be rejected before execution.

The system must retain a recovery configuration capable of booting without
optional extensions. A failed optional module must not make the system disk
permanently unbootable.

## 12. Items still to specify

The following are deliberately open:

- the relocatable module-file encoding;
- the final RSX dispatch and bypass ABI;
- the expanded, versioned CPX ABI;
- loader and configuration command syntax;
- module discovery and enumeration services;
- persistent configuration storage;
- state-export and state-import representation;
- dependency identifiers and version constraints;
- recovery and rollback storage;
- authentication or integrity requirements beyond damage detection; and
- interaction with future bank-switched memory.

These details shall be fixed by engineering specifications and executable
tests before third-party binary compatibility is promised.
