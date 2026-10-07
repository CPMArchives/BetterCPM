# BetterCP/M Post-1.0 Exploration Proposal
## System Configuration, Policy, and Historical CP/M Behavior

### Status

This is a **proposal for post-1.0 exploration**, not a proposed ABI, implementation specification, or commitment to particular features.

The purpose is to investigate whether BetterCP/M's existing CONFIG facility should evolve after 1.0 from primarily a system/setup utility into the common management interface for the persistent **configuration and policy of the BetterCP/M operating environment**.

The investigation should inform the post-1.0 roadmap. It should not expand the BetterCP/M 1.0 release gate.

---

# 1. Motivation

A discussion about the location of SUBMIT's active `$$$.SUB` file exposed a broader question.

Historically, CP/M-family systems often made application-visible behavioral choices either:

- directly in the implementation;
- at system-generation time;
- through assembly-time options;
- through environment descriptors;
- or through replacement command processors.

For example, historical implementations have differed over whether the active SUBMIT control file resides on a fixed system location such as `A0:` or follows the drive/user from which SUBMIT was invoked.

Rather than asking only:

> Where should BetterCP/M put `$$$.SUB`?

the broader question is:

> **Which aspects of BetterCP/M behavior are operating-system policy and therefore reasonable candidates for persistent configuration?**

This should be investigated systematically rather than answered one option at a time.

---

# 2. Proposed conceptual distinction

The exploration should distinguish at least four classes of system behavior.

## 2.1 BetterCP/M invariants

These define BetterCP/M compatibility and should not be user-configurable merely because another historical system behaved differently.

Examples include:

- system and extension ABI semantics;
- BCPX/BRSX carrier contracts;
- extended-BDOS selector meanings;
- resident-service address lifetime;
- transactional reconstruction semantics;
- native TIME record format;
- fixed architectural ownership/lifetime rules.

CONFIG must not become a mechanism for redefining what “BetterCP/M compatible” means.

## 2.2 System policy

These are behaviors for which several reasonable choices may exist without changing the underlying BetterCP/M ABI.

Possible examples include:

- command prompt presentation;
- startup drive/user;
- command search policy after PATH exists;
- selected SUBMIT behavior;
- human-facing date/time presentation;
- selected console interaction policies.

These are the principal candidates for CONFIG-managed persistent settings.

## 2.3 Hardware/platform configuration

These are already natural CONFIG territory:

- physical devices;
- logical disk bindings;
- FDF/FDB format selection;
- platform/device settings.

The post-1.0 investigation should preserve the distinction between hardware configuration and behavioral policy even if both are managed through CONFIG.

## 2.4 Compatibility adapters

Some historical compatibility belongs in loadable extensions rather than CONFIG.

P2DOS clock Functions 200/201 are the existing example:

```text
historical API
     ↓
P2DOS.RSX
     ↓
native TIME service
```

A CONFIG switch should not replace a clean compatibility adapter when the historical behavior is fundamentally an alternate API rather than system policy.

---

# 3. CONFIG as a system configuration interface

The possible longer-term conception is:

> **CONFIG is the common user-facing interface for defining the persistent personality of a BetterCP/M installation.**

This does **not** mean CONFIG owns all configuration state.

Natural ownership remains important.

Conceptually:

```text
CONFIG
   |
   +-- disk configuration
   |       ↓
   |   BIOS/config owners
   |
   +-- command policy
   |       ↓
   |   command environment
   |
   +-- NDR/PATH
   |       ↓
   |   NDR/path subsystem
   |
   +-- extension profiles
   |       ↓
   |   CPX/RSX managers
   |
   `-- startup
           ↓
       appropriate owner
```

CONFIG provides a coherent management interface while each subsystem retains its natural runtime state.

This is consistent with the ownership/lifetime principles established during BetterCP/M 1.0 architecture work.

---

# 4. Command-environment configuration

This appears to be the richest post-1.0 area.

Potential configuration includes:

- initial drive/user after cold boot;
- prompt presentation;
- named directories;
- command search path;
- selected search policies;
- SUBMIT policy where historical compatibility justifies it.

NDR and PATH are already planned post-1.0 BetterCP/M work.

They can naturally be understood as part of command-environment configuration rather than isolated utilities.

---

# 5. Default BetterCP/M prompt

The proposed default BetterCP/M prompt would retain the drive/user form already used by the system:

```text
A0>
B3>
C15>
```

This should remain the BetterCP/M-native default rather than reverting to the older DRI-style:

```text
A>
```

When NDR support is introduced, a candidate default to evaluate would follow the familiar Z-System-style combination of canonical location and symbolic directory name:

```text
A0 ROOT>
B3 WORK>
C7 SOURCE>
```

The DU and named-directory name convey different information:

- `A0` is the canonical CP/M location;
- `ROOT` is its symbolic NDR identity.

If the current DU has no NDR name, the prompt can remain simply:

```text
B7>
```

---

# 6. Configurable prompt

Beyond the default, prompt composition is a strong candidate for persistent policy.

Potential optional fields include:

- DU;
- NDR name;
- date;
- time.

For example:

```text
A0 ROOT>

