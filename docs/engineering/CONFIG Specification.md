# BetterCP/M CONFIG.COM Engineering Specification
**Version 1.0 — Revised engineering baseline; alignment in progress**

This document is the current CONFIG engineering baseline. Alignment is in
progress; proposed runtime extensions remain subject to their explicit audit
gates. Existing storage, active/pending/saved and verification contracts remain
authoritative. See [alignment qualification](CONFIG%20Specification%20Alignment.md)
for implemented behavior, remaining gaps and evidence.

## 1. Purpose

`CONFIG.COM` is the BetterCP/M system configuration utility.

CONFIG provides a common interface for machine-level configuration that must persist across cold boots. It manages both settings already supported by BetterCP/M and selected extensions planned for 1.0.

CONFIG is not a universal preferences editor and is not responsible for runtime administration of unrelated subsystems such as RSXs, monitor personalities, or keyboard mappings.

A design goal for CONFIG is:

> Every setting exposed interactively should also have an equivalent command-line form so that configuration can be reproduced from SUBMIT.

For settings where command-line support does not yet exist, that support is new implementation work.

---

# 2. Configuration-state model

CONFIG must preserve the existing BetterCP/M distinction between:

1. **Active settings** — values currently in effect.
2. **Pending changes** — modifications made in CONFIG but not yet committed.
3. **Saved defaults** — persistent values used at the next applicable startup or initialization.

CONFIG must not replace this model with a single undifferentiated candidate image.

Existing save scopes remain authoritative, including the distinction between:

- saving pending changes;
- saving all current settings as defaults.

New CONFIG-managed settings should fit this model where meaningful.

Some configuration domains may not support immediate activation. In those cases the active value remains unchanged while the new value is saved for the next cold boot or subsystem initialization.

---

# 3. Persistent storage model

CONFIG presents one coherent configuration interface, but BetterCP/M does **not** require all CONFIG-managed state to live in one physical configuration record.

Existing storage contracts remain valid.

In particular:

- startup configuration continues to use the existing BCST mechanism;
- drive configuration continues to use its existing storage contract;
- other domains may use the persistent representation appropriate to their subsystem.

CONFIG must not introduce a new unified configuration format merely for conceptual neatness.

Each persistent domain must nevertheless provide:

- format/version identification where applicable;
- validation;
- error detection;
- verified writes;
- recovery or rollback where supported.

CONFIG saves are not guaranteed to be power-loss atomic.

The required guarantee is:

> CONFIG validates changes before saving, verifies completed writes, and attempts rollback on save failure where the storage mechanism permits.

A power interruption during a save may still require recovery.

---

# 4. 1.0 scope and status

CONFIG functionality falls into three categories.

## 4.1 Existing architecture

These configuration domains already exist conceptually or structurally and remain part of CONFIG:

```text
STARTUP
DRIVE
```

## 4.2 Proposed 1.0 extensions pending runtime-cost qualification

These are desirable CONFIG additions but require auditing of the corresponding resident/runtime support before they become firm 1.0 commitments:

```text
IOBYTE defaults
PRINTER
SERIAL
```

The transient CONFIG utility itself is not the primary cost concern. The audit must determine what persistent resident code and state are required for the configured behavior to remain effective after CONFIG exits.

## 4.3 Explicitly outside CONFIG 1.0

```text
Keyboard remapping
Keyboard macros
Keyboard diagnostics

Monitor personality selection
Monitor RSX administration
Clock-provider administration
General RSX loading/unloading/status

Search paths
Named directories

CCP aliases
Command history
Per-utility preferences
```

Search paths and named directories are deferred until after 1.0. Their eventual management may belong to CONFIG, dedicated `PATH` and `NDR` commands, or both.

---

# 5. Invocation

Interactive mode:

```text
CONFIG
```

Command-line mode performs a specified configuration or inspection operation.

The intended long-term command set includes forms such as:

