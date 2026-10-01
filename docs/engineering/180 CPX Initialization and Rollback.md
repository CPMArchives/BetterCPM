# Engineering Specification 180: CPX Initialization and Rollback

## Result

BCPX lifecycle initialization is now executable. The reloader constructs and
links the prospective CPX chain without publishing it, places its head in the
CCP-owned page-zero scratch word at `004Bh`, and loads the relocatable CCP. On
entry, the CCP initializes present lifecycle entries in configured profile
order. It publishes the head at `ECB_CPXHEAD` only after every callback
succeeds.

If an initialization callback returns a nonzero status, the failing module is
excluded from cleanup. The CCP calls shutdown for the successfully initialized
prefix in reverse order and enters its ordinary command loop with an empty
active chain. The persistent profile remains available, so the bare CCP can
run `CPX.COM` to remove or replace the failing entry. No partly initialized
chain becomes visible to command dispatch.

## Memory disposition

The implementation changes no protected-memory address, TPA boundary, or
allocation size. The command reloader is 931 bytes in its 932-byte carrier.
Word-at-a-time clearing recovers the seven bytes needed for the prospective
head handoff. The CCP grows from 4,867 to 4,968 bytes and remains within its
existing 5,120-byte allocation, leaving 152 bytes.

At most eight CPXs are accepted. Initialization retains one two-byte module
base per completed callback plus a zero sentinel on the CCP's existing
128-byte stack. Failure rollback consumes those bases in reverse order. The
protected command-reloader stack remains unchanged.

## Focused evidence

- The reloader test proves that one- and two-module profiles produce a linked
  prospective chain while the active fixed descriptor remains zero.
- The CCP test uses synthetic lifecycle callbacks to prove profile-order
  initialization and publication after complete success.
- A forced failure in the third module proves that only the first two modules
  receive shutdown, in reverse order, and that the active head remains zero.
- The complete z80pack image builds with 43 reloader and 66 CCP relocation
  references.
- Protected cpmsim execution reaches cold and warm prompts, directory and
  transient execution, and dynamic RSX load/list/unload while enforcing the
  `DF00h` CPU and DMA write boundary.

## Remaining lifecycle work

Engineering Specification 181 completes ordinary pre-transient CPX shutdown
in reverse profile order. The fixed Implementation Item 3 closure matrix
remains the final acceptance step.
