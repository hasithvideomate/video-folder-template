# Production templates

Use only necessary fields. Fill unknowns honestly. Copy these into deliverables without overwriting the skill.

## Brief

- Uploaded script: filename, available scenes/pages, and any unreadable or missing sections.
- Director's interpretation: emotional core, audience journey, and scene intentions.
- Title / premise / audience:
- Target runtime / aspect ratio:
- Storyboard frame and sheet aspect ratio: landscape 16:9.
- Reference-sheet aspect ratio: landscape 16:9.
- Video aspect ratio: vertical 9:16, reframed from the 16:9 storyboards.
- Audience feeling at start → end:
- Want / need / belief / stakes / choice / payoff:
- Director's locked choices / provisional decisions:
- Generator and verified capabilities:

## Source coverage and scene direction

Retain the verbatim source separately from directing notes. Use source scene/line IDs or exact excerpts when pages are unavailable. Fill only supported fields; a scene may sustain its state without an emotional reversal.

| Source scene / beat / dialogue line | Storyboard / shots | Source fact | Directing inference or unresolved gap | Coverage |
| --- | --- | --- | --- | --- |
| source ID | SB01 / SB01_SH01 | supplied action or exact dialogue | staging/performance choice, clearly labeled | planned / verified / missing |

```text
SCENE: source ID
INTENTION: source-supported purpose and emotional state/change
VIEWPOINT: whose experience guides the camera
AUDIENCE: entry knowledge → intended exit understanding
REVEAL: what must be withheld until which source beat, or none
PERFORMANCE: dominant intention, stimulus, response, listening, held result
BLOCKING: positions, facing, paths, eyelines, axis, prop contacts
CAMERA REASON: what the framing/movement/cut lets the audience understand
```

## Color and light progression

| Source scene | Palette / value contrast | Light direction / softness | Focal subject | Script-supported mood or transition |
| --- | --- | --- | --- | --- |
| scene ID | concrete colors and bright/dark relationship | source and direction | face, action, or object | state/shift, not a new event |

## Voice and sound bindings

| Character | Voice identity reference | Exact source line ID | Delivery / listening direction | Actual dialogue take | Duration |
| --- | --- | --- | --- | --- | --- |
| CH01 | actual file/voice ID or pending | line ID linked to verbatim text | intention, pace, pauses, listener response | file or not generated | measured seconds or labeled estimate |

For each sound effect record source, action trigger/time, duration/tail, and perspective. Preserve intentional silence and room tone; no background music.

## Continuity bible

| ID | Locked appearance/layout | Actual reference file | Variable state |
| --- | --- | --- | --- |
| CH01 | Silhouette, proportions, face, wardrobe, material | path or unknown | Pose, emotion, damage |
| ENV01 | Geography, axis, lights | path or unknown | Time/weather |
| PROP01 | Shape, size, color | path or unknown | Holder, position, condition |

For each character, add a short performance vocabulary: posture, movement tempo, gesture range, expression limits, and body mechanics grounded in the script or labeled as design choices. Record relative character/prop scale.

## Reference sheets in Markdown packages

Include one filled character entry per distinct character and one filled location entry per distinct location in the delivered `.md` file. Include the complete prompts even when images are linked. Replace bracketed fields with project-specific details; preserve stable IDs across references and storyboards. Label missing images as awaiting generation.

### Character reference sheet

```text
CHARACTER: CH01 — [name]
USED BY: [source scenes / storyboard IDs]
REFERENCE IMAGE: [actual linked asset or awaiting generation]
COPY-READY IMAGE PROMPT:
Landscape 16:9 character reference sheet of [original character], in a
Pixar-inspired stylized 3D animation style. Establish [specific designed
head/body relationship and face masses] with [sculpted eyelids/brows,
grouped hair shapes, simplified hands and clothing folds]. Lock
[silhouette, proportions, facial structure, distinguishing marks],
[wardrobe], [palette], and [materials distinguished by broad color,
roughness and selective texture rather than photographic microdetail].
Preserve the character's age, ethnicity, build and original identity.
Three panels only, separated by clean gutters:
left, a large front-facing head-and-shoulders portrait; center, a
complete uncropped full-body front view; right, a complete uncropped
full-body back view. Calm neutral resting face in every panel; no
smiles, emotional expressions, expression studies, or extra poses.
Relaxed neutral standing pose, arms at sides. Preserve the same face,
hair, proportions, outfit, and accessories in every panel, with both
full-body views at matching scale. Use [simple backdrop] and clear,
consistent studio lighting. Appealing forms, coherent facial design,
controlled detail; no text, labels, props, scenery, cropped bodies, or
stretched proportions.
```

