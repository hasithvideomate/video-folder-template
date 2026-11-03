#!/usr/bin/env python3
"""Resumable talking-avatar batches. Live review/Premiere calls belong to the agent."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid

import agentic_pipeline as ap
import kie_tasks as kie

POLL_SECONDS = 15
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
DOWNLOAD_WORKERS = 4
CHAIN_LIMIT = 8
# Stages fetch keeps waiting on: provider generation and local download/evidence work.
ACTIVE_STAGES = ('generation', 'download', 'evidence')


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value):
        raise ValueError('Use a short alphanumeric ID with hyphens/underscores')
    return value


def rel(path):
    return str(path.relative_to(ap.ROOT))


# A clip's first take uses the batch-approved fields; automatic regenerations add take* fields.
def tag(entry):
    return entry['id'] if entry.get('take', 1) == 1 else f"{entry['id']}.t{entry['take']}"


def take_job(entry):
    return entry.get('takeJob', entry['job'])


def take_preview(entry):
    return entry.get('takePreview', entry['preview'])


def take_hash(entry):
    return entry.get('takeApprovalHash', entry['approvalHash'])


def directory(batch):
    return ap.local('File/automation/' + safe_id(batch))


@contextmanager
def lock(batch):
    folder = directory(batch)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / '.lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield folder
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    kie.replace(path, data)


def read(path):
    return ap.load(rel(path))


def inputs(job_path):
    job = ap.load(job_path)
    names = [job_path, job['script'], *job['references']]
    if job.get('voice_reference'):
        names.append(job['voice_reference'])
    return [ap.fingerprint(name) for name in names]


def unchanged(items):
    for item in items:
        if ap.fingerprint(item['path']) != item:
            raise ValueError('Source/job/reference changed; prepare a new batch version')


# ---- Automatic reference uploads -------------------------------------------------
# A job may map payload fields to selected local references, e.g.
#   "uploads": {"input.image_url": "Assets/avatar.png", "input.reference_audio": ["Assets/voice.wav"]}
# The runner uploads them through kie_tasks.upload and writes the URLs into a resolved job copy.
UPLOAD_SUBMIT_MARGIN_HOURS = 1
UPLOAD_REFRESH_HOURS = 3


def upload_plan(job):
    plan = job.get('uploads') or {}
    if not isinstance(plan, dict):
        raise ValueError('uploads must map payload fields to selected reference paths')
    allowed = set(job['references']) | ({job['voice_reference']} if job.get('voice_reference') else set())
    for name, files in plan.items():
        names = files if isinstance(files, list) else [files]
        if (not isinstance(name, str) or not name.startswith('input.')
                or name in (job['prompt_field'], job['resolution_field'])):
            raise ValueError('Upload fields must be distinct input fields')
        if not names or any(n not in allowed for n in names):
            raise ValueError('Only selected references/voice reference may be uploaded')
        ap.field(job['payload'], name)  # field path must exist in the verified model payload
    return plan


def set_urls(job, plan, name, urls):
    obj, key = ap.field(job['payload'], name)
    obj[key] = urls if isinstance(plan[name], list) else urls[0]


def resolve_uploads(job, min_hours=None):
    plan = upload_plan(job)
    resolved = json.loads(json.dumps(job)); receipts = []
    for name in sorted(plan):
        names = plan[name] if isinstance(plan[name], list) else [plan[name]]
        records = [kie.upload(n) if min_hours is None else kie.upload(n, min_hours) for n in names]
        urls = [r['downloadUrl'] for r in records]
        set_urls(resolved, plan, name, urls)
        receipts.append({'field': name, 'files': [r['file'] for r in records], 'urls': urls,
                         'expiresAt': min((r['expiresAt'] for r in records), key=datetime.fromisoformat)})
    return resolved, receipts


def apply_receipts(job, receipts):
    """Deterministically rebuild a resolved job; only upload fields may differ from the source job."""
    plan = upload_plan(job)
    if sorted(plan) != sorted(r['field'] for r in receipts):
        raise ValueError('Upload receipts do not match the job upload plan')
    resolved = json.loads(json.dumps(job))
    for receipt in receipts:
        names = plan[receipt['field']] if isinstance(plan[receipt['field']], list) else [plan[receipt['field']]]
        if [f['path'] for f in receipt['files']] != names or len(receipt['urls']) != len(names):
            raise ValueError('Upload receipts do not match the selected files')
        unchanged(receipt['files'])
        set_urls(resolved, plan, receipt['field'], receipt['urls'])
    return resolved


def expiring(receipts, hours):
    limit = datetime.now(timezone.utc).timestamp() + hours * 3600
    return any(datetime.fromisoformat(r['expiresAt']).timestamp() < limit for r in receipts or [])


# ---- One project grant (approve once, batches authorize themselves) ----------------
def grant_paths():
    folder = ap.local('File/automation')
    return folder / 'grant-request.json', folder / 'grant.json'


def grant_prepare(spec_path):
    spec = ap.load(spec_path)
    defaults = ap.load('File/repair_defaults.json') if ap.local('File/repair_defaults.json').is_file() else {}
    models = spec['models']
    if not isinstance(models, list) or not models or any(not isinstance(m, str) or not m.strip() for m in models):
        raise ValueError('List the exact verified model IDs')
    if not spec.get('references'):
        raise ValueError('A grant needs the selected visual reference(s)')
    per, total = (kie.amount(spec[k], positive=True) for k in ('per_clip_cap_credits', 'original_cap_credits'))
    if per > total:
        raise ValueError('Per-clip cap cannot exceed the original-generation cap')
    attempts = spec.get('max_attempts_per_clip', defaults.get('maxAttemptsPerAsset', 0))
    repair = kie.amount(spec.get('repair_cap_credits', defaults.get('repairCapCredits', '0')))
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 0 <= attempts <= 5:
        raise ValueError('max_attempts_per_clip must be 0 to 5')
    request = {'version': 1, 'id': safe_id(spec['id']), 'spec': ap.fingerprint(spec_path),
               'script': ap.fingerprint(spec['script']),
               'references': [ap.fingerprint(r) for r in spec['references']],
               'voiceReferences': [ap.fingerprint(v) for v in spec.get('voice_references', [])],
               'allowAdmittedTakesAsVoice': spec.get('allow_admitted_takes_as_voice', True) is True,
               'models': models, 'perClipCapCredits': str(per), 'originalCapCredits': str(total),
               'autoRegeneration': {'maxAttemptsPerClip': attempts, 'repairCapCredits': str(repair)},
               'projectCeilingCredits': str(total + repair), 'resolution': '720p', 'rules': ap.RULES,
               'scope': ('Any talking-avatar batch whose clips use only this script, these references (or an '
                         'independently admitted take as voice reference), these models and at most '
                         'perClipCapCredits each, within originalCapCredits in total across the project, plus '
                         'automatic corrective takes within autoRegeneration. Uploading the selected references '
                         'to Kie temporary storage is included. Final export is not included.')}
    path, _ = grant_paths()
    save(path, request)
    return {'grantRequest': rel(path), 'approvalHash': ap.digest(request), 'request': request}


def grant_authorize(approved_hash, evidence_ref):
    """Record the user's actual one-time project approval; never manufacture consent."""
    request_path, grant_path = grant_paths()
    request = read(request_path)
    if ap.digest(request) != approved_hash or not evidence_ref.strip():
        raise ValueError('Exact grant hash and actual user-authorization reference required')
    unchanged([request['script'], *request['references'], *request['voiceReferences']])
    grant = {'request': request, 'approvalHash': approved_hash, 'evidenceRef': evidence_ref}
    if grant_path.exists():
        current = read(grant_path)
        if current == grant:
            return {'grantAuthorized': True, 'id': request['id']}
        # Keep history: an expanded/changed grant is a new explicit user approval.
        save(grant_path.with_name(f"grant-superseded-{uuid.uuid4().hex[:8]}.json"), current)
    save(grant_path, grant)
    return {'grantAuthorized': True, 'id': request['id']}


