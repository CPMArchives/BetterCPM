# SYSGEN 1.0 specification conformance

The consolidated [SYSGEN specification](SYSGEN%20Specification.md) retains the
existing installation engine. The audit identified a command-tail validation
gap in package mode: the two CCP-prepared FCBs could identify SYSTEM.SYS and a
destination even when the full invocation contained extra or user-qualified
operands. SYSGEN now checks the entire `[drive:]SYSTEM.SYS destination:` tail
before entering the package loader. Drive-source operands also require a
separator. Valid syntax, installation confirmation and media handling remain
unchanged.

SYSGEN is now Build 002. Its additional code is transient; BIOS, BDOS and the
resident layout are unchanged. The utility remains below its private-stack
boundary. The 161-record input package and 160-record installed payload,
header/length checks without a payload checksum, geometry validation,
physical-drive protection, source buffering, record-zero-last writes,
read-back comparison and filesystem isolation remain implemented as specified.

## Validation

`test_sysgen_command_line.py` exercises 17 valid and invalid command tails with
plausible FCBs. Invalid tails must return a syntax error without entering either
source loader. It also checks standalone `/VER` and rejects combined version
requests before initialization.

The final binary passes `test_z80pack_sysgen_install.py` on disposable media:
a populated filesystem is byte-preserved, its sentinel file recovered, and the
installed system cold-boots. `test_z80pack_sysgen_refusal.py` confirms data-only
media are refused before confirmation or writes.

The final binary also passes `test_sysgen_cross_format.py` on trs80gp: both
disk-source and SYSTEM.SYS package-source installations preserve the populated
filesystem on a larger compatible format, and each installed target cold-boots.

All disk utilities assemble successfully. Documentation references and
whitespace are checked separately. These focused results do not replace final
release qualification.
