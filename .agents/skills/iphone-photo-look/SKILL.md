---
name: iphone-photo-look
description: >
  Direct an image-generation or image-editing model to create convincing photographs
  with the perspective, natural color, computational tone mapping, surface detail,
  and real-world imperfections associated with Apple iPhone still photography.
  Use when a user asks for a shot-on-iPhone appearance, an everyday smartphone
  snapshot, an Apple Photographic Style-inspired rendering, or realistic mobile
  photography rather than cinematic, DSLR, studio, CGI, or illustration aesthetics.
metadata:
  version: "1.1.1-local"
---

## Local template integration

Read root AGENTS.md and ../production-director/SKILL.md before execution. Use File/production.md for saved prompt packages, File/memory.md for handoffs and Assets/ for original references and outputs. Preserve supplied source dialogue, sequence and ending; source facts and user choices outrank stylistic examples.

This is directing guidance, not an installed generator or review worker. Paid Kie operations use ../kie-generation-runner/SKILL.md and the actual File/scripts/kie_tasks.py helper after a concrete preview and applicable authorization. Do not substitute another image/video provider or invoke missing legacy scripts/tools. Human quality review is separate from generation completion. Missing audio/motion evidence remains uncertain; no automatic paid retries or approval grants are imported.

Use ../premiere-edit/SKILL.md for actual editing and final export. The detailed guidance below is imported craft/reference material; model, pricing, camera-product and external-source claims have not been requalified by copying it. Verify current official facts when an actual technical choice depends on them; do not invent metadata or treat an old recipe as a provider contract.

## Supplied face: identity reference, not a photo replica

For a UGC avatar, use the actual supplied image as the selected model's supported identity/image reference; a text description alone is not an equivalent face reference. Preserve the person's recognizable identity while creating a new composition from the approved script/brief: requested outfit, setting, pose, expression, lighting and framing.

Generate one coherent photograph with one person. Do not output a tiled/repeated face, collage, split-screen, contact sheet, face grid, reference-photo inset or pasted face cutout. Do not reproduce the original photo's entire composition, clothing, jewelry, background or pose unless the user explicitly asks to keep those elements. This is identity-guided scene creation, not a pixel-for-pixel replica or merely a photo filter.

Include the single-person/no-collage requirement and the intended scene changes in the concrete image prompt. If the provider lacks a supported face/image reference input, report that limitation rather than claiming identity matching. Keep the reference/output as separate assets and inspect the actual result for identity and composition before acceptance. These UGC rules do not prohibit separately requested animation character sheets or storyboard review contact sheets.

# iPhone Photo Look — Image-Generation Skill

**Version:** 1.0  
**Updated:** 2026-10-12  
**Primary task:** Translate a subject or scene description into image-generation directions that create *plausible iPhone photographs*, not unverifiable replicas of Apple's closed-source image pipeline.  
**Applicable to:** Text-to-image, image-to-image editing, prompt refinement, visual evaluation, and multi-image consistency.

> **Critical distinction:** A prompt can influence visible color, exposure, perspective, sharpness and texture. It **cannot** guarantee that generated pixels were captured by an iPhone, were processed by Smart HDR/Deep Fusion/Photonic Engine, or contain a genuine Display P3 ICC profile, ProRAW DNG, HDR gain map or EXIF camera signature. Treat references to these technologies as *appearance cues* unless a real file-processing tool implements them.

## 1. Purpose and success criteria

Given a user's visual concept, create a photographic image that an ordinary viewer could plausibly mistake for a real still photo from the native iPhone Camera app. Prioritize believable physical light, sensible mobile-camera optics, skin and material color, plausible dynamic range, and recognizable everyday framing over maximal prettiness.

A strong result should feel:

- **Observed rather than art-directed:** a real place, moment, person, object or event, photographed from where a person could hold a phone.
- **Color-managed in appearance:** realistic neutral references, believable skin undertones, saturated hues that do not contaminate skin or neutral materials, no blanket teal/orange grade.
- **Computationally finished but not synthetic:** moderate shadow recovery, preserved bright areas where possible, localized contrast, fine texture and smartphone-like edge definition without halos.
- **Optically credible:** plausible field of view, perspective, focus behavior and motion handling for the selected rear/front camera.
- **Slightly imperfect:** natural posture, uneven ambient light, ordinary clutter or minor framing compromises when appropriate. Avoid inserting defects gratuitously.

### Explicit non-goals

- Do not create a generic luxury-camera ad, Hollywood frame, medium-format portrait or 3D render and label it an iPhone photo.
- Do not equate stronger saturation with higher color accuracy.
- Do not claim a specific iPhone generation's exact colorimetry can be reproduced from text alone.
- Do not invent EXIF, ICC, signed sensor data, Apple Reference Image, or false provenance as proof of capture.
- Do not force a named model, megapixel count, file format or Photographic Style when the user has not asked for one.

## 2. Activation and intake

