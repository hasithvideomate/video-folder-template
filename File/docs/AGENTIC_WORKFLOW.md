# Agent-driven production and independent review

For editing supplied spoken footage, use [EDIT_FARM.md](EDIT_FARM.md). The generation path below applies only when new media is requested; it is not a prerequisite for ordinary video editing.

Codex is the orchestrator while the task is running. For talking-avatar batches, use [BATCH_AUTOMATION.md](BATCH_AUTOMATION.md) and `File/scripts/production_runner.py`: it automates exact preview preparation, authorized submission/status, downloads, evidence files, review task tracking and edit handoff. `agentic_pipeline.py` remains the offline compiler/review gate. The agent dispatches queued reviews through connected tools and operates Premiere. No always-on service is installed. Start with “Run the agentic workflow for this project's approved script and selected reference.” Resume with “Continue the agentic workflow”; inspect saved operations before acting.

The executable compiler/gate currently supports talking-avatar clips (including talking animated characters). General animation uses [ANIMATION_FARM.md](ANIMATION_FARM.md) and `animation_review.py` for silent, effects, narration and dialogue shot checks. Silent B-roll needs its own mode-appropriate review; do not fabricate dialogue or hand checks to force them through this helper.

## Operating contract

Proceed through planning, authorized generation, download, independent review and reversible editing without routine human review requests. Independent review replaces routine human sample/clip gates for an already selected identity, source and visual direction. It does not select an ambiguous identity for the user. Automatic acceptance is allowed only for fully evidenced passes. Preserve exact dialogue, language, order and ending.

Every newly generated video is 720p, with fixed camera/angle/scale, no zoom, pan, shake, reframing or cuts inside the generated shot, no added captions/subtitles/titles/text, and a stationary reference background including physical posters and screens. Map natural gestures to exact phrases, keeping complete hands in frame. These rules apply to every attempt and the edit. Do not remove unwanted generated captions by cropping, zooming or covering them with overlays.

Existing spending authorization must cover the exact payloads and reservations. One batch authorization can cover enumerated previews; no per-clip confirmation is needed. No paid retry is authorized by this setup. A defect creates an automatic repair task under AUTO_REPAIR.md. Execute covered repairs; an uncovered paid correction becomes a concrete preview for authorization, never an untracked submission. Unknown task outcomes stop paid work until reconciled. Final export still requires current-version approval under File/agents.md. These are the two retained human boundaries, not routine review gates.

## Run and resume

1. Read the brief, memory, edit notes and actual sources. Inspect actual tools. Run `python3 File/scripts/agentic_pipeline.py doctor` for local evidence tools. Missing ASR/OCR is not a reason to install or buy services automatically; use available supported direct playback/listening. Missing temporal evidence remains uncertain.
2. Write one immutable versioned job JSON per clip (contract below). Resolve any conflicts in visual direction. Verify the current official model contract: supported 720p, reference URLs, duration, input field names. Do not infer provider support from the compiler.
3. Compile the payload. Review the entire payload, including other fields, for conflicting camera/text/background directions or unsupported settings. Use the existing `kie_tasks.py preview`, present the exact payload, source span, references, scope and reservation, and submit only under existing concrete authorization. Record preview ID/hash and task ID in memory. Serialize provider mutations. Do not change old payloads or receipts.
4. Poll known tasks with `kie_tasks.py status` using bounded waits. Download completed media to versioned Assets paths with supported tools, without forwarding API authorization to download URLs. Probe actual files for usable streams, duration and 720p (short side 720 for landscape/portrait). A successful provider task is not a passed clip.
5. Create a review packet after download. It fingerprints the job, source, selected references, optional voice reference and actual clip. Spawn an independent review agent automatically using the packet and review instructions below. Record the returned task/agent ID before waiting; do not launch a duplicate on resume. If the reviewer is unavailable, mark review blocked; the producing agent must not impersonate it.
6. Run `gate` against the returned report. `ready_for_edit` admits the clip; `rejected` isolates the take and preserves timestamped defects; `needs_evidence` investigates missing evidence without claiming a pass. For a rejected take, automatically execute the targeted repair loop in AUTO_REPAIR.md, retaining the source and selected references. Do not finish at a proposed correction when existing authority covers execution. Uncovered paid regeneration awaits exact authorization. Each new take gets a new packet and independent review. No unbounded retry loop.
7. Import only admitted clips into the existing Premiere project. Automatically perform the pacing pass in File/docs/AUTO_CUT.md using File/pacing_policy.json; an untrimmed concatenation is not a completed UGC edit. Follow bridge discovery/verification, typed previews and fresh readbacks. Keep framing locked and add no text. Inspect the complete assembled edit for dialogue order, endings, voice continuity and transitions as well as the clip checks. Cross-clip continuity cannot be proved by reviewing one clip alone; give the reviewer adjacent accepted clips/voice references when available.
8. Save the reviewable edit and request the required final-version export approval only when ready. Verify actual exported media after rendering. Persist operations, packet/report paths, review task IDs, selected takes, costs and next actions in project memory. Never put filled records into the master template.

## Job and commands

A job is JSON with these fields (all required except voice_reference):

