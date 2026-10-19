# BetterCP/M 1.0 User's Guide

---

# Part One

## Chapter 1 — Introduction

### 1.1 What Is BetterCP/M?

BetterCP/M is an enhanced implementation of the CP/M operating system for Z80-based computers. It preserves the familiar CP/M 2.2 operating environment while adding new capabilities that make the system more convenient, flexible, and enjoyable to use.

If you've used CP/M before, you'll feel at home with BetterCP/M. You'll find the familiar command prompt, drive letters, user areas, and `.COM` programs. The commands you already know are still there, and ordinary CP/M applications continue to use the same programming interfaces they've always used.

But BetterCP/M offers considerably more than a conventional CP/M 2.2 system.

The command processor has been enhanced with command-line editing, command history, and more flexible ways of working with files and directories. Many familiar commands have gained additional capabilities, while new commands and utilities make routine operations easier.

BetterCP/M also introduces a system of resident extensions. These allow additional commands and services to be loaded into memory and made available throughout a working session, without requiring modifications to the operating system itself.

Despite these enhancements, BetterCP/M remains recognizably CP/M. Its purpose is not to replace the traditional CP/M environment with something entirely different, but to build upon it.

### 1.2 BetterCP/M and Digital Research CP/M 2.2

BetterCP/M is designed to maintain compatibility with Digital Research's CP/M 2.2, one of the most widely used operating systems of the early microcomputer era.

This compatibility extends beyond the appearance of the command prompt.

BetterCP/M preserves the standard CP/M programming environment, including the BDOS interface, file system conventions, program loading, and other facilities upon which existing CP/M software depends.

For most applications, the operating system should be transparent. A program written for CP/M 2.2 should ordinarily run under BetterCP/M without modification.

There are, however, some important distinctions between BetterCP/M and the original operating system.

BetterCP/M is a new implementation, not simply a patched copy of Digital Research's CP/M. Its internal organization differs in several respects, particularly where additional facilities or greater flexibility are required.

These differences are generally invisible to conventional CP/M applications. BetterCP/M aims to preserve the established programming environment while allowing the operating system itself to evolve.

Compatibility is a fundamental design objective, but it should not be interpreted as a guarantee that every program written for every CP/M computer will work unchanged. Some programs depend on particular hardware, undocumented operating-system behavior, or features supplied by individual manufacturers.

For additional information about compatibility, see Appendix E, *BetterCP/M and CP/M 2.2 Compatibility Notes*.

### 1.3 What's New in BetterCP/M?

BetterCP/M introduces a number of enhancements to the traditional CP/M environment. Some are immediately apparent when using the command prompt; others provide additional capabilities for system configuration, software development, and everyday operation.

**An improved command environment**

The BetterCP/M command processor provides command-line editing and a history of previously entered commands. Instead of retyping a long command after making a mistake, you can recall it, make the necessary correction, and execute it again.

The command environment also supports convenient drive and user-area selection, along with additional ways of locating and executing programs.

**Enhanced commands and utilities**

Familiar commands such as DIR, ERA, REN, and TYPE retain their traditional purposes while offering additional options.

BetterCP/M also supplies more capable file-management utilities, including COPY and MOVE, together with facilities for examining disks, configuring the system, and managing the operating environment.

**Resident extensions**

One of BetterCP/M's most significant additions is its extensible resident environment.

Command Processor Extensions (CPXs) can add commands to the command processor, while Resident System Extensions (RSXs) provide additional services that remain available while other programs execute.

Extensions can be loaded and unloaded as needed, allowing the system to be tailored to different tasks without permanently incorporating every facility into the operating system.

**Improved terminal support**

BetterCP/M provides loadable terminal-monitor facilities supporting several familiar terminal environments, including ADM-3A, VT52, and a supported subset of ANSI/VT100 operation.

These facilities help programs written for different terminal conventions operate on supported BetterCP/M systems.

**System configuration and disk management**

BetterCP/M provides additional facilities for configuring the operating environment, preparing disks, and installing or maintaining system disks.

The available facilities depend in part on the hardware or emulator being used, but the general command environment remains consistent across supported platforms.

**Compatibility with existing CP/M software**

Perhaps the most important feature is what BetterCP/M does *not* require you to change.

You can continue using conventional CP/M applications, programming tools, and file formats while taking advantage of BetterCP/M's additional facilities.

### 1.4 About This Manual

This manual explains how to install, configure, and use BetterCP/M 1.0.

It assumes that you have some familiarity with CP/M or similar command-line operating systems. You need not be an assembly-language programmer or understand the internal workings of the operating system.

The manual is divided into two principal parts.

**Part I — Using BetterCP/M** introduces the operating system and explains its facilities through descriptions, examples, and practical procedures.

You'll learn how to start BetterCP/M, work with drives and files, use the command environment, configure the system, manage resident extensions, and perform common maintenance tasks.

**Part II — Command and Utility Reference** provides detailed descriptions of BetterCP/M's commands and utilities. It is intended primarily for consultation when you need to look up command syntax, available options, or particular operating details.

The two parts complement one another. The introductory chapters demonstrate common operations and refer you to the command reference when more detailed information is needed.

Additional technical documentation is available for readers who want to understand BetterCP/M's architecture, develop software that uses its extended facilities, or adapt the operating system to new hardware.

You don't need those documents to use BetterCP/M. This User's Guide should provide the information necessary for ordinary operation.

Below are **Chapters 2–4 of the BetterCP/M 1.0 User's Guide**, incorporating our latest decisions.

Chapter 2 provides a high-level architectural introduction. Chapter 3 covers getting started without tying the manual to particular machines; platform-specific instructions will be maintained separately. Chapter 4 introduces everyday file and disk operations, leaving complete command syntax and options to the reference section later in the manual.

The chapters follow the friendly, practical style established in the approved Chapter 1. They draw on the existing BetterCP/M User's Guide, with unnecessary implementation details omitted.

---

# Chapter 2 — An Overview of BetterCP/M

BetterCP/M builds upon the familiar organization of Digital Research's CP/M 2.2, but introduces several important changes to the way the operating system is organized and used.

You don't need to understand its internal workings to use BetterCP/M. Nevertheless, a general understanding of how its major components fit together will help you appreciate what the system offers and how its additional facilities work.

This chapter provides that introduction. Readers interested in a more detailed technical discussion should consult the *BetterCP/M Architecture Overview*.

## 2.1 The BetterCP/M Operating Environment

Like conventional CP/M, BetterCP/M provides an environment in which programs can be loaded from disk, executed, and given access to files and peripheral devices.

When the system is ready, it displays a command prompt:

```text
A>
```

From this prompt, you can enter commands, run programs, manage files, and configure the operating environment.

BetterCP/M retains the familiar CP/M conventions of lettered disk drives, numbered user areas, and executable programs with the `.COM` file type.

A program written for CP/M 2.2 ordinarily sees the same operating environment under BetterCP/M. It can access files, communicate with the console, and use the standard CP/M programming services without needing to know which operating system is running.

BetterCP/M extends this environment with additional commands, improved command-line facilities, and resident extensions that remain available while other programs execute.

These additions are designed to work alongside conventional CP/M software rather than require applications to be rewritten.

## 2.2 How BetterCP/M Is Organized

CP/M has traditionally been organized around three principal operating-system components: the Console Command Processor (CCP), the Basic Disk Operating System (BDOS), and the Basic Input/Output System (BIOS).

BetterCP/M retains this basic organization.

**The Console Command Processor (CCP)** provides the command-line environment. It accepts commands from the keyboard, interprets them, and either performs the requested operation or starts a program from disk.

**The Basic Disk Operating System (BDOS)** provides the standard CP/M services used by application programs. These include file operations, console input and output, disk selection, and other operating-system functions.

**The Basic Input/Output System (BIOS)** provides the interface between the operating system and the particular computer on which it runs. It handles the machine-dependent operations needed to communicate with disks, the console, and other devices.

The distinction between BDOS and BIOS is especially important to CP/M's portability. Much of the operating system can remain unchanged when it is adapted to another computer; the BIOS supplies the machine-specific operations.

BetterCP/M also provides two important extension mechanisms:

**Command Processor Extensions (CPXs)** add commands to the command environment.

**Resident System Extensions (RSXs)** provide additional resident services that can remain available while ordinary programs execute.

Together, these components provide the familiar CP/M environment while allowing BetterCP/M to offer capabilities beyond those of the original operating system.

## 2.3 The Command Processor

The command processor is the part of BetterCP/M with which users interact most frequently.

When you enter a command such as:

```text
A>DIR
```

the command processor determines how to carry it out.

Some commands are provided directly by the command environment. Others are supplied by installed CPXs. Still others are ordinary programs loaded from disk.

For example:

```text
A>DIR
A>TYPE README.TXT
A>MYPROG
```

The first two commands perform familiar file operations. The third starts a program named `MYPROG.COM`, assuming it can be found.

BetterCP/M's command processor offers several improvements over the traditional CP/M command environment.

You can edit a command before executing it, recall previously entered commands, and use convenient drive/user specifications.

You can also extend the command processor by loading CPXs. These make additional commands available without requiring the command processor itself to be permanently enlarged.

The distinction between resident and transient commands is normally invisible during everyday use. You enter the command name and its arguments in the usual way.

There are occasions when the distinction matters, however. BetterCP/M allows you to explicitly request a transient program, even when a resident command has the same name.

Chapter 5 explains the command environment in greater detail.

## 2.4 Programs and Memory

Like CP/M 2.2, BetterCP/M provides a region of memory called the **Transient Program Area**, or **TPA**.

This is where ordinary CP/M programs execute.

When you enter the name of a program, BetterCP/M locates its `.COM` file, loads it into memory, and transfers control to it.

For example:

```text
A>ED LETTER.TXT
```

starts the ED editor, provided the program is available.

When the program finishes, control returns to the operating system and the command prompt reappears.

BetterCP/M preserves the conventional CP/M program-loading environment. This allows existing CP/M applications to execute without requiring changes to their normal use of memory or operating-system services.

Resident extensions introduce an additional consideration.

Unlike ordinary transient programs, CPXs and RSXs can remain in memory while other programs execute. This makes their facilities continuously available, but it also means that the memory they occupy is unavailable to transient programs.

Loading an extension therefore involves a tradeoff: additional capabilities in exchange for some reduction in available program memory.

BetterCP/M allows supported extensions to be unloaded when they are no longer needed, releasing their memory for other uses.

For most users, the important point is simple: **the more resident facilities you load, the less memory remains available for ordinary programs.**

Chapter 8 explains how to manage extensions and examine their effect on available memory.

## 2.5 Disks and Files

BetterCP/M retains the familiar CP/M disk and file organization.

Disk drives are identified by letters, beginning with `A:`. Files are identified by names of up to eight characters and optional file types of up to three characters.

For example:

```text
README.TXT
MYPROG.COM
REPORT.DAT
```

As in conventional CP/M, each drive also supports numbered user areas.

BetterCP/M extends the command environment by allowing drive and user-area combinations to be written together.

For example:

```text
B3:
```

identifies drive B, user area 3.

This notation is particularly useful when working with files distributed among several user areas.

BetterCP/M also provides enhanced file-management commands, including facilities for locating, copying, moving, renaming, and examining files.

These commands retain familiar CP/M conventions while offering additional options.

The underlying filesystem remains compatible with conventional CP/M disk organization. BetterCP/M's enhancements do not require ordinary CP/M applications to adopt a new file format.

Chapter 4 explains how to work with drives and files.

## 2.6 Resident Extensions

One of BetterCP/M's distinguishing features is its ability to load additional operating-system facilities into memory.

These facilities are called **resident extensions** because they remain available after the command or program that loaded them has finished.

BetterCP/M provides two principal types.

### Command Processor Extensions

A CPX adds commands to the command processor.

For example, BetterCP/M's standard resident command package provides familiar operations such as DIR, ERA, TYPE, REN, COPY, and MOVE.

Because these commands are resident, they can be invoked without loading a separate transient program each time.

Additional CPXs can be loaded when their commands are needed and unloaded when they are no longer required.

### Resident System Extensions

An RSX provides services that remain available to the operating environment and other programs.

Terminal support is one example.

A terminal-monitor extension can interpret terminal control sequences used by an application and provide the corresponding display operations on the computer's screen.

BetterCP/M includes terminal facilities supporting several familiar terminal conventions, including ADM-3A, VT52, and a subset of ANSI/VT100.

These facilities allow supported applications to use the terminal environment they expect, even when the underlying display hardware differs.

### Managing Extensions

BetterCP/M provides commands for examining, loading, and unloading resident extensions.

Extensions can also be loaded automatically during system startup, allowing you to establish a preferred working environment.

Ordinary warm boots preserve supported resident extensions, so they need not be reloaded every time a program terminates.

Chapter 8 explains how to use and manage extensions. For complete command syntax and options, consult the CPX and RSX entries in the Command Reference.

## 2.7 Hardware Independence

CP/M's separation of the operating system from the hardware-specific BIOS made it possible to run the same operating environment on many different computers.

BetterCP/M retains this approach.

The standard operating-system services and programming environment remain substantially the same across supported machines, while the BIOS supplies the operations needed for each particular platform.

Some facilities necessarily depend on the capabilities of the underlying computer. Disk formats, display behavior, peripheral devices, and certain configuration options may differ between platforms.

BetterCP/M's terminal extensions help bridge some of these differences by providing familiar terminal environments through machine-specific display support.

For users, this means that most commands and programs work in the same general way regardless of the supported platform.

For information about the machines and emulators currently supported, consult the *BetterCP/M Supported Platforms* documentation.

Developers interested in adapting BetterCP/M to additional computers should consult the *BetterCP/M Porting Guide*.

---

# Chapter 3 — Getting Started

Getting started with BetterCP/M is much like getting started with conventional CP/M. Once the operating system has been prepared for your computer, you boot it, wait for the command prompt, and begin working.

The exact steps required to prepare and start BetterCP/M depend on the computer or emulator you're using. Rather than duplicate those instructions here, this chapter describes the general process and introduces the facilities you'll encounter when the system starts.

For installation and boot instructions specific to your computer, consult the *BetterCP/M Supported Platforms* documentation.

## 3.1 Obtaining BetterCP/M

BetterCP/M is distributed as a collection of operating-system files, utilities, and supporting documentation.

The distribution includes the software needed to run BetterCP/M on supported platforms, together with the programs used to configure and maintain the system.

Depending on the platform, the operating system may be supplied as a prepared disk image or as files from which a bootable system can be constructed.

A disk image is a file containing the contents of a disk. Emulators can generally use such images directly, while users of physical Z80 computers may need to transfer the image to suitable media.

BetterCP/M's distribution is organized around a system disk containing the operating system and the programs needed for ordinary operation. Additional utilities may be supplied separately.

The precise contents of the distribution may vary between releases and platforms.

Before preparing a system, make sure you have obtained the files appropriate to your computer. A disk image intended for one machine may not boot on another, even though both machines use the Z80 processor.

The *Supported Platforms* documentation identifies the available distributions and explains how to prepare them.

## 3.2 Preparing Your System

Before booting BetterCP/M, you'll need a supported computer or emulator and a suitable system disk.

For an emulator, preparation generally involves selecting the appropriate machine configuration and attaching the supplied disk image.

For a physical computer, you may need to prepare a floppy disk, configure a storage device, or transfer the system image using equipment appropriate to that machine.

BetterCP/M depends on the BIOS to communicate with the underlying hardware. Consequently, the system image must be appropriate to the computer on which it will run.

You should also consider how you intend to store your own files.

The system disk may have sufficient free space for experimentation, but a separate working disk is often more convenient. Keeping personal files separate from the operating-system distribution also makes it easier to replace or update the system disk.

If you're using physical removable media, it's a good idea to prepare a backup of the original system disk before making configuration changes.

The platform documentation explains any special preparation required for your particular system.

## 3.3 Booting BetterCP/M

Once your system has been prepared, start BetterCP/M using the normal boot procedure for your computer.

During startup, BetterCP/M initializes the operating environment and establishes the configured command processor and resident facilities.

The system can also execute a startup command automatically.

The standard BetterCP/M distribution uses a command equivalent to:

```text
SUBMIT STARTUP
```

This executes the commands contained in `STARTUP.SUB`, allowing the system to establish a preferred working environment.

The supplied startup file initially displays the BetterCP/M identification banner. It can also be customized to perform other tasks, such as loading resident extensions.

When startup is complete, BetterCP/M displays its command prompt:

```text
A>
```

The system is now ready to accept commands.

### Cold Boots and Warm Boots

CP/M distinguishes between two kinds of system startup.

A **cold boot** starts the operating system from its initial state. It establishes the operating environment and performs the configured startup operations.

A **warm boot** returns control to the operating system without repeating the entire cold-start procedure.

In BetterCP/M, an ordinary warm boot preserves supported resident extensions and other system state intended to survive program termination.

The startup command is executed during a cold boot, not during an ordinary warm boot.

This distinction becomes useful when you begin customizing BetterCP/M. For example, an extension loaded during startup can remain available throughout the working session without needing to be loaded again after every program.

Chapter 7 explains how to configure startup commands. Chapter 8 discusses the behavior of resident extensions during warm boots.

## 3.4 The Command Prompt

When BetterCP/M is ready for a command, it displays a prompt identifying the current drive and user area.

The simplest prompt is:

```text
A>
```

This indicates that drive A is selected and the current user area is zero.

If you select another drive, the prompt changes accordingly:

```text
A>B:
B>
```

BetterCP/M also allows you to select a user area directly:

```text
A>5:
A5>
```

The prompt now indicates drive A, user area 5.

You can select a drive and user area together:

```text
A>B3:
B3>
```

This selects drive B, user area 3.

Throughout this manual, examples include the command prompt to show how commands would appear on the screen. You type only the text following the prompt.

For example:

```text
A>DIR
```

means that you type `DIR` and press `RETURN`.

Chapter 4 explains drives and user areas in greater detail.

## 3.5 Your First Commands

Once BetterCP/M displays its prompt, you can begin entering commands.

If you've used CP/M before, many of these will already be familiar.

### Displaying a Directory

Enter:

```text
A>DIR
```

BetterCP/M displays the files in the current drive and user area.

You can also examine another drive without selecting it:

```text
A>DIR B:
```

Or examine a particular drive and user area:

```text
A>DIR B3:
```

### Displaying a Text File

To display the contents of a text file, use TYPE:

```text
A>TYPE README.TXT
```

The file's contents are displayed on the console.

TYPE is useful for examining documentation, program listings, command files, and other ordinary text files.

### Copying a File

BetterCP/M provides a COPY command for copying files between drives and user areas.

For example:

```text
A>COPY README.TXT B:README.TXT
```

copies `README.TXT` from the current drive and user area to drive B.

The original file remains unchanged.

### Running a Program

To execute a transient program, enter its name without the `.COM` extension.

For example:

```text
A>MYPROG
```

starts `MYPROG.COM`, provided BetterCP/M can locate it.

If the program accepts command-line arguments, enter them after its name:

```text
A>MYPROG INPUT.DAT
```

The arguments are passed to the program using the conventional CP/M command-line environment.

### Displaying System Information

BetterCP/M provides the VER command for displaying version information.

```text
A>VER
```

This identifies the running BetterCP/M system.

These examples are enough to begin exploring the command environment. Chapter 5 introduces its additional capabilities, while Part II provides the complete command reference.

## 3.6 Restarting and Shutting Down

BetterCP/M follows the traditional CP/M model of operating on a computer that is started and stopped using the facilities provided by its hardware.

There is no general requirement to perform an operating-system shutdown before turning off a conventional CP/M computer.

However, **you should never interrupt a disk operation by switching off the computer or removing its storage media while data is being written**.

Before stopping BetterCP/M, allow any active program to finish and return to the command prompt.

If you've been editing a file, make sure it has been saved and the editor has terminated normally.

If a disk utility is formatting, copying, or modifying a disk, wait until the operation has completed.

On an emulator, stop the emulation using the emulator's normal controls. On physical hardware, follow the shutdown procedure appropriate to the machine.

Restarting the computer normally performs a cold boot.

An ordinary CP/M warm boot returns control to the operating environment without necessarily reinitializing the entire machine.

The distinction matters when using resident extensions or saved startup configuration, but for everyday operation the familiar CP/M rule remains a useful one: finish your work, make sure your files are saved, and return to the command prompt before stopping the system.

---

# Chapter 4 — Working with Drives and Files

BetterCP/M retains the familiar CP/M system of disk drives, user areas, and file names. If you've used CP/M before, you'll recognize most of the conventions described in this chapter.

BetterCP/M also introduces some useful extensions, particularly in the way drives, user areas, and files can be specified in commands.

This chapter explains how to work with files and disks during ordinary operation. The complete syntax and options for individual commands are provided in Part II, *Command and Utility Reference*.

## 4.1 Drives and User Areas

### Disk Drives

Like conventional CP/M, BetterCP/M identifies disk drives by letters.

Drives are named `A:` through `P:`, although the number actually available depends on your computer and its configuration.

The current drive is shown in the command prompt:

```text
A>
```

To select another drive, enter its letter followed by a colon:

```text
A>B:
B>
```

The prompt changes to indicate that drive B is now selected.

You can also refer to files on another drive without changing the current drive.

For example:

```text
A>DIR B:
```

displays the directory of drive B while leaving drive A selected.

Similarly:

```text
A>TYPE B:README.TXT
```

displays `README.TXT` from drive B.

### User Areas

CP/M divides each disk into numbered user areas.

BetterCP/M retains this convention, allowing files to be organized into separate logical areas on the same disk.

The standard CP/M user areas are numbered 0 through 15. BetterCP/M also supports extended user-area facilities where provided by its commands and configuration.

User areas are useful for organizing files by project, application, or purpose.

For example, you might keep programming tools in one user area, source files in another, and application data in a third.

Files in different user areas are ordinarily treated as belonging to separate collections, even when they reside on the same disk.

To select user area 5, enter:

```text
A>5:
A5>
```

The prompt now indicates drive A, user area 5.

To return to user area 0:

```text
A5>0:
A>
```

### Drive/User Specifications

BetterCP/M provides a convenient way to specify a drive and user area together.

A **drive/user specification**, often abbreviated **DU**, combines the drive letter and user number.

For example:

```text
A0:
B3:
C12:
```

These identify drive A/user 0, drive B/user 3, and drive C/user 12, respectively.

To select drive B, user area 3, enter:

```text
A>B3:
B3>
```

You can also use a DU specification when referring to a file:

```text
A>TYPE B3:README.TXT
```

This displays `README.TXT` from drive B, user area 3, without changing the current drive or user area.

The ability to specify a drive and user area directly is particularly useful when working with files distributed across several user areas.

Not every conventional CP/M program understands BetterCP/M's extended DU notation. It is a feature of the BetterCP/M command environment and of utilities that explicitly support it.

Programs using the standard CP/M programming interface continue to operate according to conventional CP/M drive and user-area rules.

## 4.2 File Names and File Specifications

BetterCP/M uses the standard CP/M file-naming convention.

A file name consists of a name of up to eight characters and an optional file type of up to three characters, separated by a period.

For example:

```text
README.TXT
STAT.COM
MYPROG.ASM
DATA
```

The file type often indicates the purpose of the file.

Some common examples are:

| File type | Common purpose |
|---|---|
| `.COM` | Executable program |
| `.ASM` | Assembly-language source |
| `.TXT` | Text file |
| `.SUB` | SUBMIT command file |
| `.BAK` | Backup file |
| `.HEX` | Intel hexadecimal object file |
| `.PRN` | Assembly listing |

These are conventions rather than restrictions imposed by the filesystem.

A file named `REPORT.TXT`, for example, is not required to contain text merely because its file type is `.TXT`.

### File Specifications

A **file specification**, or **filespec**, identifies a file and may include a drive and user area.

For example:

```text
README.TXT
B:README.TXT
B3:README.TXT
```

The first refers to `README.TXT` in the current drive and user area.

The second refers to the file on drive B, using the applicable user area.

The third explicitly identifies the file in drive B, user area 3.

If the current prompt is:

```text
A2>
```

then:

```text
TYPE README.TXT
```

displays `README.TXT` from drive A, user area 2.

By contrast:

```text
TYPE B3:README.TXT
```

displays the file from drive B, user area 3.

BetterCP/M commands use file specifications extensively, and many accept the extended DU notation.

The individual command descriptions identify which forms are supported.

## 4.3 Wildcards

Wildcards allow a single file specification to refer to several files.

BetterCP/M retains the standard CP/M wildcard characters:

- `?` matches a character in a particular position.
- `*` is a convenient abbreviation for matching the remaining characters in a file name or file type.

For example:

```text
A>DIR *.COM
```

lists files with the `.COM` file type.

Similarly:

```text
A>DIR LETTER.*
```

lists files named `LETTER`, regardless of their file type.

To list all applicable files:

```text
A>DIR *.*
```

### Using Question Marks

A question mark matches any character in the corresponding position.

For example:

```text
A>DIR TEST?.COM
```

can match:

```text
TEST1.COM
TEST2.COM
TESTA.COM
```

Wildcards are especially useful when performing operations on groups of related files.

For example:

```text
A>DIR B3:*.ASM
```

lists assembly-language source files in drive B, user area 3.

### Wildcards and File Operations

Many BetterCP/M commands accept wildcards.

For example, you can use them to select files for copying, deleting, or examining.

However, **not every command permits wildcards in every operand**.

Some operations require an explicit destination filename, while others can operate on groups of files.

The command reference explains the rules for each command.

Be especially careful when using wildcards with commands that modify or delete files. A specification such as `*.*` can select every applicable file in a directory.

## 4.4 File Attributes

In addition to its name and file type, a CP/M file can have attributes that affect how it is treated.

BetterCP/M supports the familiar read-only, system, and archive attributes.

### Read-Only Files

The **read-only (R/O)** attribute protects a file against ordinary operations that would modify or erase it.

This is useful for files that should not be changed accidentally, such as important programs or reference data.

BetterCP/M respects read-only protection.

Some utilities provide explicit options for overriding this protection, but such operations should be used carefully.

### System Files

The **system (SYS)** attribute identifies a file as a system file.

Some directory commands may omit system files from their ordinary listings unless instructed to include them.

In BetterCP/M 1.0, the SYS attribute does not automatically make a file visible across different user areas. Normal drive and user-area rules continue to apply.

### Archive Files

The **archive (ARC)** attribute can be used to identify files for backup or other file-management purposes.

BetterCP/M preserves this attribute where appropriate, but does not impose a universal automatic backup policy based on it.

Individual utilities may provide options that make use of archive attributes.

### Examining and Changing Attributes

BetterCP/M provides utilities for displaying and changing file attributes.

For example, STAT can be used to examine file information and perform supported attribute operations.

The complete procedures are described in the STAT command reference.

## 4.5 Changing Disks

Many CP/M computers use removable storage media.

Whether you're working with physical floppy disks or disk images attached to an emulator, it's important to understand how BetterCP/M handles changes in media.

**Never remove or replace a disk while an operation is reading from or writing to it.**

Doing so can interrupt a file operation and may damage files or directory information.

CP/M maintains information about the disks it is using. If a disk is replaced without the operating system recognizing the change, information associated with the previous disk could otherwise be used incorrectly.

To help prevent this, BetterCP/M retains CP/M's protective behavior when a disk change is detected or suspected.

In some circumstances, a disk may be treated as read-only until the operating system has safely recognized the new medium.

If BetterCP/M reports that a disk has become read-only after a media change, follow the appropriate disk-reset or warm-boot procedure before attempting further writes.

Do not attempt to force a write merely to bypass the warning.

### A Practical Precaution

When working with removable disks, it's good practice to finish the current operation and return to the command prompt before changing media.

If you're using an emulator, follow its procedure for replacing or remounting disk images.

The details vary between systems, so consult the appropriate platform documentation when necessary.

## 4.6 Disk Capacity and Free Space

Not all CP/M disks have the same capacity.

The amount of storage available depends on the disk format, which determines how the disk is organized and how much space is available for files.

BetterCP/M supports different disk formats through its disk and system configuration facilities.

### File Storage

CP/M allocates file space in units called **allocation blocks**.

An allocation block contains a fixed amount of disk space, determined by the disk format.

A small file may occupy an entire allocation block, even if it contains only a few bytes of data.

Consequently, the amount of free space on a disk does not always decrease by exactly the size of each file written to it.

### Directory Capacity

A CP/M disk also has a limited number of directory entries.

Directory entries contain the information used to identify and locate files.

This means that a disk can sometimes have unused storage space but insufficient directory capacity to create additional files.

If you encounter this situation, deleting unneeded files or using a disk format with a larger directory may resolve the problem.

### Examining Disk Information

BetterCP/M provides utilities for examining disk capacity, available space, and related information.

STAT provides disk and file information, while other utilities can examine or configure supported disk formats.

Chapter 10 explains disk operations in more detail.

For complete command syntax, consult the appropriate entries in Part II.

## 4.7 Copying, Moving, and Managing Files

BetterCP/M provides familiar file-management commands together with additional facilities that make it easier to work across drives and user areas.

The most commonly used operations are listing files, copying them, moving them, renaming them, and deleting files that are no longer needed.

### Listing Files

To display the files in the current drive and user area:

```text
A>DIR
```

To list files on another drive:

```text
A>DIR B:
```

To list files in a particular drive and user area:

```text
A>DIR B3:
```

BetterCP/M's DIR utility provides additional options for selecting, sorting, and displaying files.

### Copying Files

COPY creates a copy of a file while leaving the original in place.

For example:

```text
A>COPY README.TXT B:README.TXT
```

copies `README.TXT` from the current drive and user area to drive B.

BetterCP/M also supports copying files between explicitly specified user areas.

For example:

```text
A>COPY B3:REPORT.TXT C2:REPORT.TXT
```

copies the file from drive B, user area 3, to drive C, user area 2.

COPY provides additional options for handling existing destination files, preserving attributes, and performing other file-management operations.

### Moving Files

MOVE transfers a file from one location to another.

Unlike COPY, MOVE is intended to remove the file from its original location after the move has been completed successfully.

For example:

```text
A>MOVE REPORT.TXT B:REPORT.TXT
```

moves `REPORT.TXT` from the current drive and user area to drive B.

Moving files can be convenient when reorganizing disks or user areas.

However, remember that MOVE changes the location of the original file. If you want to retain the original, use COPY instead.

### Renaming Files

REN changes a file's name.

For example:

```text
A>REN NEWNAME.TXT=OLDNAME.TXT
```

renames `OLDNAME.TXT` to `NEWNAME.TXT`.

Renaming is useful for organizing files, changing file types, or assigning more descriptive names.

BetterCP/M provides additional REN options beyond the conventional CP/M command.

### Deleting Files

ERA deletes files.

For example:

```text
A>ERA OLD.DAT
```

deletes `OLD.DAT` from the current drive and user area.

Wildcards can be used to select multiple files:

```text
A>ERA *.BAK
```

This selects backup files matching the specification.

**Use particular care with ERA.** Deleting files may make their contents unrecoverable.

BetterCP/M provides additional ERA facilities, including options for confirmation and handling protected files.

### Choosing the Right Command

COPY, MOVE, REN, and ERA perform different operations.

COPY duplicates files.

MOVE relocates files.

REN changes their names.

ERA removes them.

These distinctions are straightforward, but they become especially important when working with wildcard specifications or files on different drives.

For complete descriptions of these commands, including their options, confirmation behavior, and error messages, consult Part II, *Command and Utility Reference*.

Below are **Chapters 5–7 of the BetterCP/M 1.0 User's Guide**, presented together for review.

They follow the style established in Chapters 1–4: friendly, practical, and aimed at users rather than operating-system developers. Detailed command syntax belongs in Part II, while these chapters explain how to use the facilities in everyday work.

Chapter 5 incorporates our agreed wording for command history: **Ctrl-K and Ctrl-J are the documented controls for v1.0; arrow-key behavior depends on the keyboard and terminal configuration.**

The material draws on the earlier User's Guide, including its descriptions of SUBMIT, XSUB, COPY, and CONFIG. These are editorial drafts, not changes to the GitHub repository.

---

# Chapter 5 — The Command Environment

The command processor is the part of BetterCP/M you'll use most often. It accepts commands, starts programs, and provides the familiar CP/M prompt.

