# BetterCP/M 1.0 User's Guide

## Table of Contents

### 1. Introduction

BetterCP/M is a CP/M-compatible operating system for Z80-based computers. It preserves the familiar programming and operating environment of CP/M 2.2 while providing a number of extensions and improvements for modern CP/M systems.

BetterCP/M remains recognizably CP/M. Existing CP/M programs run in the conventional Transient Program Area and use the standard CP/M BDOS and BIOS interfaces. Drives, user areas, file names, command syntax, and the ordinary CP/M programming environment retain their familiar meanings.

At the same time, BetterCP/M extends the system in areas where additional facilities are useful. These include an improved command environment, command history and editing, configurable resident commands, CPX and RSX extensions, expanded disk-format and configuration facilities, and system services not provided by CP/M 2.2.

This manual describes BetterCP/M from the user's point of view: starting and operating the system, working with files and disks, using commands and utilities, configuring the system, and installing and managing extensions.

#### 1.1 What is BetterCP/M?

BetterCP/M is an implementation and extension of the CP/M operating environment rather than a replacement for it with an unrelated system.

Compatibility with CP/M 2.2 is a fundamental part of its design. Programs written for CP/M use the conventional program-entry environment, BDOS interface, file system, File Control Blocks, command tail, and other interfaces expected by CP/M software. BetterCP/M also retains familiar CP/M operating conventions such as drive letters, user areas, transient .COM programs, and warm boot.

BetterCP/M adds facilities beyond the original CP/M 2.2 environment. Some are built into the system, while others are supplied by loadable extensions or transient utilities. These facilities are designed to extend the system without unnecessarily changing the CP/M environment on which existing software depends.

BetterCP/M 1.0 is supplied for two reference environments: the TRS-80 Model 4 environment used with trs80gp, and the Z80 system environment used with z80pack/cpmsim. Platform-specific facilities can differ where the underlying hardware or emulator capabilities differ.

#### 1.2 Starting BetterCP/M

BetterCP/M starts when a prepared BetterCP/M system disk is booted on a supported system.

During a cold boot, the operating system initializes its system state, establishes the configured command environment and extensions, and applies the saved startup configuration. When initialization is complete, BetterCP/M displays its command prompt and is ready to accept commands.

A warm boot returns control to the operating system without performing a complete cold initialization. As in conventional CP/M, programs can terminate by returning through the CP/M warm-boot mechanism. BetterCP/M reconstructs the command environment as necessary and returns to the command prompt while preserving system state that is defined to survive a warm boot.

Normal operation begins at the command prompt.

#### 1.3 The Command Environment

BetterCP/M is a command-line operating system. The user interacts with and controls the operating system by typing commands at the command prompt.

A command may be provided directly by the command processor, by a resident Command Processor Extension (CPX), or by a transient program loaded from disk. This distinction is normally unimportant when entering a command: the user types the command name followed by any required operands or options.

For example:

```text
DIR
TYPE README.TXT
COPY B:PROGRAM.COM=A:PROGRAM.COM
```

BetterCP/M provides command-line editing and command history in addition to the conventional CP/M command environment. Drives and user areas can also be selected directly from the command line.

Chapter 3 describes the command environment in detail. Individual commands are described beginning in Chapter 4.

#### 1.4 Using This Manual

This manual assumes general familiarity with computers and gives particular attention to the facilities and operating conventions of BetterCP/M. Familiar CP/M concepts are described where necessary for using the system, but elementary computing concepts are not introduced separately.

Chapter 2 describes drives, user areas, file specifications, wildcards, and file attributes. Chapter 3 covers the BetterCP/M command environment, including command-line editing, history, resident and transient commands, and program execution. Chapter 4 provides the basic command reference.

Later chapters cover batch processing, CPX and RSX extensions, system configuration, disk operations, date and time facilities, installation, and troubleshooting.
Programmers who require the BetterCP/M programming interfaces should consult the BetterCP/M Programmer's Guide. Internal system architecture and implementation are covered separately in the BetterCP/M technical documentation.

### 2. Drives, User Areas, and Files
#### 2.1 Drives and User Areas

BetterCP/M follows the standard CP/M convention of identifying disk drives by letters. Drives are named `A:` through `P:`, although the number of drives actually available depends on the system and its configuration.

The current drive is shown as part of the BetterCP/M command prompt. To select another drive, enter its drive letter followed by a colon:

```text
A> B:
B>
```

Files may also be referenced on another drive without changing the current drive:

```text
A>DIR B:
A>TYPE B:README.TXT
```

BetterCP/M also retains the CP/M user-area system. Each drive can contain files in user areas numbered 0 through 15. User areas provide separate logical file spaces on the same disk: a file in one user area is ordinarily distinct from files in the other user areas on that drive.

The current user area can be selected directly by entering its number:

```text
A>5:
A5>
```

A drive and user area can be selected together:

```text
A> B3:
B3>
```

This selects drive B, user area 3.

BetterCP/M uses the term **drive/user**, or **DU**, when referring to a particular combination of drive and user area. Thus `A0:` identifies drive A, user 0; `B3:` identifies drive B, user 3.

A drive/user specification can also qualify a command or file operation without changing the current drive/user. For example:

```text
A>DIR B3:
```

lists the files in user area 3 of drive B while leaving the current drive and user area unchanged.

The ordinary CP/M conventions remain valid. Programs that use the standard BDOS drive and user facilities see the same drive/user organization, and conventional CP/M programs need not be aware of BetterCP/M's combined `DU:` command notation.

#### 2.2 File Names and File Specifications

BetterCP/M uses the standard CP/M file-naming convention. A file name consists of a name of up to eight characters and an optional file type of up to three characters, separated by a period:

```text
filename.typ
```

For example:

```text
README.TXT
STAT.COM
MYPROG.ASM
DATA
```

`README.TXT` has the file name `README` and the file type `TXT`. `DATA` has no file type.

File types commonly indicate the purpose or format of a file. For example, `.COM` normally identifies an executable program, `.ASM` an assembly-language source file, and `.SUB` a SUBMIT command file. These conventions do not change the basic organization of the file; the file type is part of its name.

A **file specification**, or **filespec**, identifies a file and may include a drive and user area:

```text
README.TXT
B:README.TXT
B3:README.TXT
```

If no drive or user area is specified, BetterCP/M uses the current drive and user area. Thus, if the current prompt is:

```text
A2>
```

the file specification:

```text
README.TXT
```

refers to `README.TXT` in drive A, user area 2.

A drive can be specified without a user number:

```text
B:README.TXT
```

and BetterCP/M commands that support DU-qualified file specifications can identify both explicitly:

```text
B3:README.TXT
```

This identifies `README.TXT` on drive B in user area 3 without requiring the current drive/user selection to be changed.

File specifications are used throughout BetterCP/M commands. For example:

```text
TYPE README.TXT
ERA B:OLD.DAT
COPY B3:REPORT.TXT A:REPORT.TXT
```

Many commands also accept **wildcard file specifications**, allowing a single specification to select more than one file. Wildcards are described in the next section.

#### 2.3 Wildcards

Many BetterCP/M commands accept wildcard file specifications when an operation is to apply to more than one file. BetterCP/M uses the standard CP/M wildcard characters `?` and `*`.

A question mark (`?`) matches any single character in the corresponding position of a file name or file type. For example:

```text
DIR TEST?.COM
```

can match files such as:

```text
TEST1.COM
TEST2.COM
TESTA.COM
```

An asterisk (`*`) is a convenient abbreviation for wildcarding the remaining characters in a name or file type. Common examples include:

```text
DIR *.COM
DIR LETTER.*
DIR *.*
```

`*.COM` selects files with the file type `COM`, regardless of file name. `LETTER.*` selects files named `LETTER` with any file type. `*.*` selects all files applicable to the command.

