# Engineering assessment Part 10: streaming command reconstruction

Date: 23 October 2026. Status: bounded assessment complete; awaiting review.
The maintainer approved Part 9 and authorized this part. Accepted core 1.0
remains `3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## 1. Decision

**Use header retention with payload streaming as the preferred memory policy
for the verified second-stage loader.** The prototype reduces RCP's temporary
reconstruction envelope from 12,672 to **5,504 bytes**, a **7,168-byte (7 KiB)**
reduction, while preserving admission checks, recovery and active RSX state
in the tested cases. The maximum application remains **57,344 bytes (56 KiB)**
unloaded and **54,272 bytes (53 KiB)** with ANSISCRN + ADM3A.

This is a reduction in temporary reconstruction workspace, not another 7 KiB
added to application TPA. It makes reconstruction possible with less free
space below existing allocations. Both designs borrow this memory after the
application has finished; the next application can reuse it.

The recommendation has real costs. Streaming permits incomplete or rejected
payload bytes in unlinked memory, adds 129 bytes to the second-stage executable,
and requires more processing in the measured functional runner. Its fixed
maximum-header reservation also costs more than full staging for tiny HELLO.
Retain Part 9's full-staging implementation as a reference. Do not call this a
speed optimization or a production-ready replacement.

## 2. What was built

The experiment is isolated on `assessment/part10-streaming-loader`, based on
Part 9 commit `d3c030082677c575a589fe3b10df16db39408ff1`. GitHub main was observed
at `c3e1d6bcf7fca8fdf5723f7e32bdf53c70cf6e71`, the PR #460 merge of Part 9.
Newer main-only work is not included in this prototype's qualification.

The same verified 54-byte bootstrap loads and checks a 2,048-byte stage carrier.
The new stage retains the complete relocation header, at most 1,536 bytes,
and reads subsequent records through one 128-byte buffer. It copies payload
bytes directly into the prospective destination, incrementally checks the
same carrier CRC, consumes command metadata, and checks the binding trailer.
The binding scratch and CRC/cursor state fit within the existing stage carrier.

All three candidate command files are **byte-identical to Part 9**. The
experimental BCPX2/BCM2 carrier and 22-byte schema-2 trailer are unchanged.
Their CRC covers the semantic header, relocation directory, payload, command
metadata and binding; it excludes its own final word, final record padding
and unused trailing records. The CPX additive payload checksum is also checked.
No new format revision is needed merely to change the buffering policy.

The complete header is read once. Relocation offsets are checked for range,
ordering and overlap before payload writes, and retained until relocation
finishes. The payload and trailer are also read once. There is no relocation
reread or second payload copy. Only after checksum, CRC and binding admission
does the loader apply relocations and publish the new allocation boundary.
The controller then links the accepted module and later permits initialization.
Private CCP remains mandatory; public CPX requires a zero ID.

The input-buffer reader preserves the caller's data registers and distinguishes
an unsuccessful record from a valid record. A failed read may change the
buffer, including all 128 bytes, but none of that unsuccessful record is
consumed. This is essential: rejecting short input is insufficient if the
caller has already copied the failed record into its payload.

## 3. Memory and capacity

| Streaming region | Address range | Reserved bytes |
| --- | --- | ---: |
| Bootstrap carrier / initial stack envelope | 0100h–04FFh | 1,024 |
| Verified second-stage carrier | 0500h–0CFFh | 2,048 |
| Second-stage stack allowance | 0D00h–0FFFh | 768 |
| Maximum relocation-header cache | 1000h–15FFh | 1,536 |
| One record buffer | 1600h–167Fh | 128 |
| Total fixed temporary envelope | 0100h–167Fh | **5,504** |

The executable stage grows from **1,172 to 1,301 bytes**. It still fits the
2,024-byte code/state allowance before the carrier's binding field, leaving
**723 bytes**. The bootstrap remains 54 bytes; both carriers retain their
original allocation. No resident allocation or raw reserved disk area grows.

A byte comparison of the full 6,656-byte resident carrier finds changes only
in the two-byte expected bootstrap-CRC operand. The upper RAM layout and
resident service addresses remain unchanged. Seven prototype executables and
carriers reproduce byte-for-byte in a second assembly.

| Carrier | Full-staging temporary bytes | Streaming temporary bytes | Runtime allocation | Full-staging minimum incoming boundary | Streaming minimum incoming boundary |
| --- | ---: | ---: | ---: | ---: | ---: |
| CCP | 10,368 | 5,504 | 5,632 | 16,256 | 11,392 |
| RCP.CPX | 12,672 | 5,504 | 7,168 | 20,096 | 12,928 |
| HELLO.CPX | 4,608 | 5,504 | 256 | 5,120 | 6,016 |

The final two columns are absolute addresses, not TPA sizes. Streaming requires
`prospective base >= 1680h`, hence `incoming boundary >= 1680h + allocation`.
All three exact boundaries pass; one byte less fails. Allocation slack is not
part of the temporary envelope. Existing modules remain above the incoming
boundary and must not be touched.

The fixed maximum-header cache deliberately favors predictable placement and
simple bounds. It saves 4,864 bytes for CCP and 7,168 for RCP, but **costs 896
extra bytes for HELLO** compared with Part 9. This is not a universal reduction
for every carrier. A variable cache could reduce the small-carrier penalty;
that additional policy is unnecessary to establish the present result.

The separate 4,096-byte RSX transaction workspace describes a different
operation. It is not automatically added to the command-reconstruction budget.
The 768-byte stack allowance is retained, not newly proved to be the minimum
or a complete worst-case bound.

## 4. Failure and recovery

Before admission, writes are restricted to scratch space and the prospective,
unlinked allocation. The published allocation boundary remains unchanged on
failure. The controller skips an invalid optional CPX with `CPX?`, restores
its boundary and continues reconstruction. Neither relocations nor entry or
lifecycle publication occur for the rejected payload.

Partial bytes are **not erased**. They can be reused by a later valid load;
they are not active code or an allocated module. This is the precise guarantee
that replaces Part 9's stronger promise of no destination writes on any
rejected input. Fixtures verify the exact unrelocated prefix written from
successful records and an untouched remainder after each injected read failure.
They also guard memory outside scratch, the prospective allocation and the
controlled read adapter, including the region above the incoming boundary.

Live fault campaigns restore a good HELLO after the failure, execute it, and
verify STATEFUL RSX data before and after recovery. A 640-byte truncated HELLO
contains the complete 512-byte header and one payload record: this exercises
failure after destination writes, unlike a file truncated at its header.
A separate final-CRC mutation rejects a fully copied payload. Both recover.

The existing requested CPX profile survives for correction. This is not an
atomic restoration of the entire prior CPX command environment; normal warm
boot reconstructs that environment. Active RSX services are separate and remain
intact in the tested failures.

Corrupt second-stage code, its ID, or mandatory CCP causes the existing `!`
halt before a command prompt. No unchecked fallback is introduced. Restart
with valid media remains necessary for that fatal path.

## 5. Processing and complexity

Successful reads remain **51 CCP records, 69 RCP records and 6 HELLO records**,
exactly as in Part 9's full-staging implementation. The verified second-stage
read is unchanged as well. The memory saving is not obtained by rereading files.

The byte-stream helper introduces cursor management and per-byte CRC updates.
A controlled comparison runs both assembled loaders against the same pinned
resident and record adapter:

| Carrier | Full-staging runner dispatches | Streaming runner dispatches | Increase | Streaming fixture stack use |
| --- | ---: | ---: | ---: | ---: |
| CCP | 413,586 | 585,643 | 41.6% | 14 bytes |
| RCP.CPX | 626,399 | 785,072 | 25.3% | 20 bytes |
| HELLO.CPX | 42,731 | 46,644 | 9.2% | 20 bytes |

These are **functional-runner dispatch counts, not Z80 cycle counts or measured
elapsed time**. The runner executes block operations such as LDIR in one
dispatch, and the adapter excludes physical I/O latency and interrupts.
The numbers reveal additional processing; they do not establish those
percentages as real-machine slowdowns. Full staging used 8, 10 and 10 stack
bytes respectively in this narrow fixture. Neither measurement establishes
physical disk-path or interrupt stack requirements.

I favor the streaming policy because removing payload size from the workspace
constraint directly serves crowded profiles and future extensions. I would
not freeze this per-byte implementation as the performance target. Record-wise
CRC/copy processing may reduce overhead while retaining the same memory policy;
that needs its own evidence if pursued. Production integration should retain
an explicit warm-boot performance check rather than quietly accepting the cost.

## 6. Executed evidence

- Real assembled loaders reproduce CCP, RCP and HELLO payloads, relocations and
  entry/lifecycle publication. Exact/minus-one placement boundaries pass.
- Every required record failure is rejected: **126 positions** across the three
  carriers. The copied payload is exactly the prefix from preceding successful
  records; the rest of the prospective allocation remains untouched.
- **32 additional read failures** change 1, 63, 127 or 128 bytes of the read
  buffer before reporting failure. No bytes from those unsuccessful records
  reach the destination.
- Header/payload/trailer corruption, all 16 ID-byte changes per carrier with
  recomputed CRCs, invalid lengths and lifecycle offsets, bad or duplicate
  relocations, stale additive checksums, invalid schema/class and public CCP
  are rejected. Rejected loads leave the allocation boundary unchanged.
- **81 synthetic carriers** cover all accepted header sizes (512/1,024/1,536),
  nine payload sizes, three metadata counts, record boundaries, and binding or
  CRC words split across records. They load at the exact workspace boundary.
- Bootstrap admission tests retain rejection at all 16 partial-read positions,
  sampled corruption, and a foreign ID even with a matching expected CRC.
- Live cpmsim runs a patterned **57,344-byte COM**, rejects 57,472 bytes and runs
  the fitting program again. RET, JP 0, BDOS Function 0 and BIOS WBOOT return.
- Five live optional-CPX fault campaigns cover changed payload, malformed public
  ID, old format, truncation after payload writes and late CRC failure. All
  recover, preserve two STATEFUL checks each, and return to 57,344-byte TPA.
- ANSISCRN + ADM3A retains 54,272 bytes; unloading returns to 57,344. Three fatal
  carrier-corruption cases halt before the prompt.
- The checked legacy cpmsim profile boots, executes and unloads HELLO with
  54,272 bytes unloaded. This smaller control is not Model 4 qualification.

The evidence bundle includes proof images, listings, transcripts, source,
carrier hashes and measurement results. [Part10-Reproduction.md](Part10-Reproduction.md)
gives the commands and pinned inputs. No production image builder was changed.

## 7. Boundaries and next part

These remain private proof images patched onto the pinned Part 8 resident,
with its old contract ID deliberately held fixed. They are not newly qualified
checked-profile builds or installable release packages. The reused raw slots
and new carrier format need a consistent production package contract.

Native/ROM builds, real Model 4 hardware, private utilities, all eight-slot
lifecycle combinations, physical-I/O abort timing, full stack high-water
qualification and installation/upgrade atomicity remain outside this part.
CRC and binding address accidental corruption and mixed products; they do not
authenticate arbitrary executable code.

**Proposed Part 11:** integrate the selected streaming loader into fresh
`cpmsim-fullram` and `cpmsim-legacy-checked` builds with the correct new input
closure/compatibility contract; validate generated packages, installation and
mixed-version rejection. Carry forward the TPA, partial-write recovery and
performance checks. Define the remaining native, stack and private-utility
adoption gates explicitly. Stop after that bounded integration assessment.

Part 10 is complete and awaits review. No Part 11 work has begun.
