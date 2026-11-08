# Terminal personalities after compact TCAP qualification

Maintainer direction, 8 November 2026: first finish the compact public interface
and installation/native qualification on cpmsim, Model 4 and Model II. Preserve
load/run/unload, zero permanent memory loss and the full-path budgets documented
in [the integrated design](TCAP-Integrated-Display-Redesign.md). The accepted
limits are 1,280 bytes for ADM3A/VT52 and 1,792 bytes for ANSI. Utility migrations
and release assignment remain deferred.

After that gate, use the historical Z-System terminal catalog as source material
for additional BetterCP/M personalities beyond ADM3A, ANSI and VT52. Its Z3T
records describe emitted controls, geometry and standout sequences. Those tables
provide protocol evidence and test vectors; a BetterCP/M personality still needs
a parser that translates application bytes into the renderer operations. The
parser and platform renderer may share the compact unloadable module, as in
the current design; a separate SCRN/SCX load is not required. Each addition must
preserve the same load/run/unload workflow and pass protocol and lifecycle
qualification. Protocol interpretation and hardware rendering remain separate
source responsibilities.

The separately prepared NZ-COM reference disks include the original Z3TCAP.TCP
catalog, TCSELECT and selected TRS-80 profiles, plus a Z-System HELP reference
collection for the later BetterCP/M HELP design. Preparing those reference media
does not migrate a utility, add a personality or assign a release.