Wildcards can also be used with drive and user-area specifications:

```text
DIR B:*.COM
DIR B3:*.ASM
```

The first searches the applicable user area on drive B for `.COM` files. The second searches user area 3 of drive B for `.ASM` files.

Not every command permits wildcards in every operand. The description of each command states where wildcard file specifications are accepted.

#### 2.4 File Attributes

BetterCP/M supports the standard CP/M **read-only**, **system**, and **archive** file attributes. These attributes are stored with the file's directory information and are preserved by operations that preserve CP/M file attributes.

The **read-only (R/O)** attribute protects a file against ordinary operations that would modify or erase it. BetterCP/M enforces this attribute.

The **system (SYS)** attribute identifies a file as a system file. In BetterCP/M 1.0, the SYS attribute does not make a file visible across user areas; normal drive and user-area rules still apply.

The **archive (ARC)** attribute is available as file metadata. BetterCP/M 1.0 does not assign it an automatic backup policy.

A file can have more than one attribute at the same time.

The system utilities provided with BetterCP/M allow these attributes to be inspected, set, and cleared. The appropriate utility and its syntax are described later in this manual.

File attributes should not be confused with file types. In:

```text
SYSTEM.COM
```

`COM` is the file type. R/O, SYS, and ARC, if present, are attributes associated with the file.

#### 2.5 Changing Media

BetterCP/M supports removable disks and preserves the CP/M rules needed to prevent directory information from one disk from being written inadvertently to another.

Do not remove or replace a disk while an operation is reading from or writing to it. Complete the operation before changing the medium.

When a disk is changed, BetterCP/M detects or responds to the media state according to the capabilities of the drive and platform. A changed disk must be recognized before operations that modify its directory or file allocation are allowed to proceed normally.

As with conventional CP/M, a disk can become temporarily read-only when the operating system cannot safely establish that its current directory information corresponds to the medium in the drive. This protects the new disk from writes based on stale information from the disk it replaced.

If BetterCP/M reports that a disk is read-only following a media change, use the normal disk-reset or warm-boot procedure appropriate to the operation before attempting further writes. Do not treat a read-only indication following an unexpected media change as permission to force a write.

Disk copying, formatting, and other operations that intentionally replace or rewrite media are performed with `DUP` and are described in Chapter 8.

#### 2.6 Disk Status and Capacity

The amount of storage available on a CP/M disk depends on its format. BetterCP/M can therefore operate with disks of different capacities and geometries without assuming that every drive contains the same type of medium.

Disk-status utilities report information about mounted disks, including available storage where applicable. This information reflects the CP/M filesystem capacity of the selected disk rather than simply the raw physical capacity of the medium.

When examining disk space, remember that CP/M allocates file storage in blocks. The amount of free space therefore changes in allocation-block units rather than one byte at a time. A small file can consume an entire allocation block.

Directory space is also finite and is separate from file-data capacity. It is therefore possible for a disk to have unused data space but no free directory entries for additional files.

The disk format also determines such characteristics as allocation-block size and directory capacity. Most users need not work with these values directly during ordinary file operations. `DUP`, `CONFIG`, and the disk-status utilities provide the appropriate information when inspecting, preparing, or configuring disks.

Detailed disk operations and disk formats are covered in Chapter 8.

### 3. Using the Command Environment
#### 3.1 The BetterCP/M Prompt

When BetterCP/M is ready to accept a command, it displays the command prompt. The prompt identifies the current drive and, when appropriate, the current user area.

For example:

```text
A>
```

indicates drive A in the default user area, while:

```text
A5>
```

indicates drive A, user area 5.

Similarly:

```text
B3>
```

indicates drive B, user area 3.

The prompt is redisplayed after a command completes and control returns to the command environment.

Throughout this manual, examples that begin with a prompt show commands as they would be entered at the BetterCP/M console:

```text
A>DIR
```

Only the text following the prompt is typed by the user.

#### 3.2 Entering Commands

Enter a command by typing its name, followed where necessary by operands or options, and press `RETURN`.

For example:

```text
A>DIR
```

displays a directory, while:

```text
A>TYPE README.TXT
```

displays the contents of `README.TXT`.

Commands are not case-sensitive. Lower-case input is accepted and interpreted in the same manner as upper-case input:

```text
A>dir
```

Command names can identify commands built into the command processor, commands supplied by an installed CPX, or transient programs stored on disk. In ordinary use, the distinction does not affect how a command is entered.

Spaces separate a command name from its operands and, where applicable, separate individual operands:

```text
A>COPY SOURCE.TXT B:SOURCE.TXT
```

The syntax description for each command shows which operands are required, which are optional, and which forms of the command are accepted.

BetterCP/M also recognizes drive/user navigation as a command. For example:

```text
A>B3:
B3>
```

selects drive B, user area 3.

#### 3.3 Command-Line Editing

BetterCP/M allows a command line to be edited before it is executed. The cursor can be moved through the line so that errors can be corrected without retyping the entire command.

The command editor supports the familiar WordStar-style control-key conventions used by many CP/M programs. Editing operations include moving the cursor, inserting and deleting characters, and moving within the command line.

For example, if a filename has been mistyped, the cursor can be moved back to the error, the incorrect characters changed, and the completed command then submitted with `RETURN`.

Editing affects only the command currently being entered. The command is not interpreted or executed until it is submitted.

The complete command-line editing key assignments are summarized in Appendix B.

#### 3.4 Command History

BetterCP/M maintains a bounded history of previously entered commands. Earlier commands can be recalled to the command line, reviewed or edited, and executed again.

A recalled command behaves like an ordinary command line. It can be executed unchanged or modified with the normal command-line editing keys before `RETURN` is pressed.

Command history is maintained by the command environment rather than by individual transient programs. It therefore remains available when control returns to the prompt after running a program.

The history is preserved across a normal warm boot. A cold boot begins with an empty command history.

Because the history has a fixed capacity, older entries are eventually discarded as newer commands are entered.

The keys used to move through command history are listed with the other command-line editing keys in Appendix B.

#### 3.5 Selecting Drives and User Areas

The current drive and user area can be changed directly from the command prompt.

To select another drive, enter its letter followed by a colon:

```text
A>B:
B>
```

To select another user area on the current drive, enter the user number followed by a colon:

```text
B>5:
B5>
```

To select both at once, combine the drive letter and user number:

```text
B5>C3:
C3>
```

This selects drive C, user area 3.

BetterCP/M refers to a drive and user-area combination as a **drive/user**, or **DU**. The forms:

```text
B:
5:
C3:
```

are therefore all forms of drive/user navigation.

Changing the current drive/user affects subsequent operations that do not explicitly specify another location. It does not move or copy files between user areas or drives.

Many BetterCP/M commands also accept a drive/user qualification without changing the current selection. For example:

```text
A2>DIR B3:
```

operates on drive B, user area 3 and then returns to the unchanged prompt:

```text
A2>
```

This distinction is useful when working with files on several drives or in several user areas: navigation changes the current working location, while a qualified command can operate elsewhere without doing so.

#### 3.6 Resident and Transient Commands

BetterCP/M commands can be either **resident** or **transient**.

A resident command is available as part of the active command environment and can be executed without first loading an ordinary program from disk. BetterCP/M keeps only a small set of commands in the core command processor; additional resident commands can be supplied by Command Processor Extensions (CPXs).

A transient command is an executable program, normally stored on disk as a `.COM` file. When a command is not handled by the command processor or an installed CPX, BetterCP/M attempts to locate and execute the corresponding transient program.

Some commands are available in both resident and transient forms. The resident form provides commonly used functions without loading a program from disk, while the transient version can provide additional functions. Where the two forms differ, the command description identifies syntax or capabilities available only in the transient version.

