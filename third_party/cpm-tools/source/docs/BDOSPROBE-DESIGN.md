# BDOSPROBE safety and probe design

BDOSPROBE is an observation harness, not a conformance verdict generator. A
probe records inputs, immediate machine-level returns, and a conservative
interpretation. It does not infer that an incidental register value is part of
the BDOS contract.

The CP/M executable is `BDOSPRB.COM`, shortened to fit the 8.3 filename limit.

## Probe admission matrix

| Class | Examples | Initial policy |
|---|---|---|
| Pure observation | 11 console status; 12 version; 24 login vector; 25 current disk; 27 allocation vector; 29 read-only vector; 31 DPB address | Admit one at a time after documenting inputs and official outputs. |
| Query with sentinel | 32 get user number with E=FFH | Admit only in the documented query form. |
| Reversible process state | select disk, set DMA, set user | Defer until the harness captures the old value, restores it on every exit, and tests restoration. |
| Filesystem activity | search, open, read, close | Defer; use named disposable fixtures and document directory/FCB side effects. |
| Persistent write | create, write, delete, rename, set attributes | Excluded from ordinary probes. Any future destructive suite must be separate, explicit, and run only on disposable media. |
| Termination or reset | warm boot, terminate, reset disk system | Excluded until an isolated child-probe design can preserve and report results safely. |

## Dev4 boundary

Dev1 established function 12. Dev2 also admits functions 11, 24, 25, 27, 29,
and 31, grouped as `/CONSOLE`, `/DISK`, and `/MEM`. Before each call it reports
the selected function number in C and `DE=0000H`. Immediately after return it
saves A, HL, BC, DE, flags, and the balanced stack pointer. Only the documented
result of each function is interpreted; the remaining registers are raw
harness observations.

The source uses only 8080 instructions despite Zilog assembly spelling. The
same executable is tested under z80pack's Z80 and Intel 8080 modes.

No dev2 call writes a disk or intentionally changes BDOS process state.

Dev3 admits function 32 only with E=FFH, the documented Get User Number
sentinel. `/USER` performs two query-only calls, reports the returned user
number, and compares the results as an unchanged-state check. The set-user
form is not present.

Dev4 admits function 14 only through `/SELECT`. The probe first obtains the
current drive from function 25, snapshots the login and read-only vectors,
passes that same drive number to function 14, and samples all three public
values again. It neither accepts a drive argument nor contains a path for
selecting a different drive. A changed value is reported as a warning.

## Validation record

Dev3 has been assembled with ZSM4 and Digital Research LINK and executed under
z80pack in both Z80 and Intel 8080 modes. It has also been exercised on
Montezuma Micro CP/M 2.2 in the TRS-80 emulator. On that system the version
probe returned A=22H and HL=0022H; the current drive was B; the read-only
vector was 0000H; the allocation-vector and DPB addresses were F77DH and
F5F8H; and console status reported no pending character. Values such as flags,
SP, and undocumented return registers are observations, not required results.
The `/USER` probe subsequently reported user 0 and user 3 correctly on the
same system and confirmed that repeated query-form calls left both unchanged.
Dev4 `/SELECT` was then run with A and B as the current drive. Function 14
received E=00H and E=01H respectively; both runs preserved the current drive,
login vector 0003H, and read-only vector 0000H.

## Planned sequence

1. Compare the observational returns across additional CP/M-compatible systems.
2. Design explicit restoration before admitting a probe which selects a
   different state value.
3. Keep persistent writes, termination, and reset outside the ordinary probe.