**Trigger phrases:** "shot on iPhone," "iPhone camera photo," "looks like Apple Photos," "iPhone 15 snapshot," "iPhone 16 Photographic Styles," "natural iPhone colors," "make it look like a phone picture," or requests for candid everyday smartphone photography.

**Inputs (infer sensible defaults instead of interrogating the user):**

| Parameter | Accepted values | Default |
|---|---|---|
| `subject` | Who or what must appear, relationships and actions | Required from request |
| `context` | Place, season, time, weather, ambient conditions | Plausible real-world setting |
| `generation` | `generic-modern`, `13`, `14`, `15`, `16`, `17`, `18-pro` | `generic-modern` |
| `camera` | `rear-main-1x`, `rear-ultrawide`, `rear-2x`, `rear-tele`, `front-selfie`, `macro` | `rear-main-1x` |
| `style` | `standard`, `rich-contrast`, `vibrant`, `warm`, `cool`, `bright`, `custom` | `standard` |
| `lighting` | Daylight, overcast, window, mixed, golden hour, street/night, indoor | Scene-appropriate natural light |
| `composition` | Candid, portrait, product, food, travel, group, documentary | Natural handheld |
| `editing_intensity` | `minimal`, `default`, `punchy` | `default` |
| `dynamic_range` | `SDR-photo-look`, `HDR-like-look` | `SDR-photo-look` |
| `aspect_ratio` | 4:3, 3:4, 1:1, 16:9 or task-specific | 4:3 landscape or 3:4 portrait |
| `destination` | Social, screen, print, web, archival | Screen/social |

**Priority in conflicts:** (1) user's scene and identity constraints, (2) physically believable photography, (3) chosen lens and illumination, (4) color/Photographic Style preset, (5) minor texture and aesthetic preferences. A named style must not change subject identity, clothing or other specified colors.

## 3. Execution procedure

1. **Parse the scene.** Name the subject, action, surroundings, time, weather, important objects, composition and any absolute constraints. Preserve these throughout.
2. **Choose one camera viewpoint.** Unless specified, use a rear main-camera handheld perspective. Select an ultrawide, telephoto or selfie view only when the scene supports it.
3. **Choose one rendering target.** Standard iPhone appearance by default; apply a named Photographic Style or custom color direction only when requested.
4. **Construct believable illumination.** Define light source direction, ambient fill, practical lights and shadow softness. Resolve mixed lighting plausibly, not perfectly.
5. **Set color behavior.** Keep faces and neutral surfaces credible; use scene-specific white balance; protect distinctive colors.
6. **Set tone and detail behavior.** Use moderate computational shadow/highlight balancing, appropriate edge sharpness and texture, and scene-specific low-light noise.
7. **Add smartphone composition cues.** Human eye/hand height, plausible distance, realistic focus, ordinary background, no forced photographic perfection.
8. **Assemble a single coherent prompt.** Put the scene first, then camera perspective, lighting, color/tone, texture, composition and hard exclusions.
9. **Generate or edit.** For image editing, preserve the supplied photograph's content, layout, identity and geometry unless user requests a change; adjust visual rendering only.
10. **Quality-check and refine once if necessary.** Identify the largest realism error; revise only that factor rather than indiscriminately increasing every adjective.

If the interface accepts negative prompts, use the negative clause in §11. If it does not, weave exclusions into positive instructions sparingly.

## 4. Visual signature: the default modern iPhone photograph

### 4.1 Color science *as an appearance target*

| Component | Positive instruction | Avoid |
|---|---|---|
| Overall color | Realistic, clear, slightly lively but controlled natural-world colors | Global neon vibrance or flat desaturation |
| White balance | Neutral-to-gently-warm daylight; contextual warmth under incandescent practicals | Sterile all-neutral night scenes; yellow cast across everything |
| Skin | Preserve each person's natural undertone, variation, translucency and lighting-dependent warmth | Orange faces, pink/magenta uniformity, waxy smoothing, homogenization |
| Greens | Natural foliage variation, balanced yellow-green and blue-green according to plant/light | Uniform fluorescent lime foliage |
| Blue skies | Convincing blue gradients, atmosphere and cloud detail where exposure allows | Cyan clipping, teal skies, banding, oversaturated cobalt everywhere |
| Reds/oranges | Saturated but textured fabric, food, foliage and signs | Featureless red clipping, neon orange skin |
| Neutrals | Whites remain plausible under incident light; gray/black retain believable tint | Pure #FFFFFF surfaces in warm ambient light; colorless blacks |
| Local variation | Skin, sky, foliage and shadows can respond differently to lighting | One color filter indiscriminately imposed on the entire frame |

There is **no universal numeric recipe** for Apple color. Don't invent fixed hue shifts, precise RGB curves or color matrices as if Apple published them. Subtle descriptive adjustments are more defensible.

### 4.2 Dynamic range and tone mapping

