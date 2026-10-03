# Engineering Specification 180: Name-Based CPX Profile Control

## Result

BetterCP/M Function 176 and `CPX.COM` now use the version-1 name-based request
defined in the programmer guide. The protected CONFIG overlay edits the ordered
four-record reconstruction table directly. It contains no RCP- or HELLO-specific
identity, membership mask, or canonical rebuild path.

The completed overlay occupies 1,018 of its fixed 1,024 bytes. The disk-control
regions and memory map are unchanged. Name-based CPX control leaves the former
`CPTFLAGS` byte available; Step 5 subsequently assigned bit 0 as the once-only
cold-startup marker without moving the persistent layout. Other bits remain
reserved.

## Validation boundary

`CPX.COM` owns syntax validation because the CCP already normalizes the second
command token into a default FCB. The utility rejects drive-qualified, blank,
wildcard, or non-CPX names and copies the normalized eight-byte stem into the
request. The protected handler checks the request version and operation,
rejects a blank mutation stem, enforces the four-record bound, and performs
only bounded table operations. This division avoids duplicating CP/M filename
parsing in the six bytes left in the overlay.

The service preserves `DE`. Enumeration is indexed and returns the active stem
through the request block. Duplicate load and absent unload are successful
no-ops. Removal shifts later records left without changing their order.

## Qualification

The focused emulator test covers unsupported versions and operations, blank
names, enumeration, arbitrary names, duplicate load, capacity rejection,
middle removal, ordering, and absent unload. Runtime qualification exercises
`CPX.COM` load, list, unload, WBOOT reconstruction, and transient fallback.
