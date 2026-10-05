# Artificial Intelligence in BetterCP/M

## Purpose

BetterCP/M makes extensive use of artificial intelligence in its development. This document explains what that means, what it does not mean, how AI is used in the project, what responsibilities remain with the human maintainer, and how BetterCP/M attempts to address the risks inherent in AI-generated software.

The short version is simple:

**AI has produced essentially all of BetterCP/M's implementation code, including its Z80 assembly-language source.**

This is not something the project attempts to hide or minimize. Anyone evaluating, using, studying, contributing to, or redistributing BetterCP/M should know how the software was produced.

At the same time, describing BetterCP/M merely as "written by AI" leaves out much of the development process. AI is principally the implementation mechanism. The project itself—what BetterCP/M is supposed to be, how it is structured, what behavior it must provide, and what evidence is required before that behavior is accepted—is directed by the human maintainer.

This document describes that distinction and the safeguards built around it.

## How BetterCP/M Began

BetterCP/M began as an attempt by its maintainer to understand CP/M.

I have used computers since the CP/M era, but I did not begin this project as a Z80 assembly-language programmer or as an experienced operating-system developer. My original interest was in understanding CP/M itself: how its major layers fit together, what the CCP, BDOS, and BIOS actually do, how programs interact with the operating system, and how the apparently simple CP/M environment is constructed internally.

BetterCP/M grew out of that process. What began as an effort to understand CP/M by examining and reconstructing it gradually became an attempt to build a modern, maintainable CP/M-compatible system. AI therefore became not only a teaching and research tool but also the principal implementation tool for the project.

## Is BetterCP/M Vibe-Coded?

