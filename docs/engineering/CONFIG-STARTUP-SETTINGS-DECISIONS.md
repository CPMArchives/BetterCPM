# CONFIG active settings and startup defaults

Agreed with the user on 2026-09-08. Requirements for the next CONFIG.COM
implementation pass; not a description of implemented behavior.

## Drive capacity and persistent RAM

Support the A–P logical namespace, including gaps. Inventory every slot and
display configured definitions with their actual letters; do not display empty
slots or stop scanning at the first undefined drive. Physical-device count is
separate from logical-drive capacity, and several logical drives may map to
one physical device. Every configured logical drive must support an independent
format; identical startup defaults must not be assumed to stay identical.

Provide a system default logical-drive capacity that users can change in
CONFIG. Show the RAM/TPA consequence. Save capacity with H and apply it on cold
boot; do not relocate the running system for this setting. Four, eight and
sixteen are examples, not an agreed restriction on the permitted choices.

Cold boot uses platform configuration and any supported device discovery to
establish active drive definitions in protected persistent RAM. Universal
hardware autodetection is not required. Mutable definitions survive warm boot;
disk login/cache state has its own reset rules. Keep ROM defaults distinct
from active writable state. Reconcile the variable-size allocation with stable
persistent addresses and the TPA boundary during design; no final layout or
capacity mechanism has yet been implemented.

## H saves system configuration, not merely drive mappings

H covers all implemented configuration categories, including future A–E
settings, drive formats/mappings and memory allocation. Each setting must have
an explicit application rule: immediate/session effect or cold-boot effect.
Cold-boot changes must be saved to take effect on a subsequent boot.

Keep three concepts distinct:

1. Active configuration used by the running system.
2. Saved startup defaults currently on the system disk.
3. Pending cold-boot changes being prepared in CONFIG.

H must offer these two save scopes:

- **Save pending cold-boot changes only.** Merge those changes into the saved
  startup configuration, preserving previously saved values for other settings.
  Do not silently copy temporary active drive formats into the saved defaults.
- **Save all current settings as startup defaults.** Save the active settings
  together with the pending cold-boot changes, with pending values taking
  precedence for settings that cannot yet be applied to the running system.

Example: the user changes memory allocation and temporarily changes B's disk
format. Choosing the first save scope keeps B's temporary format active now,
but the next cold boot uses the new allocation and B's previously saved format.
Choosing the second scope also makes B's temporary format the startup default.

Validate the complete resulting startup configuration before writing it. In
particular, a reduced logical-drive capacity must accommodate the assignments
in the resulting saved configuration. If it does not, explain the conflict
and require the user to resolve the assignments; do not silently drop them.
Distinguish this from current active assignments, which remain valid within
the running system's unchanged capacity until cold boot.

Saving remains to the current system disk for the current implementation scope.
Selecting another destination may be added later. Loading/unloading device
RSXs, dynamic drive registration and discardable RSX initialization sections
remain deferred until after 1.0.

## Implementation follow-through

- Define stored configuration versioning and validation for both save scopes.
- Preserve saved defaults independently of the active configuration; the first
  scope cannot be implemented by merely dumping active RAM.
- Display pending/reboot-required settings and the scope of an H save clearly.
- Test both example outcomes across cold boot, preservation of unsaved session
  settings during saving, and rejection of inconsistent saved capacity/mappings.
- Measure actual resident code/data cost; the earlier drive-table estimates
  are payload estimates, not guaranteed TPA results.

See [drive-table study](DRIVE-TABLE-SHARING-STUDY.md) for current byte costs.
That study's sharing recommendation is superseded by the subsequent decision:
prefer independent format records for 1.0 and budget for distinct formats for
all configured logical drives. Sharing is not a prerequisite for this design.

## Default TPA policy

Preserve 53 KiB TPA as the default target. Expose practical memory/capability
trade-offs so users can choose larger drive capacity, buffers, history or
extensions where supported. Show measured RAM cost and resulting TPA, and
whether the change requires cold boot. Optimize the default implementation
before charging users additional RAM; never sacrifice correctness to keep
the headline size. These are configuration design requirements, not claims
that every proposed setting is already implemented.
