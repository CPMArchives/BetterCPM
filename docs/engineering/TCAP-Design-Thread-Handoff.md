# BetterCP/M — Portable terminal capabilities (TCAP)

**Maintainer clarification, 8 November 2026:** TYPE, TED and HELP were illustrative
consumers, not an exhaustive set of utilities needing TCAP assessment or changes.
The [full utility impact audit](TCAP-Utility-Impact-Audit.md) covers all 52 registered utilities and
records a confirmed TED integration regression. Earlier three-name lists must
not be used to infer migration policy. The shared paging library is future exploration; compatibility checks apply
to every affected utility in 1.1. No exhaustive migration set is inferred.
Publication remains held.

## Why this thread exists

Bring TCAP forward as a **system-wide design priority during 1.1 planning**.
TYPE, TED and HELP already need answers about the active display. Settling
those answers once will let each utility concentrate on its own job. The
first deliverable is a reviewed engineering proposal. Implementation scope,
release assignment and adoption order are open.

## Three cases the design must explain

| Consumer | Question the utility needs answered |
| --- | --- |
| TYPE | Transient `:TYPE /P` currently assumes 80×24. Which dimensions should it use to count wrapped rows, leave space for its prompt and revisit a page? Ordinary TYPE must continue to work through the CP/M console. |
| TED | TED already uses SCRN 1.1 and expects an 80×24 viewport with cursor positioning, writing and erasure. How can the editor establish that it can render and restore its screen before it starts editing? How should it report a missing essential operation? |
| HELP | An author writes standard Markdown such as `**read-only**`. HELP interprets the markup and asks the display layer for strong emphasis. How can the active profile choose bold, a supported standout style such as reverse video, or plain text? How should HELP paginate when screen dimensions are unknown? |

HELP's document syntax, archive search, menus and content belong to the HELP
workstream. TCAP owns the display questions those features expose. TYPE's
paging controls and TED's editing commands likewise belong to their utilities.

## Architecture to preserve

Legacy CP/M programs continue to write their configured terminal sequences
through the normal console. Users can select ADM-3A, VT52 or ANSI personalities
as their applications require. BetterCP/M-aware utilities may use a portable
interface. Keep the terminal personality (the protocol an application sees)
distinct from the backend (the hardware or host that renders it).

BetterCP/M already has Monitor RSXs, a typed SCRN 1.1 interface and optional
SCX capability and rendition operations. The Model 4 backend advertises
reverse video; the ANSI host backend can encode styles that the endpoint must
still be capable of displaying. A configured 80×24 viewport and a measured
terminal size are different facts. TCAP is a working name. The ABI, provider
ownership and profile format remain open.

## First assignment

1. **Audit the current paths.** Trace one line of console output, a paged TYPE
   display and a TED screen update. Identify which layer knows the geometry,
   supported attributes, cursor operations and current rendering state.
2. **Draft the smallest shared contract that covers the three cases.** Define
   usable, unsupported and unknown results. Separate optional emphasis from
   operations a full-screen editor requires. Decide how a caller requests,
   scopes and restores a style without bypassing BDOS console interception,
   pausing or printer echo. Keep presentation controls out of file and printer
   output. Cover cancellation, errors, warm boot and provider changes.
3. **Compare implementation choices.** Start with the existing monitor and
   SCRN/SCX facilities. Assess what a small shared utility library could do
   and identify any operation that genuinely needs a provider change. Account
   separately for unloaded TPA, loaded provider memory and transient workspace
   against the 1.1 memory policy.
4. **Return for design review** with a capability/consumer matrix, a proposed
   interface, fallback rules and a qualification plan. Use plain-console
   HELP or TYPE and full-screen TED as contrasting cases. Cover cpmsim and
   Model 4, and include Model II as its maintained port becomes available.
   Record what has been demonstrated and what still needs a small prototype.

Use Z-System TCAP descriptions as historical input. Expanding the terminal
catalog and adopting additional emulation protocols are later decisions.

## Engineering proposal draft

The [TCAP engineering proposal](TCAP-Engineering-Proposal.md) records a static
audit of Monitor, SCRN and SCX, proposed consumer contracts and qualification
gates. Its consolidated design package is the entry point for one engineering
review, including the detailed semantic contract, owner/transaction design and
remaining feasibility gates. It is not an accepted ABI or an implemented facility.
Implementation scope and release assignment remain open.

## Starting references

- [1.1 engineering specification](1.1-ENGINEERING-SPECIFICATION.md) and [living backlog](../../TODO.md)
- [Terminal Monitor RSX architecture](../architecture/31%20Terminal%20Monitor%20RSX.md)
- [Terminal architecture outline, especially sections 21–22](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md) and [SCRN/SCX backend ABI](Unloadable%20Screen%20Backend%20ABI.md)
- [TYPE page replay](../../src/utilities/common/typepage.inc), [TED frontend](../../src/utilities/ted/frontend.mac), [Model 4 backend](../../src/rsx/screen/crt80x24.mac) and [ANSI host backend](../../src/rsx/screen/ansi-host.mac)
