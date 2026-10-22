# SYSGEN shared choice qualification

2026-10-22 — SYSGEN 1.0 Build 006

Both installation and existing-package replacement approval now call `SG_ASK`,
a compatibility binding for the shared choice-only controller. The original
questions and any-non-Y-declines policy are unchanged. The adapter introduces
no default, invalid-key retry, extra display, typeahead flush or editor state.

## Size and boundaries

The program is **5,734 bytes**, SHA-256
`6b639c4ab99bbbc138f15a770099d5de1d1845003918bae1162b51c4cabb06ba`.
Cross assembly and native ZSM4/LINK match exactly. Both builders expand the same
`expand_sysgen_ui` selection. The binding totals 220 bytes: 185 shared controller
bytes, 28 adapter-code bytes, two choice bytes and five controller-state bytes.
No editor, word module, text controller or formatting buffer is linked.

The program remains below its existing private stack. Its 4000h–8FFFh payload
workspace and 36K TPA guard are unchanged. No resident image or allocation
changes. CONFIG's dual-platform Build 014 binary remains byte-identical.

## Compiled checks

- 255 nonzero key bytes: only Y/y authorizes, N/n declines, every other response
  cancels. Exactly one key is consumed, with later input preserved. BDOS destroys
  general registers in the fixture; stack and configuration remain valid.
- Three malformed-controller configurations fail closed without reading input.
- Six standalone/combined /VER cases establish identity and pure invalid-usage
  rejection for SYSGEN. The full all-utility identity sweep was not completed in
  this partial build workspace because ADMTST.COM is absent; this is not a
  passing full-sweep claim.
- All 32 command-tail/source-I/O checks, 10 structural package validation cases
  and 24 export/recovery/failure cases pass. Existing TPA-boundary checks remain
  part of the export fixture.

## Real platform regressions

`test_z80pack_sysgen_export.py` passes named/default exports, exact 161-record
package bytes and saved startup data, package-replacement refusal/approval,
installation refusal/approval, verified reinstall, filesystem preservation and
cold boot. It runs on private copies of the existing cpmsim fixture. The first
attempt reached the expected operations but could not exit because that fixture
omitted BYE.COM; supplying the normal BYE helper on a further private copy made
the complete campaign pass. Reference/profile media were not edited.

`test_sysgen_install.py` passes native Model 4 installation through the migrated
confirmation, verifies all system records, preserves the populated target file
area and cold-boots the installed target. Native screen captures, original and
installed images and cold-boot evidence are retained.

This is focused utility qualification on disposable media, not a new complete
release-distribution or core-OS acceptance run. User behavior and recovery rules
remain governed by the current SYSGEN specification.
