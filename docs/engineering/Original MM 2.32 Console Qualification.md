# Original MM 2.32 console qualification

## Reference identity and scope

The selected compatibility reference is the existing local `CPMb232.dsk`
image, SHA-256:

```
a13e310d0668b744ebe36c0aa5621a9d6148dcb45b3477d425ea3efb38e5504e
```

The default local path is `/Users/nathanael/CPM/montezuma-micro/images/CPMb232.dsk`.
Both checks accept `--image` for another location, but require that exact hash.
The image is not copied into this repository or redistributed with the provider.
Its contents, rather than its filename alone, are pinned as the selected target.

`tools/test_mm_adm3a_reference.py` extracts sector data from the first three
tracks of the original DMK. Physical sector order is not a linear RAM image.
Unique original instruction signatures and their absolute operands identify
three needed pages: console dispatch/addressing at EF00h, controls/state at
F000h and fill at ED00h. The test loads these original bytes at their original
addresses and executes the original table dispatch at EFD9h. It does not
replace the reference handlers with reconstructed source or mock their output.
This is an isolated console execution check, not a booted-MM hardware test.

## Settled results

0Fh sets reverse ON from either prior mode; repeating it remains ON.
Insert operates on the whole current row and shifts rows down, discarding the
old bottom row. Delete shifts following rows up. Insert blanks the current row;
delete blanks the bottom row. Both clear the entire bottom row when invoked
there. All blanks reflect reverse mode; neither operation moves the cursor.

The original-binary test covers 7,680 combinations of row, column, reverse mode
and line operation. `tools/test_adm3a_lines.py` compares the assembled provider's
complete framebuffer with those original routines at two provider load
addresses, for 15,360 comparisons. It also checks repeated reverse ON, cursor
coherence and guard bytes outside video memory.

## Production lifecycle check

`tools/test_adm3a_lifecycle.py` installs the actual development carrier through
the production RSX preparation/commit code and file-backed helper container.
Removing an earlier allocation moves the provider upward while preserving
reverse mode, hidden cursor, partial escape parser and pending row. Continuing
the address and writing a character then exercises the relocated live code.
Additional load/remove operations preserve the binding. Final unload restores
the basic binding and 53K TPA while preserving the BIOS cursor position.
The fixture controls file reads; actual-media/native/ROM-backed emulator and
representative application checks remain release gates.