```text
CONFIG /SHOW
CONFIG /STARTUP="SUBMIT STARTUP"
CONFIG /PRINTER:TABS=EXPAND
CONFIG /SERIAL:1 BAUD=9600
CONFIG /VER
```

Exact syntax for settings not yet implemented remains part of their implementation work.

---

# 6. `/VER`

`/VER` follows the standard BetterCP/M standalone version convention.

```text
CONFIG /VER
```

Output:

```text
BetterCP/M CONFIG 1.0 (Build nnn)
```

`/VER` combined with any other CONFIG operation is invalid.

---

# 7. Interactive interface

CONFIG must remain usable on a basic CP/M console.

It must not require:

- the monitor RSX;
- cursor-addressable terminal control;
- a particular terminal personality.

The user interface may take advantage of richer terminal facilities when available, but a plain-console path must remain functional.

A conceptual top-level organization is:

```text
BetterCP/M System Configuration

  Logical Devices
  Startup
  Printer
  Serial Ports
  Disk Drives

  Save
  Quit
```

Only domains actually implemented on the current build/platform are shown.

If printer, serial, or persistent IOBYTE support does not qualify for 1.0, CONFIG must not present nonfunctional menu entries for them.

---

# 8. Save semantics

CONFIG must preserve the existing save model.

Interactive edits become pending changes.

CONFIG distinguishes between:

- applying a setting to the current system where supported;
- leaving a setting pending;
- saving pending settings as persistent defaults;
- saving all current settings as persistent defaults where the existing CONFIG semantics permit that operation.

Existing CONFIG terminology and menu behavior should be retained where practical rather than replaced by new vocabulary.

A failed save must not be reported as successful.

If persistent write verification fails, CONFIG must attempt the rollback/recovery procedure defined by that storage domain.

---

# 9. Command-line parity

Every interactive setting should ultimately have a command-line equivalent.

This is especially important for reproducible configuration through `SUBMIT`.

Command-line invocations must:

1. parse the entire request;
2. validate all supplied values;
3. check platform/backend capability;
4. construct the requested changes;
5. apply/save them according to the appropriate state model.

Before each command-line operation is frozen, its contract must state whether
it applies live changes, saves defaults, or performs both. Pending state private
to a CONFIG invocation must not be implied to survive after the utility exits.

No setting should be partially changed merely because parsing failed later in the same command.

Where the underlying persistent mechanism cannot provide full transactional atomicity, CONFIG must still avoid intentional partial application and must report save failures accurately.

---

# 10. Startup configuration

Startup configuration is an established CONFIG responsibility.

BetterCP/M stores the cold-start command using the existing BCST mechanism.

## 10.1 Distribution default

The normal distribution default is:

```text
SUBMIT STARTUP
```

Development and test images may deliberately ship with startup execution disabled.

Therefore `SUBMIT STARTUP` is the **distribution default**, not an invariant built into every image.

## 10.2 Execution semantics

The configured startup command:

- executes once after cold startup;
- does not execute on an ordinary warm boot;
- is submitted through the normal CCP command mechanism;
- may invoke any valid CCP command;
- uses the ordinary command-tail limit.

CONFIG changes the stored startup command. It does not execute the new command merely because it was edited.

## 10.3 Disabled startup

An empty configured command means:

```text
no automatic startup command
```

This is valid.

## 10.4 Command-line form

Intended syntax:

```text
CONFIG /STARTUP="command line"
```

Examples:

```text
CONFIG /STARTUP="SUBMIT STARTUP"
CONFIG /STARTUP=""
```

The command text is preserved for later CCP execution. `/STARTUP=` saves only
the startup record for the next cold boot; it does not execute the command or
capture active drive settings. It retains the existing Y/N confirmation and
verified-write/rollback path. Declining returns to the CCP without a change.
An empty quoted string disables startup. The complete tail must validate before
initialization or disk access. Text inside the quotes is command data, including
literal `/VER` tokens. The CCP tail limit includes the option and quote overhead.