08:42 A0 ROOT>

07-OCT-26 A0 ROOT>

07-OCT-26 08:42 A0 ROOT>
```

The investigation should determine an appropriate bounded formatting mechanism.

It should not assume the exact syntax or escape characters in advance.

Prompt generation should remain inexpensive; information requiring expensive disk scans or similar work should probably not be supported merely because it could be displayed.

---

# 7. NDR and PATH

Named directories and PATH are already post-1.0 BetterCP/M directions.

Their configuration should be considered together with the command environment.

Conceptually:

```text
Named directories

ROOT      A0:
TOOLS     B0:
WORK      B3:
SOURCE    C4:
```

and:

```text
Command path

$DU:
TOOLS:
A0:
```

The exact syntax and semantics remain future design work.

In particular, mature Z-System practice should be studied before BetterCP/M invents its own conventions for:

- current-DU representation in PATH;
- path search order;
- NDR prompt presentation;
- named-directory resolution;
- command search behavior.

---

# 8. Startup configuration

BetterCP/M 1.0 already establishes several persistent startup concepts:

- startup command;
- saved CPX profile;
- saved RSX profile.

A post-1.0 CONFIG model could also consider:

- startup DU;
- possibly startup location by NDR name after NDR exists.

For example:

```text
Startup location: A0
```

or eventually:

```text
Startup location: ROOT
```

The investigation must preserve the established distinction between active runtime state and saved startup state.

---

# 9. Human-facing date/time policy

The native TIME ABI is an invariant and should not become configurable.

Human presentation may reasonably be policy.

Potential examples:

```text
Date:
  DD-MMM-YY
  YYYY-MM-DD
  MM/DD/YY
  DD/MM/YY

Time:
  24-hour
  12-hour
```

A shared system preference could potentially be used consistently by:

- TIME.COM;
- configurable prompt date/time;
- later utilities displaying dates.

This should be evaluated as presentation policy, not as a change to TIME semantics.

---

# 10. Console policy

Historical CP/M-family systems and terminals differ in interactive conventions.

Possible candidates for investigation include:

- DEL versus BS handling;
- visual versus traditional CP/M delete behavior;
- bell enable/disable;
- selected command-line editing behavior.

The later terminal-capability redesign is already deferred beyond 1.0 and may subsume some of this area.

The investigation should avoid turning every editing key into a CONFIG option.

---

# 11. SUBMIT policy as the motivating example

Historical CP/M-family systems used more than one convention for the active `$$$.SUB` control file.

A strong evolved convention, notably in ZCPR 3.3, uses:

```text
A0:$$$.SUB
```

which makes batch execution independent of drive and user changes.

Other implementations retain current/invocation-DU behavior.

BetterCP/M 1.0 has selected `A0:$$$.SUB` as its fixed command-stream policy. The post-1.0 study may evaluate alternatives without reopening that release contract.

However, the broader configuration study should determine whether supporting an alternate historical convention provides enough real compatibility benefit to justify a CONFIG policy.

Conceptually:

```text
SUBMIT control file:
    A0
    invocation DU
