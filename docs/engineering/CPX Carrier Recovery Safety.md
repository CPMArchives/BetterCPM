# Optional CPX carrier failure recovery

V033-F1 reproduced a session-ending failure: Function 176 accepted BAD into the
persistent profile, then CPX.COM's Function-0 return rebuilt that profile and
entered CRFAIL on an invalid carrier signature. The fixed reloader rejects the
carrier without making the remaining command environment unusable.

## Recovery boundary

CROPEN saves the current downward allocation boundary on the protected reloader
stack before calling CRLOAD. The loader validates bounds before writing payload
or applying relocations. Until CRLOAD succeeds, the candidate has no link from
the prospective head/preceding CPX, and no initialization or command callback has
run. On failure, restoring the saved boundary discards that candidate's entire
allocation, including any partial payload or relocation writes. Earlier valid
CPXs lie above the saved boundary and remain intact. The next profile entry can
reuse the discarded range. The required CCP is then loaded below the surviving
chain. The active descriptor remains zero until normal CCP initialization.

The failure diagnostic is `CPX?` plus CR/LF through existing BDOS Function 9.
There is no file I/O or CPX command callback in this diagnostic. Existing monitor
RSXs may still handle console output through their normal output hook. The
persistent profile is unchanged, permitting CPX LIST and CPX UNLOAD after
recovery; the warning can recur until the carrier is repaired or removed.
Missing optional carriers remain silently skipped. Required CCP failure and
initial directory-login failure retain the existing hard-failure behavior.
This does not certify recovery from arbitrary memory corruption or malicious
code in an otherwise accepted carrier.

## Fixed-memory cost

The Model 4 reloader grows from 930 to 932 bytes within its unchanged 932-byte
slot. Space is recovered by falling through the unnecessary entry jump,
using the already-valid file-kind flag instead of a second CPX flag, and linking
the first CPX through CRHEAD as a sentinel tail destination. The same link store
then handles first and later modules. No ABI field, protected layout address,
BIOS/BDOS allocation, or unloaded 53K TPA contract changes.

The cpmsim reloader is generated from the same source with its existing raw
sector-reader substitution. The loader's required-CCP failure path is unchanged;
optional-carrier recovery is shared by both platform builds.

## Regression contract

The assembled-code test checks bare and two-CPX success, bad signatures,
ABI/flags/layout/entry/lifecycle/relocation rejection, payload/read/reset errors,
restored allocation, no rejected publication, retained profile names and a late
failure after a valid preceding CPX. The required CCP still hard-fails. Live
cpmsim and native Model 4 runners add only a malformed supplemental BAD.CPX to
disposable System Disks, reach the prompt with RCP retained, remove BAD and
check unchanged shipped files and memory recovery. Evidence and any unexecuted
variants belong to validation batch V034, rather than being inferred from this
design rationale.