def load_grant():
    path = grant_paths()[1]
    if not path.exists():
        return None
    grant = read(path)
    if ap.digest(grant['request']) != grant['approvalHash'] or not grant.get('evidenceRef', '').strip():
        raise ValueError('Project grant record changed')
    return grant


def all_states(current=None):
    for path in sorted(ap.local('File/automation').glob('*/state.json')):
        yield current if current and path == directory(current['batch']) / 'state.json' else read(path)


def granted(state):
    path = directory(state['batch']) / 'authorization.json'
    return path.exists() and read(path).get('evidenceRef', '').startswith('project-grant:')


def grant_original_spend(current):
    used = Decimal(0)
    for state in all_states(current):
        if state['batch'] != current['batch'] and granted(state):
            used += sum((regen_charge(e) for e in state['clips']), Decimal(0))
    return used


def admitted_media(current):
    return [e['media'] for state in all_states(current) for e in state['clips']
            if e['stage'] == 'ready_for_edit' and e.get('media')]


def grant_check(state):
    grant = load_grant()
    if not grant:
        return 'no_project_grant'
    g = grant['request']
    unchanged([g['script'], *g['references'], *g['voiceReferences']])
    approval = read(directory(state['batch']) / 'approval-request.json')
    voices = g['references'] + g['voiceReferences'] + (admitted_media(state) if g['allowAdmittedTakesAsVoice'] else [])
    for entry in state['clips']:
        job = ap.load(entry.get('sourceJob', entry['job']))
        if ap.fingerprint(job['script']) != g['script']:
            return 'script_not_in_grant'
        if any(ap.fingerprint(r) not in g['references'] for r in job['references']):
            return 'reference_not_in_grant'
        if job.get('voice_reference') and ap.fingerprint(job['voice_reference']) not in voices:
            return 'voice_not_in_grant'
        if entry['payload']['model'] not in g['models']:
            return 'model_not_in_grant'
        if kie.amount(entry['capCredits']) > kie.amount(g['perClipCapCredits']):
            return 'clip_cap_above_grant'
    regen = approval.get('autoRegeneration')
    if regen and (regen['maxAttemptsPerClip'] > g['autoRegeneration']['maxAttemptsPerClip']
                  or kie.amount(regen['repairCapCredits']) > kie.amount(g['autoRegeneration']['repairCapCredits'])):
        return 'regeneration_above_grant'
    batch_total = sum((kie.amount(e['capCredits']) for e in state['clips']), Decimal(0))
    if grant_original_spend(state) + batch_total > kie.amount(g['originalCapCredits']):
        return 'grant_credits_exhausted'
    return None


def auto_authorize(state):
    path = directory(state['batch']) / 'authorization.json'
    if path.exists():
        return 'already_authorized'
    reason = grant_check(state)
    if reason:
        return reason
    grant = load_grant()
    save(path, {'approvalHash': state['approvalHash'],
                'evidenceRef': f"project-grant:{grant['request']['id']}:{grant['approvalHash']}",
                'userEvidenceRef': grant['evidenceRef']})
    return 'authorized_by_project_grant'


def kie_ceiling(state, corrective):
    """Process-only Kie reservation ceiling for this submission, or None to use the project .env."""
    if granted(state):
        grant = load_grant()
        if grant:
            return grant['request']['projectCeilingCredits']
    if corrective:
        scope = read(directory(state['batch']) / 'approval-request.json')['autoRegeneration']
        return str(kie.amount(kie.config().get('KIE_PROJECT_CAP_CREDITS', '0')) + kie.amount(scope['repairCapCredits']))
    return None


def submit_take(state, entry, corrective):
    receipts = entry.get('takeUploads', entry.get('uploads'))
    if expiring(receipts, UPLOAD_SUBMIT_MARGIN_HOURS):
        if corrective:
            raise ValueError('Reference uploads expire before submission; regenerate the take record')
        raise ValueError('Reference uploads expired before submission; prepare a new batch version')
    ceiling = kie_ceiling(state, corrective)
    previous = os.environ.get('KIE_PROJECT_CAP_CREDITS')
    if ceiling is not None:
        os.environ['KIE_PROJECT_CAP_CREDITS'] = ceiling  # key selection untouched
    try:
        kie.submit(take_preview(entry), take_hash(entry))
    finally:
        if previous is None: os.environ.pop('KIE_PROJECT_CAP_CREDITS', None)
        else: os.environ['KIE_PROJECT_CAP_CREDITS'] = previous


