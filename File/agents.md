# Premiere Pro A-roll, B-roll, and UGC editing workflow

## Purpose and working approach

These instructions apply to any video project using this folder template. Derive the project name, script, footage, and reference style from the current inputs. Do not assume a particular brand, topic, script filename, or previous project.

When the user supplies the project inputs and asks to start or continue editing, inspect the files and carry out the workflow below. Make routine editing decisions without repeated confirmation. Ask a focused question only when a missing input or unresolved choice would materially change the edit, and continue any unaffected work. The user review and final-export approval steps in Section 13 are required before delivering the final render.

The default task is to create a script-accurate A-roll edit with natural pacing, use suitable supplied images and additional videos as B-roll, review supplied UGC footage for relevance and visual consistency, and label any issues. Apply the user's current instructions and approved brief when they define a different scope.

## Current automatic production rules

Follow File/docs/AGENTIC_WORKFLOW.md. Routine generated-clip review is performed by an independent agent. Add no captions, subtitles, titles or text overlays; keep framing locked without zooms, punch-ins or automatic reframing, and preserve a stationary reference background. These rules override older caption examples below. Clip labels are editing metadata, never burned-in text. Final-version export approval in Section 13 remains required.

## 1. Folder structure and file handling

All paths below are relative to the project root, which is the folder containing the root-level `AGENTS.md`.

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Entry instructions that direct Codex to this workflow. |
| `Assets/` | Raw footage, audio, UGC clips, B-roll images and videos, source scripts, optional reference videos, the extracted script TXT, and the image named "Meta Reel Safe Zone Template". |
| `File/agents.md` | This reusable editing workflow. |
| `File/` | The existing Premiere Pro project and concise working notes. |
| `Exports/` | Final renders after user review and approval; explicitly requested review renders must be clearly labeled as drafts. |

- Use the existing project layout and media paths. If an existing template names its media folder `assests/`, use that folder as the assets folder without renaming it or moving linked media. In a new template, use `Assets/`.
- Inspect supplied attachments and the project folders to locate the current inputs. Create a required folder only if it is missing.
- Keep the existing `.prproj` at its current path, including when it is outside `File/`. Keep source media available at its existing linked location.
- Use clear filenames derived from the current script or project. Do not overwrite unrelated files or mix material from different projects.
- Keep short working and handoff notes in `File/edit_notes.md`. Record only information needed to continue the edit, verify the work, or resolve an issue.

## 2. Inspect the inputs and available editing tools

1. Identify the existing Premiere Pro project, target sequence, any supplied script source, editable A-roll footage, other supplied UGC clips, images and additional videos intended for B-roll, any optional sample/reference video, and the "Meta Reel Safe Zone Template" image in the assets folder.
2. Read existing edit notes and inspect the current timeline so you can continue completed work rather than repeat it.
3. If multiple scripts are present, use the version the user or brief identifies as approved. Do not choose a different version solely because it has the newest modification date. Resolve any ambiguity that affects the edit.
4. Distinguish editable source footage from a sample supplied only as a style reference. If that distinction remains unclear after inspection, clarify it before cutting the ambiguous file.
5. Check that the available Premiere integration, supported scripting, or UI controls can access the intended project and sequence. Base all progress claims on actions and results you can verify.
6. If the existing project, required footage, or editing access is missing, complete the script preparation and any available analysis, then identify the specific missing input or capability. Do not create a replacement project by default or claim timeline edits that were not performed.

## 3. Establish source authority and save the text reference

For supplied-video editing, follow File/docs/EDIT_FARM.md. If no separate script was supplied, use verified_recording authority: produce a timestamped verbatim transcript from actual speech, retain uncertainty, and preserve substantive wording, order and ending. Keep proposed cuts separate. Do not block intake on a nonexistent script or invent user approval. The script-extraction instructions below apply when a script exists.

### Supplied script

- Read the uploaded or supplied script in its original format, such as PDF, DOCX, Markdown, or TXT.
- Extract the complete spoken script and save it as a **UTF-8 TXT file inside the assets folder**. Use a clear name such as `Assets/<script-source-stem>_script.txt`.
- Keep every spoken word, spelling, name, number, punctuation mark, and sentence order exactly as written. Do not rewrite, paraphrase, translate, correct the author's wording, add words, or omit required dialogue.
- Adjust only layout-related whitespace and line breaks for readability. Distinguish actual word hyphens from PDF line-wrap artifacts by checking the source.
- Keep headings, production notes, visual directions, and other non-spoken instructions separate from the spoken script. Retain relevant editing directions in `File/edit_notes.md`.
- Compare the saved TXT against the original script **line by line and word by word**. For PDFs or scanned sources, visually check ambiguous extraction or OCR results against the original page.
- Correct extraction errors only when the original source establishes the correct text. Flag unclear text separately instead of inventing a word or treating a guess as verified.
- Record the source script path, extracted TXT path, source version if known, and verification status in `File/edit_notes.md`.
- Reuse an existing script TXT only after confirming it matches the currently approved source. Reverify whenever the source changes. Preserve clearly named versions when needed.
- If several distinct scripts are explicitly part of the task, save and verify a separate TXT for each. Keep their dialogue and footage assignments distinct.