- Preserve usable bright-cloud or window detail **when exposure permits**, but allow small specular highlights and practical lamps to clip naturally.
- Show recognizable shadow information without flattening the image into evenly lit layers.
- Keep locally plausible midtone contrast: hair, walls, fabric and skin should retain spatial depth.
- Allow a restrained high-dynamic-range smartphone feel in backlit scenes, with the subject readable and the sky not arbitrarily crushed.
- Never make every pixel equally exposed. "Perfectly preserved highlights and shadows everywhere" reads as CGI or extreme HDR.
- Distinguish **HDR-like tonal appearance in a generated SDR picture** from a true HDR encoded file with gain-map/extended-range playback.

### 4.3 Detail, texture and noise

- Daylight: relatively clean, crisp fine textures and edges; moderate microcontrast; believable pores, textiles and organic surfaces.
- Indoor available light: mild smoothing in low-contrast areas, more noise and less precise fine detail in shadows.
- Night: luminance noise or gentle chroma suppression in dark regions, some locally softened detail, sharper stationary high-contrast edges; moving subjects may blur.
- Avoid thick outline halos around heads, tree branches, architecture or text.
- Avoid plasticky denoising, artificially etched pores, fake over-sharpened brick textures and checkerboard detail.
- Avoid super-resolution claims: specifying "48MP" describes a capture option, not a guaranteed visible realism enhancement.

### 4.4 Optics and depth of field

**Rear main 1×:** Default, everyday-documentary perspective with a moderately wide field of view (around 24–28 mm full-frame equivalent as a *rough visual cue*, depending on generation). Close subjects can show some natural background separation, but ordinary people-and-street scenes usually retain appreciable context and depth of field.

**Ultrawide:** Much wider scene inclusion, strong near/far scale differences, architectural divergence if camera is tilted, edge stretching when subjects approach corners. Keep central geometry sensible; do not apply fisheye curvature by default.

**2× / telephoto:** Narrower frame, camera farther from subject for the same framing, quieter backgrounds and more apparent compression. Actual 2× quality/implementation varies by model. Do not assume every iPhone generation has the same telephoto lens.

**Front/selfie:** Arm's-length or mirror-social perspective, nearby face noticeably larger in frame than background, realistic indoor/exterior ambient light, often group-oriented. No automatic glamour retouching.

**Portrait mode:** Separate, explicitly requested option; stronger simulated subject/background separation with **plausible segmentation** around hair, glasses and fine objects. Do not automatically use portrait-style blur for every portrait of a person.

**Macro:** Very close viewpoint, large subject relative to background, natural near-field focus falloff; use only if supported by scene and selected camera capability.

*Physics guardrail:* Apple iPhones use multiple camera modules, sensors, cropping and processing methods that vary by model. Equivalent focal lengths above are image-composition hints, not a complete lens specification.

## 5. Photographic Styles → controllable prompt presets

**Important:** These are **creative approximations** of the visible result, not reconstructions of Apple's proprietary, scene-dependent implementation. Apple's system adjusts regions/colors intelligently, rather than simply overlaying one filter [A1, A3, A4].

| Preset | Tone | Color | Skin handling | Prompt fragment |
|---|---|---|---|---|
| `standard` | Balanced contrast, readable midtones | Natural, modest liveliness | Accurate-looking under ambient light | "Apple Camera-like Standard rendering: balanced tone, realistic local contrast and natural color" |
| `rich-contrast` | Deeper shadows, defined blacks, more pronounced contour | Restrained saturation compared with dramatic filters | Keep face readable; avoid crushed dark skin or harsh pores | "slightly deeper blacks and deliberate contrast, while retaining believable facial tonal detail" |
| `vibrant` | Balanced-to-bright midtones | More pop in colored objects, not all channels | Preserve actual skin hue while enhancing surroundings | "gently livelier blues, greens and colorful objects without oversaturating faces" |
| `warm` | Similar tonal balance unless specified | Shift mood gently warmer | Preserve varied skin undertones; no orange skin | "subtle warm amber daylight impression, believable neutrals and naturally varied skin" |
| `cool` | Similar tonal balance unless specified | Slightly cooler environmental cast | Skin remains human and alive, not blue/gray | "cooler ambient atmosphere with skin protected from excessive blue tint" |
| `bright` | Lift perceived luminosity and selected midtones | Clean, modest vibrance | Bright-looking skin without erasing tone or texture | "fresh clear light, gently brighter facial midtones and restrained vibrance" |
| `custom` | User-defined highlight/shadow/midtone direction | User-defined warmth/saturation | Preserve intrinsic subject colors | Use only the axes explicitly named by user |

**Availability context:** iPhone 13 introduced Photographic Styles. The iPhone 16 generation expanded tone/color customization with special attention to skin undertones. Apple's iPhone 17 materials document a Bright style. Apple's iPhone 18 Pro materials describe additional texture and grain controls. Do not imply all styles or controls exist identically on all generations [A1–A6].

### Intensity mapping

