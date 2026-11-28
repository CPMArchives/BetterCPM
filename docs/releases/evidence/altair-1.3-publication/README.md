# Altair 1.3 publication

Status: **published and verified, 28 November 2026**. PR #696 is merged.
The [v1.3 release](https://github.com/CPMArchives/BetterCPM/releases/tag/v1.3)
now contains the Altair media package, matching source, exact artifact ledger
and separate Altair checksums. All original release assets retain their IDs,
sizes and SHA-256 digests.

`publication.json` records the frozen product source, merge, publication job,
asset URLs/digests and successful website deployment. The publisher rebuilt
both ZIPs from the exact frozen source and retained generated inputs, required
byte-identical approved archive hashes, then verified GitHub's uploaded digests.
The release notes contain the Altair addition. The maintainer also confirmed
the new card appears under “Choose your platform.”

- [System + Utilities package](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/BetterCPM-1.3-Altair.zip)
- [Matching source](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/BetterCPM-1.3-Altair-Source.zip)
- [Checksums](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/SHA256SUMS-Altair-1.3.txt)
- [Artifact ledger](https://github.com/CPMArchives/BetterCPM/releases/download/v1.3/ALTAIR-RELEASE.json)
- [Final banner/platform acceptance](../altair-1.3-banner/README.md)
- [Installation guide](../../../platform/ALTAIR-INSTALLATION.md)

OS version remains 1.3. Qualification covers the pinned Z80/64 KiB/88-2SIO/Tarbell
emulator configuration; physical hardware and 8080 operation remain unqualified.
Historical candidate and source-freeze records are retained without rewriting.