---

# 11. Startup banner

CONFIG does not own banner text.

Banner output is provided by transient VER:

```text
:VER /BANNER
```

The leading `:` is required under the current BetterCP/M handoff model because resident VER provides a feature hint rather than automatically handing off to the transient utility.

Thus a typical `STARTUP.SUB` may contain:

```text
:VER /BANNER
```

CONFIG does not duplicate banner settings.

---

# 12. Drive configuration

Drive configuration remains an existing CONFIG domain and retains its established storage and runtime contracts.

CONFIG must not redefine those contracts merely to make them match newer configuration domains.

## 12.1 Responsibilities

CONFIG may manage, as supported by the backend:

- logical-drive availability;
- logical-to-physical drive assignment;
- drive type;
- media-format association;
- backend-specific persistent drive properties.

## 12.2 DISK.FDB relationship

`DISK.FDB` remains the BetterCP/M disk-format database.

CONFIG may select or associate an FDB entry with a drive but does not become an FDB editor or duplicate the FDB catalogue. Saving the selected format’s operational parameters remains permitted where required by the existing drive-storage and boot contracts.

## 12.3 Platform capability

CONFIG must display only properties that the running disk backend actually supports.

The generic utility must not impose Model 4 floppy-controller assumptions on other systems.

Possible backend-defined properties include:

```text
physical drive
drive type
sides
density capability
step characteristics
format profile
```

These are examples, not universal CONFIG fields.

## 12.4 Validation

Drive changes must be validated against the existing drive architecture.

CONFIG must reject configurations that violate backend rules or would make required system storage unusable.

## 12.5 Activation

Some drive changes may be pending until cold boot.

CONFIG must preserve the existing distinction between current, pending, and saved drive configuration.

The exact command-line grammar for drive manipulation remains to be specified against the actual backend interfaces.

---

# 13. Persistent IOBYTE defaults
**Status: proposed 1.0 extension pending runtime-cost audit**

The intended division of responsibility is:

```text
STAT      live/current IOBYTE assignment
CONFIG    persistent cold-boot default
```

CONFIG must not replace `STAT DEV:` or `STAT CON:=...` as the normal live logical-device interface.

## 13.1 Proposed behavior

BetterCP/M already initializes IOBYTE to the compiled cold-boot default `95h`
(CON=CRT, RDR=PTR, PUN=PTP, LST=LPT) and preserves live changes across warm boot.
The proposed extension is persistent user configuration of that default, not
the introduction of cold initialization itself.

If implemented, CONFIG stores the IOBYTE value restored during cold initialization.

Changing the live IOBYTE with STAT does not automatically alter the persistent CONFIG value.

Likewise, changing the saved CONFIG default need not immediately modify the current IOBYTE.

## 13.2 Runtime audit requirement

Before this feature becomes mandatory for 1.0, implementation must determine:

- where the saved IOBYTE default is stored;
- where it is restored during cold boot;
- additional resident bytes required, if any;
- interaction with the existing boot/default architecture.

If the runtime cost is disproportionate, persistent IOBYTE management may be deferred.

## 13.3 Proposed command form

```text
CONFIG /IOBYTE logical=physical
```

Example:

```text
CONFIG /IOBYTE CON:=CRT:
CONFIG /IOBYTE LST:=LPT:
```

Exact grammar remains subject to implementation qualification.

---

# 14. Printer configuration
**Status: proposed 1.0 extension pending runtime-cost audit**

The proposed printer facility is deliberately narrow.

CONFIG would manage only:

```text
line-ending handling
form-feed handling
page length
tab handling
tab width
```

It does not become a general printer-definition system.

## 14.1 Line endings

Proposed settings:

```text
RAW
SUPPRESSLF
```

`RAW` passes CR and LF independently.

`SUPPRESSLF` suppresses an LF immediately following CR.

