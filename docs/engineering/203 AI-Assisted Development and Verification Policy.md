# Engineering Specification 203: AI-Assisted Development and Verification Policy

## Status

Proposed for adoption as a continuing BetterCP/M engineering policy and as a governing requirement for the remaining BetterCP/M 1.0 implementation and qualification work.

## Purpose

BetterCP/M makes extensive use of artificial intelligence for implementation, analysis, testing, documentation, and engineering work. Essentially all BetterCP/M implementation code has been produced with AI assistance, while the project remains human-directed at the level of goals, scope, architecture, compatibility policy, interfaces, requirements, and acceptance decisions.

This development model creates assurance risks that are not adequately addressed by ordinary build-and-test practice alone. In particular:

- the human maintainer is not presently capable of independently performing an expert line-by-line audit of the complete Z80 implementation;
- AI may reproduce the same mistaken assumption in both implementation and test code;
- repeated AI-driven debugging can converge on passing tests without identifying the underlying defect;
- AI-generated documentation and comments may accurately describe an intended design while failing to prove that the implementation conforms to it;
- an AI system reviewing AI-generated code is useful evidence but is not independent expert human review.

This specification defines the engineering controls BetterCP/M uses to reduce those risks.

It does not reopen the frozen BetterCP/M 1.0 architecture, change compatibility requirements, or require replacement of existing AI-generated implementation code.

The objective is to strengthen the evidence supporting the implementation that already exists and to govern future development.

## 1. Governing Principle

BetterCP/M shall not rely primarily on trust in generated source code.

Assurance should instead come from multiple independent or partially independent forms of evidence:

1. previously stated requirements and architecture;
2. historical CP/M behavior where applicable;
3. independently derived compatibility tests;
4. machine-checkable invariants;
5. reproducible builds and exact-artifact qualification;
6. regression and differential testing;
7. deliberate fault injection and mutation testing;
8. emulator instrumentation;
9. adversarial implementation review;
10. human technical understanding and review where available.

No single form of evidence is treated as sufficient by itself.

## 2. Specification Authority

The implementation must answer to the specification.

A BetterCP/M implementation result does not become correct merely because:

- it assembles;
- it boots;
- a test written for it passes;
- an AI system explains why it should work;
- existing software appears to tolerate it.

Where a normative architecture specification, implementation contract, compatibility requirement, or accepted historical behavior exists, that requirement remains authoritative until explicitly revised for independent reasons.

Implementation behavior must not silently redefine the requirement.

### 2.1 Test changes

A failing test must not be weakened, removed, or rewritten merely because BetterCP/M fails it.

A compatibility or acceptance test may be changed when independent evidence establishes that the test itself is incorrect, incomplete, or inconsistent with the governing requirement.

Suitable evidence includes:

- observed behavior of reference CP/M;
- authoritative Digital Research documentation;
- independently established historical behavior;
- a contradiction within the accepted BetterCP/M specification;
- a demonstrated defect in the test implementation.

The reason for such a change must be recorded.

## 3. Reference CP/M as an External Oracle

Where BetterCP/M claims CP/M-compatible behavior, reference CP/M should be used as an external behavioral oracle whenever practical.

The preferred test model is:

```text
same stimulus
     |
     +----> reference CP/M ----> observed result
     |
     +----> BetterCP/M --------> observed result
                                  |
                              comparison
```

Comparison may include, as applicable:

- return registers;
- preserved registers;
- FCB contents;
- DMA contents;
- directory entries;
- allocation state;
- disk-image changes;
- drive and user state;
- page-zero state;
- console behavior;
- error behavior;
- cold-boot and warm-boot effects.

Reference-system observation is especially valuable when a behavior is obscure, underdocumented, or likely to be implemented from an AI-generated interpretation of documentation.

BetterCP/M-specific extensions require their own explicit specifications because no historical CP/M oracle exists for them.

## 4. Verification Independence

Tests should derive their expected behavior from a source independent of the implementation whenever practical.

The following is weak evidence:

```text
AI interpretation
      |
      +----> implementation
      |
      +----> expected test result
```

because one mistaken interpretation can cause both sides to agree.

Stronger evidence separates the implementation from its oracle:

```text
historical behavior / accepted specification
                  |
                  +----> test expectation

AI implementation ---------------------> result
                                          |
                                      comparison
```

The separately maintained CP/M Compatibility Suite is therefore treated as an external compatibility authority for BetterCP/M rather than as a test collection that may be adjusted to accommodate BetterCP/M behavior.

## 5. Mutation and Fault-Injection Testing

BetterCP/M qualification shall include deliberate testing of the verification system itself.

A passing correct build demonstrates only that the test accepts one apparently correct implementation. It does not demonstrate that the test would detect an incorrect implementation.

