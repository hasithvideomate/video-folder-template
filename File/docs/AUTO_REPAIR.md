# Automatic repair after review

A confirmed, repairable review finding is work for the coordinator, not a request for the user to say “fix it.” Continue through **review → targeted repair → independent re-review → resume dependent work**. This applies to reference images, storyboard frames, generated shots and assembled edits. The reviewer records evidence; the coordinator performs corrections through the relevant supported tools. Reviewers do not approve their own repairs or operate Premiere.

## Repair loop

1. Read the actual failed asset and selected references, plus the unchanged independent report. Distinguish an observed defect from missing evidence or a genuinely ambiguous creative choice. Uncertain visibility/coverage calls for better inspection, not speculative regeneration.
2. Create a small repair task identifying the asset/take and reference versions, actual source hashes, failed checks, target changes, properties to preserve, intended tool/model, existing authorization and verification criteria. Put concrete correction instructions in the actual prompt/plan, not only in a progress message.
3. Preserve character identity, scene, selected visual style, wardrobe, props, source wording, story action, camera and framing unless a particular failing property requires a source-consistent adjustment. Fix only confirmed issues; do not restart the whole scene or replace successful assets. Use the currently selected compatible editor/model when available. Verify actual model names and supported edit/reference inputs; a shorthand label in an old screenshot is not an executable model ID.
4. Execute routine reversible local/timeline corrections immediately within the editing request. For paid generation, use the project allowance in PAID_REPAIRS.md and repair_runner.py. A covered repair does not need per-payload approval: build its exact bound preview, verify the approved asset/reference/model/defect limits and remaining credits, then submit automatically through the tracked helper. Exact-preview authorization remains available for repairs outside an allowance. Otherwise complete the repair brief, reference binding, exact preview and estimate first, then present the uncovered paid scope together. Do not stop at a vague “needs changes” report when concrete preparation is possible. A budget setting alone is not authorization; a real user-approved repair allowance does authorize qualifying future corrective payloads. This template update authorizes no paid test or retry.
5. Save a new version; preserve originals, failed takes, receipts and reports. Associate the attempt with the defect and operation ID. On an unknown operation outcome, inspect/reconcile it before another attempt. An interrupted run resumes the recorded operation, not a duplicate.
6. Dispatch a fresh independent review automatically. Include the corrected asset, original selected references, previous findings and explicit acceptance criteria. Check both the repaired properties and regressions in previously passing properties. Still review cannot pass video motion/speech checks. Use a fresh T3 task with a distinct stable clientRequestId per round, retain actual returned IDs, and preserve the report as returned.
7. When the asset passes all applicable checks, select the new version, invalidate only affected downstream evidence and continue the next authorized stage. Do not ask the user to initiate animation again. Keep unrelated ready work moving while dependent work waits.

Use at most two corrective attempts per asset/defect cycle by default (initial review plus two repair reviews). This is a loop limit, not paid authorization. Evidence-only re-review limits still apply to the relevant helper. Stop a non-improving loop after two attempts; do not reset counters by renaming a take. Record a concrete blocker with the best retained version, attempted changes, remaining defect, evidence and required next action. New source/creative decisions may establish a new scoped task; do not grant them to yourself.

## Example corrections

| Confirmed finding | Coordinator action | Re-review requirement |
| --- | --- | --- |
| Character starts too far outside a source-specified opening | Adjust only the start position/pose in the affected frame; preserve the same character and scene | Correct relationship to opening, scale and unchanged design |
| Required fingertips are hidden during a grip | Adjust the hand/prop pose or local visibility while retaining plausible grip/contact; no extra fingers or zoom | Required fingers visible, correct anatomy and credible contact |
| Image edit introduces identity/background drift | Correct the affected region against the original selected references; retain the better prior take | Both the requested fix and reference continuity pass |
| Unwanted leading/trailing dead air or an accidental timeline gap | Apply the routine reversible pacing correction through the sole Premiere writer | Normal-speed join review, exact words and complete ending |
| Sampled evidence cannot establish motion or lip-sync | Obtain supported full temporal/listening evidence | Corresponding evidence-backed check; no fabricated pass |

Images needed for animation remain excluded until corrected and independently passed. Never animate a known failing frame just to keep the queue moving. Preserve deliberate animation holds, reactions and action completion; quiet frames are not automatically defects.

## Progress and blockers

Prefer: “The reviewer found two fixable issues. I’m correcting the affected frames and sending them for re-review; the characters and scenes stay the same.” Then actually execute the authorized repair work.

Do not conclude with “Neither frame is cleared; no retries were generated” unless a real blocker remains. In that case name it precisely—such as unsupported editing capability, exact paid scope not yet covered, unresolved submission outcome, missing source authority, unavailable evidence or exhausted repair rounds—and supply the already prepared next step. Do not ask whether the user wants a routine repair they already requested through this standing rule.

## Implementation boundary

This is an agent-operated repair workflow. Current shot gates return verdicts; they do not call image editors or grant spending authority. For talking-avatar batches, `production_runner.py` regenerates rejected takes automatically inside the batch's approved `autoRegeneration` scope (BATCH_AUTOMATION.md); only a recorded `regenBlocked` reason needs coordinator follow-up. Use a new immutable corrected job/version, with authorization supplied by repair_runner.py for an eligible allowance-backed correction or exact preview approval otherwise. Preserve prior run records. Never edit approvals or overwrite failed reports to force acceptance. Final-export approval remains tied to the reviewed version.
