# Portable memory consolidation — historical intermediate checkpoint

This report preserves the intermediate findings. The completed layout and tests
are recorded in [report 127](127%2053K%20Memory%20Consolidation.md).

BetterCP/M is a general CP/M implementation. trs80gp is a test environment,
not an architectural requirement. Common system code must not depend on
Model 4 memory-map switching, hidden RAM, or additional memory banks to meet
the 53–54 KiB TPA target. Machine-specific I/O belongs in platform adapters.

The experimental upper-RAM placement and console memory-map wrappers have
been removed. The current intermediate layout places every resident service
and workspace below the test platform's ordinary RAM ceiling. It is not the
final target layout: TPA ends at C9FDh, giving 51,453 bytes above 0100h.

Retained consolidation work includes one physical disk transfer engine and
four resident logical-drive records. Sixteen format choices per CONFIG page
remain a separate UI requirement. Shared allocation/check workspace requires
additional regression coverage for drive switching before release.

An attempted extension/CCP stack merge failed the emulator command test;
separate stacks were restored. Do not merge these stacks: the CCP uses the
system stack while calling extension services.

This checkpoint is uncommitted and is not a completed BIOS release. Remaining
work includes the full disk/RSX regression suite, further portable size
reductions, and verification of the 53–54 KiB target.


Follow-up: [53 KiB consolidation and validation](127%2053K%20Memory%20Consolidation.md) records the completed September 7 layout.
