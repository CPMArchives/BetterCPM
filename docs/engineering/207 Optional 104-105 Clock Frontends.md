# Optional 104/105 clock frontends — qualification and admission

## Status and boundary

**Current status: both frontends admitted as optional-to-load 1.0 components;
Item 6 complete.** The increment history below records how the gates closed.
Final inventory/packaging and frozen release qualification remain Items 7–9.


The first bounded increment implemented `T104C3.RSX` and `T104Z8.RSX` as
BRSX-v2 candidates. Neither was admitted to the 1.0 inventory, installed in a
release image, or added to the default profile at that point. BIOS and BDOS
were unchanged.
The governing contract is Architecture Specification 22, section 7.

These modules supply only historical clock calls. They do not claim broader
CP/M 3, DOS+ or Z80DOS compatibility.

## Implemented contract

Both intercept Function 104 SET and Function 105 GET. Every claimed call
resolves native TIME through Function 182, using private request storage.
No provider entry point is reused across calls. Unclaimed functions chain unchanged.

- T104C3 copies exactly four bytes. GET returns BCD seconds in A; SET supplies
  zero seconds to the native five-byte TIME request.
- T104Z8 copies five bytes. Successful GET and SET return A=0.
- Both return HL=0 on success. A claimed failure returns A=FEh and HL=00FEh;
  failed GET leaves caller output unchanged. This uses the existing P2DOS
  minimal failure convention, pending historical-client qualification.

The implementation shares source in `src/rsx/clock104.inc`, selected by two
8.3-compatible wrapper sources. Private request buffers are mutable RSX state;
code and lookup constants require no runtime patching beyond normal relocation
and chain publication.

## Measurements and evidence

Reproduce the candidate build and CPU-level checks with:

```sh
python3 tools/build_clock104_rsx.py
python3 tools/test_clock104_rsx.py
```

| Candidate | Resident bytes | Allocation | Relocations | Carrier bytes |
| --- | ---: | ---: | ---: | ---: |
| T104C3 | 149 | 256 | 14 | 677 |
| T104Z8 | 140 | 256 | 12 | 668 |

Linked code SHA-256:

- T104C3: `4b6922f5db7108fbae897dbb346b0576d4a41b8cfffd8715fb6065c7e1dc6908`
- T104Z8: `37c5917a951ef93cd888d8893881be9abb390c489f1f77465fca44d0d1102db6`

Each build assembles at 8000h and 8101h and derives relocation offsets from the
resulting binaries. The contract test executes the actual carrier code in the
existing Z80 test interpreter against controlled registry/provider fixtures.
It verifies four/five-byte guards, seconds return/reset, native operation
selection, success and unsupported SET, missing service, provider replacement,
21 partial-output failure cases per candidate, caller input preservation,
DE/IX/IY and stack preservation, and chaining of Functions 12, 200 and 201.
These checks are not a substitute for historical clients or native RSX loading.

A first assembly exposed an eight-significant-character label collision.
Shortening the shared prefix fixed the collision; both alternate builds and
CPU contract tests then passed. This was a source-label issue, not an OS defect.

## Admission gates established for the candidate increments

1. Qualify native mutual-exclusion behavior in both load orders and applicable
   saved/cold profile paths. The shared LOAD coordinator now rejects conflicting
   exact stems before file I/O; the CPU-level evidence is recorded below.
2. Qualify real native load/unload, provider disappearance/replacement, WBOOT,
   and coexistence with P2DOS through the applicable platform paths.
3. Historical GET client gate complete under cpmsim: original SCTIME and
   DATE501 results agree with bracketing native TIME. Failure/SET behavior
   remains covered by guarded ABI probes, not these GET-only client runs.
4. Record final sizes and default-profile TPA, then make the explicit admission
   or deferral decision. Any required loader correction must stay narrowly
   bounded; these optional candidates do not justify architectural expansion.

At that point, Item 6 remained open for this optional admission decision.
The candidate increment added no release requirement.

## Shared LOAD exclusion increment