Proposed command forms:

```text
CONFIG /PRINTER:LINE=RAW
CONFIG /PRINTER:LINE=SUPPRESSLF
```

## 14.2 Form feed

Proposed values:

```text
NATIVE
SIMULATE
```

`NATIVE` passes FF through normally.

`SIMULATE` emits sufficient line feeds to perform page advance according to the configured page length.

## 14.3 Page length

Proposed default:

```text
66
```

Meaningful when FF simulation is active.

The value remains stored when native FF is selected.

## 14.4 Tabs

Proposed modes:

```text
NATIVE
EXPAND
```

`NATIVE` passes TAB to the device.

`EXPAND` converts TAB to spaces.

## 14.5 Tab width

Proposed default:

```text
8
```

Meaningful when software tab expansion is enabled.

## 14.6 Runtime audit requirement

These settings require code in the actual printer-output path.

Before inclusion in 1.0, implementation must measure:

- resident code required for CR/LF tracking;
- page-line state required for simulated FF;
- column state required for software tabs;
- configuration bytes required;
- effect on the 53K unloaded target.

If the cost is excessive, individual transformations may be deferred rather than forcing the entire proposed printer layer into 1.0.

## 14.7 Explicit exclusions

Even if printer configuration qualifies for 1.0, CONFIG will not manage:

```text
margins
headers
footers
printer initialization strings
font/style selection
printer escape sequences
character-set conversion
```

---

# 15. Serial configuration
**Status: proposed 1.0 extension pending runtime-cost and backend audit**

BetterCP/M's generic configuration model may support up to eight logical serial ports.

This is a maximum architecture limit, not a claim that every platform has eight ports.

CONFIG must expose only ports supplied by the active backend.

## 15.1 Proposed per-port settings

```text
Baud
Data bits
Parity
Stop bits
CTS
DSR
XON/XOFF
```

## 15.2 Baud vocabulary

CONFIG may recognize:

```text
110
300
600
1200
2400
4800
9600
19200
38400
57600
115200
```

The backend remains authoritative.

Only actually supported rates may be selected.

CONFIG must never approximate an unsupported rate by silently choosing another.

## 15.3 Data bits

Possible values:

```text
5
6
7
8
```

The backend may expose fewer.

## 15.4 Parity

```text
NONE
ODD
EVEN
```

## 15.5 Stop bits

```text
1
2
```

## 15.6 Flow control

Proposed settings:

```text
CTS=ON|OFF
DSR=ON|OFF
XONXOFF=ON|OFF
```

Hardware flow-control fields are displayed only when the backend provides them.

## 15.7 Proposed command syntax

```text
CONFIG /SERIAL:1 BAUD=9600
CONFIG /SERIAL:1 DATA=8 PARITY=NONE STOP=1
CONFIG /SERIAL:1 CTS=ON DSR=OFF XONXOFF=ON
```

## 15.8 Active/pending/saved behavior

Where the serial backend supports live reconfiguration, CONFIG may apply a valid change immediately.

Where it does not, the new value remains pending or saved for later initialization.

CONFIG must accurately report which state applies.

## 15.9 Runtime audit requirement

Before serial configuration becomes mandatory 1.0 scope, implementation must audit:

- current serial-driver configuration state;
- required resident storage;
- flow-control implementation cost;
- XON/XOFF state-machine cost;
- supported Model 4 hardware values;
- generic backend API implications.

In particular, adding a CONFIG field does not by itself justify new resident serial functionality.

---

# 16. `/SHOW`
**Status: drive/startup inspection implemented in Build 004; distribution reference-file integration included**

A command-line inspection facility is desirable:

```text
CONFIG /SHOW
```

It should report CONFIG-owned settings without altering them.

It must distinguish state where relevant, rather than pretending that saved defaults and active settings are necessarily identical.

For example, where pending differences exist, output may need to represent:

```text
Active
Pending
Saved
```

