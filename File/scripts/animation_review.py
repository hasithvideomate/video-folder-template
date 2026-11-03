#!/usr/bin/env python3
"""Offline animation shot review packets. Agents execute generation and delegation."""
import argparse
import json
import math

import agentic_pipeline as ap

VISUAL = ('story_action', 'design_continuity', 'motion_integrity', 'staging_contact',
          'protected_holds_ending', 'camera_locked', 'background_stationary', 'no_added_text')
AUDIO = ('sound_matches_plan',)
SPEECH = ('exact_words_speaker_ending', 'voice_matches_reference')


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Nonempty text required')
    return value


def specification(job):
    """No fabricated speech/hand requirements for silent or nonhuman animation."""
    if job.get('version') != 1 or job.get('mode') != 'animation':
        raise ValueError('Expected version 1 animation job')
    for key in ('producer_id', 'shot_id', 'source', 'source_span', 'action', 'start_state', 'end_state'):
        text(job.get(key))
    if job.get('media_origin') not in ('generated', 'supplied'):
        raise ValueError('Declare generated or supplied media origin')
    if job['source_span'] not in ap.local(job['source']).read_text(encoding='utf-8'):
        raise ValueError('Story action must identify an exact source span')
    if not isinstance(job.get('references'), list) or not job['references']:
        raise ValueError('Selected design/board references required')
    for path in job['references']: ap.fingerprint(text(path))
    if not isinstance(job.get('protected_beats'), list):
        raise ValueError('List protected action/reaction/hold beats, even when empty')
    for beat in job['protected_beats']: text(beat)
    mode = job.get('audio_mode')
    if mode not in ('silent', 'sfx', 'narration', 'dialogue'):
        raise ValueError('Choose silent, sfx, narration or dialogue')
    checks = list(VISUAL)
    if mode != 'silent':
        text(job.get('sound_plan')); checks += list(AUDIO)
    if mode in ('narration', 'dialogue'):
        speech = text(job.get('speech')); text(job.get('speaker'))
        if speech not in job['source_span']:
            raise ValueError('Speech must match the exact source span')
        ap.fingerprint(text(job.get('voice_reference')))
        checks += list(SPEECH)
        if mode == 'dialogue': checks += ['lip_sync']
    elif job.get('speech') or job.get('voice_reference'):
        raise ValueError('Non-speech mode cannot hide a speech requirement')
    return checks


def packet(job_path, media_path):
    job = ap.load(job_path); checks = specification(job)
    inputs = [ap.fingerprint(job_path), ap.fingerprint(job['source'])]
    inputs.extend(ap.fingerprint(p) for p in job['references'])
    if job.get('voice_reference'): inputs.append(ap.fingerprint(job['voice_reference']))
    result = {'version': 1, 'mode': 'animation', 'producer_id': job['producer_id'],
              'inputs': inputs, 'media': ap.fingerprint(media_path), 'shot': job,
              'checks': checks, 'review_scope': 'one_shot_only'}
    result['packet_hash'] = ap.digest(result)
    return result


def gate(p, report, completion):
    ap.validate_packet(p)
    job = ap.load(p['inputs'][0]['path']); checks = specification(job)
    if p != packet(p['inputs'][0]['path'], p['media']['path']):
        raise ValueError('Packet does not match the current animation job')
    result = completion.get('structuredContent', completion)
    if (result.get('status') != 'completed' or result.get('hasPendingChildRuns')
            or result.get('hasPendingQuestion') or result.get('pendingApproval')):
        raise ValueError('Actual delegated review must be fully completed')
    reviewer = text(result.get('childThreadId')); task_id = text(result.get('taskId'))
    if (reviewer == job['producer_id'] or report.get('reviewer_id') != reviewer
            or report.get('delegation_id') != task_id or report.get('packet_hash') != p['packet_hash']):
        raise ValueError('Independent task/report identity mismatch')
    if set(report.get('checks', {})) != set(checks):
        raise ValueError('Every mode-specific check is required')
    for name, check in report['checks'].items():
        if check.get('status') not in ('pass', 'fail', 'uncertain'):
            raise ValueError('Invalid review status')
        text(check.get('evidence')); text(check.get('method'))
        allowed = {'direct_video', 'direct_av'} if name in VISUAL else {'direct_audio', 'direct_av'}
        if name == 'lip_sync' or name == 'sound_matches_plan': allowed = {'direct_av'}
        if check['status'] == 'pass' and (check.get('coverage') != 'full_clip' or check['method'] not in allowed):
            raise ValueError('Passing animation review requires full temporal evidence in the proper modality')
    states = [c['status'] for c in report['checks'].values()]
    verdict = 'rejected' if 'fail' in states else 'needs_evidence' if 'uncertain' in states else 'ready_for_edit'
    if verdict == 'ready_for_edit':
        info = ap.probe(p['media']['path'])
        video = [s for s in info['streams'] if s.get('codec_type') == 'video'
                 and not s.get('disposition', {}).get('attached_pic')]
        audio = [s for s in info['streams'] if s.get('codec_type') == 'audio']
        duration = float(info.get('format', {}).get('duration', 0))
        if len(video) != 1 or not math.isfinite(duration) or duration <= 0:
            raise ValueError('Actual animation needs one usable video stream and positive duration')
        if job['media_origin'] == 'generated' and min(video[0].get('width', 0), video[0].get('height', 0)) != 720:
            raise ValueError('Generated animation must be 720p')
        if job['audio_mode'] != 'silent' and not audio:
            raise ValueError('Required sound is absent')
        # A purportedly silent take with audio needs listening evidence, even if it may be a silent track.
        if job['audio_mode'] == 'silent' and audio:
            check = report.get('silent_audio_evidence', {})
            if (check.get('status') != 'pass' or check.get('method') not in ('direct_audio', 'direct_av')
                    or check.get('coverage') != 'full_clip' or not check.get('evidence')):
                raise ValueError('Listen to the actual audio stream to establish silence')
    return {'status': verdict, 'packet_hash': p['packet_hash'], 'shot_id': job['shot_id'],
            'assembled_review_complete': False, 'final_export_approved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    q = commands.add_parser('packet'); q.add_argument('--job', required=True); q.add_argument('--media', required=True); q.add_argument('--out', required=True)
    q = commands.add_parser('gate'); q.add_argument('--packet', required=True); q.add_argument('--report', required=True); q.add_argument('--completion', required=True)
    args = parser.parse_args()
    if args.command == 'packet':
        result = packet(args.job, args.media); ap.write(args.out, result)
    else: result = gate(ap.load(args.packet), ap.load(args.report), ap.load(args.completion))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get('status') in ('needs_evidence', 'rejected'): raise SystemExit(2)


if __name__ == '__main__': main()
