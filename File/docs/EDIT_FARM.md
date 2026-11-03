# Supplied-video agent farm

This is the default route when the user supplies spoken video and wants an edited final video in Premiere Pro. It does not require an avatar, a generation prompt, a Kie key, or a separately written script. Use the generation workflow only when new media is actually requested. The user's instruction to edit authorizes routine reversible cutting, pacing fixes, supplied B-roll placement and review; existing reviewed-version final-export approval remains required.

The coordinator operates `File/scripts/edit_farm.py`, delegates specialist tasks through T3, and performs actual Premiere operations through the installed MCP bridge. The helper is a durable local ledger and validator, not a replacement for those tools or an installed background daemon. A completed task or a passing unit test is not proof of an edited video. Do not request a live project, media or Premiere connection just to update this template's reusable rules.

## Roles and ownership

- **Coordinator and Premiere writer:** the parent thread. It chooses the input scope, captures host evidence, reconciles specialist findings, verifies edit decisions, operates Premiere, saves versions, records receipts and maintains project memory. It is the only agent allowed to call Premiere, including selection, playback and state-dependent reads. Reviewers request needed host evidence from it.
- **Dialogue specialist:** transcribes recording truth, maps exact spoken occurrences to the supplied script when present, identifies retakes/false starts, and reports ambiguity without inventing words or approval.
- **Audio and pacing specialist:** analyzes actual sound and pause candidates, clip edges, breaths, clipping/noise and cross-clip rhythm. It proposes source-time edits; it cannot delete speech or apply timeline changes.
- **Visual specialist:** inspects source visuals, usable B-roll, reference-only footage, continuity, gestures and visible defects. It reports the difference between sampled-image and temporal evidence.
- **Independent assembled-edit reviewer:** a fresh delegated task after the actual timeline is edited and saved. It checks the full sequence and every join against the sources and edit decisions. Source-review passes cannot substitute for this stage.
- **Independent delivery reviewer:** a fresh delegated task after the approved render exists and technical checks pass. It checks the exported file itself against the reviewed edit, including speech, ending, A/V sync, text/guide absence and visuals.

Run up to three source specialists in parallel on immutable local evidence. They write only their assigned reports/supporting artifacts. Only the coordinator changes shared state, memory, approval records or Premiere. Dispatch each queued request using its stable clientRequestId and current provider/model/options from orchestrator_capabilities. Save/bind the actual returned taskId and childThreadId. A lost dispatch is retried with the same key; an evidence re-review is a fresh task/round with previous findings included. Do not create top-level conversations for these jobs.

## Intake and recording authority

The agent writes a manifest from the user-supplied files and brief. Example shape:

```json
{
  "id": "edit-v1",
  "producer_id": "ACTUAL_PARENT_THREAD_ID",
  "project": "File/Project Template.prproj",
  "intent": "Clean natural edit; preserve substantive speech and ending",
  "sources": [
    {"id": "a01", "path": "Assets/source.mov", "role": "primary"},
    {"id": "b01", "path": "Assets/product.mp4", "role": "broll"},
    {"id": "r01", "path": "Assets/style-reference.mp4", "role": "reference"}
  ]
}
```

An optional `script` path selects `sourceAuthority: supplied_script`. Otherwise the ledger selects `verified_recording`. Preserve substantive recording wording, language, order and ending; remove only well-established retakes, false starts/filler and unnecessary silence within the requested editing scope. A recording transcript is recording truth, not a fictional user-approved script. Keep the full verbatim transcript separate from script alignment and proposed selections. Resolve meaningful ambiguity rather than silently changing the message.

Source IDs and original order are explicit. Intake fingerprints each file and captures duration, streams, dimensions and rational timebase. Supplied footage may be 1080p/4K or another source format: the 720p rule applies to new generated videos, not to rewriting originals. Keep sequence/delivery settings tied to the actual project and brief. Reference-only sources cannot appear in the cut. The initial helper supports timed video/audio assets and primary spoken video; still-image guides/references use the existing manual asset-intake workflow, and silent/non-dialogue edits route to the appropriate director skill rather than fabricating transcripts.

```sh
python3 File/scripts/edit_farm.py start --manifest File/jobs/edit-v1.json
python3 File/scripts/edit_farm.py status --run edit-v1
```

