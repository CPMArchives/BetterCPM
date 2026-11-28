# RomWBW block configuration and installation acceptance

28 November 2026, macOS ARM64, pinned native emulator 1.51 / ROM 3.5.1.
See the [block ABI 6 contract](../../RomWBW-Block-Device-Interface.md) and
[port reproduction instructions](../../../../src/platform/romwbw/README.md).
The 17 recorded installation/control/fault checks and the 15 retained
bring-up checks pass. The 11-test shared-profile regression suite also passes.

| Evidence | Outcome |
| --- | --- |
| `install-result.json` | Checks and exact source/installed image, emulator and ROM hashes. |
| `regression-result.json` | Original boot, BDOS/host file comparison, API/BIOS bounds, TPA overwrite, RSX and geometry checks. |
| `install.txt` | Protected A alias rejection, unchanged B after an unsuitable unit, mapping/save/read-back and native installation. |
| `repeat-refusal.txt` | Saved B restored at cold boot; nonempty target refused byte-for-byte unchanged. |
| `destination-boot.txt` | Cold boot using unit 3; rediscovered A unit, B unbound, installed HELLO and ECHO lifecycle; 56 KiB unloaded TPA restored. |
| `source-kernel.txt`, `source-file.txt` | Corrupt reserved source area or manifest source file rejected before any target writes. |
| `other-user-refusal.txt` | A file in user 7 prevents installation; entire destination image unchanged. |
| `invalid-saved-config.txt` | A bad BWCF checksum prevents OS entry. |
| `absent-saved-device.txt` | An unavailable saved B leaves B unbound while A still boots. |
| `injected-io-error.txt` | Host truncates a disposable image after the probe is loaded. A failed HBIOS read leaves DMA unchanged; failed write pre-read returns an error. |
| `unbind-and-save.txt`, `unbound-cold-boot.txt` | Explicit unbinding is saved, verified and retained at the next cold boot. |
| `build.json` | Fixed layout, private source hashes, file identities and independently checked resident bounds. |

The host reader extracted every installed manifest file and matched the full
CP/M-record-padded SHA-256 from the build inventory. The destination initially
contained an empty E5 directory. The source system and destination are private
image copies; the tests never modify their input candidate. Blank images are
opened with explicit raw type when populating the user-7 refusal fixture.

The direct BIOS probe additionally checks atomic rejection of a modified DPB,
a null request, a request extending past the live TPA, and accepts an 80-byte
request ending exactly at that boundary. Physical tests cover invalid drive,
track and sector, last-sector RMW and DMA spanning 8000h. The separate injected
failure probe deliberately cannot warm-boot after the underlying image is
truncated; the harness captures its pass marker and stops that process.

Stored text normalizes line endings, trailing whitespace and workspace paths;
raw PTY captures stay in the test output directories. The emulator still
implements HBIOS in C++; no physical board or real hardware driver is qualified.
These are engineering CONFIG/SYSGEN variants with the documented block options.
Full CONFIG feature parity, DUP/formatting, wider utility and compatibility
qualification, screen personalities and publication remain separate work.
