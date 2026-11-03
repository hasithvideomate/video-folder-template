# Local workflow

For supplied spoken video, start with [EDIT_FARM.md](EDIT_FARM.md): parallel local source specialists, one Premiere writer, validated cuts, independent assembled and delivery review. New media generation is a separate optional route.

1. **Inspect inputs:** Read the brief, memory and edit notes. Find any supplied script, editable footage, reference-only samples, existing Premiere project and delivery requirements.
2. **Establish source authority:** If a script is supplied, extract its verified UTF-8 TXT. Otherwise produce a verified recording transcript and preserve substantive speech/order/ending. Keep original sources untouched and proposed cuts separate.
3. **Plan production if needed:** Draft UGC, animation or B-roll directions locally in Codex. Use supplied footage whenever that satisfies the request. Generation is optional.
4. **Generate only when requested and authorized:** Verify the selected Kie model's current contract. Save and present its exact request using the local preview helper, obtain concrete paid authorization, then submit once. Record every attempt and uncertain outcome. Poll the existing task, download its results locally and record the selected file.
5. **Review generated inputs:** An independent review agent automatically reviews composition, exact dialogue, sound and motion using actual available evidence under File/docs/AGENTIC_WORKFLOW.md. UGC uses an accepted avatar and representative sample; animation reviews the first three boards before the rest. These are locally managed workflow gates, not server-enforced permissions.
6. **Connect Premiere:** Discover available automation tools, verify the selected bridge, inspect the intended saved project and current sequence, and resolve live IDs.
7. **Edit:** Follow File/agents.md. Use actual transcript/recording evidence to assemble source-accurate A-roll, preserve natural pacing and add matching supplied/approved B-roll. Add no captions or text overlays; keep camera/framing and the reference background locked.
8. **Verify:** Inspect fresh timeline readback, actual frames and audio/motion where available. Use the supplied safe-zone guide for relevant B-roll/images and hide it before viewing/export. Note uncertainties rather than passing unsupported checks.
9. **User review:** Save the existing project and present the concrete edit. Apply feedback to the same project. Keep current sequence/version, issues and review state in File/edit_notes.md.
10. **Export:** After current-version approval or explicit approval for specified revisions plus export, render into Exports/ with a new versioned name. Verify the actual file; queued output is not completion.
11. **Handoff:** Update File/memory.md with decisions, selected takes, costs, sequence/version, unresolved operations and next action. Mirror new or changed reusable user rules, skills and shared helpers into the master Folder Template during the same task under AGENTS.md's automatic template upkeep rule; record synced paths without copying project history or credentials.

There is no hosted application dependency. Each folder is its own local project and memory. Adobe automation and provider access depend on the tools/accounts installed on the operator's machine.


## Camera, captions and background preference

Keep generated clips and edits at locked framing with no zooms, digital punch-ins or automatic reframing. Add no on-screen captions, subtitles or text overlays. Keep the reference room, posters, equipment and screens stationary without drift, parallax, morphing, flicker or animation; presenter speech and phrase-matched gestures remain natural. Include this direction in every future video prompt. The automatic independent post-generation review must assess camera/scale, captions and background stability separately using actual temporal evidence, with timestamped defects and honest coverage limits. These current user rules govern any older caption/edit examples.

For automatic talking-avatar batches and resumable review dispatch, follow [batch automation](BATCH_AUTOMATION.md). Use `File/scripts/production_runner.py`; routine commands are performed by the agent.

UGC/talking-head assembly includes the mandatory [automatic cutting and pacing pass](AUTO_CUT.md). Remove unwanted dead air and verify every join with actual listening/playback. The settings live in File/pacing_policy.json.

## Animation route
For supplied or newly requested animation, follow [ANIMATION_FARM.md](ANIMATION_FARM.md). Silent action, SFX, narration and dialogue have different evidence needs; protect deliberate holds and story action. Per-shot review begins after each download.

Automatic correction: follow [the repair loop](AUTO_REPAIR.md). Fixable reviewer findings trigger targeted authorized repairs, fresh independent review and continuation, preserving the same characters/scenes. Routine fixes do not require another “fix it” prompt. Uncovered paid scope and final-version export retain their approval requirements.

For automatic paid fixes, approve a [project repair allowance](PAID_REPAIRS.md) once, including a total repair-credit limit, attempt limit, assets/references and models. The agent uses repair_runner.py to bind and submit eligible corrected payloads without per-fix approval, then reviews each result before another attempt. The standing default is 1000 additional repair credits per project, with two corrective attempts per asset; no live grant or credentials are included.

Standing repair setting: **1000 additional Kie credits per project**. The coordinator applies this allowance to the selected repair scope without repeating the budget question. See File/repair_defaults.json; an active project records its own asset/model bindings and authorization evidence.
