# IOBYTE cold default

BetterCP/M initializes address 0003h to 95h (10010101b): CON=CRT,
RDR=PTR, PUN=PTP, LST=LPT. The Model 4 stage-one cold loader performs
this store before loading the resident system. cpmsim's platform initializer
performs it on BIOS cold entry, shared by RAM and ROM boot. WBOOT and RSX/CPX
reconstruction do not initialize this byte, preserving Function 8 and direct
page-zero changes.

The Model 4 resident BIOS remains within its existing fixed slot. cpmsim BIOS
adds five immutable bytes; the accepted packing measurements and relocated
template/initializer addresses advance accordingly. TPA and RAM ownership are
unchanged. The full cpmsim image builder checks RAM templates, immutable
packing and source-derived address relocation.

`tools/test_iobyte_boot.py` executes the emitted Model 4 cold-store prefix and
warm entry and runs two fresh cpmsim sessions, checking Function 7 against the
page-zero value, Function 8, WBOOT and RSX reconstruction. This does not claim a
new complete Model 4 media campaign or protected-ROM runtime campaign.

## Routing limitation

The current BIOS does not decode all IOBYTE selectors. Model 4 exposes fixed
console functions and unassigned reader/punch/list leaves; cpmsim substitutes
its host reader. Initialization makes the published default deterministic; it
does not provide missing routing. STAT/device qualification must establish and
resolve the platform capability contract separately, without assuming every
assignment printed by STAT corresponds to a functioning physical device.
