# Your Premiere automation connection

Use the existing Premiere MCP integration, not browser-driven application controls. This folder contains skills and starter projects; it does not install the Premiere bridge or copy its machine-specific configuration.

1. Have Premiere open and connect the user's existing MCP automation server to Codex.
2. Start with get_capabilities using a few relevant keywords and tool_limit: 10. Catalog availability does not prove a live host is connected.
3. Read the exact schemas and verify_premiere_connection for the selected CEP/UXP backend, or the registered equivalent. Do not switch backends silently.
4. Inspect the actual saved project, active sequence, items, tracks and clips. Resolve IDs again after structural changes. Follow paginated results before claiming complete coverage.
5. For CEP tools that support expected_project_path, bind it to the actual local saved project; use the UXP identity guards for UXP instead.
6. Prefer supported typed previews/application routes. Compound edits can use preview_edit_plan then apply_edit_plan with the unchanged issued token and required approval. Check can_execute where appropriate; it does not itself authorize or execute.
7. Serialize operations touching host state. Respect units, source bounds, locks, links, effects and transitions. Never enable unsafe-script or replay a consumed token to bypass a refusal.
8. On timeout/unknown results, inspect operation recovery and current targets before any dependent edit. Do not assume atomic rollback.
9. Verify fresh readback, save the project, present the actual edit for review and follow File/agents.md for export approval.
10. Verify the rendered artifact and actual output path after export. A capture, queued render or static report does not establish full audiovisual quality.

This session's tool discovery identified registered Premiere connection, typed edit-preview/apply and review-frame tools. No live Premiere connection, project mutation, render or visual/audio review was performed while creating the template.

If the bridge or a required tool is missing on another machine, state that prerequisite and continue script preparation or local planning. Do not claim the editor was changed.


For agent-farm runs, [EDIT_FARM.md](EDIT_FARM.md) adds cooperative project-wide writer ownership and operation journaling. It does not replace bridge authority or live project/sequence guards. Only the coordinator calls Premiere; specialists use captured local evidence. Unknown writes block dependent edits/export until the same writer reconciles actual host state.