If you've used CP/M before, you already know the basics. BetterCP/M retains the traditional command-line environment while adding conveniences such as command editing, command history, and more flexible ways of finding and running programs.

This chapter introduces those facilities and explains how they work together.

## 5.1 Entering Commands

When BetterCP/M is ready to accept a command, it displays a prompt:

```text
A>
```

The prompt identifies the current drive and, when appropriate, the current user area.

Enter a command by typing its name, followed by any required arguments, and pressing `RETURN`.

For example:

```text
A>DIR
```

displays the directory of the current drive and user area.

To display a text file:

```text
A>TYPE README.TXT
```

Commands are not case-sensitive, so:

```text
A>dir
```

has the same meaning as `DIR`.

Many commands accept additional arguments or options. For example:

```text
A>DIR B3:*.COM
```

lists executable files in drive B, user area 3.

BetterCP/M accepts commands provided directly by the command processor, commands supplied by resident extensions, and ordinary programs stored on disk.

For most purposes, you needn't worry about the distinction. You enter the command in the same general way regardless of where it comes from.

The complete syntax for individual commands is given in Part II, *Command and Utility Reference*.

## 5.2 Command-Line Editing

Anyone who has used a command-line operating system knows how frustrating it can be to type a long command, discover a mistake, and have to enter the entire line again.

BetterCP/M makes this easier by allowing you to edit a command before executing it.

You can move the cursor through the command line, correct characters, insert new text, and remove unwanted text.

For example, suppose you enter:

```text
A>COPY B3:REPROT.TXT C2:REPORT.TXT
```

but notice that you've mistyped `REPORT` as `REPROT`.

Rather than erase the entire command and start over, you can move the cursor back to the mistake and correct it.

The command isn't executed until you press `RETURN`, so you can make as many corrections as necessary before submitting it.

BetterCP/M uses editing conventions familiar to users of WordStar and other CP/M programs, although not every command-line function uses the same keys as WordStar.

The complete key assignments are listed in Appendix B, *Command-Line Editing Keys*.

## 5.3 Command History

BetterCP/M remembers previously entered commands, allowing you to recall, edit, and execute them again without retyping the entire command.

Press **Ctrl-K** to recall an earlier command, or **Ctrl-J** to move forward through the command history.

Depending on your computer's keyboard and terminal configuration, the Up and Down arrow keys may also provide these functions.

For example, suppose you've just entered:

```text
A>COPY B3:REPORT.TXT C2:REPORT.TXT
```

and then realize that you also want to copy another file.

Instead of retyping the command, recall it from history, change the filename, and press `RETURN`.

The recalled command behaves just like one you've typed yourself. You can execute it unchanged or edit it first.

Command history remains available after ordinary programs finish and return to the prompt. It also survives a normal warm boot.

A cold boot begins with an empty history.

Because history storage is limited, older entries are eventually discarded as new commands are entered.

Command history is especially convenient when working with long file specifications or commands containing several options.

## 5.4 Selecting Drives and User Areas

BetterCP/M provides several convenient ways to move among drives and user areas.

To select drive B:

```text
A>B:
B>
```

To select user area 5 on the current drive:

```text
B>5:
B5>
```

To select both a drive and user area:

```text
B5>C3:
C3>
```

This selects drive C, user area 3.

BetterCP/M refers to a drive and user-area combination as a **drive/user**, often abbreviated **DU**.

You can also specify a drive and user area when entering a command without changing your current selection.

For example:

```text
A2>DIR B3:
A2>
```

displays the directory of drive B, user area 3, and then returns to the unchanged prompt.

This is useful when working with files scattered across several drives or user areas.

Chapter 4 provides a fuller explanation of drive/user specifications.

## 5.5 Resident and Transient Commands

BetterCP/M distinguishes between two kinds of commands: **resident** and **transient**.

A resident command is already available in memory as part of the active command environment. It can be executed without first loading a separate program from disk.

A transient command is an ordinary executable program, usually stored in a `.COM` file. BetterCP/M loads it when needed and executes it in the Transient Program Area.

Some familiar commands are available in both forms.

For example, the standard resident command package provides commands such as DIR, ERA, REN, TYPE, COPY, and MOVE.

Their transient counterparts may offer additional capabilities.

### Choosing a Transient Command Explicitly

Ordinarily, you enter a command without specifying whether it should be resident or transient.

For example:

```text
A>DIR
```

uses the available resident command when one is installed.

However, BetterCP/M also allows you to request the transient version explicitly.

Prefix the command name with a colon:

```text
A>:DIR
```

This tells BetterCP/M to run `DIR.COM` rather than the resident DIR command.

A period can also be used:

```text
A>.DIR
```

The two prefixes have the same purpose.

This is particularly useful when the transient utility offers additional options not supported by its resident counterpart.

For example:

```text
A>:DIR /WHEREIS ED.COM
```

uses the transient DIR utility's file-location facility.

The command descriptions in Part II identify features that require transient execution.

## 5.6 Command Search and Execution

When you enter a command, BetterCP/M determines how to execute it.

It first recognizes commands that select drives or user areas. It then checks commands built into the command processor, followed by those supplied by installed Command Processor Extensions.

If none of these recognizes the command, BetterCP/M looks for a transient program.

### Finding Programs

When you enter an ordinary program name without specifying a drive or user area, BetterCP/M searches the current drive and user area first.

If the program isn't found there, it searches drive A, user area 0.

For example, suppose you're working in user area 3 on drive B:

```text
B3>
```

You enter:

```text
B3>MYPROG
```

BetterCP/M first looks for `MYPROG.COM` in B3:.

If it isn't found there, BetterCP/M looks in A0:.

This is convenient because commonly used programs can be kept in A0: while your working files remain in other locations.

If a program is found in A0:, it runs with your original drive and user area still selected.

You can therefore keep applications in A0: without having to move your working files there.

### Specifying a Program's Location

You can also identify a program's location explicitly:

```text
B3>C2:MYPROG
```

This tells BetterCP/M to look for the program in C2:.

When a location is explicitly specified, BetterCP/M uses that location rather than searching A0: as a fallback.

The same general lookup rules apply when you explicitly request a transient program using the `:` or `.` prefix.

### Running Programs

When BetterCP/M finds a transient program, it loads the program and starts it.

For example:

```text
A>MYPROG INPUT.DAT
```

runs `MYPROG.COM` and supplies `INPUT.DAT` as a command-line argument.

The program receives its arguments through the conventional CP/M command-line environment.

When it finishes, BetterCP/M restores the command environment and displays the prompt again.

These facilities allow ordinary CP/M programs to run without needing to know how BetterCP/M's enhanced command processor works internally.

## 5.7 Command Processor Extensions

Command Processor Extensions, or **CPXs**, allow additional commands to become part of the resident command environment.

The standard BetterCP/M configuration includes `RCP.CPX`, which provides commonly used commands such as:

```text
DIR  ERA  TYPE  REN  USER
CLS  VER  COPY  MOVE
```

Because these commands are resident, they're available without loading separate transient programs.

Additional CPXs can be installed to provide other commands.

More than one CPX can be active at a time, allowing the command environment to be customized for different purposes.

For example, a user might load an extension providing specialized commands for a particular application or working environment.

CPXs can be listed, loaded, and unloaded while the system is running.

Chapter 8 explains how to manage resident extensions. For complete CPX command syntax and options, consult the CPX entry in Part II.

## 5.8 Interrupting Commands and Programs

Most commands return to the BetterCP/M prompt when their work is complete.

Sometimes, however, you may need to interrupt a command before it finishes.

Many CP/M programs recognize **Ctrl-C** as a request to stop the current operation.

BetterCP/M commands also use Ctrl-C where appropriate to abandon an operation and return control to the command environment.

The exact effect depends on the program being executed.

Some programs may ignore Ctrl-C, while others recognize it only at particular points.

A warm boot also returns control to the operating system and restores the command environment.

### Interrupting Disk Operations

Be particularly careful when interrupting commands that modify files or disks.

For example, if a disk-copying operation is writing data when it is interrupted, the destination disk may be incomplete.

Likewise, interrupting a file operation can leave a partially written file.

Whenever possible, allow disk operations to finish normally.

If an operation fails or is interrupted unexpectedly, examine the affected files or media before continuing.

BetterCP/M's utilities provide error messages and, where appropriate, recovery procedures to help deal with these situations.

# Chapter 6 — Batch Processing

BetterCP/M can execute a series of commands automatically, saving you the trouble of entering the same instructions over and over again.

This facility is called **batch processing**. If you've used Digital Research CP/M before, you'll already be familiar with SUBMIT, the utility that reads commands from a file and executes them in sequence.

BetterCP/M retains the traditional CP/M batch-processing environment, including SUBMIT command files and the XSUB extension, while allowing batch files to take advantage of BetterCP/M's enhanced commands and utilities.

Batch processing is particularly useful for repetitive tasks such as assembling programs, copying files, preparing working disks, or performing a series of operations that you would otherwise enter individually.

This chapter introduces batch processing and shows how to create and use command files. Complete descriptions of SUBMIT and XSUB are provided in Part II, *Command and Utility Reference*.

## 6.1 Introduction to Batch Processing

Suppose you're working on an assembly-language program. Each time you make a change, you might need to assemble the source file, load the resulting program, and run a test.

You could enter each command separately, but if you perform the same sequence repeatedly, it's more convenient to place the commands in a file.

For example, a command file might contain:

```text
ASM MYPROG
LOAD MYPROG
MYPROG
```

Instead of typing these commands individually, you can instruct BetterCP/M to execute the entire sequence.

The commands are processed in order, just as though you had entered them at the command prompt.

A batch file can contain ordinary CP/M commands, BetterCP/M commands, and the names of transient programs. Commands supplied by resident extensions can also be used, provided the necessary extensions are loaded.

Batch files are especially convenient for operations that require several steps but little interaction with the user.

## 6.2 SUBMIT and SUB Files

BetterCP/M uses the familiar CP/M **SUBMIT** utility to execute command files.

A SUBMIT file is an ordinary text file containing commands, usually with the file type `.SUB`.

For example, you might create a file named:

```text
BACKUP.SUB
```

containing:

```text
DIR
COPY *.ASM B:
DIR B:
```

The first command displays the current directory. The second copies the selected assembly-language source files to drive B. The third displays the directory of drive B so you can examine the results.

To execute the file, enter:

```text
A>SUBMIT BACKUP
```

SUBMIT reads the commands from `BACKUP.SUB` and arranges for them to be executed in sequence.

You don't need to type the `.SUB` extension when invoking SUBMIT.

### Creating a SUBMIT File

Because SUBMIT files contain ordinary text, you can create them with any CP/M text editor.

For example, you could use ED to create `BACKUP.SUB`, enter the commands you want executed, and save the file.

You can also prepare SUBMIT files on another computer and transfer them to your CP/M system, provided they are saved in a suitable text format.

Each command should appear on its own line.

When writing a SUBMIT file, it's generally best to use commands that you have already tested individually. This is particularly important for commands that modify or delete files.

### Running a SUBMIT File

To execute a command file named `BUILD.SUB`, enter:

```text
A>SUBMIT BUILD
```

BetterCP/M processes the commands in the file in sequence.

The commands are executed in the normal command environment, so they can use the same drives, user areas, and resident facilities available at the command prompt.

A command file can also invoke ordinary transient programs.

If a program or command cannot be found, or if an operation fails, the result depends on the command and the batch-processing facilities involved. Don't assume that every failure will be ignored or that subsequent commands will always execute.

For important procedures, especially those that modify disks or files, test the complete sequence before relying on it for unattended operation.

## 6.3 Parameters and Substitution

SUBMIT files can be made more flexible by accepting parameters.

Rather than creating a separate command file for every program you want to assemble, you can create one file that accepts the program name as an argument.

For example, suppose `BUILD.SUB` contains:

```text
ASM $1
LOAD $1
$1
```

Here, `$1` represents the first parameter supplied when SUBMIT is invoked.

To assemble and run a program named `TEST`, enter:

```text
A>SUBMIT BUILD TEST
```

SUBMIT substitutes `TEST` for `$1`, producing the equivalent of:

```text
ASM TEST
LOAD TEST
TEST
```

This allows a single SUBMIT file to be reused with different programs.

### Using Multiple Parameters

A SUBMIT file can accept more than one parameter.

For example, a file named `COPYFILE.SUB` might contain:

```text
COPY $1 $2
```

You could then enter:

```text
A>SUBMIT COPYFILE REPORT.TXT B:REPORT.TXT
```

The resulting command would be:

```text
COPY REPORT.TXT B:REPORT.TXT
```

This is a simple example, but parameter substitution becomes particularly useful in longer command files.

### Parameter Substitution Is Textual

SUBMIT substitutes parameter text into the command file. It doesn't interpret the meaning of the resulting command.

For example, if a parameter contains a filename, SUBMIT places that filename into the command wherever the corresponding parameter reference appears.

The command that eventually executes is responsible for interpreting the filename, options, and other arguments.

This distinction is useful to remember when constructing more elaborate command files.

It also means that an incorrect parameter can produce an incorrect command. When a SUBMIT file performs destructive operations, take care to verify the parameters before executing it.

## 6.4 XSUB

Ordinary SUBMIT files execute commands entered at the command-processor level. Some programs, however, ask for additional input after they have started.

For example, a program might display a prompt asking for a filename, an option, or some other information.

Normally, the user must type a response at the keyboard.

**XSUB extends batch processing by allowing a SUBMIT file to supply input to programs that read from the console.**

This makes it possible to automate certain interactive programs that would otherwise require someone to sit at the keyboard.

### How XSUB Works

Consider a program that prompts for two filenames:

```text
Source file:
Destination file:
```

Without XSUB, you would start the program and type the filenames when requested.

With XSUB, a suitably prepared command file can supply those responses automatically.

XSUB works with programs that obtain their input through the supported CP/M buffered console-input interface.

It does not automatically provide input to every program. Software that reads the keyboard directly, uses its own device drivers, or employs other input methods may not be compatible with XSUB.

### Using XSUB

XSUB is normally activated as part of a SUBMIT procedure.

Once active, it allows subsequent submitted input to be passed to compatible programs.

The exact arrangement of commands and responses depends on the program being automated. Consult the XSUB command reference for the supported invocation procedure and any restrictions.

### Returning to Keyboard Input

BetterCP/M's XSUB facility allows a program to continue receiving ordinary keyboard input after its submitted input has been exhausted.

For example, a program may receive its initial responses from the batch file and then continue interactively.

This is useful when only part of a program's operation needs to be automated.

XSUB uses resident support while supplying batch input. In some circumstances, that support may remain loaded after the batch has finished.

If necessary, it can be removed with:

```text
A>RSX UNLOAD BATCHIO
```

This releases the resident batch-input facility when it is no longer needed.

For additional information about managing resident extensions, see Chapter 8.

## 6.5 Batch Execution and Termination

A SUBMIT file is executed as a sequence of commands, but there are some important differences between entering commands manually and allowing them to execute automatically.

### Interactive Commands

A command executed from a SUBMIT file does not necessarily become noninteractive.

For example, a file-copying command may ask whether an existing destination file should be replaced.

If the command normally requires confirmation, it may still require confirmation when executed from a SUBMIT file.

This is particularly important when preparing batch files that you intend to run unattended.

BetterCP/M provides options for some utilities that allow you to specify how such situations should be handled.

### Interrupting a Batch

Batch execution can be interrupted by commands, programs, or operating-system conditions that terminate the current batch procedure.

The precise behavior depends on the program involved and the way it returns control to the operating system.

If a batch operation is interrupted, do not assume that all commands in the file have been executed.

For example, a batch that copies several files may have copied some files successfully before encountering an error.

Before restarting such a procedure, examine the files or disks involved to determine which operations have already completed.

### Errors During Batch Processing

Some commands report errors and return control to the command processor. Others may terminate the active batch procedure.

The presence of an error message does not necessarily tell you whether subsequent commands will execute.

For this reason, a batch file should not be treated as an automatic error-recovery system.

When preparing an important batch procedure, test how its commands behave when a file is missing, a destination already exists, or a disk operation fails.

### Warm Boots and Batch Processing

CP/M uses warm boots as part of its normal program-execution environment.

BetterCP/M preserves the mechanisms needed for conventional SUBMIT operation, allowing batch execution to continue across ordinary program execution where appropriate.

Resident extensions used by the batch environment are also subject to BetterCP/M's normal extension-management rules.

A cold boot, however, establishes a new operating session rather than continuing a previous batch procedure.

## 6.6 Practical Examples

The following examples illustrate some common uses of batch processing.

### Example 1: Assembling a Program

Suppose you frequently assemble and run a program while developing it.

Create `BUILD.SUB` containing:

```text
ASM $1
LOAD $1
$1
```

To build and run `TEST`, enter:

```text
A>SUBMIT BUILD TEST
```

This executes the equivalent of:

```text
ASM TEST
LOAD TEST
TEST
```

You can use the same command file for another program simply by changing the parameter.

### Example 2: Copying Source Files

Suppose you want to copy all assembly-language source files from one user area to another.

Create `SOURCES.SUB` containing:

```text
COPY B1:*.ASM C3:
DIR C3:*.ASM
```

Then enter:

```text
A>SUBMIT SOURCES
```

The first command copies the selected files. The second displays the destination directory.

If destination files already exist, COPY may request confirmation before replacing them.

For unattended execution, you can use COPY's batch option.

### Example 3: Copying Files Without Prompts

BetterCP/M's COPY utility provides a `/B` option for batch-oriented operation.

For example:

```text
COPY B1:*.DAT C3: /B
```

This copies matching files without stopping to ask how existing destination files should be handled.

If a writable destination already exists, COPY reports `FILE EXISTS` for that file and continues with the remaining files.

It does not automatically overwrite the existing file.

You can specify a different policy explicitly.

To overwrite existing writable destination files:

```text
COPY B1:*.DAT C3: /B /O
```

To skip existing destination files:

```text
COPY B1:*.DAT C3: /B /S
```

In both cases, files without existing destinations are copied normally.

Read-only destination files remain protected.

The `/B` option applies to COPY itself. It does not make other commands in the SUBMIT file noninteractive.

For the complete description of COPY's options, consult the COPY command reference.

### Example 4: Customizing System Startup

BetterCP/M uses a SUBMIT file as part of its normal startup configuration.

The standard distribution provides:

```text
STARTUP.SUB
```

The configured cold-start command is:

```text
SUBMIT STARTUP
```

The supplied startup file initially displays the BetterCP/M identification banner.

You can edit this file to perform additional operations automatically when the system starts.

For example, startup commands can load resident extensions needed for your preferred working environment.

Because the startup procedure runs automatically, it's best to test new commands individually before adding them to `STARTUP.SUB`.

A mistake in an ordinary batch file is inconvenient. A mistake in a startup file can make every cold boot inconvenient until the file is corrected.

Chapter 7 explains how to configure the startup command, while Chapter 8 describes loading and managing resident extensions.

---

# Chapter 7 — Configuring BetterCP/M

BetterCP/M provides several facilities for customizing the operating environment to suit your computer and the way you prefer to work.

You can change the command executed when the system starts, configure disk drives and formats, select peripheral devices, and save settings for subsequent sessions.

Most of these operations are performed using **CONFIG**, BetterCP/M's system configuration utility.

If you've used conventional CP/M, you'll be familiar with the idea of configuring the BIOS and regenerating a system disk to accommodate different hardware. BetterCP/M makes many of these operations more convenient by providing configuration facilities that can be used from the command prompt.

Some settings can be changed while the system is running. Others must be saved to the system disk and take effect the next time BetterCP/M starts.

This chapter explains how to use these facilities. Complete descriptions of CONFIG and the related utilities appear in Part II, *Command and Utility Reference*.

## 7.1 Configuration Facilities

BetterCP/M distinguishes between settings currently in use and settings saved for future system startup.

This distinction is important because changing a setting does not necessarily make that change permanent.

For example, you might temporarily configure a drive to read a particular disk format. That configuration can remain active during your current session without becoming the default the next time you boot BetterCP/M.

Similarly, changing the system's startup command does not immediately execute the new command. Instead, it determines what BetterCP/M will execute during a subsequent cold boot.

### Current and Saved Settings

There are two principal kinds of configuration changes.

**Current settings** affect the operating environment that is running now. These may include drive assignments, disk formats, and peripheral-device selections.

**Saved settings** are stored with the operating system so that they can be restored during a later cold boot.

BetterCP/M allows you to make temporary changes without necessarily replacing your saved configuration.

This is useful when experimenting with different disk formats or working with hardware that is only occasionally connected.

For example, you might normally use drive B with one disk format but temporarily configure it to read a disk prepared on another CP/M computer.

Once you've finished, you can restore your usual configuration without having permanently changed the system.

### Platform-Dependent Settings

Not every configuration option is available on every computer.

Some settings depend on the capabilities of the BIOS, disk controller, or other hardware.

A computer with physical floppy drives may provide options for drive geometry and timing that have little meaning on a system using emulated storage.

Likewise, a peripheral device must actually be supported by the computer and its BIOS before BetterCP/M can use it.

The CONFIG utility provides access to supported configuration facilities, while the platform documentation describes any machine-specific requirements.

## 7.2 Using CONFIG

CONFIG is BetterCP/M's principal system configuration utility.

To start it, enter:

```text
A>CONFIG
```

CONFIG displays a menu of available configuration operations.

The configuration menu groups together the facilities used to control startup behavior, device assignments, disk drives, and disk formats.

A typical BetterCP/M 1.0 configuration menu includes:

```text
[ A ] Startup command

[ B ] Cold-boot IOBYTE

[ C ] Disk drive definitions
[ D ] Disk format definitions
[ E ] Create or edit a disk format

[ S ] Save current configuration on disk (SYSGEN)
```

Select the letter corresponding to the operation you want to perform.

CONFIG does not require a full-screen terminal monitor. It can be used through the ordinary BetterCP/M console.

### Examining the Current Configuration

Before making changes, it's often useful to examine the settings already in use.

Enter:

```text
A>CONFIG /SHOW
```

CONFIG displays information about the current system configuration, including the active drive settings and saved startup information.

Where applicable, it distinguishes between settings currently in use and those saved for the next cold boot.

This is particularly useful when you've made temporary changes and want to determine whether they will survive a restart.

The `/SHOW` option is informational. It does not modify the configuration.

### Making Changes

Some CONFIG operations change the running system immediately. Others prepare changes that must be saved before they become permanent.

For example, changing a drive assignment can affect how BetterCP/M accesses that drive during the current session.

Changing the saved startup command, on the other hand, affects what happens during a later cold boot.

CONFIG identifies when a change requires saving.

**Before making significant changes to your system configuration, it's good practice to keep a working backup of the system disk.**

An incorrect disk configuration can make a drive inaccessible until its settings are corrected. Changes to the saved boot configuration can also affect the system's ability to start normally.

## 7.3 Startup Commands

BetterCP/M can execute a command automatically during a cold boot.

This provides a convenient way to establish your preferred working environment whenever the system starts.

The standard distribution uses:

```text
SUBMIT STARTUP
```

as its saved startup command.

This causes BetterCP/M to execute the commands contained in `STARTUP.SUB`.

The supplied startup file initially displays the BetterCP/M identification banner. You can edit the file to perform additional operations.

For example, you might use it to load resident extensions or select facilities that you normally want available.

### Editing STARTUP.SUB

Because `STARTUP.SUB` is an ordinary SUBMIT file, you can edit it using a text editor.

For example, a startup file might contain:

