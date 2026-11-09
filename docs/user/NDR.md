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

Names ignore case. Numeric directory spellings such as `A`, `B2` and `31` are
reserved. Names are aliases; they do not create filesystem directories or
protect files. If several names refer to the current location, the first live
entry supplies the prompt name:

```text
A0 [COMMANDS] >
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

Names survive warm boots while NDR remains loaded. Unloading discards the live
table and frees its allocation:

```text
RSX UNLOAD NDR
```

Save a set before unloading if you want to restore it. For cold-boot restoration,
put `RSX LOAD NDR` and `NDR /LOAD MYNAMES` in your startup sequence, after the
needed disk is available. The supplied provider uses 512 protected bytes; CCP
growth is reclaimable. The existing shared RSX manager adds 1 KiB when the first
RSX is loaded, shared by all active providers.
