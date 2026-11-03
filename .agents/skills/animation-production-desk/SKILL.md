---
name: animation-production-desk
description: Track local animation stages, selected character/location reference versions, storyboard pilot gates, stale dependencies and generation cost evidence.
metadata:
  version: "1.2.0-local"
---

# Local Animation Production Desk

Read ../animation-director/SKILL.md and ../production-director/SKILL.md. No desk.py, studio.py, Project API or dashboard is bundled; this is a locally tracked workflow.

Keep the directing package in File/production.md and technical job/dependency metadata in File/production-plan.json. These are planning records, not automatically executable inputs. Actual helper previews, operations and receipts live under File/generation/. Summarize stage/handoff state in File/memory.md.

## Stages
1. Script analyzed: character/location inventory, exact dialogue/source mapping and all covered story beats exist.
2. Prompts ready: required prompt blocks exist, IDs are unique and referenced jobs are defined.
3. Character references: preview/authorize generation, inspect the results, reuse the user-selected direction and record the independently reviewed take; resolve genuinely missing creative choices.
4. Location references: inspect geography, scale, entrances, materials and light; record selected versions.
5. First three reviewed: submit only SB01–SB03 (or all if fewer) and run independent pilot review before dependent boards; existing selected direction needs no routine human gate.
6. Remaining storyboards: incorporate authorized corrections and proceed within the approved enumerated scope.
7. Video/editing: use clean accepted frames, review a representative video, independently review each later clip immediately after download with animation_review.py, and edit passing media in the existing Premiere project.

Never mark a milestone complete without its actual evidence. These are agent-managed gates, not backend enforcement.

## Reference binding
Record job ID/kind, source span/version, prompt block/version, selected reference IDs and actual take paths, downstream dependencies, proposed settings and review state. Mark model/settings unverified until checked.

Build supported provider bindings from real selected files through an available upload/reference route; do not invent URLs. If a selected reference changes, mark dependent boards/clips stale, retain old takes/reviews/charges and obtain the applicable new preview/approval. Automatically execute already-authorized targeted repairs under File/docs/AUTO_REPAIR.md; do not submit uncovered paid regeneration. A failed review queues repair/re-review, not a terminal handoff.

## Costs
Separate provider-reported charges, active reservations, completed-but-unreported billing and estimated remaining work. Estimates are not invoices or hard provider caps. Record any USD conversion basis/date rather than treating a historical rate as a bill.

Unknown submissions remain unresolved and must be reconciled before another paid attempt. Use ../kie-generation-runner/SKILL.md for actual helper commands.

Instruction version: animation-production-desk@1.2.0-local.


Follow File/docs/ANIMATION_FARM.md for stage evidence, protected holds and exact helper boundaries. Production-plan stages remain agent-maintained; do not claim production_runner.py supports general animation.

## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.