```text
:VER /BANNER
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

This example displays the system banner, loads a screen backend and an ADM-3A terminal personality, and clears the screen.

The example is appropriate only for a system that provides the named screen backend and terminal extension. Other platforms may require different commands.

Chapter 8 explains resident extension management, while Chapter 9 describes terminal support.

### Changing the Startup Command

You can change the saved startup command using CONFIG.

For example:

```text
A>CONFIG /STARTUP="SUBMIT STARTUP"
```

sets the startup command to `SUBMIT STARTUP`.

To disable automatic startup commands:

```text
A>CONFIG /STARTUP=""
```

CONFIG requests confirmation before saving the change.

The new command takes effect during a subsequent cold boot. It is not executed immediately.

### Restoring the Default Startup Command

CONFIG also provides a convenient way to prepare the standard startup command:

```text
A>CONFIG /DEFAULT
```

This prepares `SUBMIT STARTUP` as the startup command and opens the relevant configuration menu.

The change is not automatically saved. You can inspect or modify it before committing it to the system disk.

### Cold Boots and Warm Boots

The startup command is executed during a cold boot.

It is not repeated during an ordinary warm boot.

This distinction is especially useful when loading resident extensions. An extension loaded during cold startup can remain available throughout the session, even after transient programs terminate.

There is ordinarily no need to reload the extension after each warm boot.

For a complete description of startup-command options, consult the CONFIG reference in Part II.

## 7.4 Drive Configuration

BetterCP/M can work with a variety of disk formats, including formats used by other CP/M systems.

Because different computers use different disk drives and controllers, BetterCP/M separates the characteristics of a physical drive from the format of the disk being used.

CONFIG provides facilities for examining and changing both.

### Physical Drives and Logical Drives

A **physical drive** is the actual disk drive or storage device connected to the computer.

A **logical drive** is the drive letter, such as `A:` or `B:`, through which BetterCP/M accesses that device.

The distinction allows BetterCP/M to associate a logical drive with a particular physical device and disk format.

For example, you might configure logical drive B to use a physical drive containing a disk written in a format different from your usual system disks.

The available assignments depend on the computer and its BIOS.

### Examining Drive Settings

To examine the current configuration, enter:

```text
A>CONFIG /SHOW
```

CONFIG displays the active drive settings and, where available, the corresponding saved defaults.

This is a useful first step before making changes.

You can also examine drive definitions through CONFIG's interactive menus.

### Selecting a Disk Format

CONFIG provides a catalog of disk-format definitions.

When assigning a format to a drive, you can select an appropriate definition from this catalog rather than entering all the disk parameters individually.

For example:

```text
A>CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="MM 80T DS DATA"
```

This assigns logical drive C to physical drive 1 using the named disk format.

The format name must match a definition available in the system's format catalog. The example is illustrative; the correct format depends on the disk and drive you're using.

CONFIG checks whether the requested format is compatible with the selected physical drive before applying the assignment.

You can also select formats through the interactive configuration menus.

### Temporarily Changing a Drive

One of the advantages of BetterCP/M's configuration facilities is that drive assignments can be changed without necessarily changing the saved startup configuration.

Suppose you need to read a disk from another CP/M computer.

You can select an appropriate format, use the disk, and then restore your usual drive configuration.

If you don't save the temporary assignment, it won't replace your normal cold-boot defaults.

This makes it easier to work with different disk formats without maintaining a separate operating-system disk for each configuration.

### Removing a Drive Assignment

A logical drive can also be disconnected from its current assignment.

For example:

```text
A>CONFIG /LOGICAL=C /UNBIND
```

removes the active assignment for logical drive C.

This does not erase or format the disk. It simply removes the logical drive's association with the physical device.

BetterCP/M protects drive A from this operation because of its importance to the running system.

### Creating and Editing Disk Formats

CONFIG also provides facilities for creating and modifying disk-format definitions.

These are useful when working with disks whose characteristics are not already represented in the format catalog.

However, they require an accurate understanding of the disk's organization.

An incorrect format definition can cause BetterCP/M to interpret the disk incorrectly, potentially making files inaccessible or placing existing data at risk if the disk is written.

For ordinary operation, use an existing format definition whenever possible.

The CONFIG command reference describes the available format-editing facilities. More detailed information about disk organization and format definitions is provided in the technical documentation.

## 7.5 Console and Device Configuration

Like conventional CP/M, BetterCP/M provides logical device assignments for console, reader, punch, and list operations.

These assignments allow programs to use standard CP/M device interfaces without necessarily knowing which physical device provides them.

BetterCP/M retains the traditional **IOBYTE** mechanism for selecting these assignments.

### The IOBYTE

The IOBYTE is a system value used to select logical device assignments.

For example, it can determine which supported device is used for list output or other conventional CP/M character-device operations.

The available choices depend on the computer and its BIOS.

An IOBYTE assignment does not create a device or provide a driver for hardware that the system doesn't support. It merely selects among the device facilities available through the BIOS.

### Changing Device Assignments

BetterCP/M distinguishes between the IOBYTE currently in use and the value saved for the next disk cold boot.

The STAT utility provides facilities for changing the live IOBYTE assignment.

CONFIG allows you to save a separate assignment that will be established during a subsequent cold boot.

For example:

```text
A>CONFIG /IOBYTE=85
```

requests that decimal value 85 be saved as the cold-boot IOBYTE.

CONFIG asks for confirmation before saving the change.

The command does not change the current IOBYTE. To change the active assignment, use STAT.

You can examine the current and saved values with:

```text
A>CONFIG /SHOW
```

### Choosing Device Assignments

Before changing the IOBYTE, make sure the requested assignment is supported by your computer.

Some traditional CP/M device names refer to hardware that may not exist on a particular system.

For example, selecting a printer interface does not make a printer available unless the BIOS provides the corresponding output facility.

BetterCP/M also requires the console assignment to remain compatible with its supported console environment.

For the available device assignments and their meanings, consult the STAT and CONFIG command references.

Platform-specific documentation describes any additional requirements or limitations.

## 7.6 Saving Configuration Changes

Many BetterCP/M configuration changes can be made temporarily.

To retain them after a cold boot, you must save the appropriate settings to the system disk.

CONFIG provides facilities for doing this, using BetterCP/M's system-generation services.

### Temporary and Permanent Changes

Suppose you temporarily change a drive assignment to read a disk from another computer.

You may want to use that configuration for the remainder of the current session without making it your permanent default.

In that case, you can leave the saved configuration unchanged.

On the other hand, if you've installed a new disk drive or established a configuration you intend to use regularly, you'll probably want to save it.

BetterCP/M allows you to distinguish between these situations.

### Saving from CONFIG

CONFIG's main menu includes:

```text
[ S ] Save current configuration on disk (SYSGEN)
```

This option provides access to the system-configuration saving facilities.

CONFIG distinguishes between saving pending cold-boot changes and saving the current configuration as the new startup defaults.

These operations are not necessarily equivalent.

For example, you might have changed the startup command while also temporarily reassigning a disk drive.

Saving only the pending cold-boot changes allows you to retain the new startup command without making the temporary drive assignment permanent.

Saving the current configuration as the new defaults is appropriate when you want those active settings restored during future cold boots.

CONFIG presents the available choices and requests confirmation before writing the saved configuration.

### Verifying the Configuration

After saving, it's good practice to examine the configuration again:

```text
A>CONFIG /SHOW
```

Check that the saved settings correspond to what you intended.

If you've changed startup settings, remember that they won't take effect until the next cold boot.

If you've changed drive assignments, verify that the appropriate drives and formats remain available.

### Protecting Your System Disk

Saving configuration changes modifies information associated with the operating system on disk.

For this reason, you should keep a backup of a known working system configuration.

This is particularly important when changing disk-drive assignments or other settings needed to boot the computer.

If a saved configuration prevents the system from starting correctly, a backup system disk may be needed to restore a working environment.

CONFIG performs checks when saving settings, but no software can protect against every possible hardware failure or interruption.

Avoid resetting or switching off the computer while configuration information is being written.

### Returning to a Known Configuration

If you're experimenting with unfamiliar disk formats or device assignments, consider retaining a separate system disk with your normal configuration.

This gives you a convenient way to return to a known working system if an experiment produces unexpected results.

For ordinary use, however, BetterCP/M's configuration facilities should allow you to make most supported changes without rebuilding the operating system manually.

---

# Chapter 8 — Resident Extensions

One of BetterCP/M's most useful features is its ability to add commands and system services without rebuilding the operating system.

These additions are called **resident extensions**. Unlike ordinary transient programs, which are loaded when needed and normally disappear when they finish, resident extensions remain in memory and continue to provide their facilities while you work.

BetterCP/M supports two principal kinds of extensions: Command Processor Extensions (CPXs) and Resident System Extensions (RSXs).

This chapter explains how to use and manage them. You don't need to understand their internal workings to take advantage of the facilities they provide.

For complete command syntax and options, consult the CPX and RSX entries in Part II, *Command and Utility Reference*.

## 8.1 Introducing CPX and RSX Extensions

In conventional CP/M, the command processor provides a small collection of built-in commands. Most other commands are transient programs loaded from disk.

BetterCP/M extends this arrangement by allowing additional commands and services to remain resident.

For example, a resident extension might provide frequently used file-management commands, add a new operating-system service, or support a particular terminal.

Resident extensions offer several advantages. A resident command is immediately available without loading a separate program from disk each time it is used. A resident service can remain available while different applications execute. Extensions can also be loaded and unloaded to suit the work you're doing.

There is a tradeoff, however: resident extensions occupy memory that would otherwise be available to transient programs.

BetterCP/M allows you to choose which optional extensions to keep loaded, making it possible to balance additional facilities against available program memory.

### Command Processor Extensions

A **Command Processor Extension**, or **CPX**, adds commands to BetterCP/M's command processor.

The standard BetterCP/M environment includes a resident command package named `RCP.CPX`.

This package provides familiar commands such as:

```text
DIR   ERA   TYPE   REN   USER
CLS   VER   COPY   MOVE
```

These commands can be executed without loading separate `.COM` programs.

For example:

```text
A>DIR
```

normally invokes the resident DIR command when the standard resident command package is installed.

Some commands are available in both resident and transient forms. The resident version generally provides commonly used operations, while the transient version may offer additional options.

BetterCP/M allows you to request a transient program explicitly by prefixing its name with a colon:

```text
A>:DIR /WHEREIS ED.COM
```

This bypasses the resident DIR command and executes `DIR.COM`.

A period can also be used as the prefix:

```text
A>.DIR /WHEREIS ED.COM
```

Both forms have the same meaning.

BetterCP/M 1.0 does not automatically switch to the transient version when you request an option supported only by that version. Instead, the resident command may tell you to invoke the transient utility explicitly.

For example:

```text
A>DIR /WHEREIS ED.COM
DIR: Use :DIR.
```

You can then enter:

```text
A>:DIR /WHEREIS ED.COM
```

For more information about resident and transient command execution, see Chapter 5.

### Resident System Extensions

A **Resident System Extension**, or **RSX**, provides services that remain available while other programs execute.

Unlike CPXs, which add commands to the command processor, RSXs extend the operating environment itself.

Terminal support is one of the most useful examples.

A program written for a particular terminal may expect certain control sequences to move the cursor, clear the screen, or change the display.

BetterCP/M can provide these facilities through resident terminal-monitor extensions.

Other RSXs provide facilities such as support for batch input or disk-format services.

Although CPXs and RSXs both remain resident, they serve different purposes and are managed separately.

## 8.2 Installing Extensions

Resident extensions are supplied as files that BetterCP/M can load when their facilities are needed.

CPX files use the `.CPX` file type, while RSX files use `.RSX`.

For example:

```text
RCP.CPX
ADM3A.RSX
VT52.RSX
ANSI.RSX
```

Before loading an extension, make sure its file is available in the location expected by BetterCP/M.

Extensions must also be compatible with the running operating system. An extension prepared for a different version or system configuration may not load successfully.

Some extensions depend on other resident components.

For example, BetterCP/M's terminal personalities require a suitable screen backend. The backend provides the connection to the computer's display, while the terminal personality interprets the control sequences expected by applications.

These supporting components must be loaded before the extensions that depend on them.

The documentation supplied with an extension should identify any such requirements.

### Installing an Extension for Regular Use

If you frequently use a particular extension, you can arrange for it to be loaded automatically during system startup.

BetterCP/M normally uses `STARTUP.SUB` for this purpose.

For example, a system using the Model 4 screen backend might include:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

These commands load the screen backend, activate the ADM-3A terminal personality, and clear the display.

The example is appropriate only for systems supporting the named backend.

Other computers may require a different screen backend or terminal personality.

Before adding extension-loading commands to your startup file, test them individually at the command prompt.

Once you've confirmed that they work correctly, you can add them to `STARTUP.SUB`.

Chapter 7 explains how to configure startup commands.

## 8.3 Listing Installed Extensions

Before changing the resident environment, it's useful to see which extensions are currently installed.

BetterCP/M provides separate commands for examining CPXs and RSXs.

### Listing CPXs

Enter:

```text
A>CPX LIST
```

BetterCP/M displays information about the configured command processor extensions.

The list can help you identify which resident command packages are available and determine whether an optional extension is present.

An extension's appearance in the configured list does not necessarily mean it loaded successfully. If an extension could not be loaded, BetterCP/M may retain its configured entry while reporting a warning.

This distinction is useful when troubleshooting missing resident commands.

### Listing RSXs

To examine the installed resident system extensions, enter:

```text
A>RSX LIST
```

BetterCP/M displays the currently installed RSXs.

This is useful when checking which services are available or determining whether an extension is still occupying memory.

The two lists serve different purposes. `CPX LIST` describes the resident command environment, while `RSX LIST` describes the installed resident system services.

## 8.4 Loading and Unloading Extensions

BetterCP/M allows optional extensions to be added to or removed from the active operating environment.

This makes it possible to customize the system for different tasks without permanently incorporating every available facility.

### Loading a CPX

To load a command processor extension, use the CPX management command.

For example, an extension named `TOOLS.CPX` would be requested with:

```text
A>CPX LOAD TOOLS
```

The extension must be available in the appropriate location and must be compatible with the running BetterCP/M system.

Once successfully loaded, its commands become available through the normal command environment.

You can enter those commands just as you would any other BetterCP/M command.

More than one CPX can be active at the same time. BetterCP/M maintains them in a defined order, which determines how their commands are considered when you enter a command name.

Ordinarily, you need not be concerned with that order unless two extensions provide commands with the same name.

### Unloading a CPX

To remove an optional CPX, use:

```text
A>CPX UNLOAD TOOLS
```

After the extension has been removed, its commands are no longer available as resident commands.

If corresponding transient programs are present, they may still be executed normally.

Unloading an optional CPX is useful when you no longer need its commands or want to change the resident command environment.

### Loading an RSX

To load an RSX, use the RSX command.

For example:

```text
A>RSX LOAD ADM3A
```

requests the ADM-3A terminal personality.

Some RSXs depend on other extensions being loaded first.

Terminal personalities, for example, require a suitable screen backend. The backend provides the connection to the computer's display, while the terminal personality interprets the control sequences expected by applications.

The required loading order is described in Chapter 9.

### Unloading an RSX

To remove an RSX, enter:

```text
A>RSX UNLOAD ADM3A
```

BetterCP/M removes the extension when it can safely do so.

An extension that is still needed by another resident component cannot necessarily be unloaded immediately.

For example, a screen backend should not be removed while a terminal personality that depends on it remains active.

In such cases, unload the dependent extension first.

The RSX manager checks these relationships and reports operations that cannot be performed safely.

### Required Extensions

Not every resident component is necessarily optional.

Some facilities are part of the standard command environment or are required for the system to operate correctly.

BetterCP/M's extension-management facilities enforce the applicable restrictions.

If an extension cannot be removed, consult the reported message rather than attempting to bypass the restriction.

## 8.5 Extension Persistence

One of the distinguishing characteristics of BetterCP/M's resident extension system is that supported extensions remain available across ordinary warm boots.

In conventional CP/M, a warm boot returns control to the command environment after a program terminates.

BetterCP/M retains this behavior while preserving the resident extensions that are intended to survive.

For example, suppose you've loaded a terminal monitor and then started a full-screen editor.

When you leave the editor and return to the command prompt, the terminal monitor remains installed.

You can start another compatible application without loading the monitor again.

Similarly, command processor extensions remain available as the command environment is restored after transient programs finish.

### Cold Boots and Startup Configuration

A cold boot establishes a new operating session and loads the configured startup environment.

If you want a particular extension available after every cold boot, include the appropriate loading commands in your startup configuration.

The standard BetterCP/M startup arrangement uses `STARTUP.SUB`, which is executed during a cold boot.

You can add extension-loading commands to this file.

For example:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

These commands load the screen backend, activate the ADM-3A terminal personality, and clear the display.

The example is appropriate only for systems supporting the named backend.

Other computers may require a different screen backend or terminal personality.

Before adding extension-loading commands to your startup file, test them individually at the command prompt.

Once you've confirmed that they work correctly, you can add them to `STARTUP.SUB`.

Chapter 7 explains how to configure the startup command.

## 8.6 Memory Considerations

Resident extensions are loaded into memory and remain available until they are removed or the operating environment is reinitialized.

Because CP/M systems have limited memory, the number and size of loaded extensions can matter.

### Available Program Memory

Ordinary CP/M programs execute in the Transient Program Area, or TPA.

Resident extensions use memory that would otherwise be available to those programs.

Consequently, loading an extension can reduce the maximum size of a transient program that BetterCP/M can execute.

For example, you might load a terminal monitor to run a full-screen editor. While the monitor is active, less memory is available to the editor.

If you later want to run a particularly large program that doesn't require terminal emulation, you can unload the monitor and recover the memory it occupied.

This flexibility is one of the advantages of BetterCP/M's extension system.

### Choosing Which Extensions to Load

There's no particular advantage to loading every available extension simply because it exists.

Instead, consider which facilities you actually use.

Frequently used commands may be worth keeping resident.

A terminal monitor may be essential when running a particular application but unnecessary when using ordinary command-line utilities.

Specialized extensions can be loaded when needed and removed afterward.

### Extension Dependencies

Some extensions depend on other resident components.

For example, a terminal personality may require a particular screen backend.

These dependencies affect the order in which extensions must be loaded and unloaded.

In general, load the supporting component first, followed by the extension that uses it.

When removing them, reverse the order.

Chapter 9 provides examples involving terminal monitors.

### Recovering from Extension Problems

Resident extensions are normally straightforward to manage, but occasionally an extension may be missing, damaged, incompatible, or incorrectly configured.

BetterCP/M provides safeguards intended to prevent an unusable optional extension from making the entire command environment unavailable.

If an optional CPX cannot be loaded or fails validation, BetterCP/M may display:

```text
CPX?
```

The system continues to the command prompt with the remaining usable extensions.

Commands supplied by the rejected CPX will not be available.

The extension may nevertheless remain in the configured list, so its appearance in `CPX LIST` does not necessarily indicate that it loaded successfully.

To remove an unusable optional extension, enter:

```text
A>CPX UNLOAD BAD
```

where `BAD` is the name of the affected extension.

Alternatively, replace the damaged extension file with a valid copy.

Until the problem is corrected, the warning may recur when BetterCP/M restores the command environment.

If BetterCP/M refuses to unload an RSX, another extension may still depend on it. Unload the dependent extension first, then remove the supporting component.

If a transient program reports insufficient memory, examine the resident extensions currently loaded. Unloading unnecessary extensions can restore memory to the TPA.

For additional troubleshooting information, see Chapter 12.

---

# Chapter 9 — Terminal Support

BetterCP/M provides terminal-monitor facilities that allow programs written for different terminal types to operate on supported computers.

If you've used CP/M for any length of time, you've probably encountered programs that expect a particular terminal. A full-screen editor, for example, may need to know how to move the cursor, clear part of the screen, or display text in reverse video.

Different terminals use different control sequences to perform these operations. A program configured for one terminal may not display correctly on another.

BetterCP/M addresses this problem through **loadable terminal monitors**. These provide familiar terminal environments without requiring every application to understand the particular computer's display hardware.

BetterCP/M 1.0 includes support for Montezuma Micro-style ADM-3A, VT52, and a supported subset of ANSI/VT100 terminal operation.

This chapter explains how to select, load, and use these facilities. For complete RSX command syntax, consult Part II, *Command and Utility Reference*.

## 9.1 The BetterCP/M Terminal Monitor

In conventional CP/M, the BIOS provides the basic console input and output services used by application programs.

These services are sufficient for ordinary character input and output, but full-screen applications often require additional capabilities.

A text editor, for example, may need to move the cursor to a particular position, clear the remainder of a line, or scroll part of the screen.

Historically, CP/M applications often supported several terminal types. The user selected the appropriate terminal during installation or configuration.

BetterCP/M retains this approach while providing additional terminal support through resident extensions.

### Terminal Personalities

A **terminal personality** interprets the control sequences associated with a particular terminal.

For example, an ADM-3A personality recognizes the screen-control conventions used by compatible ADM-3A applications.

A VT52 personality recognizes the supported control sequences used by programs configured for a VT52 terminal.

An ANSI personality provides a supported subset of ANSI/VT100 terminal behavior.

Only one terminal personality can be active at a time.

### Screen Backends

A terminal personality does not communicate directly with every possible display device.

Instead, it uses a **screen backend** that provides the connection to the computer's actual display environment.

For example, BetterCP/M provides a screen backend for the TRS-80 Model 4 and another for systems using a compatible ANSI host terminal.

This arrangement allows the same terminal personality to be used with different display systems.

From the user's perspective, the important distinction is straightforward:

- The terminal personality determines which terminal control sequences an application can use.
- The screen backend determines how those operations appear on the computer's display.

Both must be suitable for the system you're using.

### Loading a Terminal Monitor

Terminal monitors are loaded using BetterCP/M's RSX command.

The usual procedure is to load the appropriate screen backend first, followed by the desired terminal personality.

For example:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

This loads the Model 4 screen backend, activates the ADM-3A personality, and clears the screen.

On a system using the ANSI screen backend, the corresponding commands would be:

```text
RSX LOAD ANSISCRN
RSX LOAD ADM3A
CLS
```

The correct backend depends on the computer or emulator.

The *BetterCP/M Supported Platforms* documentation identifies the appropriate screen backend for each supported environment.

## 9.2 Selecting a Terminal Personality

Before running a full-screen application, determine which terminal types it supports.

Many CP/M programs provide an installation or configuration utility that allows you to select a terminal.

Others have terminal-specific versions or require a configuration file.

For example, an editor might offer several choices:

```text
ADM-3A
VT52
VT100
```

Choose the terminal personality that matches the BetterCP/M monitor you intend to use.

If the program is configured for VT52, load BetterCP/M's VT52 personality before starting it.

If the program expects ADM-3A control sequences, use the appropriate ADM-3A personality.

The terminal monitor does not automatically detect which terminal type an application expects.

### Changing Personalities

Only one terminal personality can be active at a time.

To change from one personality to another, unload the current personality before loading the replacement.

For example, to change from ADM-3A to VT52:

```text
RSX UNLOAD ADM3A
RSX LOAD VT52
CLS
```

If the appropriate screen backend is already loaded, you can continue using it.

There is no need to unload and reload the backend merely to change terminal personalities, provided the backend supports the new personality.

### Returning to the Basic Console

If you no longer need terminal emulation, unload the active personality.

For example:

```text
RSX UNLOAD VT52
```

You can then unload the screen backend if no other extension requires it:

```text
RSX UNLOAD M4SCRN
```

Removing the monitor releases the memory it occupied, making more memory available to ordinary programs.

This can be useful when running applications that do not require full-screen terminal support.

## 9.3 ADM-3A Support

BetterCP/M provides an ADM-3A terminal personality intended particularly for software using the Montezuma Micro-style ADM-3A conventions found on historical TRS-80 Model 4 CP/M systems.

The extension is supplied as:

```text
ADM3A.RSX
```

It can be used with either the Model 4 screen backend or the ANSI screen backend, depending on the platform.

### Using ADM-3A on the Model 4

On a TRS-80 Model 4 system, the screen backend is:

```text
M4SCRN.RSX
```

To load the ADM-3A environment:

```text
A>RSX LOAD M4SCRN
A>RSX LOAD ADM3A
A>CLS
```

The Model 4 distribution normally loads the appropriate backend and ADM-3A personality during startup.

If they are already installed, there is no need to load them again.

### Using ADM-3A with an ANSI Host Terminal

On a system using the ANSI screen backend, load:

```text
A>RSX LOAD ANSISCRN
A>RSX LOAD ADM3A
A>CLS
```

The ANSI backend translates the supported display operations into sequences understood by the host terminal.

For best results, use a compatible terminal emulator.

### Testing ADM-3A Support

BetterCP/M supplies a test utility named:

```text
ADMTST.COM
```

After loading the appropriate terminal monitor, enter:

```text
A>ADMTST
```

The utility displays a series of test screens and prompts designed to exercise the supported ADM-3A facilities.

These include cursor movement, reverse video, line operations, and other display functions.

The test also requests several keyboard characters to help confirm that the terminal environment is receiving the expected input.

### Compatibility Considerations

The ADM-3A personality is intended to support the conventions used by compatible CP/M applications.

It does not make all programs written for a particular computer automatically portable.

A program that communicates directly with display hardware rather than using the supported console interface may still require its original hardware environment.

For ordinary terminal-oriented applications, however, the monitor provides a convenient way to reproduce the expected display behavior.

## 9.4 VT52 Support

The DEC VT52 was a widely supported video terminal, and many CP/M applications can be configured to use its control sequences.

BetterCP/M provides a loadable VT52 personality named:

```text
VT52.RSX
```

The same VT52 extension can be used on different supported platforms by loading the appropriate screen backend.

### Loading the VT52 Monitor

On a TRS-80 Model 4:

```text
A>RSX LOAD M4SCRN
A>RSX LOAD VT52
A>CLS
```

On a system using the ANSI screen backend:

```text
A>RSX LOAD ANSISCRN
A>RSX LOAD VT52
A>CLS
```

These examples assume that no other terminal personality is currently active.

If another personality is loaded, unload it first.

For example, if ADM-3A is active:

```text
A>RSX UNLOAD ADM3A
A>RSX LOAD VT52
A>CLS
```

You can retain the existing screen backend when changing personalities, provided it supports VT52.

### Configuring Applications for VT52

When installing or configuring a full-screen application, select VT52 as its terminal type.

The application will then send VT52 control sequences for operations such as moving the cursor or clearing portions of the display.

BetterCP/M's VT52 personality interprets the supported sequences and passes the corresponding display operations to the screen backend.

For systems using an ANSI host terminal, the host terminal should provide a suitable display area. An 80-column, 24-row configuration is appropriate for the supplied VT52 support.

### Testing VT52 Support

BetterCP/M supplies a test utility named:

```text
VT52TST.COM
```

After loading the VT52 personality, enter:

```text
A>VT52TST
```

The utility exercises supported VT52 operations, including cursor positioning, tab stops, display erasure, and terminal identification.

It pauses during the test so you can examine the results.

If the display behaves as expected, the monitor is ready for compatible applications.

### VT52 Compatibility

BetterCP/M's VT52 personality supports the terminal facilities needed by compatible applications, but it is not intended to reproduce every possible hardware characteristic of a physical VT52.

Graphics facilities, specialized keypad modes, and host keyboard translation are outside the supported subset.

In particular, the monitor does not guarantee that the host computer's arrow keys will generate the control characters expected by every application.

These details depend on the computer, terminal emulator, and application configuration.

For ordinary full-screen programs using supported VT52 control sequences, the monitor provides a convenient portable terminal environment.

## 9.5 ANSI/VT100 Support

BetterCP/M also provides an ANSI terminal personality supporting a subset of the control sequences commonly associated with ANSI and DEC VT100 terminals.

This is particularly useful for programs that expect cursor positioning, screen erasure, character attributes, and other ANSI-style display operations.

The extension is supplied as:

```text
ANSI.RSX
```

As with the ADM-3A and VT52 personalities, ANSI support requires a suitable screen backend.

### Loading the ANSI Monitor

On a TRS-80 Model 4:

```text
A>RSX LOAD M4SCRN
A>RSX LOAD ANSI
A>CLS
```

On a system using the ANSI screen backend:

```text
A>RSX LOAD ANSISCRN
A>RSX LOAD ANSI
A>CLS
```

If another terminal personality is active, unload it before loading ANSI.

For example, to change from ADM-3A to ANSI while retaining the Model 4 screen backend:

```text
A>RSX UNLOAD ADM3A
A>RSX LOAD ANSI
A>CLS
```

### Supported Display Facilities

The ANSI personality provides a useful selection of common terminal operations.

These include cursor movement, screen and line erasure, character attributes, scrolling regions, cursor save and restore, and cursor visibility.

The supported character attributes include facilities such as reverse video.

The actual appearance of an attribute depends on the display hardware.

For example, a monochrome display cannot reproduce the full range of colors available on a modern ANSI terminal.

BetterCP/M provides the supported logical terminal behavior, while the screen backend determines how it appears on the physical display.

### Testing ANSI Support

BetterCP/M supplies:

```text
ANSITST.COM
```

After loading the ANSI personality, enter:

```text
A>ANSITST
```

The test utility demonstrates several supported ANSI display operations.

These include cursor positioning, reverse video, erasure, and related screen-control behavior.

The test pauses so you can inspect the display.

### ANSI Is Not Complete VT100 Emulation

Although the ANSI personality supports many familiar ANSI/VT100 operations, it does not provide complete VT100 emulation.

Some specialized facilities are not supported, including terminal-status queries, character-set selection, keypad modes, and switching into VT52 mode.

Programs requiring these facilities may not operate correctly.

For this reason, selecting VT100 in an application's installation program does not automatically guarantee compatibility.

Where possible, consult the application's terminal requirements and use the supplied test utilities to verify the display environment.

### Display Dimensions

Some full-screen programs assume a particular number of rows and columns.

For example, a program may expect an 80-column display with 24 or 25 rows.

BetterCP/M's terminal monitor cannot always compensate for an application configured for the wrong screen dimensions.

When configuring a program, select the screen size appropriate to the computer or terminal emulator you're using.

This is particularly important when moving applications between the Model 4's display and a modern host terminal.

## 9.6 Configuring Applications for Your Terminal

The terminal monitor provides the display environment, but applications must still be configured to use it.

Many CP/M applications include a terminal-installation program or configuration procedure.

Others provide several executable versions, each intended for a particular terminal.

Before running a full-screen application, determine which terminal types it supports.

### Choosing a Terminal Type

If an application supports ADM-3A, VT52, or ANSI/VT100, select the type corresponding to the BetterCP/M personality you've loaded.

For example, if you intend to use BetterCP/M's VT52 monitor, configure the application for VT52.

If the application is already configured for ADM-3A, load the ADM-3A personality instead.

The terminal personality and application configuration must agree.

A program configured for VT52 will not necessarily display correctly when the ADM-3A personality is active.

### A Typical Setup Procedure

Suppose you've obtained a full-screen editor that supports VT52.

A typical procedure would be:

1. Load the appropriate screen backend.
2. Load the VT52 personality.
3. Clear the screen.
4. Run `VT52TST` to check the terminal environment.
5. Configure the editor for VT52 operation.
6. Start the editor.

For example, on a system using the ANSI screen backend:

```text
A>RSX LOAD ANSISCRN
A>RSX LOAD VT52
A>CLS
A>VT52TST
A>EDITOR
```

Here, `EDITOR` represents the application you've installed.

The actual configuration procedure depends on the application.

### When the Display Looks Wrong

If a full-screen program produces misplaced text, unexpected characters, or incorrect cursor movement, the first thing to check is the terminal configuration.

Make sure the program is configured for the personality currently loaded.

You can examine the installed RSXs with:

```text
A>RSX LIST
```

If the wrong personality is active, unload it and load the correct one.

If the correct personality is loaded but the display is still incorrect, run the corresponding terminal test utility.

If the test works but the application does not, examine the application's terminal settings and screen-size assumptions.

Some applications use terminal capabilities that are not supported by BetterCP/M's monitor. Others communicate directly with hardware rather than using the standard console interface.

Such programs may require their original hardware environment or additional configuration.

### Loading Your Preferred Terminal at Startup

If you regularly use applications requiring a particular terminal, you can load the corresponding personality automatically during system startup.

For example, a Model 4 system might include the following commands in `STARTUP.SUB`:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

This establishes the ADM-3A environment whenever BetterCP/M performs a cold boot.

Ordinary warm boots preserve the installed monitor, so it remains available while you work.

You can still unload it or change personalities during the session.

Chapter 7 explains how to configure startup commands, while Chapter 8 provides more information about managing resident extensions.

### Returning to the Basic Console

When you no longer need terminal emulation, unload the active personality and then its screen backend.

For example:

```text
A>RSX UNLOAD VT52
A>RSX UNLOAD ANSISCRN
```

The screen backend can be removed only when no remaining extension requires it.

Unloading the monitor releases its resident memory, making that space available to transient programs.

If you subsequently need terminal emulation again, simply reload the appropriate backend and personality.

---

# Chapter 10 — Working with Disks

BetterCP/M provides utilities for preparing, copying, checking, and installing system disks. These facilities are useful whether you're maintaining an existing BetterCP/M installation, preparing additional working disks, or experimenting with different CP/M disk formats.

If you've used conventional CP/M, you'll already be familiar with the distinction between copying files and copying an entire disk. BetterCP/M retains that distinction while providing additional facilities for working with different disk formats and system configurations.

Two utilities are particularly important:

**DUP** handles disk formatting, copying, and checking.

**SYSGEN** installs BetterCP/M onto a prepared disk or saves an installed operating system as a system-image file.

The two utilities complement one another. DUP prepares and copies disks, while SYSGEN installs and preserves the operating system itself.

This chapter explains how to perform common disk-management operations. Complete command syntax and options are provided in Part II, *Command and Utility Reference*.

Because disk-management operations can destroy existing data, read the instructions carefully before formatting or copying a disk.

## 10.1 Disk Formats

CP/M was used on a remarkable variety of computers, and those computers did not all use the same disk formats.

Even disks of the same physical size could differ in their number of tracks, sectors, recording density, and filesystem organization.

Consequently, a disk prepared on one CP/M computer might not be readable on another without suitable configuration.

BetterCP/M provides facilities for working with different disk formats, subject to the capabilities of the computer and its disk controller.

### Physical and Logical Drives

As discussed in Chapter 7, BetterCP/M distinguishes between physical and logical drives.

A **physical drive** is the actual disk drive or storage device.

A **logical drive** is the drive letter, such as `A:` or `B:`, through which BetterCP/M accesses that device.

A logical drive is associated with a physical device and a disk-format definition.

For example, logical drive B might be configured to use a physical drive containing disks prepared in a particular CP/M format.

The available assignments depend on the computer and its BIOS.

### Disk-Format Definitions

BetterCP/M uses disk-format definitions to describe how disks are organized.

These definitions tell the system how to access the sectors and filesystem structures of a particular format.

Rather than requiring users to enter all the necessary parameters each time, BetterCP/M provides a catalog of disk-format definitions.

The CONFIG utility allows you to select an appropriate definition and associate it with a logical drive.

For example:

```text
A>CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="MM 80T DS DATA"
```

This assigns logical drive C to physical drive 1 using the named disk format.

The format name must match an available definition, and the requested format must be compatible with the selected physical drive.

The example illustrates the command's use; the correct format depends on the disk and hardware you're using.

### Selecting the Correct Format

Before accessing a disk, make sure its format matches the definition assigned to the logical drive.

Using an incorrect definition may cause the disk to appear unreadable or produce errors when accessing files.

More seriously, writing to a disk using an incorrect format definition can damage existing data.

If you're uncertain about a disk's format, avoid writing to it until you've identified the correct configuration.

The CONFIG utility provides facilities for examining and changing disk assignments.

For more information, see Chapter 7, *Configuring BetterCP/M*.

## 10.2 Formatting Disks

Formatting prepares a disk for use by establishing its physical track and sector organization.

BetterCP/M provides the **DUP** utility for this purpose.

DUP can format disks, copy entire disks, and check disks for physical read errors.

To start DUP interactively, enter:

```text
A>DUP
```

The utility displays a menu similar to:

```text
A  Format a disk
B  Copy a disk
C  Check a disk for errors
```

Select the operation you want to perform.

### Formatting a Disk

To format a disk, select option A from the DUP menu.

DUP asks you to identify the destination drive.

The format used is the one currently assigned to that logical drive.

If the drive isn't configured for the format you want, exit DUP and use CONFIG to select the appropriate format first.

DUP checks whether the requested operation is supported by the drive and its disk-format definition.

It then displays a warning that formatting will destroy the existing contents of the destination disk.

**Formatting erases the disk's previous contents. Make absolutely certain you've selected the correct drive before confirming.**

DUP requires explicit confirmation before proceeding.

Only an affirmative response allows formatting to begin.

### Formatting from the Command Line

DUP also provides a direct command-line form.

For example:

```text
A>DUP /FORMAT B:
```

requests formatting of drive B using its currently assigned disk format.

The command still requires confirmation. The command-line form does not bypass the normal safeguards.

### Format Verification

DUP verifies its formatting operations by reading back the formatted tracks.

This helps identify disks or drives that cannot reliably perform the requested operation.

When formatting completes successfully, DUP reports:

```text
Format complete.
```

If an error occurs, DUP reports the problem.

An interrupted or failed format should not be treated as a successfully prepared disk.

### Protected System Drive

BetterCP/M protects the physical system drive from destructive DUP operations.

In the current implementation, physical drive 0 cannot be used as the destination for formatting or disk copying.

This protection follows the physical drive, even if logical drive letters have been reassigned.

Other drives may be used as destinations when their configurations support the requested operation.

### A Note About Available Formats

Not every disk format listed in BetterCP/M's format catalog can necessarily be created by every supported computer.

Some formats may be readable but cannot be written or formatted by a particular disk controller or emulator.

DUP reports unsupported operations rather than silently substituting another format.

Consult the platform documentation for information about the formats supported by your hardware.

## 10.3 Copying Disks

Copying an entire disk is different from copying individual files.

When you use the COPY command, BetterCP/M copies the selected files from one location to another.

When you use DUP's disk-copying facility, BetterCP/M copies the disk's contents, including its system areas, directories, and file data.

This makes DUP particularly useful for preparing duplicate working disks or making backups of complete disks.

### Starting a Disk Copy

Start DUP:

```text
A>DUP
```

Select option B, *Copy a disk*.

DUP asks you to select a source drive and a destination drive.

Alternatively, you can start the operation directly:

```text
A>DUP /COPY A: B:
```

This requests a copy from drive A to drive B.

The source disk is read, while the destination disk is written.

**All existing contents of the destination disk will be replaced.**

Make sure you've selected the correct drives before confirming.

### Using Two Drives

BetterCP/M 1.0 requires two different physical drives for DUP's disk-copying operation.

It does not support copying a disk by repeatedly swapping source and destination media in a single drive.

The destination must also satisfy the system's drive restrictions. In particular, physical drive 0 is protected against destructive disk-copy operations.

### Copying Between Different Formats

DUP uses the disk-format definitions currently assigned to the source and destination drives.

If the destination's format differs from the source, DUP can prepare the destination to match the source format, provided the operation is supported by the hardware.

DUP informs you when the destination will be reformatted.

This is an important warning: **the destination's previous contents will be destroyed, even if its original format was different from the source.**

After checking the displayed source and destination drives, confirm the operation to proceed.

### Copy Verification

DUP verifies copied data by reading it back from the destination and comparing it with the source data.

When the operation completes successfully, DUP reports:

```text
Copy complete; destination verified.
```

This indicates that the data copied by DUP has been verified.

If a read, write, or verification error occurs, DUP reports the problem.

An interrupted or failed copy may leave the destination only partly written. Do not rely on such a disk as a complete backup.

### After Copying

If DUP temporarily changed the destination's disk-format assignment during copying, it restores the previous assignment when the operation finishes.

This does not restore the disk's former physical format.

The disk now contains a copy of the source, so you may need to use CONFIG to assign the copied format before accessing it normally.

If you intend to use that format regularly, you can save the new configuration as a startup default.

Chapter 7 explains drive configuration in more detail.

## 10.4 Checking Disks

DUP can also check a disk for physical read errors.

This is useful when examining an unfamiliar disk, investigating suspected media problems, or checking whether a disk can be read reliably.

### Starting a Disk Check

Start DUP:

```text
A>DUP
```

Select option C, *Check a disk for errors*.

DUP asks you to select the drive to examine.

Alternatively, enter:

```text
A>DUP /CHECK B:
```

This checks the disk in drive B.

### What DUP Checks

DUP reads the sectors described by the disk-format definition assigned to the selected drive.

It reports sectors that cannot be read successfully.

The operation does not modify the disk's contents.

Unlike formatting and copying, checking a disk does not require confirmation before proceeding.

### Understanding the Results

As DUP checks the disk, it reports read errors and their locations.

When the check completes, it displays a summary similar to:

```text
Check complete. Unreadable sectors: 0
```

A count of zero means that DUP was able to read the sectors examined during that operation.

A nonzero count indicates that one or more sectors could not be read successfully.

### What a Disk Check Does Not Do

DUP's disk check is a test of physical readability.

It does not repair damaged sectors, reconstruct lost files, or examine the logical consistency of the CP/M filesystem.

It also does not compare the disk against another disk to determine whether their contents match.

A disk can therefore pass DUP's readability check while still containing damaged or incorrect files.

If you suspect that important data has been corrupted, compare it with a known good copy or restore it from a backup.

### Interrupting a Check

You can interrupt a disk check with `Ctrl-C`.

Because the operation only reads the disk, interrupting it does not modify the disk's contents.

However, an interrupted check is incomplete and should not be treated as evidence that the entire disk is readable.

## 10.5 Installing the Operating System

Formatting a disk prepares its physical organization, but it does not necessarily make the disk bootable.

A CP/M system disk must also contain the operating system in the locations expected by the computer's bootstrap mechanism.

BetterCP/M provides **SYSGEN** for installing the operating system onto a suitably prepared disk.

### What SYSGEN Does

SYSGEN writes the BetterCP/M operating-system image into the disk's reserved system area.

It does not format the disk.

It also does not copy ordinary `.COM` programs, utilities, or other files into the filesystem.

Consequently, preparing a complete system disk may involve several operations:

1. Configure the appropriate disk format.
2. Format the disk if necessary.
3. Install BetterCP/M using SYSGEN.
4. Copy the required utilities and supporting files onto the disk.

The exact procedure depends on the disk format and computer.

### Installing from Another System Disk

SYSGEN can install BetterCP/M using an existing system disk as its source.

For example:

```text
A>SYSGEN A: B:
```

requests installation of the operating system from drive A onto drive B.

The source and destination must be different physical drives.

As with DUP, BetterCP/M protects physical drive 0 against destination writes.

### Installing from a System-Image File

SYSGEN can also install BetterCP/M from a system-image package.

For example:

```text
A>SYSGEN SYSTEM.SYS B:
```

installs the operating system contained in `SYSTEM.SYS` onto drive B.

The package must be a valid BetterCP/M system image suitable for the destination.

A drive-qualified filename can also be used:

```text
A>SYSGEN C:SYSTEM.SYS B:
```

This reads the system-image package from drive C and installs it onto drive B.

### Confirming Installation

Before writing the system area, SYSGEN checks the destination and requests confirmation.

It displays a warning similar to:

```text
The destination system area will be replaced.
Files outside the reserved system tracks will be preserved.
Proceed (Y/N)?
```

Check the destination carefully.

Only an affirmative response allows installation to proceed.

SYSGEN verifies the system records it writes.

When installation completes successfully, it reports:

```text
System installed and verified. The destination is bootable.
```

This confirms that the operating-system image has been installed and verified.

It does not mean that every utility or supporting file required for your preferred working environment has been copied to the disk.

### Existing Files

Unlike formatting, SYSGEN is designed to preserve ordinary files outside the reserved system area.

This allows you to update or replace the installed operating system without necessarily erasing the disk's filesystem.

However, SYSGEN replaces the system-area contents.

If an installation is interrupted or fails, the destination may no longer contain a complete bootable operating system.

Keep a working system disk available when performing system installation or maintenance.

## 10.6 Backing Up and Restoring System Disks

A reliable backup is particularly important when working with system disks.

A damaged or incorrectly configured system disk may prevent your computer from booting, even if its ordinary files remain intact.

BetterCP/M provides several ways to preserve system disks and their contents.

### Making a Complete Disk Copy

For a complete disk backup, use DUP.

For example:

```text
A>DUP /COPY A: B:
```

This copies the source disk to the destination, including the system area and ordinary file contents represented by the disk format.

The destination must be suitable for the operation, and its previous contents will be replaced.

DUP verifies the copied data before reporting successful completion.

A complete disk copy is often the simplest way to preserve a working system configuration.

### Saving the Operating System to a File

SYSGEN provides another useful facility: saving the installed operating system as a system-image package.

For example:

```text
A>SYSGEN A:
```

saves the operating system installed on drive A as `SYSTEM.SYS` in the current drive and user area.

You can also specify a destination filename:

```text
A>SYSGEN A: B:BASE090.SYS
```

This saves the installed system from drive A into the named package on drive B.

The package contains the operating-system image and its saved configuration information.

It does not contain ordinary files from the source disk.

### Maintaining Several System Configurations

System-image packages are particularly useful when maintaining several BetterCP/M configurations.

For example, you might preserve separate images for different drive arrangements or hardware configurations.

Each can be saved under a descriptive filename.

When you want to restore a particular configuration, install its package using SYSGEN.

For example:

```text
A>SYSGEN B:BASE090.SYS C:
```

This installs the saved system image onto drive C after the normal confirmation.

The destination must have a compatible system area.

### Restoring a System Disk

If a system disk becomes damaged, the appropriate recovery procedure depends on the extent of the damage.

If only the installed operating system has been affected, you may be able to reinstall it using SYSGEN while preserving ordinary files.

If the disk's physical format or filesystem has been damaged, a complete restoration from a known good disk copy may be necessary.

If the disk itself is unreliable, replace the media before attempting restoration.

### Protecting Your Backups

A backup is useful only if it can be read when needed.

For important system disks, consider maintaining more than one copy.

Keep at least one backup separate from the working system.

After preparing a backup, verify that it can be read successfully. When practical, test that a backup system disk can actually boot the computer.

Remember that a system-image package and a complete disk backup serve different purposes.

**A system-image package preserves the installed operating system. A complete disk copy preserves the disk's contents, including ordinary files.**

Both can be valuable when maintaining a BetterCP/M system.

---

These specifications resolve the uncertainties in Chapter 11. In particular, **BetterCP/M 1.0 implements the TIME utility's SET interface, but neither of its currently supported clock providers permits setting the clock.**

That distinction needs to be explicit in the User's Guide.

I've now read all three documents:

- [134 — FreHD Clock Provider](https://github.com/CPMArchives/BetterCPM/blob/main/docs/engineering/134%20FreHD%20Clock%20Provider.md)
- [135 — z80pack Clock Provider](https://github.com/CPMArchives/BetterCPM/blob/main/docs/engineering/135%20z80pack%20Clock%20Provider.md)
- [205 — TIME Utility SET](https://github.com/CPMArchives/BetterCPM/blob/main/docs/engineering/205%20TIME%20Utility%20Set.md)

The principal corrections are:

| Subject | Verified BetterCP/M 1.0 behavior |
|---|---|
| Display time | `TIME` |
| Identify provider | `TIME /PROVIDER` |
| Request clock setting | `TIME /SET LL HH HR MN SC` |
| SET argument format | Five hexadecimal bytes, not a calendar date |
| FreHD provider | `FREHDCLK.RSX`, read-only |
| z80pack provider | `ZPRTC.RSX`, read-only |
| Missing provider | TIME reports that the service is unavailable |
| Unsupported SET | Provider returns a specific unsupported-operation error |
| P2DOS compatibility | Provided through a separate `P2DOS.RSX` frontend |
| Warm boots | Resident clock services survive ordinary warm boots |

The specifications also confirm that both providers have been tested with the actual TIME utility and that rejected SET requests leave the clock unchanged.

One point deserves special attention: the five-byte SET record contains a little-endian day count followed by packed-BCD hours, minutes, and seconds. That's quite different from the calendar-date input a user might reasonably expect.

Rather than documenting SET as a convenient way to adjust the clock, we should explain it as an implemented interface intended for providers that support setting, while noting that the two current providers are read-only.

---
+98
# Chapter 11 — Date and Time

BetterCP/M provides facilities for reading the system date and time through supported clock hardware or an emulator.

Unlike modern computers, many early CP/M systems did not have a built-in real-time clock. Some relied on external hardware, while others had no clock at all.

BetterCP/M accommodates these differences through loadable clock providers. A clock provider allows the operating system to obtain the current date and time without requiring applications to communicate directly with the clock hardware.

The **TIME** utility provides a convenient way to examine the system clock and identify the clock provider currently in use.

BetterCP/M 1.0 includes clock providers for FreHD and z80pack. Both support reading the clock, but neither supports changing it.

This chapter explains how to use these facilities. Complete command syntax and options are provided in Part II, *Command and Utility Reference*.

## 11.1 Clock Support

BetterCP/M provides a common clock interface that can be used with different hardware and emulated environments.

The interface separates the operating system's date and time services from the particular clock supplying the information.

For example, on a TRS-80 Model 4 equipped with FreHD, BetterCP/M can obtain the date and time through FreHD's clock interface.

Under z80pack, BetterCP/M can obtain the date and time from the clock facilities provided by the emulator.

Both arrangements use the same TIME utility.

### Clock Providers

Clock support is supplied by Resident System Extensions, or RSXs.

BetterCP/M 1.0 includes two clock providers:

| Provider | Environment | Extension |
|---|---|---|
| FreHD | TRS-80 Model 4 with FreHD | `FREHDCLK.RSX` |
| z80pack | z80pack/cpmsim | `ZPRTC.RSX` |

Neither provider is loaded automatically merely because its file is present on the system disk.

You must load the appropriate provider before using TIME.

For example, on a Model 4 equipped with FreHD:

```text
A>RSX LOAD FREHDCLK
```

Under z80pack:

```text
A>RSX LOAD ZPRTC
```

Once the provider is installed, TIME can obtain the current date and time.

You can examine the installed RSXs with:

```text
A>RSX LIST
```

### Read-Only Clock Support

Both BetterCP/M 1.0 clock providers are read-only.

They can obtain the date and time from their respective clock sources, but they do not change those clocks.

This does not prevent programs from using the current date and time.

It simply means that correcting an incorrect clock must be done through the facilities provided by the hardware, emulator, or host environment.

## 11.2 Displaying the Date and Time

To display the current date and time, enter:

```text
A>TIME
```

TIME obtains the date and time from the installed clock provider and displays the result.

The time shown is the time reported by the provider.

For example, under z80pack, the provider reads the emulator's clock interface.

On a Model 4 equipped with FreHD, the provider obtains the date and time maintained by FreHD.

### Identifying the Clock Provider

To determine which clock provider is installed, enter:

```text
A>TIME /PROVIDER
```

TIME displays information about the provider, including its name, supported interface version, and capabilities.

For example, this can help you determine whether BetterCP/M is using the FreHD or z80pack clock service.

Both supplied providers identify themselves as supporting clock reads but not clock setting.

### When No Provider Is Installed

If you enter TIME without first loading a clock provider, the utility cannot obtain the current date and time.

It reports that the required clock service is unavailable.

To correct this, load the appropriate provider for your system.

For example:

```text
A>RSX LOAD ZPRTC
A>TIME
```

If a provider is already installed but TIME still cannot obtain the clock, the underlying hardware or emulator may not be supplying valid clock information.

The appropriate remedy depends on the platform.

## 11.3 Setting the Date and Time

BetterCP/M's TIME utility includes a command for requesting that a clock be set.

However, **the FreHD and z80pack providers supplied with BetterCP/M 1.0 are read-only**.

Consequently, attempts to set the clock through either provider are rejected.

The SET facility is nevertheless implemented in TIME.COM and is available for use with clock providers that support it.

### The SET Command

The command has the following form:

```text
TIME /SET LL HH HR MN SC
```

The five arguments represent the date and time in BetterCP/M's native clock-record format.

Unlike the date-setting commands found in some operating systems, TIME does not accept an ordinary calendar-date string.

Instead, the arguments are five two-digit hexadecimal values.

The first two bytes represent the day count, with the low byte first. The remaining three bytes represent the hour, minute, and second in packed-BCD notation.

For example:

```text
A>TIME /SET 01 00 12 34 56
```

requests day 1 of the CP/M clock epoch, January 1, 1978, at 12:34:56.

The example illustrates the syntax. It will not set the clock when either of the standard BetterCP/M 1.0 providers is installed.

### Unsupported Clock Setting

When a clock provider does not support setting the clock, TIME reports that the operation is unsupported.

The existing clock value is not changed.

This is the expected result with both `FREHDCLK.RSX` and `ZPRTC.RSX`.

### Invalid Date and Time Values

TIME checks the supplied hexadecimal values before requesting a clock-setting operation.

For example, it rejects malformed hexadecimal arguments, invalid packed-BCD values, and out-of-range hours, minutes, or seconds.

Invalid command arguments produce a usage message.

For complete details of the accepted format, consult the TIME command reference.

## 11.4 Clock Providers

Although both supplied clock providers offer the same basic date-and-time service, they obtain their information differently.

### FreHD Clock Provider

The FreHD provider is supplied as:

```text
FREHDCLK.RSX
```

It obtains the date and time through FreHD's extended hardware interface.

FreHD maintains its clock information using a DS1307-compatible clock facility.

To use it:

```text
A>RSX LOAD FREHDCLK
A>TIME
A>TIME /PROVIDER
```

The provider supports dates from 2000 through 2099.

It is read-only and does not modify the FreHD hardware clock.

FreHD's clock interface is also supported by suitable emulator configurations, allowing the same provider to be used without requiring a physical FreHD device.

The actual availability of the clock depends on the computer or emulator configuration.

### z80pack Clock Provider

The z80pack provider is supplied as:

```text
ZPRTC.RSX
```

It obtains the date and time through the clock interface provided by z80pack/cpmsim.

To use it:

```text
A>RSX LOAD ZPRTC
A>TIME
A>TIME /PROVIDER
```

Like the FreHD provider, ZPRTC is read-only.

It does not change the emulator's clock or its operating mode.

The provider supports dates through 2099.

### Changing Providers

Clock providers are resident extensions.

You can examine and manage them using the RSX commands described in Chapter 8.

For example:

```text
A>RSX LIST
```

displays the installed extensions.

The corresponding RSX management commands can be used to unload a provider when it is no longer needed.

Applications using BetterCP/M's clock service obtain their information through the common clock interface, rather than communicating directly with either FreHD or z80pack.

## 11.5 Clock Availability and Reliability

The accuracy of BetterCP/M's date and time depends on the clock source.

If the underlying clock is incorrect, TIME will report an incorrect date or time.

If the source is unavailable or cannot provide a valid reading, TIME reports an error rather than inventing a time value.

### Clock Errors

A clock-reading operation may fail because the provider cannot communicate with the hardware or because the returned information is invalid.

For example, a FreHD clock request may fail if the controller is unavailable or does not respond correctly.

Similarly, a clock provider may reject a reading whose date or time fields are invalid.

BetterCP/M's clock providers check the information they receive before returning it to TIME.

### Reading the Clock During a Time Change

Clock values can change while they are being read.

For example, a program might begin reading the clock immediately before a minute changes.

BetterCP/M's providers account for this possibility.

The FreHD provider obtains a consistent clock sample through the FreHD interface.

The z80pack provider checks that its readings form a consistent timestamp and retries when necessary.

These measures help prevent applications from receiving inconsistent combinations of date and time fields.

They do not, however, correct an inaccurate underlying clock.

## 11.6 Compatibility with CP/M Clock Facilities

Digital Research CP/M 2.2 did not provide a standard general-purpose date-and-time service.

Consequently, different CP/M systems adopted different approaches to clock support.

One historically significant extension was the date-and-time interface provided by P2DOS.

BetterCP/M provides compatibility with this interface through a separate resident extension.

### P2DOS Compatibility

The compatibility extension is supplied as:

```text
P2DOS.RSX
```

It provides the P2DOS-compatible date-and-time interface for programs that use the corresponding BDOS functions.

P2DOS.RSX does not communicate directly with FreHD or z80pack.

Instead, it obtains clock services through BetterCP/M's installed clock provider.

This means that the same provider can serve both native BetterCP/M applications and programs using the P2DOS-compatible interface.

### Loading P2DOS Support

To use the P2DOS-compatible clock facilities, load an appropriate clock provider and the P2DOS extension.

For example, under z80pack:

```text
A>RSX LOAD ZPRTC
A>RSX LOAD P2DOS
```

Once installed, compatible programs can request clock information through the P2DOS interface.

As with the native TIME utility, the available operations depend on the provider.

Because the supplied providers are read-only, P2DOS-compatible requests to set the clock are not supported.

### Conventional CP/M Applications

Ordinary CP/M 2.2 applications do not require these extensions.

They continue to use the standard CP/M programming interfaces.

Applications that require date-and-time services, however, must use a supported clock interface and have access to an appropriate provider.

For programming details, consult the *BetterCP/M Developer's Guide* and the relevant engineering specifications.

---

# Chapter 12 — Troubleshooting

BetterCP/M is designed to provide a reliable CP/M operating environment, but sooner or later you're likely to encounter a command that doesn't behave as expected, a disk that can't be read, or a program that refuses to run.

Fortunately, many problems are straightforward to identify and correct.

Sometimes the cause is as simple as a mistyped filename or an incorrect drive selection. Other problems may involve disk formats, configuration settings, resident extensions, or the limitations of a particular computer.

This chapter describes common problems you may encounter when using BetterCP/M and suggests ways to resolve them.

It isn't intended to catalog every possible error message. The complete message reference appears in Appendix F, *System Messages and Error Reference*. Individual commands and utilities are documented in Part II, *Command and Utility Reference*.

When troubleshooting, it's generally best to begin with the simplest explanation before making changes to the system configuration.

## 12.1 Common Command Errors

### Command Not Found

If BetterCP/M doesn't recognize a command, it may display a question mark or another command-related error.

For example:

```text
A>MYPROG
?
```

This usually means that BetterCP/M couldn't locate the requested program.

First, check the spelling of the command.

If you're trying to run a transient program, make sure its `.COM` file is available.

BetterCP/M normally searches the current drive and user area first, followed by drive A, user area 0.

For example, if you're working in `B3:`, BetterCP/M will look for an unqualified transient program in `B3:` and then `A0:`.

You can examine these locations with:

```text
B3>DIR *.COM
B3>DIR A0:*.COM
```

If the program is elsewhere, you can specify its location explicitly.

For example:

```text
B3>C2:MYPROG
```

This requests `MYPROG.COM` from drive C, user area 2.

Remember that an explicitly qualified program name restricts the search to the specified location.

### A Command Doesn't Recognize an Option

Some BetterCP/M commands are available in both resident and transient versions.

The resident version generally provides the most frequently used operations, while the transient version may offer additional options.

For example, the resident DIR command doesn't provide every option available in `DIR.COM`.

If you enter:

```text
A>DIR /WHEREIS ED.COM
```

BetterCP/M may respond:

```text
DIR: Use :DIR.
```

This means the requested operation is available through the transient version.

Enter:

```text
A>:DIR /WHEREIS ED.COM
```

The colon tells BetterCP/M to execute the transient program rather than the resident command.

You can also use a period as the prefix.

If the transient program isn't available, BetterCP/M reports the normal command-lookup failure.

For more information, see Chapter 5, *The Command Environment*.

### Incorrect Command Syntax

If a command reports invalid syntax, check the order and spelling of its arguments.

Some BetterCP/M commands accept several forms, while others require arguments in a particular order.

For example, COPY and REN use different conventions for specifying source and destination files.

A command may also require an option to appear separately from its filename arguments.

Consult the command's reference entry in Part II for its accepted syntax.

### Unexpected Interactive Prompts

Some commands request confirmation before modifying or replacing files.

This can happen even when the command is executed from a SUBMIT file.

For example, COPY may ask how to handle an existing destination file.

When a prompt offers several abbreviated responses, entering `?` may display an explanation of the available choices.

If you're preparing a batch file, examine whether the command provides options for specifying its behavior without prompting.

For example, COPY supports `/B` for batch-oriented operation.

Chapter 6 explains batch processing in more detail.

## 12.2 File and Disk Problems

### File Not Found

If a command reports that a file cannot be found, begin by checking the current drive and user area.

For example:

```text
A>DIR
```

displays the files in the current location.

If you believe the file is on another drive or in another user area, specify that location:

```text
A>DIR B3:
```

Remember that files in different user areas are ordinarily treated as separate collections.

A file named `REPORT.TXT` in `A0:` is distinct from a file with the same name in `A5:`.

You can also use BetterCP/M's extended DIR facilities to search for a file.

For example:

```text
A>:DIR /WHEREIS REPORT.TXT
```

This searches the configured drives and user areas according to the transient DIR utility's file-location rules.

### Read-Only Files

If BetterCP/M refuses to modify or erase a file, check whether it has the read-only attribute.

Read-only protection is intended to prevent accidental changes.

Some utilities provide options for overriding this protection, but you should use them only when you're certain that the file should be modified.

If the file belongs to the operating system or an installed application, consider why it was protected before removing the attribute.

The STAT utility provides facilities for examining and changing file attributes.

### A Disk Has Become Read-Only

BetterCP/M may treat a disk as read-only when it cannot safely determine that the disk currently in a drive matches the directory information already held by the operating system.

This can happen after removable media have been changed.

The read-only condition helps prevent directory information from one disk being written to another.

If a disk becomes read-only unexpectedly, complete any active operation and use the appropriate disk-reset or warm-boot procedure before attempting further writes.

Do not attempt to bypass the protection by forcing a write.

If the problem persists, check the disk's write-protection setting and the drive configuration.

### A Disk Cannot Be Read

A disk-read failure can have several causes.

The disk may be damaged, the drive may not be ready, or BetterCP/M may be using the wrong disk-format definition.

Begin by checking that the correct disk is inserted and that the drive is available.

If the disk was prepared on another CP/M computer, verify that the assigned format matches the disk's actual organization.

Use CONFIG to examine the current drive configuration:

```text
A>CONFIG /SHOW
```

If the format is incorrect, select the appropriate definition before attempting further access.

**Avoid writing to a disk whose format you're uncertain about.** An incorrect format assignment can cause existing data to be damaged.

### Disk Full

A disk can run out of space even when its files appear relatively small.

CP/M allocates storage in blocks, and each file consumes one or more allocation blocks.

A disk can also run out of directory entries before its data area is completely full.

If BetterCP/M reports insufficient disk space or directory capacity, remove unnecessary files or copy them to another disk.

You may also be able to use a disk format with greater capacity, provided your hardware supports it.

Formatting a disk to change its organization destroys its existing contents, so preserve any important files first.

### Suspected Disk Errors

If a disk repeatedly produces read errors, DUP can examine its physical readability.

For example:

```text
A>DUP /CHECK B:
```

This checks the disk in drive B without modifying its contents.

DUP reports unreadable sectors and provides a summary when the check completes.

A successful check means the examined sectors could be read. It does not guarantee that the filesystem or individual files are logically correct.

If the disk contains important data, preserve a readable copy before attempting repairs or other changes.

Chapter 10 describes disk checking in more detail.

## 12.3 Configuration Problems

An incorrect configuration can make a drive unavailable, prevent a startup command from running, or cause a peripheral device to behave unexpectedly.

Fortunately, many configuration problems can be corrected without rebuilding the operating system.

### Examining the Current Configuration

When a configuration problem occurs, begin by examining the settings currently in use.

Enter:

```text
A>CONFIG /SHOW
```

CONFIG displays information about the active configuration and the settings saved for subsequent cold boots.

Pay particular attention to differences between the current settings and the saved defaults.

A drive that works during the current session may not be configured the same way after a cold boot.

Likewise, a temporary change may have been made without being saved.

### A Drive Is No Longer Available

If a logical drive becomes unavailable after a configuration change, check its assignment.

The drive may have been unbound, associated with an incompatible physical drive, or assigned an unsuitable disk format.

Use CONFIG to examine the available drives and their definitions.

If necessary, restore the appropriate assignment.

For example, a drive that was temporarily unbound can be assigned again using CONFIG's drive-configuration facilities.

The correct settings depend on the computer and the disk format.

### Configuration Changes Disappear After Restarting

Some CONFIG operations affect only the current session.

If you change a drive assignment but don't save the new configuration, the previous saved settings may be restored during the next cold boot.

This is normal behavior.

To make a configuration permanent, use CONFIG's save facilities.

Chapter 7 explains the distinction between temporary and saved settings.

### Device Assignments Don't Work

BetterCP/M retains CP/M's IOBYTE mechanism for selecting logical character devices.

However, selecting a device does not guarantee that the corresponding hardware exists or is supported by the BIOS.

If a printer, reader, punch, or other device does not respond, verify that the selected assignment is supported by your computer.

Remember that STAT changes the live IOBYTE, while CONFIG can save a value for subsequent disk cold boots.

Changing one does not necessarily change the other.

## 12.4 Extension Problems

BetterCP/M's resident extensions provide additional commands and system services, but problems can occur if an extension is missing, damaged, incompatible, or loaded in the wrong order.

### A CPX Command Is Missing

If a command normally provided by a CPX is unavailable, examine the configured extensions:

```text
A>CPX LIST
```

Check whether the expected extension is listed.

If it is missing, you may need to load it.

If it is listed but its commands remain unavailable, the extension may have failed to load.

An extension's appearance in the configured list does not necessarily guarantee that it is active.

### The CPX? Warning

If an optional CPX cannot be loaded or fails validation, BetterCP/M may display:

```text
CPX?
```

The system continues to the command prompt with the remaining usable extensions.

Commands supplied by the rejected CPX are unavailable.

You can remove the unusable extension from the configured environment.

For example:

```text
A>CPX UNLOAD BAD
```

where `BAD` is the name of the affected extension.

Alternatively, replace the extension file with a valid copy.

Until the problem is corrected, the warning may recur when BetterCP/M restores the command environment.

### An RSX Cannot Be Loaded

If an RSX fails to load, first check that its file is available and compatible with the running system.

Some RSXs also require supporting extensions.

For example, a terminal personality needs a suitable screen backend.

If you attempt to load a terminal personality without its required backend, the operation may fail.

Load the supporting component first, then try again.

### An RSX Cannot Be Unloaded

Some resident extensions depend on others.

BetterCP/M prevents certain unload operations when the extension is still required by another resident component.

For example, a terminal personality may depend on a screen backend.

To remove the monitor, unload the terminal personality first, then unload the backend.

Chapter 8 explains extension dependencies in greater detail.

### A Full-Screen Program Displays Incorrectly

If a full-screen application displays misplaced text, unexpected characters, or incorrect cursor movement, check its terminal configuration.

First, examine the installed RSXs:

```text
A>RSX LIST
```

Make sure the expected terminal personality and screen backend are loaded.

Next, check that the application is configured for the same terminal type.

For example, an application configured for VT52 should be used with BetterCP/M's VT52 personality.

You can also run the corresponding terminal test utility:

```text
A>VT52TST
```

If the test works correctly but the application does not, the application may be using unsupported terminal facilities or expecting different screen dimensions.

Chapter 9 provides more information about terminal configuration and troubleshooting.

### Insufficient Program Memory

Resident extensions occupy memory that would otherwise be available to transient programs.

If a program reports insufficient memory, check which extensions are loaded.

You may be able to unload facilities that aren't needed for the current task.

For example, if you're no longer using a full-screen application, unloading its terminal personality and screen backend may recover enough memory to run a larger program.

## 12.5 Startup and Boot Problems

Startup problems can arise from damaged system disks, incorrect saved configurations, missing files, or unsuitable startup commands.

The appropriate recovery procedure depends on how far the system gets before the problem occurs.

### BetterCP/M Doesn't Boot

If BetterCP/M fails to start, begin with the simplest possibilities.

Check that the correct system disk or disk image is being used.

On physical hardware, make sure the disk is inserted correctly and that the drive is functioning.

On an emulator, verify that the appropriate disk image is attached to the expected drive.

If the disk was prepared for another computer, it may not contain the BIOS or bootstrap code required by your machine.

BetterCP/M system images are platform-specific, even though the operating environment is largely portable.

Consult the appropriate platform documentation for the expected boot procedure.

### The System Boots but Reports Errors

If BetterCP/M reaches the command prompt but displays errors during startup, the problem may involve the configured startup command.

The standard distribution uses:

```text
SUBMIT STARTUP
```

This executes `STARTUP.SUB`.

If the file is missing or contains an invalid command, startup may report an error even though the operating system itself is functioning.

Check the startup file and any programs or extensions it invokes.

### A Startup Extension Fails

If `STARTUP.SUB` loads resident extensions, make sure the required files are present.

Also check their loading order.

For example, a terminal personality must be loaded after its supporting screen backend.

If a newly added startup command causes problems, remove it from `STARTUP.SUB` and test it separately at the command prompt.

Once the command works correctly, it can be restored to the startup procedure.

### Saved Configuration Prevents Normal Operation

An incorrect saved drive configuration can make disks inaccessible after a cold boot.

If the system still reaches the command prompt, use CONFIG to examine and correct the settings.

If the system cannot boot far enough to run CONFIG, you may need to start from a known working system disk.

This is one reason it's worth keeping an unmodified backup of a working BetterCP/M installation.

## 12.6 Recovery Procedures

When a problem occurs, the most important thing is to avoid making it worse.

In particular, don't begin formatting disks, changing drive definitions, or overwriting files until you've identified the likely cause.

### Begin with the Current State

Before making changes, determine what still works.

Can BetterCP/M reach the command prompt?

Can it display a directory?

Can it read files from the affected disk?

Can CONFIG display the current configuration?

Can the relevant utility run without performing a destructive operation?

These observations can help distinguish a command problem from a configuration problem, a filesystem problem, or a hardware failure.

### Preserve Important Files

If a disk is producing errors but remains readable, preserve important files before attempting repairs.

When possible, copy them to another disk.

Avoid unnecessary writes to the affected medium.

If the disk appears physically unreliable, repeated attempts to modify it may make recovery more difficult.

### Recovering from an Interrupted Disk Operation

Formatting, disk copying, and system installation can leave a destination disk incomplete if interrupted.

For example, an interrupted DUP format may leave a partially formatted disk.

An interrupted disk copy may leave a destination containing only part of the source's contents.

An interrupted SYSGEN installation may leave the system area incomplete, preventing the disk from booting.

In these situations, don't assume that the destination is usable simply because some operations completed successfully.

Correct the cause of the interruption and repeat the appropriate operation using a reliable source.

Remember that formatting and disk copying are destructive operations.

### Recovering a System Disk

If the operating system's reserved system area has been damaged, SYSGEN may be able to reinstall BetterCP/M without replacing ordinary files.

For example:

```text
A>SYSGEN SYSTEM.SYS B:
```

installs the operating system from a valid system-image package onto drive B.

The destination must be properly prepared and compatible with the image.

SYSGEN replaces the reserved system area while preserving records outside that area.

However, it cannot repair a damaged filesystem or recover files that have been lost.

If the disk's contents are extensively damaged, restoring a complete disk backup may be necessary.

Chapter 10 explains the distinction between system installation and complete disk copying.

### Returning to a Known Working Configuration

If a problem began after changing system settings, consider restoring the previous configuration.

For temporary changes, a cold boot may restore the saved defaults.

For saved changes, you may need to use CONFIG or reinstall a previously saved system image.

If you're experimenting with disk formats or resident extensions, maintaining a separate working system disk makes recovery considerably easier.

### When to Consult the Technical Documentation

Most ordinary problems can be resolved using the procedures described in this manual.

Some problems, however, involve hardware behavior, BIOS configuration, or operating-system facilities beyond the scope of the User's Guide.

If a problem persists after checking the relevant commands and configuration settings, consult the platform documentation or the more detailed BetterCP/M technical guides.

The *Architecture Overview* explains the organization of the operating system, while the *Porting Guide* and engineering specifications provide information for developers and system maintainers.

---

# Part II — Command and Utility Reference

# Chapter 13 — Introduction to the Command Reference

Part I introduced BetterCP/M's operating environment and explained how to use its principal facilities. Part II provides a detailed reference to the commands and utilities available under BetterCP/M 1.0.

This part of the manual is intended primarily for consultation. You need not read it from beginning to end. When you want to know how a particular command works, which options it accepts, or how it handles an unusual situation, you can turn directly to the appropriate entry.

BetterCP/M retains the familiar commands and conventions of Digital Research CP/M 2.2, while adding new commands and extending the capabilities of many existing ones.

Some commands are resident, some are transient programs, and some are available in both forms. Where the resident and transient versions differ, the reference describes those differences.

The command descriptions are organized by function rather than by their internal implementation. Each entry explains what the command does, how to invoke it, what options are available, and any important restrictions or compatibility considerations.

## 13.1 Command Syntax Conventions

Throughout this reference, command syntax is presented using a consistent set of conventions.

For example, a command description might begin with:

```text
COMMAND filespec [options]
```

This is a description of the command's syntax, not a command to enter literally.

### Command Names

Command names are shown in uppercase letters:

```text
DIR
ERA
REN
COPY
```

BetterCP/M accepts command names without regard to letter case.

For example:

```text
A>DIR
A>dir
A>Dir
```

all request the same command.

For clarity and consistency, the examples in this manual generally use uppercase command names.

### Required Arguments

Arguments that must be supplied are shown without enclosing brackets.

For example:

```text
TYPE filespec
```

indicates that TYPE requires a file specification identifying the file to display.

An example would be:

```text
A>TYPE README.TXT
```

The word `filespec` is a placeholder. Replace it with an actual filename or file specification.

### Optional Arguments

Optional arguments are enclosed in square brackets.

For example:

```text
COMMAND filespec [options]
```

indicates that the command requires a file specification but may also accept additional options.

The brackets are part of the syntax notation and are not normally typed.

Thus, if a command accepts an optional `/P` switch, you might enter:

```text
A>COMMAND README.TXT /P
```

or omit the switch:

```text
A>COMMAND README.TXT
```

Some BetterCP/M commands also use square brackets as part of their actual file-selection syntax. In those cases, the command description explicitly identifies the brackets as characters that must be entered.

### Alternative Forms

When a command accepts several forms, they are normally shown separately.

For example:

```text
DIR
DIR filespec
DIR DU:filespec
```

These represent different ways of invoking DIR.

The command reference explains the purpose and behavior of each supported form.

Where alternatives are shown using a vertical bar, such as:

```text
A|B
```

the bar means that one of the alternatives is selected. It is not typed unless the command description explicitly says otherwise.

### Repeated Arguments

Some commands accept more than one filename, option, or other argument.

When an argument can be repeated, the syntax description will indicate that possibility and explain any applicable limits.

For example, a command may accept a list of source files, while another may permit only one source specification.

Do not assume that a command accepting one filename can also accept several. The individual command entry defines the permitted forms.

### Spaces

Spaces normally separate a command name from its arguments and separate individual arguments from one another.

For example:

```text
A>COPY SOURCE.TXT B:SOURCE.TXT
```

The command name, source file, and destination file are separate elements.

Some commands also accept arguments containing spaces when enclosed in quotation marks.

For example:

```text
A>CONFIG /STARTUP="SUBMIT STARTUP"
```

The quotation marks preserve the startup command as a single argument.

Quoting rules are command-specific. The presence of quotation marks in one command's syntax does not imply that every BetterCP/M command supports quoted arguments.

### Numbers and Numeric Bases

Unless otherwise stated, numeric arguments are decimal.

Some commands, particularly those used to examine or modify memory, accept hexadecimal values.

For example, a memory address might be written as:

```text
0100
```

and interpreted as hexadecimal by the command concerned.

The command reference identifies the expected numeric base.

Where ambiguity is possible, the manual explicitly identifies hexadecimal values with the suffix `H`, as in `0100H`.

The suffix is an explanatory convention and should not be included in a command unless that command's syntax permits it.

### Examples and the Command Prompt

Command examples generally include the BetterCP/M prompt:

```text
A>DIR
```

You type only the characters following the prompt.

The prompt itself identifies the current drive and, where applicable, the user area.

For example:

```text
B3>DIR
```

shows DIR being entered while drive B, user area 3, is selected.

When several commands are shown together, each command is entered after the preceding operation has completed and the prompt has returned, unless otherwise indicated.

## 13.2 Command Options

Many BetterCP/M commands accept options that modify their behavior.

Options are commonly introduced by a slash (`/`).

For example:

```text
A>DIR /P
```

The `/P` option requests paged directory output in the transient DIR utility.

Other options may control sorting, file selection, confirmation, output formatting, or the treatment of existing files.

### Options and Their Arguments

Some options consist of a switch alone:

```text
/P
```

Others require a value:

```text
/C=2
```

The command reference identifies which options require values and explains the accepted forms.

For example, an option might accept a number, a filename, or a selection from several predefined values.

Do not assume that an option requiring a value can be used without one.

### Combining Options

Some commands allow several options to be supplied together.

For example:

```text
A>COPY B1:*.DAT C3: /B /O
```

Here, `/B` requests batch-oriented operation, while `/O` specifies how existing writable destination files should be handled.

The two options work together to perform the operation without asking for overwrite confirmation.

Other combinations may be invalid or mutually exclusive.

Each command reference identifies the combinations it supports.

### Option Placement

The permitted position of an option depends on the command.

Some commands accept options before or after a file specification. Others require a particular order.

For this reason, the examples and syntax descriptions should be followed rather than assuming that all BetterCP/M utilities use identical option-placement rules.

### Default Behavior

When an option is omitted, the command uses its default behavior.

For example, a file-copying command may normally request confirmation before replacing an existing destination.

An option may change that behavior by instructing the command to overwrite, skip, or reject the existing file.

The command reference explains the defaults where they are important.

### Interactive and Noninteractive Operation

Some commands request information from the user while executing.

For example, a utility may ask whether an existing file should be replaced.

BetterCP/M provides options for certain utilities that allow such decisions to be specified in advance.

This is particularly useful in SUBMIT files.

However, placing a command in a SUBMIT file does not automatically make it noninteractive.

If a command may prompt for input, consult its reference entry before using it in an unattended batch procedure.

### File Selection and Attributes

Several BetterCP/M utilities support extended file-selection facilities.

These can include drive/user specifications, wildcards, and file-attribute conditions.

For example, a command may allow you to select files with particular attributes or search across several user areas.

These facilities are not necessarily available in every command.

The reference entry identifies which selectors are supported and where they may appear.

For an introduction to file specifications, wildcards, and attributes, see Chapter 4, *Working with Drives and Files*.

## 13.3 Resident and Transient Versions

BetterCP/M distinguishes between resident commands and transient programs.

A **resident command** is provided by the active command environment. It can be executed without loading an ordinary `.COM` program from disk.

A **transient command** is an executable program that BetterCP/M loads when it is invoked.

Some commands are available in both forms.

### Why Two Versions?

The resident versions of frequently used commands provide convenient access to common operations.

For example, the standard resident command package supplies familiar commands such as DIR, ERA, REN, TYPE, COPY, and MOVE.

Their transient counterparts may offer additional capabilities.

This arrangement allows BetterCP/M to provide useful commands without permanently occupying memory with every available option.

The resident version can remain compact, while the transient version provides more extensive functionality when needed.

### Normal Command Execution

When you enter:

```text
A>DIR
```

BetterCP/M uses the normal command-search procedure.

If DIR is available as a resident command, that version is selected.

If no resident command handles the name, BetterCP/M attempts to locate and execute the corresponding transient program.

For an unqualified transient program name, BetterCP/M searches the current drive and user area first, followed by `A0:`.

A program found in the current drive/user takes precedence over one found in `A0:`.

For more information about command search and execution, see Chapter 5.

### Explicit Transient Execution

Sometimes you may want to execute a transient program even though a resident command with the same name is available.

BetterCP/M provides two prefixes for this purpose:

```text
:
.
```

Place either prefix immediately before the command name.

For example:

```text
A>:DIR
```

or:

```text
A>.DIR
```

Both forms bypass the resident command and request the transient `DIR.COM` program.

The prefix can also be used with arguments:

```text
A>:DIR /WHEREIS ED.COM
```

This invokes the transient DIR utility's file-location facility.

### Drive/User Qualifications

An explicit transient invocation can include a drive/user qualification.

For example:

```text
A>:B3:MYPROG ARGUMENTS
```

This requests `MYPROG.COM` from drive B, user area 3.

The transient-execution prefix appears before the drive/user qualification.

A qualified invocation restricts the program search to the specified location.

By contrast, an unqualified transient invocation follows the normal search procedure, including the fallback to `A0:`.

### When the Resident Command Lacks an Option

BetterCP/M 1.0 does not automatically transfer execution from a resident command to its transient counterpart when an option is unavailable.

Instead, certain resident commands recognize options that require the transient version and report that the transient program should be used.

For example:

```text
A>DIR /WHEREIS ED.COM
DIR: Use :DIR.
```

You can then enter:

```text
A>:DIR /WHEREIS ED.COM
```

The command is not automatically reissued.

If the transient program cannot be found, BetterCP/M reports the normal command-lookup failure.

### Differences Between Versions

The resident and transient versions of a command may differ in several respects.

They may accept different options, provide different output formats, or support different file-selection facilities.

The command reference distinguishes these differences explicitly.

Where appropriate, each entry provides separate syntax descriptions for the resident and transient forms.

Unless otherwise stated, examples apply to the form identified in the surrounding text.

## 13.4 Getting Help and Version Information

BetterCP/M provides several facilities for identifying commands, obtaining assistance during interactive operations, and examining software versions.

Not every command supports the same help facilities, so the individual reference entries identify the available options.

### Version Information

BetterCP/M utilities generally support the `/VER` option for displaying version and build information.

For example:

```text
A>:DIR /VER
```

identifies the transient DIR utility.

A version display might resemble:

```text
BetterCP/M DIR 1.0 (Build 002)
```

The exact build number depends on the installed utility.

Resident commands can also report version information.

For example:

```text
A>DIR /VER
```

identifies the resident DIR implementation when it is available.

A resident version display identifies the command package containing the command.

This distinction is useful when comparing the resident and transient versions of a utility.

### Version Numbers and Build Numbers

BetterCP/M distinguishes between a software version and a build number.

The **version number** identifies the software release.

The **build number** identifies a particular revision of the executable.

For example:

```text
BetterCP/M DIR 1.0 (Build 002)
```

identifies version 1.0 of DIR, build 002.

Different utilities maintain their own build sequences.

Resident commands supplied by the same command processor extension share the build identity of that extension.

Consequently, the resident and transient versions of a command may report different build numbers even though both belong to BetterCP/M 1.0.

### Using /VER

For BetterCP/M-owned utilities, `/VER` is normally used by itself.

For example:

```text
A>TIME /VER
```

The utility displays its identification and exits without performing its ordinary operation.

Do not combine `/VER` with filenames or other options unless the command reference explicitly permits it.

An invalid combination may produce:

```text
Invalid /VER usage.
```

The `/VER` convention applies to BetterCP/M utilities. Third-party CP/M programs may use different conventions or provide no version-reporting facility.

### System Version Information

BetterCP/M also provides the VER command for identifying the operating system.

For example:

```text
A>VER
```

displays the system version.

Additional VER options provide more detailed identification information, including subsystem information and the system identification banner.

The complete forms are documented in the VER command reference.

### Help at Interactive Prompts

Some BetterCP/M utilities provide help while waiting for a response.

For example, a command that encounters an existing destination file may display a prompt offering several possible actions.

When the prompt includes `?` as an available response, entering it displays a short explanation of the choices.

For example, COPY's file-collision prompt may offer:

```text
Y/N/O/S/R/?
```

Entering `?` displays information about the available responses and returns to the same decision.

Requesting help does not itself select an action or change the command's current operation.

Not every prompt supports this facility.

Simple yes/no confirmations may require only `Y` or `N`, while paging prompts generally display their available controls directly.

### When a Command Reports an Error

If a command rejects an option or file specification, consult its reference entry.

The entry describes the accepted syntax, supported options, restrictions, and important error conditions.

For problems involving the operating environment rather than a particular command, see Chapter 12, *Troubleshooting*.

Appendix F provides a reference to system messages and errors.

---

# Chapter 14 — File and Directory Commands

BetterCP/M provides a collection of commands for listing, displaying, copying, renaming, moving, and deleting files. Most will be familiar to anyone who has used Digital Research CP/M, although BetterCP/M adds several useful capabilities.

This chapter is a reference to six of the most frequently used commands:

| Command | Purpose |
|---|---|
| DIR | Display directory contents and locate files |
| ERA | Erase files |
| REN | Rename files |
| TYPE | Display text files |
| COPY | Copy files |
| MOVE | Move files |

Several commands are available in both resident and transient forms. The resident versions provide convenient access to common operations, while their transient counterparts may offer more extensive options.

Where the two forms differ, the descriptions below identify those differences.

## 14.1 DIR — Display Directory

**Purpose:** Displays files in the current or a specified drive and user area.

DIR is available as both a resident command and a transient utility, `DIR.COM`.

### Resident DIR

The resident command accepts:

```text
DIR
DIR filespec
DIR DU:
DIR DU:filespec
```

For example:

```text
A>DIR
A>DIR *.COM
A>DIR B:
A>DIR B3:*.ASM
```

Without arguments, DIR displays the files in the current drive and user area.

A file specification restricts the listing to matching files. Wildcards may be used to select groups of files.

BetterCP/M also supports extended drive/user selectors:

```text
A>DIR B[-]:*.COM
A>DIR B[3-5]:*.ASM
A>DIR [A0,B3]:*.DOC
```

Here, `B[-]:` selects all user areas on drive B, while `B[3-5]:` selects user areas 3 through 5.

The resident command displays each selected drive/user area separately and restores the original drive and user area when finished.

By default, system files are omitted.

### Selecting Files by Attribute

DIR supports file-attribute expressions.

For example:

```text
A>DIR *.COM[$ARC]
A>DIR *.DOC[$RO]
A>DIR B[-]:*.COM[$ARC+!$SYS]
```

The available attribute names are:

| Attribute | Meaning |
|---|---|
| `$RO` | Read-only |
| `$RW` | Writable |
| `$SYS` | System |
| `$DIR` | Not marked as a system file |
| `$ARC` | Archive |

Attribute expressions use `!` for NOT, `+` for AND, and a comma for OR.

For example:

```text
[$ARC+!$SYS]
```

selects files marked ARC but not SYS.

An explicit attribute expression replaces DIR's normal suppression of system files. A system file satisfying the expression can therefore appear in the listing.

Attribute selection does not change file attributes.

### Transient DIR.COM

The transient DIR utility provides additional display and file-selection options.

Invoke it explicitly with:

```text
A>:DIR
```

or:

```text
A>.DIR
```

Both forms bypass the resident command.

The general syntax is:

```text
DIR [options] [location:filespec[attribute-expression]]
```

The transient utility supports the same extended drive/user selectors and attribute expressions as resident DIR.

It also provides sorting, file sizes, attribute display, paging, and directory summaries.

### DIR.COM Options

| Option | Description |
|---|---|
| `/A` | Display file attributes |
| `/P` | Pause after each screenful |
| `/Z` or `/Z=K` | Display allocated space in kilobytes |
| `/Z=S` | Display allocated 128-byte records |
| `/Z=E` | Display directory entries used |
| `/C=1` | One-column display |
| `/C=2` | Two-column display |
| `/C=4` | Four-column display |
| `/S=N` | Sort by filename |
| `/S=T` | Sort by file type |
| `/S=Z` | Sort by allocated size |
| `/S=U` | Preserve directory order |

Sorting options `/S=N`, `/S=T`, and `/S=Z` may be followed by `+` for ascending or `-` for descending order.

For example:

```text
A>:DIR /S=N
A>:DIR /S=Z-
A>:DIR /S=T+ *.COM
```

The first sorts by filename, the second displays the largest files first, and the third sorts matching files by file type.

`/S=U` preserves the disk's directory-search order and does not accept a direction suffix.

Name-ascending order is the default.

### Displaying File Sizes

Transient DIR displays the allocated space occupied by each file.

The default unit is kilobytes.

To display allocated 128-byte records:

```text
A>:DIR /Z=S
```

To display the number of physical directory entries occupied by each file:

```text
A>:DIR /Z=E
```

These values describe allocated storage or directory usage, not necessarily the exact logical length of the file.

### Displaying Attributes

Use `/A` to include a three-character attribute field:

```text
A>:DIR /A
```

The field contains the SYS, read-only, and ARC attributes, in that order.

For example:

| Display | Meaning |
|---|---|
| `---` | No attributes set |
| `-R-` | Read-only |
| `S--` | System |
| `--A` | Archive |
| `S-A` | System and archive |

The `/A` option displays attributes but does not select files based on them.

To select files by attribute, use an attribute expression.

### Paging and Columns

For long listings, use:

```text
A>:DIR /P
```

DIR pauses after each screenful.

Press Space or Return to continue, or Ctrl-C to stop the listing.

The transient utility normally chooses a suitable column layout automatically.

You can request a particular number of columns:

```text
A>:DIR /C=1
```

A one-column display is particularly convenient when file sizes and attributes are shown.

If the requested number of columns cannot fit, DIR reports an error rather than silently changing the layout.

### Directory Summaries

Transient DIR reports file counts and allocated-space totals.

When several user areas are selected, each is listed separately.

Free space is reported once per selected drive rather than repeated for every user area.

For example, selecting both B3 and B4 produces separate listings but only one free-space total for drive B.

### Examples

Display all `.COM` files in user area 3 on drive B:

```text
A>:DIR B3:*.COM
```

Display archived files, excluding system files:

```text
A>:DIR *.*[$ARC+!$SYS]
```

Display the largest archived `.COM` files first, including their attributes:

```text
A>:DIR /A /S=Z- B3:*.COM[$ARC]
```

Display a paged, one-column listing:

```text
A>:DIR /C=1 /P
```

For ordinary directory listings, resident DIR is usually sufficient. Use transient DIR when you need sorting, sizes, paging, or more detailed information.

---

## 14.2 ERA — Erase Files

**Purpose:** Removes one or more files from disk.

ERA is available as a resident command and as the more capable transient utility `ERA.COM`.

**Files erased by ERA may be unrecoverable.** Check wildcard specifications and drive/user selections carefully before confirming an erase operation.

### Resident ERA

The resident command accepts file specifications and BetterCP/M's extended drive/user selectors.

For example:

```text
A>ERA OLD.TXT
A>ERA *.BAK
A>ERA B3:*.TMP
A>ERA B[-]:*.BAK
```

It also accepts attribute expressions:

```text
A>ERA B[-]:*.DOC[$ARC]
```

The complete selection is checked before any files are erased.

Resident ERA protects read-only and system files. These remain protected even when an attribute expression explicitly selects them.

When an all-wildcard specification is used, ERA requests confirmation:

```text
ALL (Y/N)?
```

Only `Y` proceeds.

Resident ERA does not provide the extended confirmation, reporting, and destructive-erasure options available in the transient utility.

### Transient ERA.COM

Invoke the transient utility explicitly:

```text
A>:ERA
```

Its general syntax is:

```text
ERA [options] filespec[attributes]
```

For example:

```text
A>:ERA OLD.DOC
A>:ERA *.BAK
A>:ERA B[-]:*.DOC
```

Unlike the resident command, transient ERA normally displays the files selected for deletion and requests confirmation.

For a single file, it may ask:

```text
TOM.DOC - Erase? Y/N
```

For multiple files, it displays a list of the selected files and a summary before asking whether to proceed.

### ERA.COM Options

The documented erase controls are:

| Option | Description |
|---|---|
| `/Y` | Assume yes for ordinary confirmations |
| `/Q` | Suppress ordinary informational output |
| `/C` | Confirm each file |
| `/R` | Authorize erasure of selected read-only files |
| `/D` | Destructive erase |

These options affect how files are selected, confirmed, and removed.

Some options are intended for unattended operations, while others provide additional safeguards.

### Confirmation

By default, transient ERA asks before deleting files.

For example:

```text
A>:ERA *.BAK
```

displays the selected files and requests confirmation.

To request confirmation for each file:

```text
A>:ERA /C *.BAK
```

ERA first obtains the ordinary group confirmation and then asks about individual files.

To suppress ordinary confirmation prompts:

```text
A>:ERA /Y *.BAK
```

This is useful in SUBMIT files, but should be used carefully.

### Read-Only and System Files

Transient ERA provides additional controls for protected files.

A broad erase does not automatically override read-only or system protection.

To select read-only files explicitly:

```text
A>:ERA *.DOC[$RO]
```

Without `/R`, ERA requests additional authorization before erasing a selected read-only file.

To authorize their erasure:

```text
A>:ERA /R *.DOC[$RO]
```

The `/R` option does not broaden the file selection. It only affects the treatment of read-only files already selected.

Similarly, `/Y` does not automatically override read-only protection.

System files must be deliberately selected through the appropriate attribute expression.

A file with both SYS and read-only attributes requires authorization for both conditions.

These safeguards help prevent broad wildcard operations from accidentally removing protected files.

### Quiet Operation

Use `/Q` to suppress ordinary informational output:

```text
A>:ERA /Q *.BAK
```

This does not suppress required confirmation.

For unattended operation, combine it with `/Y`:

```text
A>:ERA /Y /Q *.BAK
```

### Destructive Erase

The transient ERA utility provides a destructive-erasure option:

```text
A>:ERA /D SECRET.DAT
```

This attempts to overwrite the file's allocated data with zeroes before removing its directory information.

Destructive erase is intended to make recovery of the selected file's contents more difficult than ordinary deletion.

However, **it should not be treated as a guarantee of secure data destruction**.

Some allocation blocks may be shared with other live files. BetterCP/M preserves shared blocks rather than overwriting data belonging to another file.

Hardware characteristics and disk errors can also prevent complete overwriting.

Destructive erase requires explicit confirmation and reports incomplete operations.

### Error Handling

If an erase operation fails, ERA may offer:

```text
R/S/A/?
```

The responses are:

| Response | Meaning |
|---|---|
| R | Retry |
| S | Skip the file |
| A | Abort the remaining operation |
| ? | Display help |

With `/Y`, ERA does not stop for this recovery prompt. It reports the failed file and continues when safe.

### Completion Summary

Transient ERA reports the results of the operation.

For example:

```text
12 FILES ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

