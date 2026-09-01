# Engineering Specification 75: RANDTEST Completion

## Status

The RANDTEST catalog is complete for the BetterCP/M TRS-80 Model 4 campaign.

## Diagnostic observations

The seven CP/M 2.2 `NOT_GUARANTEED` cases ran independently under `trs80gp`
using private disk copies:

```text
0325  O  N  Prereq/Open=03; random-I/O=00
0334  O  N  Prereq/Open=03; random-I/O=00
0352  O  N  Prereq/Open=03; random-I/O=00
0372  O  N  Prereq/Open=03; random-I/O=00
0388  O  N  Prereq/Open=03; random-I/O=00
0552  O  N  Prereq=03; lifecycle=00
0554  O  N  Prereq=03; lifecycle=00
```

Each reported one observation and explicitly stated that it had no conformance
effect. The results characterize accumulator values, DMA contents after a
failed read, protected-fixture activation, late attribute state, and working
FCB metadata; CP/M 2.2 does not require a particular value for these details.

## Final accounting

RANDTEST contains 49 catalog items:

- 41 required items, all physically qualified;
- 7 not-guaranteed items, all physically observed; and
- 1 out-of-scope item, 0353, describing Digital Research's private random-seek
  implementation rather than a public CP/M behavior.

Cases 0368 and 0369 are included among the 41 required items. They were
qualified externally because the conforming `File R/O` path abandons RANDTEST
through WBOOT and therefore cannot print its own pass row.

No RANDTEST catalog work remains unless BetterCP/M later chooses to reproduce
the private DRI seek implementation, which is neither required nor presently
desirable.

