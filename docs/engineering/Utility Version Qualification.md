# Utility Version Qualification

The adopted contract is [Utility Version and Build Identification](../../specifications/UTILITY-VERSIONING.md). Build 001 is the first recorded identity under the new convention, not a historical build count. Utility versions and build counters are independent of subsystem interface/implementation versions.

## Implementation and size

Standalone `/VER` runs before normal initialization in completed BetterCP/M-owned runtime and native-build utilities. Resident dispatch selects a command-specific identity with the shared RCP build number. One shared source recognizer supplies exact-token, case-insensitive recognition and invalid-combination rejection. Transient binaries remain self-contained.

RCP grows from 5,370 to 6,053 code/data bytes, with rounded allocation increasing from 5,376 to 6,144 bytes (768 bytes). The per-command display strings are part of that increase. No BIOS/BDOS code, protected-data allocation, CPX descriptor, or subsystem version is changed. RCP remains reclaimable with the command environment.

Current transient RCP-derived binaries retain their existing complete-package source model; each grows 898 bytes, including resident dispatch strings and the transient identity table. DIR.COM is 8,483 bytes and COPY.COM is 11,238 bytes. Later dead-code elimination is separate from the reporting contract.

## Evidence

- `tools/test_utility_versions.py`: 118 assembled-entry checks pass: all 17 transient identities, all nine resident identities, mixed-form rejection, and register-preserving, service-free ordinary parser fall-through.
- Live z80pack: all 17 transient and nine resident identities pass, plus invalid `/VER /B` rejection and ordinary DIR after version requests. Transcript: `/private/tmp/utility-versions-z80pack-20261010/session.txt`.
- Live Model 4/trs80gp: eight resident/transient reporting and mixed-form rejection cases pass. Screens retained in `/private/tmp/utility-versions-model4-20261010`.
- Native ZSM4/LINK and cross builds: RCP.CPX and all six RCP-derived transient outputs are byte-identical.
- Ordinary COPY filespec/options, destination mapping/conflicts, and allocation/decimal reporting regressions pass.
- DIR option reset/failure atomicity (27 valid, 38 invalid), rendered columns (176 cases), and allocation metrics (450 cases) pass.

The existing `tools/test_subsystem_versions.py` stops because it still requires README to say BetterCP/M 0.3. README had already been changed to 1.0 development before this increment; this obsolete expectation is not evidence of a utility-version failure and was not broadened into a subsystem-release revision here.
