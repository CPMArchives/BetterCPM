# Shared input remaining consumer audit

2026-10-22, after COPY Build 005, PIP Build 028, DUP Build 006, SYSGEN Build 007 and CONFIG Build 015 integration.

This inventory distinguishes input components already shared, remaining suitable
candidates, and application command/data protocols that should retain their own
semantics. It does not claim that every keyboard read has been migrated.

| Utility/interface | Current state | Remaining action |
| --- | --- | --- |
| DUMP Find/Go To | Shared compatibility editor and screen-field renderer | No forced command-navigation migration |
| CONFIG startup and freeform numeric fields | Shared editor and inline renderer | Retain current qualified profile |
| CONFIG menu choices, drive selection and save approvals | Shared choice-only controller with existing CHOICE rendering/caller policy in Build 015 | Qualified; menus, physical attachment and all three save approvals migrated |
| DUP FORMAT/COPY confirmation | Shared one-key controller | Already qualified |
| DUP main menu and drive selection | Existing CHOICE display plus shared controller in Build 006 | Qualified; caller dispatch/cancellation and command-line bypass preserved |
| SYSGEN install/package replacement approval | Shared one-key controller | Already qualified |
| SYSGEN interactive destination B..D selection | Shared controller with unchanged KEY/caller loop in Build 007 | Qualified; repeated heading, B..D selection and Ctrl-C exit preserved |
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
the subsequent call, not just a search for a register load. SYSGEN destination selection and DUP menu/drive integration now share their
existing controllers; neither adds a second controller or field editor.

## CONFIG memory gate resolved

Dual-platform Build 014 was 15,552 bytes, leaving 64 bytes before the existing
3E00h private stack. A naive added binding did not fit. Build 015 first recovers
206 bytes: 49 short branches and 157 bytes of identical message/token storage.
It then adds a 218-byte choice-only binding for a final 15,564 bytes, leaving
52 bytes before the same stack boundary. Both 20-byte validation profiles and
both disk-boot IOBYTE descriptors remain included. No workspace or resident
allocation changed.

The compatibility binding transports one KEY event to the existing caller;
it does not reinterpret menus, defaults or any-non-Y-declines save policy.
The startup and numeric editor keep their separate reader and existing buffer.
See [CONFIG choice qualification](CONFIG%20Choice%20Input%20Qualification.md).

## Remaining scope

The suitable prompted-field consumers in this audit are migrated. Application
command/data protocols, navigation and acknowledgment pauses above intentionally
retain their existing semantics. This is not a claim that every keyboard read
must use a field editor. Any future standard-profile behavior change needs its
own specification and qualification.
