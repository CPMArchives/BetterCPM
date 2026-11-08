# Numeric command PATH for BetterCP/M 1.1 and 1.1.1

## Release scope

Numeric PATH was introduced in 1.1. The unconditional current-DU search and
incremental `/A` / `/ADD` and `/D` / `/DEL` operations are assigned to **1.1.1**.
The operator contract below includes those 1.1.1 changes. In the 1.1 baseline,
the configured list alone controls unqualified lookup, and PATH supports
whole-list replacement and `/DEFAULT` without incremental editing.

## Using PATH

| Command | Effect |
|---|---|
| `PATH` | Display the active list. |
| `PATH . B0: B1: C0: A0:` | Replace the entire list in that order. |
| `PATH /A B3:` or `PATH /ADD B3:` | Append one entry to the configured list. |
| `PATH /D B3:` or `PATH /DEL B3:` | Delete one matching entry, preserving the order of the others. |
| `PATH B3: A0:` | Search the current DU first, then B3 and A0, skipping entries matching the current DU. |
| `A0:PATH /DEFAULT` | Reach the management utility directly and restore `. A0:`. |
| `PATH /H`, `PATH /HELP`, `PATH /VER` | Show the command syntax or component identification. |

The current drive/user is always searched first, independently of the list.
PATH displays and replaces only the configured additional locations. A single
dot follows the logged drive **and** user; it remains accepted for compatibility
and does not cause another local search. Fixed entries take a drive
A–P, a decimal user 0–31 and a colon. Input is case-insensitive. A leading zero
in a two-digit user is accepted and disappears on display. Whitespace between
entries is a space. The editor validates the complete replacement before
publishing. It reports invalid syntax, out-of-range users, duplicate entries
(including repeated dots) and overflow. The old list survives each rejection.
Incremental switches take exactly one location and precede it. An add rejects
an existing entry or a full list; a delete rejects an absent entry or deletion
of the final configured entry. Matching uses canonical numeric DU values, so
`B03:` matches `B3:`; dot matches only a stored dot, not a fixed DU that happens
to resolve to the caller. Editing the implicit default first stages `. A0:`.
All failures preserve the complete live record. A zero count still selects the
default, so there is no empty-list encoding. The current DU remains an
unconditional first search regardless of incremental edits.

Six entries accommodate the dynamic caller, a system DU, and four additional
tool or application areas. An installation can name a currently unmounted DU.

The shipped default reproduces 1.0 lookup. To restore a different preference
after power-off, put a line such as `A0:PATH . B0: A0:` in the startup
script invoked by the saved cold-start command. Dot passes through SUBMIT
literally. Direct console changes last until cold boot. A malformed startup
line gets the same diagnostic and leaves the preceding policy in force.

## Lookup and load

Navigation, core commands and CPXs run before unqualified transient search.
A force prefix (`:FOO` or `.FOO`) skips those stages as in 1.0. `B:FOO`,
`3:FOO` and `B3:FOO` use exact addressing, including after a force prefix.
After a local miss, missing implicit candidates advance in list order. A resolved duplicate of the
caller DU costs no second Open. Exhaustion prints the usual `?`.
A failed Open on a fixed FCB drive uses the existing preserved-context login
adapter to distinguish an unavailable location. `DRIVE UNAVAILABLE` stops
the search. An explicit miss retains the ordinary qualified-command behavior.

A successful Open selects the executable. Zero first-extent records produce
`EMPTY PROGRAM`. A returned non-EOF read error produces `READ ERROR` and a
record crossing the TPA boundary produces `FILE WILL NOT FIT`. The latter
two messages are printed by the reconstructed CCP, which can have been wholly
overwritten. Earlier matching files always win, including when their load
fails. Raw COM has no executable header or integrity checksum. Arbitrary
damaged instructions that read successfully cannot be identified by this
loader. Physical-media errors retain BDOS's existing Bad Sector interaction,
including the operator's choice to ignore or abort.

BDOS owns the logged drive. The FCB identifies the executable drive while the
CCP saves and temporarily selects the lookup user. On a match it copies the
opened FCB into protected loader storage, restores the caller before CPX
shutdown and passes the lookup user to the sequential reader. The gateway
restores the original user before entry or error return. The WBOOT abort
handler uses the existing saved user and armed flag for nonlocal I/O aborts.
GO/JUMP and ordinary transients use the same page-zero tail and default-FCB
builder. The original case of the tail, including leading spaces, is retained.

