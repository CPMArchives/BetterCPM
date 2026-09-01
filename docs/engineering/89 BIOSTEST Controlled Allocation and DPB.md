# Engineering Specification 89: BIOSTEST Controlled Allocation and DPB

## Status

All seven required BIOSTEST Allocation/DPB controlled checks pass physically
on the TRS-80 Model 4 target using an empty disposable disk.

## Test infrastructure

The command runner now accepts repeatable delayed interactive responses. A
response may use `DELAY:TEXT` to give each emulator prompt its own wait. This
is required for controlled programs that read the Model 4 keyboard only after
different amounts of disk work; keystrokes sent before a prompt are not a
reliable queued terminal stream.

Every run mounted a private copy of `blank-790k.dmk` as B:. The reproducible
blank image and conformance image were not modified.

## Controlled result

BIOSTEST selected B:, confirmed it as empty and expendable, and executed:

```text
0424  P  R  Function 27 returned current scratch-disk ALV
0425  P  R  DPB-derived ALV length and bits matched blank disk
0426  P  R  AL0/AL1 matched reserved ALV directory bits
0431  P  R  Decoded valid 15-byte DPBs for both drives
0432  P  R  Both configured DPBs valid; sharing accepted
0433  P  R  DPB field changed, re-queried, and restored
0427  P  R  One-record block set then cleared its ALV bit
```

For case 0426 the physical evidence was:

```text
DPB AL0/AL1=C000; ALV[0/1]=C000
```

Case 0427 decoded the allocated block, observed its allocation-vector bit set
after the write, deleted the temporary file, and verified that the bit was
released. BIOSTEST left the scratch disk empty.

Together with the five safe returning checks, BetterCP/M now has twelve
qualified required BIOSTEST passes.

## Newly exposed disk-trace failures

An aggregate controlled run continued into BIOSTEST's shared disk trace. It
reported 13 passes overall but identified four failures outside the
Allocation/DPB group:

```text
Failed items: 0449 0454 0456 0458
```

These concern persistent disk-call context, SECTRAN-to-SETSEC translation,
DMA-address tracing, and WRITE type codes. They are not reclassified or hidden
by the successful allocation result. Each requires focused diagnosis in the
next disk-interface milestone.