No. BetterCP/M is not [vibe-coded](https://en.wikipedia.org/wiki/Vibe_coding) in the sense described by that term.

AI-generated code is not accepted simply because it compiles, boots, produces plausible output, or appears to solve the immediate problem. BetterCP/M is developed against previously stated architecture, behavioral requirements, compatibility requirements, subsystem interfaces, memory constraints, and acceptance criteria.

The normal direction of development is intended to be:

1. decide what the system is supposed to do;
2. specify the relevant behavior and constraints;
3. implement that behavior;
4. test the resulting implementation against those requirements;
5. investigate discrepancies rather than allowing the implementation itself to redefine the requirement.

AI plays a major role in steps 3 through 5. It does not have final authority over step 1.

This distinction does not make AI-generated code inherently correct, nor does it eliminate the risks associated with AI-assisted development. Those risks are discussed below.

## What AI Does

Artificial intelligence is used throughout BetterCP/M development, including for:

- producing Z80 assembly-language implementation code;
- modifying and refactoring existing implementation code;
- diagnosing failures and tracing execution paths;
- implementing tests and test infrastructure;
- analyzing memory layouts and binary structures;
- examining interactions between the CCP, BDOS, BIOS, CPX, RSX, utilities, and platform-specific code;
- comparing implementation behavior with specifications;
- assisting with compatibility analysis;
- generating and maintaining build and qualification tools;
- reviewing source code for possible defects;
- drafting and revising technical documentation;
- organizing engineering records and implementation plans.

Consequently, the presence of polished comments, detailed documentation, extensive test code, or carefully structured assembly should not be interpreted as evidence that those materials were manually written without AI assistance.

AI assistance extends well beyond occasional code completion.

## What the Human Maintainer Does

The human maintainer retains responsibility for the project.

That includes deciding:

- the purpose and overall direction of BetterCP/M;
- the CP/M 2.2 compatibility baseline;
- which historical behaviors should be preserved;
- which BetterCP/M extensions should exist;
- the scope of each release;
- the overall system architecture;
- subsystem boundaries and responsibilities;
- public interfaces and compatibility promises;
- memory and TPA requirements;
- which proposed features are accepted, rejected, or deferred;
- what constitutes acceptable behavior;
- what evidence is required before a feature or release is considered qualified;
- whether an AI-proposed implementation, design, explanation, or documentation change is accepted into the project.

AI frequently proposes solutions, architectures, tests, wording, or alternatives. Those proposals are not authoritative merely because an AI produced them.

Project decisions remain human decisions.

For this reason, project specifications and documentation are better described as **human-directed** rather than necessarily entirely human-written. AI is also used to help draft and refine those materials.

## An Important Limitation

There is one limitation that deserves particularly explicit disclosure.

The maintainer of BetterCP/M is not an expert Z80 assembly-language programmer and is not presently capable of independently performing an expert line-by-line audit of the complete BetterCP/M implementation.

That creates a real assurance problem.

In a traditionally developed assembly-language operating system, an experienced maintainer can often inspect a routine and independently determine whether its register usage, stack discipline, address calculations, control flow, or calling conventions are sound.

BetterCP/M cannot presently rely on that level of human source-code inspection as its primary assurance mechanism.

The project therefore attempts to move as much assurance as practical away from:

> "The maintainer read the code and believes it is correct."

and toward:

> "The implementation has been tested against independently stated behavior, machine-checkable invariants, reference-system behavior, and reproducible qualification evidence."

That approach reduces an important risk of AI-generated software. It does not eliminate it.

BetterCP/M does **not** claim that automated verification is equivalent to an independent expert human audit.

## Specification Before Implementation

A central BetterCP/M development principle is that the implementation should answer to the specification rather than the specification being inferred from whatever the implementation happens to do.

The project maintains architecture specifications, implementation contracts, compatibility requirements, memory constraints, subsystem interfaces, and release acceptance criteria separately from the source code itself.

For BetterCP/M 1.0 in particular, the architecture was frozen before the final implementation and qualification program.

The authoritative 1.0 material includes the:

- [BetterCP/M 1.0 Roadmap](docs/releases/1.0-ROADMAP.md);
- [BetterCP/M 1.0 Implementation Contracts](docs/releases/1.0-IMPLEMENTATION-CONTRACTS.md);
- architecture and engineering specifications under [`docs/`](docs/);
- compatibility requirements and evidence maintained by the project.

A source-code comment stating that a routine performs some function is not, by itself, evidence that the routine actually does so.

Where practical, the claimed behavior should be demonstrated independently.

## CP/M Compatibility as an External Constraint

Much of BetterCP/M has an advantage that ordinary new software does not: it is intended to reproduce behavior that already exists.

For CP/M-compatible behavior, Digital Research CP/M provides an external historical reference.

BetterCP/M is tested using the separately maintained [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite), along with BetterCP/M-specific tests.

The intended relationship is one-way:

**BetterCP/M must conform to the compatibility requirement. The compatibility requirement must not be changed merely because BetterCP/M fails it.**

If a compatibility test is found to be wrong, changing the test should require evidence independent of BetterCP/M—for example, observed behavior under reference CP/M, authoritative documentation, or other historical evidence.

This separation is important because AI can otherwise make the same conceptual mistake in both an implementation and the test that supposedly validates it.

A test that agrees with incorrect code does not establish compatibility.

## Verification and Qualification

BetterCP/M already uses several forms of verification that do not depend solely upon source inspection.

These include, as applicable:

- the CP/M 2.2 Compatibility Suite;
- subsystem regression tests;
- platform-specific tests;
- clean and reproducible build procedures;
- native CP/M and modern cross-development build paths;
- native/cross-build comparison where practical;
- explicit memory-layout checks;
- minimum TPA requirements;
- ROM/RAM ownership checks;
- protected ROM execute-in-place qualification;
- stack and workspace checks;
- CPX and RSX lifecycle and reconstruction tests;
- disk-format and installation tests;
- exact release-candidate artifact hashes;
- manifests and provenance information;
- qualification against more than one required platform.

For BetterCP/M 1.0, qualification is intended to attach to exact frozen release-candidate artifacts rather than merely to a source tree from which something approximately equivalent could later be rebuilt.

Changing the artifact invalidates the qualification attached to the previous artifact.

## Verifying the Verification

Passing tests is not sufficient evidence if the tests themselves are weak.

This problem is particularly important when AI has assisted in producing both the implementation and some of its test infrastructure.

BetterCP/M therefore intends to expand its verification process to include **fault injection and mutation testing**.

The basic idea is to deliberately introduce known defects into disposable builds and ask whether the qualification system detects them.

Examples may include deliberately:

- returning an incorrect BDOS result;
- failing to preserve a required register;
- corrupting an FCB field;
- mishandling an extent boundary;
- disabling read-only enforcement;
- altering drive or user state incorrectly;
- breaking cold-boot or warm-boot state handling;
- corrupting an RSX or CPX relocation;
- writing into a protected memory region;
- violating a required memory-size or TPA constraint.

These defective builds would never become production code. Their purpose is to test the measuring instrument.

A useful qualification system should not merely demonstrate that the correct build passes. It should also demonstrate that representative incorrect builds fail.

Mutation detection therefore provides information about the strength of the test system that a raw test count cannot.

## Differential Testing

Where practical, BetterCP/M should increasingly use differential testing against reference CP/M.

Instead of encoding only an expected result created specifically for BetterCP/M, the same test can be executed on both systems and their observable behavior compared.

Depending on the operation, that may include:

- returned registers;
- FCB contents;
- DMA contents;
- directory entries;
- disk contents;
- allocation state;
- drive and user state;
- page-zero state;
- warm-boot effects;
- error behavior.

For compatible facilities, reference CP/M can therefore serve as an oracle independent of the BetterCP/M implementation.

BetterCP/M-specific extensions obviously cannot use CP/M as their behavioral reference. Those facilities instead require explicit BetterCP/M specifications and regression tests.

## Machine-Checkable Invariants

Whenever an important property can be checked automatically, BetterCP/M should prefer a machine check to an assumption recorded only in prose.

Examples include verifying that:

- resident memory regions do not overlap;
- ROM-owned areas are never modified;
- writable objects remain within their assigned RAM regions;
- stacks retain required reserve;
- the default configuration retains the required TPA;
- public function-number ranges do not collide;
- generated binaries fit their assigned address ranges;
- module formats satisfy their structural requirements;
- qualified build products correspond to the recorded inputs;
- release packages contain the exact artifacts that were qualified.

This does not prove general correctness, but it removes entire categories of errors from dependence upon human inspection.

## Emulator Instrumentation

Emulated targets also provide opportunities for verification that would be difficult on original hardware.

Qualification environments may be instrumented to detect conditions such as:

- writes to ROM;
- writes outside an object's permitted region;
- stack exhaustion or guard corruption;
- unexpected BIOS activity;
- invalid memory access;
- changes to protected state;
- incorrect entry/exit register behavior.

An instrumented emulator cannot establish that every algorithm is semantically correct, but it can turn many otherwise silent implementation errors into deterministic test failures.

## AI Reviewing AI

AI may also be used to review AI-generated code.

This is useful, but BetterCP/M does not treat it as equivalent to independent human review.

Where practical, critical implementation code can be subjected to adversarial review in which another model or a separate context is given the specification and implementation and instructed to search specifically for violations, incorrect assumptions, boundary conditions, or latent defects.

The reviewer should be encouraged to challenge the implementation rather than merely explain or improve it.

Using different models or isolated review contexts can reduce some forms of shared reasoning or anchoring, but all such review remains automated review.

BetterCP/M documentation should distinguish between:

- AI-assisted source review;
- automated verification;
- reference-system comparison;
- behavioral qualification;
- independent human review.

Those are different kinds of evidence.

The project should not describe one as another.

## Bug-Fixing Policy

AI development becomes particularly dangerous when debugging degenerates into repeated trial-and-error prompting:

> change something, rerun the test, change something else, repeat until the test becomes green.

BetterCP/M should avoid accepting substantive bug fixes without an identified root cause.

A significant defect should ideally leave behind a record containing:

1. the observed symptom;
2. the violated requirement or invariant;
3. the identified root cause;
4. the affected implementation;
5. the correction;
6. a regression test demonstrating the defect.

Where practical, the regression test should first be demonstrated to fail against the defective implementation and then pass after the correction.

Every discovered bug is therefore an opportunity to strengthen the project's permanent verification knowledge.

## Human Review

Independent review by an experienced CP/M or Z80 developer would be valuable, particularly in critical areas such as:

- BDOS entry and return conventions;
- directory and allocation logic;
- disk-write paths;
- BIOS interfaces;
- boot and warm-boot reconstruction;
- CPX and RSX relocation;
- stack and memory ownership.

BetterCP/M does not, however, assume that such review will be available.

The project's assurance strategy must remain useful even if the maintainer is the only continuing human developer.

If independent human review does occur, the project should identify it explicitly rather than implying that automated or AI-assisted review constitutes the same thing.

## Maintainer Knowledge

The use of AI does not mean that the human maintainer should remain permanently unable to understand the implementation.

A practical goal is increasing implementation literacy rather than requiring the maintainer to become capable of writing the entire operating system unaided.

That includes progressively understanding:

- Z80 registers and flags;
- stack behavior;
- calls and returns;
- memory addressing;
- calling conventions;
- important system data structures;
- critical control paths;
- the relationship between specifications and implementation.

The goal is to improve the maintainer's ability to challenge explanations, inspect critical routines, and reason about failures while continuing to use AI as the principal implementation tool.

## Documentation Generated With AI

AI is also used to assist in producing BetterCP/M documentation.

Documentation should therefore not be treated as independent evidence merely because it is detailed or authoritative in tone.

Normative documents become authoritative because the human maintainer has accepted their requirements as project decisions, not because AI generated convincing prose.

Where documentation describes implementation behavior, that description should be reconciled with the relevant source, specification, tests, or qualification evidence.

## Provenance and Licensing

AI use also raises questions about source provenance.

BetterCP/M should maintain a clear distinction between:

- BetterCP/M-generated source;
- original project material;
- externally supplied source;
- historical reference material;
- third-party utilities and binaries;
- Digital Research or other copyrighted software used for development, compatibility testing, or redistribution where permitted.

Third-party material requires its own provenance and redistribution basis regardless of whether AI participated in project development.

AI generation does not make third-party licensing obligations disappear.

The BetterCP/M release process therefore includes provenance, version, hash, and redistribution checks for distributed third-party artifacts.

## What BetterCP/M Does Not Claim

The project does not claim that:

- AI-generated code is inherently reliable;
- passing the current tests proves the absence of bugs;
- AI review is equivalent to expert human review;
- extensive documentation proves implementation correctness;
- automated qualification proves every possible CP/M program will behave identically;
- the maintainer can presently perform an expert independent audit of every line of Z80 assembly;
- the safeguards described here eliminate all risks associated with AI-generated software.

The objective is narrower and more defensible:

**identify the weaknesses introduced by the development method and construct independent evidence wherever practical rather than simply trusting the generated implementation.**

## Ongoing Development of the Assurance Model

The verification methodology itself will continue to evolve.

Areas of particular interest include:

- broader differential testing against reference CP/M;
- systematic mutation and fault-injection testing;
- measuring how effectively the qualification suite detects injected defects;
- stronger emulator instrumentation;
- more explicit machine-checkable invariants;
- adversarial AI review separated from implementation contexts;
- preserving old releases as behavioral baselines;
- improving the maintainer's Z80 implementation literacy;
- independent human review where available.

Some of these safeguards are already present in BetterCP/M. Others are planned improvements.

This document should distinguish clearly between the two rather than representing proposed safeguards as completed work.

## Final Note

BetterCP/M exists in substantial part because modern AI tools make it possible for a single maintainer to undertake an operating-system project whose implementation would otherwise require skills and time that the maintainer does not possess.

That is both the opportunity and the risk.

The project does not attempt to conceal the role of AI, nor does it ask users to trust AI simply because its output looks plausible.

Instead, BetterCP/M attempts to place the generated implementation inside an increasingly strict framework of human-directed requirements, historical reference behavior, automated qualification, reproducible evidence, adversarial testing, and explicit disclosure.

Users are free to decide that AI-generated software is not something they wish to use.

Those who do evaluate BetterCP/M should at least be able to see clearly how it was built, what has and has not been independently established about it, and what the project is doing to reduce the risks of its development model.