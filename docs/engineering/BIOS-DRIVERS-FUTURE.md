# Post-1.0 consideration: loadable BIOS device drivers

Discussed September 7, 2026. Explicitly deferred until after BetterCP/M 1.0.
This is a proposal for later investigation, not a 1.0 requirement, an
implementation instruction, or a completed architecture decision. Continue
with the current statically linked TRS-80 and cpmsim adapters for 1.0.

A common BIOS core could dispatch through a small driver interface. Prefer
investigating device/controller modules over a single opaque module per machine:

- Minimal platform glue for memory mapping, interrupts and bus access.
- Console drivers for keyboard/display or serial terminals.
- Disk-controller drivers, each potentially serving several physical drives.
- Optional serial, printer, clock and other drivers.

A machine configuration would select modules and provide ports, addresses,
interrupt assignments and device capabilities. Hardware that needs different
wiring or memory-map behaviour may still require glue code rather than merely
changing parameters. Logical-drive mappings and disk formats are common data;
a different floppy mechanism or format does not necessarily need a new driver.

These should have a BIOS driver ABI and direct dispatch, not intercept BDOS
calls to reach the hardware below BDOS. Reusing some RSX loader facilities is
an option to evaluate; adopting the RSX interception contract is not decided.
Bootstrap code must be able to load the initial driver set. Drivers needed
for active console/storage services remain resident. Optional devices can
release their memory only after their users, pending I/O and interrupts have
been dealt with. Dynamic loading alone does not save active-driver memory.

The current FDF.RSX remains unchanged. If other optional disk-format services
accumulate, consider evolving it into DISK.RSX. If its useful remaining role is
only mixed-sector support, reconsider placing that support in the common BIOS.
Neither restructuring is authorized for the present test cycle.