def prepare(manifest_path):
    manifest = ap.load(manifest_path)
    batch = safe_id(manifest['id'])
    clips = manifest['clips']
    if not isinstance(clips, list) or not clips or len(clips) > 100:
        raise ValueError('A batch needs 1 to 100 ordered clips')
    regen = regeneration_scope(manifest)
    seen = set()
    entries = []
    # Validate the whole batch before creating any preview. All preparation is offline.
    for clip in clips:
        identifier = safe_id(clip['id'])
        if identifier in seen or not set(clip.get('depends_on', [])).issubset(seen):
            raise ValueError('IDs must be unique; dependencies must name earlier clips')
        job = ap.load(clip['job'])
        payload = ap.compile_job(job)
        entry = {'id': identifier, 'job': rel(ap.local(clip['job'])),
                 'inputs': inputs(clip['job']), 'depends_on': clip.get('depends_on', []),
                 'capCredits': str(kie.amount(clip['cap_credits'], positive=True)),
                 'payload': payload, 'dialogue': job['dialogue'], 'references': job['references'],
                 'stage': 'prepared', 'errors': 0}
        entries.append(entry)
        seen.add(identifier)
    with lock(batch) as folder:
        state_path = folder / 'state.json'
        if state_path.exists():
            state = read(state_path)
            if state['manifest'] != ap.fingerprint(manifest_path):
                raise ValueError('Batch ID is already used by another manifest version')
            validate(state)
            state['grantStatus'] = auto_authorize(state)
            return summary(state)
        # No paid side effects occur before the durable state and exact approval request exist.
        for entry in entries:
            source = ap.load(entry['job'])
            if source.get('uploads'):
                # Free temporary-storage uploads of the selected references; no generation request.
                resolved, receipts = resolve_uploads(source)
                resolved_path = folder / (entry['id'] + '.job.json')
                save(resolved_path, resolved)
                entry.update(sourceJob=entry['job'], job=rel(resolved_path), uploads=receipts,
                             payload=ap.compile_job(resolved),
                             inputs=entry['inputs'] + [ap.fingerprint(rel(resolved_path))])
            payload_path = folder / (entry['id'] + '.payload.json')
            if payload_path.exists() and read(payload_path) != entry['payload']:
                raise ValueError('Existing payload differs; use a new batch ID')
            if not payload_path.exists():
                save(payload_path, entry['payload'])
            preview = kie.preview(rel(payload_path), entry['capCredits'])
            entry.update(preview=preview['id'], approvalHash=preview['approvalHash'])
        approval = {'batch': batch, 'clips': [{k: e[k] for k in
                    ('id', 'job', 'inputs', 'depends_on', 'preview', 'approvalHash',
                     'capCredits', 'payload', 'dialogue', 'references', 'sourceJob', 'uploads') if k in e}
                    for e in entries],
                    'totalReservation': str(sum((Decimal(e['capCredits']) for e in entries), Decimal(0))),
                    'scope': ('One generated video per preview; automatic corrective regenerations only as '
                              'described in autoRegeneration; no final export.')}
        if regen:
            approval['autoRegeneration'] = regen
        state = {'version': 1, 'batch': batch, 'manifest': ap.fingerprint(manifest_path),
                 'approvalHash': ap.digest(approval), 'clips': entries}
        save(folder / 'approval-request.json', approval)
        save(state_path, state)
        state['grantStatus'] = auto_authorize(state)
        return summary(state)


def regeneration_scope(manifest):
    """Optional corrective-regeneration scope approved together with the batch."""
    # On by default from the standing File/repair_defaults.json; `false` disables it for a batch.
    config = manifest.get('auto_regeneration', True)
    if config is False:
        return None
    defaults = ap.load('File/repair_defaults.json') if ap.local('File/repair_defaults.json').is_file() else {}
    if config is True:
        if not defaults:
            return None
        config = {}
    attempts = config.get('max_attempts_per_clip', defaults.get('maxAttemptsPerAsset'))
    cap = config.get('repair_cap_credits', defaults.get('repairCapCredits'))
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 5 or cap is None:
        raise ValueError('auto_regeneration needs 1-5 attempts per clip and a repair credit cap')
    return {'maxAttemptsPerClip': attempts,
            'repairCapCredits': str(kie.amount(cap, positive=True)),
            'perAttemptCapCredits': 'Same as that clip\'s approved capCredits',
            'trigger': 'Independent review status rejected with a reviewer correction; never needs_evidence/uncertainty.',
            'frozen': ('Approved script span, dialogue, gestures, references, voice reference/mode, model, '
                       'resolution and every other payload field.'),
            'variable': 'Only a correction note appended to visual_direction, derived from the failed checks and reviewer correction.',
            'ceiling': ('Project-wide corrective spend across batches and repair_runner stays within repairCapCredits; '
                        'the Kie project budget is raised by exactly that amount for corrective submissions only.')}


MAX_CORRECTION_CHARS = 1500


def correction_text(report, failed):
    correction = report.get('correction')
    if isinstance(correction, (dict, list)):
        correction = json.dumps(correction, ensure_ascii=False)
    if not isinstance(correction, str) or not correction.strip():
        return None
    return ('Correction for this regeneration, from the independent review of the previous take. '
            'Fix only these failed checks (' + ', '.join(failed) + '); keep the same person, voice, room, '
            'framing, wording, gestures and everything else identical: ' + correction.strip())


def corrected_job(entry, note):
    job = ap.load(entry.get('takeBase', entry['job']))
    job['visual_direction'] = job['visual_direction'] + '\n\n' + note
    return job


def regen_charge(attempt):
    _, operation = kie.paths(attempt['preview'])
    reported = kie.load(operation).get('reportedCredits') if operation.exists() else None
    # No refunds inferred: failed/unknown work and unused reservations remain counted.
    return max(kie.amount(attempt['capCredits']), kie.amount(reported or '0'))


def project_repair_spend(current_state):
    used = Decimal(0)
    for path in ap.local('File/automation').glob('*/state.json'):
        state = current_state if path == directory(current_state['batch']) / 'state.json' else read(path)
        for entry in state['clips']:
            used += sum((regen_charge(a) for a in entry.get('regenAttempts', [])), Decimal(0))
    if ap.local('File/repair_budget/state.json').is_file():
        import repair_runner
        used += sum((repair_runner.charge(a) for a in repair_runner.load_state()['attempts']), Decimal(0))
    return used


