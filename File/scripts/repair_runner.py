#!/usr/bin/env python3
"""Project-scoped paid repair allowance; all provider calls stay in kie_tasks."""
import argparse
from contextlib import contextmanager
from decimal import Decimal
import fcntl
import json
import os

import agentic_pipeline as ap
import kie_tasks as kie
from production_runner import safe_id, unchanged, result_url, download as download_media
from edit_farm import save


def nonempty(value):
    if not isinstance(value, str) or not value.strip(): raise ValueError('Nonempty evidence/identity required')
    return value


def folder(): return ap.local('File/repair_budget')


@contextmanager
def locked():
    path = folder(); path.mkdir(parents=True, exist_ok=True)
    with (path / '.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield path
        finally: fcntl.flock(handle, fcntl.LOCK_UN)


def proposal(policy_path):
    spec = ap.load(policy_path)
    default_inputs = []
    if 'repairCapCredits' not in spec or 'maxAttemptsPerAsset' not in spec:
        defaults = ap.load('File/repair_defaults.json')
        if defaults.get('version') != 1: raise ValueError('Unsupported repair defaults')
        for key in ('repairCapCredits', 'maxAttemptsPerAsset'):
            spec.setdefault(key, defaults[key])
        default_inputs.append(ap.fingerprint('File/repair_defaults.json'))
    if spec.get('version') != 1: raise ValueError('Expected repair allowance version 1')
    safe_id(spec['id']); nonempty(spec['producer_id'])
    for name in ('repairCapCredits', 'perAttemptCapCredits', 'projectCapCredits'):
        spec[name] = str(kie.amount(spec[name], positive=True))
    if not (kie.amount(spec['perAttemptCapCredits']) <= kie.amount(spec['repairCapCredits']) <= kie.amount(spec['projectCapCredits'])):
        raise ValueError('Per-attempt <= repair total <= full project credit limit required')
    if type(spec.get('maxAttemptsPerAsset')) is not int or not 1 <= spec['maxAttemptsPerAsset'] <= 10:
        raise ValueError('Explicit attempt limit must be 1 to 10 per asset')
    for name in ('models', 'allowedChecks'):
        if not isinstance(spec.get(name), list) or not spec[name] or len(spec[name]) != len(set(spec[name])):
            raise ValueError('Provide unique nonempty ' + name)
        for value in spec[name]: nonempty(value)
    if set(spec.get('modelTemplates', {})) != set(spec['models']):
        raise ValueError('Each allowed model needs a verified fixed payload template')
    for model, contract in spec['modelTemplates'].items():
        payload = contract['payload']; a, b = contract['prompt_field'], contract['images_field']
        if (set(payload) != {'model', 'input'} or payload['model'] != model
                or not a.startswith('input.') or not b.startswith('input.')
                or a == b or a.startswith(b+'.') or b.startswith(a+'.')):
            raise ValueError('Invalid model template or overlapping input bindings')
        for field in (a, b):
            obj, key = ap.field(payload, field)
            if key not in obj: raise ValueError('Declared template field is absent')
    if not isinstance(spec.get('requiredReviewChecks'), list) or not spec['requiredReviewChecks']:
        raise ValueError('Specify the complete review checklist for these assets')
    if not set(spec['allowedChecks']) <= set(spec['requiredReviewChecks']):
        raise ValueError('Allowed repair defects must be in the review checklist')
    if not isinstance(spec.get('assets'), list) or not 1 <= len(spec['assets']) <= 100:
        raise ValueError('List 1 to 100 repairable assets')
    assets = {}; inputs = [ap.fingerprint(policy_path), *default_inputs]
    for asset in spec['assets']:
        identifier = safe_id(asset['id'])
        if identifier in assets: raise ValueError('Duplicate repair asset ID')
        nonempty(asset['preserve'])
        if not isinstance(asset.get('references'), list) or not asset['references']:
            raise ValueError('Selected identity/scene references required')
        source = ap.fingerprint(asset['source'])
        references = [ap.fingerprint(p) for p in asset['references']]
        assets[identifier] = {**asset, 'source_fingerprint': source, 'reference_fingerprints': references}
        inputs.extend([source, *references])
    result = {'version': 1, 'scope': spec, 'assets': assets, 'inputs': inputs,
              'purpose': 'Correct confirmed review defects only; preserve selected characters/scenes/source. No new creative assets or final-export authority.'}
    result['approvalHash'] = ap.digest(result)
    return result


def authorize(policy_path, approved_hash, evidence_ref):
    p = proposal(policy_path)
    if approved_hash != p['approvalHash']: raise ValueError('Approve the exact displayed allowance hash')
    nonempty(evidence_ref)
    with locked() as path:
        state_path = path / 'state.json'
        if state_path.exists():
            state = load_state()
            if state['policy']['approvalHash'] != approved_hash:
                raise ValueError('Existing project allowance is immutable; do not reset spent credits or attempts')
            return summary(state)
        state = {'version': 1, 'policy': p, 'approval_evidence_ref': evidence_ref, 'attempts': []}
        save(state_path, state)
        return summary(state)


def load_state():
    state = ap.load('File/repair_budget/state.json'); p = state['policy']; copy = dict(p)
    given = copy.pop('approvalHash')
    if ap.digest(copy) != given: raise ValueError('Repair allowance changed')
    unchanged(p['inputs'])
    for attempt in state['attempts']:
        unchanged(attempt['inputs'])
        if attempt.get('disposition'): unchanged(attempt['disposition']['inputs'])
    return state


def charge(attempt):
    _, op = kie.paths(attempt['preview_id'])
    reported = kie.load(op).get('reportedCredits') if op.exists() else None
    # No refunds inferred: failed/unknown work and unused reservations remain counted.
    return max(kie.amount(attempt['capCredits']), kie.amount(reported or '0'))


def summary(state):
    cap = kie.amount(state['policy']['scope']['repairCapCredits'])
    used = sum((charge(a) for a in state['attempts']), Decimal(0))
    return {'allowance_id': state['policy']['scope']['id'], 'repairCapCredits': str(cap),
            'reservedOrReportedCredits': str(used), 'remainingCredits': str(max(Decimal(0), cap-used)),
            'attempts': len(state['attempts']), 'final_export_approved': False}


def review_evidence(spec, asset_id, media, report_path, completion_path):
    report = ap.load(report_path); completion = ap.load(completion_path)
    completion = completion.get('structuredContent', completion)
    if (completion.get('status') != 'completed' or completion.get('hasPendingChildRuns')
            or completion.get('hasPendingQuestion') or completion.get('pendingApproval')):
        raise ValueError('Independent defect review must be fully completed')
    reviewer = nonempty(completion.get('childThreadId')); task_id = nonempty(completion.get('taskId'))
    if (reviewer == spec['producer_id'] or report.get('reviewer_id') != reviewer
            or report.get('delegation_id') != task_id or report.get('asset_id') != asset_id
            or report.get('media') != media):
        raise ValueError('Review must bind actual independent task, affected asset and exact media')
    if not set(spec['requiredReviewChecks']) <= set(report.get('checks', {})):
        raise ValueError('Complete asset checklist required')
    for check in report['checks'].values():
        if check.get('status') not in ('pass','fail','uncertain'): raise ValueError('Invalid check status')
        nonempty(check.get('evidence'))
    return report


def bound_payload(state, req):
    spec = state['policy']['scope']; asset = state['policy']['assets'][req['asset_id']]
    contract = spec['modelTemplates'][req['model']]
    uploads = ap.load(req['uploads'])
    expected = [ap.fingerprint(req['media']), *asset['reference_fingerprints']]
    if not isinstance(uploads, list) or [u.get('media') for u in uploads] != expected:
        raise ValueError('Uploaded source/reference bindings differ from approved repair scope')
    for item in uploads:
        nonempty(item.get('url'))
        if not item['url'].startswith('https://'): raise ValueError('Verified HTTPS upload binding required')
        unchanged([item['receipt']])
    payload = json.loads(json.dumps(contract['payload']))
    obj,key=ap.field(payload, contract['images_field']);obj[key]=[u['url'] for u in uploads]
    obj,key=ap.field(payload, contract['prompt_field'])
    obj[key] = ('Targeted correction of the supplied source only. Preserve: '+asset['preserve']+
                '\nConfirmed failing checks: '+', '.join(req['failed_checks'])+
                '\nCorrection: '+nonempty(req['correction'])+
                '\nKeep the same characters and scene. Preserve all unrelated passing properties. No added text or zoom.')
    return payload


def download_result(preview_id, output, caller_id):
    with locked():
        state=load_state()
        if caller_id != state['policy']['scope']['producer_id']: raise ValueError('Wrong coordinator')
        attempt=next(a for a in state['attempts'] if a['preview_id']==preview_id)
        url=result_url({'preview':attempt['preview_id']}); media=ap.local(output)
        if not media.is_relative_to(ap.local('Assets')): raise ValueError('Repair output belongs under Assets')
        if not media.exists(): download_media(url,media,accept='image/*, video/*, application/octet-stream')
        receipt=ap.load(output+'.download.json')
        if receipt['urlHash'] != ap.digest(url) or receipt['media'] != ap.fingerprint(output):
            raise ValueError('Downloaded repair does not match provider provenance')
        return {'preview_id':preview_id,'media':receipt['media'],'next':'Independent full asset review required'}


def record_result(record_path, caller_id):
    with locked() as path:
        state=load_state();spec=state['policy']['scope'];record=ap.load(record_path)
        if caller_id != spec['producer_id']: raise ValueError('Wrong coordinator')
        attempt=next(a for a in state['attempts'] if a['preview_id']==record['preview_id'])
        if attempt.get('disposition'):
            if attempt['disposition']['record'] != ap.fingerprint(record_path): raise ValueError('Disposition already recorded')
            return summary(state)
        url=result_url({'preview':attempt['preview_id']})
        media=ap.fingerprint(record['media']);provenance=ap.load(record['media']+'.download.json')
        if provenance['media'] != media or provenance['urlHash'] != ap.digest(url):
            raise ValueError('Repair result must match the completed provider output')
        report=review_evidence(spec, attempt['asset_id'],media,record['report'],record['completion'])
        if report['delegation_id']==attempt['review_task_id']: raise ValueError('Re-review must be a fresh task')
        choice=record['selection'];nonempty(record['reason'])
        if choice not in ('accepted','use_corrected','retain_previous'): raise ValueError('Unknown repair disposition')
        if choice=='accepted' and any(c['status']!='pass' for c in report['checks'].values()):
            raise ValueError('Accept only a fully passing result')
        if choice!='accepted' and not any(c['status']=='fail' for c in report['checks'].values()):
            raise ValueError('Obtain evidence for uncertainty; do not spend on speculative repair')
        selected = attempt['media'] if choice=='retain_previous' else media
        inputs=[ap.fingerprint(p) for p in (record_path,record['media'],record['media']+'.download.json',record['report'],record['completion'])]
        attempt['disposition']={'selection':choice,'selected_media':selected,'record':ap.fingerprint(record_path),'inputs':inputs}
        save(path/'state.json',state);return summary(state)


def validate_request(state, request_path):
    req = ap.load(request_path); spec = state['policy']['scope']; safe_id(req['id'])
    if req['asset_id'] not in state['policy']['assets']: raise ValueError('Asset is outside the approved repair scope')
    nonempty(req['correction'])
    report = review_evidence(spec, req['asset_id'], ap.fingerprint(req['media']), req['report'], req['completion'])
    checks = req.get('failed_checks')
    if not isinstance(checks, list) or not checks or len(checks) != len(set(checks)) or not set(checks) <= set(spec['allowedChecks']):
        raise ValueError('Repair checks are outside the approved scope')
    for check in checks:
        finding = report.get('checks', {}).get(check, {})
        if finding.get('status') != 'fail': raise ValueError('Paid repair requires an observed defect, not missing evidence')
        nonempty(finding.get('evidence'))
    preview_path, operation_path = kie.paths(req['preview_id']); preview = kie.load(preview_path)
    if kie.hash_preview(preview) != preview['approvalHash']: raise ValueError('Preview changed')
    if preview['payload']['model'] not in spec['models']: raise ValueError('Model is outside the approved allowance')
    if req['model'] != preview['payload']['model'] or preview['payload'] != bound_payload(state, req):
        raise ValueError('Exact payload is not bound to the approved source, references and correction')
    if kie.amount(preview['capCredits'], positive=True) > kie.amount(spec['perAttemptCapCredits']):
        raise ValueError('Per-attempt repair reservation exceeded')
    evidence = [ap.fingerprint(p) for p in (request_path, req['report'], req['completion'], req['media'], req['uploads'])]
    evidence.extend(u['receipt'] for u in ap.load(req['uploads']))
    evidence.append(ap.fingerprint(str(preview_path.relative_to(ap.ROOT))))
    return req, preview, operation_path, evidence


def submit(request_path, caller_id):
    with locked() as path:
        state = load_state(); spec = state['policy']['scope']
        if nonempty(caller_id) != spec['producer_id']: raise ValueError('Only the authorized coordinator may submit repairs')
        req, preview, operation_path, inputs = validate_request(state, request_path)
        prior = next((a for a in state['attempts'] if a['preview_id'] == preview['id'] or a['id'] == req['id']), None)
        if prior:
            if (prior['preview_id'] != preview['id'] or prior['id'] != req['id'] or prior['inputs'] != inputs):
                raise ValueError('Repair attempt already bound; preserve its request and preview')
        else:
            prior_asset = [a for a in state['attempts'] if a['asset_id']==req['asset_id']]
            expected_media=state['policy']['assets'][req['asset_id']]['source_fingerprint']
            if prior_asset:
                disposition=prior_asset[-1].get('disposition')
                if not disposition: raise ValueError('Review and record the previous repair before another attempt')
                if disposition['selection']=='accepted': raise ValueError('Accepted asset needs no further repair')
                expected_media=disposition['selected_media']
            if ap.fingerprint(req['media']) != expected_media: raise ValueError('Repair must use the selected asset lineage')
            review_task=ap.load(req['report'])['delegation_id']
            if any(a['review_task_id']==review_task for a in state['attempts']): raise ValueError('A corrective attempt needs a fresh review')
            if operation_path.exists(): raise ValueError('Cannot retrospectively charge an existing generation to the repair allowance')
            for attempt in state['attempts']:
                _, operation = kie.paths(attempt['preview_id'])
                if operation.exists() and kie.load(operation)['status'] in ('submitting', 'unknown'):
                    raise ValueError('Reconcile unknown repair before submitting another')
            if sum(a['asset_id'] == req['asset_id'] for a in state['attempts']) >= spec['maxAttemptsPerAsset']:
                raise ValueError('Repair attempt limit reached for this asset')
            used = sum((charge(a) for a in state['attempts']), Decimal(0))
            if used + kie.amount(preview['capCredits']) > kie.amount(spec['repairCapCredits']):
                raise ValueError('Repair allowance exhausted')
            state['attempts'].append({'id': req['id'], 'asset_id': req['asset_id'], 'preview_id': preview['id'],
                                      'approvalHash': preview['approvalHash'], 'capCredits': preview['capCredits'], 'inputs': inputs, 'media':ap.fingerprint(req['media']), 'review_task_id':review_task})
            # Persist reservation before any network request. A crash reuses this exact preview.
            save(path / 'state.json', state)
        if not operation_path.exists() and sum((charge(a) for a in state['attempts']), Decimal(0)) > kie.amount(spec['repairCapCredits']):
            raise ValueError('Reported repair charges exceed the allowance; no further submission')
        # Scoped budget was explicitly part of the approved allowance. Key selection stays untouched.
        previous_cap = os.environ.get('KIE_PROJECT_CAP_CREDITS')
        os.environ['KIE_PROJECT_CAP_CREDITS'] = spec['projectCapCredits']
        try: result = kie.submit(preview['id'], preview['approvalHash'])
        finally:
            if previous_cap is None: os.environ.pop('KIE_PROJECT_CAP_CREDITS', None)
            else: os.environ['KIE_PROJECT_CAP_CREDITS'] = previous_cap
        return {**summary(state), 'submission': result, 'next': 'Poll the existing Kie task, download the new version, independently re-review, then resume dependent work.'}


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    q=sub.add_parser('prepare'); q.add_argument('--policy',required=True)
    q=sub.add_parser('authorize'); q.add_argument('--policy',required=True); q.add_argument('--approved-hash',required=True); q.add_argument('--evidence-ref',required=True)
    q=sub.add_parser('bind-payload');q.add_argument('--request',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('download');q.add_argument('--preview',required=True);q.add_argument('--output',required=True);q.add_argument('--caller-id',required=True)
    q=sub.add_parser('record-result');q.add_argument('--record',required=True);q.add_argument('--caller-id',required=True)
    q=sub.add_parser('submit'); q.add_argument('--request',required=True); q.add_argument('--caller-id',required=True)
    sub.add_parser('status'); args=p.parse_args()
    try:
        if args.command=='prepare': result=proposal(args.policy)
        elif args.command=='authorize': result=authorize(args.policy,args.approved_hash,args.evidence_ref)
        elif args.command=='bind-payload':
            with locked():
                result=bound_payload(load_state(),ap.load(args.request));ap.write(args.out,result)
        elif args.command=='download':result=download_result(args.preview,args.output,args.caller_id)
        elif args.command=='record-result':result=record_result(args.record,args.caller_id)
        elif args.command=='submit': result=submit(args.request,args.caller_id)
        else:
            with locked(): result=summary(load_state())
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as error: p.exit(1, 'Blocked ('+type(error).__name__+'): '+str(error)+'\n')


if __name__=='__main__': main()
