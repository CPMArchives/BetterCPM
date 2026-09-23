# Engineering Specification 147: Stage 3 Initial Prospective Plan

## Status

This increment connects the validated carrier coordinator to `R3PLAN.RSX` for
the first provable profile transition: loading one carrier into an empty active
profile. It still does not change the active reconstruction table, live RSX
images, published chain, generation, or TPA ceiling. Production Function 202
dispatch does not select it.

## Planning boundary

The existing persistent profile contains ordered filename stems and primary
service numbers. It does not retain allocation sizes or reconstruction
classes. The coordinator therefore cannot safely construct a general old
allocation vector from that table. This increment accepts only an empty
profile and rejects a nonempty profile before calling the planner or publishing
the result.

After the maximum 46-byte normalized-facts reservation, the coordinator stores
one eight-byte plan record, a two-byte allocation vector, a one-byte class
vector, and the 18-byte planner request. It requires all 75 bytes through the
end of that request to fit inside the caller-owned workspace. The planner uses
`LY_RSX` as the profile top and the workspace high bound as the minimum
prospective base, preventing the first live allocation from overlapping
transaction scratch.

On success, the plan record identifies a fresh module, its prospective base,
validated allocation, and reconstruction class. The normalized facts record's
next-scratch pointer advances past the complete planning area. Planner failure,
insufficient space, or a nonempty active profile leaves all persistent and live
state unchanged.

## Qualification

The focused Z80 test runs real v2 `STATEFUL.RSX` and v1 `HELLO.RSX` carriers
through carrier validation, metadata normalization, and the real prospective
planner. It verifies the initial plan record, exact workspace boundary,
advanced scratch pointer, and rejection of a nonempty profile. Existing
corruption, unsupported-operation, and live-chain immutability checks remain.

The next increment must obtain validated allocation and reconstruction facts
for every retained carrier so that the coordinator can plan append and removal
against a nonempty profile without relying on incomplete persistent metadata.
