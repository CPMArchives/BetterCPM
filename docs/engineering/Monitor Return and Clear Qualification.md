# Monitor command-return reset and explicit clear/home

Implemented 15 October 2026 after PR 285. The locked 1.0 provider set is
MM-style ADM-3A, VT52 and a defined ANSI/VT100-compatible subset, each with a
dedicated test utility. This stage completes the hook integration; it does not
implement the terminal personalities.

## Return boundaries

The disposable reloader establishes its reconstruction stack, then dispatches
MCON operation 5 before BDOS/directory calls, CPX reconstruction or diagnostics.
Warm boot, Function 0 and ordinary COM return converge on that path. The CCP
prompt loop also dispatches operation 5 before output, covering resident/CPX
handlers that return without reconstruction. Cold initialization has already
selected the basic target before reaching the reloader.

Operation 5 discards incomplete output-parser continuation while preserving
screen, position, normal modes and ordinary keyboard input. Its correctness
inside a terminal personality remains a provider-test obligation. The basic
backend treats it as a no-op.

## Internal clear/home

Resident CLS and its generated transient equivalent use MCON operation 4.
CONFIG/DUP disk-utility headers, SYSGEN's header and TYPE page replay use a
shared transient-source wrapper which resolves MONCALL through the public
WBOOT vector and preserves AF/BC/DE/HL. TYPE retains its explicit CR to
synchronize the cooked BDOS tab column after clear/home.

Only the BIOS basic-clear implementation and its underlying platform handler
retain the legacy literal 1Ch convention. Internal callers no longer output
1Ch as a clear request, leaving that byte available for MM insert-line when
its personality is active. No source-level literal-clear caller remains in
the audited utility/resident paths.

## Footprint and qualification

Two reloader counter updates now decrement their memory byte directly. That
recovers six bytes, allowing the five-byte reset insertion to fit the existing
slot: Model 4 reloader is 930 bytes. CCP is 5,442 bytes and remains in the same
5,632-byte rounded allocation. Resident CLS shrinks by two bytes. Permanent
BIOS/BDOS regions, the ROM RAM-template extent and the 53K unloaded TPA remain
unchanged. The cpmsim ROM retains 462 spare bytes; its reloader/CCP external
reference inventories are 44 and 72 respectively.

CPU tests execute a synthetic binding and prove explicit clear preserves
utility registers and reset precedes the first reconstruction/prompt output.
Full reloader tests cover bare CCP, one/two CPXs, relocation and malformed
lifecycle rejection. Their independent physical-read stub and HELLO source
now occupy separate regions, avoiding overlap with private vectors and the
larger RCP carrier. CCP parsing, TYPE stream/page/file replay, utility identity,
resident hints, DUP command-line and SYSGEN command-tail tests pass.
The final Model 4 disk also executes resident CLS followed by DIR and returns
to A0>, with the old display cleared. The legacy development-disk command
campaign is not claimed for the smaller distribution inventory.

Both final System Disks build and boot-qualify: cpmsim 22 files/178K free;
trs80gp 21 files/626K free. Real ROM lifecycle checks exercise prompt return,
transient execution and CPX/RSX reconstruction. The platform rendering and
input test utilities will additionally qualify the completed providers.

## Emulator launch observation

The reported trs80gp crash occurred in macOS HIServices/AppKit application
registration about 0.15 seconds after launch, before guest boot. It followed
a restricted test launch. Subsequent approved Model 4 distribution launches
boot-qualified successfully; that crash report does not implicate guest
monitor handling.

## Next stage

Implement and qualify MM-style ADM-3A and VT52 providers and their dedicated
test utilities. Define the bounded ANSI/VT100 subset before implementing its
provider and tests. The developer guide records how further personalities use
the same interface; completed providers will supply worked examples.