The project shall therefore maintain a bounded mutation/fault-injection corpus containing deliberately defective variants of important behavior.

Representative mutations should include defects such as:

- incorrect BDOS return values;
- failure to preserve required registers;
- incorrect FCB updates;
- extent-boundary errors;
- allocation-state errors;
- incorrect sequential or random-record calculations;
- disabled read-only enforcement;
- incorrect drive or user transitions;
- failure to clear state on cold boot;
- failure to preserve required state on warm boot;
- incorrect CPX or RSX reconstruction;
- relocation errors;
- writes into protected memory;
- stack-boundary violations;
- violation of the 53 KiB TPA requirement;
- incorrect selector dispatch;
- failure to reject malformed persistent or module state.

Mutations are qualification artifacts only. They are never production changes.

### 5.1 Mutation result

Each mutation shall have an expected detecting test or acceptance gate.

A surviving mutation—one that remains undetected—must be:

1. explained as behavior that is genuinely outside the asserted test boundary; or
2. used to strengthen the relevant qualification mechanism.

Raw test count is not considered a measure of test quality.

Where practical, release evidence should report both:

- the mutation corpus exercised; and
- the proportion and identity of injected defects detected.

## 6. Bug-Fix Discipline

Substantive defects must not be resolved through uncontrolled prompt-and-test iteration.

A significant bug fix should establish:

1. the observed symptom;
2. the applicable specification, compatibility rule, or invariant;
3. the root cause;
4. the affected implementation path;
5. the correction;
6. a regression test or other permanent detection mechanism.

Where practical, the regression must first be demonstrated against the defective implementation and then against the corrected implementation.

The preferred sequence is:

```text
observe failure
      |
reproduce failure
      |
identify violated requirement
      |
determine root cause
      |
add or identify detecting test
      |
apply bounded correction
      |
run focused regression
      |
run affected broader qualification
```

A test becoming green is not by itself a root-cause analysis.

If the cause cannot be adequately explained, the change should remain under investigation rather than being accepted merely because an AI-generated modification suppresses the observed failure.

## 7. Permanent Regression Knowledge

Every confirmed implementation defect should strengthen the permanent verification system where practical.

A defect that has occurred once is evidence of a possible failure mode.

BetterCP/M should therefore prefer adding a regression test, invariant check, fixture, or qualification probe that prevents the same class of defect from silently returning.

The project should accumulate verification knowledge rather than repeatedly depend on rediscovery.

## 8. Machine-Checkable Invariants

Any important property that can be checked mechanically should be checked mechanically rather than left solely as a prose assertion.

Existing and future checks may include:

- resident-region non-overlap;
- valid ROM/RAM ownership;
- prohibition of writes to immutable memory;
- stack capacity and guard margins;
- workspace lifetime assumptions;
- 53 KiB default TPA preservation;
- component-size bounds;
- selector-range ownership;
- module-carrier structure;
- checksum and version validation;
- fixed persistent-layout constraints;
- native/cross-build equivalence where required;
- release-manifest consistency;
- exact artifact identity.

A machine check does not replace semantic validation, but it removes the checked property from dependence on informal source inspection.

## 9. Emulator Instrumentation

The required emulator platforms should be used as active verification environments rather than only as execution hosts.

Where practical, qualification builds may detect:

- CPU writes to protected memory;
- DMA writes to protected memory;
- stack overflow or guard crossing;
- illegal memory-region ownership changes;
- unexpected register changes;
- invalid device or BIOS access;
- corruption of protected structures;
- prohibited runtime reconfiguration.

Instrumentation that exists solely for qualification must be clearly distinguished from behavior required by the normal BetterCP/M runtime environment.

Qualification instrumentation itself must be reproducible and versioned as part of the release environment.

## 10. Adversarial AI Review

AI may be used to review AI-generated code, but review should be structured to reduce confirmation bias.

For significant or high-risk changes, an independent review context should, where practical:

- receive the governing specification;
- receive the relevant implementation;
- not receive the implementation author's reasoning unless required;
- be instructed to identify defects rather than improve style;
- search specifically for violated assumptions, boundary errors, state-lifecycle problems, register errors, address errors, and untested cases.

Different model families may be used where practical.

Such review is classified as **AI-assisted or automated review**, not independent human review.

A model's statement that code "looks correct" is not qualification evidence unless accompanied by concrete analysis that can itself be checked.

## 11. Evidence Categories

Engineering records must distinguish among materially different kinds of assurance.

The following terms are not interchangeable:

### AI-assisted source review
An AI system analyzed implementation source and reported findings.

### Automated verification
A deterministic or reproducible program checked a stated property.

### Reference-system comparison
BetterCP/M behavior was compared with an independent historical implementation.