def validate_take(entry):
    if entry.get('take', 1) == 1:
        return
    unchanged([entry['takeJobFingerprint']])
    if entry.get('takeBase') and ap.load(entry['takeBase']) != apply_receipts(ap.load(entry['sourceJob']), entry['takeUploads']):
        raise ValueError('Refreshed upload job differs from its source job and receipts')
    job = corrected_job(entry, entry['takeCorrection'])
    if ap.load(entry['takeJob']) != job or ap.compile_job(job) != entry['takePayload']:
        raise ValueError('Regenerated take is not the approved job plus its correction note')
    preview = kie.load(kie.paths(entry['takePreview'])[0])
    if (kie.hash_preview(preview) != entry['takeApprovalHash'] or preview['approvalHash'] != entry['takeApprovalHash']
            or preview['payload'] != entry['takePayload'] or preview['capCredits'] != entry['capCredits']):
        raise ValueError('Regeneration preview changed')


def regenerate(state, entry):
    """Prepare the next corrective take inside the approved scope; returns a block reason or None."""
    scope = read(directory(state['batch']) / 'approval-request.json').get('autoRegeneration')
    if not scope or not permitted(state):
        return 'not_authorized'
    if len(entry.get('regenAttempts', [])) >= scope['maxAttemptsPerClip']:
        return 'attempt_limit_reached'
    report = ap.load(entry['boundReport'])
    failed = sorted(k for k, v in report['checks'].items() if v['status'] == 'fail')
    note = correction_text(report, failed)
    if not failed or not note:
        return 'no_reviewer_correction'
    if len(note) > MAX_CORRECTION_CHARS:
        return 'correction_too_long'
    if project_repair_spend(state) + kie.amount(entry['capCredits']) > kie.amount(scope['repairCapCredits']):
        return 'repair_credits_exhausted'
    folder = directory(state['batch'])
    take = entry.get('take', 1) + 1
    name = f"{entry['id']}.t{take}"
    if entry.get('uploads') and expiring(entry.get('takeUploads', entry['uploads']), UPLOAD_REFRESH_HOURS):
        # Kie deletes uploads after 24 h: re-upload the same selected files; nothing else changes.
        base, receipts = resolve_uploads(ap.load(entry['sourceJob']), UPLOAD_REFRESH_HOURS + 3)
        base_path = folder / (name + '.base.json'); save(base_path, base)
        entry.update(takeBase=rel(base_path), takeUploads=receipts)
    job = corrected_job(entry, note)
    payload = ap.compile_job(job)
    job_path, payload_path = folder / (name + '.job.json'), folder / (name + '.payload.json')
    for path, value in ((job_path, job), (payload_path, payload)):
        if path.exists() and read(path) != value:
            raise ValueError('Existing regeneration record differs; inspect before continuing')
        if not path.exists():
            save(path, value)
    preview = kie.preview(rel(payload_path), entry['capCredits'])
    entry.setdefault('takeHistory', []).append({k: entry.get(k) for k in (
        'take', 'media', 'packet', 'report', 'boundReport', 'reviewTaskId', 'reviewerId', 'stage', 'taskId')})
    for key in ('media', 'packet', 'report', 'boundReport', 'boundFingerprint', 'reportFingerprint',
                'reviewTaskId', 'reviewerId', 'reviewCompleted', 'reviewRound', 'reviewRequest',
                'reviewHistory', 'additionalEvidence', 'taskId', 'nextPollAt', 'regenBlocked'):
        entry.pop(key, None)
    entry.setdefault('regenAttempts', []).append({'take': take, 'preview': preview['id'], 'capCredits': entry['capCredits']})
    entry.update(take=take, takeJob=rel(job_path), takeJobFingerprint=ap.fingerprint(rel(job_path)),
                 takePayload=payload, takePreview=preview['id'], takeApprovalHash=preview['approvalHash'],
                 takeCorrection=note, stage='prepared')
    return None


def validate(state):
    unchanged([state['manifest']])
    approval = read(directory(state['batch']) / 'approval-request.json')
    if ap.digest(approval) != state['approvalHash']:
        raise ValueError('Batch approval request changed')
    if len(state['clips']) != len(approval['clips']):
        raise ValueError('Batch scope changed')
    for entry, approved in zip(state['clips'], approval['clips']):
        if any(entry.get(k) != v for k, v in approved.items()):
            raise ValueError('Batch scope changed')
        unchanged(entry['inputs'])
        if entry.get('uploads') and ap.load(entry['job']) != apply_receipts(ap.load(entry['sourceJob']), entry['uploads']):
            raise ValueError('Resolved job differs from its source job and upload receipts')
        validate_take(entry)
        if entry.get('packet'):
            check_packet(entry)
        preview = kie.load(kie.paths(entry['preview'])[0])
        if kie.hash_preview(preview) != entry['approvalHash'] or preview['approvalHash'] != entry['approvalHash']:
            raise ValueError('Provider preview changed')
        if preview['payload'] != entry['payload'] or preview['capCredits'] != entry['capCredits']:
            raise ValueError('Provider preview no longer matches batch')


def authorize(batch, approval_hash, evidence_ref):
    """Record an operator assertion of EXISTING user consent, never manufacture consent."""
    with lock(batch) as folder:
        state = read(folder / 'state.json'); validate(state)
        if approval_hash != state['approvalHash'] or not evidence_ref.strip():
            raise ValueError('Exact batch hash and actual user-authorization reference required')
        path = folder / 'authorization.json'
        value = {'approvalHash': approval_hash, 'evidenceRef': evidence_ref}
        if path.exists() and read(path) != value:
            raise ValueError('Existing authorization differs')
        if not path.exists():
            save(path, value)
        return {'batch': batch, 'authorizationRecorded': True}


def permitted(state):
    path = directory(state['batch']) / 'authorization.json'
    if not path.exists():
        return False
    auth = read(path)
    return auth.get('approvalHash') == state['approvalHash'] and bool(auth.get('evidenceRef', '').strip())


def result_url(entry):
    operation = kie.load(kie.paths(take_preview(entry))[1])
    if operation['status'] != 'succeeded' or not operation.get('latestReceipt'):
        raise ValueError('A successful current receipt is required')
    saved = ap.load(operation['latestReceipt'])
    receipt = saved['receipt']
    if saved['operationId'] != take_preview(entry) or receipt['taskId'] != operation['taskId'] or receipt['state'] != 'success':
        raise ValueError('Receipt does not match the completed task')
    result = receipt['resultJson']
    result = json.loads(result) if isinstance(result, str) else result
    urls = result['resultUrls']
    if not isinstance(urls, list) or len(urls) != 1 or not isinstance(urls[0], str):
        raise ValueError('Expected exactly one result URL; inspect multiple outputs explicitly')
    return urls[0]


