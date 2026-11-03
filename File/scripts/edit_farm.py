#!/usr/bin/env python3
"""Supplied spoken-video farm ledger. Agents call T3/Premiere; this CLI verifies local gates."""
import argparse
from contextlib import contextmanager
from fractions import Fraction
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess

import agentic_pipeline as ap
import edit_decisions
import premiere_writer
from production_runner import safe_id, save as atomic_save, read, rel, unchanged, pacing_handoff

ANALYSIS = ('dialogue', 'audio_pacing', 'visual')
QUALITY_METHODS = {
    'wording_order_ending': {'direct_audio', 'direct_av'},
    'pacing_all_joins': {'direct_av'},
    'audio_quality': {'direct_audio', 'direct_av'},
    'av_sync': {'direct_av'},
    'visual_continuity': {'direct_video', 'direct_av'},
    'no_added_text_or_guides': {'direct_video', 'direct_av'},
    'no_added_camera_motion': {'direct_video', 'direct_av'},
}
BRIEFS = {
    'dialogue': 'Produce a verbatim timestamped recording transcript and distinct occurrence IDs. Preserve the original separately from edit selections. When a supplied script exists, map its exact words to actual recorded occurrences. Identify missing words, retakes and uncertain transcription. Listen to resolve uncertainty; ASR alone is not word-perfect evidence. No invented approved script or substantive rewrite.',
    'audio_pacing': 'Inspect actual sound, candidate silences, clip heads/tails, useful breaths, clipping, noise and delivery rhythm. Recommend source-time cuts using File/docs/AUTO_CUT.md. Silence thresholds are candidate finders, not proof that no speech exists. Do not auto-remove breaths or change playback speed.',
    'visual': 'Inspect actual supplied visuals, scene/gesture/identity continuity, glitches and potential B-roll uses. Separate reference-only assets from editable media. Do not suggest added text, zooms or reframing. Distinguish source-existing motion/text from added effects. Sampled frames do not establish full temporal behavior.',
    'assembled_review': 'Independently watch/listen to the exact assembled edit at normal speed. Check required words, order and complete ending, every join, natural pacing, protected breaths/gestures, A/V sync and fixed framing. Verify no added text or editing guides. Inspect all evidence and EDL; source reviews cannot pass an assembled edit.',
    'delivery_review': 'Independently inspect the actual exported file, compare it to the exact reviewed sequence and delivery contract, and check the entire narration/ending, all joins, sync, sound and visuals. Decode/probe success is not content correctness. Check for added captions/guides or camera effects. Do not approve export spending or change media.'
}


def sync_directory(path):
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(path, data):
    """Durable rename plus directory entries before any other journal advances."""
    atomic_save(path, data)  # fsyncs the file before atomic replacement
    directory = path.parent
    while True:
        sync_directory(directory)
        if directory == ap.ROOT or ap.ROOT not in directory.parents:
            break
        directory = directory.parent


def folder(run):
    return ap.local('File/edit_farm/runs/' + safe_id(run))


