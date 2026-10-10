# Utility Version and Build Identification

## Adopted 1.0 contract

BetterCP/M-owned utilities accept standalone, case-insensitive `/VER`, with optional surrounding spaces. They print their identity and exit before normal initialization, file operations, provider access, or changing the caller's DU. `/VER` combined with operands or other options reports `Invalid /VER usage.` and performs no command operation. Longer tokens such as `/VERIFY` are not version requests and remain the command parser's responsibility.

Transient output:

```text
BetterCP/M DIR 1.0 (Build 001)
```

Resident output:

```text
BetterCP/M DIR 1.0 (Resident, RCP Build 001)
```

All resident RCP commands share the RCP package identity and build sequence. Each independent transient utility has its own sequence. Existing CPX/RSX `/V` facility reporting and subsystem interface/implementation versions remain separate and unchanged. Adopted third-party binaries are outside this contract.

## Authoritative metadata and numbering

`metadata/utility-versions.tsv` owns utility version and positive integer build number. Each sequence begins at 1 when this convention is adopted; this does not reconstruct historical build counts. Display uses at least three digits, with no rollover at 999.

Build sequences increase monotonically and never reset for major or minor versions. Advance the affected utility/package's counter when publishing a changed executable revision. Do not advance it for an identical rebuild or documentation/test-only changes. Review the counter with the executable changes before publication. Versions identify intended release and compatibility boundaries; builds identify particular revisions within that history. A 1.0 banner does not by itself declare qualification or release complete.

The first adoption assigns Build 001 to STAT, COPY, DIR, CONFIG, DUP, TIME, SYSGEN, SUBMIT, XSUB, CPX, RSX, USER, CLS, VER, SYSBUILD, RESPACK, RLMBUILD, and RCP. The transitional MOVE fallback reports its RCP identity pending its independent command contract.

## Implementation

The source include `src/utilities/common/version.inc` provides one shared recognizer. Build preparation expands source markers from the authoritative metadata into flat assembler source for both assemblers. No timestamp, host path, or environment-dependent counter is embedded. Transient RCP-derived entry wrappers select a transient banner; resident dispatch selects a resident banner. RCP includes the recognizer once, without changing CPX descriptors, BIOS, BDOS, or protected runtime state.

## Qualification

`tools/test_utility_versions.py` executes real assembled entries and resident dispatch. It checks version output, case/space handling, rejection of mixed forms, and register-preserving fall-through without BDOS access. Native RCP-derived builds must remain byte-identical to cross builds. Existing command qualification still applies to ordinary behavior.
