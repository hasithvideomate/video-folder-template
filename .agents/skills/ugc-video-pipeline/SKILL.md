---
name: ugc-video-pipeline
description: Plan local vertical UGC with supplied identity references, natural phone-photo directions, exact dialogue, reviewed samples, versioned clips and optional authorized Kie generation.
metadata:
  version: "1.1.2-local"
---

# Local UGC Video Pipeline

Read ../production-director/SKILL.md and ../ugc-director/SKILL.md. Use ../iphone-photo-look/SKILL.md for photographic treatment and ../ugc-avatar-voice/SKILL.md for voice design. No old ugc.py, UGC desk or automatic verifier is bundled.

Keep original script/references under Assets/. Write prompt blocks and exact source-linked dialogue to File/production.md, technical metadata/dependencies to File/production-plan.json, and actual attempts/receipts under File/generation/. Use stable UGC01_AVATAR, UGC01_VOICE and UGC01_V01 IDs.

## Supplied face: identity reference, not a photo replica

For a UGC avatar, use the actual supplied image as the selected model's supported identity/image reference; a text description alone is not an equivalent face reference. Preserve the person's recognizable identity while creating a new composition from the approved script/brief: requested outfit, setting, pose, expression, lighting and framing.

Generate one coherent photograph with one person. Do not output a tiled/repeated face, collage, split-screen, contact sheet, face grid, reference-photo inset or pasted face cutout. Do not reproduce the original photo's entire composition, clothing, jewelry, background or pose unless the user explicitly asks to keep those elements. This is identity-guided scene creation, not a pixel-for-pixel replica or merely a photo filter.

Include the single-person/no-collage requirement and the intended scene changes in the concrete image prompt. If the provider lacks a supported face/image reference input, report that limitation rather than claiming identity matching. Keep the reference/output as separate assets and inspect the actual result for identity and composition before acceptance. These UGC rules do not prohibit separately requested animation character sheets or storyboard review contact sheets.

## Supplied identity and composition
A supplied face is the identity reference, whether an authorized real-person image or a synthetic avatar. Preserve its facial proportions, skin, eyes and hair; do not replace it with demographics. Outfit, jewelry, pose and setting follow the brief rather than copying the reference accidentally. Selecting a reference does not authorize external transfer or spending.

Default vertical 9:16 and a currently supported requested output size. Keep complete head/hair, both hands, fingertips and wrists inside the frame with gesture margins. Use relaxed separated hands and a neutral resting face for reference stills.

The old mandatory top-30%-empty rule is superseded by practical full-hand/body framing. Performances may articulate and react naturally. Avoid contradictory handheld-selfie staging with two free hands and a fixed camera; a tripod/mount can explain the viewpoint.

## Phone appearance and prompt structure
Use plausible phone perspective, ordinary scene-motivated light and natural skin/material color. Avoid unintended fashion/studio polish, but do not force a warm cast, defects, glare, shake or specific iPhone generation.

A creative JSON proposal may hold format, aspect_ratio, subject, identity_reference, framing, wardrobe, setting, lighting, camera, texture, colour and exclusions. This is planning data, not the provider schema. Map only supported fields into a separately verified request. A blacklist is not a substitute for coherent direction; use only relevant negative constraints.

## Clips and sequence
Preserve every source word, language and order. Use language/delivery and actual sample timing rather than a universal words-per-second constant. Split at meaningful source boundaries instead of truncating/rushing.

Verify selected model, voice and reference compatibility. Actual voice/character IDs require a supported separately authorized registration route; the Market helper cannot create them.

Keep talking camera/framing fixed, gestures small/in-frame and expressions specific to the phrase. Speech only: no BGM, effects, added voices or unwanted ambience. Cutaways are muted by default to preserve narration; animation/other explicitly approved editing briefs can have different sound/camera choices.

For every future video payload, explicitly require no zooms/punch-ins/reframing, no captions/subtitles/text overlays, and no movement, drift, parallax, morphing, flicker or animation in the reference background, including posters, equipment and screens. These requirements also apply during editing. Preserve natural presenter movement and script-matched gestures. After downloading, automatically run the independent review agent required by AGENTS.md, including temporal camera/background checks and a caption check. Do not rewrite historical approved payloads or receipts to add new requirements.

## Gates and corrections
1. Draft the package and show the concrete image/reference preview.
2. Submit only under authorization and obtain human avatar acceptance.
3. Use voice preparation only with an actual supported route and authorization.
4. Generate/review a representative actual-script sample.
5. Preview/authorize the enumerated remaining clips as one scope; avoid repeat per-clip confirmations.
6. Retain all takes/receipts and target corrections only to the requested property/task.
7. Import accepted local assets through ../premiere-edit/SKILL.md.

Use ../image-review-validation/SKILL.md for still evidence. No automatic ASR/verifier, acceptance, voice preparation or two-retry/252-credit allowance carries over. Missing audio/motion evidence is uncertain; notes cannot grant spending permission.

Instruction version: ugc-video-pipeline@1.1.2-local.


## Automatic review routing
File/docs/AGENTIC_WORKFLOW.md supersedes routine human sample/clip gates here: automatically delegate review and advance only on fully evidenced passes. Keep user-selected identity/source authority and the spending/final-export approval boundaries. Compile every video prompt and create a fresh hashed packet for every downloaded take.