Start is offline apart from local ffprobe. It creates three source-analysis requests under `File/edit_farm/runs/EDIT_ID/`. It does not transcribe, generate, spend or mutate Premiere by itself. For long recordings, index segments with exact source offsets and coverage; review all relevant spans rather than treating a fixed number of stills as full coverage. Do not download ASR models or use paid services silently. Capture available Premiere transcript evidence through the writer or use an actually installed supported local recognizer; uncertain words still require listening.

## Dispatch and collect specialists

Read each request JSON, discover the inherited T3 model/options and call delegate_task. Save its actual structured result, then bind immediately:

```sh
python3 File/scripts/edit_farm.py bind --run edit-v1 --task dialogue-r1 --result File/edit_farm/runs/edit-v1/dialogue-dispatch.json
# On actual child completion, save the separate task_status result:
python3 File/scripts/edit_farm.py collect --run edit-v1 --task dialogue-r1 --result File/edit_farm/runs/edit-v1/dialogue-completion.json
```

Source report JSON: `packet_hash`, actual child-thread `reviewer_id`, `status: complete | blocked`, nonempty `evidence`, and `findings`. Include concrete artifact paths, source IDs/times, methods, coverage and uncertainty. Findings are proposals, not permission to operate Premiere. A complete analysis can identify defects; the coordinator must resolve them in the edit and assembled review. A blocked analysis cannot advance to editing. Collect terminal failed/cancelled/interrupted task-status results too: the ledger preserves the transport failure as blocked evidence, then permits a new bounded round after the prerequisite is fixed. Never present a failed task as a completed analysis. Late terminal results from obsolete tasks are archived without changing the current edit/render phase. The helper checks task provenance and report fingerprints, not the semantic truth of an agent's claims.

For genuinely new evidence, `rereview --run EDIT_ID --task TASK_KEY --evidence PATH` creates a new request and preserves prior findings, with at most three total rounds per role/version. Existing running/completed round bindings cannot be overwritten. Do not repeat an active task or quietly relabel unavailable evidence as passed.

## One Premiere writer across all runs

Before host work, follow PREMIERE_AUTOMATION.md: discover the needed operations, verify the selected CEP/UXP bridge, inspect the actual saved project/sequence and capture fresh IDs. Claim ownership:

```sh
python3 File/scripts/edit_farm.py claim-writer --run edit-v1 --caller-id ACTUAL_PARENT_THREAD_ID
python3 File/scripts/edit_farm.py begin-operation --run edit-v1 --caller-id ACTUAL_PARENT_THREAD_ID --intent File/edit_farm/runs/edit-v1/intent-001.json
# Invoke the exact intended supported Premiere tool, then inspect fresh readback:
python3 File/scripts/edit_farm.py resolve-operation --run edit-v1 --caller-id ACTUAL_PARENT_THREAD_ID --operation RETURNED_OPERATION_ID --receipt File/edit_farm/runs/edit-v1/receipt-001.json --snapshot File/edit_farm/runs/edit-v1/readback-001.json --outcome verified
```

The writer record is keyed by canonical saved-project path under File/edit_farm/writers. Ownership carries run ID, owner ID and a monotonically increasing epoch. Two runs cannot claim different writers for the same project. Intents and resolution evidence are archived before state changes. There is no time-based takeover. Every writer command requires `--caller-id` from the invoking thread, which must match the coordinator; do not copy an owner ID from the ledger to impersonate it. Read-only state checks do not claim ownership. An intentional coordinator change requires the current owner to reconcile/release and the new owner to start an explicit new run; no implicit same-run transfer is supported. This is **cooperative coordination**; it does not install a permission hook into Premiere or block a human/nonparticipating tool.

Journal a mutation before dispatch, use actual typed tool previews and unchanged confirmation tokens, then resolve only the exact pending operation. `unknown` preserves the block and is not a failed/no-effect result. While pending, the same writer may perform necessary read-only recovery inspection, but no new edits, playback/selection changes or export. Never replay a consumed apply token. `no_effect` requires positive evidence of no host change. `release-writer` works only with no pending operation; do not delete lock files to take over.

Premiere can replace the project file atomically on save. To reconcile that expected replacement, the pending intent must contain `kind: save_project`, `expected_project_path` (canonical absolute path), and actual `expected_project_id`. The fresh snapshot envelope must contain matching `project_path`, `project_id`, `saved: true`, and nonempty `host_evidence` containing the actual tool readback. Only a verified matching save may update the local file identity; unrelated replacements remain blocked. Preserve actual receipts inside the envelope. These fields record the writer's checked evidence; the helper cannot authenticate a fabricated host report.