### Behavioral qualification
An exact BetterCP/M artifact passed a defined acceptance test.

### Mutation validation
A deliberately defective implementation was correctly rejected by the verification system.

### Independent human review
A knowledgeable human independently examined the relevant implementation or behavior.

Documentation must not describe AI-assisted analysis as independent human review or imply that behavioral qualification constitutes complete source audit.

## 12. Reproducibility and Exact Artifacts

Qualification evidence attaches to exact artifacts and exact environments.

Where a BetterCP/M test depends on modified external tooling or emulation, the release evidence must record enough information to reconstruct that environment.

This includes the BetterCP/M-qualified cpmsim environment required by the 1.0 z80pack target.

A successful run on an undocumented local emulator or development environment is insufficient release evidence.

Existing 1.0 requirements for:

- source revision;
- artifact hashes;
- build provenance;
- exact emulator configuration;
- package identity;
- native/cross-build evidence;

remain applicable.

## 13. Historical Release Baselines

Once a BetterCP/M release has been qualified, its source, binaries, disk images, manifests, configuration, and qualification evidence become retained behavioral evidence.

Future releases should distinguish among:

- behavior required for CP/M compatibility;
- established BetterCP/M behavior that remains part of its compatibility contract;
- intentionally changed BetterCP/M behavior.

A later AI-generated implementation must not silently redefine established BetterCP/M behavior merely because a new implementation or test produces a different result.

## 14. Human Maintainer Understanding

Automated assurance does not remove the value of human understanding.

The project shall continue to improve the maintainer's ability to reason about BetterCP/M independently of AI-generated implementation explanations.

This is approached top-down.

The intended progression is:

1. overall CP/M and BetterCP/M system architecture;
2. major subsystem responsibilities and boundaries;
3. lifecycle and control flow between subsystems;
4. internal subsystem architecture;
5. important data structures and invariants;
6. individual execution paths;
7. routines and calling conventions;
8. Z80 instructions, registers, flags, and stack effects.

The objective is not to require the maintainer to reimplement BetterCP/M unaided.

The objective is to reduce the implementation's black-box character and improve the maintainer's ability to:

- challenge AI explanations;
- recognize architectural inconsistencies;
- follow important execution paths;
- understand bug root causes;
- evaluate implementation tradeoffs;
- inspect critical routines.

Independent expert review remains desirable when available but is not assumed as a prerequisite for maintaining the project.

## 15. BetterCP/M 1.0 Application

This policy takes effect without restarting or rewriting the BetterCP/M 1.0 implementation.

Existing implementation code is not rejected merely because it predates this specification.

For 1.0:

- remaining substantive bug fixes must follow the root-cause and regression policy;
- compatibility-test changes must have independent justification;
- existing machine-checkable gates remain mandatory;
- exact release-environment reproducibility remains mandatory;
- final qualification must use the frozen release-candidate artifacts;
- a bounded initial mutation/fault-injection corpus shall exercise representative critical failure classes;
- differential/reference testing should be used for retained CP/M-compatible behavior where practical;
- qualification evidence must distinguish automated, AI-assisted, reference-system, mutation, and human evidence accurately.

The initial 1.0 mutation corpus need not attempt exhaustive mutation testing of every instruction or subsystem. It must be sufficient to demonstrate that major qualification mechanisms reject representative incorrect implementations.

Broader mutation coverage and additional differential testing remain continuing engineering work after 1.0.

## 16. Acceptance for New Development

After adoption of this specification, a significant new BetterCP/M feature or behavioral change should not be considered complete until:

1. its intended behavior is stated independently of the implementation;
2. applicable compatibility or architectural constraints are identified;
3. implementation-specific invariants are machine-checked where practical;
4. focused tests exist;
5. relevant reference behavior is compared where available;
6. discovered defects have regression coverage;
7. high-risk implementation receives adversarial review where practical;
8. broader qualification remains passing;
9. evidence is recorded using the categories defined by this specification.

These requirements apply to AI-generated and manually written future code alike.

## 17. Relationship to AI.md

[`AI.md`](../../AI.md) provides the public explanation of BetterCP/M's use of artificial intelligence.

This engineering specification is different in purpose.

`AI.md` describes the development model and its limitations to users and contributors.

This document defines the engineering controls by which the project responds to those limitations.

Where the two overlap, this specification is the normative engineering authority.

## Result

BetterCP/M does not attempt to eliminate the fact that its implementation was produced with extensive AI assistance.

Instead, the project treats that development model as an explicit engineering condition and builds its assurance process accordingly.

The governing principle is:

> **Do not ask whether the generated code looks trustworthy. Require independent evidence for the properties on which BetterCP/M depends.**