# Shared input remaining consumer audit

2026-10-22, after COPY Build 005 and PIP Build 028 integration.

This inventory distinguishes input components already shared, remaining suitable
candidates, and application command/data protocols that should retain their own
semantics. It does not claim that every keyboard read has been migrated.

| Utility/interface | Current state | Remaining action |
| --- | --- | --- |
| DUMP Find/Go To | Shared compatibility editor and screen-field renderer | No forced command-navigation migration |
| CONFIG startup and freeform numeric fields | Shared editor and inline renderer | Retain current qualified profile |
| CONFIG menu choices, drive selection and save approvals | Existing disk-common KEY/CHOICE and caller policy | Suitable choices, but full controller integration needs a separate space reduction first |
| DUP FORMAT/COPY confirmation | Shared one-key controller | Already qualified |
| DUP operation/recovery menus and drive selection | Existing disk-common CHOICE/ASKDRV | Suitable next increment; preserve caller dispatch, retry, Ctrl-C and display behavior |
| SYSGEN install/package replacement approval | Shared one-key controller | Already qualified |
| SYSGEN interactive destination B..D selection | Existing KEY/caller loop | Suitable next increment; preserve selection, repeated heading and Ctrl-C exit |
| ERA confirmation/recovery | Shared choice controller | Already qualified |
| REN choices and replacement name | Shared choice/append compatibility modules | Already qualified |
| COPY overwrite, verify recovery and replacement name | Shared choice/append compatibility modules | Already qualified |
| MOVE | Current implementation has no interactive prompts | No new UI capability implied |
| PIP protected replacement approval | Shared one-key controller in Build 028 | Qualified separately |
| PIP command line, interactive command loop, HEX and device dialogue | Parser, BDOS buffered input and transfer/data protocols | Preserve DRI semantics; outside this prompt migration |
| TYPE page/file navigation | Application command loop, including Ctrl-C as next page | Retain navigator; do not reinterpret it as generic text-field cancellation |
| ED command and text input | Historical editor command language | Explicit compatibility boundary; do not substitute a utility-field editor |
| DDT historical reproduction | Separate development task | Preserve exact reproduction; evaluate library only in a later adapted version |
| STAT, TIME, SUBMIT/XSUB, CPX/RSX, VER/CLS/USER, SYSBUILD/RESPACK/RLMBUILD | Command-tail parsing/operations, not editable prompted fields in their present implementations | No field editor to substitute; preserve command semantics |
| Monitor/test utility “press a key” pauses | Acknowledgment or application test input | Not ordinary line editing or approval; no automatic conversion |

`LD C,1` alone is not evidence of a console read. For example, STAT uses C as
an exact-token length and decimal-printing state. Classification must include
the subsequent call, not just a search for a register load. DUP and SYSGEN menus
remain candidates even though their destructive confirmations already migrated.

## CONFIG memory gate

Current dual-platform CONFIG Build 014 is 15,552 bytes, SHA-256
`2167646cfe1506405cd1834deaf26d3bc4712dc8a5911d04c26e9040fbfad9e4`.
At origin 0100h it ends at 3DC0h, leaving 64 bytes before the existing 3E00h
private-stack boundary. Both validation and IOBYTE descriptor records remain
included.

The existing minimal shared confirmation binding assembles to 220 bytes,
including its caller-owned choice state, with an external KEY callback. Adding
it without code removal would exceed the present gate by 156 bytes. A full
menu/text/layout profile costs more. Merely changing prompts or dropping a
validation profile to make room is not this migration's contract.

Keep the current stack, workspace, validation profiles and already-qualified
editor integration. A subsequent bounded CONFIG refactor must demonstrate real
savings and rerun affected configuration/save/recovery checks before adding
controllers. This is not a TPA expansion or authorization to weaken validation.
The measured fixture/report is `build/pip-shared-input/config-budget.json`.

## Suggested next increments

1. DUP menu/drive choices, using its existing linked choice controller and
   preserving caller-specific invalid-input and recovery policies.
2. SYSGEN destination-drive selection, reusing its existing controller.
3. CONFIG code-size reduction and then its remaining choices, if the measured
   result fits while retaining its existing safety and workspace contracts.

Any further standard-profile behavior change should be deliberate and separately
qualified; source reuse alone does not authorize changing keys or defaults.
