---
name: animation-script-planning
description: Break approved animation scripts into character/location references and source-linked storyboard/video prompt packages with unique kie-prompt blocks and local asset dependencies.
metadata:
  version: "1.2.0-local"
---

# Animation Script Planning and Prompt Packaging

Read ../animation-director/SKILL.md. Load ../pixar-animation-director/SKILL.md for detailed original animated-feature direction. No old planning.py/director.py or desktop application is needed.

Keep the original script unchanged in Assets/. Write the package to File/production.md and technical metadata/dependencies to File/production-plan.json. Prompt text lives in Markdown; the JSON references its block IDs. These planning files are not automatically parsed by the local Kie helper.

Preserve exact dialogue, speaker, language, source order and ending. Separate source facts, inferred acting/staging and unresolved gaps. Establish concrete shape/material/palette/light direction instead of substituting a studio name.

## Stable prompt blocks
Use a fenced block opening with three backticks followed by kie-prompt and a unique job ID, containing only copy-ready directions, then a closing three-backtick fence.

IDs: CH01_REF for characters, LOC01_REF for locations, PROP01_REF for consequential props, SB01 for storyboard sequences, SB01_SH01 for internal shots. Store exact spoken dialogue separately with its source offsets/version.

## Reference and board content
- Characters: default 16:9 sheet with a large neutral face portrait, full-body front and full-body back views. Lock silhouette, proportions, hair, facial structure, wardrobe, materials and palette. Neutral closed lips apply to reference stills, not frozen performance.
- Locations: establishing/complementary views, geography, scale, entrances/exits, key props, material design, time and light direction. Keep transient characters out unless the source requires them.
- Storyboards: framing/angle, source action, expression, eye line, emotional beat, camera/static hold, geography, selected references and light continuity.
- Sequence packages: ordered timed shot plans, with one generation prompt/job per uninterrupted static shot under the current root camera rules. Timing is estimated; dialogue and source order remain exact. Keep no-BGM default; script-motivated effects/ambience differ from UGC speech-only rules.

Planning metadata can hold id, kind, prompt_block, source_version, reference_ids, model_status and aspect_ratio. A 16:9 default can be changed by the brief. Use clean individual final-aspect frames as video inputs, not labeled contact sheets.

Complete the requested planning scope before spending. Verify current model IDs, schemas, sizes/durations and prices before building an actual request; historical aliases/costs are not defaults. Reuse selected references and independently review the first three boards before dependent work. Follow File/docs/ANIMATION_FARM.md; include locked camera, stationary scenery, no added text and 720p in each video prompt. Keep protected action/reaction/hold beats explicit and map every generated shot back to its sequence.

Use ../kie-generation-runner/SKILL.md for separately saved concrete payload previews and authorized submission.

Instruction version: animation-script-planning@1.2.0-local.

