# DRI DUMP behavioral references

These are historical reference inputs, not production build sources or Utilities
Disk artifacts. `DUMP.ASM` is the original 8080 source from the local conformance
project's investigation 042 reference collection; `DUMP.COM` is the executable
from its `reference/software` directory. Source bytes and copyright notices are
preserved. `provenance.json` records exact hashes and the source/binary evidence
limits; no source-to-binary build equivalence is asserted.

The BetterCP/M Z80 implementation is in `src/utilities/dump.mac`. Differential
tests execute both compiled programs with a public BDOS service fixture. The
retained CP/M permission correspondence is the same reference already used by
the project's DRI ED/PIP collections. No historical binary is silently installed
as BetterCP/M DUMP.
