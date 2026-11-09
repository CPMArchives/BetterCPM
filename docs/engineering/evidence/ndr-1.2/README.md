# NDR implementation checks

Checked against the v1.1.1 CCP source. The JSON records assembly/allocation
measurements for the default Model 4, cpmsim-fullram and Model II-fullram
profiles. NDR provider payloads are byte identical across these layouts.

Executed checks:

- `tools/test_ndr.py`: assembled management and shell/PATH code, name limits,
  duplicate/reserved names, saved sets, returning write errors, invalid loads,
  relocation, prompt output, file operands, quoted text, command-line bounds,
  caller-user restoration and numeric PATH capture. Ordinary blank-prefixed CP/M
  command tails, raw tails, repeated blanks, mixed-case management keywords and
  provider-independent help/version queries are exercised explicitly. Run for all
  three layouts.
- `tools/test_path_edits.py`: existing numeric PATH edits and rejection atomicity;
  run for all three layouts, with absent NDR.
- `tools/test_ccp.py`: existing CCP behavior, default layout.
- `tools/test_ccp_command_newline.py`: completed-line spacing and CR/LF before
  transient output.
- Shared PTY numeric-cursor matching accepts the prior and spaced prompts; the
  distribution boot check expects the new spaced prompt.
- `tools/test_ccpreload.py`: actual Model 4 reloader restoration and error paths,
  including the compact bootstrap carrier.
- `tools/test_ndr_manager.py`: production manager with the z80pack CPU core;
  first-load/shared overhead, exact 512-byte marginal charge, offline stateful
  reconstruction, unload recovery and empty reload.
- `tools/test_ndr_budget.py`: separate protected-provider and reclaimable-CCP
  allocation measurements; provider ceiling enforced at 768 bytes.

The profile execution checks use a controlled BDOS filesystem/console fixture.
The separate booted-guest checks below exercise real development disk I/O;
neither kind is physical-hardware sign-off. Published 1.1/1.1.1 artifacts
were not changed or rebuilt. Full release-media qualification belongs to the
1.2 release workstream.

Two broader checks have pre-existing failures, reproduced unchanged in the clean
v1.1.1 checkout: `test_utility_help_layout.py` expects NOAH's old `/HELP` label
instead of the existing `/H /HELP` label; `test_distribution.py` expects the
old development heading for release versions other than exactly 1.1. Neither
failure is caused by NDR, and neither test was weakened for this change.

Approved listing layout was also executed against the 32-name mock-up: eight
rows, column-major order, 13-character fields and four-space inter-column gaps.
The longest row is 64 characters. A second listing with deleted slots verifies
that names are compacted for display and that the live table is unchanged.


## Booted development guests

`tools/qualify_ndr_guest.py` constructs private cpmsim disks from selected built
components, boots the actual system and checks 43 command steps. It verifies
blank-provider queries, assignment/collision, named command and file operands,
DU navigation, caller DU preservation, save/clear/load, PATH remaining numeric
after alias reassignment, warm returns, unloading and empty reload. It fills
all 32 slots and checks the exact eight-row/four-column display; then it saves
30 names, loads them, deletes two, adds three, and verifies a 31-name saved set.
Host extraction validates three real 384-byte BNDR files. A separate cold boot
runs `SUBMIT RESTORE`, loading the provider and the saved three-name set.
The [receipt](booted-cpmsim.json) records the component hashes and outcomes.

The first-provider charge is 1,536 bytes (512 NDR + 1,024 existing shared
manager); unloading recovers the initial boundary. The prompt regression found
by this campaign is fixed: initial display, every edit redraw and the completed
line retain both the name and the space after `>`.

Native trs80gp Model 4 smoke checks: cold boot; `RSX LOAD NDR`;
`NDR COMMANDS A0:`; `/SAVE DEMO`; `/CLEAR`; `/LOAD DEMO`; and
`COMMANDS:NDPROBE`. The named prompt, success diagnostics and probe output were
visually verified. Model II repeats the same smoke sequence and additionally runs 32 assignments
through SUBMIT, visibly confirming eight rows in four columns and the full-table
usage count. The [native guest receipt](native-guests.json) records both targets.
These are private engineering media, not published release images.
