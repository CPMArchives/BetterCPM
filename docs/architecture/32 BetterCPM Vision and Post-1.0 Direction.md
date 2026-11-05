# BetterCP/M Vision and Post-1.0 Direction

**Status:** Working project direction, recorded after the BetterCP/M 1.0 implementation milestone  
**Role:** Guides post-1.0 roadmap discussion and feature evaluation; does not itself authorize a feature or replace subsystem specifications.

## 1. Purpose

BetterCP/M has established a CP/M 2.2-compatible baseline and a coherent 1.0 product. The next stage needs a direction for evolution, so that the accumulated post-1.0 backlog can be assessed against a shared purpose rather than treated as a roadmap by default.

This document records that broad direction. It complements [Architectural Principles](01%20Architectural%20Principles.txt), which describe system design priorities, and [Developer Platform Direction](26%20Developer%20Platform%20Direction.txt), which addresses developer-facing system interfaces. It does not replace their technical requirements.

## 2. Working vision

**BetterCP/M should make CP/M more useful and attractive to operate, while remaining a strong platform for CP/M software and providing developers with an attractive environment and a portable operating system for modern Z80-family homebrew systems.**

This direction has two related audiences:

- **Users:** People who want to run CP/M software and benefit from a more usable, capable, and coherent CP/M environment.
- **Developers:** People who create software for CP/M or BetterCP/M, extend the system, or adapt BetterCP/M to new Z80-family hardware.

The audiences overlap in practice, but each gives a distinct test for future work. A feature may improve daily use, make software development more effective, make hardware adaptation more practical, or serve more than one of these purposes.

## 3. Compatibility and evolution

CP/M 2.2 remains BetterCP/M's compatibility foundation. The documented Digital Research CP/M 2.2 application contract belongs in the core system. Compatibility decisions about less explicit behavior should consider whether a convention became meaningfully established across the CP/M software community; an isolated implementation quirk or clearly unsound programming practice does not automatically become a project obligation.

BetterCP/M may evolve beyond the DRI contract while preserving that contract for existing software. New BetterCP/M-specific services are candidates for optional extensions, including RSXs, when that keeps the core compact and lets users choose a balance between resident services and application memory. The mechanism and placement of each proposed service remain subject to its own design review.

Utilities and applications should continue to target ordinary CP/M 2.2 when that is useful to their purpose. The project should not assume that every future capability must be available on every unmodified CP/M 2.2 system; compatibility scope should be stated for each component.

## 4. Platform and architectural boundaries

BetterCP/M is a native operating system for the Z80 family. The 8080 is not a target. Portability to modern Z80-family homebrew systems is part of the direction, and platform releases should continue to derive from a shared codebase, with hardware differences handled at the appropriate platform boundary.

Banked memory may be explored as an architectural option for increasing usable memory or supporting optional system facilities while retaining the CP/M application contract. It is independent of whether a future product resembles CP/M 3. A banked configuration, a CP/M 3-like member of a possible BetterCP/M family, and the engineering needed to support either remain separate decisions; this vision commits to none of them.

The project is not open-endedly expanding into a general operating-system compatibility layer or a collection of unrelated operating systems. In particular, a CP/M compatibility subsystem inside a DOS-like host is outside the present direction. Any proposed expansion must remain connected to BetterCP/M's purpose and within a support commitment the project can sustain.

## 5. Limiting principles

Use these principles to contain growth:

1. **Stay within the Z80 family.** A processor port outside that family needs a separate reconsideration of the project boundary, not an assumption that every historically related processor belongs.
2. **Preserve the CP/M 2.2 core contract.** Extensions may add capability without making the documented baseline depend on optional facilities.
3. **Keep the system comprehensible and proportionate.** Prefer improvements that can be explained, maintained, and supported within the project's scale.
4. **Treat ports as continuing commitments.** A port includes future maintenance and qualification, not only initial boot success. Community interest and actual hardware use can inform priority, but do not by themselves create an obligation to support every platform.
5. **Let the community shape community-facing development.** New CP/M-era development can grow when users and developers identify shared needs and adopt the platform. The maintainer should not invent a community agenda in the absence of that participation.

These principles bound the field of consideration; they do not predetermine every technical choice.

## 6. Using the vision to guide post-1.0 work

For a significant proposal, ask:

- What should this let users do more easily or effectively?
- What should this make possible for CP/M or BetterCP/M software developers?
- Does it improve adaptation or portability to supported Z80-family hardware?
- What is the effect on the CP/M 2.2 contract, application memory, system size, and support burden?
- Does it belong in the core, an optional extension, a platform implementation, a separate tool, or nowhere in BetterCP/M?
- Is the benefit strong enough to justify its implementation and continuing maintenance?

A useful starting question is: **What should BetterCP/M do after 1.0 that ordinary CP/M 2.2 does not do as well?** It is a way to test individual proposals, not a complete definition of the project's purpose.

The post-1.0 backlog is a candidate inventory, not an implied commitment or priority order. During roadmap review, assess candidates against this direction, resolve practical questions such as demand and support capacity, and defer features whose value or cost is not yet clear. Not every question needs an answer in advance; this vision is intended to guide decisions when they arise.

## 7. Review status

This is a working project-level direction, not a frozen product specification. It records the broad purpose and boundaries agreed so far. Future discussions may refine it as implementation experience, hardware activity, and community participation provide evidence. Specific feature, ABI, memory, banking, platform, and release decisions belong in their respective architecture or engineering documents.