- `minimal`: unmistakably photographic, almost unstyled, strongest emphasis on physical lighting and color fidelity.
- `default`: familiar polished camera-phone JPEG/HEIC-like balance, mild enhancement that doesn't call attention to itself.
- `punchy`: a clearly noticeable but still credible Photo Style; slightly stronger contrast and color, **not** Instagram-era oversaturation or hyperreal HDR.

Never invent official numeric Tone/Color/Warmth slider values. If the user provides exact values, preserve them as user preferences but do not claim they map directly onto the image model.

## 6. Generational look profiles (soft, evidence-bounded)

**How to use:** Specify a generation only to select *tendencies or relevant advertised capabilities*. Generation alone must not rigidly determine white balance, skin color, optics or an exact LUT. Variations caused by lighting and the chosen scene are much larger than a simplified year-based formula.

| Target | Documented technology (context) | Safe prompting implication | Avoid claiming |
|---|---|---|---|
| iPhone 13 / 13 Pro | Smart HDR 4, Deep Fusion, Photographic Styles; Pro models support ProRAW [A1, A2] | Natural Smart HDR-like scene balance, crisp daytime textures, original style family | Exact "iPhone 13 color curve" |
| iPhone 14 | Photonic Engine with earlier Deep Fusion processing for mid/low light [A7] | Relatively controlled mid/low-light detail with phone-like smoothing | Reproducing Apple's fusion algorithm |
| iPhone 15 / 15 Pro | Improved Smart HDR and skin rendering; 48MP HEIF on 15 Pro [A8, A9] | Believable skin under high-contrast light; locally balanced highlight/shadow rendering | True 48MP or spectral accuracy from prompt alone |
| iPhone 16 / 16 Pro | Next-generation Photographic Styles with local color, highlight and shadow control, including skin undertones [A3] | Use region-aware style instruction; preserve skin from global tint | Copying Apple's exact per-pixel masks |
| iPhone 17 / 17 Pro | Updated Photonic Engine / next-gen Styles; Bright style on supported software [A4, A5] | Modest bright clean look with natural detail and believable noise | Guarantee of literal device output |
| iPhone 18 Pro | Variable aperture, new computational pipeline and style texture/grain controls [A6] | Allow more explicit depth-of-field, grain and texture choices when asked | Genuine variable-aperture capture, sensor signature or Reference Image |

**Default:** For an unspecified modern iPhone, adopt the `standard` preset with realistic illumination, balanced tone and moderate mobile-camera detail. Do not randomly combine the most extreme qualities of every generation.

## 7. Scene-to-scene photographic behavior

### 7.1 Outdoor daylight

- White balance follows actual sunlight/sky conditions; concrete, white clothing and gray surfaces retain believable neutrality.
- Expect detailed foliage, moderate crispness, bright skies with natural gradients, practical high dynamic range in high contrast.
- Prefer regular street-level viewpoint, imperfect but readable framing and natural human proportions.

### 7.2 Overcast / cloudy

- Soft shadows, gentle tonal contrast, slightly cooler ambient quality, richer midtone detail.
- Color still exists; overcast must not become desaturated film noir unless requested.
- Avoid fake hard sunlight and strong orange rim lighting.

### 7.3 Golden hour

- Real low-angle directional warm light and long shadows; cool-ish skylight fill is plausible.
- Warm highlights should come from illumination, not a global orange layer.
- Avoid turning neutral white objects fluorescent yellow.

### 7.4 Indoor window or office light

- Daylight from window, overhead light spill, local shadow transitions, glass/metal reflections.
- Mild white-balance compromise is realistic if warm and cool sources coexist.
- Preserve human skin texture and ambient context; avoid studio softbox perfection by default.

### 7.5 Restaurant, neon and mixed lighting

- Maintain local warm lamps, cool windows and colored signage; not every region must be neutralized.
- Protect skin from saturation spill as far as real illumination allows.
- Highlight halos/bloom should be restrained and attached to actual luminous objects.

### 7.6 Night mode-like

- A somewhat brighter-than-eye-expectation but still nighttime environment; stationary elements more detailed than moving ones.
- Controlled highlight clipping from headlights or streetlights; imperfect shadows, realistic sky darkness.
- Exposure fusion may be suggested visually but never asserted as actually performed.
- Avoid artificial blue daylight skies at midnight and perfectly noiseless shadow areas.

### 7.7 Portraits / people

- Prioritize skin identity, tone range, texture, expression and anatomically plausible hands.
- Eye and hair detail natural, not aggressively crystalline.
- If no Portrait mode requested, keep ambient background sufficiently legible; do not produce f/1.2 full-frame bokeh.
- Respect the person's actual complexion and scene lighting rather than enforcing a single universal "Apple skin tone."

### 7.8 Food, products and interiors

- Food: retain real texture and appetizing yet believable ingredient colors; allow occasional imperfect placement.
- Products: true-to-reference hue is more important than "vibrant" presets; avoid changing branded colors.
- Interiors: wide-angle perspective without impossible geometry; daylight/window exposure balanced but not unnaturally flat.

