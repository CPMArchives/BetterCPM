Final independent integration qualification, source a54dc243.

cpmsim/result.json and model4/result.json record the final CONFIG binaries.
rebuild-result.json proves independent assembly to those exact hashes.
Native Model4 install/cold captures are available as raw screen memory and text.
cpmsim transcripts include the console's command-line redraws.
The precise exported-payload/installed delta was independently asserted as
[(7030,224,160)] after the run, tightening the original <=1-byte run oracle.

Original candidates are preserved. Tests insert only final CONFIG into private
35c56a03 images; these are not newly built release packages. No package freeze.
The entry109 receipts in ../fdb-runtime-binding-qualification.json are historical
core-fix results. Its installation_cold_boot and final_fdb fields identify the
superseding final integration evidence. integration-checkpoint.json labels its
older FDB artifact snapshots; use its final_fdb field for current size/hash.

The runner snapshots document the local fixture setup, assertions and emulator
commands. They depend on local qualification directories from earlier stages;
they are archival records, not standalone repository tests. Production regression
entry points are listed in ../../engineering/209-runtime-binding.md.
