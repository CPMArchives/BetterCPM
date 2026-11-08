BETTERCP/M - SYSTEM DISK
=======================

Welcome to BetterCP/M, a CP/M-compatible operating system for Z80
computers. It keeps the familiar CP/M 2.2 programming model while adding
shared file-selection syntax, loadable extensions and modern build tools.

This is the BetterCP/M 1.1 System Disk.
See the accompanying release notes for changes and known limitations.
Targets: patched cpmsim, TRS-80 Model 4 and 64K Model II under trs80gp.
Model II uses BCM2SS single-sided IMDs; physical hardware is unverified.

GETTING STARTED

  DIR                 List files in the current drive and user area.
  TYPE README.TXT     Display this introduction.
  TYPE README.TXT /P  Read with simple resident paging.
  :DIR /C=2           Run DIR.COM with a two-column display.
  STAT                Inspect disk status.
  ED NOTES.TXT        Edit one text file with the CP/M context editor.
  CPX LIST            List installed command packages.
  RSX LIST            List loaded resident extensions.

At resident TYPE's page prompt, Space or period continues; Ctrl-C cancels.
For TYPE.COM's bidirectional pager, use :TYPE README.TXT /P. Space, period
or Ctrl-C advances; comma or Ctrl-R goes back; Ctrl-Q quits. The final
page remains available for backward navigation until you quit.

DRIVES, USERS AND FILE SELECTION

The prompt A0> means drive A, user area 0. User areas range from 0 to 31.
Enter B3: to change to drive B, user 3. A filespec may specify another
location without changing your prompt's location:

  DIR B3:*.COM
  DIR B[1,3,5-7]:*.TXT
  DIR B[-]:*.DOC[$RW]

[-] selects every user area on that drive. Attribute expressions such as
[$RW] select matching files. In a filename field, ? matches one position
and * matches the remaining positions; nothing except more stars may
follow a star in the same field. Name and extension are separate fields.

RESIDENT AND TRANSIENT COMMANDS

RCP.CPX supplies resident commands. Their .COM counterparts provide
richer options. Prefix a command with : or . to run its .COM version
explicitly. Automatic handoff is not yet implemented on this disk.
Use /VER for a command's version and build, for example DIR /VER or
:DIR /VER. Command and operating-system versions are independent.

COPY, REN and ERA change files. Read the user guide before using their
advanced options, especially ERA's destructive erase. Keep a backup of
important data and work from copies of emulator disk images.

SYSTEM FILES AND EMULATOR NOTES

Keep RCP.CPX, R3PACK.RSX and the system utilities with this System Disk.
R3PACK.RSX is an internal RSX-manager dependency; do not load it manually.
Clock providers are optional: ZPRTC.RSX for cpmsim, FREHDCLK.RSX for Model 4
with FreHD support. TIME needs a suitable loaded clock provider.

In cpmsim, BYE exits the simulator. BYE.COM is not a Model 4 utility.
On Model 4/trs80gp, Physical Keyboard Layout currently provides [ and ]
with Ctrl-8 and Ctrl-9. Physical punctuation follows the Model 4 keyboard.

DOCUMENTATION AND SOURCE

The repository contains the user guide, engineering specifications,
build instructions and the distribution manifest:

  https://github.com/CPMArchives/BetterCPM

The user guide is docs/manuals/Users-Guide.md. Packaging notes are under
docs/releases/. PIP and ED are included on the System Disk. Search for files
with :DIR /WHEREIS filespec. TED is on the Utilities Disk; HELP is not shipped.

NUMERIC PATH AND TCAP 2.0

PATH shows up to six numeric drive/user search locations. The default
is . A0: ; A0:PATH /DEFAULT restores it. Use PATH /HELP for syntax.

RSX LOAD ADM3A (or VT52 or ANSI) selects an integrated TCAP 2.0
personality/renderer. No separate screen backend is required for these
modules. Unload the active personality before selecting another.
Standalone screen backends remain for separate SCRN/SCX clients.
TYPE and TED have not been migrated to the TCAP 2.0 API.

Unloaded COM limits: cpmsim and Model II 57344 bytes; Model 4 54272.
Optional RSXs consume TPA while loaded. Complete unload restores it.
