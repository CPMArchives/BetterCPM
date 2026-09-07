# Montezuma Micro DUP 2.01: working reverse engineering

Examined September 7, 2026 to understand formatting performance and the
repeatable initial verification error reported on track 79. This is a static
analysis of the original utility, not recovered original assembly source.
The initial investigation changed no BetterCP/M runtime code. The follow-up
implementation is recorded at the end of this note.

## Binary identity and extraction

The matching 2.01 binary is on both downloaded `CPMb231.dsk` and
`MMCPM231.DSK`. Both extractions are identical: 8,064 bytes, SHA-256
`71df2862c4a5f645353f9d07d8b97fc230737e712df5bd99609035e98d0aac31`.
The displayed version agrees with the user's screenshots.

The 2.32 distribution instead contains DUP 2.10 (8,064 bytes, SHA-256
`107b4be3a1684b3bbfc698ca2053876e097123ae86fbb0c5125f852aa479074e`).
The main format/check/controller region 0599h–097Ch is identical in these
two binaries; catalogue handling and some other bytes differ. The older
CPM222 image contains DUP 1.10, which was not the focus here.

The distribution images are retained under `~/CPM/montezuma-micro/images/`.
Extraction used 40 single-sided tracks, eighteen 256-byte sectors per track,
logical sector order 1,3,...,17,2,4,...,18, two reserved tracks, and 2,048-byte
allocation blocks. DUP's directory entry uses blocks 25–28 and 63 records.
All 720 source sectors passed ID and data CRC checks. Independent extraction
with cpmtools from the deinterleaved raw image produced an identical COM file.

A selected annotated disassembly and working binary are in
`third_party/montezuma/DUP-2.01-annotated.lst`; the working binary is in
`build/reverse-mm-dup/DUP-2.01.COM`.
The disassembler was adapted from the already installed z80pack
`z80core/simdis.c`. Inline screen strings and menu-vector data are identified
rather than treated as instructions. Addresses below assume ORG 0100h.

## What accounts for the different architecture

DUP includes its own transient controller driver at 07ABh–097Ch. Formatting
and checking call that code directly. It uses MM's BIOS DPB/physical-drive
records through IY/IX, but it does not reload formatting code from drive A
between tracks and does not route these operations through BDOS file I/O.
The DISK.FDF catalogue is loaded during initialization, not per track.

The driver saves the physical cylinder in each drive record at IX+9, restores
that value to the shared FDC track register on selection, and avoids a seek
when the head is already at the requested cylinder. An unknown position is
marked FFh and causes a restore. Read/write transfers use the Model 4's
controller/NMI facilities, ports F0h–F4h and E4h, and a temporary NMI vector
at 0066h. These are machine-specific routines, not portable CP/M services.

BetterCP/M currently reloads its format control overlay into shared workspace
from drive A on each track request. Verification overwrites that workspace.
This introduces system-disk accesses, drive switches and restores/seeks absent
from MM's inner formatting loop. This is a concrete architectural difference;
this investigation has not measured the separate contributions to elapsed time.

## Principal routine map

| Address | Meaning |
|---|---|
| 0134h | Initialize stack, obtain BIOS vectors, load catalogue |
| 0181h | Option A menu and selected drive/format setup |
| 01E1h | Format cylinders upwards, starting at zero |
| 0206h | Verify cylinders downwards, ending at zero |
| 0294h | Option B source/destination selection and compatibility checks |
| 0371h | Construct temporary destination DPB from source format |
| 038Bh | Copy one cylinder: format destination, read source, write, check |
| 0403h | Option C menu |
| 0459h | Check cylinders upwards |
| 0599h | Probe initial sector; readable media triggers destruction warning |
| 05DBh | Controller-error messages and retry/cancel prompt |
| 060Bh | Read cylinder into transient buffer, both sides when applicable |
| 063Fh | Write cylinder from transient buffer |
| 0673h | Construct and write a track stream, including both sides |
| 0744h | Expand a gap count/value pair |
| 076Dh | Common physical-sector check used by A, B and C |
| 07ABh | Raw operation dispatch: 1 read, 2 write, 3 format, 4 check |
| 07BBh | Check: seek and one read attempt |
| 07C1h | Ordinary read with retry/recovery sequence |
| 07DDh | Sector-read command and byte transfer |
| 0808h | F0h WRITE TRACK command |
| 0818h | Ordinary write with retry/recovery sequence |
| 0860h | Drive/side/density selection and positioning |
| 08CAh | Skip seek if requested cylinder equals current position |
| 08F7h | Invalidate position and restore/reseek |
| 0900h | Step-in/step-out recovery |
| 0934h | Install NMI handler and command-specific continuation |
| 0966h | NMI completion: return FDC status |
| 096Eh | Timing delay |
| 15AFh | Catalogue loader |

