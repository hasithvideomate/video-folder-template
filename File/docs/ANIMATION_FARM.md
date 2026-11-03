# Animation agent farm

Use this route for character animation, stylized stories, animated products/objects, and visual explainers. It covers supplied animated footage and requested new animated shots. The coordinator selects this route from the actual brief; do not force silent animation through the spoken-video farm or invent dialogue to satisfy a validator.

The parent runs the workflow and owns Premiere. Local specialists return proposals and independent evidence. There is no background service, animation renderer, or full animation batch scheduler installed by this document. `animation_review.py` provides executable per-shot packets and evidence gates. `production_runner.py` remains a talking-avatar runner; `edit_farm.py` remains a spoken-video ledger. Neither currently manages arbitrary silent animation end to end.

## Roles and stages

1. **Story and shot planner:** map the source story/brief into ordered beats and stable scene/shot IDs; preserve exact words, speakers, actions and ending. For supplied clips without a script, inventory visible actions and existing sound with timestamps. Keep observations separate from proposed story changes. Do not generate replacement assets when supplied footage satisfies the brief.
2. **Design and continuity specialist:** bind selected character, prop, location and board versions. Track proportions, materials, palette, geography, screen direction, eyelines, prop ownership and each shot's entry/exit state. Work from actual references, not a text-only consistency claim.
3. **Storyboard/performance specialist:** plan readable staging, anticipation, action, follow-through, reactions and intentional holds. Keep exact dialogue separate from inferred acting. Independently review the first three boards (or all if fewer) before advancing dependent work; already selected direction does not need routine human pilot acceptance again. Resolve genuinely missing creative authority, rather than silently selecting an ambiguous identity/style.
4. **Generation coordinator:** prepare each exact payload through `kie_tasks.py` under the existing spending rules. Generate one uninterrupted shot per video job; cuts between shots belong in Premiere. Clean individual final-aspect frames are the inputs, never grids or annotated contact sheets. Start with a representative shot and independent review before advancing its dependent authorized jobs. A batch authorization covers only the enumerated payloads and reservations; it does not cover newly invented dependent prompts or retries.
5. **Independent shot reviewer:** dispatch immediately after each completed clip is downloaded, while unrelated authorized jobs continue. Use `animation_review.py` packets and the checklist below. Preserve actual T3 task IDs/results and untouched reviewer reports. Never wait for all clips to begin review. Failed takes stay excluded while the coordinator runs the targeted repair/re-review loop in AUTO_REPAIR.md. Preserve the same characters/scenes; execute covered repairs automatically and prepare exact uncovered paid corrections together. Do not stop at listing fixable defects. Missing evidence remains uncertain. New evidence gets a fresh delegated round, at most three rounds per take.
6. **Premiere writer and assembly reviewer:** the coordinator alone operates the existing project, claims `premiere_writer.py` ownership with its actual identity, journals mutations and verifies fresh readback. Specialists do not call Premiere. Assemble passing shots in source order, then independently review the whole sequence and every cut. Source-review passes do not establish assembled pacing.
7. **Delivery reviewer:** after current-version export approval, verify the actual rendered file technically and independently watch/listen to its complete content. Compare exact reviewed sequence/settings, action, speech, joins, sync and ending. A queued render or probe alone never establishes delivery.

Up to three independent planning/analysis tasks may run in parallel where their inputs are ready; do not parallelize Premiere calls or dependent reference/board decisions. Discover T3 provider/model/options, use stable per-round clientRequestId values, bind actual returned identities and inspect an existing task before retrying dispatch. Keep stage/dependency records in File/production-plan.json and memory in active project copies only. Changes to source, selected design, board, take or cut invalidate affected downstream reviews; preserve unaffected assets and prior receipts.

## Current directing rules

Generated animation is 720p. Lock the camera, angle, scale and framing throughout each shot; no zoom, pan, tilt, shake, automatic reframing or internal cuts. Add no captions, subtitles, titles or text overlays. Keep scenery stationary with no background drift, parallax, morphing or flicker. Animate the intended subject's actions while its environment remains fixed. Physical reference posters remain fixed scenery. If the source explicitly requires moving scenery or camera movement, record the conflict and obtain a scoped user change; the word “animation” alone does not override current rules.

Include those requirements in every generation prompt and editing plan. Preserve the chosen shot composition in Premiere; do not hide defects with punch-ins, speed changes or text. Supplied original footage retains its original resolution; record pre-existing movement/text separately from effects introduced by this workflow. Source-mandated scene changes use separately planned static shots and edit cuts, not drifting/morphing backgrounds within a generated shot.

