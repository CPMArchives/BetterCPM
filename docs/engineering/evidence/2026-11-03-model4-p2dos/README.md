# Model 4 P2DOS System image qualification

This trial covers the optional P2DOS clock frontend on trs80gp and the
packaged FreHD TIME provider. The System DMK was built from main
`064c003db9951d17e858be10c155e1299d2164b0`. Its SHA-256 is
`4e661bab569b81ac583f74aabedf41001a76b28d9721ab911e6ff0995feaf5cd`.
The System DMK extracted from the #591 review package matches byte for byte.
[Package identity and member hash](package.json)

The test booted an exact disposable copy of that DMK. A host readback of A0
verified P2DOS.RSX, FREHDCLK.RSX, TIME.COM and STARTUP.SUB against their
build receipts. The clock modules were loaded by the submitted guest commands
after startup. The batch script, register probes and explicit BDOS warm-boot
diagnostic ran from a separate 800K B: disk. The FreHD emulator used a
private directory. The packaged system master was unchanged.

| Guest state | Function 200 GET | Function 201 SET |
|---|---|---|
| Cold boot before loading P2DOS | FFh / 00FFh | FFh / 00FFh |
| FreHD and P2DOS loaded | 00h / 0000h | FEh / 00FEh |
| After explicit warm boot | 00h / 0000h | FEh / 00FEh |
| FreHD removed, P2DOS still listed | FEh / 00FEh | FEh / 00FEh |
| FreHD reloaded with the same P2DOS instance | 00h / 0000h | FEh / 00FEh |
| P2DOS removed, FreHD still available to TIME | FFh / 00FFh | FFh / 00FFh |

Each cell gives the expected A and HL pair, checked in the guest. Each stage
also verified DE, SP, IX and IY preservation, preservation of the SET input
record, and, after a failed GET, preservation of the five-byte caller buffer.
The read-only FreHD provider returned its identity and a date/time sample.
Each probe emitted a stage-specific success string only after both calls and
all register/buffer comparisons passed. [Commands, screens and hashes](results.json)

Two complementary host tests ran against the assembled files in the exact
Model 4 build workspace. The controlled P2DOS test passed all 21 partial
provider-write failure cases, recovery and per-call service discovery.
The provider sampling test passed 26 sampling and rollover checks.

## Reproduction

From a BetterCP/M checkout with the build prerequisites, prepare the System
images and run the Model 4 packaged diagnostic:

```sh
python3 tools/prepare_release_systems.py --output /new/systems --simulator /path/to/patched/cpmsim
python3 tools/test_packaged_model4_p2dos.py --image-dir /new/systems/trs80gp --output /new/model4-result --emulator /path/to/trs80gp
```

This evidence applies to the identified image in trs80gp. Physical Model 4
and FreHD hardware and final fresh-package installation are outside this
trial. Compare the final System image hash before carrying this result
forward. Package freeze remains on hold.
