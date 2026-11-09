# Named directories (BetterCP/M 1.2 development)

Named directories give familiar names to drive/user locations. Load the
provider, then create up to 32 names of at most eight letters/digits:

```text
RSX LOAD NDR
NDR COMMANDS A0:
NDR ROOT A0:
NDR UTILS B0:
NDR SOURCE C2:
NDR
```

With no operands, NDR lists the live assignments and reports how many of the
32 entries are in use, including an explicit zero count for an empty table.
Entries fill down each column, eight per column, using up to four columns.
Each entry has a 13-character field followed by a four-space gap to the next
column; the maximum display width is 64 characters. Deleted slots are skipped.

Names ignore case. Numeric directory spellings such as `A`, `B2` and `31` are
reserved. Names are aliases; they do not create filesystem directories or
protect files. If several names refer to the current location, the first live
entry supplies the prompt name:

```text
A0 [COMMANDS]> NDR
```

Use a colon to navigate or qualify a command/file operand:

```text
SOURCE:
DIR UTILS:*.COM
COPY SOURCE:HELLO.MAC=ROOT:HELLO.MAC
UTILS:MYTOOL
PATH $$ ROOT: B2: UTILS: C0:
```

The COPY example uses its existing `destination=source` syntax. CCP translates
named prefixes into numeric DU prefixes before dispatch. Double-quoted text
remains literal. PATH stores the resolved numeric locations immediately; later
name changes do not alter the saved live PATH list. Numeric PATH works without
NDR. Compound/bracket selectors continue to use numeric DU syntax.

Bare `PATH` displays the configured entries with current NDR annotations:

```text
PATH: $$: | A0:[ROOT] | B3: | C$: | B0:[UTILS]
```

Fixed DUs show the first matching live name, or just their numeric spelling
when unnamed or NDR is unloaded. Symbolic entries retain their spelling.
Name changes update annotations without changing the stored search locations.
Long lists wrap between complete entries, with continuation entries aligned
under the first. TCAP supplies the display width when known; otherwise PATH
uses 80 columns.

Manage names with:

```text
NDR /DEL SOURCE
NDR SOURCE D3:
NDR /SAVE MYNAMES
NDR /CLEAR
NDR /LOAD MYNAMES
NDR /LOAD B3:MYNAMES.NDR
NDR /HELP
NDR /VER
```

Delete an existing name before assigning it again. Save defaults the extension
to `.NDR` and refuses to overwrite an existing file; use another filename or
erase the old file first. Invalid sets do not change the current names.

To make the current names the startup defaults in a particular provider file:

```text
NDR /DEFAULT A0:NDR.RSX
```

A target filename is required; its extension defaults to `.RSX`. The file must
already exist and contain a supported, writable NDR provider. `/DEFAULT` embeds
the live set into that carrier, including an empty set after `/CLEAR`. It leaves
the live table unchanged. On the next fresh load of that file, the embedded
names are immediately available; ordinary warm boots retain the current live
names. You can repeat `/DEFAULT` to replace previously embedded defaults.
The shipped carrier starts with no names.

`/SAVE` still creates an interchangeable `.NDR` set; `/DEFAULT` updates an
existing `.RSX` carrier. To restore embedded defaults after cold boot, only
`RSX LOAD NDR` is needed in startup. An explicit `/LOAD` after it can select
a different saved set.

The replacement is staged and read back before the original is renamed. Files
with the same stem and suffix `.$ND` (staging) or `.$NB` (original backup) block
the operation rather than being overwritten. Normal success removes both.
If an interruption leaves these files, inspect them before retrying: `.$NB`
holds the original carrier, and `.$ND` holds the proposed replacement. When
restoring an absent original filename, rename the backup to its original `.RSX`
name. Returning errors attempt rollback and report retained recovery files.

Names survive warm boots while NDR remains loaded. Unloading discards the live
table and frees its allocation:

```text
RSX UNLOAD NDR
```

Save a set or embed defaults before unloading if you want to restore the names.
For restoration from a separate set, put `RSX LOAD NDR` and `NDR /LOAD MYNAMES`
in your startup sequence after the needed disk is available. The supplied provider uses 512 protected bytes; CCP
growth is reclaimable. The existing shared RSX manager adds 1 KiB when the first
RSX is loaded, shared by all active providers.