The reported space freed represents allocated disk space released, rather than the exact logical lengths of the deleted files.

### Examples

Erase a single file:

```text
A>ERA OLD.TXT
```

Erase backup files in user area 3 on drive B:

```text
A>ERA B3:*.BAK
```

Erase archived files with individual confirmation:

```text
A>:ERA /C B[-]:*.DOC[$ARC]
```

Erase selected files without ordinary confirmation:

```text
A>:ERA /Y *.BAK
```

Destructively erase a file:

```text
A>:ERA /D SECRET.DAT
```

For ordinary file deletion, resident ERA is usually sufficient. Use transient ERA when you need its additional confirmation, selection, or destructive-erasure facilities.

---

## 14.3 REN — Rename Files

**Purpose:** Changes the names or file types of existing files without changing their contents.

REN is available as both a resident command and a transient utility, `REN.COM`.

Unlike COPY and MOVE, REN does not transfer files between drives or user areas. Each renamed file remains in its original location.

### Resident REN

Resident REN accepts two equivalent forms:

```text
REN source template
REN template=source
```

For example:

```text
A>REN NEW.TXT=OLD.TXT
A>REN OLD.TXT NEW.TXT
```

Both rename `OLD.TXT` to `NEW.TXT`.

BetterCP/M also supports wildcard rename templates:

```text
A>REN *.DOC *.TXT
```

This changes the file type of matching `.DOC` files to `.TXT`, retaining their original names.

You can select files in another drive or user area:

```text
A>REN *.TXT=B3:*.DOC
```

The files remain in `B3:` after being renamed.

### Renaming Several Files

REN supports BetterCP/M's extended drive/user selectors.

For example:

```text
A>REN B[-]:*.DOC *.TXT
```

renames matching files across all user areas on drive B.

You can also use attribute expressions:

```text
A>REN B[-]:*.DOC[$RW] *.TXT
```

This selects writable `.DOC` files.

Read-only and system files are protected by the resident command, even when explicitly selected.

### Rename Templates

Rename templates determine how the new filename is constructed.

A literal character replaces the corresponding character in the source name. A question mark retains a character from the corresponding position, while a terminal asterisk retains the remainder of that filename field.

For example:

```text
A>REN X?*.BAK=B3:FOOBAR.DOC
```

produces `XOOBAR.BAK`.

The filename and file type are treated as separate fields.

A template cannot specify another drive or user area. Use COPY or MOVE when you want to change a file's location.

### Existing Destination Names

REN never overwrites an existing file.

If the requested new name already exists, resident REN stops rather than replacing it.

Any files successfully renamed before the conflict remain renamed.

REN does not automatically undo earlier operations.

### Transient REN.COM

The transient utility provides additional confirmation, preview, protection, and reporting options.

Invoke it explicitly:

```text
A>:REN
```

It accepts the same two operand arrangements:

```text
REN source template
REN template=source
```

### REN.COM Options

| Option | Description |
|---|---|
| `/C` | Confirm each eligible rename |
| `/Y` | Proceed without ordinary confirmation |
| `/N` | Display proposed mappings without renaming |
| `/DRY` | Preview the operation without changing files |
| `/P` | Permit renaming selected protected files |
| `/Q` | Suppress routine successful-operation messages |
| `/QQ` | Suppress most normal output |
| `/VER` | Display version information |

### Previewing a Rename

When renaming several files, it's often useful to see what will happen before making changes.

Use `/DRY`:

```text
A>:REN /DRY B[-]:*.DOC *.TXT
```

REN displays the proposed filename changes without modifying the files.

A visible dry run ends with:

```text
Dry run only: no files were renamed.
```

The `/DRY` option takes precedence over options that would otherwise authorize renaming.

This makes it particularly useful when experimenting with wildcard templates.

### Confirming Renames

Use `/C` to request confirmation for each eligible file:

```text
A>:REN /C *.DOC *.TXT
```

Use `/Y` when the operation should proceed without ordinary confirmation:

```text
A>:REN /Y *.DOC *.TXT
```

Neither option overrides file protection.

### Protected Files

By default, REN skips read-only and system files.

Transient REN provides `/P` to permit renaming explicitly selected protected files.

For example:

```text
A>:REN /P *.DOC[$RO] *.TXT
```

This selects read-only `.DOC` files and permits their renaming.

The files retain their attributes after the rename.

The `/P` option does not broaden the file selection or override a read-only drive.

### Name Conflicts

If a destination name already exists, transient REN can offer:

```text
File exists. N/S/A/?
```

The responses are:

| Response | Meaning |
|---|---|
| N | Enter a new name |
| S | Skip this file |
| A | Abort the remaining operation |
| ? | Display help |

A replacement name must be a valid filename without a drive/user qualification.

REN never silently overwrites an existing target.

### Errors and Completion

If an operation fails, transient REN may offer Retry, Skip, or Abort.

Successful renames are not rolled back when a later operation fails.

On completion, REN reports the results, for example:

```text
12 FILES RENAMED, 2 SKIPPED, 1 FAILED
```

### Examples

Rename one file:

```text
A>REN NEWNAME.TXT=OLDNAME.TXT
```

Change all `.DOC` files to `.TXT`:

```text
A>REN *.DOC *.TXT
```

Preview renaming across all user areas on drive B:

```text
A>:REN /DRY B[-]:*.DOC *.TXT
```

Rename selected read-only files:

```text
A>:REN /P *.DOC[$RO] *.TXT
```

For ordinary renaming, resident REN is sufficient. Use transient REN when you need confirmation controls, previews, or protected-file handling.

---

## 14.4 TYPE — Display Text Files

**Purpose:** Displays the contents of text files on the console.

TYPE is available as a resident command and as the more capable transient utility `TYPE.COM`.

### Resident TYPE

The basic form is:

```text
TYPE filespec
```

For example:

```text
A>TYPE README.TXT
```

TYPE displays the contents of `README.TXT`.

BetterCP/M also supports extended file selection:

```text
A>TYPE B3:README.TXT
A>TYPE B[-]:*.TXT
A>TYPE [A0,B3]:*.DOC
```

When several files are selected, TYPE displays them in sequence.

TYPE treats the conventional CP/M end-of-text character, Ctrl-Z (`1AH`), as the end of the text.

It does not modify the files being displayed.

### Resident Paging

Resident TYPE supports forward paging with `/P`:

```text
A>TYPE README.TXT /P
```

The display pauses after a screenful of text.

Press Space or `.` to advance.

Ctrl-C cancels the resident paged display.

The resident command provides simple forward paging rather than the more extensive navigation facilities of `TYPE.COM`.

### Transient TYPE.COM

Invoke the transient utility explicitly:

```text
A>:TYPE README.TXT
```

The transient version provides bidirectional paging, navigation between files, and several display options.

### TYPE.COM Options

| Option | Description |
|---|---|
| `/P` | Enable interactive paging and file navigation |
| `/7` | Strip the high bit from displayed characters |
| `/T` | Expand tabs to eight-column stops |
| `/CTL` | Display control characters using caret notation |
| `/VER` | Display version information |

Options may appear before or after the file specification.

For example:

```text
A>:TYPE README.TXT /P
A>:TYPE README.TXT /7
A>:TYPE README.TXT /T
A>:TYPE README.TXT /CTL
```

### Paging and Navigation

With `/P`, transient TYPE provides the following controls:

| Key | Action |
|---|---|
| Ctrl-R or `,` | Previous page |
| Ctrl-C, `.` or Space | Next page |
| `<` | Beginning of current file, or previous file |
| `>` | Beginning of next file |
| Ctrl-Q | Quit |

The meaning of Ctrl-C here is specific to TYPE.COM's paging prompt. During ordinary output, normal CP/M console handling applies.

At the end of the final file, TYPE leaves the last page displayed until you quit.

You can move backward through earlier pages without a fixed page-history limit, although revisiting distant pages may be slow on floppy disks.

### Displaying Control Characters

The `/CTL` option displays control characters in a readable form.

For example, a tab is displayed as `^I`, while a form feed appears as `^L`.

This can be useful when examining text files containing unexpected control characters.

The `/T` option expands tabs into spaces for display. When `/CTL` is used, its control-character display takes precedence over ordinary tab expansion.

### Displaying Several Files

TYPE.COM can display files selected from several drive/user areas:

```text
A>:TYPE B[-]:*.DOC /P
```

When several files are selected, the utility identifies each file as it is displayed.

You can use `<` and `>` to move between file boundaries.

This makes TYPE.COM useful for examining a collection of text files without returning to the command prompt after each one.

### Limitations

TYPE is intended for ordinary text files.

It does not provide binary inspection, decompression, text searching, or editing.

For those operations, use an appropriate specialized utility.

### Examples

Display a file:

```text
A>TYPE README.TXT
```

Display a file with simple paging:

```text
A>TYPE README.TXT /P
```

Use the transient viewer with backward paging:

```text
A>:TYPE README.TXT /P
```

Display control characters:

```text
A>:TYPE README.TXT /CTL
```

Display all `.DOC` files across drive B's user areas:

```text
A>:TYPE B[-]:*.DOC /P
```

---

## 14.5 COPY — Copy Files

**Purpose:** Copies one or more files to another filename, drive, or user area while preserving the originals.

COPY is available as both a resident command and a transient utility, `COPY.COM`.

The resident command handles ordinary file-copying operations. The transient utility adds destination filename templates, verification, backup facilities, and more extensive control over existing files.

### Resident COPY

COPY accepts two equivalent forms:

```text
COPY source destination
COPY destination=source
```

For example:

```text
A>COPY README.TXT README.BAK
A>COPY README.TXT B:
A>COPY B:README.TXT=README.TXT
```

The first copies `README.TXT` to `README.BAK` in the current location.

The second copies the file to drive B, retaining its name.

The third uses the alternative destination-first syntax.

### Copying Groups of Files

Wildcards allow several files to be copied in one operation:

```text
A>COPY *.COM B:
```

BetterCP/M also supports drive/user specifications:

```text
A>COPY A3:*.ASM B7:
```

This copies matching assembly-language files from drive A, user area 3, to drive B, user area 7.

More elaborate source selections are also supported:

```text
A>COPY B[-]:*.DOC[$RW+!$SYS] C4:
```

This selects writable, non-system `.DOC` files across all user areas on drive B and copies them to `C4:`.

The destination must identify one drive/user area.

When several files are selected, their original names are normally retained.

### Existing Destination Files

Resident COPY normally refuses to replace an existing destination file.

