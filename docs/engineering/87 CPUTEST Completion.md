# Engineering Specification 87: CPUTEST Completion

## Status

The complete five-item CPUTEST catalog is physically accounted for on the
TRS-80 Model 4 target.

## Integration

`CPUTEST.COM` is installed reproducibly in user zero of the BetterCP/M
conformance image. It follows DIRTEST in dependency order: the test validates
the portable processor floor independently of later direct-BIOS, interactive
console, CCP, and fault-injection campaigns.

## Physical result

`CPUTEST /SAFE` ran under `trs80gp`:

```text
0623  P  R  Register, ALU, memory, stack and CALL/RET signatures agreed
0624  P  R  ADC, INR carry preservation and DAA semantics agreed
0626  O  N  Undocumented processor behavior is not guaranteed
0625  -  S  Z80 extensions are outside the generic CP/M claim
0627  -  S  Timing and interrupt topology require a hardware profile
Summary: 2 pass, 0 fail, 0 error, 1 observed, 2 not-run
```

Both required cases pass. They verify the Intel 8080-compatible register,
ALU, memory, stack, CALL/RET, carry, INR, and decimal-adjust semantics used by
portable CP/M programs.

Case 0626 is deliberately an observation: BetterCP/M makes no portability
promise for undocumented processor behavior. Cases 0625 and 0627 are outside
the generic CP/M claim because Z80 extensions, processor timing, wait states,
and interrupt topology belong to a declared hardware profile.

The catalog therefore closes with two required passes, one diagnostic
observation, two explicit exclusions, and zero failures or errors.

