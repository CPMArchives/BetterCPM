BETTERCP/M - SYSTEM DISK
=======================

Welcome to BetterCP/M, a CP/M-compatible operating system for Z80
computers. It keeps the familiar CP/M 2.2 programming model while adding
shared file-selection syntax, loadable extensions and modern build tools.

This is a development System Disk for the forthcoming 1.0 release.
Utility completion and final release qualification are still in progress.
The current targets are z80pack/cpmsim and the TRS-80 Model 4/trs80gp.

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

The user guide is docs/user/users_guide.md. Packaging notes are under
docs/releases/. PIP and ED are included on the System Disk. Search for files
with :DIR /WHEREIS filespec. A full-screen editor is planned for the Utilities
Disk; it is not part of this System Disk.
