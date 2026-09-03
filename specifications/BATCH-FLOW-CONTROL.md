# BetterCP/M Batch and Flow-Control Facility

Status: proposed for the 1.0 distribution

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

The persistent DATA area holds descriptions of active batch work, not
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

