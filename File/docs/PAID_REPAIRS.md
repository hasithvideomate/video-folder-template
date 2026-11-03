# Automatic paid repairs with one project allowance

Talking-avatar clip regeneration is built into `production_runner.py` and approved with the batch (BATCH_AUTOMATION.md, "Automatic regeneration"); it draws on the same project-wide 1000-credit allowance. The policy below is for image/reference repairs and other assets.

The user wants corrective generations to proceed without approving each new prompt. Use `File/scripts/repair_runner.py` to bind those requests to a **previously approved repair allowance**. This is an exception to per-payload approval only for repairs inside that allowance. Original generation, new assets, different creative direction, uncovered models, increased limits and final export keep their existing approval boundaries.

The standing repair allowance is **1000 additional Kie credits per project**, with two corrective attempts per asset by default. Apply File/repair_defaults.json; do not ask again for this amount or per-fix approval. At project setup, bind the selected assets, models and references to that scope instead of discovering after every failed review that the original credits were spent. Record the actual user evidence. The allowance states a separate total repair reservation, per-attempt limit, overall project limit including original work, eligible assets/references, models and full review checklist. An existing clear user authorization can cover it; do not ask again merely to obtain an approval hash. The master carries this reusable 1000-credit setting, but no populated project grant or credentials. The agent records the real standing authorization in the active project. For example, an authorized original-production total of 12 credits plus this allowance gives a full project ceiling of 1012 credits; the repair allowance itself remains 1000. Do not infer authorization for unrelated production or larger limits.

## Authorize once

The coordinator writes a versioned JSON policy in the active project's File/jobs. Policy fields (repair amount and attempt count may use the saved defaults):

- `version: 1`, stable `id`, actual coordinator `producer_id`.
- `repairCapCredits`: total repair reservation, defaulting to 1000 when omitted; `perAttemptCapCredits`: maximum reservation per correction; `projectCapCredits`: total project ceiling including original work and repairs. These are explicit positive decimal strings with at most four decimal places. Per-attempt <= repairs <= project.
- `maxAttemptsPerAsset`: positive integer, defaulting to two when omitted. No reset by renaming a take.
- `models`: exact verified provider model IDs. `modelTemplates`: one contract per model, each containing its fixed `{model,input}` payload, `prompt_field` and `images_field` (distinct existing dotted fields under input). Only the prompt and one ordered source-plus-reference URL array may vary. This adapter requires a model with that supported input contract; it does not invent mappings for other endpoints.
- `allowedChecks`: repairable defects; `requiredReviewChecks`: the complete applicable checklist, including those defects and identity/scene/source preservation. Choose the real mode's full review criteria rather than only the original failure.
- `assets`: explicit records with stable `id`, original `source` file, nonempty selected `references` file list and `preserve` description specifying unchanged characters, scene, source action, dialogue/style/settings as applicable. Keep originals intact. Actual fingerprints are frozen by prepare.

```sh
python3 File/scripts/repair_runner.py prepare --policy File/jobs/repair-allowance.json
# Only after actual user authorization of the displayed scope and limits:
python3 File/scripts/repair_runner.py authorize --policy File/jobs/repair-allowance.json --approved-hash DISPLAYED_HASH --evidence-ref ACTUAL_USER_AUTHORIZATION
```

The helper records one immutable allowance under File/repair_budget. Repeating identical authorization does not reset costs or attempts. It cannot expand/revoke/replace that allowance in place; stop and resolve exhausted or changed scope explicitly, without deleting history. `authorize` is a coordinator assertion backed by the real user message, not independently authenticated consent.

## Automatic correction submission

For each actual independent failure, the coordinator prepares a repair request containing `id`, `asset_id`, `media` (current selected take path), `model`, `correction`, `failed_checks`, `report`, `completion`, and `uploads`. `preview_id` is added after the exact preview exists.

