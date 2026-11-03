# Targeted utility shared-library candidate report

3 November 2026. Read-only architectural audit accompanying shared UI integration.
No library described here is implemented or authorized by this report. The open
post-1.0 functional-commonality review remains a separate, broader workstream.

## Coverage and priorities

The [UI matrix](UI-Conformance-Matrix.md) enumerates every distributed command,
staged host helper and registry utility considered. Inspection covered their
builders and common-source selections as well as utility sources, so source
expansion is not mistaken for independent copies. The six codecs already share
`codecfile.mac`, `codecver.inc` and codec implementations; CRCKSUM/MD5SUM already
share traversal, output, support and selected parser routines; the file selectors
already use `duselect.inc`, `filespec.inc` and `attrselect.inc` in many consumers.
PATCH also expands COMPARE numeric/parser helpers through `tools/build_patch.py`; it is not another independent implementation of those algorithms. Those are existing reuse, not proposals to invent a competing library. The initial source scan recorded 224 utility/common source files and 11,509 routine/data labels; semantic equivalence is asserted only for the exact matches below.

No high-priority **new** library is justified for 1.0 by the evidence below.
The most measurable opportunities are small post-1.0 investigations; hypothetical
size wins are not counted as measured savings. Priority reflects engineering
value, not authorization or a release gate.

| Candidate | Locations and duplication | Significant differences | Proposed approach | Expected benefit | Register, stack, memory and compatibility risks | Priority | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Register-preserving BDOS wrapper | `src/utilities/ted/frontend.mac:TE_BDOS`, `src/utilities/ted/publisher.mac:TS_BDOS`, `src/utilities/ted/workspace.mac:TW_BDOS`: three identical instruction sequences, labels aside. Related wrappers: `src/utilities/common/dasmsafe.inc:D_BDOS`, `src/utilities/crc/support.inc:BDOS`, `src/utilities/compare.mac:SERVICE`, `src/utilities/patch.mac:SERVICE` | TED's three preserve BC/DE/HL/IX/IY and return A/flags; DASM additionally saves returned HL to `D_RETURN_HL`; CRC omits IY preservation. Other wrappers must be reviewed separately. | Investigate a local common callable TED routine first; selected-source macro only if independent assembly remains necessary. | Confirmed TED copies each contain 18 bytes. One callable implementation could save 36 static bytes before any linkage cost. A macro alone saves maintenance duplication, not emitted bytes. No demonstrated functional defect. | Five register pushes: 10 bytes plus call frames and BDOS depth. Export/link ownership and frontend early query path must remain valid; do not change returned flags or HL side channels. No resident data needed. | Medium | Investigate further after 1.0; retain other wrappers until their distinct ABIs are catalogued. |
| 32-bit decimal formatting | `src/utilities/compare.mac:DECIMAL`, `src/utilities/crc/support.inc:DECIMAL`; MD5SUM expands the CRC implementation, so it is not a third independent algorithm. Related 16-bit routine `src/utilities/common/printnum.inc:PN_U16` | Both 32-bit routines use repeated division by ten, but COMPARE prints via TEXT and preserves its input HL; CRC returns buffer pointer/length through NUMPTR/A. Different scratch and division loops. PN_U16 has different width and callback contract. | Later bounded converter returning a span, with explicit output adapters; compare against retaining both. | Consistent boundary behavior and smaller maintenance surface are plausible. No measured size improvement or inconsistent numeric result was found. | Must preserve full 0..4294967295, leading-zero policy, 11-byte output storage, pointer ownership and caller clobbers. A generic formatter could increase both programs. | Medium | Investigate further with emitted-byte and boundary comparison before designing an API. |
| Literal text and console output | `src/utilities/compare.mac:TEXT/PUT/UPPER`, `src/utilities/patch.mac:TEXT/PUT/UPPER`; CRC `support.inc:TEXT/CHAR`, TED `frontend.mac:TE_PRINT`, historical DASM `COUT` are related | COMPARE/PATCH TEXT loops are instruction-equivalent modulo output label; their PUT prologues are similar. CRC CHAR counts 40-column output and now protects modal input. TED uses SCRN; DASM supports capture/file output and quiet/count policy. ASCII UPPER in COMPARE/PATCH is identical. | A tiny parameterized source macro is a possible maintenance aid for the two exact matches; do not generalize the different output engines. | Removes a small confirmed source duplication. No runtime size saving from a macro; less benefit than maintaining local short loops. | NUL versus dollar terminators, cooked/direct control handling, registers and character-versus-display-cell width must remain explicit. Reusing the wrong output hook can turn local cancellation into warm boot. | Low | Retain existing code unless future repeated fixes demonstrate value. |
| Exact filename/DU validation | `common/filespec.inc:FP_VALIDATE`, `common/duselect.inc`; TED `operations.mac:OP_PARSE_FILE`, PIP operand parser, DDT command operands, checksum list parser | Existing shared selectors support lists/ranges/wildcards/attributes. TED requires an exact single identity; PIP accepts device and bracketed literal syntax; debugger operands are its command language. Similar tokens do not imply equivalent grammar. | Prefer extending adoption of the existing parser only after semantic equivalence is proven. Do not create a universal command-tail parser. | Potential consistency in 8.3 rejection and DU bounds. No newly demonstrated parser inconsistency from this read-only inspection. | Default DU, FCB high bits, case folding, optional extension, wildcard authorization and error position are compatibility-sensitive. Preserve PIP quoted/bracketed query boundaries. | Medium | Investigate further per consumer; retain specialized grammars. |
| FCB extent/random-record initialization | TED `publisher.mac:TS_RESETFCB`, `workspace.mac:TW_FCB_RESET`; CRC `output.inc:WTRESET`; file adapters in `common/dasmsafe.inc` and `codecfile.mac` | TED publisher resets an arbitrary FCB+12 for 23 bytes while preserving HL/DE/BC; workspace resets a fixed FCB with different clobbers. Other adapters reset 24 or 36 bytes and retain different identity/attribute fields. | Tiny local helper or macro with an explicit byte range; keep the already shared codec and checksum adapters. | Makes bounds and preserved identity easier to audit. Raw repetition is small; no proved data-integrity defect or aggregate saving. | One-byte extent-state differences matter. A generic zero-FCB routine can erase drive/name/attributes or omit CR/random state. Parameterization and wrappers can cost more than local instructions. | Low | Retain existing code pending a consumer-by-consumer state contract. |
| File publication/backup/recovery | TED `publisher.mac:TS_RUN`, DASM `common/dasmfile.inc` and `dasmsession.inc`, CRC `output.inc`, PATCH `patch/transaction.inc`, codec `codecfile.mac` | Similar create/close/rename sequences implement materially different fingerprint, replay, verification, backup, protection, multi-file/session and cancellation policies. This is functional overlap, not proven equivalent implementations. | No new publication framework. Compare state machines in the separate post-1.0 audit before considering extraction of individual exact primitives. | Possible long-term correctness review; no measured benefit of unification established here. | Highest data-loss and recovery risk; register/stack/workspace ownership and exact failure ordering differ. Existing fault-injection receipts would need extensive requalification. | Low | Retain existing code. |
| Command queries/error presentation | `common/version.inc:UV_QUERY`, `tools/utility_help.py:query_source`, codec query selection; staged R/W in `third_party/z80pack/patches/0005-host-transfer.patch` | Owned Z80 utilities already share exact bounded recognition. CONFIG and PIP retain literal-data boundaries. R/W are 8080 host adapters with version-over-help precedence and a separate host ABI. | Continue using existing query source; evaluate the host helpers separately, without a second query library. | Existing reuse already prevents most duplication. Host policy mismatch is a concrete review item, not a demonstrated need for a new library. | Must not interpret literal file data as queries, change precedence silently or introduce hardware dependencies into portable utilities. Pre-private-stack query depth is already tightly bounded. | Low | Retain existing libraries; seek an explicit host-helper policy decision separately. |

