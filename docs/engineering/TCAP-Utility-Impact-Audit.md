# TCAP utility impact audit

Maintainer clarification, 8 November 2026: TYPE, TED and HELP were examples
of consumers motivating a system-wide terminal-capability facility. They were
not a definition of the complete set of utilities needing assessment or changes.
A repeated three-name list must not become a migration or exclusion policy.

This audit covers **all 52 registered utilities**, their shared helpers and
resident counterparts. The [machine-readable inventory](TCAP-Utility-Impact-Audit.json)
accounts for every registered name exactly once and hashes the inspected source
references. It is a source impact assessment, not execution qualification or
authorization to change every utility. Effects must be assessed per mode:
plain output, paging, interactive fields, full-screen editing and diagnostics
have different requirements.

| Utility or path | Current display dependency | Implication |
| --- | --- | --- |
| DUMP `/P` | Callable SCRN discovery, facts, positioning, erasure and pager geometry | A real screen client beyond the three examples. Integrated TCAP alone does not supply its SCRN interface. Assess a TCAP path or explicitly preserve the existing backend path. Ordinary dump output is separate. |
| TED | MCON 1.2 admission plus SCRN 1.1 typed screen operations and 80x24 contract | Existing functionality must survive integration. TCAP adoption needs an operation-by-operation rendering and input assessment, not merely a changed lookup version. |
| CONFIG, DUP, FDB | Shared disk UI: BIOS clear/home, Function 178 optional rendition/caret, inline editors; plain fallback exists | Assess the shared helper once and all its callers. They already operate through existing console/monitor facilities; not every caller needs independent terminal code. |
| SYSGEN | Its own clear/home and optional rendition calls using the same concepts | Another consumer of display policy; protect confirmations, failure handling and installation behavior. |
| CLS and the RCP path | Native BIOS clear/home directly | Affects both resident and transient forms; cannot be omitted from a system-wide assessment. |
| TYPE | Transient page replay assumes 80 columns and 23 text rows, calls internal clear; resident paging also assumes 23 rows | Plain TYPE is a normal console stream. Paging/clearing is the affected mode. Assess both resident and transient implementations. |
| ED | Page motion/types 23 lines; line-oriented editor behavior | A page-size policy consumer; its cursor means a document position, not necessarily a hardware cursor. Do not mistake every cursor label for a terminal dependency. |
| DIR | Column/page layout in the resident/shared command code | Assess layout assumptions; user-selected column output and plain listing are not equivalent to a full-screen renderer. |
| DDT | Bounded single-line editor using ordinary output, backspace and a visible caret | Compatibility/editor audit item. It has no direct SCRN/TCAP dependency; that is not a reason to require a wholesale migration. |
| ADMTST, VT52TST, ANSITST | Deliberate protocol sequences and MCON discovery | These test terminal personalities. Replacing their protocol output with TCAP would remove the behavior they are supposed to test. Their requirements/messages and compatibility still need reconciliation. |
| Remaining 37 registered utilities | Ordinary console output/input or host transfer; no direct display-provider dependency identified in this source pass | Review shared UI and mode-specific behavior; do not migrate a text stream solely because it prints help or a progress message. The JSON lists every name. |
| HELP | Reader delivery is held; not one of the 52 delivered utility registrations | A future consumer requirement, not evidence of a working reader and not a boundary on other consumers. |
| ZSM4, LINK and other third-party CP/M applications | Existing application/terminal contracts | Qualify legacy operation under the selected console. Their inclusion does not make them utilities this project should silently rewrite. |

## Confirmed integration regression

A disposable cpmsim run using the candidate System/Utilities pair executed:

```text
RSX LOAD ANSISCRN
RSX LOAD ANSI
B0:TED
```

Interactive TED returned its missing-screen error instead of opening. This is
not a help/version-only observation. Source confirms that TED requests MCON
major 1/minor 2, while the integrated ANSI carrier advertises MCON 1.0. Loading
ANSISCRN does not repair that admission mismatch. The transcript digest is in
the audit JSON; the local probe is `build/release11-ted-compatibility-probe/`.

Do not advertise the integrated module as MCON 1.2 merely to pass this check:
MCON 1.2's full-control forwarding contract is not established by the compact
module's selectors 0–5. Determine TED's actual required operations, then make
and qualify a narrow compatibility correction or an approved consumer migration.
This is a release blocker under the existing-compatibility commitment.

## Scope and acceptance

TCAP 2.0 currently provides facts, clear, position, erase-line, emphasis and
normal baseline, with a same-owner/routing helper. It does not automatically
replace every SCRN/SCX operation or every input/editor policy. An impact audit
must distinguish existing functionality, integration regressions, desired
TCAP adoption and genuinely new utility features.

The maintainer's examples establish neither an exhaustive three-utility
migration set nor blanket deferral of all other consumers. The release assignment
of broader consumer adoption requires clarification; HELP delivery remains
held. No new utility behavior has been implemented by this audit, and no final
1.1 artifact acceptance is claimed.