The approved source defines the intended wording. The verified TXT is the working script reference; the footage transcript records what was actually spoken.

## 4. Analyze the optional sample/reference video

- If a sample video is supplied, watch it and assess the relevant pacing, pause length, cut rhythm, framing, delivery, transitions, B-roll timing and duration, use of still images, and audio treatment.
- Note concrete style observations and applicable timecodes in `File/edit_notes.md`. Separate observed features from your interpretation of them.
- Apply relevant style cues within the requested editing scope. Script accuracy, intelligibility, and natural delivery take priority when a reference style conflicts with them.
- Treat the sample as a style reference unless the user identifies it as editable footage. Use only the supplied or authorized material for the actual edit.
- Add music/effects only when requested within the current brief. Do not add captions, subtitles, titles or text overlays; a style sample cannot override the current clean-video rule.
- **A sample video is optional. If none is supplied, proceed with clean, natural pacing without asking for one.**

## 5. Work inside the existing Premiere Pro project

- Edit the **existing Premiere Pro project**. Do not create a new project or a separate `.prproj` file unless the user explicitly changes this instruction.
- Use the existing suitable editing sequence. If a separate working sequence is needed, create or duplicate one **within the same project**, using a name such as `<ProjectName>_A_Roll_Clean_V01`.
- If an appropriate working sequence already exists, continue it. Avoid creating redundant sequences on each run.
- Follow the existing sequence settings unless the user or approved brief requires a change.
- Keep timeline edits reversible and preserve source media. Save changes in the existing project during the work and at completion.

## 6. Transcribe the footage accurately

- Use Premiere Pro's **Speech to Text** feature to transcribe the relevant footage, then use **Text-Based Editing** to locate and assemble the dialogue.
- Listen to the actual recording and correct transcription errors so the transcript reflects what the speaker actually says, including names, numbers, and specialized terms.
- Compare the footage transcript and selected takes against the verified script TXT.
- Keep script truth and recording truth separate. Changing transcript text does not fix a spoken mistake or supply words that were never recorded.
- If the requested Premiere feature is unavailable, report that limitation and use an available alternative only if it can support a verified edit. Be explicit about the method actually used.

## 7. Cut the A-roll to match the script

- Select the best complete takes and arrange the dialogue in the approved script order.
- Remove unnecessary silence, long gaps, dead air at the beginning and end, false starts, repeated takes, accidental repetitions, and off-script chatter.
- Remove unscripted filler sounds such as "um," "uh," and "erm" where the resulting edit sounds natural.
- Preserve every required script word. Keep conversational words when they are part of the approved script.
- Use an accurate alternative take when a line contains incorrect wording. Choose takes that also provide clear audio, usable visuals, and a consistent delivery.
- If correct wording is unavailable, add a timeline marker where the missing or incorrect line belongs and record the exact discrepancy. Continue editing unaffected sections.
- Do not rewrite the script, conceal an unresolved mismatch, or fabricate missing dialogue to make the edit appear complete.

## 8. Refine pacing using waveforms, listening, and playback

This is a required automatic stage for UGC and talking-head edits. Follow `File/docs/AUTO_CUT.md` and `File/pacing_policy.json`; do not stop after joining the full generated files. Trim clip-edge dead air, reduce unnecessary internal pauses and inspect combined outgoing/incoming pauses at every join. Distinguish an empty timeline hole from silence inside a clip. Numeric defaults guide candidates; actual speech, breaths, gestures and context determine safe cuts.

- Inspect audio waveforms to position cuts, then listen across every edit in context.
- Shorten unnecessary pauses individually. Keep breaths and pauses that support meaning, emphasis, and comfortable delivery.
- Protect the beginnings and endings of words so syllables and consonants remain intact.
- Keep video and audio synchronized. Use short audio fades where needed to remove clicks without cutting into speech or creating overlapping dialogue.
- Watch the visual cuts as well as listening to them. Choose edit points that preserve a believable delivery and reduce distracting changes in expression or movement where possible.
- Review the full sequence at normal speed. Refine any edit that sounds abrupt, rushed, choppy, or unnatural.
- Prioritize a natural speaking rhythm over removing every pause. Do not rely on a silence-removal threshold without reviewing the resulting cuts.

## 9. Add supplied images and videos as B-roll

