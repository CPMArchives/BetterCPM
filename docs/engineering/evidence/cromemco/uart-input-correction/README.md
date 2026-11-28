# Cromemco host serial input correction — 28 November 2026

PASS: corrected emulator hardware checks, exact banner-enabled guest image,
and packaged-launcher interaction. This remains an initial engineering build.

The pinned host HAL reader declared `int data` and filled only one byte with
`read(..., &data, 1)`. Its untouched upper bytes could make the result negative.
The UART interprets negative results as "no character" and returns its previous
character. This explains why accepted keystrokes could change with the host
stack layout, including executable location. The targeted patch uses `BYTE data`,
so the successful read initializes the complete object and returns 0–255.

`uart-regression.json` retains the actual source-reader test compiled with
`-ftrivial-auto-var-init=pattern`. The original fails for 0, 65, 97, 127 and
255, returning negative integers; the corrected reader returns each exact byte.
The preparer validates the pinned source fragment, applies the patch in its
private build and includes the HAL hash in `emulator-build.json`.

`hardware-result.json` and `hardware-artifacts.tar.gz` recheck ROM boot, upper
RAM, console, A–D sector I/O and missing/wrong-size/read-only media with this
emulator hash. `system-result.json` and `system-artifacts.tar.gz` repeat the
banner-enabled candidate's complete bounded integration checks with the same
hash. Guest executable producer hashes remain identical to the banner-correction
candidate; the host HAL patch does not require a different guest ABI or image.

`packaged-launcher-check.tar.gz` retains the successful launch-from-/tmp check:
automatic banner, explicit `:VER /BANNER`, and clean `BYE`. The packaged runtime
uses the same launcher and media, with the corrected emulator binary.

This replaces the earlier assumption that extra startup delays alone explained
the automated-input discrepancy. Serial transmission is still timed and tests
still pace keystrokes, but the uninitialized integer was the reproducible bug.
