# Utility Version and Build Identification

## Adopted 1.0 contract

The common query contract recognizes an exact, case-insensitive `/VER` token
anywhere in the bounded command tail, with space/TAB separators. It prints the
identity and ignores other arguments, returning before file/provider access or
changes to the caller's DU. An exact `/HELP` token takes precedence and displays
help instead. Longer tokens such as `/VERIFY` are ordinary parser input.

All utilities using the common `version.inc` recognizer adopt this contract,
including RCP resident dispatch, transient wrappers, PIP, DUMP and the owned
DDT adaptation. `/HELP` precedence applies where a utility implements help;
this rule does not add a help screen to utilities that do not yet provide one.
PIP's bracketed S/Q string data and CONFIG's quoted startup/format text remain
literal data rather than query tokens. Recognition respects those existing
command-specific literal-data boundaries.

Transient output:

```text
BetterCP/M DIR 1.0 (Build 001)
```

Resident output:

```text
BetterCP/M DIR 1.0 (Resident, RCP Build 001)
```

DUMP, DDT, SQ, USQ, CR, UNCR, LZH and UNLZH use the finalized
[visual identity](VISUAL-IDENTITY.md) compact layout: `NAME 1.0 (Build 001)`
followed by the implied-corner BetterCP/M Utilities identification and a short
purpose line. Version and build come from the same metadata;
no-file-access requirements remain the same. Query argument handling follows the common contract above. This adoption does not restyle the other existing utilities.

All resident RCP commands share the RCP package identity and build sequence. Each independent transient utility has its own sequence. Existing CPX/RSX `/V` facility reporting and subsystem interface/implementation versions remain separate and unchanged. Adopted third-party binaries are outside this contract.

## Authoritative metadata and numbering

`metadata/utility-versions.tsv` owns utility version and positive integer build number. Each sequence begins at 1 when this convention is adopted; this does not reconstruct historical build counts. Display uses at least three digits, with no rollover at 999.

Build sequences increase monotonically and never reset for major or minor versions. Advance the affected utility/package's counter when publishing a changed executable revision. Do not advance it for an identical rebuild or documentation/test-only changes. Review the counter with the executable changes before publication. Versions identify intended release and compatibility boundaries; builds identify particular revisions within that history. A 1.0 banner does not by itself declare qualification or release complete.

The first adoption assigns Build 001 to STAT, COPY, DIR, CONFIG, DUP, TIME, SYSGEN, SUBMIT, XSUB, CPX, RSX, USER, CLS, VER, SYSBUILD, RESPACK, RLMBUILD, and RCP. SQ, USQ, CR, UNCR, LZH and UNLZH each begin at Build 001 when adopting `/VER`. The transitional MOVE fallback reports its RCP identity pending its independent command contract.

## Implementation

The source include `src/utilities/common/version.inc` provides one shared recognizer. Build preparation expands source markers from the authoritative metadata into flat assembler source for both assemblers. No timestamp, host path, or environment-dependent counter is embedded. Transient RCP-derived entry wrappers select a transient banner; resident dispatch selects a resident banner. RCP includes the recognizer once, without changing CPX descriptors, BIOS, BDOS, or protected runtime state.

## Qualification

`tools/test_utility_versions.py` executes real assembled entries and resident dispatch. It checks version output, case/space handling, ignoring other arguments in mixed forms, and register-preserving fall-through without BDOS access. Native RCP-derived builds must remain byte-identical to cross builds. Existing command qualification still applies to ordinary behavior.


Compression command builders share `tools/codec_version.py` and
`src/utilities/common/codecver.inc`. They reuse the query portion of
`version.inc`, after establishing their private stack. A bounded scratch copy
normalizes TAB separators to spaces without changing the command tail; the
query and stack frames occupy the other half of the 256-byte stack. A handled
request restores entry SP and returns directly, without normal file-state
initialization, drive/user inquiry, DMA reset or warm boot. The compression commands also adopt [Utility Help](UTILITY-HELP.md);
help shares this early query path, with `/HELP` precedence for mixed queries. `tools/test_codec_versions.py` and
`tools/test_codec_versions_cpm.py` qualify the six command entries separately
from the wider utility suite.

The forgiving query adoption and focused regression results are recorded in
[Common Utility Query Qualification](../docs/engineering/Utility%20Query%20Qualification.md).