For ordinary command entry, the distinction is usually transparent. For example:

```text
A>DIR
```

invokes the available `DIR` command according to the active command environment. The user does not normally need to specify whether the command is resident or transient.

The default BetterCP/M command environment includes the core resident commands and the standard resident command package. CPXs and their management are described in Chapter 6.

##### Explicit transient execution

Prefix a command name with `:` or `.` to bypass built-in and CPX commands
and invoke its `.COM` program through the ordinary transient lookup:

    :DIR B3:*.COM
    .COPY B1:FOO.DAT C3:
    :B3:FOO ARGUMENTS

Both prefixes have the same meaning. Place the prefix before any command DU
qualifier. Arguments retain their normal meaning. The same forms work in
SUBMIT files. A missing program reports the ordinary `?` lookup failure;
there is no fallback to the resident command. This explicitly selects the
transient program; automatic CPX-to-transient handoff remains unimplemented.

#### 3.7 CPX Commands

A **Command Processor Extension**, or **CPX**, extends the BetterCP/M command environment with additional resident commands.

The standard BetterCP/M configuration includes `RCP.CPX`, which provides frequently used commands such as:

```text
DIR   ERA   TYPE   REN   USER
CLS   VER   COPY   MOVE
```

These commands are available without loading an ordinary transient program into the Transient Program Area.

Additional CPXs can be installed when other resident command facilities are required. More than one CPX can be active, and BetterCP/M maintains them in a defined order.

The presence or absence of a CPX does not change the way its commands are typed. If a resident command is unavailable but a corresponding transient program is present, the transient program can provide the command instead.

For example, the standard distribution can provide transient fallbacks for commands that are normally supplied by `RCP.CPX`. This allows a reduced command environment to remain usable without requiring all convenience commands to be resident.

CPXs can be listed, loaded, and unloaded at run time. Chapter 6 describes CPX management and its effect on the command environment.

#### 3.8 Command Search and Program Execution

When a command is entered, BetterCP/M determines how the command is to be handled.

Drive/user navigation is recognized first. Core commands provided directly by the command processor are then checked, followed by commands supplied by the installed CPXs in their configured order. If none of these handles the command, BetterCP/M attempts to execute it as a transient program.

For an unqualified program name, BetterCP/M searches the current drive and user area first, then A0:. A program in the current DU takes precedence. This fixed fallback also applies to explicit transient execution with `:NAME` or `.NAME`. A drive or user qualifier, such as `B3:NAME`, restricts lookup to that location; it does not fall back to A0:.

A program found on A0: runs with the original caller's drive and user area, so unqualified file operands retain their ordinary meaning. A load or read failure after finding a program does not cause another search. This is a fixed lookup rule, not a configurable system path.

Thus, a command such as:

```text
A>MYPROG
```

can cause BetterCP/M to locate `MYPROG.COM`, load it into the Transient Program Area, establish the normal CP/M program environment, and transfer control to it.

Command-line text following the program name is supplied to the program using the standard CP/M command-tail conventions. BetterCP/M also prepares the standard default File Control Blocks and other compatibility-visible program state expected by CP/M software.

For example:

```text
A>MYPROG INPUT.DAT
```

executes `MYPROG.COM` with `INPUT.DAT` supplied as an argument in the conventional CP/M environment.

When the transient program terminates normally, BetterCP/M restores the command environment as necessary and displays the prompt again.

This process preserves the conventional CP/M program-execution model, allowing ordinary CP/M `.COM` programs to run without needing to know how BetterCP/M internally reconstructs its command environment.

#### 3.9 Terminating Commands and Programs

A command normally returns to the BetterCP/M prompt when its operation is complete.

Transient CP/M programs likewise return control to the operating system through the normal CP/M termination mechanisms. BetterCP/M then restores the command environment as necessary and displays the prompt for the next command.

Many commands and programs recognize `Ctrl-C` as an abort or termination request. The precise effect depends on the program being executed. In the command environment and BetterCP/M utilities, `Ctrl-C` is used where appropriate to abandon the current operation and return control to the prompt.

A CP/M warm boot also terminates the current program and returns control to the command environment. BetterCP/M preserves those portions of system state defined to survive a warm boot, including the active extension configuration and valid command history, while reconstructing the parts of the command environment that need to be restored.

Because an interrupted disk operation can leave an operation incomplete, avoid aborting a command while it is actively writing to a disk unless termination is necessary. If a disk operation reports an error or is interrupted unexpectedly, verify the affected files or media before continuing with further modifications. 

#### 3.10 Inline Help at Interactive Prompts

When an interactive prompt offers several abbreviated actions, `?` may display
a short explanation and repeat the prompt, including its file context, for the same item. Asking for help
does not retry, skip, abort, or change the command's current policy.

For example, COPY's collision prompt offers `Y/N/O/S/R/?`. Enter `?` to see
the meaning of those choices. Simple `Y/N` confirmations do not need a help
action, and paging prompts should state their controls directly.

Future ERA failure recovery will use `R/S/A/?`: retry the current item, skip
it, abort the command, or display help. This ERA interface is planned, not yet
implemented. Noninteractive modes follow their error policy without prompting;
quiet output does not by itself answer prompts.

### 4. Basic Commands

BetterCP/M provides a set of basic commands for everyday system operation. Some are built directly into the command processor, while others are normally supplied as resident commands by the standard `RCP.CPX`.

Several resident commands also have transient versions stored on disk. The resident version provides the command's basic, frequently used functions without loading a program from disk; the corresponding transient program may provide additional capabilities.

Each command description presents the resident and transient forms together. Where a syntax form, option, or feature is available only in the transient version, it is identified as **transient only**. If no distinction is shown, the described operation is available in both forms where both forms of the command exist.

The syntax descriptions in this chapter use the following conventions:

- Words shown in uppercase identify commands or literal command elements.
- *Italicized words* represent information supplied by the user.
- Items enclosed in square brackets `[ ]` are optional.
- A vertical bar `|` separates alternatives where more than one form is permitted.

Examples show the command as it is entered at the BetterCP/M prompt.

#### 4.1 DIR — Directory

Displays a list of files in the current or specified drive/user area.

`DIR` is available as both a resident command and a transient program. The
resident version supports the standard CP/M 2.2 `DIR` syntax:

    DIR
    DIR filespec
    DIR DU:
    DIR DU:filespec

Examples:

    A>DIR
    A>DIR *.COM
    A>DIR B:
    A>DIR B3:*.ASM

`DIR` without a file specification displays the directory of the selected
drive/user area. A file specification restricts the display to matching files.
The standard CP/M `?` and `*` wildcard characters may be used.

Both forms use the same bounded 8.3 wildcard rules as COPY: `?` matches one
position, and a terminal `*` fills the remainder of its filename or extension
field. Adjacent terminal stars are equivalent to one star. `F?*.DAT` and
`F***.DAT` are valid; `F*A.DAT` and `F**?.DAT` report `Invalid filespec.`
Characters cannot follow a star run within the same field.

Resident DIR also accepts compound DU selections and attribute predicates:

```text
DIR A[0,2]:*.COM
DIR [A0,B3]:*.DOC[$RW]
DIR B[-]:*.COM[$ARC+!$SYS]
```

The full selection is checked before searching. Each selected DU is listed
separately, with a drive/user prefix such as `B3:`. The original drive and user
are restored when DIR finishes. Plain DIR hides SYS files; an explicit attribute
expression controls inclusion of SYS files as well. The current platform
bindings permit drives A: through D:; an unsupported drive rejects the complete
selection. Empty locations report `NO FILE` individually.

##### Transient DIR.COM