## 8. Prompt assembly system

### 8.1 Main prompt structure

Write one continuous prompt using this sequence:

```text
[SCENE/CONTENT — who, what, where, action, essential details].
Authentic handheld photo made with [CAMERA VIEWPOINT / FOV] on a [GENERATION, IF REQUESTED] iPhone,
photographed from [DISTANCE / HEIGHT / ANGLE] in [ACTUAL LIGHTING].
[COLOR BEHAVIOR: natural skin and neutrals, selective saturation, white balance].
[TONE: plausible highlight roll-off, shadow detail, local contrast, exposure].
[TEXTURE: camera-phone edge detail, scene-specific noise and natural surfaces].
[STYLE PRESET, IF ANY]. [FRAMING: crop/aspect ratio, imperfections].
Natural real-world documentary photograph, no studio/cinematic treatment.
```

Use "made with" as an artistic *look direction*, not a factual provenance statement about generated pixels. For high-integrity contexts, prefer "**with the appearance of** an iPhone photograph."

### 8.2 Compact master prompt

```text
Create a candid, photorealistic still image of {SUBJECT} {ACTION} in {LOCATION} at {TIME}.
Make it look like a genuine handheld photo from the native iPhone Camera app:
{LENS} perspective, natural human camera height, realistic ambient illumination,
balanced computational-looking highlights and shadows, believable scene-dependent
white balance, rich but controlled colors, natural varied skin tones, crisp yet
unforced detail, and ordinary smartphone depth of field. Apply {STYLE} subtly.
Preserve realistic materials, small framing imperfections and environmental context.
Avoid filmic color grading, heavy bokeh, HDR halos, CGI smoothness and perfect studio lighting.
{IMPORTANT SUBJECT CONSTRAINTS}; {ASPECT RATIO}.
```

### 8.3 Minimal editing prompt (existing photo)

```text
Keep the original image's people, faces, identity, pose, objects, framing and scene
unchanged. Adjust only the photographic rendering so that it resembles a believable
native iPhone {GENERATION OR MODERN} photo with the {STYLE} look: natural skin and
neutral color, realistic white balance for the existing illumination, restrained
local highlight/shadow balancing, normal smartphone-like sharpness and subtle
scene-appropriate noise. Do not replace objects, invent features, add portrait blur,
or fabricate EXIF/ICC metadata.
```

### 8.4 When the user needs accurate commercial color

Replace subjective aesthetic words with:

```text
Preserve the original object's reference hue, saturation and material appearance
under neutral, known illumination. Use neutral color balance, realistic soft
shadows, undistorted product geometry and restrained contrast. Do not add a
photographic style that shifts brand colors. A generated appearance is not a
colorimetric measurement; verify against a real reference if exact accuracy matters.
```

## 9. Ready-to-use scene recipes

### Recipe A — everyday city snapshot

```text
A candid handheld photograph of two friends crossing a busy neighborhood street
in late afternoon, shop windows and pedestrians in the background. Eye-height
rear 1x iPhone-camera perspective, moderately wide natural framing, ordinary
subject distance, clear but not overprocessed building detail, subtle shadow
recovery under the awnings, believable sky highlights, lifelike skin undertones,
slightly lively city colors without neon saturation, normal smartphone depth of
field. Unposed expressions, one small framing imperfection, believable motion.
Standard color rendering, 4:3 landscape. No editorial fashion lighting or DSLR bokeh.
```

### Recipe B — indoor portrait, natural skin

```text
A spontaneous portrait of a person talking at a cafe table beside a window,
photographed from across the table with an iPhone rear main 1x camera. Soft daylight
on the face and dim warm interior light behind, natural skin undertones and fine
texture, credible white-balance compromise, moderate local contrast, subtle detail
in background chairs and mugs, practical window highlight roll-off. Standard style,
3:4 portrait. No beauty retouching, orange skin, studio flash or artificial blur.
```

### Recipe C — vibrant vacation landscape

```text
An ordinary traveler photograph of a rocky tropical cove and turquoise water,
shot by hand from a walking path on a modern iPhone rear main camera in clear
morning light. Realistic distant haze, crisp foreground stone and leaves, naturally
bright water, controlled sky saturation and plausible cloud highlights. Apply a
restrained Vibrant Photographic Style-like treatment mainly to water and vegetation;
keep shadows and white foam neutral. Wide environmental depth of field, 4:3.
No hyperreal HDR, impossible color or drone perspective.
```

### Recipe D — warm evening family photo

```text
A handheld group photo of family members laughing around an outdoor patio table
just before sunset, seen from standing height with a modern iPhone 1x camera.
Low angled warm sunlight, cooler open-sky fill, believable cast shadows, varied
individual skin tones preserved, slight localized highlight balancing and gentle
warmth in sunlit objects. Ordinary clutter on the table, natural expressions,
most faces reasonably in focus, not professional portrait bokeh. 4:3 landscape.
```

