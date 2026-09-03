# Engineering Specification 104: Runtime RSX Proof

## Status

Implemented proof of concept. The interfaces in this specification are
provisional and are not yet a stable third-party ABI.

## Purpose

This milestone proves that BetterCP/M's movable compatibility gateway can
host a protected resident-system-extension chain without making the CCP or
CPXs resident. It deliberately tests the complete lifecycle, not merely a
direct call to a fixed demonstration routine.

## HELLO.RSX

`HELLO.RSX` is not part of the cold-boot profile. `RSX LOAD HELLO` reads its
compact `BRX1` carrier from system slot 9, allocates one KiB immediately below
the fixed `C000h` system core, relocates the module, links its next pointer to
the core BDOS entry at `C100h`, and moves the three-byte CP/M gateway below the
new protected region.

The runtime header is:

```text
offset  size  meaning
0       2     next RSX entry, initially C100h
2       2     this RSX's dispatch entry
```

The proof dispatcher owns experimental BDOS Function 201. It prints
`Hello from HELLO.RSX` and returns `HL=5253h`. Calls it does not own jump to
the next RSX or the core BDOS.

## Runtime control

Experimental BDOS Function 202 implements the initial manager path. `E=0`,
`1`, and `2` mean query, load HELLO, and unload HELLO. `RSX.COM` exposes these
as `RSX LIST`, `RSX LOAD HELLO`, and `RSX UNLOAD HELLO`.

Loading or unloading completes through WBOOT. The installed RSX remains in
protected memory; WBOOT reconstructs BASIC.CPX and the CCP beneath the moved
gateway. Unloading restores the no-RSX gateway and returns the allocation to
the TPA. The one-KiB proof allocation makes this visible as 47K before load,
46K while installed, and 47K after unload.

`RSXTEST.COM` invokes Function 201 only through `CALL 0005h`. It therefore
proves the public application path rather than calling HELLO.RSX directly.

## Verified behavior

The physical `trs80gp` test verifies:

- Function 201 is unsupported before installation.
- HELLO.RSX intercepts Function 201 after installation.
- The dynamic gateway and page-zero TPA boundary move together.
- An ordinary transient program may overwrite the command region and WBOOT
  reconstructs the CPXs and CCP while preserving the RSX.
- Unload removes interception and restores the original TPA boundary.

The later general `BRSX` carrier, arbitrary filename loader, enumeration, and
multi-module chain supersede this proof format in Engineering Specification
120. Saved cold-boot profiles, initialization/shutdown calls, and a formal
bypass ABI remain future work.
