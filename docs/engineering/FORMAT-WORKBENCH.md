# Format workbench and DUP

CONFIG.COM main-menu I copies an existing B:, C: or D: binding into a
transient working record. Use G first to choose a catalogue template.
A-P edit the displayed parameters; Q submits the complete record to the
BIOS; Ctrl-C discards the working copy. Invalid submissions leave the
editor open for correction. Decimal entry supports 16-bit fields; Enter
alone keeps the old value. R changes sector IDs by physical slot (1-32).
S changes individual sector lengths (codes 0-3 mean 128-1024 bytes).
The first individual-length edit seeds all slots from the uniform size.

This is an advanced parameter editor: dependent DPB fields are explicit,
not automatically calculated. For a mixed layout set maximum size (N),
individual lengths (S), and the sum of 128-byte records (B) consistently.
P=0 returns to uniform interpretation. Allocation counts and reserved
tracks must fit the resulting geometry. BIOS validation rejects unsupported
or inconsistent definitions before installing them.

After applying a definition, exit CONFIG, run DUP, choose A, select the
logical drive, and confirm formatting. DUP obtains the active BIOS binding;
it does not reconstruct the format from the catalogue name. Copy and Check
remain placeholders. A: and physical drive 0 are protected against formatting.
Changes survive utility exits/warm boots, but not a cold boot. Named-file
saving, capacity calculations, editable gaps, and an easier derived-parameter
mode remain future work. DISK.FDF is unchanged; no permanent compatibility
commitment is implied by using it during development.

The catalogue contains the 16 recovered MM built-ins followed by 96 DISK.FDF
entries. Pages contain 16 formats, with comma/< and period/> navigation.
Mixed lengths and extended side-order mappings use optional FDF.RSX:
`RSX LOAD FDF` before configuration; `RSX UNLOAD FDF` when finished.
Unloading detaches dependent non-system bindings before releasing the module.
Uniform conventional formats do not require the extension.

Unloaded TPA remains 54,273 bytes (53 KiB + 1). FDF currently allocates
768 bytes plus the 1,024-byte chain manager when loaded alone. The editor
and formatter consume no permanent resident allocation.

## Validation and remaining limits

The compiled validator accepts 107 of 112 catalogue definitions. Five source
records still fail consistency checks: Acorn, Eagle SS, Omikron Mapper II,
Pied Piper Executive, and Zenith H89. This is not a claim of complete catalogue
support. Eight-inch controller/track-budget support also remains unresolved.
The emulator backend currently constructs 6250-byte DD or 3125-byte SD tracks.

Tests execute relocated FDF mapping code, mixed-sector boundary cases,
320/384-entry BDOS directories, and BIOS vector contracts. The live editor test
creates a two-cylinder custom format through CONFIG, exits, formats using DUP,
and inspects IDs, sector lengths, erased data and untouched tracks in the DMK.
Separate live FDF tests cover Archives and mixed-size SUPER read/write/unload.
No cpmtools compatibility result is claimed yet. That future check must extract
the sector payloads from DMK into the image ordering described by a matching
diskdefs entry; DMK headers and gaps are not flat filesystem data.
