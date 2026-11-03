---
name: frame-mcp-integration
description: Adapt the legacy desktop-agent workflow to local production files and the user's existing Premiere MCP automation, including live inspection, guarded edits and verified export.
metadata:
  version: "1.1.0-local"
---

# Local Desktop Agent and Premiere MCP Integration

The name is retained for compatibility. No Frame app, Frame MCP server, dashboard, frame_inspect/frame_save_prompt tools or frame_mcp.py is bundled. Do not configure nonexistent components.

Read root AGENTS.md, File/docs/PREMIERE_AUTOMATION.md and ../premiere-edit/SKILL.md. Use the user's existing Premiere MCP connection; machine-specific installation/configuration is not bundled.

## Local workflow equivalents
- Inspect: read File/project_brief.md, File/memory.md, local assets and live Premiere state.
- Submit plan: write a concrete proposal to File/production.md for review.
- Save prompt: update only the requested named block, preserving source and unrelated directions.
- Save review: write a versioned file under File/reviews/ and link it from memory.
- Check tasks: inspect File/generation/ records and poll known provider IDs through the helper.
- Apply edits: use registered Premiere previews and application tools with current identities and required tokens.

A proposal is not execution or spending approval. Preserve old takes, records and user decisions.

## Premiere tools
Start with get_capabilities, task keywords and tool_limit: 10. Read exact schemas/authority; verify the selected bridge before host work. Do not invent tools or silently switch backends.

Inspect the saved project/active sequence, follow paginated reads and resolve current IDs. Use expected_project_path for supporting CEP tools and appropriate UXP guards for UXP. Interchange/local IDs are not live targets.

Serialize host-state operations. Apply unchanged typed previews/single-use tokens within authorization. Respect source bounds, locks, linked A/V, captions and unrelated tracks. Unknown outcomes require recovery/state inspection before another attempt.

Verify readback and actual artifacts; stills do not prove motion/audio and queued renders are not completion. Save the existing project and follow File/agents.md for final-export review/approval.

Paid Kie operations use ../kie-generation-runner/SKILL.md. Local drafting needs no second paid GPT/Claude call; no legacy Claude streaming route is installed.

Instruction version: frame-mcp-integration@1.1.0-local.