To permit replacement of existing writable destinations, use `/O`:

```text
A>COPY README.TXT B: /O
```

Read-only destination files remain protected.

The resident command also checks for invalid or conflicting source and destination selections before beginning the copy.

For example, it refuses an operation that would overwrite one of the files selected as a source.

### Transient COPY.COM

The transient utility provides additional capabilities.

Invoke it explicitly:

```text
A>:COPY
```

The same source-first and destination-first syntax forms are supported.

### COPY.COM Options

| Option | Description |
|---|---|
| `/O` | Replace existing writable destination files |
| `/S` | Skip existing writable destination files |
| `/B` | Operate without file-collision prompts |
| `/V` | Verify copied data by rereading and comparing it |
| `/BACKUP` | Clear archive attributes after successful backup processing |

`/O` and `/S` cannot be combined.

The other options may be used together where appropriate.

### Copying with Verification

To verify a copied file, use `/V`:

```text
A>:COPY /V README.TXT B:
```

After copying, COPY rereads the source and destination records and compares them.

A successful comparison provides additional assurance that the destination contains the expected data.

Verification is particularly useful when copying important files or working with unfamiliar media.

If verification fails, COPY reports the problem and offers recovery choices.

### Handling Existing Files

Without an explicit collision policy, transient COPY asks what to do when a writable destination file already exists.

The prompt offers:

```text
Y/N/O/S/R/?
```

The responses are:

| Response | Meaning |
|---|---|
| Y | Overwrite this destination |
| N | Skip this file |
| O | Overwrite this and subsequent writable collisions |
| S | Skip this and subsequent writable collisions |
| R | Supply a different destination filename |
| ? | Display help |

The O and S responses apply only to the current COPY invocation.

Read-only destinations remain protected.

### Batch Operation

For unattended operation, use `/B`.

For example:

```text
A>:COPY B1:*.DAT C3: /B
```

COPY processes the selected files without stopping for collision decisions.

If a writable destination already exists, `/B` alone reports `FILE EXISTS` and skips that copy as a failed operation.

It does not silently overwrite the file.

To overwrite existing writable destinations:

```text
A>:COPY B1:*.DAT C3: /B /O
```

To skip existing destinations:

```text
A>:COPY B1:*.DAT C3: /B /S
```

Read-only destinations remain protected in all three cases.

The `/B` option affects COPY itself. It does not make an entire SUBMIT procedure noninteractive.

### Destination Filename Templates

Transient COPY supports wildcard destination templates.

For example:

```text
A>:COPY C3:*.DOC=A4:*.COM
```

This copies matching `.COM` files from `A4:` to `C3:`, changing their file type to `.DOC`.

A destination template can retain portions of the original filename while replacing others.

For example:

```text
A>:COPY C3:X?*.BAK=A4:FOOBAR.COM
```

creates `XOOBAR.BAK`.

Destination templates are available in the transient utility, not the resident command.

### File Attributes

COPY.COM supports attribute expressions when selecting source files.

For example:

```text
A>:COPY B[-]:*.COM[$ARC] D0:
```

selects `.COM` files marked with the archive attribute.

Attribute expressions use the same conventions described under DIR.

COPY can also assign attributes to completed destination files.

For example:

```text
A>:COPY A0:*.COM D0:[$RW,!$ARC]
```

requests writable destination copies with the archive attribute cleared.

Unspecified attributes are preserved.

Changing the requested destination attributes does not override the protection of an existing read-only destination.

### Backup Processing

The `/BACKUP` option provides additional support for file-backup procedures.

For example:

```text
A>:COPY /V /BACKUP B[-]:*.COM[$ARC] D0:
```

This selects archive-marked `.COM` files, copies them to `D0:`, verifies the copies, and clears the archive attribute on both the source and destination after successful completion.

If a file is skipped, fails to copy, or is interrupted, its source archive attribute is retained.

The `/BACKUP` option does not automatically select archive-marked files. Use `[$ARC]` when you want to restrict the operation to files carrying that attribute.

Nor does `/BACKUP` automatically enable verification. Add `/V` when verification is desired.

### Copying Limits and Conflicts

Transient COPY checks the selected files and destination mappings before beginning the operation.

It refuses operations involving conflicting destination names, invalid mappings, or destinations that overlap selected source files.

The current transient utility supports a maximum of 64 matched source files in one invocation.

If a selection exceeds that limit, COPY reports:

```text
COPY BATCH TOO LARGE
```

and does not begin writing.

For larger collections, divide the operation into smaller batches.

### Errors and Recovery

If a copy fails, COPY reports the affected file.

Depending on the failure, it may offer recovery choices or continue with later files.

An incomplete destination is normally removed when the operation fails.

If that cleanup also fails, COPY reports the condition because an incomplete file may remain on disk.

Earlier successfully completed copies are preserved.

An interrupted batch is therefore not automatically rolled back.

### Completion Information

Transient COPY reports successful copies and their allocated sizes.

For example:

```text
B1:FOO.COM -> D0:FOO.COM [2K]
```

For multiple files, it also reports totals for copied, skipped, and failed files.

### Examples

Copy one file:

```text
A>COPY README.TXT B:
```

Copy all `.ASM` files to another user area:

```text
A>COPY A3:*.ASM B7:
```

Copy and verify:

```text
A>:COPY /V README.TXT B:
```

Copy without collision prompts, skipping existing files:

```text
A>:COPY /B /S B1:*.DAT C3:
```

Back up archive-marked files with verification:

```text
A>:COPY /V /BACKUP B[-]:*.COM[$ARC] D0:
```

---

## 14.6 MOVE — Move Files

**Purpose:** Transfers one or more files to another filename, drive, or user area, removing the originals after successful transfer.

MOVE is similar to COPY, but it is intended to relocate files rather than duplicate them.

BetterCP/M 1.0 provides MOVE as a resident command.

### Syntax

MOVE accepts source-first and destination-first forms:

```text
MOVE source destination
MOVE destination=source
```

For example:

```text
A>MOVE README.TXT B:
A>MOVE B:README.TXT=README.TXT
```

Both move `README.TXT` from the current location to drive B.

### Moving Groups of Files

MOVE accepts wildcards:

```text
A>MOVE *.BAK B:
```

It also supports drive/user specifications:

```text
A>MOVE A3

We'll finish Chapter 14 with **Section 14.5 — COPY** and **Section 14.6 — MOVE**, following the structure and level of detail established in the preceding command references.

---

## 14.5 COPY — Copy Files

**Purpose:** Copies one or more files to another filename, drive, or user area.

COPY is available as both a resident command and a transient utility, `COPY.COM`.

The resident version provides the file-copying facilities needed for ordinary use, while the transient utility offers additional capabilities, including wildcard destination templates, file verification, attribute management, and backup operations.

COPY leaves the original files in place. If you want to transfer files to another location and remove the originals, use MOVE instead.

### Resident COPY

Resident COPY accepts two equivalent command forms:

```text
COPY source destination
COPY destination=source
```

For example:

```text
A>COPY README.TXT README.BAK
A>COPY README.BAK=README.TXT
```

Both commands create `README.BAK` from `README.TXT`.

You can also copy files between drives:

```text
A>COPY README.TXT B:
```

This copies `README.TXT` to drive B, retaining its original filename.

To copy a file into another user area:

```text
A>COPY A3:REPORT.TXT B5:
```

The destination file is created on drive B, user area 5.

### Copying Several Files

COPY accepts wildcard file specifications.

For example:

```text
A>COPY *.ASM B:
```

copies the matching assembly-language source files to drive B.

BetterCP/M also supports extended drive/user selectors:

```text
A>COPY B[-]:*.DOC C3:
```

This selects `.DOC` files across all user areas on drive B and copies them to drive C, user area 3.

You can combine several locations:

```text
A>COPY [A0,B[5-7],C3]:*.COM D3:
```

The destination must identify a single drive/user area.

When several source files would produce the same destination filename, COPY rejects the conflicting selection rather than silently replacing one file with another.

### Selecting Files by Attribute

Resident COPY supports file-attribute expressions.

For example:

```text
A>COPY B[-]:*.DOC[$RW+!$SYS] C4:
```

This selects writable, non-system `.DOC` files from drive B's user areas.

Attribute expressions use the same conventions described in Chapter 4 and Section 14.1.

They determine which files are selected; they do not automatically change the attributes of the source files.

### Existing Destination Files

Resident COPY normally refuses to replace an existing destination file.

For example, if `B:README.TXT` already exists, an ordinary copy to that name will not silently overwrite it.

Resident COPY provides `/O` to permit replacement of existing writable destination files:

```text
A>COPY README.TXT B: /O
```

Read-only destination files remain protected.

The option does not permit a copy operation to overwrite one of its own selected source files.

### Copying to a New Filename

When copying a single file, you can specify a different destination name:

```text
A>COPY REPORT.TXT B:REPORT.BAK
```

This creates `REPORT.BAK` on drive B.

For multiple-file selections, resident COPY retains the source filenames when the destination specifies only a drive/user area.

Wildcard destination templates are provided by the transient COPY utility.

### Transient COPY.COM

The transient utility provides additional file-copying capabilities.

Invoke it explicitly:

```text
A>:COPY
```

or:

```text
A>.COPY
```

The general command forms remain:

```text
COPY source destination
COPY destination=source
```

However, COPY.COM supports additional source-selection, destination-naming, and file-management options.

### COPY.COM Options

| Option | Description |
|---|---|
| `/O` | Replace existing writable destination files |
| `/S` | Skip existing writable destination files |
| `/B` | Operate without file-collision prompts |
| `/V` | Verify copied files by reading and comparing their contents |
| `/BACKUP` | Clear the archive attribute after successful backup copying |

The `/O` and `/S` options are mutually exclusive.

The `/B` and `/V` options can be combined with either.

### Overwriting and Skipping Files

By default, transient COPY requests instructions when an existing writable destination file would be replaced.

The available responses include:

| Response | Meaning |
|---|---|
| Y | Replace this file |
| N | Skip this file |
| O | Replace this and subsequent writable collisions |
| S | Skip this and subsequent writable collisions |
| R | Supply a new destination filename |
| ? | Display help |

The O and S responses apply only to the current COPY operation.

They do not permanently change COPY's behavior.

Read-only destination files remain protected.

### Renaming a Destination During Copying

If an existing destination file would be overwritten, the R response allows you to supply a different filename.

For example, suppose you're copying `REPORT.TXT` to drive B, but a file with that name already exists.

At the collision prompt, enter `R`.

COPY asks for a new name:

```text
New Name:
```

You might enter:

```text
REPORT2.TXT
```

COPY then uses that filename in the same destination drive/user area.

The replacement name must be an exact CP/M filename, without wildcards or a drive/user qualification.

If the new name also exists, COPY applies its normal collision handling to that name.

### Batch-Oriented Copying

The `/B` option is intended for operations that should not stop for file-collision prompts.

For example:

```text
A>:COPY B1:*.DAT C3: /B
```

If a writable destination already exists, COPY reports `FILE EXISTS` for that file and continues with the remaining files.

It does not automatically overwrite or skip the collision as a successful operation.

To specify the desired policy, combine `/B` with `/O` or `/S`.

To overwrite existing writable destinations:

```text
A>:COPY B1:*.DAT C3: /B /O
```

To skip existing destinations:

```text
A>:COPY B1:*.DAT C3: /B /S
```

Read-only destinations remain protected in both cases.

The `/B` option is useful in SUBMIT files, but it applies only to COPY. It does not make other commands in the batch noninteractive.

### Verifying Copied Files

Use `/V` to request verification:

```text
A>:COPY REPORT.TXT B: /V
```

After copying the file, COPY reopens the source and destination and compares their contents.

A successful verification provides additional confidence that the destination contains the same data as the source.

If verification fails, COPY reports the problem and provides the appropriate recovery choices.

With `/B`, a failed copy or verification does not stop for an interactive retry prompt.

An incomplete destination is removed when possible, and COPY continues according to its error-handling rules.

For important backups, `/V` is recommended.

### Wildcard Destination Templates

Transient COPY supports wildcard templates in destination filenames.

For example:

```text
A>:COPY C3:*.DOC=A4:*.COM
```

This copies matching `.COM` files from A4 to C3, changing their file type to `.DOC`.

A more selective template might be:

```text
A>:COPY C3:X?*.BAK=A4:FOOBAR.COM
```

This creates `XOOBAR.BAK`.

The destination template uses literal characters to replace source positions, question marks to retain corresponding characters, and a terminal asterisk to retain the remainder of a filename field.

The command validates the resulting destination names before copying.

### Copying Files from Several User Areas

Transient COPY supports extended source selectors.

For example:

```text
A>:COPY [A[-],B[-],C[-]]:*.COM D0:
```

This selects `.COM` files from all user areas on drives A, B, and C and copies them to D0.

The destination must still identify one drive/user area.

COPY checks the combined selection before beginning.

If different source files would produce the same destination filename, the operation is rejected.

Transient COPY.COM supports a maximum of 64 matched source files in a single invocation.

Larger selections must be divided into smaller operations.

### Destination Attributes

Transient COPY allows destination attributes to be specified explicitly.

For example:

```text
A>:COPY A0:*.COM D0:[$RW,!$ARC]
```

This requests writable destination copies with the archive attribute cleared.

Attributes not explicitly changed are preserved.

The destination attribute expression is different from a source-selection expression: it specifies the attributes to assign to completed destination files.

It does not override protection on an existing read-only destination.

### Backup Operations

The `/BACKUP` option supports workflows using CP/M's archive attribute.

For example:

```text
A>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

This selects `.DOC` files marked with the archive attribute, copies them to D0, verifies the copies, and clears the archive attribute on both source and destination after successful completion.

Files that are skipped, fail to copy, or are interrupted retain their source archive status.

The `/BACKUP` option does not automatically select archive-marked files. The `[$ARC]` expression performs that selection.

Similarly, `/BACKUP` does not automatically enable verification. Include `/V` when verification is desired.

**The archive attribute should not be assumed to identify every file changed since the last backup unless the software maintaining those files updates the attribute appropriately.**

### Copy Errors and Recovery

COPY reports errors such as missing source files, unavailable destinations, insufficient disk space, read/write failures, and verification failures.

The transient utility attempts to remove incomplete destination files when an operation fails.

If that cleanup cannot be completed, COPY reports the problem and stops rather than leaving an incomplete file without warning.

Previously completed copies remain available.

### Examples

Copy a file:

```text
A>COPY README.TXT B:
```

Copy a file under another name:

```text
A>COPY REPORT.TXT B:REPORT.BAK
```

Copy all assembly-language source files:

```text
A>COPY *.ASM B:
```

Copy files across several user areas:

```text
A>COPY B[-]:*.DOC C3:
```

Copy and verify:

```text
A>:COPY /V *.COM B:
```

Copy without overwrite prompts, replacing existing writable files:

```text
A>:COPY /B /O *.DAT B:
```

Back up archive-marked files:

```text
A>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

---

## 14.6 MOVE — Move Files

**Purpose:** Moves one or more files to another filename, drive, or user area.

MOVE is available as a resident command in BetterCP/M 1.0.

It provides a convenient way to reorganize files without separately copying them and deleting the originals.

Unlike COPY, MOVE removes the source file after successfully creating the destination.

### Command Syntax

MOVE accepts two equivalent forms:

```text
MOVE source destination
MOVE destination=source
```

For example:

```text
A>MOVE README.TXT B:
```

moves `README.TXT` from the current drive and user area to drive B.

You can also write:

```text
A>MOVE B:README.TXT=README.TXT
```

Both commands have the same effect.

### Moving Files Between User Areas

BetterCP/M allows files to be moved between user areas.

For example:

```text
A>MOVE A3:REPORT.TXT B5:
```

moves `REPORT.TXT` from A3 to B5.

The original file is removed only after the destination has been successfully created.

This is particularly useful when reorganizing project files among user areas.

### Moving Several Files

MOVE accepts wildcard specifications:

```text
A>MOVE *.BAK B:
```

This moves matching backup files to drive B.

Extended drive/user selectors are also supported:

```text
A>MOVE B[-]:*.DOC C3:
```

This selects `.DOC` files across all user areas on drive B and moves them to C3.

The destination must identify a single drive/user area.

If multiple source files would produce the same destination filename, MOVE rejects the conflicting selection.

### Selecting Files by Attribute

MOVE supports BetterCP/M's shared file-selection expressions.

For example:

```text
A>MOVE B[-]:*.DOC[$RW+!$SYS] C4:
```

This selects writable, non-system `.DOC` files from drive B's user areas.

Read-only source files are protected.

Attribute expressions determine which files are selected; they do not automatically override file protection.

### Moving a File to a New Name

MOVE can assign a new filename when moving a single file.

For example:

```text
A>MOVE REPORT.TXT B:REPORT.BAK
```

This moves the file to drive B and renames it `REPORT.BAK`.

The original `REPORT.TXT` is removed after the destination has been successfully written.

### Existing Destination Files

MOVE does not overwrite existing destination files.

If a destination name already exists, MOVE reports the conflict rather than replacing the file.

Unlike transient COPY, resident MOVE does not provide an overwrite option.

If you need to replace an existing destination, handle that file separately before moving the new one.

Be careful when removing existing files, particularly when working with wildcard specifications.

### How MOVE Handles Files

MOVE copies the file to its destination and removes the original only after the destination has been successfully written and closed.

This applies even when moving a file within the same drive/user area.

If the destination cannot be created or written successfully, MOVE does not intentionally erase the source.

However, an unexpected failure can interrupt a multi-file move after some files have already been transferred.

Earlier completed moves are not automatically reversed.

### Source Deletion Failures

Occasionally, MOVE may successfully create the destination but be unable to remove the original.

In that case, it reports:

```text
COPY MADE; SOURCE NOT ERASED
```

This means that the destination copy was created, but the source remains in place.

You should examine both files before deciding whether to delete the original manually.

### Moving Several Files Safely

When moving a large group of files, it's wise to check the source and destination directories first.

For example:

```text
A>DIR B3:*.DOC
A>DIR C4:*.DOC
```

This allows you to identify possible filename conflicts before moving the files.

You can then enter:

```text
A>MOVE B3:*.DOC C4:
```

Afterward, examine the destination:

```text
A>DIR C4:*.DOC
```

If MOVE reported an error, also examine the source to determine which files remain.

### COPY or MOVE?

COPY and MOVE serve different purposes.

Use **COPY** when you want to create another copy of a file while retaining the original.

Use **MOVE** when you want to relocate a file and no longer need it in its original location.

For important files, copying and verifying them before manually deleting the originals may provide additional reassurance.

MOVE is convenient for routine file organization, but it should not be treated as a substitute for maintaining backups.

### Examples

Move a file to another drive:

```text
A>MOVE README.TXT B:
```

Move a file to another user area:

```text
A>MOVE A3:REPORT.TXT B5:
```

Move a file and change its name:

```text
A>MOVE REPORT.TXT B:REPORT.BAK
```

Move all backup files:

```text
A>MOVE *.BAK B:
```

Move selected files from several user areas:

```text
A>MOVE B[-]:*.DOC C3:
```

Move writable, non-system files:

```text
A>MOVE B[-]:*.DOC[$RW+!$SYS] C4:
```

---

# Chapter 15 — System and Environment Commands

This chapter describes the commands used to manage the BetterCP/M operating environment, examine system information, and work directly with memory.

Several of these commands will be familiar to users of Digital Research CP/M 2.2. Others are BetterCP/M extensions that provide convenient access to facilities traditionally associated with debugging and system maintenance.

The commands covered are:

| Command | Purpose |
|---|---|
| USER | Select the current user area |
| CLS | Clear the console screen |
| VER | Display system version information |
| SAVE | Save memory to a file |
| GET | Load a file into memory |
| GO | Execute a program at address 0100H |
| JUMP | Transfer control to a specified address |
| PEEK / P | Examine memory |
| POKE | Modify memory |

The memory-oriented commands are particularly useful when examining programs, testing small machine-language routines, or working with program images.

Because these commands can access memory directly, some require more care than ordinary file-management commands. In particular, executing arbitrary memory addresses or modifying operating-system memory can cause a program to fail or make the current session unusable.

## 15.1 USER — Select User Area

**Purpose:** Changes the current user area on the selected drive.

BetterCP/M retains the conventional CP/M USER command while extending the available range of user areas.

### Syntax

```text
USER number
```

The number specifies a user area from 0 through 31.

For example:

```text
A>USER 3
A3>
```

This selects user area 3 on drive A.

To select user area 17:

```text
A3>USER 17
A17>
```

The prompt changes to reflect the new user area.

### Direct User-Area Selection

BetterCP/M also allows you to select a user area directly by entering its number followed by a colon.

For example:

```text
A>3:
A3>
```

This is equivalent to:

```text
A>USER 3
```

You can also select a drive and user area together:

```text
A3>B17:
B17>
```

This selects drive B, user area 17.

### User Areas and File Access

Changing the current user area affects commands that do not explicitly specify another location.

For example, after selecting user area 3:

```text
A3>DIR
```

displays files in user area 3 on drive A.

To examine another user area without changing the current selection:

```text
A3>DIR B5:
```

The current drive and user area remain unchanged after the command.

### Compatibility

The USER command is retained for compatibility with conventional CP/M usage.

BetterCP/M supports user areas 0 through 31, extending the traditional CP/M 2.2 range of 0 through 15.

USER is a resident command. There is no separate transient `USER.COM`.

For more information about drives and user areas, see Chapter 4.

---

## 15.2 CLS — Clear Screen

**Purpose:** Clears the console display and returns the cursor to the upper-left corner.

### Syntax

```text
CLS
```

### Example

```text
A>CLS
```

CLS clears the current display.

This is useful when the screen has become cluttered with directory listings, program output, or command messages.

### Resident and Transient Versions

CLS is normally supplied as a resident command by `RCP.CPX`.

A transient `CLS.COM` is also provided, allowing the command to remain available when the resident command package is not loaded.

To invoke the transient version explicitly:

```text
A>:CLS
```

### Terminal Considerations

The exact screen-clearing operation depends on the active console environment.

On systems using BetterCP/M's terminal-monitor facilities, the operation is performed through the appropriate display support.

The visible result is normally a cleared screen with the cursor positioned at the beginning of the display.

The underlying method may differ between supported computers and terminal environments.

For more information about terminal support, see Chapter 9.

---

## 15.3 VER — Display Version Information

**Purpose:** Displays information identifying the running BetterCP/M system.

VER is useful when checking the operating-system release, identifying the installed software, or reporting a problem.

### Syntax

```text
VER
VER /V
VER /BANNER
```

The available forms provide different levels of information.

### Displaying the System Version

Enter:

```text
A>VER
```

VER displays the BetterCP/M system identification and release version.

This is the simplest way to determine which version of BetterCP/M is running.

### Detailed Version Information

To display additional subsystem information:

```text
A>VER /V
```

The `/V` option provides more detailed identification information about the operating-system environment.

This can be useful when comparing installations or determining whether a particular subsystem has been updated.

### Displaying the Startup Banner

The transient VER utility provides the system identification banner used by the standard distribution's startup procedure.

Enter:

```text
A>:VER /BANNER
```

The `/BANNER` option is provided by `VER.COM`.

If you attempt to use it with the resident command:

```text
A>VER /BANNER
```

BetterCP/M reports:

```text
VER: Use :VER.
```

You can then invoke the transient utility explicitly.

### Resident and Transient Versions

VER is normally available as a resident command through `RCP.CPX`.

The transient `VER.COM` provides additional facilities, including the startup banner.

As with other commands available in both forms, prefixing the command name with a colon or period requests the transient version.

### Version Information for Individual Utilities

Most BetterCP/M utilities also support `/VER` to display their own version and build information.

For example:

```text
A>:DIR /VER
```

identifies the transient DIR utility.

This is different from the VER command, which identifies the operating system itself.

For additional information about utility version conventions, see Chapter 13.

---

## 15.4 SAVE — Save Memory to a File

**Purpose:** Saves a specified number of 256-byte memory pages to a disk file.

SAVE is a core resident command retained from conventional CP/M.

It is particularly useful when working with programs or data that have been loaded or modified directly in memory.

### Syntax

```text
SAVE pages filespec
```

The `pages` argument specifies the number of 256-byte pages to save.

The memory is saved beginning at address `0100H`, the conventional start of the CP/M Transient Program Area.

### Examples

Save ten pages:

```text
A>SAVE 10 TEST.COM
```

This writes 2,560 bytes from memory beginning at `0100H` into `TEST.COM`.

Save forty pages to drive B:

```text
A>SAVE 40 B:PROGRAM.COM
```

Save twenty pages to drive B, user area 3:

```text
A>SAVE 20 B3:IMAGE.COM
```

BetterCP/M extends the conventional SAVE command by allowing drive/user-qualified destination file specifications.

### Calculating the Number of Pages

Each page contains 256 bytes.

To determine the number of pages required, divide the number of bytes by 256 and round upward.

For example:

| Bytes to save | Pages |
|---:|---:|
| 256 | 1 |
| 1,024 | 4 |
| 2,560 | 10 |
| 4,096 | 16 |
| 10,240 | 40 |

If the data does not occupy an exact number of pages, the final saved page includes any remaining bytes within that page.

### Using SAVE with GET and POKE

SAVE can be used with BetterCP/M's memory commands.

For example, you might load a program with GET, modify several bytes with POKE, and then save the modified image under another filename.

```text
A>GET PROGRAM.COM
A>POKE 100 C3 00 80
A>SAVE 10 MODIFIED.COM
```

This example illustrates the general procedure. The number of pages saved must be appropriate to the size of the program or data.

SAVE does not determine the logical size of the program automatically.

### Resident Command

SAVE is implemented directly by the command processor.

It is not provided as an ordinary transient utility because loading a transient `SAVE.COM` could overwrite the very memory that SAVE is intended to preserve.

### Important Considerations

SAVE writes the contents of memory as they exist when the command executes.

It does not determine whether those contents form a valid executable program.

If you save a memory region containing incomplete or unrelated data, the resulting file will contain that data.

Likewise, saving too few pages truncates the intended image, while saving too many pages includes additional memory contents.

---

## 15.5 GET — Load a File into Memory

**Purpose:** Loads a file into memory without executing it.

GET is useful when examining or modifying program images, preparing machine-language routines for execution, or loading data into a particular memory location.

Unlike ordinary program execution, GET returns to the command prompt after loading the file.

### Syntax

```text
GET filename
GET address filename
```

With one argument, GET loads the file beginning at address `0100H`.

With two arguments, the first specifies the hexadecimal memory address at which loading begins.

### Examples

Load a program at `0100H`:

```text
A>GET PROGRAM.COM
```

Load a file at address `8000H`:

```text
A>GET 8000 DATA.BIN
```

The address is hexadecimal.

Leading zeroes are optional.

### Examining Loaded Data

After loading a file, you can examine its contents with PEEK.

For example:

```text
A>GET PROGRAM.COM
A>PEEK 100
```

This displays memory beginning at address `0100H`.

You can also modify the loaded data with POKE.

### Executing a Loaded Program

A program loaded at `0100H` can subsequently be executed with GO:

```text
A>GET PROGRAM.COM
A>GO
```

Alternatively, JUMP can transfer control to a specified address.

### Memory Protection

GET checks whether the requested load would overwrite memory required by the active BetterCP/M command environment.

If the file cannot be loaded safely, GET rejects the operation.

This protection helps prevent accidental damage to resident operating-system components.

Nevertheless, GET is intended for users who understand the memory requirements of the programs or data being loaded.

---

## 15.6 GO — Execute at 0100H

**Purpose:** Transfers control to address `0100H`, the conventional entry point for CP/M transient programs.

GO is useful when executing a program image that has already been loaded into memory.

### Syntax

```text
GO [command tail]
```

The command tail is optional.

### Examples

Execute the program currently loaded at `0100H`:

```text
A>GO
```

Execute it with a command-line argument:

```text
A>GO INPUT.DAT
```

The command tail is supplied to the program using the normal CP/M transient-program conventions.

### Using GO with GET

A common sequence is:

```text
A>GET PROGRAM.COM
A>GO
```

GET loads the program into memory.

GO then transfers control to it.

This allows a program to be loaded, examined, or modified before execution.

### Relationship to JUMP

GO is equivalent to:

```text
JUMP 0100
```

Both transfer control to address `0100H`.

GO is provided as a convenient shorthand for the most common CP/M program entry point.

### Program Environment

Before transferring control, BetterCP/M establishes the normal CP/M transient-program environment.

This includes the expected command tail, default File Control Blocks, and other program-entry conditions.

Ordinary CP/M programs therefore receive the familiar execution environment.

### Caution

GO does not verify that memory at `0100H` contains a valid program.

If the memory contains unrelated data or an incomplete program image, execution may fail.

Use GO only when you know that an appropriate program has been loaded.

---

## 15.7 JUMP — Execute at an Address

**Purpose:** Transfers control to a specified memory address.

JUMP extends the functionality of GO by allowing execution to begin at an address other than `0100H`.

### Syntax

```text
JUMP address [command tail]
```

The address is hexadecimal.

### Examples

Execute at `0100H`:

```text
A>JUMP 100
```

Execute at `8000H`:

```text
A>JUMP 8000
```

Execute at `0100H` with an argument:

```text
A>JUMP 100 INPUT.DAT
```

### Using JUMP with GET

JUMP can be used to execute a routine loaded at a nonstandard address.

For example:

```text
A>GET 8000 ROUTINE.BIN
A>JUMP 8000
```

This loads `ROUTINE.BIN` at address `8000H` and transfers control to that address.

The routine must be suitable for execution at the selected address.

### Program Environment

Like GO, JUMP establishes the normal CP/M transient-program environment before transferring control.

This includes the standard command-tail and default FCB arrangements.

### Address Range

JUMP accepts hexadecimal addresses from `0000H` through `FFFFH`.

However, **not every address is a valid or safe execution address**.

Some locations contain operating-system code, data, interrupt vectors, or other system structures.

Transferring control to an arbitrary address can cause the system to malfunction.

JUMP should therefore be used only when the contents and purpose of the target address are known.

### Error Handling

If the address is missing or invalid, JUMP reports an error and returns to the command prompt.

It does not attempt to execute an invalid address specification.

---

## 15.8 PEEK / P — Display Memory

**Purpose:** Displays memory contents in hexadecimal and ASCII form.

PEEK is useful for examining loaded programs, checking data values, and inspecting memory while developing or debugging software.

The abbreviated command `P` is equivalent to `PEEK`.

### Syntax

```text
PEEK
PEEK address
PEEK first last
```

The abbreviated forms are:

```text
P
P address
P first last
```

All addresses are hexadecimal.

### Examples

Display memory beginning at `0100H`:

```text
A>PEEK 100
```

Display memory beginning at `8000H`:

```text
A>P 8000
```

Display an explicit range:

```text
A>PEEK 100 1FF
```

### Displaying 256 Bytes

When one address is supplied, PEEK displays 256 bytes beginning at that address.

For example:

```text
A>PEEK 100
```

displays the 256-byte region beginning at `0100H`.

The output includes hexadecimal byte values and their corresponding ASCII representation where appropriate.

### Displaying a Range

When two addresses are supplied, PEEK displays the inclusive range from the first address through the last.

For example:

```text
A>PEEK 100 1FF
```

displays memory from `0100H` through `01FFH`.

The ending address is included.

### Continuing a Display

If no address is supplied, PEEK uses its remembered display position.

The first invocation begins at `0100H`.

Subsequent invocations continue from the byte following the previous display.

For example:

```text
A>PEEK 100
A>PEEK
```

The second command continues where the first left off.

### Paging Controls

During a paged display, the following controls are available:

| Key | Action |
|---|---|
| Space, `.`, `>` | Display the next page |
| `,`, `<` | Display the previous page |
| Ctrl-C | Return to the command prompt |

These controls make it convenient to examine consecutive regions of memory without entering a new address each time.

### Address Boundaries

PEEK does not wrap automatically from `FFFFH` back to `0000H`.

This prevents an ordinary memory display from unexpectedly continuing at the beginning of the address space.

### Using PEEK with GET and POKE

PEEK is particularly useful alongside the other resident memory commands.

For example:

```text
A>GET PROGRAM.COM
A>PEEK 100
A>POKE 100 C3 00 80
A>PEEK 100
```

This loads a program, examines its beginning, modifies three bytes, and displays the modified memory.

PEEK itself does not change memory.

---

## 15.9 POKE — Modify Memory

**Purpose:** Stores hexadecimal byte values or literal text directly into memory.

POKE is useful for modifying loaded program images, preparing data, or testing small machine-language routines.

Because it writes directly to memory, it should be used with care.

### Syntax

```text
POKE address byte [byte ...]
POKE address "text
POKE address byte [byte ...] "text
```

The address and byte values are hexadecimal.

A quotation mark introduces literal text. All remaining characters on the command line are stored as text.

### Writing Hexadecimal Bytes

For example:

```text
A>POKE 100 C3 00 80
```

writes three bytes beginning at address `0100H`:

```text
0100H  C3
0101H  00
0102H  80
```

The bytes are stored consecutively.

### Writing Text

POKE can also store literal text.

For example:

```text
A>POKE 200 "Hello
```

writes the characters of `Hello` beginning at address `0200H`.

The opening quotation mark identifies the beginning of the text.

A closing quotation mark is not required by this command form.

### Combining Bytes and Text

Hexadecimal bytes and text can be combined.

For example:

```text
A>POKE 300 0D 0A "BetterCP/M
```

This writes carriage return and line feed bytes, followed by the text `BetterCP/M`.

This is useful when preparing data containing both control characters and printable text.

### Input Validation

POKE validates the address and hexadecimal byte operands before modifying memory.

If an operand is invalid, the command rejects the operation without performing a partial modification.

For example, an invalid hexadecimal byte does not cause the preceding valid bytes to be written before the error is reported.

### Examining Changes

Use PEEK to verify the contents of memory after a POKE operation.

For example:

```text
A>POKE 100 C3 00 80
A>PEEK 100
```

The second command displays the bytes beginning at `0100H`.

### Saving Modified Memory

After modifying a loaded program, you can use SAVE to write the memory image to a file.

For example:

```text
A>GET PROGRAM.COM
A>
```

## 15.8 PEEK / P — Display Memory

**Purpose:** Displays the contents of memory in hexadecimal and ASCII form.

PEEK provides a convenient way to examine memory without modifying its contents. It is particularly useful when inspecting loaded programs, examining data structures, or checking the results of changes made with POKE.

The command can also be abbreviated to `P`.

### Syntax

```text
PEEK
PEEK address
PEEK first last
```

Or, using the abbreviated form:

```text
P
P address
P first last
```

All addresses are hexadecimal.

### Displaying Memory

To display memory beginning at address `0100H`, enter:

```text
A>PEEK 100
```

PEEK displays 256 bytes beginning at the specified address.

The display includes hexadecimal byte values and their corresponding ASCII representations, making it possible to examine both machine-language instructions and ordinary character data.

For example:

```text
A>P 8000
```

displays 256 bytes beginning at address `8000H`.

### Displaying an Address Range

You can specify both the first and last addresses to display.

For example:

```text
A>PEEK 100 1FF
```

This displays the inclusive range from `0100H` through `01FFH`.

The first address identifies the beginning of the range, while the second identifies its final byte.

PEEK does not wrap around from `FFFFH` to `0000H`.

### Continuing a Memory Display

If you enter PEEK without an address:

```text
A>PEEK
```

the first invocation begins at `0100H`.

Subsequent invocations continue from the byte following the previous display.

This allows you to examine consecutive regions of memory without repeatedly calculating addresses.

For example:

```text
A>PEEK
A>PEEK
A>PEEK
```

displays successive portions of memory.

### Paging Through Memory

PEEK supports interactive paging when displaying memory.

The following keys control navigation:

| Key | Action |
|---|---|
| Space | Display the next page |
| `.` | Display the next page |
| `>` | Display the next page |
| `,` | Display the previous page |
| `<` | Display the previous page |
| Ctrl-C | Return to the command prompt |

These controls allow you to move forward and backward through the displayed memory.

### Using PEEK with GET

PEEK is especially useful after loading a program or data file with GET.

For example:

```text
A>GET PROGRAM.COM
A>PEEK 100
```

GET loads `PROGRAM.COM` into memory beginning at `0100H`.

PEEK then displays the first 256 bytes of the loaded image.

You can examine additional portions by specifying other addresses or continuing the display.

### Using PEEK with POKE

PEEK can also be used to verify memory changes.

For example:

```text
A>POKE 200 48 45 4C 4C 4F
A>PEEK 200
```

The POKE command stores five bytes beginning at address `0200H`.

PEEK then displays the corresponding memory region.

The hexadecimal values represent the ASCII characters `HELLO`.

### Important Considerations

PEEK displays the contents of memory as they exist when the command executes.

It does not interpret the contents as program instructions or determine whether the data is meaningful.

Memory may contain executable code, program data, operating-system structures, or unused values.

PEEK itself does not modify memory, but the contents of some memory locations may change as programs or the operating system execute.

For disassembly and more advanced debugging operations, use an appropriate debugging utility such as DDT.

---

## 15.9 POKE — Modify Memory

**Purpose:** Stores hexadecimal byte values or literal text directly into memory.

POKE provides a convenient way to modify memory without loading a separate debugger.

It can be used to patch a program image, enter small machine-language routines, or modify data that has been loaded with GET.

Unlike PEEK, **POKE changes memory contents**. Incorrect modifications can damage a loaded program or interfere with the operating system.

### Syntax

```text
POKE address byte [byte ...]
POKE address "text
POKE address byte [byte ...] "text
```

The address and hexadecimal byte values are required in their respective forms.

The address specifies where writing begins.

Successive bytes are stored in consecutive memory locations.

### Storing Hexadecimal Bytes

For example:

```text
A>POKE 100 C3 00 80
```

stores three bytes beginning at address `0100H`:

| Address | Value |
|---|---|
| `0100H` | `C3H` |
| `0101H` | `00H` |
| `0102H` | `80H` |

These bytes form a Z80 absolute jump instruction to address `8000H`.

POKE stores the values exactly as specified. It does not interpret them as instructions while writing them.

### Storing Text

POKE can also store literal text.

For example:

```text
A>POKE 200 "Hello
```

stores the ASCII characters `Hello` beginning at address `0200H`.

A quotation mark introduces literal text. All remaining characters on the command line are stored as text.

A closing quotation mark is not required.

### Combining Bytes and Text

You can combine hexadecimal byte values with literal text.

For example:

```text
A>POKE 300 0D 0A "BetterCP/M
```

This stores a carriage return (`0DH`) and line feed (`0AH`), followed by the ASCII characters in `BetterCP/M`.

This is useful when constructing small data structures or preparing text containing control characters.

### Examining the Results

Use PEEK to examine the memory after making a change.

For example:

```text
A>POKE 200 "Hello
A>PEEK 200
```

PEEK displays the modified memory, including the hexadecimal values and ASCII representation.

### Modifying a Loaded Program

POKE can be used with GET and SAVE to modify a program image.

For example:

```text
A>GET PROGRAM.COM
A>POKE 120 00
A>PEEK 120
A>SAVE 10 MODIFIED.COM
```

This sequence:

1. Loads `PROGRAM.COM` into memory.
2. Changes the byte at address `0120H` to `00H`.
3. Displays the modified memory.
4. Saves ten 256-byte pages to `MODIFIED.COM`.

The example illustrates the procedure rather than a useful program modification. The address, replacement value, and number of pages must be appropriate to the actual program.

### Input Validation

POKE checks the address and hexadecimal byte operands before modifying memory.

If an operand is invalid, the command rejects the operation without making a partial modification.

For example, an invalid hexadecimal byte does not cause POKE to write the preceding valid bytes and then stop.

This helps prevent accidental partial changes caused by mistyped commands.

However, POKE cannot determine whether a valid address and byte sequence are appropriate for the program being modified.

### Memory Safety

POKE is intended for users who understand the memory locations they are changing.

Writing to the wrong address can corrupt program data, overwrite executable instructions, or interfere with operating-system structures.

A valid hexadecimal address is not necessarily a safe address to modify.

If you're experimenting with machine-language programs, work with known memory locations and keep copies of the original program files.

When modifying a loaded program, use PEEK to verify the changes before executing or saving it.

### Using the Memory Commands Together

BetterCP/M provides a small collection of resident commands that can be used together for memory inspection, modification, loading, execution, and saving.

| Command | Purpose |
|---|---|
| GET | Load a file into memory |
| PEEK / P | Examine memory |
| POKE | Modify memory |
| GO | Execute at `0100H` |
| JUMP | Execute at a specified address |
| SAVE | Save memory to a file |

Together, these commands provide convenient facilities for simple memory-oriented tasks without requiring a separate debugger.

For more extensive debugging, including disassembly, breakpoints, and register examination, use a dedicated debugging utility such as DDT.

---

# Chapter 16 — System Utilities

BetterCP/M provides several utilities for configuring the operating system, examining files and disks, managing the system clock, and preparing or maintaining system disks.

These utilities generally perform more specialized operations than the commands described in Chapters 14 and 15. Some modify the operating environment, while others work directly with disk formats or the operating system's reserved system area.

This chapter covers five utilities:

| Utility | Purpose |
|---|---|
| CONFIG | Examine and modify system configuration |
| STAT | Display disk and file information and manage supported attributes and device assignments |
| TIME | Display the date and time and identify clock providers |
| DUP | Format, copy, and check disks |
| SYSGEN | Install BetterCP/M and save system images |

Chapter 7 introduced system configuration, Chapter 10 explained disk operations, and Chapter 11 covered date and time facilities. This chapter provides the corresponding command references.

Because some of these utilities can modify disk structures or operating-system settings, pay particular attention to their confirmation procedures and restrictions.

## 16.1 CONFIG — System Configuration

**Purpose:** Examines and modifies BetterCP/M's system configuration, including startup commands, disk-drive definitions, disk formats, and the saved cold-boot IOBYTE.

CONFIG provides both an interactive menu and command-line operations.

It distinguishes between settings currently in use, changes prepared for saving, and settings already saved for subsequent cold boots.

### Syntax

The principal forms are:

```text
CONFIG
CONFIG /SHOW
CONFIG /DEFAULT
CONFIG /STARTUP="command"
CONFIG /STARTUP=""
CONFIG /IOBYTE=value
CONFIG /VER
```

Additional command-line forms are available for physical-drive profiles, logical-drive assignments, and disk-format definitions.

### Interactive Configuration

Enter:

```text
A>CONFIG
```

CONFIG displays a menu containing the available configuration operations:

```text
[ A ] Startup command

