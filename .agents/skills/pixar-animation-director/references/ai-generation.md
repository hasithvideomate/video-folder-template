# AI storyboard and video production

## References

Generate all reference sheets on landscape 16:9 canvases, including character sheets, environments, and props. Arrange views with consistent scale and readable spacing; preserve proportions. Generate storyboard frames and storyboard contact sheets at 16:9 too, with each panel retaining that ratio. State the ratio in prompts and verify actual dimensions; regenerate or recompose mismatched outputs without stretching. Follow a later explicit user override.

Create character references for proportions, face, wardrobe, and materials; setting references for layout and lighting; hero-prop references where needed. Use neutral views for identity and composed keyframes for acting. Character sheets are reference assets, not video start frames.

For character sheets, use three panels: a large neutral face portrait, a full-body front view, and a full-body back view, at consistent scale with neutral lighting, a neutral face, and the same outfit. Do not include expression studies or action poses unless the user requests them; direct expressions in storyboard prompts instead. Preserve asymmetrical marks and accessories on the correct side. Record character-to-character and prop-to-character scale relationships. Keep environment geography separate from mood/lighting variations.

Prefer readable references over many tiny views. Verify that the tool can use multi-view sheets; supply separate views when required by its input mechanism. Set exact supported 16:9 dimensions when possible. If direct 16:9 output is unavailable, generate a suitable supported size and recompose or crop through an available image-editing tool without losing required views. Inspect the result. A ratio in the prompt is not proof of the file's actual dimensions.

Keep identity blocks stable and bind actual input files through supported tool mechanisms. Identify subjects with visible traits and spatial bindings, such as “the copper robot on screen left.” IDs organize production; they do not bind model identity by themselves.

## Art direction: a visibly designed animated world

For everyday real-world settings, apply [the supplied grounded-worlds style guide](grounded_pixar_worlds_image_style_guide.md) as the default visual target. Its character design, regional construction, functional set dressing, material, lighting, and review guidance apply to character sheets, location sheets, and storyboards. Use the repair choices below within that selected degree of stylization; stronger caricature or enlarged furniture forms require a matching brief. Adapt scene/action and background-person instructions to neutral character sheets and any required empty location views. Preserve source facts, locked identity/geography, and production requirements.

Use this guidance when the requested look is a stylized 3D feature rather than photographic rendering. These are practical prompt and review choices, not proprietary Pixar rules. The desired amount of exaggeration belongs to the project; preserve a user's chosen realistic style when that is the brief.

Inspect actual images before prescribing a repair. Compare an older take with a newer take at both full size and thumbnail size. Record which changes improved the silhouette, proportions, facial planes, or environment design, and which photographic cues remain. Compare both the close portrait and full-body views: an appealing close-up can hide an unchanged realistic body. For environments, compare furniture proportions and architecture as well as lighting. Separate observed changes from guesses about why the model produced them.

Write design choices early in the copy-ready prompt, before long inventories of surfaces. Resolve three things:

- **Shape:** choose a coherent silhouette and a small family of large, medium, and small forms. For adult characters, use a deliberately designed head/body relationship, clear cheek and jaw masses, sculpted eyelids and brows, and simplified hands and clothing folds. Retain age, ethnicity, build, identity, and neutral sheet poses. Bigger eyes are one possible choice, not the entire style or a reason to make every adult a child. For sets, specify concrete changes such as a thick rounded tabletop, broad cushion masses, substantial door trim, simplified fixtures, and grouped plant leaves. Preserve usable scale, room geography, paths, and contact surfaces.
- **Surface:** make materials distinct through broad color, roughness, highlights, and a few intentional texture accents. Tactile does not require dense visible pores, individual hair strands, fine wood grain, every thread, scratches, or evenly noisy surfaces. Hair can read as sculpted curl groups with selective strand accents; age can read through chosen folds and planes; fabric can read through a few seams and larger folds. Avoid replacing all materials with glossy plastic or losing the mature identity.
- **Light:** retain the scripted source and time of day while arranging readable light and shadow masses, colored bounce, soft falloff, and clear subject/background separation. A warm lamp does not turn a photographic room into an animated set. A cold office and a dark living room can keep a clear stylized shape language without adding warm lamps or cheerful color that changes the scene.