rather than printing one ambiguous value.

`/SHOW` is not a general system-information command.

It must not accumulate unrelated information such as:

- loaded RSXs;
- monitor personality;
- clock-provider state;
- keyboard state.

Those remain the responsibility of their respective utilities.

Build 004 reports active physical profiles, active logical bindings, the saved
cold-start command and the absence of private pending changes in this new
invocation, then separately reports saved physical profiles and logical bindings.
It reuses the existing CONFIG save-all reference/header/geometry/carrier
validation through the read-only point. It does not fetch active state into the
proposed carrier, activate saved settings, ask for confirmation, or enter writes.
The matching `A:SYSGEN.DAT` reference is required; missing/invalid/mismatched
references or recoverable read errors produce the existing diagnostic and return
without printing unverified saved drive values. Previously printed active and
startup information remains valid. The editable table fields are copied to
private transient storage before restoring the shared FDB catalogue workspace.
`/SHOW` does not modify settings or require completion keypresses.

The maintainer approved including the required platform/build-specific
SYSGEN.DAT on both System Disks. The builders emit the same reference used by
their development images, including in the cpmsim system-tracks-only path.

---

# 17. Defaults/reset facility
**Status: proposed new CONFIG work**

A mechanism for restoring CONFIG-managed settings to platform/distribution defaults may be useful, but it must respect the existing domain storage architecture and save-state model.

A proposed command is:

```text
CONFIG /DEFAULT
```

Maintainer decision: `/DEFAULT` loads defaults into private pending state only.
It does not immediately activate or save them. The operator remains in the
interactive session and uses explicit activation/save operations. It must not
exit while implying that invocation-private pending state will survive.
Default sources and supported-domain coverage must be specified and qualified
before this operation is implemented. `/DEFAULT` remains unimplemented.

It must not bypass CONFIG's established active/pending/saved distinctions.

Therefore `/DEFAULT` remains provisional until its semantics are reconciled with the existing CONFIG model.

---

# 18. Failure handling

CONFIG must never knowingly claim that a failed save succeeded.

The required save process for each persistent domain is:

1. validate requested changes;
2. perform the domain's normal save operation;
3. verify the written data;
4. attempt rollback or restoration if verification fails and the domain supports it;
5. report the outcome accurately.

CONFIG does not promise power-loss atomicity.

A system losing power between physical writes may still contain an incomplete or damaged configuration record.

Startup code and CONFIG should detect invalid stored data wherever the corresponding storage contract provides validation information.

---

# 19. Runtime architecture rule

A transient CONFIG utility cannot make runtime functionality free.

Any setting whose effect must continue after CONFIG exits requires support in the subsystem that consumes it.

Therefore every proposed CONFIG feature must be evaluated in terms of both:

```text
CONFIG.COM transient cost
```

and:

```text
resident/runtime cost
```

This applies particularly to:

- printer transformations;
- serial flow control;
- persistent IOBYTE restoration.

No feature should be accepted merely because its CONFIG interface is small.

---

# 20. RSX and subsystem boundary

CONFIG does not administer runtime RSXs.

Dedicated RSX utilities already provide the appropriate controls for RSX loading, unloading, inspection, and provider management.

Startup selection of such facilities belongs naturally in `STARTUP.SUB`.

For example:

```text
:VER /BANNER
RSX ...
...
```

CONFIG's role is only to preserve the configured startup command that causes the script to run.

This avoids duplicating subsystem-specific interfaces inside CONFIG.

---

# 21. Keyboard boundary

BetterCP/M 1.0 CONFIG has no keyboard section.

Specifically excluded:

```text
key remapping
function-key macros
keyboard profile loading
raw keyboard diagnostics
key-repeat configuration
```

No `KEYDEF.COM` is currently planned.

Any future keyboard configuration should begin from BetterCP/M's own keyboard architecture rather than reproducing Montezuma Micro CP/M's implementation assumptions.

