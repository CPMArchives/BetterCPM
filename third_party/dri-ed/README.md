# DRI ED behavioral references

These files are read-only historical inputs for BetterCP/M's Z80/ZSM4 behavioral
reimplementation. They are not compiled by the production build and are not
installed as BetterCP/M ED.COM.

`ED.PLM` retains the exact source bytes extracted from the project's supplied
`cpm2-plm(1).zip`, member `cpm2-plm/ED.PLM`. The archive README identifies the
Caldera PLM.ZIP release and records a difference in BDOS, not ED. The supplied
ZIP is a macOS repack; its wrapper hash must not be presented as the original
Caldera ZIP hash. `archive-README.TXT` preserves that provenance statement.

`ED-CPM22-reference.COM` was extracted from the unchanged stock CP/M 2.2 disk
at the z80pack commit recorded in provenance.json. It is the behavioral oracle.
`ED-source-archive-reference.COM` is retained as comparison evidence: it differs
from the stock disk binary in length and in the common prefix. Do not attribute
this difference merely to padding or claim source/binary equivalence before
qualification. No newly compiled or optimized ED binary is used as the oracle.

The exact artifact identities, hashes, reference manual and known discrepancies
are in `provenance.json` and
[ED Reference Baseline](../../docs/engineering/ED%20Reference%20Baseline.md).
`LICENSE` retains the CP/M distribution-permission correspondence already used
for the project's DRI PIP reference. Source copyright notices remain intact.
