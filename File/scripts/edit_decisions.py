"""Offline edit-decision contract v1 (Python 3.9+, standard library).

validate(plan, sources) returns a JSON-safe normalized plan/coverage summary or
raises ValueError. It never edits files, probes media, or contacts a host.

sources is an insertion-ordered mapping: primary source order IS dialogue order.
Each source has media:{path,sha256}, duration_seconds:decimal-string, and
role:primary|broll|reference. Primary sources additionally have
transcript:{path,sha256,revision}. Supply every primary source in the intended
dialogue; each has a non-omittable ending. B-roll means non-dialogue footage;
reference cannot be used.
Extra source metadata is ignored. Paths resolve inside agentic_pipeline.ROOT.

Transcript JSON: {source_id,media_sha256,revision,mode,words,ending_word_ids}.
mode is supplied_script|verified_recording and must equal the plan mode.
words are chronological nonoverlapping {id,text,start,end,required?:bool}; IDs
are source-local occurrences, NEVER phrase text. Times are exact rational strings.
required defaults true; supplied_script forbids false. ending_word_ids is a
nonempty suffix of the required occurrence IDs and cannot be omitted. Optional
recording words still need an approved omission; optional does not mean disposable.
The caller supplies authoritative, complete transcript snapshots, not ASR guesses.

Plan JSON (all listed keys required; unknown plan/range/omission keys rejected):
{version:1, mode, frame_rate:"30000/1001", transcripts:{source_id:descriptor},
 ranges:[{source_id,source_sha256,sourceIn,sourceOut,timelineIn,timelineOut,
          reason,linked_av:true,word_ids:[...] }],
 omissions:[{source_id,word_ids:[...],kind,reason,evidence:{path,sha256}}]}.
transcripts must exactly bind every primary source's descriptor. Interval times
are nonnegative rational strings in seconds (decimals allowed, floats forbidden).
Ranges are half-open and normal speed. No frame rounding/alignment is imposed.
Each primary range lists exactly the complete words it intersects, in order;
cutting through words, replaying occurrences, and changing dialogue order fail.
B-roll can overlap primary ranges and uses word_ids:[]; primary cannot overlap.

Omissions are recording-only, kind retake|false_start|filler. Evidence is a local
fingerprinted JSON approval with source_id,media_sha256,transcript_sha256,
transcript_revision,word_ids,kind,reason matching the omission and snapshot, plus
approved:true,approved_by:<nonblank>,approval_id:<nonblank>. reason must describe
the specific omission (a bare category is insufficient). Every omitted word,
including required words, needs exactly one such approval. Ending words never do.

Fingerprints use agentic_pipeline; transcript/evidence JSON is read between hash
checks. Approval authenticity, transcription accuracy, semantic equivalence,
listening, gestures, lip sync, pacing and export readiness are NOT established.
Returned rational values are canonical Fraction strings, never binary floats.
"""

import copy
import json
import re
from fractions import Fraction

import agentic_pipeline as ap


class ValidationError(ValueError):
    """Invalid or stale local edit evidence."""


def _need(condition, message):
    if not condition:
        raise ValidationError(message)


def _text(value, label):
    _need(isinstance(value, str) and bool(value.strip()), label + ' must be nonblank text')
    return value


def _keys(value, keys, label):
    _need(isinstance(value, dict) and set(value) == set(keys.split()),
          label + ' has missing or unknown fields')


def _time(value, label, decimal=False):
    pattern = r'\d+(?:\.\d+)?' if decimal else r'\d+(?:/\d+|\.\d+)?'
    _need(isinstance(value, str) and re.fullmatch(pattern, value) is not None,
          label + ' must be a nonnegative exact numeric string')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(label + ' is invalid') from exc


def _ids(value, label, nonempty=False):
    _need(isinstance(value, list), label + ' must be an occurrence-ID list')
    for item in value:
        _text(item, label)
    _need(len(value) == len(set(value)), label + ' contains duplicate occurrences')
    _need(not nonempty or bool(value), label + ' cannot be empty')
    return value


def _fingerprint(descriptor):
    _need(isinstance(descriptor, dict), 'fingerprint must be an object')
    path = _text(descriptor.get('path'), 'fingerprint path')
    sha = descriptor.get('sha256')
    _need(isinstance(sha, str) and re.fullmatch(r'[0-9a-f]{64}', sha),
          'sha256 must be 64 lowercase hex characters')
    actual = ap.fingerprint(path)
    _need(actual['sha256'] == sha, 'stale fingerprint: ' + path)
    return actual


