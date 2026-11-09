# 1.2 smoke boundaries

The smoke checks are boot/integration sanity checks, not renewed component
qualification. Use writable copies of the matching System and Utilities media.
cpmsim requires the Companion Utilities disk at C: for its shipped HELP PATH.

1. Boot and confirm the normal prompt and Core OS identity where displayed.
2. Run `STAT MEM`: cpmsim/Model II unloaded COM limit 57,344 bytes; Model 4
   shipped startup limit 52,480 bytes (54,272 unloaded, before optional modules).
3. `RSX LOAD NDR`, `NDR SYSTEM A0:`, then `SYSTEM:`.
4. `PATH` must annotate the matching entry as `A0:[SYSTEM]`.
5. Open `HELP PIP`, see the topic title/menu, then `Q` to the command prompt.
   Native screen checks use the shipped ADM3A personality; the Model II check
   loads it explicitly. The basic-console cpmsim check uses its sequential menu.
6. Run one ordinary transient (`DIR` or the already observed `STAT MEM`).

Retained captures and transcripts, not script exit codes alone, determine PASS.
A capture taken just after a success message may precede the returned prompt;
a subsequent new command/result can independently prove that return. Early
keyboard-paced runs and System-only cpmsim fixtures are not acceptance of
checks they did not actually observe. No broad NDR/HELP/maximum-COM or media
installation campaign was run.
