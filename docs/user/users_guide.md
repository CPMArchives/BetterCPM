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
