# BetterCP/M 1.1 User's Guide

License: original prose/illustrations are CC BY 4.0; original reusable code examples are GPL-2.0-or-later. Third-party material retains its own terms. See [licensing and example boundaries](../LICENSING.md).

This guide assumes that you can operate a computer and are familiar with CP/M drives, user areas, 8.3 filenames and COM programs. Part I concentrates on useful BetterCP/M tasks. Part II explains the system behind those tasks. Look up complete syntax, switches and diagnostics in the separate [Command and Utilities Reference](Command-and-Utilities-Reference.md).

This edition describes BetterCP/M 1.1 for patched cpmsim, TRS-80 Model 4 and the 64 KiB Model II under trs80gp 2.5.8. Use matching System and Utilities downloads from the same release. Package identity and exact source/image hashes come from RELEASE.json and the release index. The prior 1.0 and 1.0.1 downloads and locks remain unchanged. See the [1.1 scope](../releases/1.1-SCOPE-AND-ACCEPTANCE.md) and [platform boundaries](../platform/SUPPORT-1.1.md); engineering receipts are not acceptance of differently hashed final media.

## 1.1 operating profile

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

BetterCP/M 1.1 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. TYPE/TED/HELP have not been migrated to TCAP 2.0, and HELP is not shipped. TYPE, TED and HELP are examples, not the complete affected-utility set; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md).

Numeric PATH has up to six ordered drive/user entries, default `. A0:`. `.` tracks the caller. Use `PATH /H`, `/HELP` or `/VER`; `A0:PATH /DEFAULT` recovers the default. PATH is volatile: use the existing startup script to apply a preferred list after cold boot. Named directories and scripting are outside 1.1.

## Contents

