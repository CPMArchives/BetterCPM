# BIOS recoverable-error retry (0392)

2026-09-08. The Model 4 common physical read/write engine now makes at most
three attempts. Recoverable status errors and bounded timeouts cause a force
interrupt, invalidate the remembered head position, and repeat seek/transfer.
A returned write-protect status ends immediately. Persistent errors return the
last nonzero result; exhausted timeouts retain the existing status 1 convention.
Track formatting is not repeated by this wrapper. Other platform adapters are
not changed by this Model 4 repair.

Write inversion is done once before the attempts and reversed on every final
exit. Read normalization remains on successful physical reads only. This avoids
alternating write polarity on retries and leaves the submitted write buffer
unchanged on return.

Resident disk code grows 33 bytes (927 to 960). Extensions and disk code move
33 bytes down into previously unused space following BDOS. Protected boundaries
and the 54,273-byte TPA are unchanged. No bank switching or history reduction.

`tools/test_bios_retry.py` executes the assembled retry/inversion instructions
with controlled single-attempt outcomes. Its 112 cases cover transient CRC,
lost-data and record-not-found outcomes, persistent errors, timeout results,
write protection, 128–1024-byte sectors, inverted writes and stack/status
preservation. DC_TRY and force-interrupt completion are substituted, so these
are deterministic policy tests, not physical controller timing validation or a
rerun of the original operator-injected conformance case. Existing real-emulator
boot and BIOS/BDOS regression tests remain separate checks.