## Source-linked edit decisions

Apply the existing File/agents.md and AUTO_CUT.md workflows, including natural pacing, clip-edge trimming, every combined pause at a join, all-track gap inspection, full-hand gesture continuity, no added captions and no zoom/reframing. Use live source-to-timeline mapping; never apply source seconds as timeline seconds. Do not round fractional frame rates to use an integer-only ripple tool. Re-read/remap after structural edits.

`File/scripts/edit_decisions.py` validates the decision contract. Its module docstring is the exact schema. The coordinator assembles it from actual specialist evidence and host inspection:

- Each primary transcript snapshot has source_id, media_sha256, revision, mode, timed words with unique occurrence IDs, and ending_word_ids. Preserve exact rational times as strings, such as `30000/1001` for frame rate and `12.08` or `302/25` for seconds. Do not identify repeated phrases by their text alone.
- In verified_recording mode, the snapshot represents the full verified recording words. In supplied_script mode, use a separate approved-script-to-recording alignment snapshot containing every required script occurrence; preserve the full recording transcript separately so off-script words/retakes cannot disappear from the evidence. Verify the alignment against the actual approved script; the structural validator cannot establish this semantic mapping.
- A plan contains version, mode, frame_rate, transcript descriptors, retained source/timeline ranges and explicit omissions. Ranges bind media hashes, sourceIn/sourceOut/timelineIn/timelineOut, a concrete reason, linked_av:true and the exact word_ids contained in each range. B-roll has no dialogue word IDs and may overlap A-roll; reference-only assets are refused.
- Recording-only retake/false_start/filler omissions require a fingerprinted evidence record binding exact source hash, transcript hash/revision and occurrence IDs, with a concrete reason. `approved_by`/`approval_id` here record the coordinator's editorial acceptance under the existing routine-cut authorization; they do not require per-word user approval and do not grant export/spending permission. Substantive omissions remain outside that default scope. Supplied-script aligned words and required endings cannot be omitted.

The validator refuses truncated words, replayed occurrences, omitted/unapproved words, changed order, out-of-bounds ranges, source/timeline duration mismatch, stale evidence and missing endings. Passing means structurally valid, not verified speech, motion or pacing. The coordinator resolves actual uncertainty through listening/playback and the independent assembled reviewer.

## Record the actual saved edit

After editing, verify fresh timeline readback, A/V synchronization and every join, save the existing project, and resolve all pending writer operations. Write a local record JSON with:

- `producer_id`, `project`, current `writer_epoch`, actual `sequence_id`, unique `edit_version`.
- `transcripts`: source ID to `{path, sha256, revision}` for every primary source; `decisions`: validated plan JSON path.
- `snapshot`: captured current timeline readback JSON path; `operation_receipts`: nonempty list of actual host receipt paths.
- `delivery`: actual intended `width`, `height`, rational-string `frame_rate`, `audio_required: true`, and a new versioned `.mp4` `output` path under Exports/. Include any required codec/preset/audio settings in the record and verify them through the supported delivery tools; do not substitute a guessed preset.

```sh
python3 File/scripts/edit_farm.py record-edit --run edit-v1 --record File/edit_farm/runs/edit-v1/edit-v1.json
```

This validates the EDL, fingerprints the saved project and edit evidence, creates an edit hash and queues a fresh assembled reviewer. Word/audio checks require listening; joins/sync require synchronized audiovisual evidence; visual checks require temporal visual evidence. All passes require full-sequence coverage. The reviewer must account for every generated join ID, including B-roll boundaries. Each packet provides exact rational timeline boundary times. Sampled frames or ASR alone cannot pass temporal checks.

Quality report JSON: `packet_hash`, actual `reviewer_id`, `reviewed_join_ids` exactly matching the packet, and `checks` with every key in packet.checks. Each check contains `status: pass | fail | uncertain`, nonempty `evidence`, `method`, and `coverage`. Allowed pass methods are direct_audio/direct_av for wording and sound, direct_av for pacing and sync, and direct_video/direct_av for visuals/text/camera. Pass coverage is `full_sequence`. Include timestamps, tools/files and unavailable checks honestly.

A fail routes to revision; uncertainty routes to new evidence. The coordinator fixes routine reversible edit defects automatically, records a new version and requests fresh independent review. Prior versions/reports remain. A changed project, decision plan, transcript, policy or review evidence invalidates affected completion; do not reuse stale approval. Numeric clip-generation checks do not imply the assembled edit passes.

