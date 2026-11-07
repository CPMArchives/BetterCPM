# Utility UI conformance matrix

Reviewed 3 November 2026. **Not a blanket platform qualification.**

C = Conforming in the named bounded evidence; E = intentional compatibility/context exception; N = N/A; O = Outstanding (unverified or conflicting).
Columns separate behavior and applicability. A shared include is never itself evidence.
Query C refers to compiled host checks; platform execution must be read separately below.
Invalid O identifies remaining development-only review gaps and the resident
command gap recorded below; see the explicit scope below.
Exception cells retain the utility-specific specification; they do not waive data-integrity checks.

| Utility | /HELP | /VER | Invalid/malformed | Editing | Escape/cancel | Q | Defaults | Confirm | Status | /40 | Basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADMTST | C | C | C | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| ANSITST | C | C | C | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| BYE | C | C | C | N | C | N | C | C | N | N | shared immediate Y/N; explicit default No |
| CLS | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| COMPARE | C | C | C | N | C | C | N | N | E | C | forward display paging; read-only |
| CONFIG | C | C | C | E | E | E | E | E | E | N | compat editor/menu controller; fixed geometry |
| COPY | C | C | C | E | E | E | E | E | N | N | compat append/choice; overwrite/recovery semantics |
| CPX | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| CR | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| CRCKSUM | C | C | C | N | E | N | E | E | N | C | space exception; local decision loop; direct Ctrl-C; ESC invalid |
| DASM | C | C | C | E | E | E | N | E | E | N | only-Y CHIN; historical command language |
| DDT | C | C | E | C | C | E | E | N | N | N | standard field with debugger-specific aliases/empty input |
| DIR | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DLINK | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DSYM | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| DUMP | C | C | C | E | E | E | N | N | E | C | compat editor/renderer; navigation retained |
| DUP | C | C | C | N | E | E | N | E | E | N | menu/drive/only-Y approval; no new defaults |
| ED | C | C | C | E | E | E | E | E | N | N | explicit DRI editor/command-language boundary |
| ERA | C | C | C | N | E | N | N | E | N | N | compat retry/help/abort choices |
| FDB | C | C | C | O | O | C | O | O | O | O | [Compiled queries and malformed converter syntax](209-standard-queries.md#validation). [Workbench Q](FDB-Main-Menu-Correction.md) was exercised on both platforms. Other cells await individual review. |
| LINK | E | E | E | E | E | E | E | E | E | E | unmodified selected third-party tool; original interface |
| LZH | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| MD5SUM | C | C | C | N | E | N | E | E | N | C | same compact checksum engine; allocation exception; independent digest |
| MOUNT | E | E | E | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| MOVE | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| NOAH | C | C | C | N | C | E | C | C | E | E | shared choices; overlay and navigation retained |
| PATCH | C | C | C | N | C | N | N | N | N | E | operation cancellation/acknowledgment; narrow report option |
| PATH | C | C | C | N | N | N | N | N | N | N | Command-tail utility. Bare PATH displays the list. Exact help and version queries precede edits. Invalid replacements preserve the old list. See [numeric PATH qualification](Numeric-PATH-1.1.md#qualification). |
| PIP | C | C | C | E | E | E | N | E | N | N | replacement binding only; command/data language |
| R | E | E | E | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| RCP | O | C | O | E | E | E | E | E | E | E | resident DIR/ERA/TYPE/REN/CLS/USER/VER/COPY/MOVE; version dispatch checked; standard help missing; resident tail review outstanding |
| REN | C | C | C | E | E | E | N | E | N | N | compat append/choice; cooked transport boundary |
| RESPACK | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| RLMBUILD | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| RSX | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SEARCH | C | C | C | N | C | C | N | N | E | C | forward paging; literal pattern parser |
| SQ | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| STAT | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SUBMIT | C | C | E | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| SYSBUILD | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| SYSGEN | C | C | C | N | E | N | N | E | N | N | destination and only-Y approval |
| TED | C | C | C | C | C | E | C | C | C | N | standard fields/choices; immediate Y/N; No skips, Cancel stops |
| TIME | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| TYPE | C | C | C | N | E | E | N | N | E | N | page/file navigation is an application protocol |
| UNCR | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| UNLZH | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| USER | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| USQ | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| VER | C | C | C | N | N | N | N | N | N | N | command-tail operation; no generic prompted field |
| VT52TST | C | C | C | E | E | E | N | N | E | N | raw keyboard/terminal diagnostic protocol |
| W | E | E | E | N | N | N | N | N | N | N | staged cpmsim host helper; separate query/8080 ABI; source review only |
| WARM | C | C | O | N | N | N | N | N | N | N | command-tail operation; no generic prompted field; registry/development command, not current disk membership |
| XSUB | C | C | C | N | N | N | N | N | N | N | Optional source DU. [Source parser and guest qualification](RSX-Offline-Loading-Implementation.md) supersede the no-operand tests for revision 008. |
| ZSM4 | E | E | E | E | E | E | E | E | E | E | unmodified selected third-party tool; original interface |

## Resident command coverage correction — 4 November 2026

Named utility rows above describe the transient implementations. They do not
qualify the resident command of the same name: ordinary unqualified invocations
can be claimed by `RCP.CPX` before a `.COM` file is loaded. Resident CLS and MOVE
also remain relevant even though separate transient files are not distributed.
The earlier blanket frozen-RCP exception did not establish user-visible
conformance and cannot support a claim that all shipped command paths are done.

The help contract requires exact case-insensitive `/H` and `/HELP` queries,
help-over-version precedence and console-output-only handling before operations.
Source review at `31dba474927be420796ab9e4cb3c75daddd6f0ab` confirms that
`tools/utility_versions.py` injects help into transient paths, while resident
dispatch uses `src/cpx/feature-hint.inc:RH_VERSION` and the version-only
`UV_QUERY`. All nine resident commands need separate help acceptance checks.
The reported revision 017 produces `NO FILE` for `ERA /HELP`, invalid-filespec
diagnostics for TYPE/REN `/H`, and short COPY syntax for `/H`; the COPY output
is not a standard help screen. `/VER` works and does not prove help conformance.

A compiled relocated revision 016 development carrier reproduces these failure
classes for `/H` and `/HELP`; ERA reaches BDOS state/search calls instead of a
pure help return. This is additional host evidence, not platform qualification
of revision 017. The historical compiled resident version checks support the
bounded `/VER` C cell; no new help or platform pass is claimed. Resident malformed
tail handling remains O pending its own review. Release/package freeze restricts
production changes; it does not convert these gaps into conforming behavior.

## Release disposition and 1.01 scope

On 4 November 2026 the maintainer withdrew the earlier lock override for these
issues and reaffirmed the 1.0 release/package lock. Only showstoppers warrant
reconsidering that lock. The demonstrated help/version inconsistencies are
accepted non-showstopper usability defects for 1.0, targeted for **1.01**.
The maintainer also explicitly accepts the reported `:DIR *.COM` issue for
1.0 and defers its correction to **1.01**. That invocation selects transient
DIR; track its defect separately from resident help/version dispatch. This
disposition records the reported invocation, not a new diagnosis or test pass.
No resident fix, component revision change or release-artifact rebuild is
authorized for 1.0 by this correction. Preserve the separate implementation
candidate as deferred work; its development checks do not qualify the locked
release or establish final 1.01 acceptance. RCP's outstanding cells remain O.

The 1.01 work should provide:

- Separate resident/transient identification using each implementation's actual
  revision and a clear indication of which implementation is running.
- Implementation-specific `/H` and `/HELP` screens. Compact resident help must
  describe resident syntax and supported switches; transient help must describe
  the transient implementation. A pointer to `:COMMAND /H` must explicitly label
  its additional features rather than imply they are supported by the resident.
- Brief local help for resident-only commands; no separate CLS.COM is required.
- Correct FDB.COM's compact main menu to Engineering Specification 209's
  version heading, grouped bracketed choices and bracketed choice prompt,
  preserving commands and exit behavior. See the [FDB erratum](../releases/1.0-ERRATA.md#fdb-main-menu-presentation)
  and the explicit 1.01 task in [the backlog](../../TODO.md#101-release-corrections).
- Correct the separately reported transient DIR case issue: `:DIR *.com`
  incorrectly finds no files, while uppercase works. See the
  [focused correction and qualification](DIR-Lowercase-Filespec-Correction.md).
- Resolve XSUB's Utilities Disk companion-location mismatch, recorded with the
  copy-to-A0 workaround in the [1.0 errata](../releases/1.0-ERRATA.md#xsub-companion-must-be-copied-to-a0).
  Review packaging/installation and loading alternatives before choosing a fix;
  qualify actual batch input and reconstruction, not merely help/version output.
- Focused query-precedence and malformed-argument review across all nine
  resident commands, with separate resident-path acceptance checks that cannot
  pass by loading a matching COM file.
- Measured code/text, carrier and command-environment costs before selecting
  the final implementation; retain CPX reclaimability and qualify affected
  artifacts on both supported platforms after the implementation stabilizes.

## Evidence and limits

- Query evidence: `test_utility_finalization.py` (37 screens and manager parser checks), `test_remaining_utility_help.py`, `test_codec_versions.py`, `test_z80pack_bye.py`, and dedicated CONFIG/NOAH/staged-helper checks. Staged helpers remain E until an owned-versus-host query policy is approved.
- Shared controllers: `test_shared_ui.py`, `test_shared_ui_format.py`, `test_shared_ui_screen.py`, `test_shared_ui_layouts.py`, `build_native_shared_ui.py`. These cover compiled buffers, bounds, hostile callbacks, stack balance, cancellation, defaults, immediate choices, rendering and module omission. They do not certify native display transport.
- Consumer evidence: existing `test_*shared*` suites for CONFIG/COPY/REN/ERA/DUP/SYSGEN/PIP; `test_ddt_input.py`, `test_ted_frontend.py`; new checksum-transport/DASM byte campaigns and BYE full-core campaign. Exact receipts are indexed in the engineering summary. Legacy E behavior is compared rather than relabeled standard editing.
- Changed binary cpmsim campaign: `test_ui_integration_media.py --platform cpmsim`; executable/file readback and filesystem integrity are checked. CRC/MD5 native builds execute under stock CP/M and compare exact bytes. DASM native parity/help uses `test_native_remaining_help.py`.
- Changed Model 4 artifacts: **PASS for the bounded CRCKSUM/MD5SUM/DASM campaign**, twenty executed/captured phases on the reference system, including six query outputs, checksum creation/refusal/Ctrl-C, DASM restart refusal and independent file/filesystem checks. Exact payloads and receipts are in [current Model 4 evidence](evidence/2026-11-03-model4-pass/results.json). TED's current-payload native `choices` campaign also **passes**; corrected `choice-scope` also **passes**, independently verifying per-match No/Yes/Cancel and exact target/backup bytes (see [scope receipt](evidence/2026-11-03-ted-model4-scope/results.json)). The earlier harness case mismatch remains separately archived. BYE and staged host helpers are cpmsim-only (Model 4 N/A). Unchanged utilities retain historical receipts only for matching hashes/configurations.
- Invalid/malformed C is bounded to the associated focused suites; it does not claim exhaustive arbitrary command language inputs. O cells are verification work, not permission to redesign syntax.
- `/40` C refers to that utility's own display modes, not a universal 40-column help promise. CRC/MD5/SEARCH/COMPARE paging and line bounds have focused suites; PATCH retains its own report option. Utilities without `/40` have N, except third-party E.

### Argument-validation follow-up

The [follow-up record](UI-Argument-Validation-Followup.md) and its archived receipts
supply bounded malformed-tail evidence for the 28 newly classified C entries.
ADMTST/ANSITST/VT52TST/XSUB now reject operands after query processing, before
provider lookup or installation. Their host, cpmsim and current-payload Model 4
checks pass. The [22-phase native receipt](evidence/2026-11-03-ui-noargs-model4-pass/results.json)
includes all captures and independently read-back payloads; the previous #571
receipts are not transferred to these changed binaries.
The other 24 entries use existing parser/full-command suites without production
changes. USER/VER retain the frozen RCP-derived `?` diagnostic format; C records
detection and existing grammar, not a new diagnostic presentation.
UNLZH's 75 self-contained full-Z80 cases pass; missing historical CRLZH fixtures
prevent its separate historical-archive campaign from running.

The six remaining O entries are **CLS, MOVE, RESPACK, RLMBUILD, SYSBUILD, WARM**.
These are registry/development commands absent from current disk membership.
Their query checks pass, but operational-tail behavior is not accepted as
conforming merely because they are outside the release. The fixed-input builders
ignore operational tails (`START` in their respective sources); changing that
behavior is not included in the four-utility fix. No production requirement is
silently waived. That review concerns transient rows only. The resident RCP
command paths have an explicit outstanding help and malformed-tail review above.

## Decisions and exceptions

All compatibility profiles are selected under sections 1 and 8 of the shared specification. Empty Enter, raw/cooked transport, Ctrl-C context, no-default approval and historical command languages intentionally differ. Q remains ordinary text inside fields. No Q/ESC aliases are invented for other protocols.

TED confirmation was corrected with maintainer approval. Its C cells are bounded compiled/cpmsim results from [current qualification](TED%20Shared%20Choice%20Qualification.md): immediate Y/N, default No, invalid retry, local cancellation, and distinct per-match No/Cancel. Both bounded current-payload Model 4 campaigns pass, including per-match No/Cancel and exact saved/backup data.

DDT's non-query startup keeps historical CCP-FCB semantics under
`DDT Specification.md`, “Utility identity and startup”; debugger operand syntax
is not replaced by a generic switch parser. SUBMIT preserves the stock
`SUBMIT name [p1 ... p9]` grammar and CCP-prepared FCB/source-line diagnostics
specified in `129 Stock-Compatible SUBMIT and XSUB.md`. Their invalid-tail E
cells record these existing language boundaries, not newly introduced aliases.
R/W/MOUNT retain their staged upstream host/8080 grammar in
`third_party/z80pack/patches/0005-host-transfer.patch`, `0006-guest-mount.patch`
and `0007-mount-help.patch`; this is source-reviewed E, not native UI qualification.

R/W currently use version-over-help precedence in the pinned host-transfer patch; owned Z80 utilities use help-over-version. This source-verified difference is explicit E under their separate staged-host contract, pending a policy decision. ZSM4 and LINK retain original options and line editing.

## Maintenance

`python3 tools/test_utility_ui_inventory.py` checks complete, unique matrix coverage against current System/Utilities/companion projections and the utility registry, and rejects unknown classifications. Add/update rows with any membership or behavior change; retain per-requirement proof and outstanding statuses.
