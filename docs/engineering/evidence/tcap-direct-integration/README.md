# Direct TCAP 2.0 integration evidence

The active contract and accounting are in
[TCAP-Direct-ABI.md](../../TCAP-Direct-ABI.md) and the
[combined display design](../../TCAP-Integrated-Display-Redesign.md).
Utility migrations and release assignment are deferred.

The platform receipts identify actual core/module binaries, source and installed
workflows, emulator hashes, commands and exact memory boundaries. Native screen
captures remain with generated build artifacts; their hashes are retained in the
receipts. `reproduction.json` confirms that all nine builds from the canonical
sources produce byte-identical qualification modules.

CPU receipts qualify their own stated boundaries. They do not substitute for
boot/installation tests. The earlier ADM3A native CPU receipt includes the
conventional extra cache page in its fixture allocation; current full-path costs
come from the final platform receipts, whose modules explicitly own an inline
cache footer. This does not change the tested executable payload.

ANSI's executable comparison covers native and host rendering at two relocation
addresses, typed operations, Function-178 cursor presentation, all supported
renditions, indexed/RGB groups, bounded malformed sequences, saves and scrolling.
Equivalent palette encodings and invisible space foregrounds are normalized;
SCX's omitted-bottom default is expanded for the installed pyte implementation.
The candidate's scope is a fixed 80x24, seven-bit terminal protocol, as documented.
The Model II CPU receipt separately exercises exact private admission, video
mapping, both caller-stack locations and interrupt states, and stack guards.

The inline-cache receipt executes actual manager transactions, movement,
reconstruction and returning-error rollback. The final platform receipts and
packaged-capacity checks establish complete unload restoration using real maximum
COM loads, rather than rounded free-KiB reports.

## Final source cleanup

The final cpmsim and Model II receipts were regenerated after removing abandoned
transaction-engine hooks and optional permanent-reservation profiles. The normal
`cpmsim-fullram` and `model2-fullram` build profiles are used. No `public_tcap=True`
core variant is required or shipped. Model 4's clean-built runtime and packaged
image are byte-identical to its earlier passing campaign, so its original native
and capacity receipts are retained. `cleanup-reproduction.json` records that reuse;
no new Model 4 native run is implied. CPU receipts retain their stated allocation
and admission scope; the current full-machine receipts exercise all three final
carriers on each platform.

## Reproduction entry points

Build the normal system workspaces with the existing distribution builders:
Model 4's default `trs80gp`, checked `cpmsim-fullram` for `z80pack`, and
`model2-fullram` for `trs80m2`. Keep their ordinary SUBMIT and VER utilities for
packaged startup. These engineering tools consume those built workspaces and
create fresh disposable outputs; they do not change distribution membership.

```sh
python3 tools/build_integrated_display.py <workspace> --platform model4 --personality ANSI --inline-cache --output <new-module-dir>
python3 tools/qualify_integrated_cpmsim.py <cpmsim-workspace> --inline-cache --all-personalities --output <new-cpmsim-qualification>
python3 tools/qualify_tcap_trs80.py <native-workspace> --platform model2 --inline-cache --all-personalities --output <new-model2-qualification>
```

Use `--platform model4` for the Model 4 native run. The ANSI executable comparison
accepts `--reference-workspace <model4-workspace>` and
`--cpmsim-bios <cpmsim-workspace>/build/z80pack`. The ADM3A native and host
comparisons also accept `--reference-workspace`; the host comparison's `--bios`
selects the cpmsim BIOS directory. The Model II CPU runner accepts its checked
workspace, `--personality` and `--inline-cache`.

`package_integrated_tcap.py` consumes the three passing qualification directories
and their matching core workspaces. Run `qualify_tcap_package_capacity.py` for
each resulting platform image. Raw receipts and source hashes are recorded here;
generated media and captures stay in the ignored build directory. The Python
runners require pyte; full-machine tests additionally require the emulator and
CP/M disk tools identified in the receipts.