### Recipe E — realistic night street

```text
An unposed handheld iPhone-like night photograph of a person waiting outside a
small convenience store in the rain. Shop fluorescent light mixes with amber
streetlights and reflected car lights on wet pavement. Night-mode-like shadow
visibility without looking like daylight, some fine shadow noise, slight softness
on distant moving people, stationary lettering and windows reasonably legible,
natural skin not made orange or blue, controlled glowing practical lights.
Standard rendering, 3:4 portrait. No cyberpunk neon grade or extreme HDR bloom.
```

### Recipe F — casual food photo

```text
A believable quick iPhone photo of a bowl of noodles at a modest restaurant,
shot from seated height at a slight diagonal angle. Warm mixed indoor illumination,
true-to-food color with a gentle lively finish, natural glistening highlights,
visible noodle and vegetable texture, background condiments and table edge in
recognizable focus, normal main-camera depth of field. Natural casual framing,
no advertising studio lights, fake steam clouds or orange saturation blanket.
```

### Recipe G — front camera selfie

```text
A casual handheld front-camera selfie of two friends on a crowded sidewalk on an
overcast morning, taken at normal arm's length. Slight perspective enlargement of
the nearer face, visible street background, soft sky light with lifelike facial
shading, credible skin texture, gentle computational tone balance and modest
smartphone detail. Some background busyness, spontaneous imperfect smiles, not a
beauty-filtered studio portrait. 3:4 portrait.
```

### Recipe H — iPhone 18 Pro-inspired environmental portrait

```text
A natural environmental portrait of an artisan working near a workshop window,
as if photographed using an iPhone 18 Pro rear main camera with a moderate
aperture choice. Believable separation without extreme blur; hands and primary
work surface in useful focus. Natural material texture and fine facial detail,
subtle option for restrained photographic grain, precisely directed daylight,
locally balanced shadows and highlights, Standard color with realistic complexion.
3:4 portrait. This is a visual simulation, not actual signed camera data.
```

## 10. Color profile, format and HDR instructions for downstream delivery

**Never confuse image appearance with file metadata.** Generative models commonly output SDR PNG/JPEG/WebP or another service-specific raster. The image's actual profile, bit depth and HDR metadata must be inspected after generation; a phrase inside the image prompt does **not** embed ICC tags or create gain maps.

| Concept | What it means | Image-model behavior | Real post-export action |
|---|---|---|---|
| `sRGB` | Standard RGB encoding/color space, generally safe for broadly compatible sharing | May guide moderate, realistic gamut appearance; not proof of ICC tagging | Convert to sRGB using color-managed software and embed the profile |
| `Display P3` | Wider gamut than sRGB, with D65 white point and sRGB-style tone curve | May suggest richer authentic chroma where physically supported, but cannot guarantee P3 data | Convert from a known source profile to Display P3; embed profile; verify wide-gamut viewer |
| ICC profile | Numeric interpretation of encoded colors | Cannot be reliably authored by prose | Inspect, assign **only if source interpretation is known**, or convert with a CMS |
| JPEG | Usually lossy delivered raster, frequently SDR 8-bit per channel in common workflows | The look can be approximated; compression is an export operation | Export high-quality JPEG with embedded ICC |
| HEIC/HEIF | Container/encoding family; supports efficient still-image workflows | Prompt alone cannot produce valid HEIF container features | Export with real HEIF tooling if available |
| ProRAW DNG | Apple computationally processed RAW-like capture file | Cannot be generated authentically by prompt | Capture on a supported iPhone; retain original DNG for raw editing |
| HDR gain map | Auxiliary data used for extended HDR display behavior | "HDR look" is not a real gain map | Use actual HDR-capable software/format and verify playback |

**Important color-management rules:**

1. A wider gamut is not evidence that a photograph has more accurate colors.
2. A color-space conversion changes RGB numbers to preserve appearance as closely as possible; *assigning* a different profile reinterprets unchanged RGB numbers and can visibly shift colors [A12].
3. A bright, contrast-rich SDR simulation is not a true HDR photo.
4. Output depends on the display, app, ambient illumination and whether wide-color/HDR metadata survive posting.
5. When unsure about a web destination, deliver a color-managed **sRGB SDR JPEG**, and keep a higher-quality original separately.
6. For professional matching, compare on a calibrated or appropriately profiled display, disable or standardize True Tone/Night Shift and use physical color references; don't promise instrument-grade fidelity from generative prompting.

## 11. Failure patterns and negative prompt

### Hard failures

- Face colors become identically orange or magenta despite varied natural complexions.
- Background is melted into full-frame portrait bokeh for an ordinary 1x photo.
- Sky, clouds, skin, foliage and interiors all have equally lifted shadows and no luminous hierarchy.
- Over-sharpening creates bright/dark outlines, digital grit or plastic textures.
- Image is editorially posed, overlit, cinematic, hyperrealistic or excessively symmetrical despite a candid brief.
- Lens perspective is impossible for the requested shot distance.
- Physical objects, signage, hands or architecture are visibly malformed.
- The result fakes a camera provenance statement, EXIF metadata or signed sensor authenticity.

