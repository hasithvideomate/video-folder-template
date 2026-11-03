---
name: ugc-director
description: Draft and direct local UGC avatar production with exact source dialogue, full-hand framing, consistent identity/voice, fixed camera, clean speech and sample review before remaining clips.
metadata:
  version: "1.0.2"
---

# UGC director

For the detailed local sequence load ../ugc-video-pipeline/SKILL.md, photographic treatment ../iphone-photo-look/SKILL.md, and voice planning ../ugc-avatar-voice/SKILL.md.

Read ../production-director/SKILL.md for local files, optional Kie tasks, costs and authorization. Use the current script, language/accent preferences and references from Assets/ and File/project_brief.md.

## Supplied face: identity reference, not a photo replica

For a UGC avatar, use the actual supplied image as the selected model's supported identity/image reference; a text description alone is not an equivalent face reference. Preserve the person's recognizable identity while creating a new composition from the approved script/brief: requested outfit, setting, pose, expression, lighting and framing.

Generate one coherent photograph with one person. Do not output a tiled/repeated face, collage, split-screen, contact sheet, face grid, reference-photo inset or pasted face cutout. Do not reproduce the original photo's entire composition, clothing, jewelry, background or pose unless the user explicitly asks to keep those elements. This is identity-guided scene creation, not a pixel-for-pixel replica or merely a photo filter.

Include the single-person/no-collage requirement and the intended scene changes in the concrete image prompt. If the provider lacks a supported face/image reference input, report that limitation rather than claiming identity matching. Keep the reference/output as separate assets and inspect the actual result for identity and composition before acceptance. These UGC rules do not prohibit separately requested animation character sheets or storyboard review contact sheets.

Separate identity from outfit, jewelry, pose and scenery; do not inherit them by accident. Propose requested wardrobe/setting and natural phone-photo appearance. Compose vertical 9:16, eye-level, complete head/hair, and both hands with every finger visible plus gesture room. Avoid a mandatory top-30%-empty rule that removes body/hand space.

Preserve exact dialogue and language. Use small natural gestures, direct lens engagement and a fixed camera: no zoom, pan, tilt, shake, cuts or angle changes. Speech only, without music, effects, ambience or added words. Match the requested accent rather than inferring it from appearance. Do not omit words or unnaturally accelerate delivery to fit a model's duration limit.

Apply the user's clean-video rule to every generation prompt and edit: locked camera and scale, no zooms or digital punch-ins, no on-screen captions/subtitles/text overlays, and a stationary reference background. Keep walls, posters, furniture, equipment and screens fixed without drift, parallax, morphing, flicker or animation while the presenter speaks and gestures naturally. Review actual temporal evidence for all three requirements and flag observed violations; do not infer stability from one still.

Plan and obtain acceptance of the avatar reference, then a representative actual-script sample before the remaining clips. Verify selected provider support for reference/voice consistency. This local template has no built-in voice/character registration adapter; do not fabricate IDs or claim binding succeeded. Use a supported separately reviewed route when required.

Keep local task/source-span/reference-version mapping in File/ and File/memory.md. Reuse an accepted sample when it is already a final segment. Changing identity, voice or references can invalidate prior sample acceptance.

Human review must cover actual wording, sound, voice continuity, gestures and frame coverage. A still is composition evidence only. Record missing playback/audio evidence as uncertain and target corrections only to the requested take, retaining prior media and receipts.

After selecting footage, use ../premiere-edit/SKILL.md to edit it into the existing project.

Instruction version: ugc-director@1.0.2.


## Automatic review routing
File/docs/AGENTIC_WORKFLOW.md supersedes routine human sample/clip gates here: automatically delegate review and advance only on fully evidenced passes. Keep user-selected identity/source authority and the spending/final-export approval boundaries. Compile every video prompt and create a fresh hashed packet for every downloaded take.

For confirmed fixable review defects, follow File/docs/AUTO_REPAIR.md automatically: preserve the same characters/scenes, repair the affected property, independently re-review, and resume dependent work. A findings-only message is not completion when authorized repair remains possible.
