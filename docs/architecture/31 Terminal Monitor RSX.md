# Terminal monitor RSX for BetterCP/M 1.0

Accepted design: 2026-10-12. Implementation closure: 2026-10-15. The BIOS
hooks, transactional RSX lifecycle, command-return reset and explicit clear
paths are implemented. ADM3A, VT52 and the bounded ANSI/VT100 provider ship
with their test utilities on the appropriate target disks. See
[monitor implementation closure](../engineering/Monitor%201.0%20Implementation%20Closure.md)
for evidence and remaining qualification limits. VT52 completion is reopened:
native wire output is corrected, but portable backend and native display
qualification are still required. The original design selected
the bounded RSX approach from the
[monitor memory review](../engineering/Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md);
its audit prototypes are not the production providers.

## Scope and terminal personalities

BetterCP/M 1.0 will provide terminal emulation through a loadable monitor RSX,
with compact BIOS hooks and the existing basic console as the fallback.
The three committed 1.0 personalities are ADM-3A (the Montezuma Micro behavior
on Model 4), VT52, and a defined ANSI/VT100-compatible subset. Each requires
its own test utility. ANSI/VT100 is intended for ordinary cpmsim use in macOS
and compatible Linux terminals; its supported subset and qualification are
recorded in the [ANSI provider record](../engineering/ANSI%20Provider%20Foundation%20Qualification.md). ANSI.RSX renders ANSI host output. Corrected VT52.RSX emits native VT52
controls and requires a VT52 endpoint; it no longer translates to ANSI.
VT52 portable-backend and native endpoint qualification remain open; see the
[native correction audit](../engineering/VT52%20Native%20Correction%20Qualification.md). Use one active monitor provider;
platform-specific builds may share parser and rendering source where useful.
Only one monitor provider may be resident at a time.

This supplies a de facto TCAP capability: the loaded provider supplies the
console's terminal personality. `TCAP` is a working name, not a frozen filename,
capability-record format, query API or database. General capability discovery,
terminal-profile configuration and a broader portable TCAP interface remain
post-1.0 work. The monitor layer may support VIEW and existing full-screen
software; this decision does not itself approve or qualify those utilities.

The [post-1.0 terminal architecture outline](../engineering/POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md)
preserves the later discussion agenda. It is an incomplete proposal, not an
extension of the frozen 1.0 hook or capability contracts.

## Console boundary

Fixed BIOS trampolines shall route console operations to either the active
provider or the basic backend. They must cover direct BIOS callers as well as
BDOS-mediated console access. A BDOS-output-only interceptor is insufficient.
Programs that bypass BIOS and access hardware directly remain outside this
terminal-emulation boundary.

Keep the standard BIOS vectors and calling conventions intact. Hook targets
and parser state belong in protected writable memory; immutable or ROM code
must not be patched. Define a backend interface that lets the provider reuse
screen primitives without recursively entering its own hooks or calling BDOS
from a BIOS callback. Input/status handling and the private cursor operation
must be coordinated with output parsing where the chosen terminal requires it.

Without a provider, retain today's usable basic console: prompt and command
editing, text output, CR/LF, backspace, scrolling and the existing clear-screen
operation. This fallback does not promise full ADM-3A or VT52 emulation.

## Startup and lifetime

Use the existing saved cold-start command to run a SUBMIT script, for example
`SUBMIT STARTUP`. The Model 4 STARTUP.SUB loads ADM3A through ordinary RSX management after
the banner. The cpmsim script remains banner-only; users can load VT52 or ANSI
explicitly or edit the script. Provider and script filenames are recorded in
the distribution manifest. No special
BIOS monitor-file search or autoload mechanism is required.

The saved startup command runs once on cold boot. Warm boot preserves the
loaded monitor and reconstructs the command environment without rerunning the
script. Startup suppression and command failure retain the existing cold-start
rules; failure to install a monitor must leave the basic console usable.

Installation, reconstruction, movement, failed transactions and unloading
must never leave BIOS targets pointing into released or stale module memory.
Publish a provider only when its installation is committed. Rebind external
hook targets after movement, restore the basic backend before releasing the
provider, and preserve or restore the prior binding on rollback. Ordinary
STATEFUL repair of pointers inside a module does not by itself repair pointers
owned by BIOS. The implemented binding/lifecycle contract supports STATEFUL
providers, retained movement and unloading; no COLD_ONLY restriction is used.

## Memory policy

The core system must retain at least 53K TPA with no RSXs loaded. A monitor RSX
may reduce available TPA under the established extension policy. Report its
page-rounded allocation and any first-provider manager reservation separately
from permanent BIOS growth. Unloading it releases its allocation; unloading
the last RSX must restore the 53K core baseline. Other loaded RSXs retain their
own allocations.

Compact permanent hooks and any backend changes must fit the qualified core
layout without reducing that baseline. The audit measured hook prototypes,
not a complete installed-provider cost. The measured BIOS/BDOS savings remain
qualification candidates, not permission to adopt unverified production changes.

The implementation design and isolated feasibility probes are recorded in
[Monitor RSX Hook and Lifecycle Contract](../engineering/Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md).
Production integration and the selected qualification campaigns are complete.
See the implementation closure for the difference between these completed
contracts and release-wide testing still to be performed.

## Implementation acceptance

The implemented interface is qualified through the shared and target-specific
campaigns linked in the closure record, covering:

- BIOS and BDOS console paths, documented terminal controls and screen behavior;
- basic-console operation with no provider or after failed installation;
- cold startup, warm boot, provider movement, transaction rollback and unload;
- ROM ownership, register/stack contracts and unloaded/loaded memory accounting;
- command editing and cursor behavior while terminal parsing is active.

The Model 4 control-code conflict is resolved: internal clear/home callers use
operation 4 rather than inserting literal 1Ch into terminal output. MM-style
ADM3A retains 1Ch insert-line behavior. The production VT52 provider supersedes
the audit sample and has its own live, application and protected-ROM evidence.

## Provider behavior

[Monitor Provider Behavioral Requirements](../engineering/Monitor%20Provider%20Behavioral%20Requirements.md) defines the MM-style ADM-3A and VT52 personalities, input/reply queue semantics and qualification cases.