[ B ] Cold-boot IOBYTE

[ C ] Disk drive definitions
[ D ] Disk format definitions
[ E ] Create or edit a disk format

[ S ] Save current configuration on disk (SYSGEN)
```

Select the letter corresponding to the operation you want to perform.

Press Ctrl-C to leave the main menu.

CONFIG operates through the ordinary console and does not require a terminal-monitor extension.

### Displaying the Configuration

To examine the current configuration without changing it:

```text
A>CONFIG /SHOW
```

This displays information about the active physical-drive profiles, logical-drive assignments, saved startup command, and saved drive defaults.

It also distinguishes between the live IOBYTE and the value saved for subsequent cold boots.

This is particularly useful when troubleshooting a configuration problem or determining whether temporary changes have been saved.

### Startup Commands

BetterCP/M can execute a command automatically during a cold boot.

The standard distribution uses:

```text
SUBMIT STARTUP
```

This executes `STARTUP.SUB`, allowing the system to establish a preferred working environment.

To change the saved startup command:

```text
A>CONFIG /STARTUP="SUBMIT STARTUP"
```

CONFIG requests confirmation before saving the change.

The new command takes effect during a subsequent cold boot. It is not executed immediately.

To disable automatic startup commands:

```text
A>CONFIG /STARTUP=""
```

An empty startup command prevents BetterCP/M from automatically executing a command during cold startup.

### Restoring the Default Startup Command

Enter:

```text
A>CONFIG /DEFAULT
```

This prepares `SUBMIT STARTUP` as the pending startup command and opens the appropriate configuration menu.

The change is not automatically saved.

You can inspect or modify it before committing it to the system disk.

`/DEFAULT` affects the startup command; it does not restore every configuration setting to its original value.

### Physical-Drive Configuration

CONFIG provides command-line facilities for changing physical-drive characteristics.

For example:

```text
A>CONFIG /PHYSICAL=1 /TRACKS=80 /SIDES=2 /STEP=6
```

This requests an 80-track, double-sided configuration for physical drive 1, with the specified step timing.

The supported fields include:

| Option | Purpose |
|---|---|
| `/PHYSICAL=` | Select the physical drive |
| `/TYPE=` | Select 5-inch or 8-inch drive type |
| `/TRACKS=` | Set the track count |
| `/SIDES=` | Set the number of sides |
| `/STEP=` | Set step timing |
| `/SPINUP=` | Set spin-up delay |
| `/SETTLE=` | Set head-settle delay |

The accepted values depend on the field and the platform.

Physical-drive changes affect the active configuration. They do not automatically replace the saved startup defaults.

### Logical-Drive Configuration

To associate a logical drive with a physical drive and disk format:

```text
A>CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="MM 80T DS DATA"
```

This assigns logical drive C to physical drive 1 using the named format.

The format name must match an available definition in the disk-format catalog.

CONFIG checks that the requested assignment is compatible with the selected drive.

To remove a logical-drive assignment:

```text
A>CONFIG /LOGICAL=C /UNBIND
```

This disconnects logical drive C from its active assignment without erasing the disk.

BetterCP/M protects drive A from these logical-binding changes.

### Editing Disk-Format Definitions

CONFIG provides facilities for editing the characteristics of an active disk-format assignment.

For example:

```text
A>CONFIG /EDIT=B /CKS=16
```

This changes the specified field of drive B's active format definition.

Other fields describe the disk's allocation, directory, sector, and physical organization.

These are advanced configuration facilities. An incorrect definition can cause BetterCP/M to interpret an existing disk incorrectly.

**Changing a disk-format definition does not format the disk.** It changes how BetterCP/M attempts to access it.

Use the interactive format editor or the command-line editing facilities only when you know the disk's actual organization.

### Saved IOBYTE

BetterCP/M retains CP/M's IOBYTE mechanism for selecting logical character devices.

STAT changes the live IOBYTE, while CONFIG can save a value for subsequent disk cold boots.

For example:

```text
A>CONFIG /IOBYTE=85
```

The value is decimal.

CONFIG requests confirmation before saving it.

This operation does not change the IOBYTE currently in use.

The selected device assignments must be supported by the computer's BIOS.

### Saving Configuration Changes

CONFIG distinguishes between saving pending cold-boot changes and saving all current settings as the new startup defaults.

For example, you may have temporarily changed a drive assignment while also preparing a new startup command.

Saving only the pending startup change allows you to retain your existing saved drive configuration.

Saving all current settings makes the active configuration the new startup default.

Use the save menu to select the appropriate operation.

CONFIG verifies saved configuration writes and reports failures.

**Keep a backup of a working system disk before making significant changes to saved configuration information.**

### Version Information

Enter:

```text
A>CONFIG /VER
```

CONFIG displays its version and build identification without modifying the system.

The option must be used alone.

### Limitations

CONFIG is not a general-purpose preferences editor.

BetterCP/M 1.0 does not use CONFIG to manage resident extensions, terminal personalities, keyboard mappings, or clock providers.

Those facilities are managed through their respective commands and extensions.

For an introduction to configuration procedures, see Chapter 7.

---

## 16.2 STAT — System and File Statistics

**Purpose:** Displays information about disks, files, and logical devices, and provides supported facilities for examining or changing file attributes and device assignments.

STAT retains the familiar role of Digital Research's CP/M utility while adding support for BetterCP/M's extended drive/user specifications.

### Basic Use

To examine the status of the current disk:

```text
A>STAT
```

STAT displays disk information according to the supported CP/M conventions.

To examine a particular file:

```text
A>STAT REPORT.TXT
```

A drive-qualified file specification can also be used:

```text
A>STAT B:REPORT.TXT
```

### Extended Drive/User Selection

BetterCP/M extends STAT's file-inspection facilities to support explicit user areas and compound selections.

For example:

```text
A>STAT B3:*.COM
```

examines matching files in drive B, user area 3.

To examine several user areas:

```text
A>STAT B[3,5]:*.COM
```

To examine all user areas on drive B:

```text
A>STAT B[-]:*.COM
```

Compound selections are also supported:

```text
A>STAT [A0,C[3,5,7-11],5]:*.DAT
```

STAT processes the selected locations and identifies each result by its drive and user area.

Duplicate locations are visited only once.

### Displaying File Sizes

STAT provides the `$S` option for displaying logical file sizes.

For example:

```text
A>STAT B[3,5]:*.DAT $S
```

This examines matching files in the selected user areas and includes the additional size information.

The distinction between logical file size and allocated disk space is important. CP/M allocates storage in blocks, so a file's allocated space may exceed the amount of data it contains.

### File Attributes

STAT provides conventional CP/M facilities for examining and changing supported file attributes.

These include read-only and system attributes.

Attribute operations can be useful when protecting important files or changing how files appear in directory listings.

Be careful when changing the attributes of operating-system or application files. A protected file may have been marked that way deliberately.

### Logical Device Assignments

STAT also provides the conventional CP/M facilities for examining and changing logical device assignments through the IOBYTE.

These assignments control the supported console, reader, punch, and list-device selections.

For example, a logical list device may be associated with a printer interface provided by the BIOS.

The available assignments depend on the computer.

Changing an IOBYTE assignment does not create hardware support for a device that the BIOS does not provide.

### Extended Selection Restrictions

BetterCP/M's compound drive/user selectors are supported for file inspection.

They are not accepted indiscriminately by every STAT operation.

In particular, extended selectors cannot be used with the conventional drive-wide operations or file-attribute modification forms.

For those operations, use the supported conventional single-location syntax.

### STAT and CONFIG

STAT and CONFIG serve different purposes when managing device assignments.

**STAT changes the live IOBYTE.** Its changes affect the current operating environment.

**CONFIG manages the saved cold-boot IOBYTE.** Its saved value is established during a subsequent disk cold boot.

The two facilities complement one another.

For example, you can use STAT to test a supported device assignment before saving it as a startup default through CONFIG.

### Examples

Examine the current disk:

```text
A>STAT
```

Examine files in user area 3:

```text
A>STAT B3:*.COM
```

Examine files across all user areas on drive B:

```text
A>STAT B[-]:*.COM
```

Display file sizes for selected user areas:

```text
A>STAT B[3,5]:*.DAT $S
```

For further information about drive/user specifications and file attributes, see Chapter 4.

---

## 16.3 TIME — Date and Time

**Purpose:** Displays the current date and time, identifies the installed clock provider, and provides an interface for requesting clock-setting operations.

TIME uses BetterCP/M's resident clock services. It does not communicate directly with individual clock devices.

BetterCP/M 1.0 includes read-only clock providers for FreHD and z80pack.

### Syntax

```text
TIME
TIME /PROVIDER
TIME /SET LL HH HR MN SC
```

The first form displays the date and time. The second identifies the installed clock provider. The third requests a clock-setting operation.

### Displaying the Date and Time

Enter:

```text
A>TIME
```

TIME obtains the current date and time from the installed provider.

A provider must be loaded before TIME can obtain clock information.

On a TRS-80 Model 4 equipped with FreHD:

```text
A>RSX LOAD FREHDCLK
A>TIME
```

Under z80pack/cpmsim:

```text
A>RSX LOAD ZPRTC
A>TIME
```

If no clock provider is installed, TIME reports that the required service is unavailable.

### Identifying the Provider

Enter:

```text
A>TIME /PROVIDER
```

TIME displays information about the installed clock provider, including its identity, interface version, and capabilities.

The two providers supplied with BetterCP/M 1.0 are:

| Provider | Extension | Capabilities |
|---|---|---|
| FreHD | `FREHDCLK.RSX` | Read-only |
| z80pack | `ZPRTC.RSX` | Read-only |

The provider information can help determine which clock service is active and whether it supports setting the clock.

### Setting the Clock

TIME includes the following SET syntax:

```text
TIME /SET LL HH HR MN SC
```

The arguments are five two-digit hexadecimal bytes representing BetterCP/M's native clock record.

| Argument | Meaning |
|---|---|
| `LL` | Low byte of the day count |
| `HH` | High byte of the day count |
| `HR` | Hour, packed BCD |
| `MN` | Minute, packed BCD |
| `SC` | Second, packed BCD |

The day count is measured from the CP/M clock epoch of December 31, 1977, with day 1 corresponding to January 1, 1978.

For example:

```text
A>TIME /SET 01 00 12 34 56
```

requests January 1, 1978, at 12:34:56.

The hour, minute, and second are represented in packed binary-coded decimal. Thus, hexadecimal byte `12` represents decimal 12, not decimal 18.

TIME checks the arguments before requesting the operation.

Malformed hexadecimal values, invalid BCD digits, and out-of-range time fields are rejected.

### Clock-Setting Limitations

**Neither clock provider supplied with BetterCP/M 1.0 supports setting the clock.**

Consequently, a valid SET request is rejected as unsupported when either `FREHDCLK.RSX` or `ZPRTC.RSX` is installed.

The existing clock value remains unchanged.

The SET interface is implemented for compatibility with the native clock service and for use with providers that support writable clocks.

### P2DOS Compatibility

BetterCP/M provides a separate resident extension, `P2DOS.RSX`, for applications using the P2DOS-compatible clock interface.

To use it under z80pack:

```text
A>RSX LOAD ZPRTC
A>RSX LOAD P2DOS
```

P2DOS obtains its clock services through the installed native provider.

Because the supplied providers are read-only, P2DOS-compatible requests to set the clock are also unsupported.

The P2DOS extension is not required for ordinary use of TIME.

For additional information about clock providers and their capabilities, see Chapter 11.

---

## 16.4 DUP — Disk Utilities

**Purpose:** Formats disks, copies entire disks, and checks disks for physical read errors.

DUP is BetterCP/M's disk-management utility. Unlike the COPY command, which operates on individual files, DUP works directly with the physical organization and contents of a disk.

It provides three principal operations:

| Operation | Purpose |
|---|---|
| FORMAT | Prepare a disk using its assigned disk format |
| COPY | Copy the contents of one disk to another |
| CHECK | Examine a disk for unreadable sectors |

All three operations are available through DUP's interactive menu or directly from the command line.

**Formatting and disk copying can destroy existing data.** Always verify the selected drives before confirming either operation.

### Syntax

```text
DUP
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
DUP /VER
```

For example:

```text
A>DUP
A>DUP /FORMAT B:
A>DUP /COPY A: B:
A>DUP /CHECK C:
```

The command-line forms use the same operations, validations, and safeguards as the interactive menu.

There is no command-line option for bypassing destructive-operation confirmations.

### Interactive Operation

To start DUP interactively, enter:

```text
A>DUP
```

DUP displays its main menu:

```text
A  Format a disk
B  Copy a disk
C  Check a disk for errors
```

Select the desired operation by entering its letter.

DUP then asks for the appropriate drive or drives.

Press Ctrl-C to exit the main menu. At a drive-selection prompt, Ctrl-C returns to the menu.

The current DUP interface supports logical drives A through D.

### Drive and Format Selection

DUP uses the disk-format definition already assigned to each logical drive.

It does not provide a separate disk-format selection menu.

If you need to change a drive's format, use CONFIG before starting DUP.

For example:

```text
A>CONFIG
```

You can then select the appropriate disk format and associate it with the desired logical drive.

DUP uses that assignment when formatting, copying, or checking the disk.

The available formats and operations depend on the computer's BIOS and disk hardware.

A format listed in the system's catalog is not necessarily supported for every operation on every platform.

DUP reports unsupported operations rather than substituting another format.

### Protected System Drive

BetterCP/M protects physical drive 0 against destructive DUP operations.

Physical drive 0 cannot be used as the destination for FORMAT or COPY.

This protection follows the physical drive even if logical drive letters have been reassigned.

The protected drive may still be read by CHECK or used as the source of a disk-copy operation.

This safeguard helps prevent accidental destruction of the running system disk.

### Formatting a Disk

To format a disk interactively, start DUP and select option A.

DUP asks you to identify the logical drive to format.

Alternatively, enter:

```text
A>DUP /FORMAT B:
```

This requests formatting of drive B using its currently assigned format.

DUP validates the drive and format before proceeding.

If the operation is supported, it displays a warning that the destination disk's contents will be destroyed and requests confirmation.

Only `Y` proceeds.

**Formatting destroys the previous contents of the destination disk.**

Make sure the correct disk is inserted and that its existing contents are no longer needed.

#### Format Verification

DUP verifies formatting by reading back the formatted tracks.

If formatting and verification complete successfully, DUP reports the number of tracks processed and displays:

```text
Format complete.
```

If a write or verification error occurs, DUP stops the operation and reports the problem.

An interrupted format may leave the disk only partly formatted.

Do not treat such a disk as ready for normal use.

#### Interrupting Formatting

Ctrl-C can interrupt formatting between disk operations.

An operation already in progress may finish before the interruption takes effect.

If formatting is interrupted, the destination disk may require formatting again before it can be used reliably.

### Copying a Disk

DUP's COPY operation duplicates the contents of an entire disk.

Unlike the file-oriented COPY command, it copies the sector data represented by the source disk's format, including system areas, directories, file data, and unused space.

This makes it useful for preparing duplicate disks and maintaining complete disk backups.

To copy a disk interactively, start DUP and select option B.

DUP asks for the source and destination drives.

Alternatively, enter:

```text
A>DUP /COPY A: B:
```

This requests a copy from drive A to drive B.

The source is read, while the destination is written.

**The destination's previous contents will be replaced.**

#### Two-Drive Requirement

DUP requires two different physical drives for disk copying.

It does not support copying between two disks by repeatedly exchanging them in a single drive.

The destination must also satisfy the system's drive-protection restrictions.

In particular, physical drive 0 cannot be used as the destination.

#### Copying Between Different Formats

DUP examines the format assignments of the source and destination.

If they match, DUP can copy the source without first reformatting the destination.

If they differ, DUP reports that the destination will be formatted to match the source.

The operation proceeds only if the required formatting and copying operations are supported.

DUP requests confirmation before replacing the destination's contents.

Check both the logical and physical drive assignments before proceeding.

#### Copy Verification

DUP verifies copied data by reading it back from the destination and comparing it with the source data.

A successful operation reports:

```text
Copy complete; destination verified.
```

This indicates that the data copied by DUP has been verified.

If a read, write, or comparison error occurs, DUP reports the failure.

An interrupted or failed copy may leave the destination partly written.

Do not rely on such a disk as a complete backup.

#### What DUP Copies

DUP copies the sector contents represented by the source disk's configured format.

This includes the system area, directory information, file data, and unused disk space.

It is not a magnetic flux-level copying utility.

It does not reproduce physical characteristics outside the represented sector data, such as weak sectors or special deleted-data address marks.

For ordinary BetterCP/M and compatible CP/M disks, the operation provides a verified sector-data copy.

#### Temporary Format Changes

When copying between different disk formats, DUP may temporarily change the destination's active format assignment.

It restores the previous assignment when the operation completes.

However, restoring the assignment does not restore the destination disk's former physical format.

After copying, use CONFIG to assign the copied format before accessing the destination normally.

If you intend to use that format regularly, save the appropriate configuration as the new startup default.

### Checking a Disk

DUP's CHECK operation examines a disk for physical read errors without modifying its contents.

It is useful when investigating suspected media problems, checking an unfamiliar disk, or determining whether the sectors of a disk can be read reliably.

To check a disk interactively, start DUP and select option C.

DUP asks you to select the drive to examine.

Alternatively, enter:

```text
A>DUP /CHECK B:
```

This checks the disk in drive B using its currently assigned format.

Unlike FORMAT and COPY, CHECK does not require confirmation because it performs no writes.

#### What CHECK Examines

CHECK reads the sectors represented by the disk-format definition assigned to the selected drive.

If a sector cannot be read successfully, DUP reports the error and its location.

Ordinary read errors do not necessarily stop the check. DUP continues examining the remaining sectors whenever it can safely do so.

When a physical sector contains several logical CP/M records, an unreadable sector is counted once rather than once for each record it contains.

#### Check Results

When CHECK completes, DUP displays:

```text
Check complete. Unreadable sectors: n
```

The value of `n` indicates the number of physical sectors that could not be read successfully.

For example:

```text
Check complete. Unreadable sectors: 0
```

indicates that all sectors examined during the check were readable.

A nonzero count indicates that one or more sectors could not be read.

#### What CHECK Does Not Do

CHECK examines physical readability. It does not repair disks or validate the logical consistency of the filesystem.

In particular, CHECK does not:

- Repair unreadable sectors.
- Reconstruct damaged files or directories.
- Restore deleted files.
- Compare the disk with another disk.
- Verify that individual files contain the expected data.

A disk can pass CHECK while still containing damaged or incorrect files.

If important data may have been corrupted, compare it with a known good copy or restore it from a backup.

#### Interrupting a Check

Press Ctrl-C to interrupt CHECK.

Because CHECK performs no writes, interrupting it does not change the disk.

DUP reports:

```text
Check stopped. No disk contents changed.
```

An interrupted check is incomplete and should not be treated as evidence that the entire disk is readable.

### Errors and Recovery

DUP reports errors encountered during disk operations.

These may include a drive that is not ready, write protection, missing sectors, read errors, unsupported operations, or verification failures.

Where possible, DUP identifies the physical location associated with the error.

For example, it may report the cylinder, side, sector, or record involved.

#### Drive Not Ready

If DUP reports that a drive is not ready, check that the correct disk is inserted and that the drive is available.

On an emulator, verify that the appropriate disk image is attached.

#### Write Protection

If a destination disk is write-protected, DUP cannot format it or write copied data to it.

Check the disk's write-protection setting before retrying.

Do not remove write protection unless you're certain the destination disk is the one you intend to modify.

#### Unsupported Operations

Some disk formats can be described by BetterCP/M's format catalog but cannot be formatted or copied using a particular hardware backend.

DUP reports unsupported operations rather than silently substituting another format.

If an operation is rejected, examine the drive configuration and consult the platform documentation.

#### Read and Verification Errors

A read error indicates that DUP could not obtain the requested data reliably.

A verification error indicates that data read back from the destination did not match the expected contents.

For FORMAT and COPY, errors that make continued operation unsafe cause DUP to stop.

The destination may be incomplete and should not be treated as successfully prepared.

#### Interrupted Operations

DUP recognizes Ctrl-C during physical disk operations.

An operation already in progress may finish before the interruption takes effect.

The consequences depend on the operation:

| Operation | Effect of interruption |
|---|---|
| FORMAT | Destination may be partly formatted |
| COPY | Destination may be partly written |
| CHECK | Operation stops without changing disk contents |

An interrupted FORMAT or COPY should be repeated from a reliable source after the cause of the interruption has been corrected.

### Restoring Temporary Drive Assignments

When DUP temporarily changes a destination drive's format assignment during copying, it attempts to restore the previous assignment before returning to the command prompt.

If restoration fails, DUP displays:

```text
Cannot restore destination configuration. Press a key to retry.
```

Press a key to retry the restoration.

DUP retains the information needed to restore the previous assignment and does not knowingly return to normal operation while the temporary assignment remains installed.

Do not reset the computer merely to dismiss this message. Follow the recovery prompt unless a hardware failure makes further recovery impossible.

### Memory Requirements

DUP requires approximately 51K of available transient program memory.

If resident extensions have reduced the available TPA below this requirement, DUP reports insufficient memory and does not begin the requested operation.

You may be able to recover the required memory by unloading resident extensions that are no longer needed.

For information about managing extensions, see Chapter 8.

### Version Information

To display DUP's version and build identification, enter:

```text
A>DUP /VER
```

DUP displays its identification and returns to the command prompt without performing a disk operation.

### Examples

Start the interactive disk utility:

```text
A>DUP
```

Format drive B:

```text
A>DUP /FORMAT B:
```

Copy the contents of drive A to drive B:

```text
A>DUP /COPY A: B:
```

Check drive C for unreadable sectors:

```text
A>DUP /CHECK C:
```

Display version information:

```text
A>DUP /VER
```

For an introduction to disk formats, system disks, and backup procedures, see Chapter 10, *Working with Disks*.

---

## 16.5 SYSGEN — System Generation

**Purpose:** Installs BetterCP/M onto a prepared system disk or saves an installed operating system as a system-image file.

SYSGEN is used when preparing a bootable BetterCP/M disk, replacing an installed operating system, or preserving a working system configuration.

Unlike DUP, which can format and copy entire disks, SYSGEN works specifically with the operating system's reserved system area.

It can obtain the operating system from another bootable disk or from a `SYSTEM.SYS` package.

SYSGEN also provides the reverse operation: reading the installed operating system from a disk and saving it as a package file for later use.

**SYSGEN does not format disks or copy ordinary files.** It installs or saves the operating system itself.

### Syntax

BetterCP/M 1.0 supports the following forms:

```text
SYSGEN
SYSGEN source: destination:
SYSGEN [drive:]package destination:
SYSGEN source: [drive:]package
SYSGEN source:
SYSGEN /VER
```

The principal operations are:

| Form | Operation |
|---|---|
| `SYSGEN` | Install from drive A, prompting for a destination |
| `SYSGEN A: B:` | Install from one system disk onto another |
| `SYSGEN SYSTEM.SYS B:` | Install from a system-image package |
| `SYSGEN A:` | Save the installed system from A as `SYSTEM.SYS` |
| `SYSGEN A: B:BACKUP.SYS` | Save the installed system under a specified filename |
| `SYSGEN /VER` | Display version information |

Source drives may be A through D. Installation destinations may be B through D, subject to physical-drive restrictions.

### Interactive Installation

To start SYSGEN interactively, enter:

```text
A>SYSGEN
```

SYSGEN uses drive A as the source system and prompts:

```text
Destination drive [ B - D ], or BREAK (^C) to exit:
```

Select the destination drive.

For example, entering `B` requests installation onto drive B.

SYSGEN then examines the source and destination to determine whether the operation can be performed safely.

If the destination is suitable, SYSGEN displays the installation details and requests confirmation before writing.

Press Ctrl-C at the destination prompt to exit without modifying any disk.

### Installing from Another System Disk

To specify both drives directly, use:

```text
SYSGEN source: destination:
```

For example:

```text
A>SYSGEN A: B:
```

This reads the installed BetterCP/M system from drive A and installs it onto drive B.

Another example is:

```text
A>SYSGEN C: D:
```

This installs the system from drive C onto drive D.

The source and destination must refer to different physical drives.

Using different logical drive letters is not sufficient if both letters refer to the same physical device.

SYSGEN checks the physical assignments and refuses an installation that would use the same physical drive as both source and destination.

### Installing from SYSTEM.SYS

SYSGEN can also install BetterCP/M from a system-image package.

For example:

```text
A>SYSGEN SYSTEM.SYS B:
```

This reads `SYSTEM.SYS` from the current drive and user area and installs its operating-system image onto drive B.

A drive-qualified package name can also be used:

```text
A>SYSGEN C:SYSTEM.SYS B:
```

This reads the package from drive C.

The package filename need not be `SYSTEM.SYS`. Any valid, explicitly specified CP/M 8.3 filename can be used.

For example:

```text
A>SYSGEN B:BASE090.SYS C:
```

This installs the saved system image contained in `BASE090.SYS` onto drive C.

Package filenames do not support wildcard specifications, compound drive/user selectors, or explicit user-area qualifications.

An unqualified package name refers to the current drive and user area.

### System-Image Packages

A BetterCP/M system-image package contains the operating-system image together with information needed to identify and install it correctly.

The standard package is named:

```text
SYSTEM.SYS
```

A valid BetterCP/M 1.0 package contains a header followed by the operating-system image.

SYSGEN checks the package before installation.

It verifies that the expected header and system-image structure are present, that the complete package can be read, and that the image is suitable for the destination.

If the package is invalid or incompatible, SYSGEN refuses the operation before writing to the destination.

A structurally valid package is not necessarily free from every possible form of corruption. Use system images obtained from a trusted source.

### Preparing the Destination Disk

Before using SYSGEN, the destination disk must already have a suitable format.

SYSGEN does not format disks.

If the disk needs to be formatted, use CONFIG to establish the appropriate disk-format assignment and DUP to perform the formatting.

For example:

```text
A>CONFIG
A>DUP /FORMAT B:
A>SYSGEN SYSTEM.SYS B:
```

This illustrates the general preparation sequence.

The correct format depends on the computer and the system image being installed.

The destination must provide a compatible bootstrap arrangement and sufficient reserved space for BetterCP/M.

### Compatible Disk Formats

SYSGEN does not require the source and destination disks to have identical filesystem capacities.

For example, it may be possible to install BetterCP/M onto a disk with a larger filesystem than the source, provided the destination has compatible bootstrap geometry and sufficient reserved system space.

BetterCP/M 1.0 requires at least 160 reserved 128-byte logical records for the installed system.

This corresponds to 20,480 bytes of reserved system space.

A destination may have more reserved space, but SYSGEN writes only the required system records.

If the reserved area is too small, SYSGEN reports:

```text
Destination reserved system area is too small (160 records required).
```

If the destination's bootstrap geometry is incompatible, SYSGEN refuses the installation.

It does not attempt to convert the disk into a different format.

### Protected System Drive

BetterCP/M protects physical drive 0 against SYSGEN destination writes.

This protection follows the physical drive, regardless of its logical drive letter.

For example, assigning physical drive 0 to another logical letter does not make it an acceptable SYSGEN destination.

If the requested destination resolves to physical drive 0, SYSGEN reports:

```text
Physical drive 0 is protected as the running system disk.
```

This safeguard helps prevent accidental replacement of the operating system from which the computer is currently running.

### Confirming Installation

Before writing to the destination, SYSGEN displays the installation information and requests confirmation.

The warning includes:

```text
The destination system area will be replaced.
Files outside the reserved system tracks will be preserved.
Proceed (Y/N)?
```

Only `Y` begins installation.

Any other response cancels the operation without modifying the destination.

The confirmation is required whether SYSGEN was started interactively or with command-line arguments.

BetterCP/M 1.0 does not provide an option for bypassing this confirmation.

### Preserving Existing Files

SYSGEN replaces the operating system in the reserved system area.

It does not erase or rewrite ordinary filesystem records.

This means that a compatible disk containing existing files can receive a new BetterCP/M system without necessarily losing those files.

For example, a disk containing application programs and data files may be suitable for system installation if it has the required reserved system area.

SYSGEN preserves records outside the system area it installs.

However, this protection does not mean that every disk is suitable.

A disk with no compatible system area, or with insufficient reserved space, cannot be made bootable merely by running SYSGEN.

### Installation and Verification

SYSGEN reads the complete source image before beginning destination writes.

It also prepares the image for the destination's configuration.

During installation, SYSGEN writes the system records and verifies each one by reading it back and comparing the data.

The boot record is written last.

When the operation completes successfully, SYSGEN reports:

```text
System installed and verified. The destination is bootable.
```

This indicates that the operating-system image was installed and verified.

It does not mean that the disk contains every utility or supporting file required for your preferred working environment.

Those files must be copied separately.

For example, a complete system disk may also require the appropriate command utilities, resident extensions, and `STARTUP.SUB`.

### Saving an Installed System to a Package

SYSGEN can also read the operating system from a disk and save it as a `SYSTEM.SYS` package.

This is useful for preserving a working configuration, maintaining several system versions, or preparing an image for installation onto another compatible disk.

To save the installed system from drive A:

```text
A>SYSGEN A:
```

SYSGEN reads the system area from drive A and creates `SYSTEM.SYS` in the current drive and user area.

You can specify another filename and destination drive:

```text
A>SYSGEN A: B:BASE090.SYS
```

This saves the installed system from drive A as `BASE090.SYS` on drive B.

The resulting package can later be installed using:

```text
A>SYSGEN B:BASE090.SYS C:
```

### What a Saved Package Contains

A saved system package includes the installed BetterCP/M operating system and its saved configuration information.

This includes the saved startup command, cold-boot IOBYTE, and saved drive configuration.

It does not include unsaved changes made only to the running system.

It also does not include ordinary files from the source disk.

For example, changes made to `STARTUP.SUB` are not captured in the system-image package because that file resides in the ordinary filesystem.

To preserve both the operating system and its supporting files, use a complete disk backup.

### Replacing an Existing Package

If the requested output filename already exists, SYSGEN asks:

```text
Replace existing package (Y/N)?
```

Only `Y` permits replacement.

Read-only and system files are protected against replacement.

SYSGEN verifies the package before reporting successful export.

A successful operation displays:

```text
Package exported and verified.
```

### Interrupted Package Export

SYSGEN takes precautions to avoid replacing an existing package with an incomplete one.

It first writes the new package to a temporary file, verifies it, and then publishes it under the requested filename.

During replacement, it may use the temporary filenames:

```text
SYSGEN.$$$
SYSGEN.BAK
```

These names are reserved for recovery.

If a package export fails, one or both files may remain.

**Do not delete these files without first examining the failed operation.** They may contain a recoverable package or the previous version of the file.

SYSGEN reports publication failures and identifies the files that should be inspected.

The export procedure reduces the risk of losing an existing package, but it cannot guarantee recovery from every possible disk or power failure.

### Interrupting Installation

SYSGEN recognizes Ctrl-C during installation.

At the interactive destination prompt, Ctrl-C exits without modifying the disk.

During installation, Ctrl-C is checked between disk operations.

An operation already in progress may finish before the interruption takes effect.

If installation is interrupted after writing has begun, the destination system area may be incomplete.

The disk may no longer boot.

SYSGEN does not automatically restore the previous operating system after a partial installation.

Correct the cause of the interruption and repeat installation from a valid source.

### Installation Errors

SYSGEN reports errors encountered while reading the source, validating the destination, writing system records, or verifying the installed image.

Common causes include incompatible disk formats, insufficient reserved system space, unavailable drives, write protection, and read or write failures.

#### Invalid System Package

If a system-image package is invalid or cannot be installed on the selected destination, SYSGEN may report:

```text
The system package is invalid or cannot represent the destination.
```

Check that the package is a valid BetterCP/M system image and that it is compatible with the destination.

#### Incompatible Bootstrap Geometry

If the destination's bootstrap geometry is unsuitable, SYSGEN reports:

```text
Destination bootstrap geometry is not supported by this system package.
```

Use CONFIG to examine the destination's format assignment.

SYSGEN cannot convert an incompatible disk format into a bootable one.

#### Insufficient Reserved Space

If the destination does not provide enough reserved system space, SYSGEN reports:

```text
Destination reserved system area is too small (160 records required).
```

A disk with insufficient reserved space cannot accept the BetterCP/M 1.0 system image.

#### Read and Write Failures

If a source read fails, SYSGEN stops before beginning destination installation.

If a destination write or verification fails after installation has begun, the destination may contain an incomplete system.

Do not assume that such a disk is bootable.

### Memory Requirements

Saving an installed system to a package requires at least 36K of available transient program memory.

If resident extensions have reduced the available TPA below this requirement, SYSGEN refuses the export operation.

Unload unnecessary extensions before retrying.

### Version Information

To display SYSGEN's version and build identification:

```text
A>SYSGEN /VER
```

The utility displays its identification and returns to the command prompt without performing an installation or export.

### Examples

Start interactive installation:

```text
A>SYSGEN
```

Install from drive A onto drive B:

```text
A>SYSGEN A: B:
```

Install from a system-image package:

```text
A>SYSGEN SYSTEM.SYS B:
```

Install from a package on another drive:

```text
A>SYSGEN C:SYSTEM.SYS B:
```

Save the installed system from drive A:

```text
A>SYSGEN A:
```

Save the installed system under a specified filename:

```text
A>SYSGEN A: B:BASE090.SYS
```

Restore a saved system image:

```text
A>SYSGEN B:BASE090.SYS C:
```

Display version information:

```text
A>SYSGEN /VER
```

### SYSGEN, DUP, and SYSBUILD

BetterCP/M provides three utilities with related but distinct purposes.

| Utility | Purpose |
|---|---|
| **DUP** | Format disks, copy entire disks, and check physical readability |
| **SYSGEN** | Install BetterCP/M onto prepared media or save an installed system image |
| **SYSBUILD** | Construct a system-image package from operating-system build products |

For ordinary system maintenance, DUP and SYSGEN provide the facilities needed to prepare and install BetterCP/M disks.

SYSBUILD is primarily intended for developers and system builders preparing new operating-system images.

For an introduction to disk preparation, installation, and backup procedures, see Chapter 10, *Working with Disks*.

---

# Chapter 17 — Batch and Extension Commands

BetterCP/M provides facilities for automating command sequences and extending the operating environment without rebuilding the operating system.

Two utilities, **SUBMIT** and **XSUB**, provide batch processing. SUBMIT executes commands stored in a text file, while XSUB allows compatible programs to receive input from a batch file instead of the keyboard.

Two additional utilities, **CPX** and **RSX**, manage resident extensions. CPXs add commands to the command processor, while RSXs provide services that remain available while other programs execute.

This chapter covers four utilities:

| Utility | Purpose |
|---|---|
| SUBMIT | Execute commands from a batch file |
| XSUB | Supply batch-file input to compatible programs |
| CPX | Manage Command Processor Extensions |
| RSX | Manage Resident System Extensions |

Chapter 6 introduced batch processing, and Chapter 8 explained resident extensions. This chapter provides the corresponding command references.

## 17.1 SUBMIT — Batch Command Processing

**Purpose:** Executes a sequence of commands stored in a text file.

SUBMIT allows frequently used command sequences to be saved and executed without entering each command individually.

It retains the familiar CP/M batch-processing conventions, including `.SUB` files and positional parameter substitution.

### Syntax

```text
SUBMIT filename [parameters]
```

The filename identifies a SUBMIT command file. The `.SUB` extension is normally omitted when invoking the utility.

For example:

```text
A>SUBMIT BACKUP
```

executes the commands contained in `BACKUP.SUB`.

### Creating a SUBMIT File

A SUBMIT file is an ordinary text file containing commands.

Each command appears on a separate line.

For example, a file named `BACKUP.SUB` might contain:

```text
DIR *.ASM
COPY *.ASM B:
DIR B:*.ASM
```

To execute it:

```text
A>SUBMIT BACKUP
```

SUBMIT arranges for the commands to be executed in sequence.

The commands are interpreted by the normal BetterCP/M command environment.

Consequently, a SUBMIT file can contain resident commands, transient programs, and commands provided by installed CPXs.

### Parameters

SUBMIT files can accept parameters supplied when the file is invoked.

Parameters are referenced using a dollar sign followed by a number.

For example, suppose `BUILD.SUB` contains:

```text
ASM $1
LOAD $1
$1
```

Enter:

```text
A>SUBMIT BUILD TEST
```

SUBMIT substitutes `TEST` for `$1`, producing the equivalent of:

```text
ASM TEST
LOAD TEST
TEST
```

This allows the same command file to be used with different programs.

### Multiple Parameters

A SUBMIT file can refer to several parameters.

For example, `COPYFILE.SUB` might contain:

```text
COPY $1 $2
```

You could invoke it with:

```text
A>SUBMIT COPYFILE REPORT.TXT B:REPORT.TXT
```

The resulting command would be:

```text
COPY REPORT.TXT B:REPORT.TXT
```

Parameter substitution is textual. SUBMIT does not interpret filenames or options while performing the substitution.

The resulting command is interpreted by the command processor or utility that executes it.

### Command Execution

SUBMIT commands execute in the normal BetterCP/M command environment.

A command may load a transient program, invoke a resident command, or use an installed extension.

Ordinary warm boots preserve the batch-processing mechanisms needed to continue supported SUBMIT operations.

A cold boot establishes a new operating session rather than continuing a previous batch.

### Interactive Commands

A command executed from a SUBMIT file does not automatically become noninteractive.

For example, COPY may ask whether an existing destination file should be replaced.

If the batch is intended to run unattended, use the command's supported options to specify the desired behavior.

For example:

```text
COPY B1:*.DAT C3: /B /O
```

uses COPY's batch option and requests replacement of existing writable destination files.

The `/B` option belongs to COPY. It does not change SUBMIT's behavior or make other commands noninteractive.

### Errors and Interruptions

Errors during batch execution may interrupt the procedure or affect subsequent commands.

The exact behavior depends on the command and the error encountered.

A failed command does not necessarily undo earlier successful operations.

For example, if a batch copies several files and encounters an error partway through, some destination files may already have been created.

Before restarting an interrupted batch, examine the results to determine which operations have completed.

### Startup Files

BetterCP/M uses SUBMIT for its standard startup procedure.

The default cold-start command is:

```text
SUBMIT STARTUP
```

This executes `STARTUP.SUB`.

The supplied startup file displays the BetterCP/M identification banner and can be customized to perform additional operations.

For example, it may load resident extensions needed for a preferred working environment.

The startup command is executed during a cold boot, not during an ordinary warm boot.

For information about configuring startup behavior, see Chapter 7.

### Examples

Execute a command file:

```text
A>SUBMIT BACKUP
```

Execute a command file with one parameter:

```text
A>SUBMIT BUILD TEST
```

Execute a command file with two parameters:

```text
A>SUBMIT COPYFILE REPORT.TXT B:REPORT.TXT
```

For an introduction to batch processing, see Chapter 6.

---

## 17.2 XSUB — Extended Batch Input

**Purpose:** Allows compatible programs to receive input from a SUBMIT file through the CP/M buffered console-input interface.

Ordinary SUBMIT processing supplies commands to the command processor.

Some programs, however, request additional input after they have started.

For example, an editor or utility might ask for a filename or an option.

XSUB extends batch processing by allowing submitted input to be supplied to such programs.

### How XSUB Works

XSUB provides a resident input facility that cooperates with SUBMIT.

When a compatible program requests buffered console input, XSUB can supply the next submitted input line.

This allows certain interactive procedures to be automated.

For example, a program that normally asks:

```text
Source file:
Destination file:
```

may be able to receive those responses from the batch file.

XSUB does not automatically support every interactive program.

Programs that read the keyboard directly, use private input routines, or bypass the supported BDOS console-input interface may still require ordinary keyboard input.

### Using XSUB

XSUB is normally activated as part of a SUBMIT procedure.

The batch file can then supply input to compatible programs.

The supported invocation and placement of XSUB depend on the batch-processing arrangement.

Unlike an ordinary transient utility, XSUB provides resident support that can remain available while another program executes.

### Returning to Keyboard Input

When the submitted input has been exhausted, XSUB allows the program to continue receiving input from the keyboard.

For example, a program may receive its initial responses automatically and then continue interactively.

This is useful when only the repetitive portion of an operation needs to be automated.

A malformed or unusable submitted-input queue is discarded before returning to ordinary console input.

### Resident BATCHIO Support

BetterCP/M's XSUB facility uses a resident component named `BATCHIO`.

This component may remain installed after the batch has finished.

Under the supported warm-boot conditions, an idle BATCHIO provider can retire automatically.

However, some program-termination paths may leave it resident.

You can examine installed RSXs with:

```text
A>RSX LIST
```

To remove BATCHIO explicitly:

```text
A>RSX UNLOAD BATCHIO
```

This releases its resident memory when it is no longer needed.

### Memory Considerations

Like other resident extensions, BATCHIO occupies memory that would otherwise be available to transient programs.

Unloading it when no longer needed can restore available program memory.

The exact amount recovered depends on the other resident extensions installed.

### Limitations

XSUB is intended for programs that use compatible buffered console-input services.

It is not a general keyboard-recording or keyboard-simulation utility.

It does not guarantee automation of programs that communicate directly with keyboard hardware or use unsupported input methods.

For ordinary command sequences that do not require input to running programs, SUBMIT alone is sufficient.

For an introduction to XSUB and batch processing, see Chapter 6.

---

## 17.3 CPX — Command Processor Extension Manager

**Purpose:** Displays, loads, and unloads Command Processor Extensions.

A Command Processor Extension, or CPX, adds commands to BetterCP/M's command environment.

Unlike an ordinary transient program, a CPX remains available after individual commands have finished. This allows frequently used commands to be provided without loading a separate `.COM` file each time.

The standard BetterCP/M command environment includes `RCP.CPX`, which supplies familiar commands such as DIR, ERA, REN, TYPE, COPY, and MOVE.

The CPX manager allows additional command packages to be installed or removed.

### Command Forms

The principal CPX management commands are:

```text
CPX LIST
CPX LOAD name
CPX UNLOAD name
```

The `name` argument identifies the extension to be managed.

For example:

```text
A>CPX LOAD TOOLS
```

requests the command package `TOOLS.CPX`.

### Listing CPXs

To examine the configured command processor extensions, enter:

```text
A>CPX LIST
```

BetterCP/M displays information about the configured CPX packages.

This is useful when determining which command packages are available or investigating a missing resident command.

An important distinction is that **a configured CPX is not necessarily a successfully loaded CPX**.

BetterCP/M may retain an extension's configured entry even when the corresponding file cannot be loaded.

Consequently, the presence of a name in `CPX LIST` does not by itself establish that its commands are available.

### Loading a CPX

To load an additional command package, enter:

```text
CPX LOAD name
```

For example:

```text
A>CPX LOAD TOOLS
```

BetterCP/M attempts to load the specified extension.

The extension must be available in the expected location and compatible with the running BetterCP/M system.

If loading succeeds, the commands supplied by the extension become available through the normal command environment.

For example, if `TOOLS.CPX` provides a command named `TOOLS`, that command can be invoked directly:

```text
A>TOOLS
```

The actual commands provided depend on the extension.

### Loading Several CPXs

BetterCP/M can maintain more than one CPX.

The command environment considers installed extensions in a defined order when resolving resident command names.

This matters when two extensions provide commands with the same name.

In ordinary use, you need not be concerned with the extension order unless a command name is duplicated.

For example, installing another CPX that provides DIR may affect which resident DIR implementation is selected.

If you need to execute a particular transient utility regardless of the resident command environment, use BetterCP/M's explicit transient-execution prefix:

```text
A>:DIR
```

This bypasses resident command lookup.

For more information about command search and execution, see Chapter 5.

### Unloading a CPX

To remove an optional command package, enter:

```text
CPX UNLOAD name
```

For example:

```text
A>CPX UNLOAD TOOLS
```

After the extension has been removed, its commands are no longer available as resident commands.

Corresponding transient programs, if present, remain available through the ordinary program-search mechanism.

Unloading a CPX can be useful when you no longer need its commands or want to change the resident command environment.

### Required Command Components

Not every command component is necessarily optional.

Some components are required for normal BetterCP/M operation.

The extension-management facilities enforce the applicable restrictions.

If an extension cannot be unloaded, examine the reported error rather than attempting to bypass the restriction.

### Recovering from an Unusable CPX

If an optional CPX file fails validation, BetterCP/M may display:

```text
CPX?
```

The operating system continues to the command prompt with its remaining usable extensions.

Commands supplied by the rejected CPX are unavailable.

The rejected extension may nevertheless remain in the configured profile.

For example:

```text
A>CPX LIST
```

may still show the extension.

To remove an unusable optional CPX, enter:

```text
A>CPX UNLOAD BAD
```

where `BAD` is the name of the affected extension.

Alternatively, replace the damaged file with a valid copy.

Until the problem is corrected, the warning may recur when BetterCP/M restores the command environment.

A missing optional CPX file may simply be skipped without producing the same warning.

### CPXs and Available Memory

Command Processor Extensions occupy memory while installed.

This memory is unavailable to ordinary transient programs.

Loading additional command packages therefore involves a tradeoff between convenience and available program memory.

For frequently used commands, keeping a CPX installed may be worthwhile.

For commands used only occasionally, a transient utility may be more appropriate.

### CPX Examples

List configured command extensions:

```text
A>CPX LIST
```

Load an optional extension:

```text
A>CPX LOAD TOOLS
```

Unload an optional extension:

```text
A>CPX UNLOAD TOOLS
```

Request a transient utility rather than a resident command:

```text
A>:DIR /WHEREIS ED.COM
```

For an introduction to CPXs and their relationship to the command environment, see Chapter 8, *Resident Extensions*.

---

## 17.4 RSX — Resident System Extension Management

**Purpose:** Lists, loads, and unloads Resident System Extensions (RSXs).

Resident System Extensions provide services that remain available while other programs execute. Unlike Command Processor Extensions, which add commands to the command environment, RSXs extend the services available to applications and the operating system.

BetterCP/M uses RSXs for several purposes, including terminal emulation, clock support, batch input, and other optional system facilities.

The RSX utility allows you to manage these extensions without rebuilding the operating system.

### Syntax

The principal command forms are:

```text
RSX LIST
RSX LOAD name
RSX UNLOAD name
```

The `name` argument identifies the extension to be loaded or unloaded. The `.RSX` extension is normally omitted.

For example:

```text
A>RSX LOAD ADM3A
```

loads the ADM-3A terminal personality from `ADM3A.RSX`.

### Listing Installed RSXs

To display the currently installed Resident System Extensions, enter:

```text
A>RSX LIST
```

BetterCP/M displays the installed extensions.

This is useful when determining which system services are available, checking whether a particular extension is loaded, or investigating memory usage.

For example, you might use RSX LIST to determine whether a terminal personality or clock provider is installed before running an application that requires it.

### Loading an RSX

To load an extension, enter:

```text
RSX LOAD name
```

For example:

```text
A>RSX LOAD FREHDCLK
```

loads the FreHD clock provider.

Once successfully loaded, the provider makes its supported clock services available to programs using BetterCP/M's clock interface.

Another example is:

```text
A>RSX LOAD VT52
```

which loads the VT52 terminal personality.

Some extensions require other resident components to be loaded first.

The extension's documentation identifies these requirements.

### Extension Dependencies

Some RSXs depend on services provided by other extensions.

BetterCP/M's terminal-monitor system provides a common example.

A terminal personality interprets the control sequences used by an application, while a screen backend communicates with the actual display environment.

The backend must be loaded before the terminal personality.

For example, on a TRS-80 Model 4:

```text
A>RSX LOAD M4SCRN
A>RSX LOAD ADM3A
```

The first command loads the Model 4 screen backend.

The second loads the ADM-3A terminal personality.

On a system using the ANSI screen backend, the corresponding commands are:

```text
A>RSX LOAD ANSISCRN
A>RSX LOAD ADM3A
```

These commands establish the supported ADM-3A display environment using the appropriate backend.

### Unloading an RSX

To remove an installed extension, enter:

```text
RSX UNLOAD name
```

For example:

```text
A>RSX UNLOAD ADM3A
```

removes the ADM-3A terminal personality.

Once the extension has been removed, its services are no longer available.

Unloading an extension also releases the memory occupied by that extension when the resident manager can reclaim it.

### Unloading Dependent Extensions

When several extensions depend on one another, remove them in the reverse order from which they were loaded.

For example:

```text
A>RSX UNLOAD ADM3A
A>RSX UNLOAD M4SCRN
```

This removes the terminal personality before removing its supporting screen backend.

Attempting to remove a supporting extension while another component still requires it may be rejected.

If RSX reports that an extension cannot be unloaded, examine the installed extensions and their dependencies before trying again.

### Changing Terminal Personalities

Only one terminal personality can be active at a time.

To change from ADM-3A to VT52 while retaining the same screen backend:

```text
A>RSX UNLOAD ADM3A
A>RSX LOAD VT52
```

The screen backend need not be reloaded if it remains installed and supports the new personality.

To verify the new environment, run the corresponding terminal test utility:

```text
A>VT52TST
```

For further information about terminal personalities, see Chapter 9, *Terminal Support*.

### Clock Providers

BetterCP/M provides loadable clock providers through the RSX system.

For example, on a TRS-80 Model 4 with FreHD:

```text
A>RSX LOAD FREHDCLK
A>TIME
```

Under z80pack:

```text
A>RSX LOAD ZPRTC
A>TIME
```

These providers allow TIME and compatible applications to obtain the current date and time.

Both providers supplied with BetterCP/M 1.0 are read-only.

You can identify the active provider with:

```text
A>TIME /PROVIDER
```

For more information, see Chapter 11, *Date and Time*, and Section 16.3, *TIME*.

### P2DOS Clock Compatibility

BetterCP/M provides a separate RSX for compatibility with the P2DOS date-and-time interface.

For example:

```text
A>RSX LOAD ZPRTC
A>RSX LOAD P2DOS
```

The first command loads the native clock provider.

The second installs the P2DOS-compatible interface.

The P2DOS extension uses BetterCP/M's native clock service rather than communicating directly with the underlying clock hardware.

Consequently, its capabilities depend on the installed provider.

With the standard read-only providers, clock-setting requests are not supported.

### Batch Input Support

BetterCP/M's XSUB facility uses a resident extension named `BATCHIO`.

This extension allows compatible programs to receive submitted input through the CP/M buffered console-input interface.

BATCHIO may remain resident after the batch procedure has finished.

To check whether it is installed:

```text
A>RSX LIST
```

To remove it explicitly:

```text
A>RSX UNLOAD BATCHIO
```

This releases the resident batch-input facility when it is no longer needed.

For additional information, see Section 17.2, *XSUB*.

### RSXs and Program Memory

Resident System Extensions occupy memory that would otherwise be available to transient programs.

Loading an extension can therefore reduce the available Transient Program Area (TPA).

For example, a terminal monitor may be useful while running a full-screen editor but unnecessary when running an ordinary command-line utility.

If a program reports insufficient memory, examine the installed RSXs:

```text
A>RSX LIST
```

You may be able to unload extensions that are no longer needed.

Some utilities have substantial memory requirements. DUP, for example, requires approximately 51K of available transient memory.

Unloading unnecessary extensions may provide sufficient space for such programs.

### Warm Boots and Extension Persistence

BetterCP/M preserves supported resident extensions across ordinary warm boots.

For example, suppose you load a terminal monitor:

```text
A>RSX LOAD M4SCRN
A>RSX LOAD VT52
```

You can then run a compatible full-screen application.

When the application terminates and control returns to the command processor, the terminal monitor remains available.

There is ordinarily no need to reload it after every program.

A cold boot establishes a new operating session.

If you want particular extensions loaded automatically whenever BetterCP/M starts, add the appropriate commands to `STARTUP.SUB`.

For example:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
CLS
```

