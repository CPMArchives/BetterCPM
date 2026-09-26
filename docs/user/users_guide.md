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

In addition to the above, the transient `DIR.COM` provides extended directory
display and file-selection functions. Planned extensions include:

- selection and display by file attributes;
- display of file date and time information where available; and
- selection of files by date and time where supported.

##### Transient DIR Syntax

[TBD — final `DIR.COM` syntax and options will be added when the BetterCP/M
1.0 transient DIR interface is finalized.]

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

In addition to the above, the transient `ERA.COM` provides extended file
selection and erase functions.

##### Transient ERA Syntax

[TBD — final `ERA.COM` syntax and options will be added when the BetterCP/M
1.0 transient ERA interface is finalized.]


#### 4.3 REN — Rename Files

Changes the name or file type of a file.

`REN` is available as both a resident command and a transient program. The
resident version supports the standard CP/M 2.2 `REN` syntax:

    REN newname=oldname
    REN DU:newname=oldname

Examples:

    A>REN NEW.TXT=OLD.TXT
    A>REN PROGRAM.COM=PROGRAM.OLD
    A>REN B:FINAL.ASM=DRAFT.ASM
    A>REN B3:NEW.DAT=OLD.DAT

The old and new names refer to files in the same drive/user area. `REN` changes
the directory entry for the file; it does not copy the file to another drive
or user area. Use `MOVE` when a file is to be moved to another location.

In addition to the above, the transient `REN.COM` provides extended rename
functions.

##### Transient REN Syntax

[TBD — final `REN.COM` syntax and options will be added when the BetterCP/M
1.0 transient REN interface is finalized.]


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

[TBD — additional `COPY.COM` functions and options will be added when the
BetterCP/M 1.0 transient COPY interface is finalized.]


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
