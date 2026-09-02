# Engineering Specification 56: Transient COM Loader

## Milestone

The BetterCP/M CCP can now load and execute a transient `.COM` program from the
physical system disk. The generated DMK includes `HELLO.COM` as the first
end-to-end fixture.

## Command resolution

After checking resident built-ins, the initial loader accepts a bare command
name of one through eight characters, constructs an uppercase `NAME.COM` FCB,
and calls BDOS Open File. Explicit extensions, drive prefixes, arguments,
default FCB parsing, and command search paths remain later CCP work.

An absent or syntactically unsupported command retains the current `?` result.

## Loading and entry

The CCP loads sequential 128-byte records beginning at `0100h`, advancing the
DMA address after every successful read and refusing to cross the resident BDOS
boundary at `C100h`. At EOF it restores DMA `0080h`, clears the provisional
default-FCB area, creates an empty command tail at `0080h`, and transfers control
to `0100h`.

The entry stack contains a zero return word. A normal transient `RET` therefore
reaches page-zero WBOOT. Function 0 and explicit `JMP 0000h` already reach the
same reconstruction path.

## Physical fixture

`HELLO.COM` uses only the public CP/M interface: it begins a new line, prints `Hello from
BetterCP/M` with BDOS Function 9 and executes `RET`. The DMK builder installs a
standard user-zero `HELLO   COM` directory entry with one record in 16-bit
allocation block 2. The file and directory begin after the two reserved system
cylinders; no private loader shortcut is used.

## Resident placement

At this milestone the enlarged CCP remained resident at `EA40h`. BIOS directory, checksum, and
allocation workspaces were moved to hardware-safe RAM (subsequently relocated
from `F300h` to `EC80h`) through
`F3D1h`, leaving the CCP room to grow below the physical buffer at `ED00h`.
Those workspaces are runtime storage and do not enlarge the disk-loaded sparse
resident image.

## Verification

The CCP, BIOS, BDOS, directory services, gateway, and both boot stages retain
native CP/M and cross-build byte identity. The automated physical test waits for
the prompt, types `HELLO`, requires the transient's message, and verifies the
prompt returns through `RET` and WBOOT. This covers the interactive
keyboard-to-CCP-to-BDOS-to-disk-to-TPA path without a private loader shortcut.

## Next increment

Implemented by [Engineering Specification 57](57%20Resident%20DIR.md).