### Optional negative prompt

```text
CGI, 3D render, illustration, plastic skin, beauty filter, fashion editorial lighting,
cinematic teal-orange color grade, extreme HDR, surreal saturation, crushed skin
shadows, fluorescent greenery, cyan sky clipping, excessive bloom, sharpening
halos, crunchy microcontrast, fake fine detail, noise-free night, oversmoothed
faces, medium-format bokeh, implausible perspective, artificial studio symmetry,
fake film scratches, watermarks, image metadata overlays, fabricated EXIF text
```

Do **not** include an absurdly long negative list if the model handles negatives poorly. Use 3–8 highest-risk constraints for that scene.

## 12. QA rubric and revision logic

Score each category **0 = fails, 1 = partly plausible, 2 = convincing**; maximum 16.

| Criterion | Pass question |
|---|---|
| Scene faithfulness | Are the requested people, objects, actions and location visibly correct? |
| Camera perspective | Could a person capture this composition from the stated phone viewpoint? |
| Illumination | Are light direction, shadows and practical sources physically coherent? |
| Color integrity | Do skin, neutrals and distinctive subject colors remain believable? |
| Tone / HDR restraint | Is contrast readable without local HDR halos or globally flat lighting? |
| Detail / noise | Does sharpening and texture resemble a phone photograph at this light level? |
| Focus / depth | Is blur consistent with camera and distance, without automatic DSLR bokeh? |
| Snapshot credibility | Does it feel observed and unforced rather than staged or computer-rendered? |

**Acceptance:** 14–16 excellent; 11–13 usable with targeted fixes; 0–10 revise before delivery. This score is a heuristic, not a measured benchmark.

**Revision order:** wrong identity/content → lighting → perspective → skin/white balance → contrast/HDR → background blur → noise/sharpening → aesthetic polish.

Useful targeted corrections:

- Too cinematic → "remove editorial lighting and stylized color grade; replace with ordinary ambient light and candid composition."
- Too saturated → "reduce global saturation; preserve only naturally saturated scene objects."
- Skin orange → "neutralize skin cast while preserving complexions, individual undertones, ambient warmth and texture."
- Overprocessed HDR → "restore natural contrast and small clipped highlights; reduce local edge halos and shadow lifting."
- Looks like DSLR → "increase environmental context and depth of field, use natural 1x smartphone perspective, eliminate artificial large-aperture bokeh."
- Too clean at night → "restore low-light limits: subtle shadow noise, slightly softened distant details, truthful lamp highlights."
- Too artificial → "replace symmetry and spotless perfection with modest real-world irregularities appropriate to the scene."

## 13. Guidance for multi-image consistency

When producing a series, keep these fixed unless instructed otherwise:

- Person/subject identity, clothing, physical features and distinct material colors.
- Camera family, default camera module, approximate shooting distance and aspect ratio.
- Rendering style and its intensity; skin/neutral color handling.
- Ambient light direction, weather and scene continuity where relevant.

Allow naturally varying auto-exposure and white-balance behavior across environments; not every frame should have an identical filter. Do not claim hidden photo metadata proves consistency.

## 14. Final response/output protocol

**For direct image generation:** Generate the image; avoid explaining the process unless asked. If supplying optional text, state only the chosen appearance (for example, "Standard-style, handheld rear 1×, cloudy daylight"). Do not announce real iPhone provenance.

**For prompt-writing requests:** Return exactly one ready-to-paste best prompt, plus a concise negative prompt if useful. Include requested model/style settings; default intelligently for unspecified details.

**For image-editing requests:** Preserve existing identity, objects and composition by default. Only change photographic appearance, color/tone, blur and texture as permitted. Be explicit that the edited output is a stylization, not a newly captured real photograph.

**For high-fidelity/professional deliverables:** Distinguish the visual prompt from actual ICC conversion, bit depth, HDR handling, and export. If needed, provide a separate real color-management process.

## 15. Evidence register and source notes

The generation guidance above uses **documented platform features** as background, while its exact visual recipes are **creative heuristics**. Apple does not publicly specify every proprietary ISP operation, scene mask, hue curve or model-dependent rendering matrix required to reproduce its pipeline exactly.

