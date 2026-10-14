# ADM-3A native Model 4 qualification

## Reproducible campaigns

`tools/qualify_adm3a_native.py` builds private media from the Model 4 distribution
image, replacing R3PACK with its current build and adding the development
ADM3A/ADMTST artifacts. Each run has a fresh directory under
`build/monitor-development/native-campaign/`, so stale captures cannot satisfy
checks. The distribution image is not edited. Existing helper/provider/test entries
are replaced only on private media. Normal runs use the integrated startup;
`--manual-load` explicitly loads ADM3A when testing an older image.

Run the script normally for six text/GIF captures, with `--application` for the
original MM CONFIG opening screen, or with `--bell` for a WAV recording of a
small raw-output BEL probe. The emulator command interface is used for input,
frame waits and captures; after ADMTST completes, the page campaign waits for
the returned prompt before typing UNLOAD. Sending a command earlier can lose
its first characters during command-processor reconstruction.

## Qualified observations

The corrected raw-output page campaign shows the marker at row 5/column 10,
readable output after partial-address reset, contiguous LEFT/RIGHT text, TAB
output at column 8, reverse ON/OFF/toggle, EOL/EOS erasure and the expected
A/blank/C/D line pattern. Captured reverse bytes and corresponding screenshots
agree. Cursor OFF/ON service queries pass, and the utility accepts A, colon,
opening bracket and closing bracket through real character input.

ADMTST uses BDOS 6 raw output for control streams. BDOS 2 expands TAB according
to BDOS's column counter, which does not follow terminal escape addressing.
Zero termination also avoids BDOS 9 terminating on encoded coordinate 24h.
These are test-utility transport corrections, not changes to BDOS behavior.

Final captured output after unloading is:

```
A0>RSX UNLOAD ADM3A
A0>RSX LIST
No RSXs loaded
TPA available: 53K
```

The bell campaign mutes emulator sound effects and records Model 4 audio while
a standard raw-console BEL probe runs. The 44,100 Hz, stereo, 8-bit PCM capture
has exactly 512 threshold transitions, matching 256 high/low cycles. The check
requires the transition count, not merely nonzero samples or a DC level. This
qualifies actual emulator sound generation; it does not certify loudness or
physical Model 4 speaker performance.

## Original application screen

The application campaign runs the unchanged original MM CONFIG 3.10 binary,
renamed MMCONF.COM only to avoid colliding with BetterCP/M CONFIG. SHA-256:

```
3bf6d305f549346b52969a7eb457a6f7dbcc727fbd183a881ae4f024e79e2740
```

Its reverse-video heading, eight-option menu, alignment and choice prompt render
correctly. This exercises a real MM/ADM-3A application screen. No option is
selected: MM-specific disk/BIOS configuration operations are outside this test
and are not promised to work under BetterCP/M.

## Limits and next stage

These campaigns qualify the native Model 4 target, not every ADM-3A application
or physical machine. Cursor visibility routing and input pass; detailed blink
appearance across software and hardware remains a manual observation topic.
The available protected ROM target is cpmsim and has a different backend bit;
it cannot be substituted for a ROM-backed Model 4 rendering test.

Distribution integration now builds release artifacts in build/rsx and
build/utilities, adds Model 4 manifest entries and loads ADM3A from its
platform-specific STARTUP.SUB. Development evidence remains under
monitor-development. Unloading restores 53K; the loaded default has 51K TPA.


## Release build integration

The complete Model 4 build now generates ADM3A version 1.0 and ADMTST's metadata-
owned `BetterCP/M ADMTST 1.0 (Build 001)` identity. Its standalone `/VER` path
runs before service lookup. Model 4 STARTUP.SUB loads the monitor after the
banner; cpmsim keeps its separate banner-only startup. ADMTST is excluded from
the cpmsim development disk as well as its distribution manifest, avoiding an
unrelated disk-full failure from collecting every utility artifact.


Clean manifest-selected distribution builds passed for both platforms: Model 4
has 23 files and 622K free; cpmsim has 22 files and 178K free. ED.COM remains
planned. On the rebuilt Model 4 disk, a separate boot campaign confirmed
STARTUP's automatic ADM3A load, 51K loaded TPA, `ADMTST /VER` returning
`BetterCP/M ADMTST 1.0 (Build 001)`, then successful unload, an empty RSX list
and 53K TPA. Capture: `build/monitor-development/adm3a-integrated-startup.bin`.
The clean-build membership checks exclude both Model 4 artifacts from cpmsim.