For environments, name at least two setting-specific design anchors rather than repeating generic "rounded, cinematic, high quality" language. A home might use plump couch cushions and thick curved trim; an office might use thick table slabs and simple sculpted chair backs; a car might use a compact body mass and broad dashboard controls. Match the characters' scale and design strength. Support varied palettes, emotional states, and materials across locations without making every place the same pastel room.

When stronger stylization is requested, rewrite conflicting material language rather than only appending "not photorealistic." Replace dense weave, fine grain, pores, or ray-traced showcase language with the chosen simplified surface treatment. Keep a short, coherent style brief instead of a growing stack of contradictory instructions. Every executable prompt must contain its own visual direction; a style paragraph outside the prompt block is not sent to the model.

If a first repair changes surfaces or lighting only slightly, shorten the prompt and replace vague "slightly rounded" language with visible form changes. Describe the couch as broad cushion masses, a table as a thick disc and stout support, or a door surround as substantial bowed trim. Keep spatial requirements separate and concise. Do not accept the result as a style target merely because the prompt contains the intended style words; judge the downloaded image.

Review texture separately after a successful shape change. Oversized knit loops and detailed rug fibers may still make a bedroom look realistic even when its trim and furniture are more stylized. For a further surface repair, specify calm matte fabric volumes and a few folds/seams, leaving detailed weave as a selective accent. Preserve the successful silhouettes and light state. Log incidental additions and rendering defects so the reference is not mistaken for authority to change scripted props or lighting.

Assign reference roles explicitly. Preserve identity or geography from a supplied image while describing any authorized style change; do not blindly inherit its realism. For a fresh take, use established character/location dependencies and the saved prompt, not the previous output as an image-edit target unless the user asks to edit it. An environment reference may establish room layout for a new time-of-day state. Respect stable reference bindings and invalidate dependent selections when their source version changes.

Review a first revised result before expanding a batch. Check designed silhouettes, simplified surfaces, readable light masses, identity/geography, and compatibility with the current cast. A sharper or warmer result alone is not proof of a stronger animated design. Log remaining defects honestly and adjust the failing design variable. Keep paid refinements within the user's scope; reconcile existing tasks before another take. Save the prompt before preview/submission and inspect the downloaded output before using it downstream.

## Prompt separation

**Board/image:** framing + concrete character identity/reference + setting and spatial relationships + one visible pose + light/palette/material + aspect ratio. Describe one moment. Put captions in metadata.

**Image-to-video:** visible subject + ordered action/reaction + camera behavior + relevant environment motion + end-state hold. Do not contradict the starting pose or unnecessarily redescribe it.

**Text-to-video:** visual facts plus motion plan. Write one prompt per storyboard sequence, describing its internal shots and cuts in order. Verify multi-shot and duration support. Where the model needs separate runs, keep the master storyboard prompt and map execution segments to its internal shots. Do not promise an entire film from one generation.

**Negative constraints:** keep them in the production record. Use positive staging where possible, such as “locked camera,” “one robot,” “clean frame.” Send dedicated negative prompts only when supported and recommended by the specific provider.

## Capability check

Record model, version, interface, verification date, supported durations, aspect ratios/resolutions, reference limits, endpoint controls, audio, and camera controls. Verify feature combinations. Use unknown for unverified fields. Never present internal production JSON as a provider's API schema. Timing/optics in prose communicate intent, not guaranteed physical precision.

## Efficiency

Solve story problems in rough boards. Inspect clean inputs for identity, anatomy, contact, and layout. Test a representative difficult shot. Generate authorized candidates, inspect, and log outcomes. Retry a targeted variable. Check whole-scene rhythm and adjacent cuts before selecting takes.

| Failure | First repair |
| --- | --- |
| Identity drift | Rebind actual references; fix input; reduce occlusion/turn complexity. |
| Random acting | Reduce gestures; give one stimulus/response; add a readable hold. |
| Merged hands/props | Fix keyframe contact; simplify action or cut to an insert. |
| Missing payoff | Reduce actions or split the beat; adjust supported length and edit timing. |
| Style changes | Keep materials/light and references stable; inspect input. |
| Two characters exchange identity | Use distinct traits and spatial bindings; try singles/reaction cuts. |
| Dialogue overruns/lip sync fails | Preserve every line; extend/split the sequence, use suitable reaction coverage, or generate voice separately. |
| Cut jars | Check screen direction, pose, sound overlap, and holds before regeneration. |

Distinguish generated and used duration. Add edit handles where useful and supported. Smooth room tone and sound effects across cuts; independently generated audio may not match automatically. Do not add background music.
