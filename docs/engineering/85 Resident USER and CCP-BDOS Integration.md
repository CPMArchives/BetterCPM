# Engineering Specification 85: Resident USER and CCP-BDOS Integration

## Status

BetterCP/M now provides a resident CCP `USER` command, and required DIRTEST
case 0567 is physically qualified on the TRS-80 Model 4 target.

## Command contract

The CCP accepts decimal `USER 0` through `USER 31`. It validates the operand
and delegates the state change to BDOS Function 32. The CCP does not retain a
private copy of the current user; command execution and transient applications
therefore observe the same resident BDOS state.

The conformance image installs `DIRTEST.COM` in users zero and one. This is a
test fixture, not a cross-user command-search rule: after `USER 1`, ordinary
CP/M lookup correctly requires the transient program to be present in user
one.

## Memory-map revision

The previous CCP region at `E940h..ECFFh` was exactly full before `USER` was
added. Directory Services currently ends at `E8A0h`, leaving a verified gap
below the CCP. The CCP base initially moved to `E8C0h`; the later addition of
public SECTRAN calls grew Directory Services through `E8C0h`, so the base is
was `E8D0h`; live-DPB refresh moved it again to `E8E0h`. This preserves a
ten-byte guard after Directory Services and
retains `ED00h..EEFFh` for the BIOS physical-sector buffer.

The resulting CCP is 1,033 bytes in the 1,056-byte `E8E0h..ECFFh` region.
Native CP/M and cross builds are byte-identical. The composed resident system,
all 39 BDOS function tests, warm-boot/CCP test, native loader build, and
physical boot test pass after the relocation.

## Physical result

The required workflow ran in one `trs80gp` boot session:

```text
A>USER 1
A>DIRTEST /0567
0567  P  R  CCP/BDOS user=01; next=00
Summary: 1 pass, 0 fail, 0 error, 0 observations
```

This completes all eight required User Areas cases. Engineering Specification
86 records diagnostic 0565 and closes the group and the DIRTEST catalog.
