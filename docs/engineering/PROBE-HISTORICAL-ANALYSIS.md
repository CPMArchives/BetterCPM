# PROBE.COM Historical Analysis

## Artifact

PROBE is a CP/M system and disk-parameter inspection utility by Paul M. Sittler. The supplied documentation identifies the program as PROBE.C Version 1 Revision 01, dated 2 September 1984, copyright 1984, released for non-commercial use.

The examined PROBE.LBR contains:

- PROBE.COM — 132 CP/M 128-byte records (16,896 bytes)
- PROBE.DOC — 20 CP/M 128-byte records (2,560 bytes)

The original C source is not present in this library.

## Historical purpose

The documentation says PROBE was written in C to help decode disk formats on different CP/M machines for portability work. The author describes transferring PROBE to a target CP/M system, obtaining its disk/system parameters, and using the results when constructing support for foreign floppy formats.

The documentation also describes a "Uniform(tm)-like" utility that changed disk parameter information so a system could access multiple foreign floppy formats. This makes PROBE directly relevant to BetterCP/M's configurable disk-format research, even though PROBE itself is primarily an inspection utility.

## Reported information

PROBE reports or inspects information including:

- CP/M or MP/M version
- I/O byte where applicable
- CCP, BDOS, and BIOS addresses
- BIOS jump table
- CP/M Plus extended BIOS calls
- MP/M XIOS calls
- selected-drive DPH and DPB information
- allocation block/group size
- total disk size
- directory entry count and directory storage
- usable disk space
- disk allocation vector

The documentation warns that probing utilities may not produce accurate results on every CP/M implementation. Results therefore describe what the utility infers through expected CP/M structures and interfaces, not an infallible physical-media measurement.

## Reconstructed operating method

Analysis of the distributed PROBE.COM establishes the important disk-inspection path.

### Version

PROBE uses BDOS function 12 (Return Version Number) to identify the operating-system version and distinguish relevant CP/M/MP/M paths.

### BIOS location

PROBE uses the low-memory warm-boot vector to locate the BIOS jump-table area. It can then enumerate or invoke BIOS entries through the standard jump-table layout.

### DPH discovery

For the selected drive, PROBE invokes BIOS SELDSK (BIOS function 9). The returned HL value is treated as the Disk Parameter Header address.

This is preferable to scanning memory for a structure: PROBE obtains the DPH through the BIOS interface that owns it.

### DPB discovery

PROBE selects the desired disk through the normal CP/M environment and uses BDOS function 31 (Get Disk Parameter Address). HL supplies the DPB address.

The DPH also contains a DPB pointer, giving PROBE related views of the same selected-drive state.

Conceptually:

    BIOS SELDSK  -> DPH
    BDOS 31      -> DPB

### DPB interpretation

PROBE interprets the normal CP/M 2.x DPB fields:

- SPT
- BSH
- BLM
- EXM
- DSM
- DRM
- AL0
- AL1
- CKS
- OFF

It prints raw parameter data and derives higher-level quantities such as allocation-block size, disk capacity, directory capacity, directory storage, and usable storage.

### DPH interpretation

PROBE interprets standard DPH pointers including:

- XLT — sector translation table
- DIRBUF — directory buffer
- DPB — disk parameter block
- CSV — check vector
- ALV — allocation vector

It also examines the allocation vector.

## Important limitation: XLT is not physical interleave

PROBE can identify the DPH XLT pointer, but this is CP/M BIOS logical-sector translation. It does not establish the physical rotational interleave of sector IDs on the medium.

No evidence found in the examined binary indicates that PROBE interrogates the floppy controller or physically scans sector IDs to determine rotational order.

Therefore:

    DPH.XLT = CP/M logical-sector translation
    DPH.XLT != necessarily physical sector interleave

This distinction is important to BetterCP/M's disk-format model and to interpretation of historical utilities named "SKEW".

## Implications for BetterCP/M tools

PROBE is a useful historical predecessor to proposed BIOSINFO/DISKINFO-style tools.

A modern utility can follow the same non-invasive discovery chain:

    BDOS 12          -> OS version
    low-memory vector -> BIOS location
    BIOS jump table   -> BIOS entries
    BIOS SELDSK       -> DPH
    BDOS 31           -> DPB
    DPH               -> XLT, DIRBUF, DPB, CSV, ALV

Potential improvements over PROBE for BetterCP/M tooling include:

- dump the actual XLT table when nonzero, not merely its address;
- clearly label XLT as logical translation rather than physical interleave;
- report provenance/assumptions when structures are inferred;
- separate CP/M filesystem information from physical-media information;
- avoid claiming physical properties that cannot be observed through the CP/M interfaces.

## Relationship to disk-format research

PROBE is valuable for recovering the logical CP/M organization of a running system. It cannot by itself provide all information needed for a canonical physical disk definition.

For physical properties such as FM/MFM recording, physical sector IDs and sizes, track ordering, and rotational interleave, additional evidence is required from BIOS/controller information, physical disk analysis, OEM documentation, or disk images that preserve the relevant metadata.

The missing historical SKEW.COM remains worth investigating specifically to determine whether it merely exposes DPH/XLT translation or attempts to infer physical sector ordering.
