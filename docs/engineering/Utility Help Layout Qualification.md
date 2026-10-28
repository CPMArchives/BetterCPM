# COMPARE and NOAH help layout correction

Date: 2026-10-28. Implements the established Utility Help Screens design.
COMPARE 1.0 revision 002 and NOAH 1.0 revision 019 now generate help from their
metadata identity, followed by the short corner, concise purpose/usage, aligned
options and final HELP/VER rows. Each fits an 80-column, 24-row console while
reserving the returned prompt line. NOAH's development disclaimer and dense
operational commentary are removed from the quick reference; full behavioral
rules remain in the Utilities manual. NOAH /VER retains the utility identity
format and describes it simply as Archive Utility.

No option is added or removed, and comparison/archive semantics and documented
query precedence are retained. COMPARE additionally stops interpreting BDOS 35's
undefined accumulator as a size-query failure; the FCB carries the size result.
Its native runner requires actual guest comparison output and fails on timeout.

Checks: 88 compiled COMPARE cases, including exact help layout and screen bounds;
stock CP/M ZSM4/LINK parity and actual summary execution; NOAH compiled help
queries with no overlay access; 38 existing NOAH write cases; native parity for
NOAH resident and CLI phases; packaged BetterCP/M help/version queries and
COMPARE range/pager execution; unchanged mounted media; independent inventory
and complete readback for both platform images. Source/provenance packaging is
checked against the complete corresponding-source archive.

The blanket Model 4 deferral for the later manual campaign remains in force.
No Model 4 PASS or new release baseline is asserted. Earlier qualification
records describe their original byte identities, not these new revisions.
