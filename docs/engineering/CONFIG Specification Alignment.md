# CONFIG engineering-specification alignment

## Authority and current status

The current CONFIG engineering specification is the implementation baseline.
Build 003 begins closing the audit gaps; it does not declare CONFIG complete.
The spec's cost/backend gates remain required for proposed runtime facilities.

| Requirement | Current status |
| --- | --- |
| Implemented domains only in menu | Corrected: F–J retained; A–E placeholders removed |
| Utility identity | Menu and /VER use the same metadata-owned version/build |
| Full command-tail validation | Implemented before INIT, catalogue reads or changes |
| /SHOW | Active physical/logical settings and saved startup; saved-drive defaults still open |
| /STARTUP="..." | Confirmed, verified startup-only save; does not execute command |
| /DEFAULT | Pending-only semantics agreed; implementation/default-domain sources open |
| Drive command-line parity | Open; retain existing drive storage/activation contracts |
| Persistent IOBYTE, printer and serial | Required runtime-cost/backend audits open |
| Native build | ZSM4/LINK and cross assembly match at 12,843 bytes |

The no-longer-offered keyboard/video sections are outside CONFIG's 1.0 scope;
printer/serial/IOBYTE entries may be added only when actual supported facilities
are implemented and qualified. An unavailable backend must not become a fake
working menu item.

## Command semantics and safety

No operands enters the existing menu. `/SHOW` returns without a completion
pause and does not alter the disk. Invalid/extra operands fail before INIT or
file access. `/VER` remains standalone and pure. Valid quoted startup command
text is parsed as data, avoiding false version detection on `/VER` inside it.

`/STARTUP="..."` prepares a complete canonical BCST record and uses the
established pending-only save path. It asks the existing Y/N question. A decline
returns immediately; acceptance writes/verifies both protected startup records
and uses the existing rollback on failure. It neither executes the command nor
saves active drive profiles. Empty text disables startup. The CLI's command
capacity is bounded by the complete CCP tail, including option/quote overhead.

## Evidence

- `test_config_command_line.py`: full-tail parsing, quoting, rejection before
  side effects, identity purity, menu scope and metadata-owned title.
- `test_config_startup_save.py`: first/second-record failures restore old BCST;
  rollback failure reports possible damage; CLI reports do not pause or claim
  success after failure.
- `qualify_config_command_line.py`: six live cpmsim cases on private disks:
  /SHOW, malformed request, declined save, accepted save, quoted /VER data and
  disabling startup. Inspection/decline/invalid cases preserve the entire image;
  accepted saves alter only BCST's two physical records, checked with the
  independent host parser. Evidence: build/config-command-line/run-_xywifnc.
- `build_native_config.py`: actual ZSM4/LINK parity, with deterministic reserved
  workspace bytes. Existing common utility identity tests continue to pass.

These checks do not yet establish final Model 4, clean-distribution or all-domain
CONFIG conformance. All remaining rows above must be addressed before closure.

## PIP and DUP reconciliation

PIP Build 026 passes all 18 focused campaigns. Its completion qualification
supersedes historical development notes; the obsolete opening work-review
heading now states that status. DUP Build 003 passes direct parser/dispatch and
cleanup tests; the specification version example is updated, while the
command-line report identifies Build 002 as the introduction of that feature.
DUP's explicitly retained legacy menu title is part of its present contract.

The final parser rejects overlong command-tail lengths before reading operands
and accepts the maximum 127-byte CLI tail without overwriting its text buffer.
Final artifact repeat: `build/config-command-line/run-d9cgmira`.
