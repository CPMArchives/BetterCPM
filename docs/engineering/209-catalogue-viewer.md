# Native detail and comparison viewer

D selects one definition. P selects two independently and starts in
differences-only mode. For each selection, enter a working-catalogue ID,
`/` for an external .FDB and ID, `@` for the working editor, or
`:B`, `:C` or `:D` for an active logical drive. External inspection does
not change the catalogue's save default. Captured drives have unknown catalogue
IDs and descriptions, displayed explicitly rather than as numeric zero.

Keys 1–4 select Geometry, Addressing and sector map, CP/M parameters and FDB
encoding, and Effective filesystem layout. Geometry and addressing flags are
decoded with their meaning beside each value. A toggles all values and
differences; the heading shows the current mode. Q or BREAK returns to the
session. Sector maps use < and > for eight-slot ranges. Differences mode hides
unchanged slot IDs and sizes and detects sectors absent on either side.

Each source has its own snapshot, including the complete sector-ID and size
arrays. The fourth page compares raw capacity, directory byte offset, block
bytes, directory bytes, allocated filesystem bytes and directory end byte.
These are effective values, so equal OFF values can yield different directory
offsets. Invalid editor geometry is refused for inspection, with the edited
working object preserved for correction.

Build tools emit FDB.COM and FDBVIEW.OVL. Keep the pair together on the current
drive and user area. The viewer is compiled against that resident build's
symbols and loaded above the scratch catalogue. A build tag and a CRC over
the complete record-padded overlay are checked before execution. External
catalogues use the shared native FDB validator, with a separate ownership
bitmap in the import scratch arena. External sources are bounded to 9,472
compiled bytes. A damaged, mismatched or absent overlay and an invalid source
return an error without changing pending work.

## Qualification

Run the session, editor and round-trip test programs. The session test checks
the MMI012 directory offset and compares it with an external cylinder-unit
variant. Both have OFF=2, but their directory offsets are 10,240 and 20,480.
It also checks corrupt-overlay refusal. The editor test checks active-drive
unknown identities and preservation of temporarily invalid editor work.

The platform qualifier accepts --details. It displays MMI012, compares it
with itself, inspects B and C independently, inspects the loaded working
editor and an external catalogue, then continues importing and safely saving
the session. Host readback checks that inspection preserved the working
catalogue and import source.
