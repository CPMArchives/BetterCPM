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

## Current routing and persistence boundary

The shared IOBYTE routing and character-device capability query now exist.
Model 4 advertises CRT console and CRT list output (`IO_CAPS=2002h`); its
reader returns EOF and its punch is unassigned. LST=CRT uses the monitor output
path; LST=LPT does not imply a physical printer driver exists.

cpmsim advertises `7337h`. Its character dispatcher routes console, reader,
punch and list selections to the supported console, auxiliary and printer
leaves. Auxiliary input/output uses port 5; printer status/output uses ports
2/3. See `src/platform/z80pack/chario.inc` and the platform builder's capability
constant. These endpoints do not provide a baud/parity/flow-control API.

STAT changes live assignments; no CONFIG persistent IOBYTE control has yet
been implemented. The compiled 95h cold default remains unchanged. The
persistence alternatives and remaining audit work are recorded in
[CONFIG Runtime Audit](CONFIG%20Runtime%20Audit.md).