**DIR.COM supports compound DU selections and attribute predicates, and works
with RCP unloaded. It combines directory extents into one file entry, supports
sorting, allocated KiB/record and directory-entry units, attribute display, automatic or explicit
columns, paging, per-DU totals and once-per-drive free-space reporting.**
Resident DIR retains its traditional
four-column display, with no sorting, sizes, attribute display or summaries.

Implemented sorting: `/S=N`, `/S=T` and `/S=Z` accept an optional `+` (ascending)
or `-` (descending); `/S=U` preserves native directory order and accepts no sign.
The last sort switch wins. Switches may go before or after the selection operand.
Type and size ties use ascending filename order. Size sorting uses allocated
space, independently of how that size is displayed. Invalid switches reject the
whole command before listing.

`/A` adds a three-position `SRA` field after each file size: SYS, read-only,
and ARC respectively, with `-` for each clear bit. For example, `-R-` means
read-only, and `S-A` means SYS plus ARC. Repeating `/A` is harmless. It does
not select files, reveal SYS files, or change their attributes; use an operand
attribute expression to select them. The display is off again on the next
invocation unless `/A` is specified.

`/Z` and `/Z=K` select allocated KiB (the default). `/Z=S` displays allocated
128-byte records, not physical floppy sectors or logical file length. `/Z=E`
counts physical directory entries occupied by the file. An empty file still
occupies one directory entry. This is not a count of logical 16 KiB extents;
one physical entry can describe several logical extents on some formats.
Per-file sizes and each selected-DU total use the chosen unit, with `K`, `S` or `E`
as the suffix. The last valid size-unit switch wins; a later `/Z` restores K.
Unit selection resets to K on the next invocation. Sorting by `/S=Z` continues
to use allocated space regardless of the display unit.

`/P` pauses after 23 output lines on the standard 24-row display. Headings,
blank lines and summaries count toward the page. The prompt spells out the
controls: Space or Enter continues, and Ctrl-C aborts DIR and restores your
original drive and user. Other keys are ignored. Repeating `/P` is harmless;
paging is off again for the next DIR command. A listing that ends exactly at
the page boundary does not require an extra key.

DIR automatically uses four, two or one column, whichever fits the selected
entries on the supported 80-column display. It measures the actual size digits
and optional attribute field, and aligns adjacent cells with ` : ` separators.
`/C=1`, `/C=2` or `/C=4` requests a specific count; the last `/C=` wins. If that
count cannot fit, DIR reports `Requested columns do not fit.` before listing
that DU. Column selection and sorting apply separately to each selected DU.
Use `/C=1 /P` when you want a paged, one-file-per-line listing. The next command
returns to automatic columns unless `/C=` is supplied again.

After listing the selected DUs, DIR prints a separate free-space footer for
each selected drive, for example `B: 94K FREE`. Free space belongs to the drive,
so selecting B3 and B4 produces only one B: footer. This also applies when no
files match. Free space always uses KiB, even with `/Z=S` or `/Z=E`; file counts and
selected-file totals remain separate for each DU. DIR restores your original
drive and user when finished.

It will not display or
filter dates, timestamps or wheel-protection attributes in 1.0.

```text
DIR [options] [location:filespec[attribute-expression]]
```

Omitting the location uses the current drive/user. Omitting the filespec uses
`*.*`. To select the transient explicitly, use `:DIR` or `.DIR`; automatic
handoff from resident DIR is still pending. The examples below describe the
implemented transient behavior.

##### Selecting locations and files

```text
DIR *.COM
DIR B7:*.COM
DIR B[3-5]:*.COM
DIR B[-]:*.COM
DIR [A0,B[3-5],C[4,5,9],5]:*.COM
```

`B[-]:` selects all users on B:. A bare user term such as the final `5` in the
last example inherits the drive that was current when DIR began. Selector
brackets belong to the location; brackets after the filespec are attribute
qualifiers. `[*]` is not an alias for all users.

Wildcards retain the resident bounded rules described above. Extended selectors
do not change filename matching.

##### Selecting files by attributes

| Qualifier | Matches |
| --- | --- |
| `[$RO]` | Read-only files |
| `[$RW]` | Writable files |
| `[$SYS]` | System files |
| `[$DIR]` | Files without SYS set |
| `[$ARC]` | Files with ARC set |

`$R/O` and `$R/W` are aliases for `$RO` and `$RW`. Expressions use `!` for NOT,
`+` for AND and comma for OR, with precedence NOT, AND, then OR:

```text
DIR *.COM[$ARC+!$SYS]
DIR *.DOC[$RO,$SYS]
DIR *.*[!$ARC]
```

These select ARC-marked non-SYS `.COM` files, `.DOC` files with RO or SYS set,
and files with ARC clear, respectively. Qualifiers select files without changing
their attributes. They do not accept size/date queries, parentheses or `$WHL`.

SYS files are hidden by default. An explicit attribute predicate replaces that
default suppression: any SYS file satisfying the predicate is displayed. For
example, `[$RW]` also includes writable SYS files; `[$RW+!$SYS]` excludes them.
Predicates such as `[$SYS]` or `[$SYS,$RO]` display their matches rather than silently
applying the default suppression.

##### Display and sorting options

Options are case-insensitive. `/A` and `/P` may be repeated harmlessly. For
value-bearing size, column and sort options, the last value wins.

| Option | Meaning |
| --- | --- |
| `/A` | Display the three-character SYS/RO/ARC field |
| `/P` | Pause after each screenful |
| `/Z` or `/Z=K` | Display allocated kilobytes; the default |
| `/Z=S` | Display size in allocated record units |
| `/Z=E` | Count physical directory entries used |
| `/C=1`, `/C=2`, `/C=4` | Request that many columns |
| `/S=N`, `/S=N+`, `/S=N-` | Sort by name ascending or descending |
| `/S=T`, `/S=T+`, `/S=T-` | Sort by extension ascending or descending |
| `/S=Z`, `/S=Z+`, `/S=Z-` | Sort by size ascending or descending |
| `/S=U` | Keep native directory-search order |

Name ascending is the default sort. Size sorting uses a numeric size metric,
not the printed size text; changing `/Z=` does not change the sorting key.
`/S=U+` and `/S=U-` are invalid. Other invalid values include `/C=3`, `/Z=X`
and `/S=Q`.

The attribute field is always three positions, **SRA**. A clear bit displays
`-`: `---` means none set, `-R-` means read-only, and `S-A` means SYS plus ARC.
`/A` displays attributes; it does not select ARC files or make SYS visible by
itself. A selector does not turn on `/A` automatically.

For example, this planned command selects ARC-marked non-SYS `.COM` files,
displays attributes and lists the largest first:

```text
DIR /A /S=Z- B7:*.COM[$ARC+!$SYS]
```

Size is always displayed. Automatic layout chooses the greatest supported
column count that fits: four, then two, then one. An explicit `/C=` request
that will not fit reports an error; DIR does not silently reduce it.

Here is an illustrative one-column listing; names and sizes are examples:

```text
A0>:DIR /A /C=1
A: COPY     COM    9K  --A
A: README   TXT    1K  ---
A: STAT     COM    7K  -R-
3 FILES, 17K TOTAL, 116K FREE
A0>
```

##### Paging, summaries and multiple user areas

Paging is off unless `/P` is supplied. At a page pause, Space or Return displays
the next page; Ctrl-C aborts the listing and restores the caller's DU/context.
DIR never changes file attributes or directory entries.

Each summary counts only selected files. Per-file size and selected-file TOTAL
use the same `/Z=` unit. A single-DU summary also reports the drive's free space;
`1 FILE` uses singular wording. No matches reports `NO FILE`.

For multi-DU selectors, DIR lists and sorts each DU separately, with a heading:

