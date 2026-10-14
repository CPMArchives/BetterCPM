# Character device capability query

BIOS API 1.6 adds a private JP vector at BIOS+63. Calling it returns a
16-bit capability word in HL without I/O or allocation. A, BC, DE and IX
are preserved. It uses no mutable scratch storage.

Four nibbles describe supported IOBYTE selectors: CON in bits 0–3, RDR
in 4–7, PUN in 8–11 and LST in 12–15. Each bit corresponds to selector
0, 1, 2 or 3 of that logical device. Model 4 returns 2002h; cpmsim returns
7337h. Support means an implemented route, not ready or present media.

Clients must establish compatible BIOS API version 1.6 or later through
the existing version descriptor before calling this vector. Older BIOS
layouts may contain unrelated code at that address. PIP rejects physical
aliases when the query is unavailable and retains legacy logical behavior.

Existing private vectors through +60 retain their positions. Planned
monitor vectors follow at +66, +69 and +72. No BDOS growth is required.