- [Part I — Using BetterCP/M](#part-i)
  - [1. Start with BetterCP/M's distinctives](#chapter-1)
  - [2. Choose and prepare a working environment](#chapter-2)
  - [3. Boot and check your first session](#chapter-3)
  - [4. Find and manage files](#chapter-4)
  - [5. Edit, recall and run commands](#chapter-5)
  - [6. Automate a repeated task](#chapter-6)
  - [7. Inspect, change and save configuration](#chapter-7)
  - [8. Manage extensions and program memory](#chapter-8)
  - [9. Match a terminal personality to an application](#chapter-9)
  - [10. Back up and maintain disks](#chapter-10)
  - [11. Read the clock](#chapter-11)
  - [12. Recover from common problems](#chapter-12)
- [Part II — Understanding BetterCP/M](#part-ii)
  - [13. Organization](#understanding-organization)
  - [14. Memory and Execution](#understanding-memory-and-execution)
  - [15. Command Environment](#understanding-command-environment)
  - [16. Files/Drives/Disks](#understanding-files-drives-disks)
  - [17. Console/Terminals/I/O](#understanding-console-terminals-io)
  - [18. Extensions](#understanding-extensions)
  - [19. Portability](#understanding-portability)
- [Appendices](#appendices): [task locator](#appendix-a), [editing keys](#appendix-b), [keyboard conventions](#appendix-c), [file notation](#appendix-d), [compatibility](#appendix-e), [messages](#appendix-f), [glossary](#appendix-g), [further documentation](#appendix-h).

<a id="part-i"></a>

## Part I — Using BetterCP/M

<a id="chapter-1"></a>

### Chapter 1 — Start with BetterCP/M's distinctives

BetterCP/M preserves the CP/M 2.2 application environment while improving everyday command use and making configuration and extensions explicit. Existing CP/M habits remain useful; the following differences are worth learning first.

| When you want to… | BetterCP/M facility | Start here |
| --- | --- | --- |
| Correct or reuse a command | Line editing and persistent command history | [Chapter 5](#chapter-5) |
| Work across users and drives | DU locations, selectors and file attributes | [Chapter 4](#chapter-4) |
| Choose the fuller version of a familiar command | Explicit transient invocation, such as `:DIR` | [Chapter 5](#chapter-5) |
| Change disk or startup settings | CONFIG with distinct active and saved state | [Chapter 7](#chapter-7) |
| Add commands or services | Loadable CPXs and RSXs | [Chapter 8](#chapter-8) |
| Run full-screen applications | A screen backend and selected terminal personality | [Chapter 9](#chapter-9) |
| Inspect or edit format definitions | FDB catalogue workbench | [Chapter 10](#chapter-10) |

Ordinary CP/M programs use the familiar BDOS/BIOS interfaces. Programs that patch private OS addresses, assume a particular terminal or address hardware directly may require adaptation. [Appendix E](#appendix-e) describes the compatibility boundary and how to investigate a problem.

The four-manual collection consists of this User's Guide, the [Command and Utilities Reference](Command-and-Utilities-Reference.md), the [Programmer's Guide](Programmers-Guide.md) covering applications/extensions/APIs, and the [Practical Porting Guide](Practical-Porting-Guide.md). Existing programmer and architecture references remain available behind those guides; the [coverage/evidence ledger](../programmers/REFERENCE-STATUS.md) records their stability and expansion boundaries. The 1.1 platform and feature boundaries are recorded above.

<a id="chapter-2"></a>

### Chapter 2 — Choose and prepare a working environment

Choose the System download for patched z80pack/cpmsim or Model 4 under trs80gp. Read the corresponding [cpmsim](../platform/CPMSIM-INSTALLATION.md) or [Model 4](../platform/MODEL4-INSTALLATION.md) installation guide before mounting media. Stock upstream cpmsim does not supply the required interfaces; use the pinned offline reconstruction inputs supplied with the release. Physical Model 4 media transfer and other machines are outside these emulator qualification receipts.

Keep original images unchanged and run writable copies. System and Utilities are independent downloads. A useful combined arrangement is:

| Logical drive | Usual purpose |
| --- | --- |
| A: | System, support carriers and startup script |
| B: | Primary Utilities |
| C: | Companion Utilities: NOAH, PATCH and COMPARE |
| D: | Writable work files |

Without Utilities, B/C can hold compatible work media. Follow the platform guide for actual physical attachments and bindings; a logical letter is not a format conversion. Model 4's System uses BCPM780, while its ordinary data/work media use 800K DATA. cpmsim release media use CCS 332K.

The Source download supplies the matching offline reconstruction and native build material. An automatic GitHub source archive is not a substitute for the packaged dependency tar. The dedicated Documentation download supplies the reconciled manuals; old instructions embedded in the locked five archives remain historical snapshots.

<a id="chapter-3"></a>

### Chapter 3 — Boot and check your first session

Start the platform using its installation guide. At `A0>`, the letter is the current drive and the decimal number is the current user, including zero. Run these checks before changing configuration:

```text
VER
VER /V
DIR
CONFIG /SHOW
RSX LIST
STAT MEM
```

cpmsim startup displays the banner without loading a personality or clock. Model 4 startup loads integrated ADM3A, clears the display and shows the banner. Model II starts with its basic console; its supplied STARTUP.SUB may be run explicitly. The banner script invokes `:VER /BANNER`. None of these starts a clock provider or P2DOS.

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

If Utilities are mounted normally, `B0:DUMP A0:README.TXT` inspects a System file without changing the working drive. For a first ordinary text display, use `TYPE A0:README.TXT`. Consult the [command reference](Command-and-Utilities-Reference.md) for exact options.

Save files and finish disk operations before stopping the emulator. cpmsim's `BYE` asks before exiting; `BYE /Y` exits immediately. Model 4 uses its emulator controls. Ctrl-C performs a warm boot/command return where supported; it is not a cold machine reset or a general save command.

<a id="chapter-4"></a>

### Chapter 4 — Find and manage files

Select a drive/user together with `D3:`, or inspect another location without selecting it. BetterCP/M supports users 0–31; the locked BIOS configures four logical drives A–D. Some parsers recognize A–P without making unconfigured drives available.

```text
DIR D3:*.TXT
:DIR /WHEREIS ED.COM
:DIR /P /A D3:*.TXT
COPY A0:README.TXT D0:
```

Resident DIR handles ordinary listings. Transient `:DIR` adds file-location search, sorting, sizes and paging. `/WHEREIS` with an unqualified filename searches configured accessible drives and users 0–31. An unreadable location can make that search incomplete; zero matches then does not prove absence everywhere.

Use a selector when you deliberately need several users, for example `DIR B[-]:*.COM` or `DIR B[3-5]:*.ASM`. Attribute predicates such as `[$RO]` or `[$ARC+!$SYS]` select files; they do not automatically override protection. A command must explicitly support that grammar. Compression tools, ED, DUMP and extension managers have different operand rules. PIP accepts expanded source DU selectors for copying into one destination DU; its trailing bracket parameters have their historical meanings.

For work files, inspect before moving, renaming or erasing:

```text
DIR D0:*.BAK
REN D0:REPORT.TXT REPORT.BAK
MOVE D0:REPORT.BAK D3:
```

REN keeps files in their original DU; its template cannot select a new location. MOVE creates and closes the destination before deleting the source and refuses an existing destination. It is not an all-or-nothing multi-file transaction. COPY retains the source. Use transient `:COPY` for its batch/verification/replacement facilities rather than passing unsupported switches to resident COPY. See [COPY](Command-and-Utilities-Reference.md#copy-transient), [MOVE](Command-and-Utilities-Reference.md#move-resident) and [ERA](Command-and-Utilities-Reference.md#era-transient) before performing a bulk operation.

To copy using historical destination-first syntax, use [PIP](Command-and-Utilities-Reference.md#pip), for example `PIP D:=A:*.COM`. `PIP A4:=B[-]:*.COM` copies from all B user areas into A4. It checks up to 64 matched files before copying and rejects distinct sources with the same destination filename; see [PIP selector and collision rules](Command-and-Utilities-Reference.md#expanded-source-du-selectors). Its bracket parameters are not COPY's attribute syntax. Use STAT to distinguish allocation space from file record length and directory-entry capacity.

#### Named directories (1.2 development)

Load `NDR.RSX` with `RSX LOAD NDR`, then use `NDR COMMANDS A0:` and
`NDR SOURCE B2:` to assign names. Up to 32 names of one to eight letters or
digits are supported. Names ignore case; numeric DU spellings remain reserved.
`SOURCE:` selects B2; `TYPE SOURCE:NOTE.TXT` reads a named file location.
The prompt becomes `A0 [COMMANDS]> `, including the space after `>`.
Names alias existing drive/user areas; they do not create directories.

`NDR` lists eight entries down each column, up to four columns, with four
spaces between 13-character fields, followed by the in-use count.
Delete with `NDR /DEL SOURCE` before reassigning an existing name. `/CLEAR`
removes the live set. `NDR /SAVE MYNAMES` creates MYNAMES.NDR; it refuses an
existing file. `NDR /LOAD MYNAMES` replaces the live set only after validating
it. Names survive warm boot while the provider is loaded. Unload discards them;
save first. `NDR /DEFAULT A0:NDR.RSX` embeds the current set in that existing
provider for its next fresh load. Then `RSX LOAD NDR` alone restores the names
after cold boot. Alternatively follow the load with `NDR /LOAD A0:MYNAMES`
to restore a separate set. The shipped provider defaults to an empty table.

PATH accepts names as input and stores their numeric locations immediately:
`PATH $$ COMMANDS: SOURCE:`. Later name changes do not retarget PATH.
See [NDR](Command-and-Utilities-Reference.md#ndr) for syntax and limitations.

<a id="chapter-5"></a>

### Chapter 5 — Edit, recall and run commands

Edit the current command before pressing Return. Ctrl-S/D moves left/right; Ctrl-H or DEL removes the preceding character; Ctrl-G deletes at the cursor. Recall older commands with Ctrl-K and move forward with Ctrl-J. History survives ordinary warm boot and is cleared by cold boot. [Appendix B](#appendix-b) contains the full key card and platform qualifications.

An ordinary name goes through the command environment. To select a disk program explicitly, prefix its name with `:` or `.`:

```text
DIR D0:
:DIR /P D0:
:VER /BANNER
```

The first uses resident DIR if RCP is loaded. The second selects DIR.COM. Unsupported resident options do not automatically launch a transient replacement. In particular, select `:COPY` for `/B` and `:VER` for `/BANNER`.

Unqualified transients are searched in the current DU, then A0. A qualified invocation such as `B0:DUMP` searches only B0. The program's file operands retain their own defaults; finding a program in A0 does not move your work there. Carrier loading by CPX/RSX is a different mechanism and uses A0.

For 1.1, see [Numeric PATH commands and cold-start setup](../engineering/Numeric-PATH-1.1.md#using-path).

For help, use the command's documented query. BetterCP/M-owned utilities generally supply `/H`, `/HELP` and `/VER`; ZSM4 and LINK retain their original interfaces. Quoted SEARCH patterns and PIP bracket strings remain data even when they contain apparent query tokens. Read the [query conventions](Command-and-Utilities-Reference.md#query-conventions) instead of assuming every program parses switches alike.

<a id="chapter-6"></a>

### Chapter 6 — Automate a repeated task

Create a plain text SUB file with ED or TED. A small `D0:LISTING.SUB` can contain:

```text
DIR $1
STAT
```

Run `SUBMIT D0:LISTING D0:*.TXT`. SUBMIT substitutes its parameters and queues the resulting commands. Use explicit transient names and supported noninteractive options when a script requires them; an interactive question can still stop unattended progress. The [SUBMIT entry](Command-and-Utilities-Reference.md#submit) defines parameter substitution, limits and cancellation.

Keep A0 writable. SUBMIT and XSUB use `A0:$$$.SUB` even when the script lives elsewhere and commands change the working DU. Do not treat a same-named file in another user as the authoritative queue. Ordinary command/program warm returns are part of batch execution, not necessarily cancellation.

XSUB feeds submitted lines to compatible programs using buffered console input; it is not a universal keyboard emulator. With Utilities in B, use `B0:XSUB B0:` so its matching BATCHIO.RSX is loaded from B0. Keep matching R3PACK.RSX and R3CACHE.RSX on System A0. Help/version queries do not activate it. The copy-to-A0 workaround in the 1.0 erratum applies only to those older locked binaries.

The supplied STARTUP.SUB is itself a practical batch example. Keep an unchanged copy before customizing it, especially if you use `SUBMIT STARTUP` to restore the Model 4 console after unloading modules. Extended flow-control scripting remains outside 1.1.

<a id="chapter-7"></a>

### Chapter 7 — Inspect, change and save configuration

Begin with `CONFIG /SHOW`. Record active drive bindings and saved startup settings before editing. Close files before changing disk configuration. CONFIG's menu separates startup command, cold-boot IOBYTE, physical drive definitions, logical formats and saving.

Changing a runtime binding does not format a disk. Changing a catalogue does not reinterpret an existing active binding. A setting can work for the session without becoming the next cold-boot default. CONFIG distinguishes current state and pending cold-boot settings; choose the save operation matching your intention rather than assuming every menu edit is already on disk.

For an actual disk task:

1. Confirm the physical drive's track/side capabilities and the inserted media format.
2. Select the logical drive, physical selector and named format through CONFIG.
3. Inspect the resulting binding and read the intended directory.
4. Perform the task on writable work media.
5. Save defaults only if that is the configuration you want at cold boot.

For Model 4 System installation, use the exact [named BCPM780 procedure](../platform/MODEL4-SHIPPED-INSTALLATION.txt), also described in the [SYSGEN entry](Command-and-Utilities-Reference.md#sysgen). Do not substitute historical 790K or an ordinary 800K Work disk.

Startup-script edits, extension load/unload operations, terminal selection and clock-provider loading have their own tools and lifetimes. CONFIG does not manage all of them. Use the [complete CONFIG reference](Command-and-Utilities-Reference.md#config) for menu/input controls, command-line forms, save choices and recovery.

<a id="chapter-8"></a>

### Chapter 8 — Manage extensions and program memory

Inspect before changing the environment:

```text
CPX LIST
RSX LIST
STAT MEM
```

CPXs add commands at the prompt; RSXs supply services while applications run. Place compatible normal CPX/RSX carriers in A0 before loading. Keep configured CPXs there for reconstruction after transient execution. Keep the matching R3PACK.RSX manager container in A0; it is support material, not a module to load manually.

CPX has an ordered four-name profile including RCP. A configured name can remain listed when its carrier is missing or rejected, so LIST alone does not prove its commands loaded. Restore standard commands with `CPX LOAD RCP` if necessary. Removing RCP is allowed and removes its commands; it does not create missing transient files. CLS.COM, USER.COM and MOVE.COM are not selected System Disk contents.

Loaded RSXs reduce protected program headroom. CPX/CCP command code is reclaimable for a transient and is reconstructed on warm boot; unloading a CPX therefore does not reclaim TPA in the same way as unloading an RSX. Read STAT MEM's maximum COM size separately from current command-memory occupancy.

Interactive FDB needs the unloaded 53K environment. From normal Model 4 startup, use:

```text
RSX UNLOAD ADM3A
FDB
```

After quitting FDB, use the unmodified `SUBMIT STARTUP` on Model 4 or cold boot to restore its supplied console. Unload any additional optional RSXs if needed. FDB queries do not need the interactive workbench allocation. Keep FDB.COM 1.01 with its matching FDBVIEW.OVL; component revisions are independent of the package version.

<a id="chapter-9"></a>
<a id="host-terminal-size-and-recovery"></a>

### Chapter 9 — Match a terminal personality to an application

Select the personality expected by the application, then configure the application for that protocol. The supplied 1.1 modules combine personality and renderer. Only one active personality is supported; unload it before selecting another.

| Environment | Backend | Initial personality |
| --- | --- | --- |
| Model 4 startup | Integrated renderer | ADM3A |
| cpmsim startup | Basic console | None |
| Model II startup | Basic console | None |

To use ANSI on normal Model 4 startup:

```text
RSX UNLOAD ADM3A
RSX LOAD ANSI
RSX LIST
```

On cpmsim and Model II, load ANSI directly; no ANSISCRN or M2SCRN prerequisite is required by the integrated personality. Keep a cpmsim host terminal at least 80 columns by 24 rows. The launcher refuses undersized windows. After a resize, exit and restart applications to redraw. Use VT52 if the application is installed for VT52. Visual, keyboard and audible checks remain distinct observations.

TED requires an 80-by-24 backend and ANSI personality and does not load them itself. Use its [reference entry](Command-and-Utilities-Reference.md#ted) before starting. ANSI provides a defined VT100-compatible subset, not every VT100 facility. A general terminal-capability database and arbitrary application hardware access are outside this mechanism.

If output is misplaced, check the application protocol, selected personality and host dimensions. Standalone SCRN/SCX clients need their documented screen backend in addition to the integrated console personality. Unload an optional backend only after its clients have exited.

<a id="chapter-10"></a>
<a id="editing-disk-format-definitions"></a>

### Chapter 10 — Back up and maintain disks

Choose the operation by what you need to preserve:

| Task | Tool and boundary |
| --- | --- |
| Copy selected files | COPY or PIP; source files remain |
| Move work files | MOVE; source deletion follows successful copy |
| Copy/check/format a disk | DUP; assigned geometry and backend capabilities apply |
| Export/install an OS package | SYSGEN; reserved system area and saved configuration |
| Compose SYSTEM.SYS from assembled products | SYSBUILD in the source/build workflow |
| Inspect/edit a format catalogue | FDB; catalogue changes are not formatting or installation |

Back up source images before formatting or installation. DUP FORMAT destroys the destination contents. DUP copy needs two drives; it does not implement repeated source/destination swapping in one drive. Physical drive 0 is protected from destination formatting/copying. DUP checks are not a general filesystem repair tool. Read the [DUP entry](Command-and-Utilities-Reference.md#dup) for actual verification and error scope.

SYSGEN can save an installed system to a named package, such as `SYSGEN A: D:BACKUP.SYS`. That package contains the installed system and saved configuration, not unsaved live settings or ordinary file backups. Installing a validated package writes the system area while preserving ordinary destination files when the qualified compatible-layout procedure is followed.

For Model 4, temporarily replace normal B: Utilities with the prepared System-format target and follow [the installation guide](../platform/MODEL4-INSTALLATION.md). A release System copy has the BCPM780 reserved area; an 800K DATA Work disk does not. Fully quit/remount and cold boot the destination before validating it.

FDB 1.01 supplies the grouped main menu and matching viewer. Follow the displayed choices and use Q or BREAK to exit. Model II supplies only its qualified BCM2SS catalogue; the other targets retain their catalogue and separately bounded supplement. Editing a catalogue, applying a drive binding, formatting media and saving cold defaults are separate operations.

Catalogue admission means structural validity, not successful interchange on every physical controller. The release-media layouts are CCS 332K, Model 4 800K DATA and BetterCP/M 780K System. Optional historical MMI012 790K is different from BCPM780. Preserve format provenance and rights notices when redistributing catalogues.

<a id="chapter-11"></a>

### Chapter 11 — Read the clock

Startup loads no clock provider. On cpmsim, load ZPRTC; on a Model 4 with suitable FreHD hardware/emulation, load FREHDCLK. Then query TIME:

```text
RSX LOAD ZPRTC
TIME /PROVIDER
TIME
```

Use FREHDCLK instead of ZPRTC on the appropriate Model 4 setup. Both supplied providers are read-only: they obtain time but cannot change the underlying clock. Correct the host/hardware clock through its own facilities. TIME's implemented `/SET` request is not proof that either supplied provider can set it.

For an application requiring P2DOS-compatible Functions 200/201, load the native provider first, then `RSX LOAD P2DOS`. P2DOS.RSX is supplied in A0 on both System disks but is optional to load. It does not create a hardware clock or make a read-only provider writable. The 104/105 adapters are deferred.

If TIME fails, distinguish no loaded provider, unsupported SET and a failed/invalid hardware sample. See [TIME](Command-and-Utilities-Reference.md#time) and [RSX](Command-and-Utilities-Reference.md#rsx). Clocks do not imply filesystem timestamp support in 1.0.

<a id="chapter-12"></a>

### Chapter 12 — Recover from common problems

Start with a nonmutating inspection. Preserve original media, exact error text, the command, working DU, versions and loaded modules before experimenting.

| Symptom | First checks | Next reference |
| --- | --- | --- |
| `?` or a missing command | Program name, current DU/A0, qualified program location, RCP availability | [Command lookup](#understanding-command-environment), [shared messages](Command-and-Utilities-Reference.md#system-messages) |
| Resident option rejected | Use the explicitly selected transient if its file is supplied | [Command reference](Command-and-Utilities-Reference.md) |
| `CPX?` on return | CPX profile versus actual A0 carrier; remove rejected optional name or replace its matched file | [CPX](Command-and-Utilities-Reference.md#cpx) |
| A large program refuses to start | STAT MEM and protected RSX allocations | [Chapter 8](#chapter-8) |
| FDB fails at normal Model 4 startup | Matching viewer; unload ADM3A and any separately loaded screen backend; restore afterward | [FDB](Command-and-Utilities-Reference.md#fdb) |
| Full-screen output is wrong | Application terminal choice, personality/backend order, host dimensions | [Chapter 9](#chapter-9) |
| Disk unavailable or wrong directory | Attachment, physical capabilities, logical binding, inserted format | [CONFIG](Command-and-Utilities-Reference.md#config) |
| Disk full despite free data space | Directory-entry limit as well as allocation blocks | [STAT](Command-and-Utilities-Reference.md#stat) |
| A setting vanishes at cold boot | Active versus saved state and the selected save operation | [Chapter 7](#chapter-7) |
| XSUB reports Xsub Load Error | Matching BATCHIO.RSX must be copied from Utilities to writable A0 | [XSUB](Command-and-Utilities-Reference.md#xsub) |
| Clock unavailable | Native provider first, hardware/emulator availability | [TIME](Command-and-Utilities-Reference.md#time) |

Complete open-file work before media changes. There is no background media-change detector that makes arbitrary replacement safe. Reconfiguration, aliases and cached disk context require the documented reset rules. A software read-only state is different from hardware write protection.

For interrupted file publication, retain reported work/backup files until you identify the complete copy. A successful earlier item in a multi-file operation is not automatically rolled back. Read the specific command's recovery rules before rerunning with the same names.

Cold boot a known preserved System image if the session is unusable. Restore A0 carriers and an unmodified STARTUP.SUB when reconstruction or console startup fails. The known malformed-history audit condition and other deferred dispositions remain documented release limitations; these manuals do not silently claim they were repaired. Report a reproducible case with exact images/versions and emulator configuration.

<a id="part-ii"></a>

## Part II — Understanding BetterCP/M

<a id="understanding-organization"></a>

### Chapter 13 — Organization

BetterCP/M keeps the CP/M division of responsibility. The CCP accepts commands and starts programs; BDOS provides file, character and program-support services; BIOS connects those services to the particular machine. These are responsibility boundaries, not a promise that every subsystem is one file or contiguous memory region.

At the prompt, built-in CCP operations and CPX command packages form the command environment. An ordinary COM program replaces reclaimable command code while it runs. RSXs remain in protected memory and can intercept calls or publish services for that program. Warm boot rebuilds the command environment around the surviving protected services.

The System disk contains more than boot tracks: carriers, startup material, configuration catalogue and utilities support reconstruction and normal operation. Do not remove A0 support files merely because the system has already booted. Primary and companion Utilities disks add applications; they are not prerequisites for an independent System installation.

Configuration belongs to its owner. BIOS owns physical records and normalized logical bindings. CONFIG edits candidates and saved settings through defined interfaces. FDB manages catalogue definitions. CPX/RSX managers own extension profiles and lifetime. The distinction makes it possible to change one kind of state without claiming that every other kind changed too.

See [Overall System Architecture](../architecture/02%20Overall%20System%20Architecture.txt) for the technical model and [Extensions](#understanding-extensions) for resident services.

<a id="understanding-memory-and-execution"></a>

### Chapter 14 — Memory and Execution

Ordinary COM programs begin at 0100h in the Transient Program Area. Page zero retains the CP/M entry conventions, command tail and default FCB environment. The dynamic compatibility gateway defines the protected upper boundary visible through the jump at 0005h. An application must use that current boundary rather than assume all RAM is available.

| Region or state | Application execution | Ordinary warm boot | Cold boot |
| --- | --- | --- | --- |
| Application/TPA contents | Owned by current transient | Can be replaced | Reinitialized by startup |
| CCP and CPX command code | Reclaimable by transient | Reconstructed from configured carriers | Constructed from startup environment |
| Active supported RSXs | Protected; consume TPA headroom | Preserved | Reloaded only by the cold-start path/script |
| Built-in history | Fixed bounded persistent object | Preserved | Emptied |
| Saved disk configuration | Installed defaults remain on media | Distinct from live state | Loaded into runtime bindings |

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

SAVE belongs in the CCP because loading another transient would destroy the memory image it saves. GET loads without execution; GO establishes ordinary entry at 0100h, while JUMP transfers to a chosen address under its documented contract. Use their [reference entries](Command-and-Utilities-Reference.md#get) for exact operands and entry-state differences.

The bounded PDS contains the fixed 192-byte HISTORY object only. It is not a general allocator for all persistent subsystem state. ROM/XIP ownership has separate technical qualification and does not replace the default RAM downloads; 56K fullram and checked profiles remain deferred.

<a id="understanding-command-environment"></a>

### Chapter 15 — Command Environment

The prompt identifies the current drive and user. Drive/user navigation and the deliberately built-in memory commands are handled by the CCP. Other commands are offered to CPXs in configured order. The first package that handles a name wins; only an unhandled name proceeds to transient lookup. Explicit `:` or `.` requests bypass ordinary resident selection.

Unqualified transient lookup checks the current DU and then A0. Qualified lookup restricts the location. Operand resolution is separate from executable lookup, so a program loaded from A0 can still operate on files in the caller's DU. CPX/RSX carriers instead use their documented fixed A0 loading path.

Editing and history operate at the command line. They do not impose the same keys on every application. Warm boot reconstructs CCP/CPX code and preserves the bounded history object. The history's warm lifetime does not mean it is a disk-based history file or a separately loaded HISTORY.RSX.

Batch execution is another command source. SUBMIT constructs the authoritative A0 queue; compatible XSUB buffered input consumes submitted application lines through its service. These mechanisms do not provide general conditionals, named-directory lookup, universal keyboard injection. Numeric PATH is provided separately in 1.1.

RCP is the normal command package but can be removed. A CPX name retained in the four-entry profile may lack a usable carrier. Distinguish configuration, successful loading and actual command availability when diagnosing a missing command. There is no general automatic resident-to-transient option handoff.

<a id="understanding-files-drives-disks"></a>

### Chapter 16 — Files/Drives/Disks

A file is identified by its DU and 8.3 name, not just its displayed name. A user area partitions directory names on one logical drive; it is not a modern hierarchical directory. BetterCP/M extends the available user range to 0–31. A logical drive maps through a normalized binding to physical storage and a format interpretation.

CP/M transfers 128-byte logical records and allocates space in larger blocks. Allocated bytes, physical record length, directory entries and a text program's 1Ah end marker measure different things. A file can have padding in its last record; a checksum or binary tool must state what bytes it covers. Free data blocks do not guarantee a free directory entry.

Read-only, system and archive attributes have distinct roles. A selection predicate filters files; it is not permission to override protection. COPY's backup completion and ARC behavior are defined by COPY, not inherited automatically by PIP or every writer. Shared selection syntax is available only in commands that implement it.

Text FDF and compiled FDB describe how to construct a validated binding. The active BIOS-owned binding is runtime authority; replacing a catalogue does not reinterpret it. Saved cold-boot bindings are self-contained. Candidate edits, active state, saved state, observed media and derived caches must be kept distinct.

Formatting writes physical media, copying duplicates data, and SYSGEN installs or exports the reserved system image. None is a synonym for selecting a catalogue entry. BCPM780 uses a different reserved area from optional historical 790K. The catalogue's 108 admitted definitions do not establish universal controller or physical-media interchange.

<a id="understanding-console-terminals-io"></a>

### Chapter 17 — Console/Terminals/I/O

CP/M applications can use cooked character services, direct console services, logical reader/punch/list devices or BIOS calls. Those routes differ in echo, control-character handling, polling and redirection. An application's private hardware accesses can bypass the portable console path entirely.

BetterCP/M 1.1 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. TYPE/TED/HELP have not been migrated to TCAP 2.0, and HELP is not shipped. TYPE, TED and HELP are examples, not the complete affected-utility set; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md).

The personality owns protocol state such as an incomplete sequence; the backend owns hardware rendering and its limits. Command return discards unfinished parsing according to the monitor contract without treating that reset as a request to clear the screen or discard ordinary keyboard input. Backend dependencies must remain satisfied while a personality is active.

IOBYTE selects logical character routes where the platform supplies them. PIP's physical aliases temporarily select appropriate routes; unavailable devices fail explicitly. A device name in a historical manual is not proof that the locked BIOS implements that device on both targets.

ANSI/VT100 support is a bounded subset. Keyboard mappings also depend on the original machine, emulator and host terminal. Use the actual application installation, personality tests and [keyboard notes](#appendix-c) to diagnose a mismatch. TCAP 2.0 supplies the bounded direct API; additional terminal geometry and utility migrations remain deferred.

<a id="understanding-extensions"></a>

### Chapter 18 — Extensions

A CPX extends command interpretation and belongs to the reclaimable command environment. An RSX extends services and remains protected while a transient runs. The word resident does not give both classes the same lifetime or memory cost.

Load order is explicit profile order. The managers validate carriers and reconstruct affected memory under their supported transaction/lifecycle rules; runtime addresses are not permanent module identities. Stateful movement requires declared pointer repair, not merely copying bytes. Applications should discover supported services through versioned interfaces rather than retain addresses across a layout change.

Service discovery and service operation are separate contracts. The native clock illustrates this: a hardware provider publishes TIME service; TIME.COM is a client; optional P2DOS translates historical Functions 200/201 to that native service. Loading the frontend alone does not supply hardware, and a read-only provider cannot satisfy clock-setting requests.

Carrier formats and ABIs are independent of the distribution number. Production RSXs use BRSX v2; BRSX v1 is history. CPX carriers use BCPX v1. Public private-namespace services occupy assigned Functions 176–183; reserved/test selectors are not extra application APIs. The [Programmer's Guide](Programmers-Guide.md) consolidates current calling contracts from the existing [extension reference](../programmers/RSX%20and%20CPX%20Programmer%27s%20Guide.md) and focused specifications.

User-facing extension management remains bounded: fixed A0 carrier lookup, configured profile limits, explicit terminal dependencies and supported warm lifetime. Named directories, general PDS allocation and a general dependency framework are not implied by the mechanism.

<a id="understanding-portability"></a>

### Chapter 19 — Portability

Application portability and operating-system porting are different tasks. An ordinary CP/M 2.2 application can remain portable by using the documented execution, file and character interfaces. An OS port must supply hardware initialization, memory ownership, console and storage services, boot media and qualification for a new target.

The BIOS boundary keeps much of the system hardware-independent. Disk formats still require suitable controller operations, sector geometry and translation. Terminal personalities reduce application/display coupling, but direct video-memory code and unsupported sequences retain platform assumptions. Clock providers likewise isolate hardware without making every historical clock API available.

The two locked release targets are patched cpmsim and Model 4 under trs80gp. Their receipts do not establish physical Model 4 transfer, Model 4D/4P support, arbitrary controllers, or another Z80-family machine. ROM/XIP evidence is separately scoped. A platform-roadmap entry is not release qualification.

For rebuilding supplied targets, start with [distribution construction](../releases/DISTRIBUTION-BUILD.md), [native build media](../programmers/BUILD-DISK.md) and matching Source-package instructions. For adaptation, start with [Hardware Abstraction](../architecture/08%20Hardware%20Abstraction.txt) and the [baseline platform specification](../platform/Baseline%20Platform%20Specification.txt). The [Practical Porting Guide](Practical-Porting-Guide.md) covers assessment, bring-up, BIOS/disk/memory integration, media generation and qualification; it does not add a new 1.0 port requirement.

<a id="appendices"></a>

## Appendices

<a id="appendix-a"></a>

### Appendix A — Task and command locator

| Task | Reference |
| --- | --- |
| List or find files | [DIR resident](Command-and-Utilities-Reference.md#dir-resident), [DIR transient](Command-and-Utilities-Reference.md#dir-transient) |
| Copy, move, rename or erase | [COPY](Command-and-Utilities-Reference.md#copy-transient), [MOVE](Command-and-Utilities-Reference.md#move-resident), [REN](Command-and-Utilities-Reference.md#ren-transient), [ERA](Command-and-Utilities-Reference.md#era-transient), [PIP](Command-and-Utilities-Reference.md#pip) |
| Inspect bytes, search, compare or verify | [DUMP](Command-and-Utilities-Reference.md#dump), [SEARCH](Command-and-Utilities-Reference.md#search), [COMPARE](Command-and-Utilities-Reference.md#compare), [CRCKSUM](Command-and-Utilities-Reference.md#crcksum), [MD5SUM](Command-and-Utilities-Reference.md#md5sum) |
| Edit text | [ED](Command-and-Utilities-Reference.md#ed), [TED](Command-and-Utilities-Reference.md#ted) |
| Configure or maintain disks | [CONFIG](Command-and-Utilities-Reference.md#config), [FDB](Command-and-Utilities-Reference.md#fdb), [DUP](Command-and-Utilities-Reference.md#dup), [SYSGEN](Command-and-Utilities-Reference.md#sysgen) |
| Manage memory or extensions | [STAT](Command-and-Utilities-Reference.md#stat), [CPX](Command-and-Utilities-Reference.md#cpx), [RSX](Command-and-Utilities-Reference.md#rsx) |
| Automate commands | [SUBMIT](Command-and-Utilities-Reference.md#submit), [XSUB](Command-and-Utilities-Reference.md#xsub) |
| Archive or compress | [NOAH](Command-and-Utilities-Reference.md#noah), [compression entries](Command-and-Utilities-Reference.md#archives-and-compression) |
| Develop or inspect a program | [development tools](Command-and-Utilities-Reference.md#editing-and-development-tools), [memory commands](Command-and-Utilities-Reference.md#command-environment-and-execution) |

Complete syntax is maintained in those entries rather than repeated here. A PEEK invocation can use its alias P. Program availability and package location are stated in each entry.

<a id="appendix-b"></a>

### Appendix B — Command-Line Editing Keys

BetterCP/M provides command-line editing and command-history facilities that make it easier to enter, correct, and reuse commands.

Instead of retyping an entire command after making a mistake, you can move the cursor to the error, correct it, and continue typing. You can also recall previously entered commands, modify them, and execute them again.

BetterCP/M uses editing conventions familiar to users of WordStar and other CP/M programs, although some assignments differ.

This appendix summarizes the command-line editing facilities described in [Chapter 5](#chapter-5).

#### B.1 Entering and Editing Commands

Commands are entered at the BetterCP/M command prompt.

For example:

```text
A0>COPY REPORT.TXT B:
```

Press **Return** to execute the command.

Before pressing Return, you can edit the command line. Editing changes only the command being entered; it does not affect files or execute any part of the command.

##### Basic Editing Operations

The command editor provides facilities for moving the cursor, inserting characters, and deleting unwanted text.

For example, suppose you've typed:

```text
A0>COPY REPROT.TXT B:
```

You can move the cursor back to the misspelled filename, correct it to `REPORT.TXT`, and then press Return.

You don't need to erase and reenter the entire command.

##### Editing-Key Conventions

BetterCP/M follows several conventions familiar to users of WordStar-style editors.

However, the command editor is not a complete WordStar editor, and its key assignments should not be assumed to match WordStar in every respect.

The exact assignments for cursor movement and line editing should be taken from the command processor's supported keyboard interface.

The key combinations listed below are those established for BetterCP/M 1.0.

#### B.2 Command History

BetterCP/M maintains a history of previously entered commands.

You can recall an earlier command, edit it, and execute it again without retyping the entire line.

The command-history controls in BetterCP/M 1.0 are:

| Key | Function |
|---|---|
| **Ctrl-K** | Recall the previous command |
| **Ctrl-J** | Move forward to a newer command |
| **Return** | Execute the displayed command |

For example, suppose you've entered:

```text
A0>COPY REPORT.TXT B:
```

To repeat the command, press Ctrl-K to recall it.

You can then press Return to execute it again or edit the command before executing it.

To move farther back through the history, press Ctrl-K again.

To move toward more recently entered commands, press Ctrl-J.

##### Arrow Keys

The original Model 4 keyboard supplies these command-editor aliases:

| Physical key | Function |
|---|---|
| Left / Right | Move one character left / right |
| Up / Down | Previous / next command in history (Ctrl-K / Ctrl-J) |
| Clear / Shift-Clear | Escape (ESC, `1Bh`) |
| Ctrl-Clear | DEL (`7Fh`) |
| Shift-Left / DEL | Delete the character left of the cursor (Ctrl-H) |

CLEAR follows Montezuma Micro's ESC convention; use Ctrl-V to toggle
insert/overwrite. In trs80gp, Home activates CLEAR. Physical Layout also maps
the host apostrophe key to CLEAR; the software keyboard offers a `CLR` key.
Host Esc activates BREAK, which produces Ctrl-C rather than ESC. See the
[trs80gp keyboard reference](https://48k.ca/trs80gp.html#keyboard).

Physical Left is distinct from Ctrl-H. Ctrl-E and Ctrl-X retain physical-line continuation and line-discard behavior; they do not navigate history.

Host-emulator keyboard translation and other console keyboards may produce different codes or escape sequences. The Model 4 assignments describe the original machine's keyboard signals. Use Ctrl-K/J for history if host arrow keys do not behave as expected.

##### Editing Recalled Commands

A recalled command can be edited just like a newly entered command.

For example, suppose the history contains:

```text
A0>COPY REPORT.TXT B:
```

You could recall it, change the destination drive, and execute:

```text
A0>COPY REPORT.TXT C:
```

The recalled command is not executed until you press Return.

##### History Persistence

Command history is maintained by the command environment rather than by individual transient programs.

It remains available when a program finishes and returns control to the command processor.

It also survives an ordinary warm boot.

A cold boot begins with an empty command history.

History storage is limited. As new commands are entered, older entries are eventually discarded.

#### B.3 Control Keys and Terminal Differences

Control-key combinations are entered by holding Ctrl while pressing the corresponding key.

For example, Ctrl-K means holding Ctrl and pressing K.

On most terminals, control-key combinations produce character codes rather than distinct keyboard events.

This distinction matters because different keyboards and terminal emulators may generate different codes for the same physical key.

##### Physical Keys and Control Characters

An arrow key is not necessarily equivalent to a particular control-key combination.

For example, one computer may generate a single control character when its Up arrow is pressed, while a terminal emulator may transmit a sequence of several characters.

BetterCP/M can recognize a key only if the console environment supplies a representation that its command editor understands.

Consequently, the behavior of physical cursor keys can vary between platforms.

##### WordStar Conventions

Some command-editor controls follow WordStar conventions, but Ctrl-E/X keep CP/M continuation/discard behavior. Use the complete editor table in [Section B.5](#appendix-b--command-line-editing-keys). [Section C.4](#appendix-c--control-characters-and-keyboard-conventions) describes traditional application-level WordStar controls.

#### B.4 Keyboard Differences Between Platforms

BetterCP/M runs on computers with different keyboard arrangements.

Some provide dedicated cursor keys, while others rely heavily on control-key combinations.

Terminal emulators may also translate host keyboard input before passing it to the emulated computer.

For example, a modern keyboard may provide characters or keys that did not exist on the original computer.

The emulator must translate those inputs into codes recognized by the emulated hardware or operating system.

##### TRS-80 Model 4 Keyboard

The TRS-80 Model 4 keyboard lacks several punctuation characters found on modern keyboards.

BetterCP/M retains Montezuma Micro-style keyboard combinations for entering these characters.

| Character | Model 4 key combination |
|---|---|
| `[` | Ctrl-8 |
| `]` | Ctrl-9 |
| `{` | Ctrl-comma |
| `}` | Ctrl-period |
| `\` | Ctrl-/ |
| `\|` | Ctrl-1 |
| `~` | Ctrl-3 |
| `^` | Ctrl-5 |
| `` ` `` | Ctrl-7 |
| `_` | Ctrl-minus |

These combinations refer to the original Model 4 keyboard.

When using an emulator, the host keyboard may require different physical keys to produce the corresponding Model 4 key signals.

Shift may also be held with the indicated control-key combinations.

##### Terminal Emulators

When using BetterCP/M through a terminal emulator, the emulator's keyboard configuration can affect which control characters reach the operating system.

If a key does not behave as expected, check the terminal emulator's keyboard settings.

In particular, do not assume that its arrow keys produce the same control codes as the original computer's cursor keys.

For command-history navigation, Ctrl-K and Ctrl-J remain the documented BetterCP/M 1.0 controls.

#### B.5 Quick Reference

These assignments apply while the BetterCP/M command editor owns input at the prompt. Applications can assign different meanings to the same controls.

| Key | Function |
|---|---|
| Return | Execute the current command |
| Ctrl-S / Ctrl-D | Move one character left / right |
| Ctrl-A / Ctrl-F | Move to the previous / next word |
| Ctrl-T | Delete the next word and adjacent spacing |
| Ctrl-V | Toggle insert/overwrite |
| Ctrl-G | Delete the character under the cursor |
| Ctrl-H | Delete the character left of the cursor |
| Ctrl-U / Ctrl-X | Discard the complete command line and redraw an empty prompt |
| Ctrl-E | Continue the same command on a new physical screen line; do not execute it |
| Ctrl-K / Ctrl-J | Previous / next command in history |
| Ctrl-C | Abandon input, echo `^C`, and warm boot |
| Ctrl-P | Toggle shared console printer echo to `LST:` |

Ctrl-S moves the cursor at the prompt. During cooked console output it pauses scrolling until the next key; the resume key is consumed. Ctrl-P changes the shared console printer-echo state, so its effect can continue into transient programs.

For the control characters used by CP/M programs and terminal devices, see [Appendix C](#appendix-c), *Control Characters and Keyboard Conventions*.

<a id="appendix-c"></a>

### Appendix C — Control Characters and Keyboard Conventions

Control keys depend on input context. The CCP's history keys are not WordStar movement keys; TED, ED, DDT and other applications retain their own bindings. Ctrl-C can request command termination or warm boot and must not be treated as a universal save. Ctrl-Z is a text/input terminator in particular tools, not a filesystem byte-length field. Raw binary tools can treat 1Ah as ordinary data.

On the original Model 4, BREAK supplies ETX and CLEAR supplies Escape. Host emulators may map these differently; consult the platform guide. The portable CCP history assignments are Ctrl-K/Ctrl-J. A host arrow key can send a multi-byte terminal sequence, so do not infer a control byte merely from the keycap.

Console echo/flow control and application terminal parsing are separate. BDOS cooked output may expand TAB; direct byte output and a terminal personality have different responsibilities. For exact interactive keys use the command's reference entry and for CP/M calling semantics use programmer documentation.

<a id="appendix-d"></a>

### Appendix D — File Attributes and File Specifications

The canonical detailed notation and per-command selection matrix now live in [File specifications and attributes](Command-and-Utilities-Reference.md#file-specifications). Use a simple DU such as B3: for a location; use selector lists/ranges or attribute predicates only when the command supports them. A template for REN is not a destination DU; compression commands accept drive-only file operands; CPX/RSX accept carrier stems. These distinctions prevent a familiar-looking qualifier from selecting an unintended file or being rejected.

<a id="appendix-e"></a>

### Appendix E — BetterCP/M and CP/M 2.2 Compatibility Notes

BetterCP/M is intended to provide a compatible implementation of Digital Research CP/M 2.2 while extending its capabilities in ways useful to contemporary CP/M users.

Compatibility is an important part of BetterCP/M's design. Existing CP/M programs should ordinarily be able to use the familiar operating-system services without modification, while users can take advantage of BetterCP/M's additional commands, utilities, and resident extensions.

Nevertheless, compatibility does not mean that BetterCP/M behaves identically to Digital Research CP/M 2.2 in every respect.

Some differences are deliberate extensions. Others reflect variations among historical CP/M implementations, differences in hardware, or the behavior of particular utilities.

This appendix summarizes the principal compatibility considerations that may affect users running conventional CP/M software under BetterCP/M 1.0.

It is not intended to reproduce the complete technical compatibility specification. Programmers requiring exact BDOS behavior, calling conventions, or implementation details should consult the *BetterCP/M Compatibility Documentation* and the appropriate programming references.

#### E.1 Compatibility Objectives

BetterCP/M preserves the principal conventions of Digital Research CP/M 2.2.

These include the familiar command environment, `.COM` executable format, drive and user-area organization, file-naming conventions, and standard operating-system interfaces.

Programs that use conventional CP/M services should ordinarily require no changes.

For example, a program that uses BDOS to open, read, write, and close files should continue to use those services in the expected manner.

Likewise, programs that use the conventional console interface can continue to communicate through the BIOS and BDOS facilities provided by BetterCP/M.

##### Compatibility and Extensions

BetterCP/M adds facilities beyond those provided by Digital Research CP/M 2.2.

These include extended drive/user specifications, enhanced file-management utilities, resident extensions, terminal monitors, and clock services.

These additions are intended to supplement conventional CP/M operation rather than require applications to adopt a new programming model.

An ordinary CP/M program does not need to know whether BetterCP/M has an extended DIR utility or a resident terminal monitor installed.

It can continue using the conventional interfaces.

##### Compatibility Is Not Hardware Emulation

BetterCP/M provides an operating-system environment, not a universal emulator for every computer that historically ran CP/M.

A program that communicates directly with a particular computer's hardware may not run correctly on another computer, even when both use compatible CP/M operating systems.

For example, a program written specifically for the TRS-80 Model 4's video hardware may depend on memory addresses or hardware behavior not present on another system.

BetterCP/M's terminal monitors can provide compatible terminal-control behavior, but they cannot make arbitrary hardware-specific programs portable.

#### E.2 Program Compatibility

##### Transient Programs

BetterCP/M retains the conventional CP/M transient-program model.

Executable programs normally use the `.COM` file type and begin execution at address `0100H`.

BetterCP/M establishes the expected program environment, including the command tail, default File Control Blocks, and conventional page-zero facilities.

Programs using these conventions should ordinarily run without modification.

##### Program Termination

Conventional CP/M programs terminate by returning control to the operating system through the supported termination mechanisms.

BetterCP/M preserves this behavior.

When a transient program terminates, BetterCP/M restores the command environment and displays the command prompt.

Resident extensions intended to survive ordinary warm boots remain available.

##### Available Memory

The amount of memory available to a transient program depends on the system configuration.

Loaded RSXs occupy protected memory that is unavailable to transient programs. The CCP and CPX command code are reclaimable and can be overwritten by a transient; BetterCP/M reconstructs the command environment on warm boot.

A program may therefore encounter insufficient memory when RSXs are loaded, even though it fits without those services.

Use `STAT MEM` to check the maximum loadable COM size and `RSX LIST` to identify services you can unload. Removing an unnecessary RSX can recover program memory; unloading a CPX does not increase the maximum COM size by its reclaimable command-code size.

This is a resource limitation rather than necessarily an incompatibility in the program's operating-system calls.

##### Programs That Modify System Memory

Some historical CP/M programs make assumptions about the location or contents of the command processor, BDOS, BIOS, or other system structures.

Such programs may rely on details of a particular CP/M implementation rather than on its documented programming interface.

BetterCP/M does not guarantee compatibility with every such assumption.

Programs that use documented operating-system entry points are generally more portable than programs that inspect or modify private system structures.

#### E.3 File and Disk Compatibility

##### File Naming

BetterCP/M retains CP/M's 8.3 filename convention.

Ordinary CP/M filenames and file types remain valid.

BetterCP/M also retains conventional wildcard characters and file attributes.

Its enhanced utilities provide additional file-selection capabilities, but ordinary programs are not required to use them.

##### User Areas

Digital Research CP/M 2.2 conventionally provides user areas 0 through 15.

BetterCP/M extends this range to 0 through 31.

The additional user areas are a BetterCP/M facility.

Programs that assume the conventional range may not recognize or manage files in the additional areas correctly.

For maximum compatibility with conventional utilities, use user areas 0 through 15 when working with software that makes assumptions about the available range.

##### Drive/User Specifications

BetterCP/M commands can accept explicit drive/user specifications such as:

```text
B3:REPORT.TXT
```

Some enhanced utilities also support compound selectors:

```text
B[-]:*.COM
[A0,B3]:../user/%2A.DOC
```

These forms are BetterCP/M command extensions.

They are not part of the conventional CP/M 2.2 filename syntax understood by every application.

A third-party CP/M program may interpret such arguments differently or reject them.

Use conventional file specifications when invoking software that does not explicitly support BetterCP/M's extensions.

##### Disk Formats

CP/M was used on many computers with different disk formats.

BetterCP/M can support multiple formats through its drive-configuration facilities, subject to the capabilities of the computer and its disk controller.

However, a disk that uses a valid CP/M filesystem is not necessarily physically readable by every CP/M computer.

Differences in recording density, sector size, track organization, and controller capabilities can prevent direct interchange.

BetterCP/M's CONFIG and DUP utilities help manage supported formats, but they do not eliminate hardware limitations.

##### File Attributes

BetterCP/M retains conventional CP/M file attributes, including read-only and system attributes.

Its enhanced utilities also support archive-attribute selection and management.

Programs that use ordinary CP/M file operations can continue to use the conventional attributes.

However, software that maintains file attributes independently may not follow BetterCP/M's extended backup conventions.

In particular, the ARC attribute should not be assumed to identify every modified file unless the software involved maintains it appropriately.

#### E.4 Command Compatibility

BetterCP/M retains the familiar CP/M command environment while extending several commands.

Some extensions are available through resident commands, while others require transient utilities.

##### Resident and Transient Commands

Digital Research CP/M 2.2 includes a small set of resident commands and uses transient programs for other operations.

BetterCP/M follows the same general arrangement but supports additional resident commands through Command Processor Extensions.

The standard resident command package, `RCP.CPX`, provides commands such as:

```text
DIR   ERA   TYPE   REN   USER
CLS   VER   COPY   MOVE
```

Some commands are also available as transient programs.

For example, DIR and `DIR.COM` provide related but different capabilities.

The transient utility supports additional sorting, display, and file-search options.

##### Explicit Transient Execution

BetterCP/M provides a way to execute a transient utility even when a resident command with the same name is available.

Prefix the command with a colon or period:

```text
A0>:DIR
A0>.DIR
```

Both forms explicitly request `DIR.COM`.

This is a BetterCP/M extension to the conventional command environment.

The prefixes are interpreted by BetterCP/M's command processor and do not change the executable filename.

##### Differences in Command Syntax

Some BetterCP/M commands accept syntax that conventional CP/M utilities do not recognize.

For example:

```text
A0>COPY B[-]:*.DOC C3:
```

uses BetterCP/M's extended drive/user selection.

Similarly:

```text
A0>:DIR /S=Z-
```

uses a transient DIR option for sorting by allocated size in descending order.

These facilities are useful when working within BetterCP/M, but they should not be assumed to exist on other CP/M implementations.

##### Compatibility of Command Files

SUBMIT retains the familiar `.SUB` command-file convention and positional parameter substitution.

However, a SUBMIT file containing BetterCP/M-specific commands or options may not run unchanged under Digital Research CP/M 2.2.

For example, a batch file that invokes CONFIG or uses extended COPY options depends on BetterCP/M facilities.

When preparing command files intended for several CP/M systems, restrict them to commands and syntax supported by all the target environments.

##### Conventional Utility Behavior

BetterCP/M aims to preserve the familiar behavior of conventional CP/M utilities where compatibility matters.

However, some enhanced utilities deliberately provide additional safeguards, confirmation prompts, or error-handling facilities.

For example, transient ERA provides more extensive confirmation and file-protection controls than the traditional resident ERA command.

Likewise, transient COPY offers verification, destination-collision handling, and backup operations.

These differences are intentional and are documented in the corresponding command references.

#### E.5 Console and Terminal Compatibility

##### Conventional Console Services

BetterCP/M retains the conventional CP/M console services used by ordinary applications.

Programs that read and write characters through the supported BIOS and BDOS interfaces can continue to use those facilities.

The actual keyboard and display hardware depend on the computer.

##### Terminal-Specific Applications

Many historical CP/M applications were configured for a particular terminal.

For example, a full-screen editor might expect ADM-3A or VT52 control sequences.

BetterCP/M provides resident terminal personalities for:

| Terminal | Extension |
|---|---|
| Montezuma Micro-style ADM-3A | `ADM3A.RSX` |
| VT52 | `VT52.RSX` |
| ANSI/VT100 subset | `ANSI.RSX` |

These extensions interpret supported terminal-control sequences and pass the corresponding display operations to a screen backend.

The application must still be configured for the appropriate terminal type.

##### Terminal Limitations

BetterCP/M's terminal personalities provide supported subsets of the corresponding terminal behavior.

They do not necessarily reproduce every feature of the original physical terminals.

For example, ANSI support does not constitute complete VT100 emulation.

Similarly, keyboard translation depends on the computer, BIOS, terminal emulator, and application.

A terminal personality that interprets display sequences does not automatically guarantee that every physical key generates the codes expected by the application.

##### Direct Hardware Access

Some applications bypass CP/M's console services and manipulate display hardware directly.

These programs may be tied to a particular computer.

BetterCP/M's terminal monitors do not automatically translate such hardware access.

For best portability, use applications that communicate through conventional CP/M console services or supported terminal-control sequences.

#### E.6 Date and Time Compatibility

Digital Research CP/M 2.2 did not define a general-purpose date-and-time service in its standard programming interface.

Consequently, historical CP/M systems adopted several different clock interfaces.

BetterCP/M provides a native clock service and an optional compatibility interface for programs using P2DOS-style clock functions.

##### Native Clock Support

BetterCP/M's TIME utility obtains the date and time through a loadable clock provider.

BetterCP/M 1.0 includes:

| Provider | Environment |
|---|---|
| `FREHDCLK.RSX` | FreHD clock interface |
| `ZPRTC.RSX` | z80pack/cpmsim clock interface |

Both providers are read-only.

They support obtaining the date and time but do not permit setting the underlying clock.

The TIME utility implements a SET request, but the supplied providers reject it as unsupported.

##### P2DOS Compatibility

The optional-to-load `P2DOS.RSX` supports applications using the P2DOS-compatible date-and-time interface. Its matched carrier is supplied in A0 on both System Disks; load the platform’s native provider before the example below.

The extension supplies the corresponding BDOS functions through BetterCP/M's native clock service.

For example, under z80pack:

```text
A0>RSX LOAD ZPRTC
A0>RSX LOAD P2DOS
```

This makes the P2DOS-compatible interface available to programs that use it.

The P2DOS extension does not provide an independent hardware clock.

Its capabilities depend on the installed native provider.

Consequently, setting the clock remains unsupported with the standard read-only providers.

##### Compatibility Limits

Programs using the conventional CP/M 2.2 programming interface do not require clock support.

Programs depending on a particular manufacturer's proprietary clock interface may require additional compatibility facilities.

BetterCP/M's native and P2DOS-compatible clock services should not be assumed to reproduce every historical CP/M clock interface.

For more information, see [Chapter 11](#chapter-11), *Date and Time*.

#### E.7 Resident Extensions and Compatibility

BetterCP/M provides two types of resident extensions:

- **CPXs**, which add commands to the command processor.
- **RSXs**, which provide services that remain available while programs execute.

These are BetterCP/M facilities and are not part of the standard Digital Research CP/M 2.2 operating environment.

##### Command Processor Extensions

CPXs allow additional commands to remain resident.

Ordinary CP/M programs do not need to know whether a command is provided by a CPX or loaded from disk.

However, programs that inspect the command processor's private memory structures may encounter differences from Digital Research CP/M.

##### Resident System Extensions

RSXs provide optional services such as terminal support, clock providers, and batch input.

They can remain installed across ordinary warm boots.

Because RSXs occupy memory, they can reduce the available TPA.

This may affect programs that require nearly all the memory available on a conventional CP/M system.

Unloading unnecessary extensions can restore memory for such programs.

##### Extension Dependencies

Some RSXs require supporting extensions.

For example, a terminal personality depends on a suitable screen backend.

Load the backend before the personality, and unload them in the reverse order.

For additional information, see [Chapter 8](#chapter-8), *Resident Extensions*.

#### E.8 Compatibility Considerations for Existing Software

Most conventional CP/M applications should require little or no special preparation beyond having the appropriate executable files and terminal configuration.

However, several factors are worth checking when a program does not behave as expected.

##### Operating-System Interface

Programs using documented CP/M 2.2 BDOS and BIOS services are generally more portable than programs relying on undocumented internal structures.

If an application behaves differently under BetterCP/M, determine whether it uses conventional interfaces or makes assumptions about a particular implementation.

##### Terminal Configuration

Full-screen applications must be configured for a supported terminal environment.

If the display is incorrect, check the installed terminal personality and the application's terminal settings.

Use the supplied terminal test utilities to verify the monitor independently of the application.

##### Memory Requirements

Resident extensions reduce available transient memory.

If a program reports insufficient memory, unload optional extensions that are not required for its operation.

##### File and Disk Assumptions

Some programs assume particular disk capacities, drive arrangements, or user-area ranges.

BetterCP/M's extended facilities do not automatically remove those assumptions.

Use compatible disk formats and conventional file locations when working with software that has limited configuration options.

##### Program-Specific Installation

Some historical CP/M applications require installation or configuration for a particular terminal, printer, or computer.

These requirements remain relevant under BetterCP/M.

The operating system cannot automatically determine every application-specific hardware assumption.

Consult the application's original documentation when necessary.

#### E.9 Reporting Compatibility Problems

If a conventional CP/M program behaves unexpectedly under BetterCP/M, the most useful first step is to determine whether the problem is reproducible.

Record the program's name and version, the BetterCP/M version, the computer or emulator, and the circumstances under which the problem occurs.

Where possible, determine whether the same program behaves differently under Digital Research CP/M 2.2 on an equivalent platform.

This can help distinguish an operating-system compatibility issue from an application configuration problem or a hardware limitation.

##### Information to Record

A useful compatibility report should identify:

| Information | Example |
|---|---|
| Application | Program name and version |
| Operating system | BetterCP/M release and build |
| Platform | Computer or emulator |
| Terminal configuration | Installed screen backend and personality |
| Resident extensions | Output of `RSX LIST` and `CPX LIST` |
| Disk configuration | Relevant drive and format assignments |
| Problem | Expected behavior and observed behavior |

Include the commands needed to reproduce the problem when possible.

If the application displays an error message, record its exact wording.

##### Comparing with Digital Research CP/M

When practical, test the same application under a known working Digital Research CP/M 2.2 installation.

Use equivalent hardware or emulator configurations where possible.

A difference in behavior may identify a compatibility issue, but it may also reflect different BIOS implementations, terminal settings, or disk formats.

A controlled comparison is more useful than simply observing that a program works on one computer and fails on another.

##### Further Technical Documentation

This appendix summarizes compatibility issues from the user's perspective.

More detailed compatibility information is maintained separately, including documentation of the supported CP/M interfaces and the results of compatibility testing.

Those documents are intended primarily for developers, system maintainers, and users investigating specific compatibility questions.

For the programming interfaces themselves, consult the [BetterCP/M RSX and CPX Programmer's Guide](../programmers/RSX%20and%20CPX%20Programmer%27s%20Guide.md) and the original Digital Research CP/M 2.2 documentation.

<a id="appendix-f"></a>

### Appendix F — System Messages and Error Reference

The complete [shared message reference](Command-and-Utilities-Reference.md#system-messages) is now maintained with the Command and Utilities Reference. Each command entry also explains its own errors and recovery. [Chapter 12](#chapter-12) provides symptom-oriented starting points. Preserve exact error wording, versions, locations and any reported recovery filenames when reporting a problem.

<a id="appendix-g"></a>

### Appendix G — Glossary

This glossary defines the principal terms used throughout the BetterCP/M User's Guide.

It includes terminology inherited from Digital Research CP/M 2.2, terms associated with BetterCP/M's extensions, and expressions commonly encountered when working with CP/M computers and software.

The definitions are intended to help readers understand the manual rather than provide exhaustive technical descriptions. Where a subject requires more detailed treatment, references to the relevant chapters are provided.

#### A

**Allocation Block**  
A unit of disk space allocated to a file by the CP/M filesystem. An allocation block consists of one or more 128-byte logical records. The allocation-block size depends on the disk format.

**Archive Attribute (ARC)**  
A file attribute commonly used by backup utilities. BetterCP/M can select files according to their ARC status and provides facilities for clearing the attribute after successful backup operations. The attribute does not necessarily indicate whether a file has changed unless the software modifying it maintains the attribute appropriately. See [Appendix D](#appendix-d).

**ASCII (American Standard Code for Information Interchange)**  
A character-encoding standard used by CP/M for text and control characters. Standard ASCII defines 128 character codes, including printable characters and control codes such as carriage return, line feed, and Escape.

**Attribute**  
Information associated with a file that affects its treatment by the operating system or utilities. CP/M attributes include read-only, system, and archive. BetterCP/M provides extended facilities for selecting files according to their attributes.

#### B

**Batch File**  
A text file containing commands to be executed in sequence. BetterCP/M uses `.SUB` files with the SUBMIT utility for batch processing. See [Chapter 6](#chapter-6).

**BDOS (Basic Disk Operating System)**  
The portion of CP/M that provides standard operating-system services to programs, including file management, console input and output, and other system functions. Programs ordinarily access BDOS through the conventional CP/M calling interface.

**BIOS (Basic Input/Output System)**  
The hardware-dependent portion of CP/M. The BIOS provides low-level services for disk drives, the console, and other devices. Different computers require BIOS implementations suited to their hardware.

**Boot**  
The process of starting the operating system. A cold boot initializes a new operating session, while a warm boot returns control to the operating environment without performing a complete cold startup.

**Boot Disk**  
A disk containing the operating-system image and bootstrap information required to start the computer. A boot disk may also contain ordinary programs and data files.

**Bootstrap**  
The initial program or sequence of operations that loads the operating system into memory and transfers control to it.

**BS (Backspace)**  
ASCII control character `08H`, commonly generated by Ctrl-H or a Backspace key. Its treatment depends on the console or application.

#### C

**CCP (Console Command Processor)**  
The portion of CP/M responsible for accepting and interpreting commands entered at the console. BetterCP/M extends the conventional command environment through resident commands, command history, and Command Processor Extensions.

**Cold Boot**  
A complete operating-system startup that establishes a new session and initializes the configured environment. BetterCP/M executes its saved startup command during a cold boot. Command history begins empty, and the configured startup environment is established.

**Command History**  
A collection of previously entered commands retained by BetterCP/M's command processor. Commands can be recalled, edited, and executed again. BetterCP/M 1.0 uses Ctrl-K and Ctrl-J for history navigation. See [Appendix B](#appendix-b).

**Command Processor Extension (CPX)**  
A resident extension that adds commands to BetterCP/M's command processor. The standard resident command package is `RCP.CPX`. CPXs are managed using the CPX utility. See [Chapter 8](#chapter-8).

**Command Tail**  
The text following a transient program's name on the command line. CP/M makes this text available to the program using its conventional command-tail representation.

**Console**  
The keyboard and display, terminal, or equivalent device through which the user communicates with the operating system.

**Control Character**  
An ASCII character traditionally used for a control operation rather than as a printable symbol. Examples include carriage return, line feed, backspace, and Escape. See [Appendix C](#appendix-c).

**CP/M (Control Program for Microcomputers)**  
The operating system developed by Digital Research for microcomputers, particularly those using Intel 8080-compatible processors. CP/M 2.2 is the principal compatibility target for BetterCP/M.

**CP/M 2.2**  
The widely used Digital Research CP/M release that provides the standard operating-system interface and behavior BetterCP/M seeks to reproduce.

**CPX**  
See *Command Processor Extension*.

**Current Configuration**  
The system settings presently in use. These may differ from the settings saved for subsequent cold boots. See [Chapter 7](#chapter-7).

#### D

**DDT (Dynamic Debugging Tool)**  
Digital Research's machine-language debugging utility. DDT provides facilities for examining and modifying memory, disassembling instructions, and controlling program execution.

**Directory**  
The portion of a CP/M filesystem containing information about files, including their names, user areas, attributes, and allocated storage. Unlike hierarchical filesystems, conventional CP/M directories do not contain subdirectories.

**Directory Entry**  
A record in the CP/M directory describing a file or part of a file. A file may require several directory entries depending on its size and the disk format.

**Disk Format**  
The organization of a disk, including its physical recording characteristics and filesystem parameters. CP/M computers used many different formats, not all of which are interchangeable.

**Disk-Format Definition**  
A description of a disk's organization used by BetterCP/M to access it. Format definitions are selected and managed through CONFIG.

**Drive**  
A logical or physical storage device. CP/M identifies logical drives by letters such as A and B.

**Drive/User (DU)**  
A particular combination of logical drive and user area, such as `A0:` or `B3:`. BetterCP/M uses drive/user specifications extensively in its enhanced file-management commands.

**DU Selector**  
A BetterCP/M file-selection expression identifying one or more drive/user areas. For example, `B[-]:` selects all user areas on drive B. See [Appendix D](#appendix-d).

#### E

**ED**  
Digital Research's traditional CP/M context editor. ED is a line-oriented text editor operated through commands rather than a full-screen display.

**End-of-Text Marker**  
The Ctrl-Z character (`1AH`), traditionally used to indicate the end of meaningful text in CP/M text files.

**Escape Sequence**  
A sequence of character codes, commonly beginning with ASCII Escape (`1BH`), used to request terminal operations such as cursor movement or screen clearing.

**Extent**  
A unit of file organization represented by CP/M directory information. Large files may occupy multiple extents and directory entries.

#### F

**FCB (File Control Block)**  
A data structure used by CP/M programs to identify files and perform file operations through BDOS. Conventional CP/M programs use FCBs for opening, reading, writing, and managing files.

**File Attribute**  
See *Attribute*.

**File Specification (Filespec)**  
A filename, optionally accompanied by a drive/user qualification, wildcard characters, or supported attribute expressions. For example, `B3:*.COM[$ARC]` is an extended BetterCP/M file specification.

**File Type**  
The optional portion of a CP/M filename following the period. A file type contains up to three characters. Common examples include `.COM`, `.ASM`, `.TXT`, and `.SUB`.

**FreHD**  
A storage peripheral for the TRS-80 Model 4 and related systems. BetterCP/M provides a FreHD clock provider through `FREHDCLK.RSX`.

#### H

**Hexadecimal**  
A base-16 number system using digits 0–9 and letters A–F. Hexadecimal is commonly used when displaying memory addresses, machine instructions, and byte values. In this manual, hexadecimal values may be identified by an `H` suffix.

**Host Computer**  
The computer running an emulator or providing services to an emulated CP/M system. For example, z80pack may obtain date and time information from its host environment.

#### I

**IOBYTE**  
A conventional CP/M system value used to select logical character-device assignments. BetterCP/M retains the IOBYTE mechanism. STAT manages the live value, while CONFIG can save a value for subsequent disk cold boots.

#### L

**Logical Drive**  
A drive identified by a CP/M drive letter, such as A or B. BetterCP/M associates logical drives with physical devices and disk-format definitions.

**Logical Record**  
The standard 128-byte unit used by CP/M file and disk services. Physical disk sectors may contain one or more logical records.

#### M

**Montezuma Micro**  
A company known for its CP/M implementation for the TRS-80 Model 4. BetterCP/M retains compatibility with selected Montezuma Micro conventions, including its ADM-3A terminal behavior and keyboard arrangements.

#### P

**P2DOS**  
A CP/M-compatible operating-system implementation that introduced additional services, including date-and-time facilities. BetterCP/M provides optional P2DOS-compatible clock services through `P2DOS.RSX`.

**Physical Drive**  
The actual disk drive or storage device associated with a logical drive. BetterCP/M distinguishes physical-drive characteristics from logical-drive assignments.

**PIP (Peripheral Interchange Program)**  
The traditional CP/M utility for copying and transferring data between files and devices. PIP supports a variety of text and data-transfer options.

**Program Image**  
The machine-language instructions and associated data of a program as stored in a file or loaded into memory.

#### R

**RCP (Resident Command Package)**  
The standard BetterCP/M Command Processor Extension, supplied as `RCP.CPX`. It provides frequently used commands such as DIR, ERA, REN, TYPE, COPY, MOVE, CLS, and VER.

**Read-Only Attribute (RO)**  
A file attribute that protects a file against ordinary modification or deletion. BetterCP/M utilities may provide explicit facilities for handling protected files.

**Resident Command**  
A command available directly through the command processor or an installed CPX, without loading a separate transient `.COM` program.

**Resident System Extension (RSX)**  
A loadable component that provides services while other programs execute. BetterCP/M uses RSXs for terminal support, clock providers, batch input, and other facilities. See [Chapter 8](#chapter-8).

**RSX**  
See *Resident System Extension*.

#### S

**Saved Configuration**  
System settings stored for use during subsequent cold boots. Saved settings may differ from those currently active.

**Sector**  
A physical unit of disk storage. Sector sizes and organization depend on the disk format. A physical sector may contain several CP/M logical records.

**SUBMIT**  
The CP/M batch-processing utility that executes commands stored in `.SUB` files. BetterCP/M retains the familiar SUBMIT conventions. See [Chapter 6](#chapter-6).

**System Area**  
The reserved portion of a bootable CP/M disk containing operating-system and bootstrap information. SYSGEN installs BetterCP/M into this area.

**System Attribute (SYS)**  
A file attribute that ordinarily suppresses a file from conventional directory listings. The attribute does not necessarily mean that the file is part of the operating system.

**System Image**  
The operating-system code and associated configuration information installed in a disk's reserved system area. BetterCP/M system images can be saved and installed using SYSGEN.

**SYSTEM.SYS**  
The conventional filename for a BetterCP/M system-image package. Such packages contain the operating-system image and associated installation information.

#### T

**Terminal**  
A device or emulated environment providing keyboard input and character-oriented display output.

**Terminal Monitor**  
A resident facility that interprets supported terminal-control sequences and performs the corresponding display operations through a screen backend.

**Terminal Personality**  
An RSX that interprets the control sequences associated with a particular terminal type. BetterCP/M provides ADM-3A, VT52, and ANSI/VT100-subset personalities.

**TPA (Transient Program Area)**  
The region of memory available for ordinary CP/M programs. Resident extensions reduce the amount of TPA available to transient programs.

**Transient Command**  
A command implemented by a program loaded from disk, normally as a `.COM` file. BetterCP/M can explicitly invoke a transient command using a colon or period prefix.

#### U

**User Area**  
A numbered file-organization area within a CP/M drive. Conventional CP/M 2.2 supports user areas 0–15; BetterCP/M extends the range to 0–31.

#### V

**VT52**  
A DEC video terminal whose control sequences were supported by many CP/M applications. BetterCP/M provides a compatible terminal personality through `VT52.RSX`.

**VT100**  
A DEC video terminal associated with ANSI-style control sequences. BetterCP/M provides a supported subset of ANSI/VT100 behavior through `ANSI.RSX`.

#### W

**Warm Boot**  
A return to the CP/M command environment without performing a complete cold startup. BetterCP/M preserves supported resident extensions and command history across ordinary warm boots.

**Wildcard**  
A character used in a file specification to select several files. CP/M uses `?` and `*` as wildcard characters. BetterCP/M provides consistent bounded wildcard rules in its enhanced file-selection facilities.

**WordStar**  
A widely used CP/M word processor whose control-key conventions influenced many other programs. BetterCP/M uses some WordStar-style editing conventions, although its command-history assignments differ.

#### X

**XSUB**  
A CP/M batch-processing extension that allows compatible programs to receive submitted input through buffered console-input services. BetterCP/M provides this facility using resident batch-input support.

#### Z

**Z80**  
An 8-bit microprocessor developed by Zilog and widely used in CP/M computers. It is compatible with the Intel 8080 instruction set while providing additional instructions and facilities.

**z80pack**  
A collection of Z80 emulation tools, including cpmsim. BetterCP/M supports z80pack environments and provides a clock provider through `ZPRTC.RSX`.

<a id="appendix-h"></a>

### Appendix H — Further Reading and Technical Documentation

| Need | Publication or current entry point |
| --- | --- |
| Operate BetterCP/M | This guide, Part I |
| Understand its behavior | This guide, Part II |
| Look up a command | [Command and Utilities Reference](Command-and-Utilities-Reference.md) |
| Install a supplied platform | [cpmsim](../platform/CPMSIM-INSTALLATION.md), [Model 4](../platform/MODEL4-INSTALLATION.md) |
| Write extensions | [Programmer's Guide](Programmers-Guide.md) with API chapters, examples and existing [monitor development](../programmers/Monitor%20RSX%20Development.md) detail |
| Rebuild from source | [Distribution build](../releases/DISTRIBUTION-BUILD.md), [native build disk](../programmers/BUILD-DISK.md), matching Source download |
| Adapt the OS | [Practical Porting Guide](Practical-Porting-Guide.md), [Hardware Abstraction](../architecture/08%20Hardware%20Abstraction.txt) and [platform references](../platform) |
| Check exact released files and limits | [Non-documentation lock](../releases/non-documentation-lock-1.0/README.md), [release notes](../releases/RELEASE-NOTES-1.0.md) |
| Study design/evidence | [Architecture](../architecture), [engineering history](../engineering), [compatibility material](../compatibility) |
| Reuse or redistribute | [Licensing](../LICENSING.md) and supplied third-party notices/source companions |

The four manuals have different coverage and evidence levels; the [programmer/porting status ledger](../programmers/REFERENCE-STATUS.md) identifies further expansion without adding software release requirements. Architecture specifications and dated engineering records remain technical references. On a conflict, check the locked artifacts, later focused contracts and exact qualification scope rather than treating an older milestone as current status. Source/specification links may require the matching Documentation or Source download when this guide is read from a System package.

Original Digital Research CP/M 2.2 operating, interface, alteration, ED, ASM and DDT manuals provide historical background. Ensure an Interface Guide includes the addendum for BDOS Functions 37 and 40. Manufacturer manuals explain their particular hardware and conventions; they do not establish BetterCP/M behavior. Consult the [BetterCP/M repository](https://github.com/CPMArchives/BetterCPM) and [Digital Research archive](http://www.cpm.z80.de/drilib.html) with the version and target machine in mind.