```text
B3:
B: BAR      COM   8K : FOO      COM   6K
2 FILES, 14K TOTAL

B4:
B: TEST     COM   4K : UTIL     COM   7K
2 FILES, 11K TOTAL

B: 25K SELECTED, 94K FREE
```

The example uses illustrative values. Free space belongs to the drive, not to
an individual user area, so it is reported once per selected drive rather than
repeated after every DU. An empty DU does not stop later selected DUs. DIR does
not merge all DUs into one listing or sort across them.

The default transient presentation is name-sorted, with K sizes, attributes
hidden, paging off, automatic columns and summaries on. Precise record/extent
accounting and terminal geometry will be qualified before release.

#### 4.2 ERA — Erase Files

Erases one or more files from the current or specified drive/user area.

`ERA` is available as both a resident command and a transient program. The
resident version supports the standard CP/M 2.2 `ERA` syntax:

    ERA filespec
    ERA DU:filespec

Examples:

    A>ERA OLD.TXT
    A>ERA *.BAK
    A>ERA B:OLD.COM
    A>ERA B3:*.TMP

The file specification may contain the standard CP/M `?` and `*` wildcard
characters. When wildcards are used, all matching files are erased.

Resident ERA validates the complete filespec before selecting the target DU or
erasing anything. It uses COPY's bounded wildcard rules: `F?*.DAT` and
`F***.DAT` are valid; `F*A.DAT`, `F**?.DAT`, and overlong 8.3 names report
`Invalid filespec.` rather than being truncated or expanded to a broader match.
Compound DU selectors and attribute qualifiers currently report
`Selection not supported by resident ERA.` and erase nothing. Their confirmation
and protection behavior will be implemented separately.

##### Planned transient ERA.COM

The following interface is the agreed target for the expanded ERA.COM. It is
not yet implemented; today's resident/basic transient command does not offer
these options. The implementation contract is recorded in
[ERA Specification](../engineering/ERA%20Specification.md).


`ERA` removes files from disk.

BetterCP/M ERA extends the traditional CP/M command with multi-DU selection, attribute selection, confirmation controls, read-only protection, and an optional destructive erase.

Basic syntax:

```text
ERA [options] filespec[attributes]
```

Examples:

```text
ERA OLD.DOC
ERA *.BAK
ERA B[-]:*.DOC
ERA B[-]:*.DOC[$ARC]
```

---

##### Ordinary erase

For one exact file:

```text
ERA TOM.DOC
```

ERA asks:

```text
TOM.DOC - Erase? Y/N
```

For a set of files, ERA shows what it intends to erase before doing anything:

```text
THE FOLLOWING FILES WILL BE ERASED:

OLD1.BAK     OLD2.BAK     TEST.BAK     TEMP.BAK
SAVE.BAK     JUNK.BAK

6 FILES, 27K TOTAL

ERASE THESE FILES? Y/N
```

Large lists are displayed in multiple columns and paged automatically:

```text
MORE -- Space/ENTER for next page.
```

---

##### Selecting files

ERA supports BetterCP/M DU selectors:

```text
ERA B[1,3,8-10]:*.DOC
ERA B[-]:*.BAK
ERA [A0,B[3-5],C[-]]:*.TMP
```

It also supports attribute qualifiers:

```text
ERA *.DOC[$ARC]
ERA *.DOC[$SYS+$ARC]
ERA *.DOC[$RO+$ARC]
```

Attribute operators are:

```text
!    NOT
+    AND
,    OR
```

Examples:

```text
[$ARC+!$SYS]
[$RW,$RO]
```

---

##### Protected files

ERA deliberately protects SYS and read-only files.

A normal broad erase does not casually erase protected files.

To select SYS files deliberately:

```text
ERA *.DOC[$SYS]
```

To select archived SYS files:

```text
ERA *.DOC[$SYS+$ARC]
```

Read-only files require additional authorization.

To select them:

```text
ERA *.DOC[$RO]
```

To authorize their erasure without the read-only protection step:

```text
ERA /R *.DOC[$RO]
```

`/Y` does **not** imply `/R`.

That distinction is deliberate.

---

##### Options

###### `/D` — destructive erase

```text
ERA /D SECRET.DAT
```

overwrites the file's allocated data with zeroes and then destroys the residual directory metadata.

For multiple files ERA warns:

```text
THE FOLLOWING FILES WILL BE DESTRUCTIVELY ERASED:
```

and finally:

```text
DESTRUCTIVELY ERASE THESE FILES? THIS IS UNRECOVERABLE. Y/N
```

Destructive erase is transient-only. It is not described as cryptographic secure erase. If a data overwrite fails, directory entries remain identifiable, but file data may be partially zeroed. Only successful overwrite and directory scrubbing count as destructive erasure.

---

###### `/Y` — assume Yes

```text
ERA /Y *.BAK
```

performs the operation without the manifest or ordinary confirmation prompts. It also skips RO files unless `/R` authorizes their erasure, and never pauses for failure recovery.

Useful in SUBMIT files.

`/Y` does not override read-only protection.

To erase deliberately selected RO files unattended:

```text
ERA /Y /R *.BAK[$RO]
```

---

###### `/R` — allow read-only erase

```text
ERA /R *.BAK[$RO]
```

authorizes erasure of selected read-only files.

Without `/R`, explicitly selected read-only files require a separate per-file authorization. Under `/Y`, they are skipped instead. `/R` does not broaden the selector.

---

###### `/Q` — quiet

```text
ERA /Q *.BAK
```

suppresses the filename listing and ordinary informational output, but does not suppress required interaction.

Thus the command still asks:

```text
ERASE THESE FILES? Y/N
```

For fully unattended quiet operation:

```text
ERA /Y /Q *.BAK
```

---

###### `/C` — confirm each file

```text
ERA /C *.DOC
```

first performs the ordinary group confirmation, then asks about each erasable file:

```text
BOB.TXT Y/N
FRED.COM Y/N
```

Protected files which ERA is not authorized to erase are skipped rather than turned into ordinary `/C` questions.

With `/R`, selected RO files participate normally in `/C`. `/Y` suppresses `/C` confirmations; `/Q` does not.

---

##### Errors

If an erase operation fails interactively:

```text
ERA TOM.DOC - Failed. R/S/A/?
```

Enter:

```text
R    Retry
S    Skip
A    Abort all
?    Show help
```

Entering `?` displays:

```text
R Retry, S Skip, A Abort all.
```

and repeats the prompt.

With `/Y`, ERA never pauses for this recovery menu; it reports the failed file, skips it, and continues when safe.

---

##### Completion summary

ERA finishes with a compact summary:

```text
12 FILES ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

For destructive erase:

```text
12 FILES DESTRUCTIVELY ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

`FREED` is actual allocated disk space released, not logical file length.

`/Q` suppresses this normal summary. Zero-valued categories are omitted; skipped and failed files contribute nothing to `FREED`. No qualifying files reports `NO FILE` without confirmation.

---

##### Archiving files and then deleting the originals

ARC denotes changed since last backup. The following cleanup selects files whose ARC bit is set; it does not prove those files were copied successfully.

After confirming every selected file was successfully copied, the planned cleanup sequence is:

```text
COPY B[-]:*.*[$ARC] D0:
ERA    B[-]:*.*[$ARC]
ERA    B[-]:*.*[$SYS+$ARC]
ERA /R B[-]:*.*[$RO+$ARC]
```

The separate ERA commands are intentional.

ERA's SYS and RO protections are not weakened merely to make every protected case fit into one command line.

---

##### Backing up files while retaining the originals

The convenient form is:

```text
COPY /BACKUP B[-]:*.DOC[$ARC] D0:
```

`/BACKUP` clears ARC on both source and destination only after successful copy/close and any requested verification. Add `/V` when verification is wanted; `/BACKUP` does not imply it.

