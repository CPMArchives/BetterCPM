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

These configuration domains are implemented in CONFIG:

```text
STARTUP
DRIVE
Disk-boot IOBYTE
```

## 4.2 Proposed 1.0 extensions pending runtime-cost qualification

These are desirable CONFIG additions but require auditing of the corresponding resident/runtime support before they become firm 1.0 commitments:

```text
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
CONFIG /DEFAULT
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

Interactive edits follow their domain contracts. Startup-command edits remain
private pending changes. The format workbench edits a private binding until
Apply; successful drive updates change active state without saving defaults.
Do not infer a general pending-drive reset facility from this state model.

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

Builds 006–008 provide physical-profile, logical binding/format-selection and
scalar format-workbench forms below. Build 009 adds sector-ID and size-map
slot command-line editing.

## 12.6 Physical-profile command line (Build 006)

```text
CONFIG /PHYSICAL=n /TYPE=inches /TRACKS=count /SIDES=count /STEP=ms /SPINUP=quarters /SETTLE=ms
```

`/PHYSICAL=0` through `/PHYSICAL=3` must come first, followed by at least one
field. Each field is optional, appears at most once, and may appear in any order.
Names are case-insensitive; values are unsigned decimal bytes. Fields must be
separated by whitespace. No combination with `/SHOW`, `/STARTUP`, `/DEFAULT` or
`/VER` is specified. The whole tail, including all field values and duplicates,
is checked before INIT, catalogue/file access or any configuration mutation.

| Field | Accepted values | Meaning |
| --- | --- | --- |
| `/TYPE` | 5, 8 | Existing profile drive type in inches |
| `/TRACKS` | 35, 40, 77, 80 | Existing menu's track-count choices |
| `/SIDES` | 1, 2 | Available drive sides |
| `/STEP` | 6, 12, 20, 30 | Milliseconds, converted to backend codes 0–3 |
| `/SPINUP` | 0–16 | Quarter-second units |
| `/SETTLE` | 0–255 | Head-settling milliseconds |

For example:

```text
CONFIG /PHYSICAL=1 /TRACKS=80 /SIDES=2 /STEP=6
```

This changes active state only, matching menu C. Unspecified fields are read
from the current physical profile and retained. All supplied fields are merged
into a private request and submitted in one public configuration-API update;
backend validation remains authoritative. The supported scope is the existing
six-field physical-profile API on the two shipped backends, not a new generic
hardware-capability schema. Physical timing effects depend on the backend.
No DISK.FDB load, save confirmation, completion keypress or disk save occurs.
The result reports `Disk configuration changed (until cold boot).` To persist
it, enter CONFIG later and explicitly choose save-all-current settings. It does
not create invocation-private pending state that disappears on exit.

Both menu C and this CLI now query A:'s current binding before a physical update.
If the proposed track/side limits cannot support that binding, or its query
fails, reject before committing any profile or detaching any binding. This is a
geometry guard, not detection of the actual attached drive hardware.

After a successful profile update, incompatible non-system bindings are detached
and their BDOS login/allocation state reset as in the existing physical-first
menu behavior. Every cleanup query/detach is checked. A failure after the
profile update reports `Drive profile changed; binding cleanup incomplete.`;
it must not claim either complete success or that nothing changed. Live profile
application and subsequent binding cleanup are not a transactional disk save.
The operator may need to retry or reconfigure affected logical bindings.
A failure before committing the physical update reports
`Cannot safely apply drive profile. Nothing changed.` without a pause.


## 12.7 Logical binding command line (Build 007)

```text
CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="MM 80T DS DATA"
CONFIG /LOGICAL=C /UNBIND
```

These forms apply one active logical binding, or mark it unconfigured. They do
not save defaults, touch file contents, or ask for confirmation/completion keys.
Use the separate save-all-current action to persist the result. A: remains the
protected boot binding and is rejected during parsing; targets are B through D.

Operands have the order shown. Physical indexes are 0–3. The quoted format is
an exact catalogue display description, compared case-insensitively with its
32-byte space padding; it is not a catalogue row number, source-file long name,
prefix or wildcard. Require 1–32 printable ASCII characters with at least one
non-space character. No quote escapes are defined. Control characters, extra
operands, combinations with other operations and malformed tails fail before
INIT or catalogue access. A valid quoted `/VER` substring is data, not a version
option. Normal command-tail length bounds still apply.

Resolve the complete catalogue before selecting an entry: unknown or duplicate
case-insensitive display descriptions fail. A unique match must pass the shared
FDB normalization/support checks, the existing physical track/side compatibility
check, and final backend logical-binding validation before commit. No failed
lookup, catalogue read, compatibility check or rejected backend request may
change an active binding. After success reset exactly the selected logical
drive's BDOS login/allocation state, as in the menu binding path.

`/UNBIND` requires no catalogue and uses the existing backend unconfigured marker
without erasing the remaining format fields. Named binding loads and validates
DISK.FDB through the existing current-drive/A: lookup. Missing or corrupt
catalogues return with the existing diagnostic and no CLI pause. Interactive
catalogue errors retain their existing pause. The FDB reader's consumer abort
target makes that policy explicit; DUP retains its identical existing binary.

Unknown, ambiguous or unsupported formats report
`Unknown, ambiguous, or unsupported format. Nothing changed.`. Compatibility or
backend failures report `Cannot apply logical binding. Nothing changed.`.
Successful binding or unbinding reports the existing until-cold-boot message.

The shipped catalogue currently has unique display descriptions; a replacement
catalogue with duplicate names must be corrected or selected through the menu.

---

## Scalar format-workbench command line (Build 008)

```text
CONFIG /EDIT=B /CKS=16
CONFIG /EDIT=C /SPT=40 /BSH=4 /BLM=15
```

`/EDIT=B` through `/EDIT=D` must appear first, followed by one or more named
scalar fields. A: is protected. Fields may appear in any order, once each:

| Field | Workbench meaning | Decimal storage range |
| --- | --- | --- |
| PHYSICAL | Physical drive | 0–255; final binding must select 0–3 |
| SPT | 128-byte records per track | 0–65535 |
| BSH, BLM, EXM | Block shift, block mask, extent mask | 0–255 each |
| DSM, DRM | Last allocation block, last directory entry | 0–65535 each |
| AL0, AL1 | Directory allocation masks | 0–255 each |
| CKS, OFF | Directory check size, reserved tracks | 0–65535 each |
| CYLINDERS, SECTORS | Cylinders, physical sectors per track | 0–255 each |
| SIZE, FLAGS, SIZEMAP | Maximum size code, format flags, explicit size-map flag | 0–255 each |

These are parser storage ranges, not promises that every numeric value or
combination is supported. Existing backend validation remains authoritative.
Unsigned decimal, case-insensitive names and whitespace separators are required.
Duplicate/unknown fields, overflow and extra commands fail before INIT or I/O.

The command starts with the selected active 64-byte binding, changes only named
scalar fields, checks physical geometry and submits the complete record through
the existing validated binding API. Failure before commit leaves active state
unchanged. Success resets only that logical drive's BDOS login state. This is
active-only, requires no DISK.FDB, and returns without a prompt; persistence
requires the separate save-all operation. It does not format or write media.
Sector-ID and size-map slots also accept the Build 009 forms below.
An unbound drive must first receive a valid binding, or an edit must supply a
valid physical drive and complete backend-valid fields.

---

## Sector-map slot command line (Build 009)

```text
CONFIG /EDIT=B /SLOT=1 /ID=200
CONFIG /EDIT=B /SPT=35 /SLOT=1 /CODE=0
```

`SLOT` is a one-based physical-order slot, 1–32. `ID` is the physical sector
ID, 0–255. `CODE` is 0–3 for 128/256/512/1024-byte sectors. A slot requires
`ID`, `CODE`, or both; neither field is allowed without a slot. Each operand
appears once. Scalar fields may accompany the slot edit, in any order after
`/EDIT=`, so SPT/maximum size and the map can be made consistent in one commit.
One slot is edited per invocation. Other slots and unspecified fields survive.
Duplicate IDs or inconsistent geometry are rejected by the existing backend.
To exchange two IDs under uniqueness constraints, use an unused temporary ID or
make multiple private edits in menu E before applying them together.

The first size edit seeds all 32 packed slots from the current uniform size;
subsequent edits preserve other packed slots. The menu and CLI share this code.
Explicit size maps require FDF.RSX's checked normalization service before the
binding setter is called. Missing support or an inconsistent map fails without
an active update. This also closes a menu E safety gap: the legacy setter's
uniform fast path could discard a requested size map while reporting success.
CONFIG now validates the explicit map first instead of silently losing it.

These are active binding-definition changes, not physical formatting. All
normal backend limits, separate-save semantics and selected-drive reset apply.
No disk write or confirmation occurs for these CLI commands.

---

# 13. Persistent disk-boot IOBYTE (Build 011)
**Status: implemented for the qualified Model 4 and cpmsim disk-boot profiles**

STAT owns live IOBYTE assignment. CONFIG owns the separately saved disk-boot
default. It patches the build-published operand of `LD A,095H; LD (0003H),A`
in Model 4 stage one or cpmsim's stored BIOS initializer. No boot instructions,
resident storage, BDOS calls or descriptor ABI are added. Unloaded TPA stays 53K.

```text
CONFIG /IOBYTE=85
CONFIG /IOBYTE=149
```

The operand is an unsigned decimal byte. 85 is 55h (CRT console, PTR reader,
PTP punch, CRT list); 149 is the compiled 95h default (same, but LPT list).
The complete request must validate before INIT/I/O. Extra operands, signs and
overflow are rejected. CON must remain CRT: both current platforms support it,
so CONFIG cannot save a console route that would strand the next boot.

Changed routes require the running platform's character capability bit. Existing
unchanged placeholder routes may be retained. An explicit 149 restores the
compiled factory assignment even when a placeholder such as Model 4 LPT has no
physical implementation. This does not make that device functional.

Menu K provides the same confirmed-save operation. `/SHOW` distinguishes the
live byte from the saved disk-boot byte, in decimal. It reports an unavailable
saved byte if build/record/read validation fails, without inventing a default.
This is a direct confirmed save, not another pending field in H's save scopes.
`/DEFAULT` still resets only the pending startup command.

Before confirmation, CONFIG chooses build-generated metadata by qualified boot
geometry, reads the containing 128-byte record and checks its CRC-32 after
normalizing only the operand to compiled 95h. The build resolves the explicit
`IO_COLD` assembly symbol and checks the five-byte instruction contract; it never
searches for a byte value. The current stored byte must retain CON=CRT. The
builder independently checks that the embedded descriptor matches the installed
boot code before publishing a System Disk.

On Y, CONFIG changes only the operand, writes the record and compares all 128
bytes on readback. A failed write or comparison attempts verified restoration
of the original record, including the potentially partially written record.
Restoration failure reports possible damage. N and validation/read failures make
no write. Power loss during a physical sector write can still require recovery
from another boot disk; this is not a power-loss transaction.

The live byte at 0003h is unchanged. Warm boots preserve it. Next disk cold boot
uses the saved operand. Save-all retains that operand, and its resident CRC check
normalizes the cpmsim operand to the compiled value while checking all other
immutable bytes. SYSGEN's existing copy of the installed loader/carrier preserves
the operand in disk/package payloads; it does not synthesize a new IOBYTE value.

The setting belongs to the boot disk. It does not rewrite ROM firmware or change
an immutable ROM's cold default. A ROM default change requires rebuilding that
ROM; saving a disk default must not be described as changing firmware.

See [cold-operand qualification and layout](CONFIG%20Cold%20IOBYTE.md).

---

# 14. Printer configuration
**Status: deferred to post-1.0 by maintainer decision, 2026-10-16**

The proposal below is retained for future implementation, not as a 1.0 release
requirement. See the [prototype](Printer%20RSX%20Prototype.md) and
[post-1.0 work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#printer-rsx-implementation-follow-up--2026-10-16).
References below to possible 1.0 inclusion record the earlier proposal and are
superseded by this decision. The separate serial proposal is unchanged.

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
**Status: deferred to post-1.0 by maintainer decision, 2026-10-16**

The proposal below is retained for future implementation, not as a 1.0 release
requirement. See the [backend audit](CONFIG%20Serial%20Backend%20Audit.md) and
[post-1.0 work item](../releases/POST-1.0-CONFIG-POLICY-STUDY.md#serial-support-follow-up--2026-10-16).
Earlier references below to possible 1.0 inclusion are superseded by this decision.

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
**Status: drive/startup inspection implemented; Build 005 uses embedded CRC-32 validation**

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

Build 005 reports active physical profiles, active logical bindings, the saved
cold-start command and the absence of private pending changes in this new
invocation, then separately reports saved physical profiles and logical bindings.
It reads the carrier, checks the public layout and geometry, and verifies its
fixed bytes with the embedded build fingerprint described below. Inspection
cannot enter activation or writes. Recoverable read errors or incompatibility
produce a diagnostic and return without unverified saved drive values. Previously
printed active and startup information remains available. Editable table fields
are copied to private transient storage before restoring the FDB catalogue.
`/SHOW` does not require completion keypresses or SYSGEN.DAT.

## 16.1 Embedded build validation for inspection and save-all

The former 6,784-byte external reference is replaced by a 20-byte record per
supported platform/layout: the 16-byte build/layout/geometry descriptor followed
by a four-byte little-endian CRC-32. Records are generated from the actual
assembled carrier; public configuration table addresses and BIOS record geometry
select a compatible record. Existing table bounds and reserved-track checks
remain required before carrier access. Ambiguous records are rejected at build time.

The checksum is CRC-32/ISO-HDLC (reflected polynomial EDB88320h, initial value
FFFFFFFFh, final XOR FFFFFFFFh; `123456789` gives CBF43926h). It covers all 52
128-byte resident-carrier records, including their padding, starting at logical
record 8. Normalize only these existing editable ranges to zero:

- 24 bytes at the physical-profile table;
- 64 binding bytes at offset 16 of each of the four 80-byte logical-drive entries.

The first 16 bytes of every logical-drive entry remain covered. No other bytes
are omitted. BCST startup records 1–2 are separate and retain their existing
format/checksum validation and verified-write/rollback rules.

CONFIG reads the installed carrier into its proposed buffer and copies the exact
original to rollback storage before normalization. After a successful CRC check,
it restores the unmodified carrier bytes to the proposed buffer before inspecting
or merging active settings. A mismatch returns before confirmation, activation
or any save. Existing per-record differences, write verification and rollback
continue to use exact original bytes, not the normalized checksum input.

CRC-32 is an accidental-corruption/build-mismatch check. It replaces the earlier
exact reference comparison and therefore admits a nonzero checksum collision
risk; it is not cryptographic authentication. It does not validate the contents
of editable fields merely because they are excluded from the fingerprint.
No permanent BIOS/BDOS storage or ABI expansion is required. SYSGEN.DAT is no
longer shipped or used. CONFIG must still be built for the installed system;
runtime discovery cannot establish that a foreign system's layout is safe.

---

# 17. Defaults/reset facility
**Status: startup-only pending reset implemented in Build 010**

A mechanism for restoring CONFIG-managed settings to platform/distribution defaults may be useful, but it must respect the existing domain storage architecture and save-state model.

The standalone command is:

```text
CONFIG /DEFAULT
```

Maintainer decision and Build 010 behavior: `/DEFAULT` restores only the
startup-command domain to `SUBMIT STARTUP`. Physical profiles, logical bindings,
format definitions, IOBYTE and peripheral settings are outside this operation.
The command is standalone; extra operands and combinations are rejected before
INIT or I/O. It uses the existing interactive CONFIG/catalogue environment.

The generated canonical BCST record is private pending state, enabled with the
14-byte command and a valid checksum. Nothing is executed, activated or saved.
CONFIG reports “Startup default pending; drives unchanged.” and opens the
startup menu after acknowledgment. The pending/unsaved status is displayed.
The operator can inspect, edit, clear or explicitly test the command, then use
H's existing save scope and Y/N confirmation to persist it. Exiting without
saving discards the pending replacement. A declined save also preserves the
installed record. Existing save verification/rollback remains in force.

This is the distribution startup default (`metadata/distribution.json`), not a
reset of the contents of STARTUP.SUB. A future change to that default must keep
CONFIG's default command and the distribution metadata aligned. Broader drive
factory-default support is not specified for 1.0.

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
CONFIG /PHYSICAL=n /field=value [...]
CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="name"
CONFIG /LOGICAL=B /UNBIND
CONFIG /EDIT=B /CKS=16
CONFIG /IOBYTE=85
```