`R3COORD` now compares the exact canonical eight-byte candidate name against
T104C3 and T104Z8. For either candidate, it scans the bounded persistent active
name list and rejects the opposite stem before opening the candidate file.
Function 177's shared LOAD path owns this check, so calling the API directly
does not bypass it. No general dependency tracking is introduced. Normal
same-name duplicate validation remains the prospective builder's job.

The prospective builder measured 1,012 bytes before this change, with no spare
capacity. The load coordinator measured 707 bytes and now measures 808 bytes,
leaving 204 bytes in its 1,012-byte execution slot. Its released overlay remains
1,024 bytes. No permanent resident allocation or default TPA changes.

Reproduce the bounded checks:

```sh
python3 tools/build_rsx_runtime_overlays.py
python3 tools/test_clock104_exclusion.py
python3 tools/test_rsxcoordinator.py
python3 tools/test_rsx_runtime_overlays.py
python3 tools/test_clock104_rsx.py
```

All pass. The new exclusion test exercises 45 cases: both directions, every
position in each one-to-four-entry list, empty/same-name/unrelated profiles,
nonexact names and invalid clock-profile counts. It also runs the production
coordinator entry for both conflicting LOAD orders, asserting FFh, no file open,
no candidate-length publication and unchanged live profile/memory.

This proves the shared coordinator check, not complete emulator qualification.
Native lifecycle, reconstruction/cold behavior and historical clients remain
admission gates. Neither frontend is added to distribution media by this change.

## Native cpmsim lifecycle increment

`tools/test_z80pack_clock104.py` runs both released candidate carriers through
real Function 177 loading on a disposable copy of the z80pack image. The test
installs the new R3COORD overlay and removes unrelated old probes only from
that copy to provide directory entries. The original image is unchanged.

The passing campaign is retained in
`build/test-results/z80pack-clock104-v5/`: generated probe sources/listings/COM
files, runtime disk images, a command transcript and an evidence JSON containing
artifact, boot-image and simulator hashes. The report directory is never
overwritten by a rerun. Reproduce with:

```sh
python3 tools/test_z80pack_clock104.py --report build/test-results/z80pack-clock104-new
```

Both frontends pass actual GET/read-only SET register and buffer checks,
provider disappearance and replacement after a changed RSX layout, WBOOT and
mutual exclusion in both load orders. P2DOS's 200/201 calls are exercised while
each adapter is resident, including provider absence. Final unload restores the
empty profile and 53K TPA. No OS implementation correction was needed.

An inherited harness branch treated a nonzero successful four-byte seconds
return as a failed GET. Inspecting the generated probe isolated this error:
availability now follows the explicit probe mode, while A retains its historical
seconds semantics. The failure case still requires unchanged caller output.

At that point the Model 4/FreHD path and SCTIME/DATE501 clients remained
unqualified. Thus the cpmsim increment did not admit the candidates or close
Item 6. The historical binaries have been retrieved from the documented
archive for later checks; they are not redistributed in this commit.

## Independent historical-client increment

`tools/test_clock104_clients.py` executes the original archived SCTIME.COM with
T104C3 and DATE501.COM with T104Z8 under cpmsim. It does not rebuild or edit either
client. It pins their SHA-256 values and records the archive URLs, boot image,
frontends, coordinator, probe and simulator hashes. The runtime disk retains
the exact input binaries. Neither archived utility is redistributed in source.

Archive binaries:

- [SCTIME.COM](https://ftpmirror.infania.net/sites/www.seasip.info/Cpm/2000/sctime.com):
  `d176ad1622087126dd986b138ff28517e765a40458f20263dd171a6af24a0609`
- [DATE501.COM](https://ftpmirror.infania.net/sites/www.seasip.info/Cpm/2000/date501.com):
  `c4d1e909ab277256fbfce8d0e4d397bc02278cbc49fbd1c7e08fbd2989a7cd84`

SCTIME writes SuperCalc's BCD month/day/year/hour/minute/second record at
0010h–0015h. Its binary stores E at 0010h and D at 0011h after conversion; the
checker reads the six-byte output before making further BDOS calls. DATE501's
independent PRDMJ source specifies DD-Mon-YYYY hh:mm:ss output. These observations
corrected initial harness assumptions about date ordering and numeric months;
neither the clients nor frontend implementation changed.

Both observed results fall between native TIME samples taken before and after
each original client. Final unload restores 53K TPA. The passing evidence is
`build/test-results/clock104-clients-v3/`. Reproduce using independently obtained
binaries matching the pinned hashes:

```sh
python3 tools/test_clock104_clients.py --sctime /path/to/SCTIME.COM --date501 /path/to/DATE501.COM --report build/test-results/clock104-clients-new
```

This completes the historical GET-client gate. It does not claim the clients
handle service failure or writable hardware; those behaviors are tested by the
separate ABI/lifecycle probes. After the historical-client increment, Model 4 qualification and the explicit
admission decision remained open.

## Model 4 timing probe — qualification still open

The attempted full Model 4 campaign was not a pass. Its captured screens show
truncated commands, including `0CLKPROB 0`, after the third RSX load. It reached
its 180-second bound without completing the sequence. This is recorded as
incomplete automation evidence, not a demonstrated clock or OS defect.

The next targeted test limited execution to four commands: load FREHDCLK,
load P2DOS, load T104C3, and invoke the guarded clock ABI probe. Increasing the
post-T104C3-load delay from 8,000 to 16,000 made this test pass with fresh
`CLOCK ABI PASS` output immediately before the prompt. Source and frontend
binaries did not change. The passing capture is retained in
`build/test-results/frehd-clock104-c3-probe/`.

`tools/test_frehd_clock104_probe.py` preserves this four-command diagnostic,
using the existing application launcher, private writable working directory,
immutable original disk copy, native probes and hash evidence. It is explicitly
not the full lifecycle qualification. The sandbox launcher failure occurred
before emulator startup; the successful run used desktop-launch permission.

The timing-probe increment left Model 4 lifecycle runs and the explicit
admission decision open; it did not admit either candidate.

## Final Model 4 qualification and admission

Both full lifecycle campaigns pass with the measured transition waiting:

```sh
python3 tools/test_frehd_clock104_probe.py --profile T104C3 --lifecycle --report build/test-results/frehd-clock104-c3-new
python3 tools/test_frehd_clock104_probe.py --profile T104Z8 --lifecycle --report build/test-results/frehd-clock104-z8-new
```

Passing evidence is retained in `build/test-results/frehd-clock104-c3-lifecycle/`
and `build/test-results/frehd-clock104-z8-lifecycle/`. Each contains its private
DMK image, generated probes, invocation, per-command screens and artifact/source
image/simulator hashes. Sixteen captured commands per adapter qualify actual
GET/read-only SET, WBOOT, the opposite-profile rejection, failed-GET atomicity
after FreHD removal, provider replacement, P2DOS coexistence, final unload and
53K TPA recovery. The extended campaign has a fixed 450-second bound; the small
four-command diagnostic retains its 180-second bound. No automatic retries or
OS changes are made on failure.

The CPU contract test additionally mutates four-byte GET to copy five bytes.
The guard check rejects this deliberate overwrite for the intended reason.
This is an executable-code guard-oracle test, not a carrier-CRC test.

Admission evidence now covers small measured cost, stateless per-call discovery,
exact four/five-byte behavior, historical original clients, mutual exclusion and
both native platform lifecycles. Admit T104C3 and T104Z8 as independently loadable
optional 1.0 clock frontends, with only one 104/105 profile active at a time.
Either may coexist with P2DOS. Both remain absent from the default profile;
this is clock-call compatibility only.

Item 6 implementation and retained qualification are complete. Include the
accepted modules in the final utility/disk inventory and packaging under
Items 7–8, then rerun their contracts on the exact frozen release artifacts
under Item 9. This decision adds no timestamps, writable clock hardware,
Function-12 impersonation or general dependency architecture.
