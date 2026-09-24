# Patterns worth knowing about, not worth copying yet

Architectures seen elsewhere that are too tightly coupled to their original context to drop in as
generic skills, but are worth remembering before building something similar from scratch.

## Tiered plan-and-verify loop with idea briefs

A heavier variant of this repo's own `sdlc-feature-analyst`/`sdlc-ralph-implement` pair: work is triaged
into three tiers by risk (skip planning entirely / lightweight plan / full idea-brief-then-plan),
and every plan ends with a black-box verification round — a separate subagent that never saw the
code, given only user-facing scenarios and acceptance criteria, talking to the built thing the way
a real user would. Tracking failures over time found that every criterion that failed black-box
testing was an invariant left to prose ("the agent must never X") rather than enforced in code —
worth remembering generally: if a requirement reads like "must always/never," write the code
guard, not just the instruction. Adopt the tiering and the black-box-verifier idea if a project's
plans keep either over- or under-investing relative to the actual risk of the change.

## Deploy-safety protocol

Ask consent → backup current state → deploy → restart → health-check with retry → rollback on
failure. The shape generalizes to any single-server deploy, regardless of the specific
infra/SSH/orchestration tooling underneath.

## Agent-loop design notes

Useful ideas for a long-running agent loop (as opposed to a per-invocation skill): a running
findings memory carried across turns, a rate-limit fallback chain across providers/models, and
per-session logging for post-hoc debugging.
