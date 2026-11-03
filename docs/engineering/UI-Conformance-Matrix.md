# Utility UI conformance matrix

Reviewed 3 November 2026. **Not a blanket platform qualification.**

C = Conforming in the named bounded evidence; E = intentional compatibility/context exception; N = N/A; O = Outstanding (unverified or conflicting).
Columns separate behavior and applicability. A shared include is never itself evidence.
Query C refers to compiled host checks; platform execution must be read separately below.
Invalid O means suite-wide malformed/combination coverage is incomplete, not a demonstrated parser defect.
Exception cells retain the utility-specific specification; they do not waive data-integrity checks.

| Utility | /HELP | /VER | Invalid/malformed | Editing | Escape/cancel | Q | Defaults | Confirm | Status | /40 | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADMTST | C | C | O | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| ANSITST | C | C | O | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| BYE | C | C | C | N | C | N | C | C | N | N | shared immediate Y/N; explicit default No |
| CLS | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| COMPARE | C | C | C | N | C | C | N | N | E | C | forward display paging; read-only |
| CONFIG | C | C | O | E | E | E | E | E | E | N | compat editor/menu controller; fixed geometry |
| COPY | C | C | O | E | E | E | E | E | N | N | compat append/choice; overwrite/recovery semantics |
| CPX | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| CR | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| CRCKSUM | C | C | C | N | E | N | E | E | N | C | space exception; local decision loop; direct Ctrl-C; ESC invalid |
| DASM | C | C | C | E | E | E | N | E | E | N | only-Y CHIN; historical command language |
| DDT | C | C | O | C | C | E | E | N | N | N | standard field with debugger-specific aliases/empty input |
| DIR | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DLINK | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DSYM | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DUMP | C | C | O | E | E | E | N | N | E | C | compat editor/renderer; navigation retained |
| DUP | C | C | O | N | E | E | N | E | E | N | menu/drive/only-Y approval; no new defaults |
| ED | C | C | O | E | E | E | E | E | N | N | explicit DRI editor/command-language boundary |
| ERA | C | C | O | N | E | N | N | E | N | N | compat retry/help/abort choices |
| LINK | E | E | E | E | E | E | E | E | E | E | unmodified selected third-party tool; original interface |
| LZH | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| MD5SUM | C | C | C | N | E | N | E | E | N | C | same compact checksum engine; allocation exception; independent digest |
| MOUNT | E | E | O | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| MOVE | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| NOAH | C | C | O | N | C | E | C | C | E | E | shared choices; overlay and navigation retained |
| PATCH | C | C | C | N | C | N | N | N | N | E | operation cancellation/acknowledgment; narrow report option |
| PIP | C | C | O | E | E | E | N | E | N | N | replacement binding only; command/data language |
| R | E | E | O | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| RCP | E | E | E | E | E | E | E | E | E | E | frozen resident command package; transient interfaces reviewed separately; registry/development command, not current disk membership |
| REN | C | C | O | E | E | E | N | E | N | N | compat append/choice; cooked transport boundary |
| RESPACK | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| RLMBUILD | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| RSX | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SEARCH | C | C | C | N | C | C | N | N | E | C | forward paging; literal pattern parser |
| SQ | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| STAT | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SUBMIT | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SYSBUILD | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| SYSGEN | C | C | O | N | E | N | N | E | N | N | destination and only-Y approval |
| TED | C | C | O | C | C | E | C | C | C | N | standard fields/choices; immediate Y/N; No skips, Cancel stops |
| TIME | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| TYPE | C | C | O | N | E | E | N | N | E | N | page/file navigation is an application protocol |
| UNCR | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| UNLZH | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| USER | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| USQ | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| VER | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| VT52TST | C | C | O | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| W | E | E | O | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| WARM | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| XSUB | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| ZSM4 | E | E | E | E | E | E | E | E | E | E | unmodified selected third-party tool; original interface |

## Evidence and limits

- Query evidence: `test_utility_finalization.py` (37 screens and manager parser checks), `test_remaining_utility_help.py`, `test_codec_versions.py`, `test_z80pack_bye.py`, and dedicated CONFIG/NOAH/staged-helper checks. Staged helpers remain E until an owned-versus-host query policy is approved.
- Shared controllers: `test_shared_ui.py`, `test_shared_ui_format.py`, `test_shared_ui_screen.py`, `test_shared_ui_layouts.py`, `build_native_shared_ui.py`. These cover compiled buffers, bounds, hostile callbacks, stack balance, cancellation, defaults, immediate choices, rendering and module omission. They do not certify native display transport.
- Consumer evidence: existing `test_*shared*` suites for CONFIG/COPY/REN/ERA/DUP/SYSGEN/PIP; `test_ddt_input.py`, `test_ted_frontend.py`; new checksum-transport/DASM byte campaigns and BYE full-core campaign. Exact receipts are indexed in the engineering summary. Legacy E behavior is compared rather than relabeled standard editing.
- Changed binary cpmsim campaign: `test_ui_integration_media.py --platform cpmsim`; executable/file readback and filesystem integrity are checked. CRC/MD5 native builds execute under stock CP/M and compare exact bytes. DASM native parity/help uses `test_native_remaining_help.py`.
- Changed Model 4 artifacts: **PASS for the bounded CRCKSUM/MD5SUM/DASM campaign**, twenty executed/captured phases on the reference system, including six query outputs, checksum creation/refusal/Ctrl-C, DASM restart refusal and independent file/filesystem checks. Exact payloads and receipts are in [current Model 4 evidence](evidence/2026-11-03-model4-pass/results.json). TED's two changed-binary native campaigns remain **Outstanding**. BYE and staged host helpers are cpmsim-only (Model 4 N/A). Unchanged utilities retain historical receipts only for matching hashes/configurations.
- Invalid/malformed C is bounded to the associated focused suites; it does not claim exhaustive arbitrary command language inputs. O cells are verification work, not permission to redesign syntax.
- `/40` C refers to that utility's own display modes, not a universal 40-column help promise. CRC/MD5/SEARCH/COMPARE paging and line bounds have focused suites; PATCH retains its own report option. Utilities without `/40` have N, except third-party E.

## Decisions and exceptions

All compatibility profiles are selected under sections 1 and 8 of the shared specification. Empty Enter, raw/cooked transport, Ctrl-C context, no-default approval and historical command languages intentionally differ. Q remains ordinary text inside fields. No Q/ESC aliases are invented for other protocols.

TED confirmation was corrected with maintainer approval. Its C cells are bounded compiled/cpmsim results from [current qualification](TED%20Shared%20Choice%20Qualification.md): immediate Y/N, default No, invalid retry, local cancellation, and distinct per-match No/Cancel. Model 4 execution remains Outstanding.

R/W currently use version-over-help precedence in the pinned host-transfer patch; owned Z80 utilities use help-over-version. This source-verified difference is explicit E under their separate staged-host contract, pending a policy decision. ZSM4 and LINK retain original options and line editing.

## Maintenance

`python3 tools/test_utility_ui_inventory.py` checks complete, unique matrix coverage against current System/Utilities/companion projections and the utility registry, and rejects unknown classifications. Add/update rows with any membership or behavior change; retain per-requirement proof and outstanding statuses.
