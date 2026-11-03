---
name: image-review-validation
description: Inspect actual stills against selected identity/location references and source requirements, documenting visual mismatches, uncertainty and minimal corrections with independent evidence gates and coordinator-driven targeted repair.
metadata:
  version: "1.2.0-local"
---

# Image Review and Visual Validation

View both the actual take and its selected references with an image-capable tool. Paths, success receipts and unseen thumbnails are not visual review. No legacy image_validator.py, feedback.py or ugc_verifier.py is bundled.

## Checklist
1. Identity/anatomy: face, skin, eyes, brows, hair silhouette, proportions, hands/fingers and limb artifacts.
2. Wardrobe/accessories: approved garment cut/material/color, intended jewelry and consequential props.
3. Expression/acting: the source beat, eye line and readable intent. Neutral closed lips belong to still references; talking performance can articulate.
4. Environment/geography: selected architecture, entrances, landmarks, scale and prop placement.
5. Light/color: scene-motivated direction, shadows, palette and continuity without a universal warm cast.
6. Composition: aspect/framing and complete hands when required; a still proves only the inspected instant.

Use current selected reference take/version IDs, not superseded takes as authority.

For UGC avatar images, additionally check that the supplied identity is preserved in one newly composed single-person photograph. Flag duplicate/tiled faces, collages, split screens, reference insets, pasted-face seams, and unintended copying of source outfit/background/pose. Do not apply this single-frame rule to separately requested animation reference sheets or storyboard contact sheets.

## Video camera, captions and background review

For talking-avatar clips subject to the user's clean-video rule, inspect actual ordered frames or supported playback for zooms/punch-ins/reframing, on-screen captions/subtitles/text overlays, and background movement. Check stationary anchors such as poster edges, walls, furniture, equipment and screens for drift, parallax, morphing, flicker and animation independently of the presenter's natural gestures. Record separate camera/framing, caption and background-stability verdicts with observed time intervals and coverage. Observed violations are needs_changes; insufficient temporal evidence is uncertain. One still cannot establish a stationary background or camera. Physical reference posters are scenery and should remain fixed.

## Review record
Save a versioned JSON/Markdown record under File/reviews/ with asset ID, take path, reference versions, verdict, coverage, concrete observations/issues, suggested fixes and selected creative-authority reference. Verdict is pass, needs_changes or uncertain. A fully evidenced independent pass can clear routine production gates within already selected direction; final-export approval remains separate.

Missing references, unreadable views and unavailable evidence stay uncertain. Numeric scores/confidence are heuristic, not calibrated proof. Full motion, all-frame hand visibility, speech fidelity and lip sync need corresponding temporal/audio evidence.

## Surgical fixes
Follow File/docs/AUTO_REPAIR.md. Identify the exact failing property and specify the minimum correction, preserving the same characters/scenes, working composition/style and source. The coordinator must proceed with supported, authorized repair and fresh independent review rather than stop after listing issues. Prepare exact corrected payloads before any uncovered paid authorization request; retain old outputs, reports and charges.

The review worker inspects and reports; the coordinator executes repairs and dispatches independent re-review. This skill does not register voices, supply an ASR adapter or grant new spending authority. No historical two-retry/252-credit permission carries into this project. A note or imported skill cannot create authorization.

Instruction version: image-review-validation@1.2.0-local.


## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.

For allowance-backed fixes, the independent JSON report also binds asset_id, media:{path,sha256}, actual reviewer_id and delegation_id, plus all required checks with pass/fail/uncertain and evidence. Preserve the raw report; the coordinator supplies the actual completed T3 transport separately.