## Follow-up observation: no-operand tail validation

Low priority; retain existing code for 1.0. The follow-up contains four identical
36-byte instruction sequences (labels aside) at `ARG_SCAN`/`ARG_BAD` in
`src/utilities/admtst.mac`, `ansitst.mac`, `vt52tst.mac`, and `xsub.mac`.
Each accepts only spaces/TABs after the existing query handler and rejects any
other byte or counted length >=128; the dollar-terminated messages name different
utilities. This is confirmed duplication with the same grammar, distinct from
the specialized parsers above. A parameterized include/macro could remove source
maintenance duplication but saves no emitted bytes. A shared callable routine
would need an explicit message pointer, A/B/HL clobber contract and caller-stack
budget; current inline code adds no pushes or resident storage. ADMTST has only
three bytes left in its current 2-KiB allocation, so unmeasured abstraction
cost is unwelcome. No demonstrated maintenance problem justifies a new library
now. Investigate further only if additional equivalent consumers emerge; no
candidate implementation is authorized by this observation.

## Confirmed versus inferred

The TED BDOS wrappers and the paired TEXT/UPPER loops are confirmed instruction
matches after label normalization. Decimal formatting, FCB operations, filename
parsing and publication are functionally related with explicit differences;
they are not claimed to be byte-identical algorithms. No defect is inferred
merely from independent implementation. The checksum Ctrl-C finding is an
actual cpmsim reproduction in the integration work, not speculative audit risk.

All above utility groups are covered without modifying the frozen RCP/core,
third-party historical references, BIOS ports or unrelated codebase-audit items.
Implementation of any candidate requires separate review and authorization.