```

This should **not** be adopted merely because two historical behaviors existed.

Invocation-DU behavior also has a lifecycle consequence: BetterCP/M would need to remember the batch's originating DU after the active DU changes and preserve that state across every lifecycle through which a submit job is expected to survive.

The investigation should measure the compatibility benefit against that additional state and testing burden.

---

# 12. ZCPR/Z-System as a source of configuration candidates

ZCPR3 and its descendants are particularly valuable sources for this exploration.

ZCPR historically offered numerous assembly/build-time configuration options because it had to operate within the traditional fixed CCP footprint and accommodate different system personalities.

Later ZCPR versions moved some formerly compile-time choices into environment descriptors.

BetterCP/M does not share all of ZCPR's historical size constraints.

Its reclaimable/reconstructable command environment may permit some genuine policy choices to be implemented once and selected through persistent configuration rather than by rebuilding the command processor.

Therefore:

> **The ZCPR3/ZCPR33 build-time configuration set should be systematically mined for possible BetterCP/M configuration policies.**

This is not an instruction to reproduce ZCPR's options.

Each option should be classified.

---

# 13. Proposed ZCPR-option classification

For each ZCPR build-time/environment option, determine which category it belongs to:

### BetterCP/M invariant

One behavior should simply be BetterCP/M's defined semantic.

No CONFIG option.

### CONFIG policy candidate

The option represents a genuine user/system preference that remains useful and does not redefine the BetterCP/M ABI.

### Already generalized by BetterCP/M

The historical option solved a problem BetterCP/M already handles through another mechanism.

Examples may include resident-command selection being superseded by CPXs or resident-service mechanisms.

### Deferred/out of scope

The option belongs to facilities BetterCP/M does not presently intend to implement, such as a historical security model.

This classification should prevent CONFIG from becoming a museum of every historical CP/M implementation switch.

---

# 14. Examples worth examining in ZCPR

Without presupposing adoption, the audit should examine at least:

- prompt composition and DU display;
- NDR behavior;
- PATH/current-DU search behavior;
- direct DU addressing policy;
- maximum drive/user handling;
- command-search policy;
- SUBMIT behavior;
- environment descriptor options;
- RCP/FCP/NDR allocation choices;
- resident-command selection;
- error/reporting options;
- wheel/security/password options;
- other documented build-time feature equates.

Some of these will almost certainly be rejected.

The purpose is to identify the ones that represented genuine policy choices rather than code-size compromises or implementation details.

---

# 15. Extension configuration

BetterCP/M already has saved CPX and RSX startup profiles.

A future question is whether extensions themselves should eventually be able to expose persistent configuration parameters through CONFIG.

For example, a hypothetical extension might require:

```text
buffer size = 16
mode = X
```

This could eventually imply extension-published configuration schemas.

Do **not** design that mechanism as part of this exploration.

Record it only as a possible future requirement to revisit when a concrete extension demonstrates the need.

The recent correction concerning premature dependency metadata is a useful warning against designing carrier facilities before real consumers exist.

---

# 16. Printer/list-device configuration

Another area worth examining is the CP/M list/printer environment.

Potential distinctions include:

- hardware/list-device mapping;
- printer-echo default;
- other human-facing list behavior.

Hardware mapping belongs naturally to platform configuration.

Printer-echo policy may belong to command-environment policy.

The audit should distinguish the two rather than assume CONFIG must own their runtime state.

---

# 17. Error and presentation policy

Some CP/M-family systems differed in human-facing error presentation.

Potential investigation areas include:

- terse versus descriptive errors;
- boot-banner verbosity;
- other presentation choices.

Application-visible BDOS error semantics must remain BetterCP/M invariants.

Only presentation behavior should be considered configurable.

---

# 18. Avoid combinatorial configuration

Configurability has a real cost.

Ten independent Boolean switches theoretically create 1,024 combinations.

Every supported policy increases:

- documentation burden;
- testing burden;
- interaction cases;
- support complexity.

Therefore a configuration option should have a meaningful justification.

A useful candidate test is:

1. multiple historically significant or practically useful choices exist;
2. the choice is not fundamental to the BetterCP/M ABI;
3. real workflow or compatibility benefit exists;
4. the setting can be changed without destabilizing unrelated subsystems;
5. its active/saved and cold/warm lifecycle is clear;
6. the benefit justifies the qualification burden.

Failure of that test should normally mean BetterCP/M chooses one behavior.

---

# 19. BetterCP/M defaults still matter

Making a policy configurable does not mean BetterCP/M should be neutral about defaults.

BetterCP/M should have a coherent native personality.

Examples discussed so far include:

```text
Prompt:             DU>
                     A0>

With NDR:           DU NDR>
                     A0 ROOT>

