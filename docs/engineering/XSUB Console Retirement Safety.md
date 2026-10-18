# XSUB console fallback and retirement safety

V031-F1 exposed an input-call lifetime error: BATCHIO invoked Function 177
operation 4 inside Function 10 when the submitted queue ended. That transaction
uses low TPA, prepares retained providers and may remove the calling module.
Its unconditional warm boot therefore discarded the input application. Merely
removing JP 0000H would return through memory that may already have moved or been
overwritten. No caller-owned scratch range exists in the arbitrary input ABI.

The bounded correction keeps the transaction out of Function 10. Missing or
malformed queues mark BATCHIO idle and chain the original user buffer to console
input. Normal lower BDOS return resumes the application. Opening a newly valid
queue clears idle. Only an explicit BDOS Function 0 while idle may run retirement:
that request already abandons the caller's TPA and has no application return
contract. Explicit RSX UNLOAD is the other supported reclamation path.

A RET or direct BIOS warm boot can reconstruct BATCHIO before observing that
idle state; automatic reclamation on every such route is not implemented. The
provider remains safe and transparent on subsequent console reads. This bounded
lifecycle rule is documented in specification 129 and the user guide. It avoids
new hooks or permanent state. Existing operation 4 remains unchanged for callers
that already relinquish their workspace.

BATCHIO grows from 474 to 502 code bytes, retaining its 512-byte allocation and
service-10 carrier identity. SUBMIT and XSUB utility binaries are unchanged.
The compared fresh BDOS (3,454), BIOS (757) and resident image (6,588) bytes are
identical to the previous runtime. Unloading still restores 53K.

`test_batchio_console_retirement.py` checks absent and malformed queues,
read/close failures, application-memory/DU/DMA/stack preservation, no Function-177 call during input,
explicit Function-0 retirement and reactivation by a new valid stream.
`run_validation_cpmsim_batch.py` checks full-TPA batch continuation, console input
return to the application, safe retirement and 53K recovery on private media.
The native runner adds the same supplemental XSUB fixtures to a Model 4 candidate
without replacing shipped files. Validation records distinguish that unpublished
candidate from a final immutable release.