## Approval, rendering and verified delivery

A full assembled-review pass moves to `awaiting_user_review`. Present the concrete saved version for the existing required user approval. Do not ask before there is a reviewable result. Draft renders still require the established draft-render authorization; supported playback/captured evidence may be used without inventing a draft-export approval.

```sh
python3 File/scripts/edit_farm.py approve-export --run edit-v1 --edit-hash EXACT_REVIEWED_HASH --evidence-ref ACTUAL_USER_APPROVAL_REFERENCE
```

Approval binds the edit hash and delivery settings, not just a version label. Re-inspect the live sequence immediately before export; the saved file hash alone cannot detect unsaved host edits. If anything changed, record/review the new version. No pending or unknown writer operation may proceed to export. Use begin-operation with `kind: export`, the exact supported invocation and actual expected project/sequence identities. The journaled export enters `export_submitting` before the command returns; only then invoke the tool once. Inspect its receipt and fresh host state, then resolve the invocation when its acceptance/outcome is positively known. Verified acceptance records `render_pending` directly. The farm flushes its state file and directory entries before clearing the writer journal. A crash between the writer journal and run-state update remains fenced in `export_submitting`; do not submit again. Reconcile the existing operation through `render-started` with the exact receipt already archived by the writer. Verified `no_effect` returns to export authorization and archives the attempt. An accepted asynchronous render remains pending even though the invocation was verified.

```sh
python3 File/scripts/edit_farm.py render-started --run edit-v1 --receipt File/edit_farm/runs/edit-v1/render-start.json
# Wait for the actual existing render operation; never submit a replacement merely because it is slow.
python3 File/scripts/edit_farm.py verify-render --run edit-v1 --receipt File/edit_farm/runs/edit-v1/render-completion.json
```

`render-started` is an idempotent reconciliation of an already journaled export, not permission for an untracked submission. It checks the exact acceptance receipt against the writer history; a confirmed no-effect resolution can also be reconciled this way. It does not claim rendering success. `verify-render` requires the expected file, correct video/audio streams, exact dimensions/timebase, duration within two frames of the approved EDL, and a successful full decode. It fingerprints the output and queues a separate delivery reviewer. Use supported Premiere delivery/conformance verification for any additional brief requirements such as codec, loudness or preset. Technical checks are separate from content checks.

If the actual host confirms failure/cancellation, or confirms completion but the output fails verification, record that evidence rather than retrying an unknown operation:

```sh
python3 File/scripts/edit_farm.py reconcile-render-failure --run edit-v1 --caller-id ACTUAL_PARENT_THREAD_ID --evidence File/edit_farm/runs/edit-v1/render-failure.json
```

The evidence JSON requires exact `operation_id`, `edit_hash`, `output`, `status: failed | cancelled | invalid_output`, `host_terminal: true`, nonempty actual `host_evidence`, and a concrete `reason`. A timeout, missing file or decode failure alone does not establish that the host has stopped. Reconcile any pending writer operation first. This archives the attempt and any failed output fingerprint without deleting the file, then enters `render_failed`. Fix the cause and record a new version with a fresh output path, review and export approval. Existing failures remain in history. If interrupted after archiving failure evidence, retry with the identical evidence to finish the transition; conflicting evidence cannot replace the archive. Unknown outcomes continue blocking resubmission.

Only the exact-file independent content pass sets `delivered_verified`. Return the final video path, existing saved Premiere project/sequence, concise work summary and any real limits. Recheck the ledger immediately before delivery. Never report a queued job, an existing filename, or successful ffprobe as a completed reviewed film. Release idle writer ownership after delivery and update project memory/edit notes with the run path, version/hash, actual task/operation IDs, approval reference and verified output.

## Runtime boundaries

Source specialists can work in parallel; Premiere operations stay serialized. Worker failure, unavailable transcription/playback or an unknown mutation is a specific blocker to resolve, not a reason to fabricate completion. Preserve task IDs and receipts on resume. No recurring timer is installed on the master template. If the user later requests unattended continuation for an actual project, configure an explicit T3 schedule with the run ID and the same continuation loop; do not copy schedule IDs or filled state into the template.

This implementation validates structured evidence and recorded authority. It does not independently authenticate a model's report, grant user consent, prove that a host receipt is truthful, or infer semantic correctness from hashes. Actual tool evidence, direct review and the single-writer operating contract remain necessary.