| ID | Publisher, date | Evidence used | Primary URL |
|---|---|---|---|
| A1 | Apple Newsroom, **2021-09-14** | iPhone 13; Smart HDR 4 and introduction of Photographic Styles | https://www.apple.com/newsroom/2021/09/apple-introduces-iphone-13-and-iphone-13-mini/ |
| A2 | Apple Newsroom, **2021-09** | iPhone 13 Pro; Deep Fusion, Smart HDR, ProRAW and styles | https://www.apple.com/newsroom/2021/09/apple-unveils-iphone-13-pro-and-iphone-13-pro-max-more-pro-than-ever-before/ |
| A3 | Apple Newsroom, **2024-09** | iPhone 16 Pro; locally adjusted tone/color and skin undertones | https://www.apple.com/newsroom/2024/09/apple-debuts-iphone-16-pro-and-iphone-16-pro-max/ |
| A4 | Apple Newsroom, **2025-09-09** | iPhone 17 Pro; updated Photonic Engine and Bright style | https://www.apple.com/newsroom/2025/09/apple-unveils-iphone-17-pro-and-iphone-17-pro-max/ |
| A5 | Apple Newsroom, **2025-09** | iPhone 17; next-generation Photographic Styles | https://www.apple.com/newsroom/2025/09/apple-debuts-iphone-17/ |
| A6 | Apple Newsroom, **2026-09** | iPhone 18 Pro; variable aperture and Photographic Styles texture/grain controls | https://www.apple.com/newsroom/2026/09/apple-debuts-iphone-18-pro-and-iphone-18-pro-max/ |
| A7 | Apple Newsroom, **2022-09-07** | iPhone 14; Photonic Engine applies Deep Fusion benefits earlier | https://www.apple.com/newsroom/2022/09/apple-introduces-iphone-14-and-iphone-14-plus/ |
| A8 | Apple Newsroom, **2023-09** | iPhone 15 Smart HDR, rendering in difficult light, skin tone claims | https://www.apple.com/newsroom/2023/09/apple-debuts-iphone-15-and-iphone-15-plus/ |
| A9 | Apple Newsroom, **2023-09** | iPhone 15 Pro; 48MP HEIF and portrait/Smart HDR capabilities | https://www.apple.com/newsroom/2023/09/apple-unveils-iphone-15-pro-and-iphone-15-pro-max/ |
| A10 | Apple Support, **living documentation, accessed 2026-10-12** | Photographic Styles adjustment, latest-generation features | https://support.apple.com/en-ie/guide/iphone/iph629d2cd37/27/ios/27 |
| A11 | Apple Support, **living documentation, accessed 2026-10-12** | ProRAW combines RAW information and iPhone image processing, uses DNG | https://support.apple.com/en-ie/119916 |
| A12 | Adobe Photoshop Help, **updated 2026-10-06** | Assign versus convert profiles and export implications | https://helpx.adobe.com/photoshop/desktop/adjust-color/color-profiles/change-a-documents-color-profile.html |
| A13 | Apple Developer, **WWDC 2016** | Display P3 primaries; sRGB-like transfer function; D65 white | https://developer.apple.com/videos/play/wwdc2016/501/ |
| A14 | Apple Developer, **living documentation** | Why embedding and managing sRGB/P3 color profiles matters | https://developer.apple.com/design/human-interface-guidelines/color |
| A15 | Apple Developer, **living documentation** | Apple HDR auxiliary gain map versus base photographic image | https://developer.apple.com/documentation/appkit/applying-apple-hdr-effect-to-your-photos |

### Reliability labels for downstream agents

- **Documented:** Model capabilities, Apple's supported style controls, existence of ProRAW/HEIF/P3, gain-map formats and profile conversions (subject to platform/software version).
- **Interpretive:** "balanced iPhone contrast," "lively but natural color," "a little edge crispness," and the scene-specific recipes. These are aesthetic approximations, not Apple measurements.
- **Unsupported if asserted as factual:** Precise Apple tone curves, neural-network layers, semantic color masks, model-specific LUTs, proprietary sensor-to-P3 transformations, exact camera-original bit depth from a text prompt, or verified shot-on-iPhone origin for generated images.

---

## Quick-start invocation

**Input:** `Create an image of [subject and setting], like it was taken on an iPhone, [optional lens / generation / style / lighting].`

**Required result:** A believable spontaneous photograph with context-aware light, convincing skin/neutrals, restrained computational-looking tone, suitable phone optics, credible texture/noise and no cinematic over-processing.

**Default all-purpose suffix:**

```text
Photorealistic handheld native-iPhone-camera aesthetic; 1x rear main-camera
perspective at natural eye height; ordinary candid framing; realistic ambient
lighting; accurate-looking skin undertones and neutral colors; controlled but
lively saturation; gentle computational-style highlight and shadow balancing;
credible smartphone sharpness, natural texture and depth of field; subtle
real-world imperfections; no studio glamor, cinematic LUT, exaggerated HDR,
waxy skin, oversharpened halos or full-frame DSLR bokeh.
```

## UGC avatar framing in this template

For UGC, preserve the complete head/hair and both full hands with practical gesture margins. There is no mandatory empty top-30% rule. Avoid forced warm casts, gratuitous defects or handheld staging that contradicts the fixed-camera/two-free-hands brief. The selected brief wins over generic photo recipes. Reference stills and moving performances have different mouth/gesture requirements.
