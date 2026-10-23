# Part 12 reproduction

Use `assessment/part12-utilities-stacks`, Python 3, cpmtools, z80asm 2.1 at
`~/bin/z80asm`, and the pinned Part 2 cpmsim. Its SHA-256 is
`b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
All build output directories must be new. The tools stage source copies and
apply changes only to the selected checked streaming cpmsim profile.

```sh
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/p12-full
python3 tools/assessment_checked_profiles.py cpmsim-legacy-checked --carrier-bindings --streaming-commands --output /tmp/p12-legacy
python3 tools/assessment_checked_profiles.py cpmsim-fullram --carrier-bindings --streaming-commands --output /tmp/p12-repeat
python3 tools/audit_part11_builds.py /tmp/p12-full /tmp/p12-legacy /tmp/p12-repeat --output /tmp/p12-audit.json
```

The private closure includes all src/tools/metadata/third_party inputs except
Python caches. Freeze those bytes before building; editing a test script also
changes the contract. Documentation changes do not. The recorded Git base and
working-tree input hashes identify the tested source. On hosts with a restricted
Python cache location, set PYTHONPYCACHEPREFIX to a writable temporary folder.

Run every cpmsim campaign sequentially because the emulator shares auxiliary
FIFO names. Set BETTERCPM_ASSESSMENT_SIM for the Part 12 probe helpers if needed;
the older Part 11 package helper retains its pinned simulator path.

```sh
python3 tools/qualify_part12_utilities.py /tmp/p12-full /tmp/p12-legacy --output /tmp/p12-utils-full --live
python3 tools/qualify_part12_utilities.py /tmp/p12-legacy /tmp/p12-full --output /tmp/p12-utils-legacy --live
python3 tools/qualify_part12_stacks.py /tmp/p12-full --output /tmp/p12-stacks-full
python3 tools/qualify_part12_stacks.py /tmp/p12-legacy --output /tmp/p12-stacks-legacy
python3 tools/qualify_part11_live.py /tmp/p12-full /tmp/p12-live-full
python3 tools/qualify_part11_live.py /tmp/p12-legacy /tmp/p12-live-legacy
python3 tools/qualify_part11_packages.py /tmp/p12-full /tmp/p12-legacy --output /tmp/p12-packages-full
python3 tools/qualify_part11_packages.py /tmp/p12-legacy /tmp/p12-full --output /tmp/p12-packages-legacy --live-only
```

Read the results JSON, corresponding transcripts and assembled probe listings.
The probes are installed only in disposable copies, as are HELLO.CPX and
STATEFUL.RSX. They do not alter the clean System Disk or system tracks. Two
fill patterns reduce incidental marker coincidences but do not turn a watermark
into an exhaustive high-water proof. The utility-entry fixtures control public
BDOS output; the live campaigns independently exercise the actual core.

The final preserved stages are qualified-fullram, qualified-legacy and
qualified-repeat. Development stages and earlier tested-* builds are not the
Part 12 deliverables. The attached evidence records qualified stages, selected
products/listings, source changes, build contracts, transcripts, target images
and SHA-256 hashes. Native/ROM and physical interrupted-install recovery remain
outside these commands.
