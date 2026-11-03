# Local skill catalog

This template includes the six local workflow skills plus nine adapted skills from the supplied older template. Open this folder in Codex; the hidden .agents/skills directory provides discovery. The modules guide the current agent; File/docs/AGENTIC_WORKFLOW.md requires automatic independent review subagents.

## Main workflow

| Skill | Purpose |
| --- | --- |
| $production-director | Coordinate local inputs, optional generation, review and editing |
| $premiere-edit | Operate the existing Premiere project through the user's automation tools |
| $ugc-director | Route UGC direction and its detailed modules |
| $animation-director | Route animation direction and its detailed modules |
| $broll-director | Plan source-linked realistic action/product footage |
| $project-memory | Maintain File/memory.md and the editing handoff |

## Added modules

| Skill | Purpose and adaptation |
| --- | --- |
| $animation-production-desk | Local stage/dependency records and first-three pilot gate; no desk API/dashboard |
| $animation-script-planning | Unique prompt blocks, source-linked characters/locations and storyboard packages |
| $pixar-animation-director | Detailed original animated-feature direction and six preserved craft references |
| $iphone-photo-look | Detailed smartphone-photo appearance, color/optics recipes and review rubric; practical full-hand framing replaces mandatory 30% headroom |
| $ugc-video-pipeline | Detailed local identity/avatar/sample/clip sequence and source-preserving direction |
| $ugc-avatar-voice | Original language/accent/voice design and binding plan; no unimplemented registration claims |
| $image-review-validation | Actual still/reference comparison with uncertainty and human acceptance recorded separately |
| $kie-generation-runner | Documents the available local preview/submit/status helper and its real limits |
| $frame-mcp-integration | Historical skill name retained; now maps to local files and existing Premiere MCP tools |

## Local paths

- Assets/ contains original source, references and downloaded outputs.
- File/production.md can contain source-linked directing notes and named kie-prompt blocks.
- File/production-plan.json can track proposed technical settings, stable asset IDs, selected take paths and dependencies. This is planning metadata, not an automatically executed job catalog.
- File/generation/ contains actual helper previews, operation state and receipt snapshots.
- File/reviews/ can contain versioned still-review evidence and human decisions.
- File/memory.md and File/edit_notes.md contain resumable decisions and editing status.

These supporting files remain inside the hidden File support folders or are created only when needed. Premiere/After Effects project files remain visible.

## What was intentionally changed

The imported skills no longer require the old Frame app/server, dashboard, desk.py, studio.py, planning.py, ugc.py or old scripts/kie.py. They do not claim nonexistent tools were installed.

Old fixed model aliases/prices, automatic voice preparation, ASR/video verification, two-retry/252-credit permissions and forced warm casts/headroom are not carried over as universal operating rules. Current user preferences, actual model contracts, concrete authorization and the available local tool implementation govern execution.

The detailed Pixar-inspired reference files and the substantive iPhone photographic guidance were retained. Imported technical/product/source claims are reference material, not newly verified current facts or live qualification.

The local Kie helper still supports Market-task preview, one attempted submission per preview and known-task status. It also uploads selected references to Kie temporary storage. It does not gain voice/character registration, chat planner, downloader or orphan-task linking command merely because a skill discusses them. Such actions require an actual separately available supported integration.

No secrets were copied. No paid request, external account setup, Premiere mutation or render was performed when adding these skills.

Agentic execution: see [AGENTIC_WORKFLOW.md](AGENTIC_WORKFLOW.md) for the orchestration loop, offline compiler, review packets and gate. The Kie helper retains its existing limited scope.

For automatic talking-avatar batches and resumable review dispatch, follow [batch automation](BATCH_AUTOMATION.md). Use `File/scripts/production_runner.py`; routine commands are performed by the agent.

## Supplied-video farm
[EDIT_FARM.md](EDIT_FARM.md) defines the default spoken-video editing route without a separate script or generation key. `edit_farm.py` tracks intake, tasks, reviewed versions and delivery; `premiere_writer.py` coordinates one project writer; `edit_decisions.py` validates source-linked cut decisions. The production-director/premiere-edit/project-memory skills route and operate the farm. Runtime records under File/edit_farm/ belong only to active project copies.

## Animation farm
[ANIMATION_FARM.md](ANIMATION_FARM.md) coordinates story, design/continuity and performance specialists with one Premiere writer and independent reviews. `animation_review.py` supplies mode-specific shot packets/gates. General animation generation/assembly stages remain agent-coordinated rather than implemented by the talking-avatar batch runner.

Automatic correction: follow [the repair loop](AUTO_REPAIR.md). Fixable reviewer findings trigger targeted authorized repairs, fresh independent review and continuation, preserving the same characters/scenes. Routine fixes do not require another “fix it” prompt. Uncovered paid scope and final-version export retain their approval requirements.

For automatic paid fixes, approve a [project repair allowance](PAID_REPAIRS.md) once, including a total repair-credit limit, attempt limit, assets/references and models. The agent uses repair_runner.py to bind and submit eligible corrected payloads without per-fix approval, then reviews each result before another attempt. The standing default is 1000 additional repair credits per project, with two corrective attempts per asset; no live grant or credentials are included.

Standing repair setting: **1000 additional Kie credits per project**. The coordinator applies this allowance to the selected repair scope without repeating the budget question. See File/repair_defaults.json; an active project records its own asset/model bindings and authorization evidence.