A future STAT ARC-clearing operation could provide a manual source-side workflow. The following STAT syntax is proposed and is not currently implemented:

```text
COPY B[-]:*.DOC[$ARC] D0:
STAT B[-]:*.DOC[$ARC] !$ARC
```

This would clear source ARC only, unlike `/BACKUP`, which clears source and destination ARC. Use such a manual step only after checking every selected source was successfully copied; a partial or skipped batch must not be followed by clearing the entire source selection.

This illustrates a broader BetterCP/M design principle: the utilities expose sufficiently general primitives that higher-level workflows can be composed from ordinary commands.

#### 4.3 REN — Rename Files

Resident `REN` renames files in place:

    REN template=source

Examples:

    REN NEW.TXT=B3:OLD.TXT
    REN *.TXT=B[-]:*.DOC
    REN X?*.BAK=[A3,B5]:*.DOC[$RW]

The source accepts the shared DU selectors, bounded wildcards and attribute
expressions. The template must contain only a filename pattern, with no drive
or user qualifier. Each result remains in its source DU; use COPY or MOVE to
change locations.

Template literals replace the corresponding filename positions. `?` copies
one source position, and a terminal `*` copies the remainder of that field.
Name and extension are separate fields. Repeated terminal stars are equivalent
to one star; characters following a star run are invalid. The historical `_`
separator is also accepted when no `=` is present.

Before renaming anything, REN checks the complete selection. Invalid generated
names, duplicate targets within a DU, existing target files, and read-only
files or drives reject the operation. Another selected source is also an
existing target: rename chains and swaps are rejected. Identical target names
in different DUs are permitted. A file mapped to its own name is unchanged.
System files are included unless an attribute expression excludes them.

REN preserves contents and attributes and restores the caller's DU. An
unexpected failure during execution stops the command; previously completed
renames are not rolled back.

##### Transient REN

The extended transient REN interface remains to be finalized and implemented.


#### 4.4 TYPE — Display a File

Displays the contents of a text file on the console.

`TYPE` is available as both a resident command and a transient program. The
resident version supports the standard CP/M 2.2 `TYPE` syntax:

    TYPE filespec
    TYPE DU:filespec

Examples:

    A>TYPE README.TXT
    A>TYPE PROGRAM.ASM
    A>TYPE B:NOTES.TXT
    A>TYPE B3:README.TXT

`TYPE` sends the contents of the specified file to the console. The command is
intended primarily for text files; displaying a binary file can produce
unreadable output or terminal control characters.

The BetterCP/M resident `TYPE` also supports paged display, allowing long files
to be viewed one screen at a time.

In addition to the above, the transient `TYPE.COM` provides extended display
functions.

##### Transient TYPE Syntax

[TBD — final `TYPE.COM` syntax and options will be added when the BetterCP/M
1.0 transient TYPE interface is finalized.]

#### 4.5 USER — Select User Area

Selects the current user area.

Syntax:

    USER number

where `number` is a user area from 0 through 31.

Examples:

    A>USER 3
    A3>USER 17
    A17>

BetterCP/M also permits the user area to be selected directly by entering the
user number followed by a colon:

    A>3:
    A3>

or together with a drive:

    A3>B17:
    B17>

`USER` is retained as a resident command for compatibility with conventional
CP/M usage. There is no separate transient `USER.COM`.


#### 4.6 COPY — Copy Files

Copies one or more files to another file, drive, or user area.

`COPY` is available as both a resident command and a transient program. Both
versions accept either source-first or destination-first syntax:

    COPY source destination
    COPY destination=source

Examples:

    A>COPY README.TXT README.BAK
    A>COPY README.TXT B:
    A>COPY *.COM B:
    A>COPY A3:*.ASM B17:
    A>COPY B:README.TXT=README.TXT
    A>COPY B:=*.COM

The two syntax forms are equivalent. When the destination does not specify a
new filename, the source filename is retained.

Wildcards may be used to copy groups of files. Drive and user-area
specifications may be used with the source and destination without changing
the current drive/user.

The source files remain unchanged after a successful copy.

In addition to the above, the transient `COPY.COM` provides extended
file-copying functions while retaining both syntax forms.

##### Transient COPY Syntax

`COPY.COM` accepts destination wildcard templates as well as source wildcards:

    COPY C3:*.DOC=A4:*.COM
    COPY C3:X?*.BAK=A4:FOOBAR.COM

The second example creates `XOOBAR.BAK`. Destination literals replace the
corresponding source positions, `?` retains one source position, and a terminal
`*` retains the remainder of that filename field.

COPY.COM also accepts extended DU selectors on the source, with one destination:

    :COPY [A0,B[5-7],C[3,5,6],5]:*.COM D3:
    :COPY [A[-],B[-],C[-]]:*.COM D0:

The final user-only `5` inherits the caller's original drive. Sources are
collected in drive/user order, with names sorted within each DU. Repeated DU
selections do not repeat files. The destination cannot be a DU set.

Preflight covers the combined source set. Equal generated destination names
from different source locations reject the entire batch, even with `/O`.
A destination that overlaps any selected source also rejects it. An unavailable
source drive or a combined selection exceeding 64 files stops before writing.
A selected DU with no matches contributes no files; if no DU has a match,
COPY reports `NO FILE`.

Global options may precede or follow the operands, or occur in both groups:

```text
COPY /V /B B1:*.COM C0:
COPY /V C0: = B1:*.COM /B
```

Whitespace around `=` is optional. Options between source and destination are
not accepted. Leading and trailing groups share the same invocation-wide
policy; `/O` and `/S` conflict even when supplied in different groups.

| Option | Meaning |
| --- | --- |
| `/O` | Replace existing writable destination files. |
| `/S` | Skip existing writable destination files. |
| `/B` | Run without collision prompts. See section 5.7. |
| `/V` | Reopen and compare source and destination records after copying. |

`/O` and `/S` cannot be combined. `/V` and `/B` may be combined with either. Read-only
destinations are never overwritten; they report `READ ONLY`, fail that file,
and allow processing to continue.

Without `/B`, `/O` or `/S`, an existing writable destination prompts:

    [Destination exists. Overwrite? Y/N/O/S/R/?]

`Y` replaces that file; `N` skips it. `O` replaces this and subsequent writable
collisions; `S` skips this and subsequent collisions. `?` displays help and
repeats the prompt. The O/S choice lasts only for the current COPY invocation.
At a collision prompt, Ctrl-C aborts COPY, preserving completed earlier copies
and the existing destination.

`R` asks for `New Name:` in the same destination DU. Enter a bare exact 8.3
filename, without wildcards or a DU qualifier. Invalid names reprompt. A name
that conflicts with a selected source or another planned batch destination
also reprompts without writing. Blank input returns to the collision prompt;
Ctrl-C aborts COPY. If the new name already exists, normal collision handling
applies to that name, including read-only protection.

During copying and `/V` comparison, COPY checks for Ctrl-C between 128-byte
records. Ctrl-C removes the current incomplete or unverified destination,
preserves completed earlier files, restores the caller's DU and DMA, and returns
to the prompt. A disk operation already in progress finishes before the next
check. Other keys during transfer are ignored; `/B` does not disable Ctrl-C.

With `/V`, COPY verifies every 128-byte record and requires matching logical
ends before applying attributes. A verification failure prompts `R/S/?`:
`R` retries from the beginning, `S` removes the failed destination and continues,
and `?` displays help. Ctrl-C removes the failed destination and aborts COPY.
With `/B`, failure removes the destination and continues without prompting or
automatic retry. SUBMIT alone retains interactive verification prompts.

Before copying, the transient checks the complete mapping. Duplicate
destinations, exact self-copy, destinations overlapping selected sources, and
invalid generated names reject the operation without changing a destination.
`/O` cannot override these checks. The current transient limit is 64 matched
files; a larger batch reports `COPY BATCH TOO LARGE` before writing.

