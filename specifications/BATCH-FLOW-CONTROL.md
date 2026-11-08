# BetterCP/M Batch and Flow-Control Facility

Status: full SUBMIT/XSUB compatibility confirmed for 1.0; extended flow features remain proposed.

## Confirmed release boundary

The core CCP's built-in command inventory is GET, JUMP, PEEK/P, POKE, GO and SAVE.
RCP.CPX supplies the other standard CP/M resident commands. Full SUBMIT/XSUB behavioral
compatibility ships in 1.0. Flow control and further batch extensions are loadable
CPX features; the extended language below is not automatically a mandatory 1.0
inventory. Qualify original SUBMIT/XSUB syntax and workflows independently of the
chosen internal implementation, including parameter substitution, command order,
program input, cancellation and return across warm boot.

## Tentative 1.3 flow-control investigation

**Planning status:** documentation-only proposal, tentatively targeted for
BetterCP/M 1.3. Neither scope nor syntax is approved; the target is not a release
commitment. This agenda develops the existing proposal below rather than
introducing a second scripting facility. The module names, language forms,
common-stream interfaces and broad PDS inventory below remain proposal material,
not implemented behavior or new allocations in the frozen architecture.

### Boundaries to preserve

- **SUBMIT/XSUB:** shipped CP/M-compatible sequential command submission,
  parameter substitution and submitted program input. The
  [qualified implementation](../docs/engineering/129%20Stock-Compatible%20SUBMIT%20and%20XSUB.md)
  uses `SUBMIT.COM`, `XSUB.COM` and the disk-backed `A0:$$.SUB` continuation;
  the proposed `SUBMIT.CPX` below is not its shipped implementation.
- **BATCHIO.RSX:** the resident input component used by XSUB, not a flow-language
  interpreter or command scheduler. Preserve its Function-10 console fallback
  and safe retirement behavior; future scripted-input extensions require their
  own review.
- **Multiple-command-line (MCL) support:** a separate
  [investigation](../TODO.md#multiple-command-line-mcl-support) of sequential
  commands on one prompt line, useful without a scripting language. Sharing
  future command-source machinery must not make MCL depend on FLOW.
- **Flow control:** optional loadable CPX command logic beyond those facilities.
  Preserve the core CCP inventory and CP/M 2.2 contract. Resident services are
  for work that must remain active during transients, not a reason to move
  the interpreter into the core.

### Questions before design approval

1. Compare Z-System/ZEX practice and the existing
   [scripting backlog](../TODO.md#enhanced-command-automation-and-scripting).
   Select a bounded initial scope from conditional execution, branching/labels,
   variables, loops and nested scripts. Investigate `IF...THEN` alongside
   `IF`/`ELSE`/`ENDIF`, `GOTO`/`CALL` and structured loops; none of these
   spellings or constructs is accepted syntax.
2. Define command-completion status and the treatment of legacy `.COM` programs
   that report none. CPX handled/declined dispatch is not success/failure.
3. Review source precedence and interfaces among interactive commands, MCL,
   submitted commands, nested scripts and program input. Ensure BATCHIO cannot
   consume a pending command as application input. Preserve ordinary command
   tails, quoting and existing `.SUB` substitution.
4. Compare disk-backed continuation, optional RSX-owned state and a later PDS
   allocation for script positions, parameters, variables and nesting.
   [PDS ownership](../docs/architecture/18%20Persistent%20Data%20Segment.txt)
   normally keeps optional state in its RSX; the fixed 192-byte 1.0 history PDS
   has no scripting capacity. The broad PDS description below does not override
   that decision. Retain no pointers into reclaimed CCP, CPX or transient memory.
5. Specify bounds, overflow, abort, error recovery, cold reset and WBOOT resume
   after a transient overwrites the full TPA. Measure permanent, loaded and
   peak workspace costs and net application TPA before recommending placement
   or any ABI change.

The investigation should produce reviewed scope alternatives, a syntax proposal,
state/interface contracts and acceptance criteria. Later implementation would
need independent SUBMIT/XSUB regression and cross-platform lifecycle/failure
qualification. This entry authorizes no implementation, allocation or ABI change.

## Purpose

The BetterCP/M Batch Facility unifies CP/M 2.2 SUBMIT compatibility,
ZEX-style memory-resident command execution, and ZCPR3-style conditional flow
control. Existing `.SUB` files should remain usable, while new scripts gain
variables, conditions, branching, nested execution, error handling, and
scripted input.

The facility is presented as one user feature but is divided into modules so a
small system need not pay for every capability.

## Modules

### SUBMIT.CPX

The foundation provides sequential command execution, positional parameters,
CP/M-compatible substitution, ordinary CCP command lines, comments, command
echo control, `PAUSE`, nested command sources, and compatible execution of
ordinary `.SUB` files. Compatibility is behavioral; BetterCP/M need not use
`$$$.SUB`, reverse-written files, or a drive-A restriction.

### FLOW.CPX

The optional flow package builds on the common batch-stream interface and adds
named persistent variables, quoted parameters, defaults, nested
`IF`/`ELSE`/`ENDIF`, `IF EXIST`, `IF NOT EXIST`, `IF ERROR`, `IF DEFINED`,
string and numeric comparisons, labels, `GOTO`, `CALL`, `EXIT`, `INPUT`, and
message output. Labels and `GOTO` are sufficient for initial-release looping;
structured `WHILE` and `FOR` constructs may follow later.

### BATCHIO.RSX

Scripted input to a transient program cannot be implemented solely by a CPX,
because CPX and CCP memory is reclaimable during transient execution.
`BATCHIO.RSX` is therefore the optional resident input-injection component. It
intercepts the defined console-input path while an input block is active and
otherwise chains transparently. The Batch Facility may install it when needed
and unload it after the scripted-input scope ends.

## Persistent execution state

The Persistent Data Segment (PDS) holds descriptions of active batch work, not
reclaimable CPX code or transient pointers. At minimum it records the command
source stack, source positions, parameters, variables, conditional stack,
current execution state, last command/error status, echo mode, and any active
scripted-input source. This permits WBOOT to reconstruct CPXs and the CCP and
then resume the command environment coherently.

Inactive conditional branches are parsed sufficiently to maintain nesting but
their commands are not dispatched.

## Command sources

Batch processing consumes the common completed-command stream. Sources may be
standard `.SUB` files, extended BetterCP/M batch files, ZEX-compatible memory
streams, nested files invoked with `CALL`, the CCP multiple-command queue, or
other CPXs. All sources use the same dispatch and flow-control machinery.

Raw physical keystrokes and scripted program input are not completed commands.
They enter through the command-input system and remain distinguishable by
source and interpretation policy.

## Required supporting contracts

- a versioned command-source and completed-command interface;
- a persistent batch-context representation with explicit resource limits;
- a standard command-completion status for `IF ERROR` and `EXIT`;
- CPX dependency and ordering declarations;
- a CPX-to-RSX control interface for scripted-input installation and data;
- defined abort, WBOOT, nesting, overflow, and recovery behavior; and
- transactional loading so failure can return to a batch-free command prompt.

The design progression is:

**CP/M SUBMIT -> ZEX/XSUB-style automation -> ZCPR3-style flow control.**
