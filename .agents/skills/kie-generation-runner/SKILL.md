---
name: kie-generation-runner
description: Use the local Kie Market-task helper for private authentication, exact previews, authorized single submissions, known-task status, preserved receipts and uncertain-outcome recovery.
metadata:
  version: "1.1.4-local"
---

# Local Kie Generation Runner

Read File/docs/KIE_SETUP.md and ../production-director/SKILL.md. The implementation is File/scripts/kie_tasks.py, not the old scripts/kie.py or .kie/ runner.

## Credentials and budgets
KIE_API_KEY is loaded privately only from this project's root .env. Ignore .env.local and inherited process KIE_API_KEY; if the project key is missing or empty, stop rather than using another account. Only KIE_PROJECT_CAP_CREDITS may use a process-scoped override for an authorized budget. Never read/print it into model context, pass it as a command argument, put it in prompts/logs or share secret files.

KIE_PROJECT_CAP_CREDITS defaults to zero. A positive authorized reservation budget is required. Local accounting cannot coordinate other folders/accounts or guarantee a provider-side spending ceiling.

## Available commands
Prepare a model-specific request JSON containing model and input from the current official contract. Asset placeholders/local paths are not uploaded URLs.

    python3 File/scripts/kie_tasks.py preview --payload File/request.json --cap-credits 10

Preview saves/prints the exact request, UUID, reservation and approval hash. It needs no key and makes no network call. Show the concrete request and obtain authorization before submission.

    python3 File/scripts/kie_tasks.py submit --preview PREVIEW_UUID --approved-hash REVIEWED_HASH

Each preview permits one attempted createTask POST, recorded first, without automatic retry. Reusing its ID returns local state. A new UUID is a new potential paid attempt, not provider idempotency; do not create one to bypass unknown outcomes.

    python3 File/scripts/kie_tasks.py status --preview PREVIEW_UUID

Status queries the known task and appends a receipt. It does not regenerate or download. Missing charges remain unknown/reserved; failure does not authorize retry.

## History and recovery
File/generation/ contains saved previews, operation state and separate receipt snapshots. Retain every attempt, take, estimate/reservation and reported charge.

Submission diagnostics are retained separately in File/generation/submission_receipts/: successful/error JSON envelopes and bounded HTTP error bodies are redacted before saving; network errors retain only their type. The operation points to its receipt. This preserves evidence for manual recovery, not automatic reconciliation or retry. A response lost before this receipt support was added cannot be recovered retroactively by repeating a POST.

An ambiguous response/missing trustworthy task ID marks unknown and blocks further submissions. Inspect Kie logs and reconcile the real outcome; do not delete/fabricate history. No automated orphan-task linking command is implemented.

## Scope limits
Only Market createTask/recordInfo is implemented. `upload --file PATH` sends a selected project reference to Kie temporary storage (24 h) and returns its URL. There is no credits, sync-all, reconcile or force-new-take CLI, no voice/character adapter, automatic downloader, rate-limit submission retry or chat endpoint. Never pretend legacy commands exist.

Account inspection and Omni registration require separately available reviewed tools/contracts. A download must not receive the Kie Authorization header. Save/verify selected local outputs under Assets/ before Premiere import.

Verify current model IDs, schemas, reference compatibility, supported sizes/durations and prices before execution. Do not hard-code old aliases/pricing or assume registrations are free. A USD equivalent is labeled with its conversion basis, not called an invoice.

Installing the skill authorizes no live call or paid test.

Instruction version: kie-generation-runner@1.1.4-local.


## Batch wrapper
File/scripts/production_runner.py now provides authorized batch advancement and a bounded HTTPS downloader around this helper. Read File/docs/BATCH_AUTOMATION.md. The underlying Kie helper still has only preview/submit/status; status now retains a latestReceipt pointer for verified downloads. The wrapper never bypasses its credential selection, exact-preview hash, budget reservation or single-POST rules.

## One-time automatic paid-repair allowance
Follow File/docs/PAID_REPAIRS.md and File/scripts/repair_runner.py. A user-approved project repair allowance replaces repeated payload approval for qualifying corrections: the runner binds each exact payload to approved assets/references/models/failed checks and reserves credits before submission. Ask for scope/limits once, then automatically correct, independently re-review and continue. Older “exact new payload approval” wording applies only when no allowance covers the repair. Default repair rounds remain bounded; no credits are authorized by template setup, and final-export approval stays separate.