@contextmanager
def locked(run):
    path = folder(run); path.mkdir(parents=True, exist_ok=True)
    with (path / '.lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield path
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def nonempty(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Nonempty identity/evidence text required')
    return value


def load_state(run):
    state = read(folder(run) / 'state.json')
    unchanged(state['inputs'])
    if not ap.local(state['project']).is_file():
        raise ValueError('Existing Premiere project is missing')
    for task in state['tasks'].values():
        if task.get('report'):
            unchanged([task['report']])
        if task.get('failure'):
            unchanged([task['failure']])
    return state


def idle_writer(state):
    owner = premiere_writer.inspect(state['project'])
    if owner is None or (owner['run_id'], owner['owner_id']) != (state['run'], state['producer_id']):
        raise ValueError('Claim the project with the actual coordinator identity first')
    if owner['pending'] is not None or state.get('writer_epoch', owner['epoch']) != owner['epoch']:
        raise ValueError('Resolve pending writer operations and stale ownership before continuing')
    return owner


def active_edit(state):
    idle_writer(state)
    edit = state['edit']
    unchanged(edit['inputs'])
    if ap.fingerprint(state['project']) != edit['project_saved']:
        raise ValueError('Saved project changed; capture and review a new edit version')
    return edit


def task_packet(state, key, role, context, extra_inputs=None, previous=None):
    if key in state['tasks']:
        raise ValueError('Task round already exists; preserve its transport and findings')
    packet = {'version': 1, 'run': state['run'], 'task': key, 'role': role,
              'producer_id': state['producer_id'], 'inputs': state['inputs'] + (extra_inputs or []),
              'sourceAuthority': state['sourceAuthority'], 'sources': state['sources'], 'source_order': state['source_order'],
              'context': context, 'previous_findings': previous or [],
              'checks': list(QUALITY_METHODS) if role not in ANALYSIS else []}
    packet['packet_hash'] = ap.digest(packet)
    packet_path = folder(state['run']) / (key + '.packet.json')
    report_path = folder(state['run']) / (key + '.report.json')
    if packet_path.exists() and read(packet_path) != packet:
        raise ValueError('Task key already used by different evidence; preserve previous rounds')
    if not packet_path.exists(): save(packet_path, packet)
    request = {'role': 'review' if role not in ANALYSIS else 'research', 'mode': 'async',
               'title': role.replace('_', ' ') + ': ' + state['run'],
               'clientRequestId': 'edit-farm-' + state['run'] + '-' + key + '-' + packet['packet_hash'][:12],
               'task': (f'Project: {ap.ROOT}. Read File/docs/EDIT_FARM.md and packet {rel(packet_path)}. '
                        + BRIEFS[role] + f' Write only your assigned report {rel(report_path)} and supporting '
                        'artifacts in its named task subfolder. Return the documented report JSON. '
                        'Use your actual child thread ID as reviewer_id. No Premiere calls (including playback/selection), '
                        'shared memory edits, generation, purchases, credentials, source changes or model downloads. '
                        'Coordinate needed host evidence through the parent writer. Unsupported evidence stays uncertain; '
                        'list exact missing capabilities. No self-granted export approval.')}
    request_path = folder(state['run']) / (key + '.request.json'); save(request_path, request)
    state['tasks'][key] = {'role': role, 'round': 1, 'state': 'pending', 'packet': ap.fingerprint(rel(packet_path)),
                           'request': rel(request_path), 'report_path': rel(report_path)}
    return key


def inspect_source(source):
    sid = safe_id(source['id'])
    if source.get('role') not in ('primary', 'broll', 'reference'):
        raise ValueError('Every source needs primary/broll/reference role')
    media = ap.fingerprint(source['path']); info = ap.probe(source['path'])
    duration = info.get('format', {}).get('duration', '')
    try:
        number = float(duration)
    except (TypeError, ValueError):
        raise ValueError('Sources must have a measurable duration; use video/audio references here') from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError('Source duration must be positive')
    streams = [{k: stream[k] for k in ('codec_type', 'codec_name', 'width', 'height', 'avg_frame_rate',
                                      'r_frame_rate', 'sample_rate', 'channels') if k in stream}
               for stream in info['streams']]
    if source['role'] == 'primary' and not any(s['codec_type'] == 'audio' for s in streams):
        raise ValueError('Spoken-video farm needs primary speech audio; route silent footage to broll-director')
    return sid, {'media': media, 'role': source['role'], 'duration_seconds': str(duration), 'streams': streams}


def start(manifest_path):
    manifest = ap.load(manifest_path); run = safe_id(manifest['id'])
    nonempty(manifest['producer_id']); nonempty(manifest['intent'])
    project = ap.local(manifest['project'])
    if not project.is_file() or project.suffix.lower() != '.prproj':
        raise ValueError('Use the existing saved Premiere project')
    source_list = manifest['sources']
    if not isinstance(source_list, list) or not 1 <= len(source_list) <= 100:
        raise ValueError('Provide 1 to 100 explicit source assets')
    sources = {}; inputs = [ap.fingerprint(manifest_path), pacing_handoff()['policy']]
    for source in source_list:
        sid, inspected = inspect_source(source)
        if sid in sources:
            raise ValueError('Duplicate source ID')
        sources[sid] = inspected; inputs.append(inspected['media'])
    if not any(s['role'] == 'primary' and any(t['codec_type'] == 'video' for t in s['streams']) for s in sources.values()):
        raise ValueError('At least one primary video is required')
    if manifest.get('script'):
        inputs.append(ap.fingerprint(manifest['script']))
    with locked(run) as path:
        if (path / 'state.json').exists():
            state = load_state(run)
            if state['inputs'] != inputs:
                raise ValueError('Run ID belongs to different intake')
            return status(state)
        state = {'version': 1, 'run': run, 'producer_id': manifest['producer_id'], 'project': rel(project),
                 'sourceAuthority': 'supplied_script' if manifest.get('script') else 'verified_recording',
                 'intent': manifest['intent'], 'sources': sources, 'source_order': list(sources), 'inputs': inputs, 'tasks': {},
                 'phase': 'analysis', 'edit_versions': [], 'delivered': None}
        for role in ANALYSIS:
            task_packet(state, role + '-r1', role, {'intent': manifest['intent'], 'script': manifest.get('script')})
        save(path / 'state.json', state)
        return status(state)


def packet_for(task, verify_inputs=True):
    unchanged([task['packet']]); packet = ap.load(task['packet']['path'])
    given = packet.pop('packet_hash')
    if ap.digest(packet) != given:
        raise ValueError('Packet hash mismatch')
    packet['packet_hash'] = given
    if verify_inputs: unchanged(packet['inputs'])
    return packet


def transport(path):
    value = ap.load(path); value = value.get('structuredContent', value)
    nonempty(value['taskId']); nonempty(value['childThreadId'])
    return value


def bind(run, key, result_path):
    with locked(run) as path:
        state = load_state(run); task = state['tasks'][key]; packet_for(task)
        if task['state'] not in ('pending', 'running'):
            raise ValueError('Task is not pending/running')
        result = transport(result_path)
        if result['childThreadId'] == state['producer_id']:
            raise ValueError('A specialist must be a separate child')
        if task.get('task_id') not in (None, result['taskId']):
            raise ValueError('Task already bound; do not duplicate dispatch')
        if any(t.get('task_id') == result['taskId'] for k, t in state['tasks'].items() if k != key):
            raise ValueError('Each farm task/round needs a distinct delegated task')
        receipt_path = path / (key + '.dispatch.json')
        if receipt_path.exists() and read(receipt_path) != result:
            raise ValueError('Do not replace a dispatch receipt with status output')
        if not receipt_path.exists(): save(receipt_path, result)
        task.update(state='running', task_id=result['taskId'], reviewer_id=result['childThreadId'])
        save(path / 'state.json', state); return status(state)


def quality(report):
    checks = report['checks']
    if set(checks) != set(QUALITY_METHODS):
        raise ValueError('Every assembled/delivery quality check is required')
    for name, check in checks.items():
        if check.get('status') not in ('pass', 'fail', 'uncertain'):
            raise ValueError('Invalid quality status')
        nonempty(check.get('evidence')); nonempty(check.get('method'))
        if check['status'] == 'pass' and (check.get('coverage') != 'full_sequence'
                                         or check['method'] not in QUALITY_METHODS[name]):
            raise ValueError('A quality pass needs full temporal/audio evidence in the proper modality')
    values = [c['status'] for c in checks.values()]
    return 'fail' if 'fail' in values else 'uncertain' if 'uncertain' in values else 'pass'


def collect(run, key, result_path):
    with locked(run) as path:
        state = load_state(run); task = state['tasks'][key]
        if task['state'] != 'running': raise ValueError('Task must be running')
        packet = packet_for(task, verify_inputs=False); result = transport(result_path)
        if (result['taskId'] != task['task_id'] or result['childThreadId'] != task['reviewer_id']
                or result.get('hasPendingChildRuns') or result.get('hasPendingQuestion') or result.get('pendingApproval')):
            raise ValueError('Exact delegated task must be fully completed')
        # Obsolete results are retained for audit, never allowed to change active phases.
        current = (task is max((t for t in state['tasks'].values() if t['role'] == task['role']),
                               key=lambda t: t['round']) if task['role'] in ANALYSIS else
                   state.get('quality_task') == key and packet['context']['edit_hash'] == state.get('edit', {}).get('hash'))
        if not current:
            if result.get('status') not in ('completed', 'failed', 'cancelled', 'interrupted'):
                raise ValueError('Obsolete task is not terminal')
            archive = path / (key + '.obsolete.json'); save(archive, result)
            task.update(state='complete', verdict='obsolete', failure=ap.fingerprint(rel(archive)))
            save(path / 'state.json', state); return status(state)
        unchanged(packet['inputs'])
        if result.get('status') in ('failed', 'cancelled', 'interrupted'):
            failure_path = path / (key + '.failure.json'); save(failure_path, result)
            task.update(state='complete', verdict='blocked', failure=ap.fingerprint(rel(failure_path)))
            state['phase'] = ('analysis_blocked' if task['role'] in ANALYSIS else
                              'needs_edit_review_evidence' if task['role'] == 'assembled_review' else 'needs_delivery_evidence')
            save(path / 'state.json', state); return status(state)
        if result.get('status') != 'completed':
            raise ValueError('Exact delegated task must be fully completed')
        report = ap.load(task['report_path'])
        if report.get('packet_hash') != packet['packet_hash'] or report.get('reviewer_id') != task['reviewer_id']:
            raise ValueError('Report does not match delegated task/packet')
        if task['role'] in ANALYSIS:
            if report.get('status') not in ('complete', 'blocked') or not report.get('evidence'):
                raise ValueError('Analysis requires status and actual evidence or concrete unavailable reason')
            verdict = report['status']
        else:
            edit = active_edit(state)
            if packet['context']['edit_hash'] != edit['hash']:
                raise ValueError('Review belongs to another edit version')
            if task['role'] == 'delivery_review':
                unchanged([state['render']['media']])
            verdict = quality(report)
            if report.get('reviewed_join_ids') != packet['context']['join_ids']:
                raise ValueError('Review must account for every current join')
        task.update(state='complete', verdict=verdict, report=ap.fingerprint(task['report_path']))
        save(path / (key + '.completion.json'), result)
        if task['role'] in ANALYSIS:
            latest = latest_analysis(state)
            state['phase'] = 'ready_for_edit' if all(t.get('verdict') == 'complete' for t in latest) else 'analysis'
        elif task['role'] == 'assembled_review':
            state['phase'] = 'awaiting_user_review' if verdict == 'pass' else 'needs_edit_review_evidence' if verdict == 'uncertain' else 'needs_revision'
        else:
            state['phase'] = 'delivered_verified' if verdict == 'pass' else 'needs_delivery_evidence' if verdict == 'uncertain' else 'delivery_failed'
            if verdict == 'pass':
                state['delivered'] = {'media': state['render']['media'], 'project': state['project'],
                                      'sequence_id': state['edit']['sequence_id'], 'edit_hash': state['edit']['hash'],
                                      'review': task['report'], 'technical': state['render']['technical']}
        save(path / 'state.json', state); return status(state)


def latest_analysis(state):
    return [max((t for t in state['tasks'].values() if t['role'] == role), key=lambda t: t['round']) for role in ANALYSIS]


def record_edit(run, record_path):
    with locked(run) as path:
        state = load_state(run)
        if state['phase'] in ('export_submitting', 'render_pending', 'delivery_review', 'needs_delivery_evidence', 'delivered_verified'):
            raise ValueError('Resolve current render/delivery or start a new run before replacing the edit')
        if not all(t.get('verdict') == 'complete' for t in latest_analysis(state)):
            raise ValueError('Complete source analysis before recording an edit')
        record = ap.load(record_path)
        if record['producer_id'] != state['producer_id'] or rel(ap.local(record['project'])) != state['project']:
            raise ValueError('Wrong writer/project')
        owner = premiere_writer.claim(state['project'], run, state['producer_id'])
        if owner['epoch'] != record['writer_epoch'] or owner['pending'] is not None:
            raise ValueError('Resolve all writer operations with fresh readback before recording an edit')
        nonempty(record['sequence_id']); nonempty(record['edit_version'])
        if record['edit_version'] in state['edit_versions']:
            raise ValueError('Use a new edit version and retain prior reviews')
        source_map = {sid: json.loads(json.dumps(state['sources'][sid])) for sid in state['source_order']}
        for sid, desc in record['transcripts'].items(): source_map[sid]['transcript'] = desc
        plan = ap.load(record['decisions']); validated = edit_decisions.validate(plan, source_map)
        if plan['mode'] != state['sourceAuthority']:
            raise ValueError('Edit authority must match source intake')
        delivery = record['delivery']
        if (type(delivery['width']) is not int or type(delivery['height']) is not int
                or min(delivery['width'], delivery['height']) <= 0 or Fraction(delivery['frame_rate']) <= 0
                or delivery.get('audio_required') is not True):
            raise ValueError('Provide actual delivery dimensions/timebase and speech audio')
        if Fraction(delivery['frame_rate']) != Fraction(plan['frame_rate']):
            raise ValueError('Delivery and edit timebases differ')
        output = ap.local(delivery['output'])
        if not output.is_relative_to(ap.local('Exports')) or output.exists() or output.suffix.lower() != '.mp4':
            raise ValueError('Use a fresh versioned MP4 path under Exports')
        evidence = [ap.fingerprint(record_path), ap.fingerprint(record['decisions']),
                    ap.fingerprint(record['snapshot']), *[ap.fingerprint(p) for p in record['operation_receipts']]]
        if not record['operation_receipts']: raise ValueError('Actual host operation receipts are required')
        evidence.extend(ap.fingerprint(d['path']) for d in record['transcripts'].values())
        evidence.extend(ap.fingerprint(o['evidence']['path']) for o in plan['omissions'])
        duration = Fraction(validated['duration_seconds'])
        boundaries = sorted({Fraction(r[k]) for r in validated['plan']['ranges']
                             for k in ('timelineIn', 'timelineOut')} - {Fraction(0), duration})
        joins = ['join-' + str(i + 1) for i in range(len(boundaries))]
        join_points = [{'id': key, 'timeline_seconds': str(t)} for key, t in zip(joins, boundaries)]
        edit = {'sequence_id': record['sequence_id'], 'edit_version': record['edit_version'],
                'inputs': evidence, 'project_saved': ap.fingerprint(state['project']),
                'delivery': delivery, 'duration_seconds': validated['duration_seconds'],
                'join_ids': joins, 'join_points': join_points, 'decisions_summary': validated, 'snapshot': record['snapshot']}
        edit['hash'] = ap.digest(edit)
        state['edit'] = edit; state['writer_epoch'] = owner['epoch']; state['edit_versions'].append(record['edit_version'])
        state.pop('approval', None); state.pop('render', None); state['delivered'] = None
        key = 'assembled-' + safe_id(record['edit_version']) + '-r1'
        state['quality_task'] = task_packet(state, key, 'assembled_review',
            {'edit_hash': edit['hash'], 'edit': edit, 'join_ids': joins}, evidence)
        state['phase'] = 'assembled_review'; save(path / 'state.json', state)
        return status(state)


def approve_export(run, edit_hash, evidence_ref):
    with locked(run) as path:
        state = load_state(run); edit = active_edit(state)
        if state['phase'] != 'awaiting_user_review' or edit_hash != edit['hash']:
            raise ValueError('Only the exact reviewed edit may be approved')
        nonempty(evidence_ref)
        if ap.local(edit['delivery']['output']).exists(): raise ValueError('Export destination already exists')
        approval = {'edit_hash': edit_hash, 'evidence_ref': evidence_ref, 'delivery': edit['delivery']}
        approval_path = path / ('approval-' + safe_id(edit['edit_version']) + '.json')
        save(approval_path, approval)
        state['approval_fingerprint'] = ap.fingerprint(rel(approval_path))
        state['approval'] = approval; state['phase'] = 'export_authorized'
        save(path / 'state.json', state); return status(state)


def render_started(run, receipt_path):
    """Reconcile an accepted journaled export after interruption; never submit it."""
    with locked(run) as path:
        state = load_state(run); edit = active_edit(state)
        if state['phase'] not in ('export_submitting', 'render_pending'):
            raise ValueError('No journaled export submission to reconcile')
        unchanged([state['approval_fingerprint']])
        render = state['render']; owner = idle_writer(state)
        accepted = [e for e in owner['history'] if e['event'] == 'resolve'
                    and e['operation_id'] == render['operation_id'] and e['outcome'] in ('verified', 'no_effect')]
        receipt = ap.fingerprint(receipt_path)
        if not accepted or receipt != accepted[-1]['receipt']['source']:
            raise ValueError('Receipt must match the verified journaled export acceptance')
        if accepted[-1]['outcome'] == 'no_effect':
            state.setdefault('render_history', []).append({'render': state.pop('render'),
                'resolution': accepted[-1], 'edit_hash': edit['hash']})
            state['phase'] = 'export_authorized'; save(path / 'state.json', state); return status(state)
        render['start_receipt'] = accepted[-1]['receipt']['archive']
        state['phase'] = 'render_pending'; save(path / 'state.json', state); return status(state)


def reconcile_render_failure(run, evidence_path, caller_id):
    """Record positive terminal evidence. Unknown/slow renders remain blocked."""
    with locked(run) as path:
        state = load_state(run)
        if nonempty(caller_id) != state['producer_id']: raise ValueError('Wrong invoking coordinator identity')
        idle_writer(state)
        if state['phase'] not in ('export_submitting', 'render_pending'):
            raise ValueError('No unresolved render to reconcile')
        evidence = ap.load(evidence_path); render = state['render']
        if (evidence.get('operation_id') != render['operation_id']
                or evidence.get('edit_hash') != state['edit']['hash']
                or evidence.get('output') != render['output']
                or evidence.get('status') not in ('failed', 'cancelled', 'invalid_output')
                or evidence.get('host_terminal') is not True or not evidence.get('host_evidence')):
            raise ValueError('Exact render identity and positive terminal host evidence required')
        nonempty(evidence.get('reason'))
        # Save a separate immutable audit copy; leave any failed output untouched.
        archived = path / ('render-' + safe_id(state['edit']['edit_version']) + '.failure.json')
        if archived.exists() and read(archived) != evidence:
            raise ValueError('Conflicting archived render failure; preserve the original evidence')
        if not archived.exists(): save(archived, evidence)
        failure = {'render': render, 'evidence': ap.fingerprint(rel(archived)), 'edit_hash': state['edit']['hash']}
        if ap.local(render['output']).is_file(): failure['output'] = ap.fingerprint(render['output'])
        state.setdefault('render_history', []).append(failure)
        state['phase'] = 'render_failed'; save(path / 'state.json', state); return status(state)


def verify_render(run, completion_receipt):
    with locked(run) as path:
        state = load_state(run); edit = active_edit(state)
        if state['phase'] != 'render_pending': raise ValueError('No pending render to verify')
        unchanged([state['render']['start_receipt'], state['approval_fingerprint']])
        media = ap.fingerprint(state['render']['output']); info = ap.probe(media['path'])
        videos = [s for s in info['streams'] if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')]
        audio = [s for s in info['streams'] if s.get('codec_type') == 'audio']
        contract = edit['delivery']; fps = Fraction(contract['frame_rate'])
        if len(videos) != 1 or not audio: raise ValueError('Final video needs one video stream and speech audio')
        v = videos[0]
        if (v.get('width'), v.get('height')) != (contract['width'], contract['height']) or Fraction(v['avg_frame_rate']) != fps:
            raise ValueError('Final dimensions/timebase differ from reviewed delivery contract')
        if abs(Fraction(str(info['format']['duration'])) - Fraction(edit['duration_seconds'])) > 2 / fps:
            raise ValueError('Final duration differs by more than two frames')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(ap.local(media['path'])),
                        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                       check=True, capture_output=True, timeout=600)
        unchanged([media])
        technical_path = path / ('render-' + safe_id(edit['edit_version']) + '.technical.json')
        technical = {'media': media, 'probe': info, 'full_decode': True, 'content_review': 'pending',
                     'completion_receipt': ap.fingerprint(completion_receipt)}
        save(technical_path, technical)
        state['render'].update(media=media, technical=ap.fingerprint(rel(technical_path)))
        key = 'delivery-' + safe_id(edit['edit_version']) + '-r1'
        state['quality_task'] = task_packet(state, key, 'delivery_review',
            {'edit_hash': edit['hash'], 'edit': edit, 'media': media, 'join_ids': edit['join_ids']},
            edit['inputs'] + [media, state['render']['technical']])
        state['phase'] = 'delivery_review'; save(path / 'state.json', state); return status(state)


def rereview(run, key, evidence_path):
    with locked(run) as path:
        state = load_state(run); task = state['tasks'][key]
        if task['state'] != 'complete' or task.get('verdict') not in ('blocked', 'uncertain') or task['round'] >= 3:
            raise ValueError('Only blocked/uncertain work can retry with new evidence, up to three rounds')
        if task['role'] not in ANALYSIS and state['quality_task'] != key:
            raise ValueError('Only the current quality task may be retried')
        if task['role'] not in ANALYSIS: active_edit(state)
        packet = packet_for(task); evidence = ap.fingerprint(evidence_path)
        if evidence in packet['inputs']: raise ValueError('New evidence is required')
        next_round = task['round'] + 1; new_key = key.rsplit('-r', 1)[0] + '-r' + str(next_round)
        previous = packet['previous_findings'] + [task.get('report') or task['failure']]
        new = task_packet(state, new_key, task['role'], packet['context'],
                          packet['inputs'][len(state['inputs']):] + [evidence], previous)
        state['tasks'][new]['round'] = next_round
        if task['role'] in ANALYSIS: state['phase'] = 'analysis'
        else:
            active_edit(state); state['quality_task'] = new
            state['phase'] = 'assembled_review' if task['role'] == 'assembled_review' else 'delivery_review'
        save(path / 'state.json', state); return status(state)



def writer_command(run, action, caller_id, intent=None, operation=None, receipt=None, snapshot=None, outcome=None):
    with locked(run) as path:
        state = load_state(run)
        if nonempty(caller_id) != state['producer_id']:
            raise ValueError('Wrong invoking coordinator identity; ownership transfer must be explicit')
        owner = ({'epoch': state['writer_epoch']} if action == 'resolve-operation'
                 else premiere_writer.claim(state['project'], run, caller_id))
        if state.get('writer_epoch') not in (None, owner['epoch']):
            raise ValueError('Writer generation changed; inspect ownership before continuing')
        state['writer_epoch'] = owner['epoch']
        args = (state['project'], run, caller_id, owner['epoch'])
        if action == 'claim-writer': result = owner
        elif action == 'begin-operation':
            plan = ap.load(intent)
            if plan.get('kind') == 'export':
                edit = active_edit(state)
                if state['phase'] != 'export_authorized' or state['approval']['edit_hash'] != edit['hash']:
                    raise ValueError('Export operation requires current-version authorization')
                unchanged([state['approval_fingerprint']])
            result = premiere_writer.begin(*args, intent)
            if plan.get('kind') == 'export':
                state['render'] = {'operation_id': result['operation_id'], 'intent': result['intent']['archive'],
                                   'output': edit['delivery']['output']}
                state['phase'] = 'export_submitting'
        elif action == 'resolve-operation':
            pending_owner = premiere_writer.inspect(state['project'], allow_saved_replacement=True)
            pending = pending_owner['pending']
            if pending and pending['operation_id'] == operation:
                archived = pending['intent']['archive']; unchanged([archived])
                if ap.load(archived['path']).get('kind') == 'export':
                    if state.get('render', {}).get('operation_id') not in (None, operation):
                        raise ValueError('Export operation differs from tracked submission')
                    state['render'] = state.get('render') or {'operation_id': operation,
                        'intent': archived, 'output': state['edit']['delivery']['output']}
                    state['phase'] = 'export_submitting'
                    # Fence retries before clearing the separately durable writer journal.
                    save(path / 'state.json', state)
            result = premiere_writer.resolve(*args, operation, receipt, snapshot, outcome)
            if state.get('render', {}).get('operation_id') == operation:
                if outcome == 'verified':
                    state['render']['start_receipt'] = result['history'][-1]['receipt']['archive']
                    state['phase'] = 'render_pending'
                elif outcome == 'no_effect':
                    state.setdefault('render_history', []).append({'render': state.pop('render'),
                        'resolution': result['history'][-1], 'edit_hash': state['edit']['hash']})
                    state['phase'] = 'export_authorized'

        else:
            result = premiere_writer.release(*args)
            state.pop('writer_epoch', None)
        save(path / 'state.json', state)
        return {'run': run, 'writer': result}


def status(state):
    actions = [{'task': key, 'request': task['request'], 'task_id': task.get('task_id'), 'state': task['state']}
               for key, task in state['tasks'].items() if task['state'] in ('pending', 'running')]
    return {'run': state['run'], 'phase': state['phase'], 'sourceAuthority': state['sourceAuthority'],
            'max_parallel_specialists': 3, 'tasks': actions,
            'blocked_tasks': [key for key, task in state['tasks'].items() if task.get('verdict') in ('blocked', 'uncertain', 'fail')], 'edit_hash': state.get('edit', {}).get('hash'),
            'delivery': state['delivered'], 'premiere_writer': state['producer_id'],
            'note': 'Local ledger only; agents execute T3/Premiere calls and verify actual evidence.'}


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    q = sub.add_parser('start'); q.add_argument('--manifest', required=True)
    for name in ('status',):
        q = sub.add_parser(name); q.add_argument('--run', required=True)
    for name in ('bind', 'collect'):
        q = sub.add_parser(name); q.add_argument('--run', required=True); q.add_argument('--task', required=True); q.add_argument('--result', required=True)
    q = sub.add_parser('record-edit'); q.add_argument('--run', required=True); q.add_argument('--record', required=True)
    q = sub.add_parser('approve-export'); q.add_argument('--run', required=True); q.add_argument('--edit-hash', required=True); q.add_argument('--evidence-ref', required=True)
    for name in ('render-started', 'verify-render'):
        q = sub.add_parser(name); q.add_argument('--run', required=True); q.add_argument('--receipt', required=True)
    for name in ('claim-writer', 'release-writer'):
        q = sub.add_parser(name); q.add_argument('--run', required=True); q.add_argument('--caller-id', required=True)
    q = sub.add_parser('begin-operation'); q.add_argument('--run', required=True); q.add_argument('--caller-id', required=True); q.add_argument('--intent', required=True)
    q = sub.add_parser('resolve-operation'); q.add_argument('--run', required=True); q.add_argument('--caller-id', required=True); q.add_argument('--operation', required=True); q.add_argument('--receipt'); q.add_argument('--snapshot'); q.add_argument('--outcome', choices=('verified', 'no_effect', 'unknown'), required=True)
    q = sub.add_parser('reconcile-render-failure'); q.add_argument('--run', required=True); q.add_argument('--caller-id', required=True); q.add_argument('--evidence', required=True)
    q = sub.add_parser('rereview'); q.add_argument('--run', required=True); q.add_argument('--task', required=True); q.add_argument('--evidence', required=True)
    a = p.parse_args()
    try:
        if a.command == 'start': result = start(a.manifest)
        elif a.command == 'status':
            with locked(a.run):
                state = load_state(a.run)
                if state.get('edit'): active_edit(state)
                if state.get('delivered'): unchanged([state['delivered']['media'], state['delivered']['technical']])
                result = status(state)
        elif a.command == 'bind': result = bind(a.run, a.task, a.result)
        elif a.command == 'collect': result = collect(a.run, a.task, a.result)
        elif a.command == 'record-edit': result = record_edit(a.run, a.record)
        elif a.command == 'approve-export': result = approve_export(a.run, a.edit_hash, a.evidence_ref)
        elif a.command == 'render-started': result = render_started(a.run, a.receipt)
        elif a.command == 'verify-render': result = verify_render(a.run, a.receipt)
        elif a.command in ('claim-writer', 'release-writer'): result = writer_command(a.run, a.command, a.caller_id)
        elif a.command == 'begin-operation': result = writer_command(a.run, a.command, a.caller_id, intent=a.intent)
        elif a.command == 'resolve-operation': result = writer_command(a.run, a.command, a.caller_id, operation=a.operation, receipt=a.receipt, snapshot=a.snapshot, outcome=a.outcome)
        elif a.command == 'reconcile-render-failure': result = reconcile_render_failure(a.run, a.evidence, a.caller_id)
        else: result = rereview(a.run, a.task, a.evidence)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as error:
        p.exit(1, 'Blocked (' + type(error).__name__ + '): ' + str(error) + '\n')


if __name__ == '__main__': main()
