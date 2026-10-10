# Transient COPY — Frozen z80pack Qualification

Date: 2026-10-10

This campaign qualifies the completed transient COPY.COM on z80pack. Model 4,
CPX-to-transient handoff, and full BetterCP/M release conformance remain separate.
It introduces no implementation behavior and makes no BIOS/BDOS changes.

## Binary and evidence

- COPY.COM: 10,303 bytes.
- SHA-256: `c0c6ee7cde8eedd32f3fb7a7ca42b67a0def6de81ff3c8ed8cee3a1d8a1e9b27`.
- Bundle: `/private/tmp/copy-final-z80pack-bundle-20261010`.
- Manifest SHA-256: `28a6d8cdd5aa863352f729b0b7b93d4065b8a2ccce34b03ff53a2ba72a549f25`.
- All 722 inventoried files were checked against their recorded size and hash.

The bundle includes the exact input simulator disks and diskdefs, per-case final
media and transcripts, private controlled-failure binaries, run commands and exit
codes, tested COPY.COM, and source/test snapshots. `run-record.json` contains all
twelve native invocations; each report contains its own `evidence.json`.
The collector checks the COPY identity of every report before archiving. Its
negative check rejects a mismatched identity before creating an output directory.
RCP/BDOS snapshots are references; they are not claimed as independently qualified
components by this transient-only campaign.

## Native campaign

| Suite | Required behavior | Result |
| --- | --- | --- |
| du_sets | Compound selectors, source preservation, global mapping/capacity safety | PASS |
| mapping | Positional destination substitution and mapping conflict rejection | PASS |
| interactive | Y/N/O/S/R/?, rename validation, session policy, SUBMIT prompting | PASS |
| verify_flow | /V success, failure, retry, skip, batch and abort cleanup | PASS |
| cancel | Transfer/verification cancellation, prior copies retained, later reuse | PASS |
| select | Source predicates, aliases, precedence, metadata and filtered preflight | PASS |
| dest | Destination overrides, contradictions, multi-extent metadata, R/O protection | PASS |
| backup | ARC completion, skip/failure preservation, metadata-failure retention | PASS |
| errors | Read/write/close continuation, full-disk stop, failed-cleanup stop | PASS |
| reporting | Actual allocation, empty/multi-extent/overwritten files, mixed totals | PASS |
| batch | Global 64-file acceptance and 65-file rejection before mutation | PASS |
| skip | Explicit /S and protected read-only targets | PASS |

## Execution-level checks

Filespec grammar, destination mapping, operand qualifier splitting, all attribute
predicate states, destination attribute overrides, byte/word allocation maps,
1K/2K/4K/16K blocks, and unsigned decimal boundaries through 4,294,967,295 pass.
The implementation binaries remained unchanged throughout this campaign.
Native/host build equality for this binary was established in the reporting
increment; the final campaign consumes that frozen binary.

## Remaining qualification

Continue the corresponding completed transient behavior on Model 4/trs80gp and
preserve matching evidence. The first Model 4 results and remaining scope are
recorded in [the Model 4 qualification note](COPY%20Transient%20Model%204%20Qualification.md). This z80pack result does not qualify an older Model 4
COPY binary by inference. The separately specified handoff mechanism remains
outside this command-only campaign.