Use sound effects/ambience only when motivated by the brief, and keep the existing no-background-music default. Silent action, effects-only sound, narration and visible dialogue are distinct modes. Only visible dialogue needs lip-sync; narration does not. Talking-avatar animation still uses phrase-matched gestures/full-hand framing and may use the existing avatar compiler when it actually fits that mode.

## Animation pacing

Do not apply UGC silence thresholds as automatic animation cuts. Mark protected anticipation, thought/reaction, comedic or emotional holds, contact, follow-through, reveals and final settling. A quiet pose can carry story information. Trim accidental frozen tails, duplicated lead-ins and unintended timeline gaps only after temporal review confirms they are not protected beats. Check all relevant tracks, including sound tails, before ripple changes.

Evaluate each join for screen direction, pose/velocity continuity, eyelines, action completion, sound continuity and audience comprehension. Keep source in/out distinct from timeline placement, use exact timebases and refresh mappings after edits. Review normal-speed motion and sound across every join and through the complete ending. Do not use playback-speed changes, zooms or captions as repairs.

For general animation, maintain an occurrence-linked shot/action decision record with source hashes, shot/beat IDs, exact source and timeline ranges, reasons, protected boundaries and linked sound. `edit_decisions.py` can validate spoken-word coverage where its contract fits, but it is not a validator for silent story/action completeness. The independent sequence reviewer must explicitly check that coverage; do not fabricate transcript words or treat an empty word list as proof.

## Executable shot review

Write a versioned job JSON. Required fields:

- `version: 1`, `mode: animation`, actual `producer_id`, stable `shot_id`.
- `source`: local UTF-8 script/brief or verified supplied-action inventory; `source_span`: an exact nonempty span identifying this shot. The coordinator verifies semantic alignment and occurrence; substring matching is only a structural check.
- `action`, `start_state`, `end_state`: concrete shot requirements.
- `references`: nonempty list of selected local design/board paths; `protected_beats`: list of protected action/hold/ending descriptions, possibly empty only when genuinely absent.
- `media_origin: generated | supplied`; set from actual provenance, not to bypass generation restrictions.
- `audio_mode: silent | sfx | narration | dialogue`. Non-silent modes require `sound_plan`. Narration/dialogue also require exact `speech` contained in source_span, `speaker`, and a selected local `voice_reference`. Establish/select an original voice through an authorized, independently reviewed reference step before matching later shots; this helper does not create voices.

```sh
python3 File/scripts/animation_review.py packet --job File/jobs/shot-01-v1.json --media Assets/shot-01-v1.mp4 --out File/reviews/shot-01-v1.packet.json
# Delegate independent review with the packet and preserve the actual completed task result.
python3 File/scripts/animation_review.py gate --packet File/reviews/shot-01-v1.packet.json --report File/reviews/shot-01-v1.report.json --completion File/reviews/shot-01-v1.completion.json
```

Packets fingerprint source, job, selected references, voice and media. Existing packet files are not overwritten. Gate revalidates current inputs and the report's match to the actual completed T3 task. A pass also probes usable video, duration, generated 720p and required audio. Supplied 1080p/4K is preserved. Commands neither submit generation nor claim to have viewed media.

Reviewer reports use `packet_hash`, actual `reviewer_id` (childThreadId), actual `delegation_id` (taskId), and `checks` keyed exactly by packet.checks. Each check requires `status: pass | fail | uncertain`, `method`, `coverage`, and concrete `evidence` with timestamps/observations/paths. All passes require `full_clip`. Visual checks need direct_video/direct_av; speech/voice need direct_audio/direct_av; sound timing and lip-sync need direct_av. Inspect actual selected references and neighboring accepted shots when relevant. If a silent job contains an audio stream, also supply `silent_audio_evidence` with full-clip direct listening before passing it as silent. ASR, sampled frames and technical probes do not establish motion or full audiovisual correctness.

Gate returns ready_for_edit, rejected or needs_evidence; the latter two exit 2. A shot pass always leaves assembled_review_complete and final_export_approved false. This validates recorded evidence and identity matching, not the truth of fabricated reports or provider provenance. The coordinator must preserve the real transport results and inspect capabilities honestly.

For animation assembly/export, carry forward the single-writer, exact reviewed-version approval, unresolved-operation recovery and actual-file review contracts in EDIT_FARM.md. Its spoken-video CLI is not a general animation ledger: retain the equivalent animation stage evidence explicitly in the production plan and use the standalone writer journal. Never claim the animation lifecycle has the spoken runner's executable state enforcement. Current limits should be reported when they affect the requested production.

## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.
