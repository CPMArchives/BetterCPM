# Engineering Specification 201: FDF Production Selector Closure

## Result

The disk backends and DUP now invoke FDF.RSX through its production Function
183 selector. Seven call sites had retained the former Function 209 value after
the namespace migration: capability discovery and geometry normalization in
both configuration overlays, logical-address mapping in both disk backends,
and DUP capability discovery. FDF.RSX itself and its carrier already published
Function 183.

This mismatch made an installed FDF provider appear unavailable to those
callers. It could reject an otherwise valid mixed-sector binding before DUP
reached its backend decision. The correction changes selector constants only;
it does not alter the disk ABI, normalized binding, resident allocation, or
53 KiB TPA boundary. The Model 4 controller's `D1h` restore command is unrelated
and remains unchanged.

## Focused evidence

The complete system and z80pack images build successfully. The retained
z80pack DUP test proves both sides of its formatter boundary:

- a uniform raw image is formatted completely and read back as erased; and
- with FDF.RSX loaded, a mixed-sector MM SUPER binding is accepted by CONFIG,
  DUP receives the backend's unsupported result, and the raw image remains
  byte-for-byte unchanged.

The relocated FDF unit test continues to pass 1,536 catalogue-boundary mappings
at two load addresses together with rejection, private-stack, and unload cases.

The remaining DUP capability-closure work is to publish and execute the full
two-platform supported/unsupported matrix; this correction supplies the
production selector path that matrix requires.
