# RSX container distribution qualification

Date: 2026-10-11. The fifteen helpers are distributed as one build-matched
`R3PACK.RSX`; their standalone artifacts remain for diagnostics.

Both clean System Disk builds pass boot qualification. cpmsim has 19 files
and 214 KB free; Model 4 has 18 files and 662 KB free. Savings on each:
14 KB and fourteen filenames.

All slot, malformed-slot, truncation and partial-read checks pass. Stateful
load/unload, retained-state reconstruction, warm boot and missing-container
rollback pass on both platforms. Coordinator, gateway-safe handoff, loader
safety, resolver, native build-disk and distribution tests pass.

The copied reader is 242/256 bytes. BDOS, the protected file-loader ABI,
memory allocations and ROM/RAM ownership totals are unchanged.

Qualified artifact SHA-256 values:

- `build/system/R3PACK.RSX`: `438356ad94cbdbb70624f2edb3471c7bb9eae8112f163137c6174375b9b119e0`
- `build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk`: `cc7df4a8b9cbbab27950713e44fc4a9bfa2cf5b20a574bff2178d10c04ca94bc`
- `build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`: `b90cfe9c13b261ff3eaea72d03fa598dca2be2b91610e414182b8def18bf75b9`
