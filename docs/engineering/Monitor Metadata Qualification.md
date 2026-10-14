# MCON metadata validation qualification

Qualified 14 October 2026. RSX implementation 1.4 retains API 1.0. The shared
R3META phase now reserves the MCON callable identity: version must be 1.0,
reconstruction class STATEFUL, entry offset inside executable payload at 8 or
above, and capability word exactly 0001h on Model 4 or 0002h on cpmsim.
Other callable identities retain their existing validation behavior.

Candidate and retained carriers both use this phase. Invalid MCON metadata
returns failure before metadata-fact publication. This does not yet select a
provider, reject duplicate MCON providers across the prospective profile or
reconcile retained live descriptors. Production finalization still publishes
the basic-console target. Those preparation gates remain required before real
provider activation.

The normalizer occupies 881 of 1,024 bytes; no overlay file, manager reservation
or permanent BIOS/BDOS growth is added. Unloaded TPA remains 53K.

The 34-case test_monitor_metadata.py campaign covers both backend words,
version/class/capability rejection, entry bounds and unchanged behavior for
another callable identity. Each rejection preserves the prior metadata facts
and leaves completion unset. Existing carrier, coordinator, transactional
Stage-3 load/removal and monitor publication campaigns pass. ROM builds resolve
all 718 overlay address words. Both System Disks build and boot-qualify:
cpmsim 22 files/178K free; trs80gp 21 files/626K free.

[Developing monitor RSXs](../programmers/Monitor%20RSX%20Development.md) documents
the 1.0 contract and implementation gates. ADM-3A and VT52 worked examples will
follow their provider implementations and dedicated test utilities.