SUBMIT control:     A0:$$$.SUB (chosen 1.0 policy)
```

Historical alternatives should be optional only where justified.

CONFIG should allow tailoring of BetterCP/M, not eliminate the concept of default BetterCP/M behavior.

---

# 20. Possible future CONFIG organization

One conceptual organization worth evaluating is:

```text
CONFIG
|
+-- MACHINE
|   +-- devices
|   +-- disks
|   `-- platform settings
|
+-- ENVIRONMENT
|   +-- startup location
|   +-- prompt
|   +-- date/time presentation
|   +-- NDR
|   `-- PATH
|
+-- STARTUP
|   +-- startup command
|   +-- CPX profile
|   `-- RSX profile
|
+-- COMPATIBILITY
|   `-- selected historical behavior policies
|
`-- EXTENSIONS
    `-- future extension configuration if justified
```

This is illustrative only.

It should not be treated as a proposed CONFIG UI or persistent-data schema.

---

# 21. Command-line CONFIG

The broader configuration role also strengthens the case for a scriptable CONFIG interface.

Interactive CONFIG remains appropriate for normal administration.

Advanced users and SUBMIT files may benefit from command-line access to the same operations.

Conceptually:

```text
CONFIG /...
```

could eventually manage prompt, PATH, NDR, startup, or other policy.

The exact command syntax should be designed only after the configuration model is known.

The important principle is:

> Interactive and command-line CONFIG should be two frontends to the same configuration operations, validation, ownership, and persistence model.

---

# 22. Relationship to BetterCP/M 1.0

This exploration should **not expand BetterCP/M 1.0**.

The 1.0 CONFIG implementation should remain bounded to the contracts already frozen for the release.

However, 1.0 implementation should avoid unnecessary assumptions that CONFIG will forever manage only the settings currently present in 1.0.

Where inexpensive and architecturally clean, its internal organization and saved-state mechanisms should leave room for later configuration domains.

Do not introduce speculative 1.0 metadata, storage allocations, or ABI fields merely to anticipate this work.

---

# 23. Requested post-1.0 research

After BetterCP/M 1.0, perform a bounded configuration-policy study covering:

1. DRI CP/M 2.2;
2. significant vendor CP/M variants where relevant;
3. ZCPR/ZCPR3/ZCPR33 and Z-System;
4. CP/M Plus where its behavior illuminates later CP/M evolution;
5. modern CP/M implementations and environments such as RomWBW and current homebrew ports.

Identify application-visible and user-visible behaviors that varied.

For each, record:

- historical behaviors;
- why the variation existed;
- whether software depended upon it;
- whether BetterCP/M already has a frozen semantic;
- whether BetterCP/M already generalizes the issue another way;
- implementation/lifecycle cost;
- testing cost;
- recommended classification:
  - invariant;
  - CONFIG candidate;
  - compatibility adapter;
  - already generalized;
  - deferred/rejected.

Give particular attention to the ZCPR build-time configuration set because it provides a historically mature catalogue of system-integration choices.

---

# 24. Desired outcome

The desired result is **not a long list of switches**.

The desired result is an informed answer to:

> **What aspects of the BetterCP/M operating environment should constitute persistent system policy, and which historical CP/M configuration choices are worth making runtime-configurable?**

A successful investigation may conclude that only a handful of options deserve implementation.

That would be preferable to excessive configurability.

The study should also clarify whether CONFIG should formally evolve after 1.0 into the common management interface for:

- machine/platform configuration;
- command-environment policy;
- startup configuration;
- extension startup profiles;
- selected compatibility behavior.

---

# 25. Proposed roadmap disposition

Add this as a **post-1.0 exploration item**, not a committed feature set.

Suggested roadmap wording:

> **System configuration and policy study:** Evaluate expansion of CONFIG into the common management interface for persistent BetterCP/M system policy. Mine ZCPR/Z-System and other mature CP/M-family environments for historically useful build-time and runtime configuration choices; classify each as a BetterCP/M invariant, CONFIG policy candidate, compatibility adapter, already-generalized facility, or deferred feature. Include post-1.0 NDR/PATH and prompt configuration in the study. Preserve coherent BetterCP/M-native defaults and avoid speculative 1.0 ABI/storage changes.

The exploration should precede any broad post-1.0 CONFIG redesign.

---

## Recording notes

Recorded 2026-10-07 as an exploration proposal, not an accepted feature set.
Prompt layouts, CONFIG organization, command syntax, and extension schemas are
illustrative candidates. The research should produce a bounded evidence and
cost matrix before any broad CONFIG redesign. Start with command environment,
NDR/PATH, startup, and SUBMIT policy; expand only where concrete evidence
justifies it. No speculative 1.0 ABI fields or allocations are authorized.
