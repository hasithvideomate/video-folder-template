# Optional local Kie setup

Editing supplied media through Premiere needs no Kie key. For new image/video generation, this folder can call Kie directly with Python 3.10+ and no web app/database.

## Private environment
Copy .env.example to .env, enter your own KIE_API_KEY privately in an editor and restrict the file to your user. Do not paste it into Codex chat, pass it as a command argument, print the file or share it. The helper reads KIE_API_KEY only from this project's root .env and never echoes it. It ignores .env.local and process KIE_API_KEY; a missing or empty project key blocks live requests rather than falling back to another account. KIE_PROJECT_CAP_CREDITS can still be overridden for an explicitly authorized process-scoped run.

KIE_PROJECT_CAP_CREDITS defaults to zero, which blocks paid submission. Set a positive project reservation budget only for an authorized run. Local reservations and estimates do not guarantee a provider-side spending ceiling and cannot account for other folders/accounts spending concurrently.

## Supported helper scope
File/scripts/kie_tasks.py supports the documented Market createTask/recordInfo interface. It also uploads reference files (`upload`, below). It is not a model catalog, chat planner, voice/character registration adapter, downloader or a replacement for checking a model's current schema. Models using different endpoints need their own reviewed integration.

Codex drafts prompts locally; a separate paid GPT planning API is unnecessary. Use current official model documentation to build a model-specific request JSON under File/. Do not use placeholder models or fabricate input URLs. Local reference paths become URLs through the upload command:

```sh
python3 File/scripts/kie_tasks.py upload --file Assets/avatar.png
```

It POSTs the file to Kie's file-stream upload (`https://kieai.redpandaai.co/api/file-stream-upload`, project .env key only, no generation credits) and saves a receipt under File/generation/uploads with the file hash, `downloadUrl` and a 24-hour expiry (Kie deletes uploads after 24 hours). A fresh receipt for the same bytes is reused; otherwise the file is uploaded again. Only image/video/audio files inside the project are accepted. `production_runner.py` calls this automatically for job `uploads` fields.

## Preview — no key/network/spend required
From the project root:

```sh
python3 File/scripts/kie_tasks.py preview --payload File/request.json --cap-credits 10
```

The helper saves and prints the exact payload, local preview ID, reservation and SHA-256 approval hash. This prepares one task, not an approved submission. Initial/uncovered work requires actual request/scope authorization. Qualifying corrective payloads may instead use the explicit project repair allowance and repair_runner.py described in PAID_REPAIRS.md; the coordinator records the exact preview without asking again per correction.

## Submit once — paid
Only after that authorization, use the returned ID and full hash:

```sh
python3 File/scripts/kie_tasks.py submit --preview PREVIEW_UUID --approved-hash REVIEWED_HASH
```

The command-line flag records the operator's assertion of approval; it does not independently prove human consent. The Codex skill must obtain it from the user. The helper checks local budget reservations, records the attempt before the single POST and never automatically retries it. Reusing the preview never creates another POST. There is no provider-level exactly-once guarantee.

The helper preserves redacted submission responses in `File/generation/submission_receipts/` and links the receipt from the operation. This includes error JSON returned with HTTP success and bounded HTTP-error bodies; network exceptions retain their type without printing their message or credentials. An error receipt does not automatically establish that a task is absent, authorize retry, or unlock an unknown operation. Responses discarded by older helper versions cannot be recovered by repeating a paid submission.

An unknown/submitting outcome blocks further submissions from this folder. Reconcile it in your Kie account logs and preserve the local history before continuing; do not delete records to retry. A known task ID can be polled safely with the status command. There is no automatic reconciliation or refund inference.

## Check an existing task
```sh
python3 File/scripts/kie_tasks.py status --preview PREVIEW_UUID
```

Each query saves a separate receipt. It reports provider state and reported credits if present; absent billing remains unknown/reserved. A terminal failed task is not automatically resubmitted. Preserve result URLs privately in the receipt and download/verify selected media into Assets/ using an available supported download tool. Downloads must never receive the Kie Authorization header.

## Limits and validation
The helper has offline regression coverage for preview integrity, one-submit behavior, unknown outcomes, budget blocking, receipt retention and key redaction. This template has not performed live model qualification, uploaded source assets or spent credits. Unknown media/billing states remain unknown.

Official contracts: [Getting started](https://docs.kie.ai/getting-started), [Market task status](https://docs.kie.ai/market/common/get-task-detail). Verify model-specific fields and prices before each new model integration.


## Automated batches
Use [BATCH_AUTOMATION.md](BATCH_AUTOMATION.md) for the `production_runner.py` wrapper. It compiles exact previews, records existing batch authorization, submits/polls through this helper, downloads one matching successful result without authentication headers, prepares evidence and tracks independent reviews. Status operations now save `latestReceipt` for result provenance. This does not add upload/voice registration support or authorize any spending.

## Reference sheets (standing authorization)
Reference sheets with Nano Banana Pro at 2K are pre-authorized up to 300 credits per project (File/reference_defaults.json; AGENTS.md, "Standing reference-sheet authorization"). Preview each exact request, then submit it without asking; permission to use supplied faces and images is assumed. Other models, video and larger limits keep the normal authorization flow.
