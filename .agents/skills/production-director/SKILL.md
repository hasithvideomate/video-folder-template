---
name: production-director
description: Coordinate a local video project in Codex using supplied files, optional direct Kie generation, the user's Premiere automation tools, review and local memory.
metadata:
  version: "1.2.0"
---

# Local production director

For optional Kie execution load ../kie-generation-runner/SKILL.md; for actual still review load ../image-review-validation/SKILL.md. Use the mode-specific router to select the detailed modules; do not load all skills by default.

Read root AGENTS.md, File/project_brief.md, File/memory.md and File/edit_notes.md. This folder is the project identity; there is no backend account or remote project UUID.

Inspect Assets/ and the existing .prproj. Determine whether the task is editing supplied footage, planning new media or both. Do not generate replacement media when supplied material meets the requested scope.

Load ../ugc-director/SKILL.md, ../animation-director/SKILL.md or ../broll-director/SKILL.md only as relevant. Use ../premiere-edit/SKILL.md for actual editor work and ../project-memory/SKILL.md for handoffs. The modules guide the current agent; independent generated-media review is explicitly delegated under File/docs/AGENTIC_WORKFLOW.md.

## Supplied-video route
For supplied spoken video, load File/docs/EDIT_FARM.md and use File/scripts/edit_farm.py. This is the default edit-farm route; do not require generation metadata, an avatar or a separate script. The coordinator delegates dialogue/audio/visual analysis, owns all Premiere calls, validates source-linked edit decisions, requests independent assembled and exported-file reviews, and tracks exact-version approval through verified delivery. Only load generation modules when new media is requested. Template improvements alone require no live host or project inputs.

## Animation route
For animated stories, objects/products and silent or narrated action, use File/docs/ANIMATION_FARM.md and animation-director. Delegate story/design/performance proposals and independent per-shot/assembled/delivery reviews. Use animation_review.py for general animation packets; keep the UGC batch runner and spoken edit ledger within their documented modes.

## Production loop
1. Verify the approved source/version and exact spoken text. Preserve original files, narrative order and ending. Keep visual directions separate.
2. Draft a local production plan using actual source spans, reference paths, intended assets, language/accent and version names. Do not fabricate capabilities; local references become URLs only through `kie_tasks.py upload` or a job `uploads` map.
3. If new generation is requested, read File/docs/KIE_SETUP.md and verify the chosen model's current official endpoint/schema. The optional helper supports Market tasks only. Reference uploads use `kie_tasks.py upload`. Separate voice/character registration and chat endpoints require their own supported integration. At talking-avatar project setup, obtain one project grant (BATCH_AUTOMATION.md) so later batches authorize themselves.
4. Save a concrete one-task preview through File/scripts/kie_tasks.py. Show the exact request, references, output scope, credit reservation and local budget limitation before requesting paid authorization. Planning or template setup never authorizes spending.
5. Submit an approved exact preview once using its ID/hash. For a batch, obtain approval for the enumerated previews and total scope; execute each included task once without asking again per clip. Inspect existing authorization before asking.
6. Poll known task IDs, preserve receipts, download selected outputs into Assets/ using supported tools without the Kie Authorization header, and inspect actual files. Unknown submission outcomes block another paid submission; reconcile in Kie logs rather than deleting local records.
7. Apply the mode's review gates. A fixable defect triggers File/docs/AUTO_REPAIR.md: perform authorized targeted repair, independently re-review and continue. Do not end at a findings report. Preserve the same characters/scenes, previous takes and costs; prepare exact uncovered paid scope before requesting it.
8. Import selected local media into the existing Premiere project and follow the user's editing workflow. Save, present the concrete edit for review and export only under the applicable current-version approval.
9. Update local memory with paths, operation IDs, selected takes, costs, review evidence, unresolved issues and next action. Whenever reusable user rules, skills or shared helpers change, apply AGENTS.md's automatic template upkeep during the same task and record the synced paths.

Follow File/docs/AGENTIC_WORKFLOW.md for the automatic review loop and File/scripts/agentic_pipeline.py for prompt compilation and evidence gates. Routine human clip/sample acceptance is replaced by an independent fully evidenced review. Check whether exact repair scope is already approved before asking; run covered repairs automatically. Uncovered paid scope still requires approval. Estimates and local reservations are not provider-side hard limits. Still frames cannot establish full motion/audio correctness. Claim only actual tool/file evidence.

Instruction version: production-director@1.2.0.


## Batch automation
For talking-avatar jobs, load File/docs/BATCH_AUTOMATION.md and operate File/scripts/production_runner.py. The runner prepares the batch, advances authorized provider work, downloads outputs, extracts supporting evidence and validates reviews. Automatically dispatch its review requests with the saved idempotency keys and bind actual T3 results. Preserve completed rounds; use bounded evidence re-review and recover commands. Follow the returned states until all clips pass or a concrete approval/input/evidence blocker remains; do not hand routine CLI work back to the user. Revalidate before consuming the complete edit handoff. Use `fetch` to collect clips in one call and show them as UNREVIEWED previews immediately. Rejected talking-avatar takes regenerate automatically under the batch's approved `autoRegeneration` scope; for talking-avatar clips use that instead of repair_runner.py, and surface only `regenBlocked` reasons.

For generated UGC, the edit handoff includes a mandatory pending auto-cut contract. Continue through File/docs/AUTO_CUT.md after source review; do not present untrimmed concatenation as a completed edit. Each clip is reviewed immediately after its download, while later clips may still be generating.

## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.