## Formatting and verification

Option A formats all cylinders first. The 0673h routine constructs a stream
at 5900h and formats side zero and, for DS formats, side one. It creates ID
fields, data marks, E5h data (complemented for inverted formats), controller
CRC tokens and FM/MFM gaps. At 06BAh it handles the MM SUPER special case:
sector ID 6 on a six-sector track uses 512 bytes rather than the normal
maximum sector size. This is a specific convention, not a general mixed-size
map like BetterCP/M's.

After the upward format pass, A decrements the cylinder number and invokes
the common checker from the highest cylinder down to zero. C invokes that
same checker in ascending cylinder order. B also invokes it after writing a
copied cylinder.

The checker at 076Dh reads every physical sector into 5900h, reusing the same
buffer. It checks the read status and counts failures. It does **not** compare
the payload with E5h or with the original copy buffer. The read continuation
masks FDC status with 9Ch (not-ready, record-not-found, CRC and lost-data bits).
Thus MM's successful verification means the sectors were readable without
those controller errors; it does not establish byte-for-byte agreement with
the intended content. BetterCP/M's format/copy comparison is stronger.

Check operation 4 bypasses the normal read retry ladder. A failed nonfatal
read increments the count and checking proceeds to the next sector. At the
end of a cylinder with errors, the caller displays the verification error
and waits for Enter or BREAK. Fatal conditions take the error/retry prompt.
The accumulated bad-sector count at 150Eh is one byte and can wrap at 256;
this is another detail BetterCP/M should not reproduce.

The not-blank test is a successful initial sector read, not a directory scan
for live files. A previously formatted but empty disk can therefore trigger
the warning shown in the user's screenshots.

## Copying and configuration

B saves the destination description, then builds a private destination DPB
at 151Ah from the source format. It keeps the source and destination physical
record pointers separately and alternates IX/IY while copying. The formatter
and raw driver consume this transient DPB. The actual destination BIOS DPB
is not overwritten by this mechanism, so there is no persistent format
assignment to restore on exit.

Each cylinder is formatted on the destination, read from the source into the
transient buffer, written to the destination, then checked for readability.
This differs from BetterCP/M's choice to read the source before destroying the
corresponding destination track and to compare the copied bytes afterwards.

## Track 79: what is and is not established

The observed failure is on the first cylinder of the reverse verification
pass. The single-attempt check path makes a first-read transient plausible,
but static analysis does not prove that explanation. The displayed message
omits side, sector ID and raw status. A counted error on that cylinder does
not, by itself, identify a permanently defective sector.

A useful next diagnostic is to record cylinder, side, sector and raw FDC
status at the return from 077Eh, then reread that same sector. Compare against
an independent inspection of the resulting image. This would distinguish a
badly written record from a transient first-read failure. It has not yet been
performed, and the original binary has not been patched in place.

## Implications for BetterCP/M

1. Remove repeated system-disk loading from the formatting inner loop. Keep
   the required code available for the duration of DUP, using transient memory
   or an optional disk extension rather than consuming permanent TPA.
2. Keep the shared utility portable. MM's direct ports and NMI code belong in
   a platform adapter behind a defined interface, not in the common DUP core.
3. Retain whole-sector reads, explicit byte comparisons, bounded errors and
   useful cylinder/side/sector diagnostics.
4. Retain the user's preferred immediate verify-after-write order. MM's speed
   does not depend on copying its separate reverse verification pass.
5. Consider transient per-operation format descriptions as an alternative to
   temporarily reconfiguring the destination's global BIOS binding.

The user's current MM measurement is about 29–30 seconds (18 format, 11
verify), with the repeated track-79 error; exclude the manual acknowledgement
pause. BetterCP/M's latest automated full-disk measurement was 341.10 seconds
with all 1,600 sectors passing. Emulator speed settings must be matched for
an exact timing ratio. The binary analysis nevertheless identifies substantial
avoidable work in BetterCP/M's current path.

## Follow-up implementation

DUP 1.13 / BIOS 1.9 (disk ABI 5) implements a private transient control-image
cache through an advertised platform entry. It copies the control image back
before each track format, sharing the existing validated formatter and error
paths. z80pack advertises no such capability and uses the ordinary operation.
The resident disk and control allocations remain 927 and 1,024 bytes; maximum
TPA remains 54,273 bytes. A full 800K run improved from 341.10 to 50.81 seconds,
with all 1,600 sectors independently verified. The byte-comparison policy and
immediate per-track verification are retained.
