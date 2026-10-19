# BetterCP/M 1.0 User's Guide

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

The CONFIG and SYSGEN command references provide complete instructions for saving and restoring system configurations.

---

