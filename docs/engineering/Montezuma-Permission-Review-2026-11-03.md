# Montezuma permission investigation — 3 November 2026

Status: **redistribution permission unresolved; package freeze on hold**.
Read-only public-source research; no person or archive has been contacted.
No current rights-holder identity or chain of title is established here.

## Evidence and its limits

- [Jim Stutsman’s October 2008 first-person interview](https://www.trs-80.org/interview-jim-stutsman.html)
  distinguishes Montezuma’s license for original CP/M from the BIOS and
  utilities he wrote. This supports separate authorship; it is not a grant or
  proof of present ownership of each catalog/CONFIG/DUP/MDIR file.
- [The 1985 System Programmer’s Guide, indexed scan](https://oldcomputers.dyndns.org/public/pub/manuals/montezuma_system_programmers_guide_trs80m4.pdf)
  identifies Montezuma Micro/JBO copyright and describes the manual/listings
  as material for modifying the purchaser’s own system. The search index
  exposes the introductory copyright text; direct full-PDF retrieval was
  blocked by archive redirection/authentication. Do not claim a full manual
  rights review or infer a redistribution grant from that indexed excerpt.
- [Montezuma’s 1988 catalog, 80 Micro February 1988](https://colorcomputerarchive.com/repo/Documents/Magazines/80%20Micro/1988/80%20Micro%20-%208802%20-%20February%201988.pdf)
  describes a public-domain software library while requiring customers to
  have Montezuma CP/M to read its disk format. The library’s distribution
  description does not establish that the CP/M product, utilities or catalog
  used by BetterCP/M were themselves placed in the public domain.
- [Computer News 80 archival scan](https://archive.computerhistory.org/resources/access/text/2019/12/102794144-05-03-acc.pdf)
  has indexed historical distribution-agreement/commercial-sale material.
  The full 52 MB document exceeded the web reader limit. It is a lead for
  tracing historical distribution, not proof of current ownership or permission.
- The [DRI CP/M permission](https://www.cpm.z80.de/license.html) grants rights
  to CP/M and derivatives. No evidence found in this bounded search establishes
  a grant by Montezuma’s relevant rightsholder for these separate contributions.
  Availability on preservation/download sites is not that evidence.

No broad public redistribution grant was located. This is an evidence gap,
not proof that permission cannot exist. Retain the full search/retrieval limits.

## Actual release exposure

`third_party/montezuma/` contains MDIR, CONFIG and DUP reference binaries and
listings plus DISK.FDF/DISK-INT.FDF and extraction/provenance notes. Full Source
and Utilities source companions copy that tracked material, even when it is
not selected on a System/Utilities disk. DISK.FDF is an input to distributed
DISK.FDB. A GPL declaration for original BetterCP/M work does not clear these
inputs or waive source/rights checks in nested archives.

## Recommended next decision

Seek a specific, retainable permission covering the actual selected file hashes,
redistribution and any derivative catalog data, including full source companions.
Historical publisher/author evidence can guide a rights inquiry but is not a
verified current contact or chain of title. Contacting anyone needs a separate
instruction; none was sent during this investigation.

If no adequate permission can be established, prepare a separate reviewed
public-payload plan: exclude nonessential original binaries/listings, preserve
needed private research separately, and independently document/reconstruct
required format facts. Audit every build/test/reference dependency and validate
catalog equivalence/media compatibility before changing inputs or support.
Do not silently delete references, relabel them GPL, or narrow supported formats.
These alternatives are recommendations only; no catalog replacement/exclusion
is implemented by the P2DOS/license review PR.
