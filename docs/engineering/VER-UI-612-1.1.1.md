# VER query UI correction for 1.1.1 — issue #612

Issue: https://github.com/CPMArchives/BetterCPM/issues/612

The reported normal-command-path defect had two parts: a title-only `/VER`
response and `/HELP` rejection. Current main already implements resident help;
this correction completes standard identification without changing command
dispatch, parsers or terminal providers.

The resident printer uses the same command title and purpose records as help.
It emits the standard separator, BetterCP/M Utilities line and command purpose.
The shared implementation gives all nine resident commands the same format,
with their resident RCP identity retained. Transient VER.COM keeps its own
component identity and existing standard identification/help. Exact help tokens
take precedence over `/VER`, and queries perform console output only.

Normal VER, `/V` subsystem reporting, transient `/BANNER` and the resident hint
to use `:VER /BANNER` are unchanged. Forced `:VER` and qualified `A0:VER` remain
transient dispatch routes; the query recognizer does not change those rules.

RCP adds 46 code/data bytes and one relocation, remaining in its existing
8,192-byte allocation. Its 744 relocations fit the existing 1,536-byte carrier
header exactly. No carrier format or TPA allocation is enlarged. A nearby jump
to the shared syntax routine becomes relative to preserve that header limit.

The RCP revision advances. The six fallback executables also advance because
they embed RCP titles and shared command bodies; their own operations are
unchanged. This follows the existing component revision audit for RCP fallbacks.

Validation: build RCP and its fallbacks; run `tools/test_ver_banner.py` and
`tools/test_resident_feature_hints.py`. The latter checks 735 relocated resident
query/rejection cases and 84 transient queries, including hostile console-call
register clobbering and memory/stack guards. The query stack peak is 22 bytes.
The VER checks distinguish resident and transient identity/help, preserve the
concise banner and exact transient `/BANNER`, and retain the resident feature
hint. These are assembled-code host checks, not final-media qualification.

Release target: **1.1.1**. Published 1.0/1.0.1/1.1 media and release locks are
not changed. Final release acceptance must still exercise normal `VER`, forced
`:VER` and qualified `A0:VER` on the selected platform media.
