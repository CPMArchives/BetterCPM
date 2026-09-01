# Engineering Specification 88: BIOSTEST Safe Baseline

## Status

BIOSTEST is installed on the reproducible BetterCP/M conformance image, and
all five of its safe returning checks pass physically on the TRS-80 Model 4
target.

## Physical result

`BIOSTEST /SAFE` ran under `trs80gp`. Its 46-row report scrolled normally and
ended with:

```text
Summary: 5 pass, 0 fail, 0 error, 11 observations
30 scope/required/profile procedures remain untested.
```

The five passing rows are:

```text
0443  P  R  Function 7/8 and 0003h were coherent; restored
0451  P  R  Current DPH pointers and Function 31 agreed
0461  P  R  Found 17 consecutive public JMP vectors
0463  P  R  BIOS base derived only from WBOOT gateway
0622  P  R  Modified code executed at two TPA locations
```

These checks establish coherent IOBYTE access and restoration, agreement
between the current-drive DPH and BDOS Function 31, the conventional ordered
17-entry BIOS jump table, public BIOS-base discovery through the page-zero
WBOOT gateway, and writable/executable transient memory at two locations.

The eleven non-guaranteed rows are observations rather than requirements.
The remaining thirty rows require controlled scratch media, direct device
providers, injected faults, boot procedures, optional profiles, or are
documentary exclusions. The safe run does not promote any of them to a pass.

This is therefore a clean baseline, not completion of the 46-item BIOSTEST
catalog. Subsequent BIOSTEST work must execute its controlled groups with the
declared media and device procedures.