### Location reference sheet

```text
LOCATION: ENV01 — [name]
USED BY: [source scenes / storyboard IDs]
REFERENCE IMAGE: [actual linked asset or awaiting generation]
COPY-READY IMAGE PROMPT:
Landscape 16:9 location reference sheet of [setting], a Pixar-inspired
stylized 3D animated environment. Show a wide establishing view and
complementary views of [reverse angle / key activity area / landmark],
keeping [spatial layout, entrances/exits, landmark positions, scale]
consistent across all views. Establish [two setting-specific designed
shape anchors, such as broad cushion masses and thick curved trim],
with [large/medium/small shape hierarchy], [materials distinguished
by broad color, roughness and selective texture], and [palette].
Keep surfaces calm at thumbnail scale; use a few designed grain, weave
or wear accents rather than photographic surface noise. Preserve
adult scale, functional contact areas and the scene's emotional mood.
Set [time of day and weather] with cinematic lighting from [direction],
[shadow character], and [emotional atmosphere]. Preserve [consequential
props and action areas] and clear staging space for the characters.
Render all views in the same stylized animated world as the character
sheets, with no photorealistic environment treatment. Keep individual
views legible with clean gutters.
```

## Shots inside each storyboard

Group the table under its storyboard ID. Preserve one master video prompt for the whole storyboard; keep per-shot notes nested inside it.

| Shot | Used seconds | Purpose / turn | Framing / camera | Visible action | Panels | Audio | Continuity in → out |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SB01_SH01 | duration | what changes | scale, camera height/angle, orientation, move/hold, cut | expression, eye focus, posture, gesture, reaction | SB01_SH01_F01/F02 | exact dialogue, voice binding, timed SFX/ambience; no BGM | pose, eyeline, prop |

Sum used durations to target runtime. Track generated duration and trims separately.

## Storyboard-sequence package

```text
STORYBOARD: SB01
SOURCE: source scene/page/beat references
SHEETS: SB01_PAGE01, SB01_PAGE02 if needed; each landscape 16:9
INTERNAL SHOTS: SB01_SH01, SB01_SH02, ...
PANEL MAP: panel ID → internal shot ID → start/turn/end moment
SEQUENCE TURN: entry state → emotional change → exit state
TOTAL USED DURATION: sum of internal shots
DIRECTOR NOTE: narrative purpose and audience inference
VIEWPOINT / ATTENTION: whose experience; primary focal subject; reveal timing
REFERENCES: actual character/setting/prop input bindings
START FRAME: first internal shot’s beginning pose and layout
BOARD PROMPT: 16:9 storyboard sheet containing the internal shots
              with character expressions, poses, framing, and camera angles
VIDEO PROMPT: one vertical 9:16 sequence prompt describing internal shots in order,
              with each shot’s expression changes, acting, framing, camera
              angle/movement, action, duration, cuts, and timed sound effects;
              explicitly include "No background music"
END STATE: pose, expression, prop state, editorial hold
AUDIO: exact dialogue / character-to-voice-reference bindings /
       timed ambience and SFX / no background music / separate-edit plan
SETTINGS: model + interface, verified duration, ratio, resolution, controls
PROMPT RECORD: Markdown path, prompt block ID/version; exact saved text for API use
EDIT: used duration, trims, neighboring cut compatibility
CHECK: essential story, acting, identity, and contact criteria
EXECUTION SEGMENTS: only if required by model limits; map to internal shot IDs
STATUS: planned / frame-generated / clip-generated / inspected / selected
```

## Take ledger

| Shot / take | Model/settings | Input paths | Prompt version | Output path | Observed result | Selected? |
| --- | --- | --- | --- | --- | --- | --- |
| SB01_SH01_T01 | known/unknown | actual inputs | v01 | actual/not generated | concrete defects/strengths | yes/no/pending |

## Candid review

```text
Review pass: source fidelity / comprehension / performance / timing / image-sound integrity.
Material inspected: prompt / still / sequence / audio; pending checks named explicitly.
Observation: visible/audible issue, shot ID and timestamp where available.
Audience consequence: what becomes unclear or ineffective.
Likely cause: a hypothesis separated from observation.
Smallest repair: specific cut, pose, frame, prompt, sound, or setup change.
Alternative: only when there is a meaningful creative tradeoff.
Director decision: only the unresolved creative choice.
```