Each successful transient copy reports its source, destination, and allocated
space on the destination disk:

```text
B1:FOO.COM -> D0:FOO.COM [2K]
```

`K` means 1024 bytes. The size includes allocation-block rounding; an empty file
reports `0K`. For batches selecting more than one file, COPY reports nonzero
copied, skipped, and failed totals. Only successful copies contribute to the
allocation total:

```text
3 FILES COPIED [18K]
1 FILE SKIPPED
1 FILE FAILED
```

These extended forms require `COPY.COM`. Use `:COPY` or `.COPY` to select it
explicitly while automatic resident-to-transient handoff remains pending.


##### COPY attribute selection and backup

**Source attribute selection, destination attribute qualifiers, and /BACKUP
are implemented in transient COPY.COM.**

For example, this supported command selects ARC-marked files across all B:
users and copies them to D0:, preserving attributes without changing source ARC:

```text
COPY /B /V B[-]:*.COM[$ARC] D0:
```

Source filtering takes place before global mapping checks and the 64-file limit.
No matches reports `NO FILE`. Invalid expressions fail before writes.

Command-wide options use `/`; qualifiers attached to an operand use brackets.
For example, the planned backup syntax is:

```text
COPY /V /BACKUP B[-]:*.COM[$ARC] D0:
```

This selects `.COM` files across all user areas on B: **whose ARC bit is set**,
copies them to D0:, verifies their contents, then clears ARC on both the source
and destination after success. `/B` continues to mean noninteractive batch;
`/BACKUP` is a separate option.

ARC means “changed since the last completed backup.” Ordinary COPY preserves
ARC and leaves the source unchanged. `[$ARC]` only selects files; it does not
change their attributes. `/BACKUP` alone does not filter files by ARC.

Source attribute qualifiers select files:

| Qualifier | Selects |
| --- | --- |
| `[$RO]` | Read-only files |
| `[$RW]` | Writable files |
| `[$SYS]` | System files |
| `[$DIR]` | Files without SYS set |
| `[$ARC]` | Files with ARC set |

Use `!` for NOT, `+` for AND and comma for OR. AND binds more tightly than OR:
`[$ARC+!$SYS]` selects ARC-marked files without SYS; `[$RO,$SYS]` selects files
with RO or SYS. `$R/O` and `$R/W` are aliases for `$RO` and `$RW`.

Destination qualifiers set the completed copy's attributes after the copy and
requested verification succeed:

```text
COPY A0:*.COM D0:[$RW,!$ARC]
```

This requests writable destination copies with ARC clear. Unspecified attributes
are preserved. Opposite assignments such as `[$RO,$RW]` are invalid before writes; repeated
equivalent assignments are harmless. Destination qualifiers are comma-separated
state assignments, not Boolean expressions with AND or OR. Existing
read-only destinations remain protected, even when `[$RW]` is requested.

`/BACKUP` takes precedence over destination ARC settings and clears ARC after
success, including when the destination says `[$ARC]`. Skipped, failed and
aborted copies retain source ARC. If data copying succeeds but an attribute
update fails, COPY reports incomplete backup-status handling.

If a source read or destination write/close fails, COPY reports the file and
removes its incomplete destination before continuing to later files. Disk full
stops the batch. If removal fails, `INCOMPLETE DESTINATION CLEANUP FAILED`
means the incomplete file may remain; COPY stops. Earlier completed copies
remain available, and the failed file retains its source ARC status.

Both operand orders support source and destination qualifiers:

```text
COPY B2:*.DOC[$ARC] C0:[!$ARC] /V
COPY /V C0:[!$ARC]=B2:*.DOC[$ARC]
```

Leading and trailing slash options have the same command-wide scope. They do
not become destination options merely by appearing at the end.

Automatic ARC setting when a file changes is a separate proposal. Until that
exists, the user or another tool must explicitly maintain ARC status; do not
assume this facility automatically discovers all changed files.


#### 4.7 MOVE — Move Files

Moves one or more files to another name, drive, or user area.

`MOVE` is available as a resident command and supports syntax parallel to
`COPY`:

    MOVE source destination
    MOVE destination=source

Examples:

    A>MOVE README.TXT B:
    A>MOVE *.BAK B:
    A>MOVE A3:*.ASM B17:
    A>MOVE B:README.TXT=README.TXT
    A>MOVE B:=*.COM

Wildcards may be used to move groups of files. Drive and user-area
specifications may be used with the source and destination without changing
the current drive/user.

When the source and destination are on different drives or in different user
areas, BetterCP/M copies each file to its destination and removes the source
only after the destination has been successfully written and closed.

Where possible, a move within the same drive/user area is performed by
renaming the file rather than copying its contents.

[TBD — determine whether BetterCP/M 1.0 will also provide a transient
`MOVE.COM` and, if so, document its additional functions here.]

#### 4.8 CLS — Clear Screen

Clears the console screen and returns the cursor to the upper-left corner.

Syntax:

    CLS

Example:

    A>CLS

`CLS` is supplied as a resident command by `RCP.CPX`. A matching transient
`CLS.COM` is also provided so that the command remains available when the
resident command package is not loaded.

The exact screen-clearing operation is provided by the active console
environment and may differ between supported platforms.

#### 4.9 VER — Display Version Information

Displays BetterCP/M version information.

Syntax:

    VER

Example:

    A>VER

`VER` is supplied as a resident command by `RCP.CPX`. It identifies the
running BetterCP/M system and its release version.

[TBD — expand this entry when the final BetterCP/M 1.0 VER display and any
additional version-reporting options are finalized.]

#### 4.10 SAVE — Save Memory to a File

Saves the contents of the Transient Program Area to a file.

`SAVE` is a core resident command and supports the standard CP/M 2.2 syntax:

    SAVE pages filespec

where `pages` is the number of 256-byte pages to save, beginning at address
0100H.

Examples:

    A>SAVE 10 TEST.COM
    A>SAVE 40 B:PROGRAM.COM
    A>SAVE 20 B3:IMAGE.COM

For example:

    A>SAVE 10 TEST.COM

writes 10 pages, or 2560 bytes, beginning at 0100H to `TEST.COM`.

`SAVE` is implemented directly by the BetterCP/M command processor rather than
as a transient program. A transient `SAVE.COM` could overwrite the memory that
SAVE is intended to preserve.

BetterCP/M extends the conventional command to permit drive/user-qualified
destination file specifications.

#### 4.11 GET — Load a File into Memory

Loads a file into memory without executing it.

Syntax:

    GET filename
    GET address filename

With one operand, `GET` loads the file beginning at address 0100H:

    A>GET PROGRAM.COM

An optional hexadecimal address specifies another load address:

    A>GET 8000 DATA.BIN

Leading zeroes in the address are optional.

`GET` returns to the command prompt after loading the file. It does not execute
the loaded image. The loaded program or data can subsequently be examined or
modified with `PEEK` and `POKE`, or executed with `GO` or `JUMP`.

`GET` rejects a load that would overwrite memory required by the active
BetterCP/M command environment.


#### 4.12 GO — Execute at 0100H

Transfers control to address 0100H.

Syntax:

    GO [command tail]

Examples:

    A>GO
    A>GO INPUT.DAT

`GO` is equivalent to:

    JUMP 0100

Before transferring control, BetterCP/M establishes the normal CP/M transient
program environment, including the stack, DMA address, page-zero vectors,
command tail, and default FCBs.

`GO` is useful for executing a program image previously loaded or modified in
memory with commands such as `GET` and `POKE`.


#### 4.13 JUMP — Execute at an Address

Transfers control to a specified memory address.

Syntax:

    JUMP address [command tail]

