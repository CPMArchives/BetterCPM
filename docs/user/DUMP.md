# DUMP — hexadecimal file viewer

DUMP is on the Utilities Disk. It displays one file without modifying it.

```text
DUMP B7:FILE.COM
DUMP FILE.COM /P
DUMP FILE.COM /40 /P
DUMP FILE.COM /FROM=1200H
DUMP /BARE FILE.COM
DUMP /VER
```

The normal display shows 16 bytes per row in hexadecimal and ASCII, with an
eight-digit hexadecimal file offset. `/40` shows eight bytes per row in 37
columns. Bytes outside printable ASCII appear as dots. CP/M final-record padding
is displayed, including `1Ah`; DUMP does not infer a text-file length.

Without `/P`, output continues through the file. Ctrl-C stops it. `/FROM=` starts
at the row containing the supplied hexadecimal byte offset; EOF itself is not a
valid starting position. `/40`, `/P` and `/FROM=` may be combined.

`/P` needs a loaded screen backend, such as M4SCRN on Model 4 or ANSISCRN under
cpmsim. Existing monitor personalities can remain loaded. DUMP uses the backend's
callable screen operations, so its own display does not depend on selecting a
particular terminal personality. If screen support or dimensions are inadequate,
DUMP reports the requirement and returns; it does not load a driver automatically.

| Viewer key | Action |
| --- | --- |
| Space or Ctrl-C | Next page |
| Ctrl-R | Previous page |
| `.` / `,` | Next/previous page, or next/previous match when a search is active |
| F | Find |
| G | Go to hexadecimal byte offset |
| Q | Quit |

Find asks for the pattern first, then H for hex or A for ASCII. ASCII search is
case-sensitive. Hex accepts contiguous byte pairs or pairs separated by spaces.
The maximum is 32 decoded bytes and 95 input characters. Searches include
overlapping matches and never wrap automatically. A new Find begins at the
current page's first byte. Use G with offset zero to search from the beginning.
Successful search places the containing row at the top and reports the exact
match offset. Paging and Go To retain the pattern and reset the continuation
position to the new page's start.

Prompts support Ctrl-S/Ctrl-D for left/right, Ctrl-G for delete under the cursor,
and Ctrl-H/Backspace for delete before it. Typing inserts; long input scrolls
within the bottom row. A reverse-video character marks the insertion point;
an underscore marks it at the end of the input. Enter submits, and ESC cancels a prompt or running search.
On Model 4, CLEAR and Shift-CLEAR generate ESC; Control-CLEAR generates DEL.
In trs80gp, Home maps to CLEAR; on a MacBook use Fn-Left Arrow for Home.
Empty Enter cancels. Invalid Go To input remains editable for correction.

The bottom row alternates between command hints, status and input prompts. EOF
leaves the final page visible. Read errors preserve the previous complete page;
an initial-page error returns to the CCP. Search errors are not reported as a
completed no-match result.

`/BARE` reproduces DRI DUMP's hexadecimal-only, 16-byte rows and wrapping four-digit
offsets. Any pending character stops it at a row boundary without being consumed.
It accepts ordinary optional drive qualification in the current user, and rejects
DU selection and enhanced switches. Both `DUMP /BARE FILE.COM` and
`DUMP FILE.COM /BARE` work. `/VER` is standalone. Unknown or incompatible options
produce a diagnostic; `/FIND=` and `/LEN=` are not supported.