def download(url, destination, accept='video/*, application/octet-stream'):
    """Unauthenticated, bounded HTTPS fetch; never logs result URLs or response bodies."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Download requires a public HTTPS URL without credentials')
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Non-public download address refused')
    if destination.exists():
        raise ValueError('Refusing to overwrite existing media')
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=destination.parent, prefix='.download-')
    started = time.monotonic()
    try:
        # Separate opener: no Kie headers, no cookies, no environment proxy or redirects.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), kie.NoRedirect)
        request = urllib.request.Request(url, headers={'Accept': accept})
        with os.fdopen(fd, 'wb') as out, opener.open(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError('Download did not return a complete file')
            size = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                if size > MAX_DOWNLOAD_BYTES or time.monotonic() - started > 180:
                    raise ValueError('Download exceeds local size/time bound')
                out.write(block)
            if not size or (response.headers.get('Content-Length') and size != int(response.headers['Content-Length'])):
                raise ValueError('Incomplete media download')
            out.flush(); os.fsync(out.fileno())
        # Existing media is never replaced, including when another writer races us.
        os.link(tmp, destination)
        save(Path(str(destination) + '.download.json'),
             {'urlHash': ap.digest(url), 'media': ap.fingerprint(rel(destination))})
    finally:
        Path(tmp).unlink(missing_ok=True)


def prepare_evidence(media, folder):
    """Artifacts aid review; sampled frames/ASR are never a motion or speech pass."""
    stamp = ap.fingerprint(rel(media))
    index = folder / 'index.json'
    if index.exists():
        record = read(index)
        if record['media'] != stamp:
            raise ValueError('Evidence belongs to different media')
        unchanged(record['artifacts'])
        return
    info = ap.verify_media(rel(media))
    duration = float(info['format']['duration'])
    if not math.isfinite(duration) or not 0 < duration <= 120:
        raise ValueError('Automatic evidence supports clips up to 120 seconds')
    staging = Path(tempfile.mkdtemp(prefix='.evidence-', dir=folder.parent))
    try:
        # One decode pass feeds every output: full-stream decode check, 12 review frames,
        # a 4x3 contact sheet for immediate local preview, and full mono audio.
        fps = f'fps={12/duration}'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(media),
                        '-map', '0:v:0', '-f', 'null', '-',
                        '-map', '0:v:0', '-vf', fps, '-frames:v', '12', str(staging / 'frame-%03d.jpg'),
                        '-map', '0:v:0', '-vf', fps + ',scale=320:-2,tile=4x3', '-frames:v', '1',
                        str(staging / 'contact.jpg'),
                        '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', str(staging / 'audio.wav')],
                       check=True, capture_output=True, timeout=120)
        save(staging / 'probe.json', info)
        if folder.exists():
            folder.rename(folder.with_name(folder.name + '.incomplete-' + uuid.uuid4().hex[:8]))
        staging.rename(folder)
        artifacts = [ap.fingerprint(rel(p)) for p in sorted(folder.iterdir()) if p.is_file()]
        save(index, {'media': stamp, 'artifacts': artifacts, 'coverage': 'sampled_frames_and_full_audio',
                     'frameSampling': f'fps={12/duration}, at most 12 frames; approximate time spacing {duration/12}s',
                     'note': 'Successful decode is technical evidence only. No visual/audio quality pass is inferred.'})
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def review_request(state, entry, packet_path, report_path, evidence_path):
    packet = read(packet_path)
    request_id = f"review-{state['batch']}-{tag(entry)}-r{entry.get('reviewRound', 1)}-{packet['packet_hash'][:16]}"
    prior_context = '\nPrior review history (address every unresolved finding): ' + json.dumps(entry.get('reviewHistory', []))
    extra_evidence = '\nAdditional evidence: ' + json.dumps(entry.get('additionalEvidence', []))
    return {'clientRequestId': request_id, 'role': 'review', 'mode': 'async',
            'title': 'Review ' + entry['id'],
            'task': (f"Independently review this talking-avatar take. Project: {ap.ROOT}. "
                     'Read File/docs/AGENTIC_WORKFLOW.md, its independent-review contract, and '
                     f"packet {rel(packet_path)}. Supporting evidence: {rel(evidence_path)}/index.json. "
                     f"Write the report to {rel(report_path)}. Use your actual child thread/agent identity "
                     'for reviewer_id and your actual task ID for delegation_id. If the task ID is not '
                     'available in your context, leave delegation_id null; the parent will bind transport '
                     'metadata in a separate copy without altering your findings. Read the actual full '
                     'video and listen to speech; sampled frames do not prove motion, captions absence, '
                     'gesture timing or lip sync. Mark genuinely unavailable checks uncertain. '
                     'Do not spend, generate, change sources, operate Premiere, or approve export. '
                     'Return timestamps, evidence limits and a minimal correction proposal for defects. '
                     'Put that proposal in the report `correction` field as concrete prompt direction: an approved '
                     'batch regenerates rejected takes automatically from it.'
                     + prior_context + extra_evidence)}


def check_packet(entry):
    unchanged([entry['media']])
    packet = ap.load(entry['packet'])
    ap.validate_packet(packet)
    expected = ap.packet(take_job(entry), entry['media']['path'])
    if packet != expected:
        raise ValueError('Review packet is not bound to this exact job and media')
    unchanged(entry.get('additionalEvidence', []))
    return packet


def media_path(state, entry):
    return ap.local(f"Assets/generated/{state['batch']}/{tag(entry)}.mp4")


def step(state, entry, fetch_media=True):
    folder = directory(state['batch'])
    stage = entry['stage']
    if any(next(e for e in state['clips'] if e['id'] == dep)['stage'] != 'ready_for_edit'
           for dep in entry['depends_on']):
        return False
    if stage in ('prepared', 'generation'):
        operation_path = kie.paths(take_preview(entry))[1]
        if not operation_path.exists():
            if not permitted(state):
                return False
            health = ap.tool_health()
            if not all(health[name]['usable'] for name in ('ffmpeg', 'ffprobe')):
                raise ValueError('FFmpeg/ffprobe must start successfully before paid submission')
            # Save intent first; the Kie helper independently journals before its single POST.
            entry['stage'] = 'generation'; save(folder / 'state.json', state)
            corrective = entry.get('take', 1) > 1
            if corrective:
                scope = read(folder / 'approval-request.json')['autoRegeneration']
                if project_repair_spend(state) > kie.amount(scope['repairCapCredits']):
                    raise ValueError('Repair credits exhausted before corrective submission')
            submit_take(state, entry, corrective)
            return True
        operation = kie.load(operation_path)
        status = operation['status']
        entry['taskId'] = operation.get('taskId')
        if status in ('unknown', 'submitting'):
            entry['stage'] = 'unknown_submission'; return True
        if status == 'failed':
            entry['stage'] = 'generation_failed'; return True
        if status == 'succeeded':
            if not operation.get('latestReceipt'):
                kie.status(take_preview(entry))
            entry['stage'] = 'download'; return True
        if status != 'submitted':
            raise ValueError('Unsupported provider operation state')
        if time.time() < entry.get('nextPollAt', 0):
            return False
        entry['nextPollAt'] = time.time() + POLL_SECONDS
        save(folder / 'state.json', state)
        kie.status(take_preview(entry))
        entry['stage'] = 'generation'
        return True
    if stage == 'download':
        media = media_path(state, entry)
        url = result_url(entry)
        if not media.exists():
            if not fetch_media:
                return False
            download(url, media)
        receipt = read(Path(str(media) + '.download.json'))
        if receipt['urlHash'] != ap.digest(url) or receipt['media'] != ap.fingerprint(rel(media)):
            raise ValueError('Existing media does not match its download receipt')
        # A crash after durable download provenance but before state save can resume.
        ap.verify_media(rel(media))
        entry['media'] = ap.fingerprint(rel(media))
        entry['stage'] = 'evidence'; return True
    if stage == 'evidence':
        unchanged([entry['media']])
        evidence = folder / (tag(entry) + '.evidence')
        prepare_evidence(ap.local(entry['media']['path']), evidence)
        packet_path = folder / (tag(entry) + '.packet.json')
        if packet_path.exists():
            entry['packet'] = rel(packet_path)
            check_packet(entry)
        else:
            save(packet_path, ap.packet(take_job(entry), entry['media']['path']))
        entry['reviewRound'] = 1
        report_path = folder / (tag(entry) + '.review-r1.json')
        request = review_request(state, entry, packet_path, report_path, evidence)
        save(folder / (tag(entry) + '.review-request-r1.json'), request)
        entry.update(stage='review_requested', packet=rel(packet_path), report=rel(report_path),
                     reviewRequest=rel(folder / (tag(entry) + '.review-request-r1.json')))
        return True
    if stage == 'review_running' and entry.get('reviewCompleted'):
        packet = check_packet(entry); report = ap.load(entry['report'])
        if report.get('reviewer_id') != entry['reviewerId']:
            raise ValueError('Report reviewer does not match the delegated child')
        if report.get('delegation_id') not in (None, entry['reviewTaskId']):
            raise ValueError('Report task ID does not match the delegated child')
        # Preserve the untouched child report; bind transport-only metadata separately.
        report['delegation_id'] = entry['reviewTaskId']
        gate = ap.gate(packet, report)
        bound = folder / (tag(entry) + f".bound-review-r{entry['reviewRound']}.json"); save(bound, report)
        entry.update(stage=gate['status'], boundReport=rel(bound),
                     boundFingerprint=ap.fingerprint(rel(bound)), reportFingerprint=ap.fingerprint(entry['report']))
        if gate['status'] != 'ready_for_edit':
            save(folder / (tag(entry) + f".correction-r{entry['reviewRound']}.json"), {
                'packet_hash': packet['packet_hash'], 'status': gate['status'],
                'checks': {k: v for k, v in report['checks'].items() if v['status'] != 'pass'},
                'proposedCorrection': report.get('correction'),
                'autoRegeneration': 'Handled by the approved batch scope when present; see clip regenBlocked otherwise.'})
        return True
    if stage == 'rejected' and not entry.get('regenBlocked'):
        reason = regenerate(state, entry)
        if reason:
            entry['regenBlocked'] = reason
        return True
    return False


def refresh_ready(state):
    for entry in state['clips']:
        if entry['stage'] == 'ready_for_edit':
            unchanged([entry['reportFingerprint'], entry['boundFingerprint']])
            if ap.gate(check_packet(entry), ap.load(entry['boundReport']))['status'] != 'ready_for_edit':
                raise ValueError('Previously accepted review no longer passes')



def pacing_handoff():
    path = 'File/pacing_policy.json'
    policy = ap.load(path)
    values = policy['pause_planner']
    threshold, target, sentence = (values[k] for k in
                                  ('max_pause_seconds', 'target_pause_seconds', 'sentence_pause_seconds'))
    if (policy.get('version') != 1 or policy.get('required') is not True
            or any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
                   for v in (threshold, target, sentence))
            or not 0 < target <= sentence <= threshold):
        raise ValueError('Invalid mandatory pacing policy')
    if (policy.get('add_captions') is not False or policy.get('allow_zoom_or_reframing') is not False
            or policy.get('change_playback_speed') is not False):
        raise ValueError('Pacing must preserve text-free, fixed-framing, normal-speed delivery')
    return {'required': True, 'status': 'pending', 'policy': ap.fingerprint(path),
            'settings': policy, 'workflow': 'File/docs/AUTO_CUT.md',
            'reviewScope': 'Every clip edge and join, then full assembled sequence; source review is insufficient.'}


def eligible(entry):
    return entry.get('errors', 0) < 3 and time.time() >= entry.get('retryAt', 0)


def record_error(entry, error):
    entry['errors'] = entry.get('errors', 0) + 1
    entry['errorType'] = type(error).__name__  # Never log signed URLs/response bodies.
    entry['retryAt'] = time.time() + 60 * 2 ** (entry['errors'] - 1)


def run_chain(state, entry, folder, budget, fetch_media):
    """Advance one clip through consecutive stages until it must wait."""
    actions = 0
    for _ in range(CHAIN_LIMIT):
        if actions >= budget or not eligible(entry):
            break
        try:
            moved = step(state, entry, fetch_media)
        except Exception as error:
            record_error(entry, error)
            save(folder / 'state.json', state)
            return actions + 1
        save(folder / 'state.json', state)
        if not moved:
            break
        actions += 1; entry['errors'] = 0
        entry.pop('errorType', None); entry.pop('retryAt', None)
    return actions


def parallel_downloads(state, folder):
    """Fetch every finished, not-yet-local result concurrently (unauthenticated HTTPS only)."""
    jobs = []
    for entry in state['clips']:
        if entry['stage'] != 'download' or not eligible(entry) or media_path(state, entry).exists():
            continue
        try:
            jobs.append((entry, result_url(entry), media_path(state, entry)))
        except Exception as error:
            record_error(entry, error)
    if jobs:
        with ThreadPoolExecutor(max_workers=min(DOWNLOAD_WORKERS, len(jobs))) as pool:
            futures = [(entry, pool.submit(download, url, media)) for entry, url, media in jobs]
            for entry, future in futures:
                try:
                    future.result()
                except Exception as error:
                    record_error(entry, error)
    save(folder / 'state.json', state)


def advance(batch, max_actions=40):
    if not 1 <= max_actions <= 100:
        raise ValueError('max-actions must be 1 to 100')
    with lock(batch) as folder:
        state = read(folder / 'state.json')
        # Invalidate any old edit handoff before checks; failures cannot leave a usable stale queue.
        handoff = folder / 'edit-ready.json'
        save(handoff, {'ready': False, 'clips': [], 'finalExportApproved': False})
        validate(state)
        refresh_ready(state)
        actions = 0
        # Pass 1 runs provider/status work up to the download stage, pass 2 downloads all
        # finished clips concurrently, pass 3 continues verification and evidence locally.
        for fetch_media in (False, True):
            for entry in state['clips']:
                if actions >= max_actions:
                    break
                actions += run_chain(state, entry, folder, max_actions - actions, fetch_media)
            if not fetch_media:
                parallel_downloads(state, folder)
        refresh_ready(state)
        ready = all(e['stage'] == 'ready_for_edit' for e in state['clips'])
        auto_cut = pacing_handoff() if ready else None
        save(handoff, {'ready': ready, 'approvalHash': state['approvalHash'],
                       'autoCut': auto_cut, 'editingComplete': False,
                       'clips': [{'id': e['id'], 'media': e['media'], 'packet': e['packet'],
                                  'report': e['boundReport']} for e in state['clips']] if ready else [],
                       'rules': ap.RULES, 'finalExportApproved': False})
        return summary(state)


def bind_review(batch, clip_id, result_path, completed=False):
    result = ap.load(result_path)
    result = result.get('structuredContent', result)
    with lock(batch) as folder:
        state = read(folder / 'state.json'); validate(state)
        entry = next(e for e in state['clips'] if e['id'] == clip_id)
        if entry['stage'] not in ('review_requested', 'review_running'):
            raise ValueError('Clip is not awaiting a review task')
        check_packet(entry)
        if not result.get('taskId') or not result.get('childThreadId'):
            raise ValueError('Save the actual delegate_task/task_status result')
        if result['taskId'] in ([h['taskId'] for h in entry.get('reviewHistory', [])]
                                + [h.get('reviewTaskId') for h in entry.get('takeHistory', [])]):
            raise ValueError('A new round requires a new delegated task')
        if entry.get('reviewTaskId') not in (None, result['taskId']):
            raise ValueError('A different reviewer task is already bound; do not duplicate it')
        if completed and (result.get('status') != 'completed' or result.get('hasPendingChildRuns')
                          or result.get('hasPendingQuestion') or result.get('pendingApproval')):
            raise ValueError('Review task is not fully completed')
        entry.update(stage='review_running', reviewTaskId=result['taskId'], reviewerId=result['childThreadId'])
        if completed:
            if not ap.local(entry['report']).is_file():
                raise ValueError('Completed task has no report file')
            entry['reviewCompleted'] = True
        # Immutable transport history remains local, separate from reviewer findings.
        receipt = folder / (tag(entry) + f".review-r{entry['reviewRound']}" + ('.completion.json' if completed else '.dispatch.json'))
        if receipt.exists() and read(receipt) != result:
            raise ValueError('Transport receipt differs; inspect before changing reviewer')
        if not receipt.exists():
            save(receipt, result)
        save(folder / 'state.json', state)
        return summary(state)



def recover(batch, clip_id, reason):
    if not reason.strip():
        raise ValueError('Record the corrected prerequisite or reconciliation evidence')
    with lock(batch) as folder:
        state = read(folder / 'state.json'); validate(state)
        entry = next(e for e in state['clips'] if e['id'] == clip_id)
        before = json.loads(json.dumps(entry))
        if entry['stage'] == 'unknown_submission':
            operation = kie.load(kie.paths(take_preview(entry))[1])
            if (operation.get('status') not in ('submitted', 'succeeded', 'failed')
                    or not operation.get('taskId') or operation.get('approvalHash') != take_hash(entry)):
                raise ValueError('The original provider operation is still unresolved')
            entry['stage'] = 'generation'
        elif entry['stage'] not in ('prepared', 'generation', 'download', 'evidence', 'review_running'):
            raise ValueError('This stage is not a local-error recovery; retain quality failures')
        entry.update(errors=0, retryAt=0, nextPollAt=0)
        entry.pop('errorType', None)
        save(folder / ('recovery-' + uuid.uuid4().hex + '.json'), {'before': before, 'reason': reason})
        save(folder / 'state.json', state)
        return summary(state)


def rereview(batch, clip_id, evidence_path):
    with lock(batch) as folder:
        state = read(folder / 'state.json'); validate(state)
        entry = next(e for e in state['clips'] if e['id'] == clip_id)
        if entry['stage'] != 'needs_evidence' or entry['reviewRound'] >= 3:
            raise ValueError('Only missing-evidence reviews can reopen; at most three rounds')
        check_packet(entry)
        unchanged([entry['reportFingerprint'], entry['boundFingerprint']])
        evidence = ap.fingerprint(evidence_path)
        if evidence in entry.get('additionalEvidence', []):
            raise ValueError('Provide new evidence for the new round')
        entry.setdefault('reviewHistory', []).append({
            'round': entry['reviewRound'], 'taskId': entry['reviewTaskId'],
            'reviewerId': entry['reviewerId'], 'report': entry['report'],
            'boundReport': entry['boundReport'], 'status': entry['stage']})
        entry.setdefault('additionalEvidence', []).append(evidence)
        entry['reviewRound'] += 1
        entry['report'] = rel(folder / (tag(entry) + f".review-r{entry['reviewRound']}.json"))
        request_path = folder / (tag(entry) + f".review-request-r{entry['reviewRound']}.json")
        request = review_request(state, entry, ap.local(entry['packet']), ap.local(entry['report']),
                                 folder / (tag(entry) + '.evidence'))
        save(request_path, request)
        entry.update(stage='review_requested', reviewRequest=rel(request_path), errors=0)
        for key in ('reviewCompleted', 'reviewTaskId', 'reviewerId', 'reportFingerprint',
                    'boundReport', 'boundFingerprint', 'retryAt', 'errorType'):
            entry.pop(key, None)
        save(folder / 'state.json', state)
        return summary(state)


def preview_info(state, entry):
    if not entry.get('media'):
        return {}
    contact = directory(state['batch']) / (tag(entry) + '.evidence') / 'contact.jpg'
    reviewed = {'ready_for_edit': 'PASSED', 'rejected': 'REJECTED', 'needs_evidence': 'NEEDS_EVIDENCE'}
    return {'mediaPath': entry['media']['path'],
            'contactSheet': rel(contact) if contact.is_file() else None,
            'reviewStatus': reviewed.get(entry['stage'], 'UNREVIEWED')}


def summary(state):
    folder = directory(state['batch'])
    return {'batch': state['batch'], 'approvalHash': state['approvalHash'],
            'approvalRequest': rel(folder / 'approval-request.json'), 'authorized': permitted(state),
            'clips': [{k: e[k] for k in ('id', 'stage', 'errors', 'errorType', 'nextPollAt', 'retryAt',
                       'reviewRequest', 'reviewTaskId', 'report', 'take', 'regenBlocked') if k in e} | preview_info(state, e)
                      for e in state['clips']],
            'editHandoff': rel(folder / 'edit-ready.json'), 'finalExportApproved': False,
            **({'grantStatus': state['grantStatus']} if state.get('grantStatus') else {})}


def waiting(state, entry):
    if entry.get('errors', 0) >= 3:
        return False
    if entry['stage'] in ACTIVE_STAGES:
        return True
    deps_ready = all(next(e for e in state['clips'] if e['id'] == dep)['stage'] == 'ready_for_edit'
                     for dep in entry['depends_on'])
    return entry['stage'] == 'prepared' and permitted(state) and deps_ready


def fetch(batch, wait_seconds=540, open_folder=False):
    """Repeat advance until every authorized clip is local and review-requested, or time runs out."""
    if not 0 <= wait_seconds <= 1800:
        raise ValueError('wait must be 0 to 1800 seconds')
    deadline = time.monotonic() + wait_seconds
    opened = False
    while True:
        result = advance(batch, 100)
        state = read(directory(batch) / 'state.json')
        if open_folder and not opened and any(e.get('media') for e in state['clips']) and shutil.which('open'):
            subprocess.run(['open', str(ap.local(f'Assets/generated/{safe_id(batch)}'))], check=False)
            opened = True
        pending = [e for e in state['clips'] if waiting(state, e)]
        if not pending:
            return result | {'fetchComplete': True}
        if time.monotonic() >= deadline:
            return result | {'fetchComplete': False, 'stillWaiting': [e['id'] for e in pending]}
        wake = min(max(e.get('nextPollAt', 0), e.get('retryAt', 0)) for e in pending)
        time.sleep(min(max(wake - time.time(), 2), POLL_SECONDS, max(deadline - time.monotonic(), 0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--manifest', required=True)
    p = sub.add_parser('authorize'); p.add_argument('--batch', required=True); p.add_argument('--approval-hash', required=True); p.add_argument('--evidence-ref', required=True)
    p = sub.add_parser('advance'); p.add_argument('--batch', required=True); p.add_argument('--max-actions', type=int, default=40)
    p = sub.add_parser('fetch'); p.add_argument('--batch', required=True); p.add_argument('--wait', type=int, default=540); p.add_argument('--open', action='store_true')
    p = sub.add_parser('status'); p.add_argument('--batch', required=True)
    p = sub.add_parser('grant-prepare'); p.add_argument('--spec', required=True)
    p = sub.add_parser('grant-authorize'); p.add_argument('--approved-hash', required=True); p.add_argument('--evidence-ref', required=True)
    p = sub.add_parser('recover'); p.add_argument('--batch', required=True); p.add_argument('--clip', required=True); p.add_argument('--reason', required=True)
    p = sub.add_parser('rereview'); p.add_argument('--batch', required=True); p.add_argument('--clip', required=True); p.add_argument('--evidence', required=True)
    for name in ('bind-review', 'complete-review'):
        p = sub.add_parser(name); p.add_argument('--batch', required=True); p.add_argument('--clip', required=True); p.add_argument('--result', required=True)
    a = parser.parse_args()
    try:
        if a.command == 'prepare': result = prepare(a.manifest)
        elif a.command == 'authorize': result = authorize(a.batch, a.approval_hash, a.evidence_ref)
        elif a.command == 'advance': result = advance(a.batch, a.max_actions)
        elif a.command == 'fetch': result = fetch(a.batch, a.wait, a.open)
        elif a.command == 'grant-prepare': result = grant_prepare(a.spec)
        elif a.command == 'grant-authorize': result = grant_authorize(a.approved_hash, a.evidence_ref)
        elif a.command == 'recover': result = recover(a.batch, a.clip, a.reason)
        elif a.command == 'rereview': result = rereview(a.batch, a.clip, a.evidence)
        elif a.command == 'status':
            with lock(a.batch):
                state = read(directory(a.batch) / 'state.json'); validate(state); refresh_ready(state)
                result = summary(state)
        else: result = bind_review(a.batch, a.clip, a.result, completed=a.command == 'complete-review')
        print(json.dumps(result, indent=2))
    except Exception as error:
        parser.exit(1, 'Blocked (' + type(error).__name__ + '). Inspect local state and receipts; no automatic paid retry.\n')


if __name__ == '__main__':
    main()
