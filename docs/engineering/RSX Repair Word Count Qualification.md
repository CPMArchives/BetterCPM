# RSX repair-word byte-count qualification

The SCX host backend has 144 static relocation words. Its preparation and
movement exposed byte-count arithmetic that doubled an 8-bit word count but
discarded the carry. Counts 128..255 consequently reserved or copied too few
bytes. This is an implementation bug, not a new restriction on RSX carriers.

The corrections are in `r3kpre.mac` (temporary/durable union space), `r3final.mac`
(maximum mover request), and `rsxsched.mac` (capacity validation and copying).
The scheduler also skips a zero-word copy: BC=0 passed to Z80 LDIR means 65,536
bytes rather than zero. Small local instruction savings preserve its original
496-byte slot. Finalizer and retained preparer are 968 and 900 bytes respectively,
within their unchanged execution slots. There is no permanent BIOS/BDOS growth,
container slot increase, descriptor expansion or service change.

Evidence on 2026-10-16:

- Actual scheduler plus mover: counts 0, 1, 127, 128, 144 and 255, every declared
  pointer repaired, exact scratch capacity accepted, capacity one byte short
  rejected before mutation, scratch boundary guards preserved.
- Existing multi-module upward/downward and mixed-direction rejection tests pass.
- General Stage 3 transactional load/remove and retained-state movement pass.
- Actual manager ADM3A/backend relocation, rejection of missing/needed backend,
  retained parser state, rebinding, lookup and unload/53K pass on both platforms.
- Live cpmsim exercises the 144-relocation ANSISCRN carrier, unrelated-module
  removal, all ADM3A utility phases and unload/53K successfully. Local evidence:
  `build/monitor-development/live/cpmsim-gp7l3rzm/`.
- Native ZSM4/LINK parity passes for all three changed overlays, both backends,
  portable ADM3A and VT52. The comparison makes DS padding explicit because
  the cross assembler fills it with FF and native LINK normally uses zero;
  operational bytes are otherwise unchanged.

Tests: `tools/test_rsxschedule.py`, `tools/test_rsx_stage3.py`,
`tools/test_adm3a_lifecycle.py`, `tools/test_monitor_backend_native.py` and
`tools/qualify_adm3a_cpmsim.py`. The CPU fixture adds RL B support for the new
carry-preserving instruction, using the same documented carry/zero behavior as
its existing RL C/D implementation.

Final qualification also passes both clean System Disk builds/boots, native
Model 4 command-line editing and unload/53K, and protected-ROM cpmsim with the
freshly rebuilt matching relocated overlay container. The seven guard primitive
checks pass; there are no ROM-write violations and unloading restores 53K.
ROM evidence: `build/monitor-development/live/cpmsim-o3hlii3d/`.
Native evidence: `build/monitor-development/native-campaign/editing-hoyvix42/`.
Clean-build evidence: `/private/tmp/bettercpm-scx-qualified-work/` locally.
The old ROM container must never be substituted with a RAM container.
