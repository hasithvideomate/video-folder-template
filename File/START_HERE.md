# Bot Farm — Start Here

This folder is the reusable setup for editing supplied videos, generating UGC, and coordinating animation in T3 Code with Premiere Pro. The agent handles job records, specialist dispatch, routine review and reversible edits. You do not need to run its Python commands manually.

## 1. Create your project

Duplicate the entire bot-farm folder and rename the copy for your project. Keep hidden files, especially `.agents/` and `AGENTS.md`. Keep this clean starter for future projects.

Put your inputs into `Assets/`:

| Mode | Inputs |
| --- | --- |
| Edit supplied video | Original clips; a separate script is optional |
| Generate UGC | Approved script and selected avatar; selected voice reference if available |
| Animation | Story/script or brief, selected design/style references, existing boards/clips if available |

Keep source originals unchanged. Final verified renders go into `Exports/`.

## 2. Open your tools

- Open the copied project folder in T3 Code with agent delegation available.
- Open that copy's existing `File/Project Template.prproj` in Premiere Pro.
- Start your installed Premiere MCP bridge and keep Premiere/T3 available while work runs. The coordinator verifies actual capabilities and the live project before editing.
- Have Python 3.10+ and working ffmpeg/ffprobe installed. The agent checks prerequisites before generation. No installers, paid tests or recurring services are run by opening this folder.
- Only for new paid generation: privately configure this copy's root `.env` according to [Kie setup](docs/KIE_SETUP.md). Never paste your key into chat. Supplied-video editing needs no Kie key.

The package includes starter projects, instructions, skills and local helpers. It does not install Adobe, the Premiere MCP bridge, T3 Code, ASR models or generation accounts.

## 3. Paste this in the project conversation

Replace the bracketed choices with your brief. Do not paste credentials.

```text
Use $production-director to run this project's agent farm.

Mode: [edit supplied video / generate UGC / animation]
Inputs: Assets/
Goal: [describe the finished video]
Format: [9:16 / 16:9]
Target duration: [duration or preserve the complete content]
Language: [language or no speech]

Read the project instructions, brief, memory and edit notes.
Inspect the actual inputs and existing Premiere project.
Prepare the brief and required job records yourself.
Use the appropriate UGC, supplied-video or animation workflow.
Delegate relevant specialists and independent reviewers automatically.

Review each generated clip immediately after download.
Fix routine reversible editing issues and unnecessary pauses.
Preserve dialogue, story order and the complete ending.
For animation, protect deliberate holds, reactions and action completion.
Follow the saved camera, captions and generation-resolution rules.

Continue through assembled-edit review without routine confirmations.
Present exact paid requests before spending.
Present the reviewed final version for export approval.
Verify the actual exported file before reporting delivery.
Report concrete blockers honestly; do not mark unavailable checks passed.
```

## 4. While it works

The coordinator creates the run records, dispatches reviewers, tracks completed work and remains the sole Premiere writer. You do not need to start each reviewer or wait for every generated clip before review begins. Answer only genuinely missing creative/input choices and the retained exact spending/final-version export approvals.

Paid authorization covers the listed payloads and reservations; it does not authorize unspecified regeneration. Routine review is automatic. Final export requires approval of the concrete reviewed version. Keep the machine and necessary tools available; this is agent-driven execution, not an installed always-on bot.

## 5. Resume or check progress

Resume in the same project conversation, or a new conversation opened on the same project copy:

```text
Continue the agent farm from saved state. Read the brief, memory and
edit notes. Inspect existing tasks, receipts and Premiere state first.
Reuse completed work and reconcile unknown operations before retrying.
Do not duplicate generation, review dispatch or exports.
```

For a status-only check:

```text
Show the current farm stage, completed clips/reviews, blockers,
known pending operations and next action. Do not submit new work.
```

If a bridge or evidence capability is missing, the agent should identify the exact prerequisite and continue unaffected local work. Do not delete run records to force a retry.

## 6. Receive the deliverables

- `Exports/`: the verified final video after current-version export approval.
- `File/Project Template.prproj`: the existing editable Premiere project, saved by the writer.
- `File/edit_notes.md` and `File/memory.md`: current sequence/version, review evidence and handoff.

A queued export or an existing filename is not verified delivery.

## What is implemented

- **UGC:** resumable talking-avatar generation/download/review requests, independent review and an editing handoff; the coordinating agent performs Premiere editing.
- **Supplied spoken video:** source-analysis tasks, source-linked cut validation, durable writer ownership, assembled review, export tracking and actual-file delivery review.
- **Animation:** story/design/performance workflow and executable shot-review packets/gates for silent action, SFX, narration and dialogue. General animation production/assembly stages remain agent-coordinated; they do not have the UGC runner's full batch state machine.

Current rules include generated 720p, no added captions/text, locked framing, and stationary reference scenery. Animation protects intentional holds instead of blindly applying UGC silence thresholds.

## Reference guides

[Workflow overview](docs/WORKFLOW.md) · [Supplied-video farm](docs/EDIT_FARM.md) · [UGC batch automation](docs/BATCH_AUTOMATION.md) · [Animation farm](docs/ANIMATION_FARM.md) · [Premiere connection](docs/PREMIERE_AUTOMATION.md)

Offline validation: the packaged helper suite has 157 passing tests. These verify local contracts and recovery behavior; they do not certify live provider/Premiere execution or audiovisual quality on your footage.

Automatic correction: follow [the repair loop](docs/AUTO_REPAIR.md). Fixable reviewer findings trigger targeted authorized repairs, fresh independent review and continuation, preserving the same characters/scenes. Routine fixes do not require another “fix it” prompt. Uncovered paid scope and final-version export retain their approval requirements.

For automatic paid fixes, approve a [project repair allowance](docs/PAID_REPAIRS.md) once, including a total repair-credit limit, attempt limit, assets/references and models. The agent uses repair_runner.py to bind and submit eligible corrected payloads without per-fix approval, then reviews each result before another attempt. The standing default is 1000 additional repair credits per project, with two corrective attempts per asset; no live grant or credentials are included.

Standing repair setting: **1000 additional Kie credits per project**. The coordinator applies this allowance to the selected repair scope without repeating the budget question. See File/repair_defaults.json; an active project records its own asset/model bindings and authorization evidence.
