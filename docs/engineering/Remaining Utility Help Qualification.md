# DUMP, DASM, DSYM and TED help conformance

2026-10-28. Corrects the four additional screens reported by the maintainer.
DUMP 007 adds the missing HELP query; DASM 002, DSYM 002 and TED 002 replace
old usage/key summaries with the shared utility help design. Each generated
screen uses the same metadata identity as VER, short corner, purpose/usage,
aligned options and final HELP/VER entries. All fit within 23 lines and 79
columns. Interactive commands and complete operating rules remain in the manual.
DASM's interactive H reference is unchanged. Third-party source is untouched.

The scoped generator is tools/utility_help.py. DASM and DSYM query dispatch now
precedes drive/user inquiries and returns directly without operation cleanup.
DUMP likewise queries before file/DU services; TED retains its provider-free
query path. Every exact HELP query ignores other arguments and wins over VER.
Unknown/malformed operation arguments retain their existing error handling.
No new file operations or interactive choices are introduced.

[The current qualification record](Remaining-Utility-Help-Qualification.json)
binds exact artifacts and packaged media. Checks passed:

- 24 actual compiled query cases: exact text/identity, maximum screen dimensions,
  case/TAB handling, maximum command tail, HELP precedence, console-only BDOS,
  caller-stack balance and command-tail preservation.
- Existing behavioral campaigns: 174 enhanced DUMP cases, 161 DASM command
  campaigns, 73 DSYM cases and 21 complete TED frontend cases.
- Stock CP/M ZSM4/LINK builds of all four prepared sources match cross COM
  bodies exactly. Each native executable actually runs HELP and returns to CCP.
- Exact packaged BetterCP/M executions of HELP, mixed HELP/VER/invalid arguments,
  and VER print the expected output. All mounted disk images remain unchanged.
- Both-format membership, allocation and complete record readback checks pass.
  The primary 332K disk retains 2K free; these changes fit existing allocations.
- Registry projection/tests, Python compilation and whitespace checks pass.

Reproduce with test_remaining_utility_help.py, test_native_remaining_help.py,
test_remaining_help_media.py and test_utilities_inventory.py. The native and
packaged transcripts are retained under build/remaining-help-native and
build/remaining-help-cpmsim. Registry/input-map changes carry the new source
fragment into corresponding-source packaging. Earlier qualification receipts
remain evidence for their original binaries, not automatic acceptance here.
The standing Model 4 deferral remains in force for the later manual campaign.