Physical field operands use the slash-prefixed names in section 12.6. `/SHOW`
includes separate active and CRC-validated saved drive settings.

Proposed/new; not currently available:

```text
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

Scalar and sector-map slot command-line fields are specified in section 12.

## Consolidation and implementation boundary

This specification is the reconciled CONFIG baseline. The implemented command
summary above and sections 12 and 16 take precedence over older implementation
notes describing A–E placeholders, an external SYSGEN.DAT reference, or wholly
missing drive CLI support. The two save scopes and separate storage domains
remain unchanged. The gated printer
and serial proposals remain open; consolidation does not approve them or claim
complete CONFIG qualification. See the [alignment record](CONFIG%20Specification%20Alignment.md)
and [runtime audit](CONFIG%20Runtime%20Audit.md) for evidence and remaining gates.

CONFIG saves settings on the current system disk;
[SYSGEN](SYSGEN%20Specification.md) installs a system on another disk;
[DUP](DUP%20Specification.md) formats, copies and checks media.

## Existing contract references

- [Active settings and startup defaults](CONFIG-STARTUP-SETTINGS-DECISIONS.md)
- [Startup record reader](195%20CONFIG%20Startup%20Record%20Reader.md)
- [Pending startup command](196%20CONFIG%20Pending%20Startup%20Command.md)
- [Pending-only save scope](198%20CONFIG%20Pending-Only%20Save%20Scope.md)
- [All-current save scope](199%20CONFIG%20All-Current%20Save%20Scope.md)
- [Compiled IOBYTE cold default](IOBYTE-COLD-DEFAULT.md)


## Main-menu organization (Build 012)

The main menu assigns A to Startup command, B to Cold-boot IOBYTE,
C to Disk drive definitions, D to Disk format definitions, E to Create or
edit a disk format, and S to Save current configuration on disk (SYSGEN).
Separate startup, IOBYTE, disk, and save groups with blank lines. The selection
prompt is `Select [ A - E or S ], or BREAK (^C) to exit.` These keys replace
the former F–K assignments; submenu keys and setting semantics are unchanged.