The startup file is executed during a cold boot when the standard startup command is configured.

For more information, see Chapter 7, *Configuring BetterCP/M*.

### Extension Errors

An RSX may fail to load because its file is missing, damaged, incompatible, or unsuitable for the current system.

A load may also fail because the required supporting services are unavailable.

If an extension fails to load, check that its file is present and that any required supporting extensions have already been installed.

For example, a terminal personality requires a suitable screen backend.

If an extension cannot be unloaded, another resident component may still depend on it.

Remove the dependent extension first.

### Recovering from Extension Problems

If an RSX causes problems, begin by examining the installed extensions:

```text
A>RSX LIST
```

If the affected extension can be safely removed, unload it.

For example:

```text
A>RSX UNLOAD VT52
```

If the problem began after adding an extension to `STARTUP.SUB`, remove the corresponding startup command and test the extension manually.

A cold boot can restore the configured startup environment, but it will also execute the configured startup procedure again.

If that procedure contains an unsuitable extension-loading command, the problem may recur until the startup file is corrected.

### Examples

List installed RSXs:

```text
A>RSX LIST
```

Load a terminal screen backend:

```text
A>RSX LOAD M4SCRN
```

Load an ADM-3A terminal personality:

```text
A>RSX LOAD ADM3A
```

Change to VT52:

```text
A>RSX UNLOAD ADM3A
A>RSX LOAD VT52
```

Load the FreHD clock provider:

```text
A>RSX LOAD FREHDCLK
```

Load z80pack clock support:

```text
A>RSX LOAD ZPRTC
```

Load P2DOS-compatible clock services:

```text
A>RSX LOAD P2DOS
```

Remove the batch-input extension:

```text
A>RSX UNLOAD BATCHIO
```

Unload a terminal monitor:

```text
A>RSX UNLOAD VT52
A>RSX UNLOAD M4SCRN
```

For an introduction to resident extensions and their use, see Chapter 8, *Resident Extensions*.

For detailed information about developing RSXs, consult the *BetterCP/M Developer's Guide*.

---