where `address` is a hexadecimal address from 0000H through FFFFH.

Examples:

    A>JUMP 100
    A>JUMP 8000
    A>JUMP 100 INPUT.DAT

Before transferring control, `JUMP` establishes the normal CP/M transient
program environment, including the stack, DMA address, page-zero vectors,
command tail, and default FCBs.

`GO` is equivalent to `JUMP 0100`.

If no address is supplied, or the address is invalid, `JUMP` reports an error
and returns to the command prompt.


#### 4.14 PEEK / P — Display Memory

Displays the contents of memory in hexadecimal and ASCII form.

`P` is an abbreviation for `PEEK`.

Syntax:

    PEEK
    PEEK address
    PEEK first last

or:

    P
    P address
    P first last

Examples:

    A>PEEK 100
    A>P 8000
    A>PEEK 100 1FF

With one address, `PEEK` displays 256 bytes beginning at that address. With two
addresses, it displays the inclusive range from `first` through `last`.

With no address, the first invocation begins at 0100H. Subsequent invocations
continue from the byte following the previous display.

During a paged display:

    SPACE  .  >     display the next page
           ,  <     display the previous page
       Ctrl-C       return to the command prompt

Addresses are hexadecimal and may be written without leading zeroes. The
display does not wrap from FFFFH to 0000H.


#### 4.15 POKE — Modify Memory

Stores bytes or text directly into memory.

Syntax:

    POKE address byte [byte ...]
    POKE address "text
    POKE address byte [byte ...] "text

where `address` and byte values are hexadecimal.

Examples:

    A>POKE 100 C3 00 80
    A>POKE 200 "Hello
    A>POKE 300 0D 0A "BetterCP/M

Bytes are stored consecutively beginning at the specified address. A quotation
mark introduces literal text; all remaining characters on the command line are
stored as text.

`POKE` validates the address and all hexadecimal byte operands before modifying
memory. If an operand is invalid, no partial modification is performed.

`POKE`, together with `GET`, `PEEK`, `GO`, `JUMP`, and `SAVE`, provides a small
resident set of memory inspection, modification, loading, execution, and saving
commands.

### 5. Batch Processing
5.1 SUBMIT 5.2 SUB Files 5.3 Parameters and Substitution 5.4 XSUB 5.5 Batch Execution and Termination 5.6 Examples

#### 5.7 COPY in Batch Files

A SUBMIT file executes a sequence of commands; it does not automatically make
those commands noninteractive. A COPY command in a SUBMIT file may pause for
an overwrite response. Use `/B` explicitly when the command must run without
collision prompts.

For example, a SUBMIT file may contain:

    COPY B1:*.DAT C3: /B

If a writable destination exists, `/B` alone reports `FILE EXISTS`, counts
that file as failed, and continues with the next source. It does not overwrite
or silently skip that file. New destination files are copied normally.

To choose a collision policy in advance:

    COPY B1:*.DAT C3: /B /O
    COPY B1:*.DAT C3: /B /S

The first command replaces existing writable destinations. The second skips
existing writable destinations. Both copy files whose destinations do not
already exist. A read-only destination fails that file and is preserved in
all three forms; processing continues with later files.

`/B` works equally at the command prompt. It does not change SUBMIT itself,
make the whole script noninteractive, or suppress prompts from other programs.
The mapping and capacity checks in section 4.6 still apply before any writes.

### 6. CPX and RSX Extensions
6.1 BetterCP/M Extensions 6.2 CPXs 6.3 Listing CPXs 6.4 Loading and Unloading CPXs 6.5 RSXs 6.6 Listing RSXs 6.7 Loading and Unloading RSXs 6.8 Extension Order and Memory Use 6.9 Warm Boot and Extension Persistence 6.10 Recovery
This should be user-oriented throughout.

### 7. Configuring BetterCP/M
7.1 CONFIG 7.2 Active and Saved Configuration 7.3 Applying and Saving Changes 7.4 System Devices 7.5 Keyboard and Console Settings 7.6 Printer and List-Device Settings 7.7 Serial Configuration 7.8 Disk Configuration 7.9 Startup Command 7.10 Platform-Specific Options 7.11 Configuration Recovery
This chapter will need adjustment to the final CONFIG implementation.

### 8. Disk Operations
8.1 DUP — Disk Utility Program 8.2 Disk Formats 8.3 Inspecting Disks 8.4 Preparing and Formatting Media 8.5 Copying Disks 8.6 Other DUP Operations 8.7 Unsupported Formats and Operations 8.8 Safe Media Handling
Again, final DUP functionality determines the exact subsections.

### 9. Date and Time
9.1 BetterCP/M Clock Support 9.2 TIME 9.3 Displaying the Date and Time 9.4 Setting the Date and Time 9.5 Read-Only Clock Providers 9.6 P2DOS Compatibility
Probably a relatively short chapter.

### 10. Installing BetterCP/M
10.1 BetterCP/M Distribution Media 10.2 Preparing a System Disk 10.3 Installing BetterCP/M with SYSGEN 10.4 Preserving Files During Installation 10.5 Booting the Installed System 10.6 Installation Problems and Recovery
This is installation, not system generation.

### 11. Messages and Troubleshooting
11.1 Command Errors 11.2 File and Disk Errors 11.3 Configuration Errors 11.4 CPX/RSX Errors 11.5 Startup and Boot Problems 11.6 Recovery Procedures

## Appendixes
A. Command Summary B. Command-Line Editing Keys C. File Attributes D. Control Characters E. BetterCP/M 1.0 Compatibility Notes F. Error Messages — possibly instead of Chapter 11 depending on size G. Glossary — only BetterCP/M/CP/M terminology actually worth defining


#### 4.16 STAT — Extended DU File Inspection

STAT accepts extended DU selectors when reporting file statistics:

    STAT B[3,5]:*.COM
    STAT B[5-3]:*.DAT $S
    STAT B[-]:*.COM
    STAT [A0,C[3,5,7-11],5]:*.DAT

A drive's bracketed list selects users on that drive. `[-]` selects users
0–31; open endpoints and descending ranges are accepted. Compound lists
combine locations. A user-only term inherits the caller's original drive;
a drive-only term inherits the original user. Duplicate locations are visited
once, in drive-major/user-minor order. `[*]` is invalid as a user selector.
Filename wildcards retain the bounded 8.3 rules.

Each location has a DU heading, and every file result includes its DU. Empty
locations report `File Not Found`. An unavailable drive is identified and
inspection continues with the remaining locations. The caller's drive and
user are restored on completion.

An explicit filename or pattern is required after an extended selector.
`$S` adds logical file size. Extended selectors currently support inspection
only: attribute options and drive-wide commands such as `DSK:` and `=R/O`
are rejected. Conventional single-DU STAT commands retain their existing
behavior and output.

### Utility version identification

Use `/VER` by itself to identify a BetterCP/M utility:

```text
A0>DIR /VER
BetterCP/M DIR 1.0 (Resident, RCP Build 001)
A0>:DIR /VER
BetterCP/M DIR 1.0 (Build 002)
```

The resident line identifies the installed RCP package. The force-transient `:DIR` form identifies DIR.COM. Transient utilities omit “Transient” from their output. Other examples include `STAT /VER`, `COPY /VER`, and `TIME /VER`.

Version identifies the release; build identifies its particular executable revision. Each utility has an independent build sequence, while resident commands share the RCP sequence. Build numbers continue across version changes and do not advance merely because the same source is rebuilt.

`/VER` prints the identity and exits without carrying out the command. Do not combine it with filespecs or other options; such combinations report `Invalid /VER usage.` Existing CPX/RSX `/V` reports facility versions and remains a separate option. This convention applies to BetterCP/M-owned utilities, not adopted third-party programs.