## Ownership and memory

| Option | Measured consequence or operational cost |
|---|---|
| Extend the contiguous 1.0 PDS downward | The checked ceiling is E101h. Removing 13 bytes crosses a complete-record boundary and loses 128 loadable bytes. Repartitioning the existing 192 bytes would reduce command history. |
| Reconstruct from a disk file | Authoritative live edits would require writable media or a retained dirty copy. Swapping disks could change policy at WBOOT and reloading would add directory traffic. |
| Fixed protected command-environment state | The assembled BDOS stack ends at E429h in the Model 4 layout and F029h in the full-RAM layout. Each has 17 bytes before the extension entry. A 13-byte list and a one-byte reader result fit with three bytes spare. |

The third design is implemented. These are named allocations enforced when the
resident image is assembled. The BDOS stack grows downwards. Its allocation
and the 192-byte HISTORY object keep their original sizes. The location of the
live list is a property of the selected layout. A cold image initializes it,
and WBOOT, CPX reconstruction, RSX moves and COM execution preserve it. No
field points into reclaimable memory. There is no backing file or disk write
when setting PATH.

| Field | Encoding |
|---|---|
| `LY_PATH+0` | Count 1–6. Zero selects the constant default. |
| `LY_PATH+1` through `+12` | Six pairs of one-byte FCB drive (1–16) and binary user (0–31). The dynamic entry is the pair 0,0. Only the count's entries are used. |
| `LY_LERR` | Separate protected loader-result byte, consumed and cleared after reentry. |

The profile-matched PATH.COM validates the BIOS WBOOT vector and the existing
BM version-1 extension descriptor with PATH capability bit 1 before writing.
The CCP and the utility share one layout contract. General BDOS file searches
and module loaders never consult these bytes. A future shell interface can
expose the same state. Fixed locations already contain the canonical result
that a future NDR resolver would provide. PATH neither grants nor restricts
access to any DU.

The CCP overlays POKE's staged bytes on the original-case line after POKE
accepts the command. It parses operands from the separate folded buffer.
The numeric CCP payload is 5,599 bytes in its existing 5,632-byte reclaimable
allocation. Its carrier occupies 6,623 bytes, or 6,645 with the checked
binding, within the 6,656-byte disk slot. Its reconstruction costs no extra
TPA. The baseline checked builder leaves 11 bytes in the slot. The concurrent 1.1 cpmsim builder omits the 128-byte uninitialized stack from the disk payload, producing a 6,517-byte carrier with the same live allocation.

## Qualification

The public-prompt tests ran on disposable images. The merged cpmsim
default-full-RAM build passed its 23 distribution checks and the 32-command
PATH suite. The Model II builder installs the profile-matched PATH.COM in A0.
The media check extracts it with cpmtools and compares every CP/M record
with the selected build. On 7 November 2026 the interactive trs80gp 2.5.8
run cold-booted a copy of the normal System disk (SHA-256
`d8e20a91e8277090ffbb095fad96b9d2c653af960791d9caa69f154e75a7110d`).
The fixture disk in B held the submitted job and test programs. Final 1.1
media are rechecked at release.

| Runtime | Observed |
|---|---|
| cpmsim, 1.1 full RAM | 32 prompt commands plus the submitted sequence. First match, later match, explicit miss, force prefix, resident DIR precedence, bad input with old list preserved, direct recovery, dynamic DU and cross-DU tail/FCB probe passed. Loaded 57,344 bytes from B3. Rejected 57,472. Bad Sector on an unmounted drive followed by Ctrl-C returned to A3 and preserved PATH. |
| cpmsim, 1.0-layout compatibility build | Same suite passed. Largest test executed 54,272 bytes. The next 128-byte record was rejected. |
| TRS-80 Model 4 in trs80gp | Cold-start SUBMIT set the path. At A5 the A3 image won. A 54,272-byte COM executed, the 54,400-byte first candidate reported FILE WILL NOT FIT, the following submitted command again ran the A3 image. XSUB's Function 10 probe printed INPUT OK. A0:WHICH selected the other image and A0:PATH displayed the original order. |
| TRS-80 Model II in trs80gp | Interactive PATH at A0 displayed `. A0:`. With `B3: . B0:` set, the submitted job at A5 ran B3:WHICH and the 57,344-byte B3 program. A 57,472-byte first match produced `FILE WILL NOT FIT`. The next command ran B3:WHICH again. XSUB printed `INPUT OK`, explicit B0:WHICH ran the second copy, and A0:PATH displayed the configured order. After setting an A9-only list, A0:PATH /DEFAULT restored `. A0:`. The job printed `PACKAGED PATH DONE` and returned to A5. |

