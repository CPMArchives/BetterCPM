# BetterCP/M

BetterCP/M is an effort to design a compact, maintainable successor to CP/M 2.2 while preserving a rigorously defined CP/M-compatible environment.

The project is currently in its architectural definition phase. No implementation is included yet.

## Design direction

The current work emphasizes:

- CP/M 2.2 compatibility grounded in an explicit specification and conformance suite
- a memory footprint in the same general class as Digital Research CP/M
- a small command processor and an improved command environment
- a unified model for drives, user areas, named directories, and command search paths
- table-driven, inspectable configuration
- separation of portable system code from hardware-dependent support
- an architecture suitable for ROM-resident code
- explicit interfaces and state instead of magic addresses and undocumented dependencies

## Documents

The initial architecture material is in [`docs/architecture`](docs/architecture). It covers architectural principles and boundaries, memory and boot design, the command environment, system services, hardware abstraction, program execution, storage, system state, compatibility, constraints, extensions, and open questions.

These are working engineering documents. They record the present design thinking and may change as project goals and requirements are refined.

## Related work

BetterCP/M's compatibility foundation is developed separately in the [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite).