def _json(descriptor):
    before = _fingerprint(descriptor)
    value = json.loads(ap.local(before['path']).read_text(encoding='utf-8'))
    _need(ap.fingerprint(before['path']) == before, 'file changed during validation')
    _need(isinstance(value, dict), 'local JSON truth must be an object')
    return value


def validate(plan, sources):
    """Validate the v1 contract above; raise ValueError on invalid/stale input."""
    try:
        return _validate(plan, sources)
    except ValidationError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ValidationError('invalid edit evidence: ' + str(exc)) from exc


def _validate(plan, sources):
    _keys(plan, 'version mode frame_rate transcripts ranges omissions', 'plan')
    _need(type(plan['version']) is int and plan['version'] == 1, 'unsupported version')
    _need(plan['mode'] in ('supplied_script', 'verified_recording'), 'invalid mode')
    fps = _time(plan['frame_rate'], 'frame_rate')
    _need(fps > 0, 'frame_rate must be positive')
    _need(isinstance(sources, dict) and bool(sources), 'sources must be a nonempty mapping')
    _need(isinstance(plan['transcripts'], dict), 'transcripts must be a mapping')
    _need(isinstance(plan['ranges'], list) and bool(plan['ranges']), 'ranges must be nonempty')
    _need(isinstance(plan['omissions'], list), 'omissions must be a list')
    normalized = copy.deepcopy(plan)
    normalized['frame_rate'] = str(fps)
    durations, truth, snapshots, endings = {}, {}, {}, set()
    media_hashes = {}
    expected = []
    for sid, source in sources.items():
        _text(sid, 'source_id')
        _need(isinstance(source, dict), 'source must be an object')
        _need(source.get('role') in ('primary', 'broll', 'reference'), 'invalid source role')
        media_hashes[sid] = _fingerprint(source['media'])['sha256']
        duration = _time(source['duration_seconds'], 'duration_seconds', decimal=True)
        _need(duration > 0, 'duration_seconds must be positive')
        durations[sid] = duration
        if source['role'] != 'primary':
            continue
        descriptor = source['transcript']
        _keys(descriptor, 'path sha256 revision', 'transcript descriptor')
        _text(descriptor['revision'], 'transcript revision')
        _need(plan['transcripts'].get(sid) == descriptor, 'stale transcript binding: ' + sid)
        data = _json(descriptor)
        _need(data.get('source_id') == sid and data.get('media_sha256') == media_hashes[sid],
              'transcript source/media mismatch: ' + sid)
        _need(data.get('revision') == descriptor['revision'], 'stale transcript revision: ' + sid)
        _need(data.get('mode') == plan['mode'], 'transcript mode mismatch: ' + sid)
        words = data.get('words')
        _need(isinstance(words, list) and bool(words), 'primary transcript words must be nonempty')
        previous, seen, parsed, required = Fraction(0), set(), [], []
        for word in words:
            _need(isinstance(word, dict), 'word must be an object')
            wid = _text(word.get('id'), 'word occurrence id')
            _need(wid not in seen, 'duplicate transcript occurrence: ' + wid)
            seen.add(wid)
            _text(word.get('text'), 'word text')
            start, end = _time(word.get('start'), 'word start'), _time(word.get('end'), 'word end')
            _need(previous <= start < end <= duration, 'word timing/order out of bounds: ' + wid)
            previous = end
            is_required = word.get('required', True)
            _need(type(is_required) is bool, 'required must be boolean')
            _need(plan['mode'] != 'supplied_script' or is_required, 'script words must be required')
            if is_required:
                required.append(wid)
            parsed.append((wid, start, end))
            expected.append((sid, wid))
        ending = _ids(data.get('ending_word_ids'), 'ending_word_ids', nonempty=True)
        _need(required[-len(ending):] == ending, 'ending must be a suffix of required words')
        endings.update((sid, wid) for wid in ending)
        truth[sid], snapshots[sid] = parsed, descriptor
    _need(bool(truth), 'at least one primary transcript is required')
    _need(set(plan['transcripts']) == set(truth), 'transcripts must bind exactly all primary sources')

    primary, retained, covered = [], [], set()
    for index, item in enumerate(plan['ranges']):
        _keys(item, 'source_id source_sha256 sourceIn sourceOut timelineIn timelineOut reason linked_av word_ids',
              'range')
        sid = _text(item['source_id'], 'range source_id')
        _need(sid in sources, 'unknown range source: ' + sid)
        role = sources[sid]['role']
        _need(role != 'reference', 'reference-only source cannot be included')
        _need(item['source_sha256'] == media_hashes[sid], 'stale range source hash')
        _need(item['linked_av'] is True, 'linked_av must be true')
        _text(item['reason'], 'range reason')
        a, b, c, d = [_time(item[k], k) for k in ('sourceIn', 'sourceOut', 'timelineIn', 'timelineOut')]
        _need(a < b <= durations[sid] and c < d, 'range out of bounds or empty')
        _need(b - a == d - c, 'source/timeline duration mismatch; normal speed required')
        for key, val in zip(('sourceIn', 'sourceOut', 'timelineIn', 'timelineOut'), (a, b, c, d)):
            normalized['ranges'][index][key] = str(val)
        claimed = _ids(item['word_ids'], 'range word_ids')
        actual = []
        for wid, start, end in truth.get(sid, []):
            if start < b and a < end:
                _need(a <= start and end <= b, 'range truncates word occurrence: ' + wid)
                actual.append(wid)
        _need(claimed == actual, 'range word_ids do not match timed occurrences')
        if role == 'primary':
            primary.append((c, d, sid, actual))
    previous = Fraction(0)
    for start, end, sid, ids in sorted(primary, key=lambda row: row[0]):
        _need(start >= previous, 'overlapping primary timeline intervals')
        previous = end
        for wid in ids:
            key = (sid, wid)
            _need(key not in covered, 'replayed word occurrence: ' + wid)
            covered.add(key)
            retained.append(key)
    _need(endings <= covered, 'missing required ending word occurrences')

    omitted = set()
    all_words = set(expected)
    for omission in plan['omissions']:
        _keys(omission, 'source_id word_ids kind reason evidence', 'omission')
        _need(plan['mode'] == 'verified_recording', 'supplied-script words cannot be omitted')
        sid = _text(omission['source_id'], 'omission source_id')
        _need(sid in truth, 'omission requires a primary source')
        ids = _ids(omission['word_ids'], 'omission word_ids', nonempty=True)
        _need(omission['kind'] in ('retake', 'false_start', 'filler'), 'substantive omission is forbidden')
        reason = _text(omission['reason'], 'omission reason')
        _need(len(reason.split()) >= 3 and reason.strip().lower() not in
              ('remove this word', 'remove these words'), 'omission reason must be concrete')
        keys = {(sid, wid) for wid in ids}
        _need(keys <= all_words and not keys & (covered | omitted | endings),
              'unknown, retained, duplicate or ending omission occurrence')
        _need(ids == [wid for source_id, wid in expected if source_id == sid and (sid, wid) in keys],
              'omission IDs must follow transcript order')
        _keys(omission['evidence'], 'path sha256', 'omission evidence')
        evidence = _json(omission['evidence'])
        binding = {'source_id': sid, 'media_sha256': media_hashes[sid],
                   'transcript_sha256': snapshots[sid]['sha256'],
                   'transcript_revision': snapshots[sid]['revision'],
                   'word_ids': ids, 'kind': omission['kind'], 'reason': reason}
        _need(all(evidence.get(k) == v for k, v in binding.items()), 'omission evidence binding mismatch')
        _need(evidence.get('approved') is True, 'omission lacks explicit approval')
        _text(evidence.get('approved_by'), 'approved_by')
        _text(evidence.get('approval_id'), 'approval_id')
        omitted.update(keys)
    _need(covered | omitted == all_words, 'missing word occurrences without approved omission evidence')
    _need(retained == [key for key in expected if key not in omitted], 'dialogue occurrence order changed')
    return {'status': 'structurally_valid', 'plan': normalized,
            'retained_word_count': len(covered), 'omitted_word_count': len(omitted),
            'duration_seconds': str(max(_time(r['timelineOut'], 'timelineOut') for r in plan['ranges'])),
            'audiovisual_review_verified': False, 'semantic_truth_verified': False,
            'final_export_approved': False}
