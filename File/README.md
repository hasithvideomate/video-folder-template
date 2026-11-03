# Local production + Premiere automation template

Duplicate this folder for each project and open the copy in Codex. This works from local files with your Premiere automation agent. No website, login, database or hosted production service is required.

Start with the practical [START HERE SOP](START_HERE.md).

## Start
1. Put your video and any supplied references in Assets/. A separate script is optional for editing existing footage.
2. Tell the agent the intended edit; it records the brief and asks only for genuinely missing choices.
3. Open File/Project Template.prproj in Premiere. Keep existing linked media paths intact.
4. Connect the Premiere automation MCP integration to Codex.
5. Ask: **Run the edit farm on my supplied video. Clean up the pacing, review it, and finish it in Premiere.**
6. Codex follows your editing workflow, keeps File/memory.md updated, presents the result for review and exports the approved edit.

Editing existing footage needs no Kie key. Optional image/video generation uses your own Kie API key privately in .env; see [Kie setup](docs/KIE_SETUP.md).

## Folder layout
Only Assets/, File/ and Exports/ are visible at the top level in normal Finder view. Supporting guides, scripts, notes and memory live inside File/. Codex discovery files remain hidden at the root; AGENTS.md stays there so Codex can load instructions automatically. Workspace Explorer exclusions also hide setup files. Inside File/, the START_HERE guide and the .prproj/.aep project files are visible; supporting files and folders are hidden but remain available to Codex at their existing paths.

| Path | Purpose |
| --- | --- |
| AGENTS.md | Local Codex entry instructions |
| .agents/skills/ | Fifteen discoverable production/editing/review skills |
| Assets/ | Original scripts, footage, references and generated media |
| File/agents.md | Your supplied Premiere editing workflow |
| File/Project Template.prproj | Existing Premiere project starter |
| File/Project Template.aep | Existing optional After Effects project starter |
| File/project_brief.md | Current project and creative choices |
| File/edit_notes.md | Timeline changes, issues and review/export status |
| File/generation/ | Local Kie previews, operations and receipt history, created on demand |
| File/memory.md | This project's resumable memory; no remote project ID needed |
| Exports/ | Approved final exports and explicitly requested labeled drafts |
| .env.example | Blank optional Kie configuration |
| File/scripts/kie_tasks.py | Optional local Market-task preview, submit and status helper |

The .aep file is supplied, not automatically edited. Capability discovery must establish which Premiere/After Effects operations are actually available. The safe-zone image is not included in the original template; supply it when its checks are needed.

## Skills and examples
Detailed imported modules and local adaptations are listed in [the skill catalog](docs/SKILLS.md).

- $production-director — coordinate the full local workflow.
- $premiere-edit — edit the existing Premiere project.
- $ugc-director — preserve dialogue, compose avatars and plan UGC clips.
- $animation-director — plan characters, continuity and storyboards.
- $broll-director — plan physical actions and supporting footage.
- $project-memory — record decisions and the next step in File/memory.md.

Examples:
- Use $premiere-edit to cut my supplied A-roll to the approved script and add matching supplied B-roll.
- Use $ugc-director to draft three talking-head prompts; do not submit generation.
- Use $animation-director to prepare the first three storyboards for review.
- Use $project-memory to save a handoff for the next Codex session.

## Share the clean template
The provided ZIP includes hidden skills and empty media/export folders, with no API key or live project history. Use a fresh copy when sharing. Filled project copies can contain private scripts, media, notes and credentials; Git ignore rules do not sanitize a manually created ZIP.

[Full workflow](docs/WORKFLOW.md) · [Premiere automation](docs/PREMIERE_AUTOMATION.md) · [Kie setup](docs/KIE_SETUP.md)


## Agentic production
Start with “Run the agentic workflow for the approved script and selected reference.” See [docs/AGENTIC_WORKFLOW.md](docs/AGENTIC_WORKFLOW.md). Codex handles routine steps and delegates independent clip review; exact paid scope and final-version export approval remain required. The talking-avatar compiler/review gate is `scripts/agentic_pipeline.py`. No background daemon is installed.

For automatic talking-avatar batches and resumable review dispatch, follow [batch automation](docs/BATCH_AUTOMATION.md). Use `File/scripts/production_runner.py`; routine commands are performed by the agent.

## Supplied video to final delivery
The [edit farm](docs/EDIT_FARM.md) coordinates dialogue, audio/pacing and visual specialists; one Premiere writer applies verified cuts. Separate agents review the assembled edit and the actual export. Runtime phases distinguish analysis, editing, user review, rendering and verified delivery. The existing final-version export approval remains; no paid generation is needed to edit supplied footage.

## Animation
The [animation farm](docs/ANIMATION_FARM.md) covers characters, animated objects/products and silent or narrated stories. Review each shot for action, continuity, motion and protected holds, then review the full edit and actual export. The executable animation shot-review helper supports silent, SFX, narration and dialogue; general animation batches remain agent-coordinated.

Automatic correction: follow [the repair loop](docs/AUTO_REPAIR.md). Fixable reviewer findings trigger targeted authorized repairs, fresh independent review and continuation, preserving the same characters/scenes. Routine fixes do not require another “fix it” prompt. Uncovered paid scope and final-version export retain their approval requirements.

For automatic paid fixes, approve a [project repair allowance](docs/PAID_REPAIRS.md) once, including a total repair-credit limit, attempt limit, assets/references and models. The agent uses repair_runner.py to bind and submit eligible corrected payloads without per-fix approval, then reviews each result before another attempt. The standing default is 1000 additional repair credits per project, with two corrective attempts per asset; no live grant or credentials are included.

Standing repair setting: **1000 additional Kie credits per project**. The coordinator applies this allowance to the selected repair scope without repeating the budget question. See File/repair_defaults.json; an active project records its own asset/model bindings and authorization evidence.