- `producer_id`: nonempty actual orchestrating thread/agent identifier, validated before any preview/submission.
- `script`: local approved UTF-8 source path; `dialogue`: exact contiguous source span.
- `references`: selected local reference paths; optional `voice_reference`: selected local voice evidence.
- `resolution`: `720p`; optional `mode`: `talking_avatar` (the only supported helper mode).
- Optional `voice_mode`: `match_reference` (default, requires `voice_reference`) or `establish_baseline` (requires no selected voice reference). Unsupported modes fail before generation. Use baseline mode only when the approved brief allows an original voice and no voice reference has been selected. The reviewer listens to the full first take for consistent voice, requested language/accent and suitability; records `baseline_established: true` in the voice check and explicitly states that cross-clip continuity is not yet applicable. The admitted first take becomes `voice_reference` for later clips. Never use baseline mode to bypass a selected voice.
- `gestures`: list of objects with `phrase` (exact phrase from dialogue) and `cue` (visible gesture and timing). Cover the meaningful spoken phrases rather than repeating one generic cue.
- `visual_direction`: editable direction, separate from the source; resolve conflicts with mandatory rules before compiling.
- `payload`: verified provider object containing `model` and `input`. References inside the provider payload use real supported URLs, not local paths.
- `prompt_field` and `resolution_field`: actual dotted paths such as `input.prompt` and `input.resolution`, only when supported by that model. Unsupported contracts block generation rather than silently choosing 1080p.

```sh
python3 File/scripts/agentic_pipeline.py compile --job File/jobs/clip-01-v1.json --out File/jobs/clip-01-v1.payload.json
python3 File/scripts/kie_tasks.py preview --payload File/jobs/clip-01-v1.payload.json --cap-credits AUTHORIZED_RESERVATION
# Existing helper submit/status commands follow concrete authorization.
python3 File/scripts/agentic_pipeline.py probe --media Assets/clip-01-v1.mp4
python3 File/scripts/agentic_pipeline.py packet --job File/jobs/clip-01-v1.json --media Assets/clip-01-v1.mp4 --out File/reviews/clip-01-v1.packet.json
python3 File/scripts/agentic_pipeline.py gate --packet File/reviews/clip-01-v1.packet.json --report File/reviews/clip-01-v1.report.json
```

Outputs are never overwritten by compile/packet. Use new version names. The gate rehashes current inputs and rejects stale evidence. The gate validates a reviewer's structured claims, not their truth or cryptographic identity; the orchestrator must verify the actual delegation result and evidence. A job edit, source/reference change or replaced media requires a new review. The report must be retained as returned by the reviewer, not upgraded by the producer. The batch runner may bind a missing delegation task ID in a separate transport-bound copy while preserving the raw report and all findings.

## Independent reviewer task

Use this brief with the actual packet path and destination report path:

> Review the actual downloaded clip independently against the packet's approved source, selected references, phrase-specific gestures and mandatory rules. Read File/docs/AGENTIC_WORKFLOW.md. Do not generate, spend, edit media or operate Premiere. Inspect actual video and audio using supported tools. Check the full duration, including opening/ending and gesture transitions. Inspect identity and compare the selected voice/neighboring clips if supplied. A still cannot establish motion, ASR cannot establish voice/lip-sync, and sparse OCR cannot establish absence of text. Distinguish direct synchronized AV, video-only, audio-only, ASR and sampled stills. Physical fixed posters are permitted scenery. Mark unavailable checks uncertain. Record timestamps, observed defects, evidence paths/methods and actual coverage. Return a versioned report JSON, concise findings, and a minimal proposed correction for failures. Do not alter packets or grant export/spending approval.

Discover delegation through the live orchestration catalog; honor current provider/model options. Native same-provider child tools are suitable when supported with no model options; otherwise use `delegate_task`. Each new T3 review round uses a fresh delegate_task and distinct stable clientRequestId, including previous findings and unresolved objections. Store taskId, not just childThreadId. On resume inspect the existing task before dispatching another. Do not start top-level threads for reviews.

Report JSON: `packet_hash`, actual `reviewer_id`, actual `delegation_id`, and `checks` keyed by every packet check. Each check has `status` (`pass`, `fail`, `uncertain`), `method`, `coverage`, and nonempty `evidence` (timestamps, observations and file/tool evidence or a concrete unavailable reason). Temporal passes require `coverage: full_clip`; methods are `direct_av`, `direct_video`, or `direct_audio` as appropriate. Wording/completeness/voice require listening; gesture timing and lip-sync require synchronized AV; camera, text, background and hand framing require video. Other evidence methods may support failures/uncertainty but cannot alone pass those checks. Resolution requires method `ffprobe` with actual probe evidence; the gate independently probes the current file and requires video, audio, positive duration and 720p dimensions; identity needs inspected reference comparisons. Voice continuity without a selected voice or comparison clip remains uncertain unless the explicit first-take baseline procedure above applies. Include `correction` for failures as concrete prompt direction for the next take; approved batches regenerate automatically from it. Never claim full coverage from sampled frames.

CLI gate exits 0 only for ready_for_edit, 2 for rejected/needs_evidence, and nonzero for malformed/stale records or failed media validation. A gate pass never grants final export approval.

## Template validation
The shared setup has offline regression tests in `File/scripts/test_agentic_pipeline.py`; run `python3 -m unittest discover -s File/scripts -p 'test_*.py'` to include existing Kie safeguards. Tests use synthetic fixtures, not production-quality evidence. Keep master brief/memory/edit notes blank; project runs record their own inputs, reviewer IDs, outcomes and approvals. Shared files updated together: root AGENTS.md, this workflow, WORKFLOW.md, SKILLS.md, File/agents.md, File/README.md, the production-director and UGC skills, and the compiler/tests.

## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.
