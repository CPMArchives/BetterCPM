# Architecture Readiness Review

Status: Initial review
Date: 2026-08-31

## Purpose

This review determines whether the fifteen BetterCP/M architecture documents define a sufficient basis for Phase 2 engineering specifications and identifies unresolved matters that block particular implementation milestones.

## Conclusion

The architecture is ready to enter Phase 2.

No unresolved architectural question prevents baseline platform bring-up. The first executable milestone can therefore be a 128-byte `cpmsim` stage-zero boot record that loads and enters a diagnostic stage-one image.

The architecture does not yet provide enough detail to implement the complete resident system. That is expected: the missing decisions are engineering-specification subjects explicitly delegated by the architecture.

## Findings by milestone

### Baseline bring-up

No architectural blocker exists. The baseline platform specification already defines:

- z80pack `cpmsim` as the initial target;
- a Z80 with a 64 KiB address space;
- a 128-byte boot record loaded at `0000h` and entered at `0000h`;
- console status and data at `cpmsim` ports 0 and 1;
- the raw-sector interface at ports 10 through 17; and
- the validated 77-track, 26-sector, 128-byte-sector drive geometry.

The remaining decisions—stage-one placement, disk-image layout, initial register contract, diagnostic behavior, build procedure, and acceptance tests—belong in the Baseline Bring-Up engineering specification.

### Resident-system implementation

The following must be specified before implementation of the complete resident operating system:

1. **Memory layout and quantitative budgets.** Exact resident placement, CCP disposition, BIOS/BDOS-equivalent boundaries, stack ownership, buffer placement, system-state placement, and minimum TPA must be decided and measured.
2. **System-image organization.** Component ordering, assembly and linking model, load addresses, padding, configuration data, and boot-time loading must be defined.
3. **Hardware-Abstraction interface.** The minimum internal calls, register conventions, status results, mutable platform configuration, and relationship to the compatibility-visible BIOS jump table must be fixed.
4. **Storage engineering.** The initial logical disk format, DPB/DPH exposure, disk-format description, logical-to-physical translation ownership, directory/allocation working state, and invalidation rules must be defined.
5. **System-state layout.** Each persistent item requires an owner, representation, lifetime, initialization rule, and transition behavior.
6. **Cold start, warm start, and command restoration.** Preserved, discarded, reconstructed, and reloaded state must be enumerated.
7. **Program execution.** Loader limits and failures, page-zero contents, initial registers, command tail, default FCBs, DMA state, termination paths, and restoration must be specified from the compatibility contract.
8. **System Services.** Internal organization, call conventions, private errors, and translation to each CP/M-visible BDOS result must be specified.
9. **Command Environment.** Resident commands, parsing, lookup, error behavior, residency, restoration, and byte budget must be specified.

These are Phase 2 tasks, not deficiencies requiring another architecture phase.

## Documentation synchronization required

`15 Open Questions.txt` reflects an earlier state of the compatibility program. It says that the precise compatibility boundary remains to be established, while the original BetterCP/M material now contains investigations through 074 and release-assembly work. Before compatibility-dependent engineering specifications are approved:

- replace broad compatibility questions with references to the released Compatibility Policy, Compatibility Ledger, Conformance Strategy, and suite;
- retain only propositions that are still explicitly policy-pending or unresolved;
- update architecture sections that promise later compatibility investigation when that investigation has now concluded; and
- make the exact compatibility-suite release or commit an engineering input.

This synchronization is not a prerequisite for the diagnostic boot milestone because that milestone exposes no CP/M application interface.

## Questions safely deferred

The following do not block the compatible baseline and should remain deferred:

- bank-switched memory;
- additional hardware targets;
- SD and CompactFlash support;
- generalized extension discovery;
- extended System Services;
- enhanced or alternative command environments;
- public debugging facilities;
- a generalized configuration-management service; and
- speculative driver, module, or extension frameworks.

## Engineering sequence

The recommended Phase 2 sequence is:

1. Baseline Bring-Up Specification
2. Source and Build Conventions
3. Resident Memory and System-Image Specification
4. Hardware-Abstraction and Compatibility BIOS Specification
5. Storage and Initial Disk-Format Specification
6. System State and Initialization Specification
7. System-Service Specification
8. Program Execution Specification
9. Command Environment Specification
10. Integrated Boot, Warm Start, and Restoration Specification

Specifications may overlap where dependencies require it, but code should not silently decide an unresolved external interface or persistent representation.

## Readiness decision

**Approved to begin Phase 2 and the baseline diagnostic bring-up.**

Approval does not extend to the final resident layout, storage representation, BDOS organization, BIOS exposure, or Command Environment implementation until their engineering specifications resolve the dependencies listed above.
