# Catalogue inspection foundation

D displays an ID from the working catalogue. P selects two working-catalogue
IDs and starts with differences only. Keys 1–4 select geometry, addressing and
sector map, CP/M parameters, and derived layout. A toggles all values and
differences. Q or BREAK returns to the session. Sector maps use < and > to
move by eight slots. Each side shows sector IDs and effective byte sizes.

The viewer is read-only. Catalogue entries are copied into private comparison
records, while the working catalogue and editor retain their contents.
The fourth page compares raw capacity, directory byte offset and allocation
block bytes as effective values rather than comparing only OFF or BSH.

Build tools emit FDB.COM and FDBVIEW.OVL. Keep the pair together on the current
drive and user area. The viewer is compiled against the resident symbols of
that exact build. FDB checks a matching build tag and the overlay's complete
record-padded CRC before executing it. The overlay is loaded into the catalogue
scratch arena, below the resident editor. An absent, damaged or mismatched
overlay returns an error and preserves the working session.

This is an initial working-catalogue inspection increment. Spec 209 remains open
for independently selecting active drives, the working editor and external
catalogues, rendering unknown active-record values, semantic flag descriptions,
and the complete effective filesystem-layout report. Map rows are shown
together on page 2 even in differences mode.

Run the session, editor and round-trip test programs. The platform qualifier
accepts --details to display MMI012, compare it against itself, then continue
importing and safely saving the session. The core test verifies the 10,240-byte
directory offset and overlay corruption refusal.