The review report must include actual `reviewer_id`, `delegation_id`, the stable `asset_id`, exact `media:{path,sha256}`, and `checks` with status pass/fail/uncertain and concrete evidence. All required checks must exist; requested corrections must reference observed fail checks inside the allowance. The saved completion is the real completed T3 result with matching task/child IDs and no pending work. When an older report lacks bindings, obtain a properly bound independent review automatically; do not rewrite or upgrade the original report.

`uploads` points to an ordered JSON list for the current source media followed by the approved references. Each record contains `media:{path,sha256}`, actual HTTPS `url`, and `receipt:{path,sha256}` for supported upload evidence. Preserve that receipt and verify that it really binds the uploaded bytes to the URL. This helper checks local evidence and mappings; it does not upload files or authenticate remote content from a claimed receipt.

```sh
python3 File/scripts/repair_runner.py bind-payload --request File/jobs/fix-01.json --out File/jobs/fix-01.payload.json
python3 File/scripts/kie_tasks.py preview --payload File/jobs/fix-01.payload.json --cap-credits RESERVED_REPAIR_CREDITS
# Record the returned preview_id in fix-01.json; no per-fix user approval within the allowance.
python3 File/scripts/repair_runner.py submit --request File/jobs/fix-01.json --caller-id ACTUAL_COORDINATOR_ID
```

`bind-payload` builds the prompt from the approved preservation instructions and targeted correction, inserts the exact source/reference bindings and preserves all other model settings. `submit` reconstructs that payload and checks equality before using its exact Kie preview hash. An unrelated prompt or mismatched references cannot use the allowance merely because its model is allowed. The coordinator still verifies that the natural-language correction is actually limited to the failed properties; hashes cannot establish semantic truth.

The runner reserves allowance credits durably before calling `kie_tasks.submit`. It retains the existing one-create-POST journal, private project .env credential selection and unknown-outcome block. The approved project limit is supplied as a process-only budget override; no key is read by the repair runner and no .env is changed. Original operations count against the project ceiling. Repair spending counts the greater of each reservation or reported charge, including failures; no automatic refund is inferred. Reservations are estimates, not provider-enforced billing caps.

Repeat the exact request after interruption. It reuses the reservation and preview rather than creating another paid attempt. Unknown results require reconciliation; never generate another preview to bypass them.

## Download, independently review and select

Poll the same operation through `kie_tasks.py status`. Once success is confirmed:

```sh
python3 File/scripts/repair_runner.py download --preview PREVIEW_ID --output Assets/repairs/frame-01-v2.png --caller-id ACTUAL_COORDINATOR_ID
```

Download uses a verified successful receipt, a public HTTPS URL, no API authentication headers, a new versioned output and preserved hash provenance. It handles one returned output. Do not expose signed result URLs in messages.

Dispatch a fresh independent review of the actual result against all selected references and previous findings. Then write a result record with `preview_id`, `media`, `report`, `completion`, `selection` and `reason`:

- `accepted`: every applicable review check passed; continue dependent production through its normal evidence gate.
- `use_corrected`: a confirmed defect remains; a permitted next repair must use this reviewed corrected take.
- `retain_previous`: the reviewed correction was worse; keep the prior selected take, preserve the rejected result and obtain fresh bound defect evidence for that retained take before another repair.

```sh
python3 File/scripts/repair_runner.py record-result --record File/jobs/fix-01-result.json --caller-id ACTUAL_COORDINATOR_ID
python3 File/scripts/repair_runner.py status
```

A second repair cannot start while the previous correction is still generating, lacks a downloaded result, or lacks its independent disposition. New requests must match the selected media lineage and use fresh review evidence. A passed asset cannot consume more repair attempts. Uncertainty calls for better evidence, not speculative paid correction. A failed provider operation without an output remains a concrete recovery case; this helper does not fabricate a reviewable result for it.

This is an executable allowance/submission/download gate driven by the coordinator, not a background daemon. T3 dispatch, actual visual/AV inspection, model-schema qualification and Premiere remain agent/tool responsibilities. Final-export approval is unchanged. Template setup performs no paid request.