---

# 22. Post-1.0 command-environment extensions

Two likely future persistent settings are:

```text
search path
named directories
```

They are explicitly deferred.

Possible future administration models include:

```text
CONFIG manages them

PATH and NDR commands manage them

CONFIG edits persistent defaults while
PATH and NDR provide day-to-day/runtime control
```

No 1.0 CONFIG implementation should unnecessarily constrain that decision.

---

# 23. Platform abstraction

CONFIG should contain as little hardware-specific knowledge as practical.

Generic CONFIG code may own:

```text
menu/UI framework
command-line parser
active/pending/saved presentation
common validation
startup interface
generic printer schema
generic serial schema
generic drive-management interface
```

Platform/backend code remains responsible for:

```text
actual serial-port enumeration
supported serial parameters
serial hardware programming

actual disk-device enumeration
drive capabilities
drive validation/application

supported logical-device mappings

persistent backend-specific records
```

CONFIG must not display a generic option simply because its schema contains a field for it.

---

# 24. Release qualification

Before CONFIG 1.0 scope is frozen, Work should classify each domain as follows.

### Existing and retained

```text
Startup
Drive configuration
```

### Candidate additions requiring audit

```text
Persistent IOBYTE defaults
Printer configuration
Serial configuration
```

For each candidate, the audit should report:

```text
resident bytes required
persistent bytes required
new runtime code required
backend changes required
current-state vs pending-state behavior
cold-boot initialization changes
```

After those numbers are known, each feature can be marked either:

```text
Committed for 1.0
Deferred post-1.0
Reduced in scope for 1.0
```

---

# 25. 1.0 implementation principle

CONFIG 1.0 should remain a **system configuration utility**, not grow into a general control panel.

A setting belongs in CONFIG when all of the following are true:

1. it is system-wide rather than application-specific;
2. it has persistent meaning across cold boot;
3. it belongs to a core BetterCP/M subsystem;
4. there is a well-defined runtime consumer for it;
5. its resident/runtime cost is justified.

This is the controlling rule for future additions.

---

## Current working command summary

Established:

```text
CONFIG
CONFIG /VER
CONFIG /SHOW
CONFIG /STARTUP="command line"
CONFIG /STARTUP=""
```

`/SHOW` has the saved-drive-inspection limitation described in section 16.

Proposed/new; not currently available:

```text
CONFIG /DEFAULT

CONFIG /IOBYTE logical=physical [...]

CONFIG /PRINTER:LINE=RAW|SUPPRESSLF
CONFIG /PRINTER:FF=NATIVE|SIMULATE
CONFIG /PRINTER:PAGELENGTH=n
CONFIG /PRINTER:TABS=NATIVE|EXPAND
CONFIG /PRINTER:TABWIDTH=n

CONFIG /SERIAL:n BAUD=n
CONFIG /SERIAL:n DATA=5|6|7|8
CONFIG /SERIAL:n PARITY=NONE|ODD|EVEN
CONFIG /SERIAL:n STOP=1|2
CONFIG /SERIAL:n CTS=ON|OFF
CONFIG /SERIAL:n DSR=ON|OFF
CONFIG /SERIAL:n XONXOFF=ON|OFF
```

Drive command-line syntax remains intentionally unresolved until reconciled with the existing drive configuration contract.

## Existing contract references

- [Active settings and startup defaults](CONFIG-STARTUP-SETTINGS-DECISIONS.md)
- [Startup record reader](195%20CONFIG%20Startup%20Record%20Reader.md)
- [Pending startup command](196%20CONFIG%20Pending%20Startup%20Command.md)
- [Pending-only save scope](198%20CONFIG%20Pending-Only%20Save%20Scope.md)
- [All-current save scope](199%20CONFIG%20All-Current%20Save%20Scope.md)
- [Compiled IOBYTE cold default](IOBYTE-COLD-DEFAULT.md)