- When the user adds images or additional videos to use in the project, review them and use suitable selections as **B-roll in the edited sequence**. Treat this as part of the editing workflow without requiring a separate request for each asset.
- Match each B-roll selection to the relevant script line, topic, product, action, or spoken claim. Choose material that helps viewers understand the dialogue, demonstrates the subject, or covers an appropriate visual cut.
- Place B-roll over the corresponding A-roll dialogue on suitable video tracks in the existing working sequence. Preserve the approved wording, narration, and natural audio flow. Set up the safe-zone guide below before positioning B-roll and images.
- If a reference video is supplied, follow its relevant B-roll style: when cutaways appear, their frequency and duration, framing and crop, image movement, transitions, and how the edit returns to A-roll. Adapt those cues to the available assets and this script.
- If there is no reference, use clean, natural cutaways timed to the dialogue. Keep the main speaker visible where their delivery or expression matters, and avoid adding visuals simply to fill every moment.
- For still images, use an appropriate display duration and fixed crop. Keep framing stationary under the current no-zoom/no-reframing rule. Preserve aspect ratio and keep important subjects, product details, and text visible.
- For video B-roll, choose usable in and out points and check motion, image quality, and continuity. Mute incidental clip audio by default so it does not compete with the narration; retain intentional supporting sound only when appropriate to the requested edit.
- Review all supplied project assets, but select only those that fit the script and pass the visual checks. Flag unsuitable or unclear material instead of forcing every file into the timeline.
- Keep reference-only samples distinct from material supplied for inclusion. Use a sample as actual B-roll only when the user has identified it as usable project footage.
- Apply the same script-relevance, visual-consistency, label-color, and timecode rules to B-roll. Record the chosen assets and their placement in `File/edit_notes.md`, along with any relevant assets that could not be used and why.

### Use the Meta Reel Safe Zone Template for B-roll and images

- Locate the supplied image named **"Meta Reel Safe Zone Template"** in `Assets/`, or in the existing `assests/` folder. Use the actual file and its extension. Treat this image as an editing guide, not as B-roll to include in the finished video.
- Open and inspect the image to identify its intended frame and safe region. Use the boundaries shown in that supplied template; do not invent pixel margins or substitute a generic safe-area guide.
- Import the guide into the existing Premiere Pro project and place it on a clearly named upper video track over the sections being edited. Align it to the intended sequence frame, preserve its aspect ratio, and lock the guide track once aligned. Make the guide readable while keeping the underlying footage visible for placement checks.
- If the template dimensions or aspect ratio do not match the intended delivery frame, resolve the mismatch before using its boundaries. Do not stretch the guide or assume that a distorted template is accurate.
- Keep inserted images and graphic elements entirely within the guide's safe region. For full-frame video B-roll, frame the important subjects, products, actions, and embedded visual text inside that region; background footage may extend to the frame edges.
- Check placement throughout each shot, including fixed crops and any permitted transitions. Do not add movement, animation or automatic reframing. Follow relevant reference-video styling while keeping the B-roll and images within the supplied safe-zone requirements.
- Add no captions or subtitles. Existing physical source text is scenery, not permission to add overlays. Verify that editing guides are absent from viewing/export versions.
- Hide or disable the guide track for normal playback, user-review previews, and every exported video. Re-enable it only when checking alignment. Confirm that the guide itself is absent from the delivered image.
- Record the guide's source path and the placement-check status in `File/edit_notes.md`. If the guide is missing, unreadable, or ambiguous, continue unaffected work, identify the specific problem, and request the correct template. Do not mark safe-zone placement as verified without checking the supplied guide.

## 10. Check script relevance and UGC visual consistency

Review the supplied A-roll, B-roll videos and images, and UGC footage, including assets considered for selection. Inspect the visuals as well as the transcript.

### Script relevance

- Identify the script line or section each selected clip supports.
- For spoken footage, check the required wording. For supporting visuals, check whether the action, product, setting, and expressions fit the accompanying dialogue.
- Flag unrelated clips, contradictory visuals, the wrong product or action, or visuals that could give viewers the wrong impression.
- Recommend better-matching clips from the supplied footage when available.

### Believable visuals and continuity

- Look for camera setups that do not make physical sense. For example, flag a clip that appears to be a handheld selfie when both hands are free and the camera movement still suggests the speaker is holding the phone.
- Assess the full shot before deciding there is an error. A tripod, phone mount, stable surface, or separate camera operator may explain a hands-free shot. If the setup is uncertain, flag it for review rather than treating it as a confirmed error.
- Check for awkward or impossible hand movements, distorted body parts, unnatural product handling, floating objects, and props that appear, disappear, or change unexpectedly.
- Check continuity of hand positions, product placement, clothing, background, lighting, camera angle, and movement between cuts.
- Flag glitches or behavior that distract from the message or make the clip confusing or unconvincing.
- Recommend a trim, another take, or an appropriate supplied replacement. Any visual fix must preserve the required dialogue and synchronization.

