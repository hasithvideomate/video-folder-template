---
name: premiere-edit
description: Operate the user's Premiere automation MCP tools on the existing local project, following the supplied A-roll/B-roll/UGC workflow, source-accurate editing, review and approved final export.
metadata:
  version: "1.2.0"
---

# Premiere automation editor

For local desktop/Premiere integration details load ../frame-mcp-integration/SKILL.md. Its historical name does not imply a Frame app or server dependency.

Read root AGENTS.md, File/docs/PREMIERE_AUTOMATION.md, File/project_brief.md, File/memory.md, File/edit_notes.md and File/agents.md. File/agents.md is the full user-supplied editing workflow; follow it, including its review and export rules.

## Connect and inspect
Use the existing connected Premiere MCP integration. Discover registered operations with get_capabilities, bounded keywords and tool_limit: 10. Read exact schemas, verify the chosen Premiere bridge, inspect the actual saved project/sequence and obtain fresh item/clip IDs. Static discovery is not host readiness. Do not invent tools or silently change backends.

Use expected_project_path for supporting CEP tools and the appropriate UXP identities for UXP. Follow paginated reads before declaring the timeline fully inspected. Import local media before placing it. Keep host-state reads and mutations sequential.

## Edit
Use the existing File/Project Template.prproj or the user's current established project; do not replace it. Preserve source media and keep suitable working sequences within that project.

Extract and verify the supplied script into Assets/, or use a verified verbatim recording transcript when no script exists. Use actual recording/transcript evidence to locate complete takes. Changing a transcript cannot repair words that were spoken incorrectly. Cut source-accurate A-roll with natural pacing, then use suitable supplied or authorized generated B-roll.

Follow the current no-added-caption/text rule and the workflow's safe-zone, labels and issue-timecode rules. Use the actual supplied safe-zone image; if missing, continue unaffected work but do not claim its check passed. Do not import a reference-only clip as editable material without authorization.

Use supported typed preview/apply routes and required unchanged single-use tokens. Inspect results before dependent steps. Unknown tool outcomes require recovery inspection, not blind replay or unsafe scripting.

## Verify, review and export
Re-read affected and unaffected timeline state. Inspect actual frames for visual claims and playback/audio for temporal or sound claims. Save the existing project, record version and issue timecodes, and present the edit for user review.

Apply authorized revisions without repeated routine confirmations. Final export follows the explicit current-version review/approval in File/agents.md. Hide editing guides, export to a new versioned path under Exports/, then verify the actual rendered file. Queue acceptance does not mean completion.

Update File/edit_notes.md and File/memory.md. If host tools are unavailable, prepare script/edit decisions locally and report the missing capability without claiming timeline edits.

Optional paid generation is a separate user-authorized operation through ../production-director/SKILL.md; it is not required for editing supplied footage.

Instruction version: premiere-edit@1.2.0.


## Required automatic pacing pass
For UGC/talking-head footage, read File/docs/AUTO_CUT.md and File/pacing_policy.json. Trim clip heads/tails, tighten unnecessary pauses and inspect the combined silence at every clip join. Use actual transcript/audio evidence, source-to-timeline mapping and supported typed previews; distinguish empty-track gaps from silence inside footage. Preserve speech, meaningful breaths and gestures; keep A/V linked and framing fixed. Listen/watch every cut at normal speed, recheck actual timeline readback and delegate assembled pacing review when supported. Generation review and an edit-ready handoff do not establish that pacing edits were performed.

## Agent-farm ownership and completion
For supplied spoken video, use File/docs/EDIT_FARM.md. Only the coordinator operates Premiere. Claim the project-wide writer, journal intended mutations, archive actual receipts/readbacks and block new mutations on unknown outcomes. Independent workers inspect local evidence only. Validate the EDL before applying its intended cuts and again when recording the actual saved edit. Source reports cannot substitute for assembled QA; verify the actual approved exported file and independent delivery review before returning a finished video. Preserve current-version export approval.
