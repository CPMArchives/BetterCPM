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
3.1 The BetterCP/M Prompt 3.2 Entering Commands 3.3 Command-Line Editing 3.4 Command History 3.5 Selecting Drives and User Areas 3.6 Resident and Transient Commands 3.7 CPX Commands 3.8 Command Search and Program Execution 3.9 Terminating Commands and Programs

### 4. Basic Commands
4.1 DIR — Directory 4.2 ERA — Erase Files 4.3 REN — Rename Files 4.4 TYPE — Display a File 4.5 USER — Select User Area 4.6 COPY — Copy Files 4.7 MOVE — Move Files 4.8 CLS — Clear Screen 4.9 VER — Display Version Information 4.10 SAVE — Save Memory to a File 4.11 GET — Load a File into Memory 4.12 GO — Execute at 0100H 4.13 JUMP — Execute at an Address 4.14 PEEK / P — Display Memory 4.15 POKE — Modify Memory
The final ordering is open. Alphabetical may prove better.

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