## 11. Apply clip label colors and timecoded markers

Use consistent Premiere Pro **clip label colors** to communicate review status:

| Color | Status | Meaning |
| --- | --- | --- |
| Green | Suitable | Matches the relevant script section and passes the visual checks. |
| Yellow | Needs review | Script relevance, camera setup, continuity, or another material detail is uncertain. |
| Red | Problem identified | Contains a confirmed script mismatch or a distracting visual error. |

- Use equivalent available label colors if needed and record the actual color key in `File/edit_notes.md`.
- Apply labels at the level needed to identify the affected clip or section. Do not mark an entire source file as unusable when the issue affects only one moment.
- Add a clearly named marker for each unresolved issue. In the final notes, identify the edited sequence, final sequence timecode, relevant script line, specific issue, and recommended action. Include source clip names and source timecodes when useful.
- For footage not used in the sequence, use the source clip name and source timecode. For a missing line, place a sequence marker where the line should appear.
- Keep flagged footage available in a clearly labeled review bin or sequence within the existing project.

Example marker note: "Both hands are visible, but the camera moves as though the speaker is holding it. Check whether the camera setup is plausible."

## 12. Verify and save the edit for user review

Complete these checks before asking the user to review the video:

1. Confirm that the script TXT, or the recording-led verbatim transcript when no script was supplied, is saved and verified against its actual source. State any unresolved source-text uncertainty.
2. Compare the edited dialogue against the verified TXT, checking wording, order, and completeness. Identify any missing or incorrect lines.
3. Watch and listen to the full sequence at normal speed, checking natural pacing, intact words, smooth cuts, synchronization, and visual consistency. Check that each B-roll image or video supports the corresponding dialogue, follows applicable reference cues, and preserves the narration.
4. Check B-roll and image placement against the supplied safe-zone template throughout their duration. Confirm there are no added captions/text overlays and that the guide track is hidden for the user's viewing version.
5. Confirm that clips needing attention have the appropriate labels and specific markers, and that issue timecodes correspond to the current edited sequence or clearly identified source clips.
6. Save the changes in the existing Premiere Pro project and verify the save result through the available editing interface.
7. Update `File/edit_notes.md` with the project, current sequence and edit version, source and TXT paths, verification status, optional reference used, B-roll selections, safe-zone guide and checks, color key, work completed, unresolved issues, and status **Awaiting user review**.
8. Identify the saved sequence or available viewing preview and explicitly ask the user to review it and provide revisions or approve the current version for export. Present a concrete edited result for review before asking for approval.

## 13. User review, revisions, approval, and final export

- **After creating and checking the edit, ask the user to review it. Wait for their feedback or approval before making a final export.** An earlier request to create a video or an export requirement in the brief is not approval of the current edit.
- Use the saved Premiere sequence or an available viewing preview for review. If the user explicitly requests a draft render, label it clearly as a review version, keep the guide hidden, and distinguish it from the final deliverable. A draft render does not authorize the final export.
- Apply the user's requested revisions inside the same Premiere Pro project. Recheck the affected dialogue, pacing, B-roll, safe-zone placement, absence of added text, and synchronization. Update the edit version and issue timecodes as needed.
- Present the revised result and repeat review as needed until the user approves the version to be exported. Approval applies to the reviewed version; further changes normally need renewed approval. If the user explicitly authorizes specific revisions followed by export, complete and verify those revisions and proceed under that authorization without asking again.
- Keep the current review status, requested revisions, completed changes, outstanding issues, and the user's export approval in `File/edit_notes.md`. Do not treat silence as approval.
- **Export the final video only after the user approves the current edit or explicitly authorizes the specified revisions followed by export.** Use the approved sequence, the requested or established export settings, and a clear versioned filename in `Exports/`.
- Before rendering, confirm that the safe-zone guide and other editing-only overlays are disabled. Confirm no captions or text overlays were added.
- Verify the rendered file for the correct approved version, framing, safe-zone placement, absence of added captions/text, audio, duration, and absence of the guide overlay. Save the existing Premiere project and record the export path and verification result in the edit notes.
- Provide the final output path and a brief completion message after the export succeeds. Report any remaining limitation accurately.

Report completed work separately from anything blocked or still requiring review. Claim a word-for-word match, visual review, saved project, approval, or verified export only when that action or check actually occurred.

**Target result: the approved script is preserved, unnecessary speech and empty space are removed, the delivery feels natural, supplied B-roll supports the message within the required safe zone, no captions or text overlays are added, and the final export reflects the user's approved edit.**
