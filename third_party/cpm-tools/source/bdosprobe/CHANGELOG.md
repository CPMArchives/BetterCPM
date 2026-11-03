# BDOSPROBE changelog

## 0.1.0-dev4 — 2026-08-31

- Added `/SELECT`, the first guarded reversible-state probe.
- Obtained the current drive with function 25 and passed only that same drive
  to function 14.
- Compared the current drive, login vector, and read-only vector before and
  after selection and reported any change.
- Recorded successful dev3 `/USER` tests in user areas 0 and 3 under Montezuma
  Micro CP/M 2.2.
- Validated `/SELECT` from current drives A and B under Montezuma Micro CP/M
  2.2. Both runs preserved the selected drive, login vector 0003H, and
  read-only vector 0000H.

## 0.1.0-dev3 — 2026-08-31

- Added `/USER` using function 32 only with the documented E=FFH query
  sentinel.
- Queried twice and reported whether the current user remained unchanged.
- Extended raw input reporting so DE shows the actual value supplied.
- Retained 8080 compatibility and dual-CPU execution tests.

## 0.1.0-dev2 — 2026-08-31

- Added `/DISK` probes for the login vector, current disk, and read-only vector.
- Added `/MEM` probes for the allocation-vector and DPB addresses.
- Added `/CONSOLE` using the observational console-status call.
- Reused the dev1 raw result-capture harness for every call.
- Validated all dev2 groups on Montezuma Micro CP/M 2.2 and under z80pack in
  Z80 and Intel 8080 modes.

## 0.1.0-dev1 — 2026-08-31

- Added the reusable post-BDOS register capture harness.
- Added `/CPM`, using only BDOS function 12 (Return Version Number).
- Reported raw A, BC, DE, HL, flags, and SP, while distinguishing documented
  results from incidental observations.
- Added Z80 and Intel 8080 execution tests.