The assembled recording provider also checks the exact sequence of Open calls
for fixed-first and dynamic-first duplicates and a six-entry list. The
protected-loader provider tests returned read errors 02h and FFh, oversize
rejection, caller-user restoration and CPX shutdown. Native ZSM4/LINK and
cross-builds agreed on the CCP (5,599 bytes), BDOS image (3,451 bytes) and
extension services (424 bytes) in the conventional layout.

For an emulator timing sample, 11 commands per case were run on the checked
cpmsim candidate with the same backing images. Median host wall times from
sending the command through the next prompt include console output and, for a
successful COM, execution and WBOOT. The first and last hit used the same A0
executable. These figures measure image-backed emulation. Physical floppy
seek/rotation times remain unmeasured.

| Case | Open calls | Median ms |
|---|---:|---:|
| First of four | 1 | 7.66 |
| Last of four | 4 | 9.04 |
| Complete four-entry miss | 4 | 2.60 |
| Complete miss, dot and A0 both resolve to A0 | 1 | 1.12 |
| P31 unavailable | 1 plus login check | 1.08 |

The implementation uses sequential Open calls and keeps no directory cache.

Run the guest tests with `tools/qualify_numeric_path.py` on a prepared cpmsim
disk set and `tools/qualify_numeric_path_trs80.py` on the matching TRS-80
build. Both harnesses use a fresh output directory. With `--prepare-only`,
the TRS-80 harness prepares media for an interactive run. On the Model II,
mount `Model-II-PATH.imd` in drive 0 and `Model-II-PATH-Fixtures.imd` in
drive 1. The former starts as a byte-for-byte copy of the normal System disk.
At A0 enter `B0:SUBMIT B:PTEST`. Drive B supplies the script, test programs
and BATCHIO.RSX. The packaged A0:PATH manages the list throughout the run.

Additional control runs found two existing harness failures on both the base
tree and the PATH branch. The old system-console stub stops on an unmodeled IN
instruction, and NOAH's help-layout test expects the former help footer. The
historical CCP acquisition script also requires local September disk fixtures.
The public-prompt, loader and batch results above were obtained independently.

## 1.1.1 current-DU precedence correction — 8 November 2026

The current DU is now an unconditional first candidate, even when the list
contains only another DU such as `D0:`. This supersedes the earlier policy
that let a fixed entry precede or exclude the caller. A local match wins even
if loading it fails; explicit qualifiers still search exactly one location.
Existing dot entries and fixed entries resolving to the caller are skipped
after the local attempt. The list encoding, default and six-entry limit are
unchanged. The historical qualification and timing observations above describe
the earlier implementation; they do not establish the revised lookup order.

The revised assembled recording-provider suite passes local-only hits with a
D0-only list, local precedence over fixed-first lists, local misses followed
by ordered fallback, both force prefixes, exact qualifiers, duplicate caller
entries and caller restoration. The CCP parsing/dispatch and protected-loader
EOF/error suites also pass. The CCP grows by four bytes to 5,603 bytes within
the unchanged 5,632-byte allocation; the legacy carrier is 6,627 bytes.
Public-prompt harness expectations are updated; new release media still need
their normal qualification.

Incremental-edit qualification executes the assembled PATH.COM with a recording
BDOS. It covers all four edit switches, lowercase forms, implicit-default edits,
first/middle/last deletion, canonical matching, duplicates, full capacity,
missing entries, final-entry rejection, malformed options/operands, whole-list
replacement, `/DEFAULT`, `/H` and `/VER`. Rejected edits preserve all 13 live
bytes. Run `python3 tools/build_path.py` followed by
`python3 tools/test_path_edits.py`.
