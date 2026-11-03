# BDOSPROBE

BDOSPROBE is a CP/M-resident harness for observing documented BDOS calls and
recording their complete returned register state. Its CP/M command and files
are named `BDOSPRB` to fit the CP/M 8.3 filename limit.

Development release `0.1.0-dev4` adds the first guarded state probe. It obtains
the current drive, selects that same drive, and verifies that the current
drive, login vector, and read-only vector have not changed. Every call reports
A, BC, DE, HL, flags, and SP, but interprets only documented results.

```text
BDOSPRB
BDOSPRB /CPM
BDOSPRB /DISK
BDOSPRB /MEM
BDOSPRB /CONSOLE
BDOSPRB /USER
BDOSPRB /SELECT
BDOSPRB /H[ELP]
BDOSPRB /INFO
BDOSPRB /VER[SION]
```

Run `./build.sh` to assemble with ZSM4 and Digital Research LINK and exercise
the result under z80pack in both Z80 and Intel 8080 modes. Dev3 has also been
tested in user areas 0 and 3 on Montezuma Micro CP/M 2.2 in the TRS-80
emulator. Dev4 `/SELECT` has passed there from current drives A and B; both
runs preserved the selected drive, login vector `0003H`, and read-only vector
`0000H`.

The probe-selection rules and future sequence are in
[`docs/BDOSPROBE-DESIGN.md`](../docs/BDOSPROBE-DESIGN.md).
