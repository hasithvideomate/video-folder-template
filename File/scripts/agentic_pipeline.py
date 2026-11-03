#!/usr/bin/env python3
"""Offline production packets and fail-closed review gate; Codex drives live tools."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RULES = ('Generate at 720p. Lock the camera, angle, framing and scale throughout: '
         'no zoom-in, zoom-out, pan, tilt, shake, digital punch-in, cuts or automatic reframing. '
         'Do not add captions, subtitles, speech text, titles, logos or text overlays. '
         'Keep the reference background stationary: no moving, drifting, morphing or animated '
         'walls, posters, furniture, equipment or screens; no parallax or flicker. '
         'Existing physical posters remain fixed scenery. Preserve natural articulation and '
         'phrase-matched gestures, with complete hands and fingertips inside the frame.')
CHECKS = ('resolution', 'wording', 'speech_complete', 'gesture_timing', 'hand_framing',
          'identity', 'voice_continuity', 'lip_sync', 'camera_locked', 'no_added_text',
          'background_stationary')
TEMPORAL = set(CHECKS) - {'resolution', 'identity'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def local(name):
    p = (ROOT / name).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Inputs must stay inside the project')
    return p


def fingerprint(name):
    p = local(name)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return {'path': str(p.relative_to(ROOT)), 'sha256': h.hexdigest()}


def load(name):
    return json.loads(local(name).read_text(encoding='utf-8'))


def write(name, data):
    p = local(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def field(obj, dotted):
    parts = dotted.split('.')
    for part in parts[:-1]:
        obj = obj[part]
    return obj, parts[-1]


def compile_job(job):
    """Explicit model field mapping avoids guessing provider schemas."""
    if not isinstance(job.get('producer_id'), str) or not job['producer_id'].strip():
        raise ValueError('A nonempty producer_id is required before generation')
    voice_mode = job.get('voice_mode', 'match_reference')
    if voice_mode not in ('match_reference', 'establish_baseline'):
        raise ValueError('Unsupported voice_mode')
    if voice_mode == 'match_reference' and not job.get('voice_reference'):
        raise ValueError('Voice matching requires a reference; explicitly select baseline mode for a permitted original voice')
    if voice_mode == 'establish_baseline' and job.get('voice_reference'):
        raise ValueError('A selected voice reference requires match_reference mode')
    if job.get('mode', 'talking_avatar') != 'talking_avatar':
        raise ValueError('This helper currently supports talking-avatar footage only')
    if job['resolution'] != '720p':
        raise ValueError('Only 720p is permitted')
    source = local(job['script']).read_text(encoding='utf-8')
    dialogue = job['dialogue']
    if not dialogue.strip() or dialogue not in source:
        raise ValueError('Dialogue must be an exact contiguous approved-source span')
    if not job['gestures'] or any(not g['cue'].strip() or not g['phrase'].strip()
                                 or g['phrase'] not in dialogue for g in job['gestures']):
        raise ValueError('Provide phrase-specific gesture cues from this dialogue')
    if not job['references']:
        raise ValueError('Selected visual reference is required')
    payload = json.loads(json.dumps(job['payload']))
    if set(payload) != {'model', 'input'} or not isinstance(payload['input'], dict):
        raise ValueError('Expected a Market model/input payload')
    if not job['prompt_field'].startswith('input.') or not job['resolution_field'].startswith('input.'):
        raise ValueError('Model fields must be under input')
    a, b = job['prompt_field'], job['resolution_field']
    if a == b or a.startswith(b + '.') or b.startswith(a + '.'):
        raise ValueError('Prompt and resolution fields must be distinct and non-overlapping')
    obj, key = field(payload, job['prompt_field'])
    # Free visual direction is retained; agent must resolve conflicting directions before preview.
    obj[key] = (job['visual_direction'] + '\n\n' + RULES + '\n\n'
                + 'Speak exactly this source text, without additions or omissions:\n' + dialogue
                + '\nPhrase-specific performance cues:\n'
                + '\n'.join(g['phrase'] + ': ' + g['cue'] for g in job['gestures']))
    obj, key = field(payload, job['resolution_field'])
    obj[key] = '720p'
    return payload


def packet(job_name, media_name):
    job = load(job_name)
    compile_job(job)
    inputs = [fingerprint(job_name), fingerprint(job['script'])]
    inputs += [fingerprint(p) for p in job['references']]
    if job.get('voice_reference'):
        inputs.append(fingerprint(job['voice_reference']))
    result = {'version': 1, 'inputs': inputs, 'media': fingerprint(media_name),
              'dialogue': job['dialogue'], 'gestures': job['gestures'], 'rules': RULES,
              'checks': list(CHECKS), 'producer_id': job['producer_id'],
              'voice_mode': job.get('voice_mode', 'match_reference')}
    result['packet_hash'] = digest(result)
    return result


def validate_packet(p):
    copy = dict(p)
    given = copy.pop('packet_hash')
    if digest(copy) != given:
        raise ValueError('Packet changed')
    for item in p['inputs'] + [p['media']]:
        if fingerprint(item['path']) != item:
            raise ValueError('Stale packet: source, reference, job or media changed')


def probe(name):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                              '-of', 'json', str(local(name))], timeout=60))


def verify_media(name):
    info = probe(name)
    video = [s for s in info['streams'] if s.get('codec_type') == 'video'
             and not s.get('disposition', {}).get('attached_pic')]
    audio = [s for s in info['streams'] if s.get('codec_type') == 'audio']
    if not video or not audio or float(info['format'].get('duration', 0)) <= 0:
        raise ValueError('Talking-video review requires usable video, audio and positive duration')
    if any(min(s.get('width', 0), s.get('height', 0)) != 720 for s in video):
        raise ValueError('Actual media must be 720p')
    return info


def gate(p, report):
    validate_packet(p)
    if report['packet_hash'] != p['packet_hash']:
        raise ValueError('Review belongs to a different packet')
    if not report.get('reviewer_id') or report['reviewer_id'] == p['producer_id']:
        raise ValueError('Independent reviewer identity is required')
    if not report.get('delegation_id'):
        raise ValueError('Record actual child task/agent ID')
    job = load(p['inputs'][0]['path'])
    voice = fingerprint(job['voice_reference']) if job.get('voice_reference') else None
    has_voice_reference = voice is not None and voice in p['inputs']
    results = report['checks']
    if set(results) != set(CHECKS):
        raise ValueError('Every required check must be present')
    for name, check in results.items():
        if check['status'] not in ('pass', 'fail', 'uncertain'):
            raise ValueError('Invalid review status')
        if not check.get('evidence') or not check.get('method'):
            raise ValueError('Every check needs evidence or an explicit unavailable reason')
        if check['status'] == 'pass':
            if name == 'resolution' and check['method'] != 'ffprobe':
                raise ValueError('Resolution requires ffprobe evidence')
            if name == 'voice_continuity' and not has_voice_reference:
                if p.get('voice_mode') != 'establish_baseline' or check.get('baseline_established') is not True:
                    raise ValueError('Voice continuity requires a reference or explicit first-take baseline mode')
            if name in TEMPORAL and check.get('coverage') != 'full_clip':
                raise ValueError('Temporal passes require full-clip coverage')
            if name in TEMPORAL and check['method'] not in ('direct_av', 'direct_video', 'direct_audio'):
                raise ValueError('ASR and sampled stills alone cannot pass temporal checks')
            if name in ('wording', 'speech_complete', 'voice_continuity') and check['method'] not in ('direct_audio', 'direct_av'):
                raise ValueError('Audio checks require listening')
            if name in ('gesture_timing', 'lip_sync') and check['method'] != 'direct_av':
                raise ValueError('Synchronized audiovisual evidence required')
            if name in ('hand_framing', 'camera_locked', 'no_added_text', 'background_stationary') and check['method'] not in ('direct_video', 'direct_av'):
                raise ValueError('Visual checks require temporal visual evidence')
    statuses = [c['status'] for c in results.values()]
    if all(status == 'pass' for status in statuses):
        verify_media(p['media']['path'])
    return {'status': 'rejected' if 'fail' in statuses else 'needs_evidence' if 'uncertain' in statuses else 'ready_for_edit',
            'packet_hash': p['packet_hash'], 'final_export_approved': False}



def tool_health():
    result = {}
    for name in ('ffmpeg', 'ffprobe', 'whisper', 'whisper-cli', 'tesseract'):
        path = shutil.which(name)
        item = {'path': path, 'usable': None}
        if name in ('ffmpeg', 'ffprobe'):
            item['usable'] = False
            if path:
                try:
                    run = subprocess.run([path, '-version'], capture_output=True, timeout=10)
                    item['usable'] = run.returncode == 0
                    item['returncode'] = run.returncode
                except (OSError, subprocess.SubprocessError) as error:
                    item['errorType'] = type(error).__name__
        result[name] = item
    result['note'] = 'FFmpeg tools startup-tested; ASR/OCR presence only. No media quality checks or model downloads.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    c = sub.add_parser('compile'); c.add_argument('--job', required=True); c.add_argument('--out', required=True)
    c = sub.add_parser('packet'); c.add_argument('--job', required=True); c.add_argument('--media', required=True); c.add_argument('--out', required=True)
    c = sub.add_parser('gate'); c.add_argument('--packet', required=True); c.add_argument('--report', required=True)
    c = sub.add_parser('probe'); c.add_argument('--media', required=True)
    args = parser.parse_args()
    if args.command == 'doctor':
        result = tool_health()
    elif args.command == 'compile':
        result = compile_job(load(args.job)); write(args.out, result)
    elif args.command == 'packet':
        result = packet(args.job, args.media); write(args.out, result)
    elif args.command == 'gate':
        result = gate(load(args.packet), load(args.report))
    else:
        result = probe(args.media)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == 'gate' and result['status'] != 'ready_for_edit':
        sys.exit(2)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit('Blocked: ' + str(exc)) from None
