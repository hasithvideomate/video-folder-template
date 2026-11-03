"""Synthetic structural tests; fixture bytes are not audiovisual evidence."""
import copy
import json
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import edit_decisions as ed


class EditDecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        mock = patch.object(ap, 'ROOT', self.root)
        mock.start()
        self.addCleanup(mock.stop)
        (self.root / 'source.mov').write_bytes(b'synthetic media fixture')
        self.media = ap.fingerprint('source.mov')
        self.transcript = {
            'source_id': 'a', 'media_sha256': self.media['sha256'],
            'revision': 'r1', 'mode': 'supplied_script',
            'words': [
                {'id': 'w1', 'text': 'Hello', 'start': '0', 'end': '1/2'},
                {'id': 'w2', 'text': 'Hello', 'start': '1', 'end': '3/2'},
                {'id': 'w3', 'text': 'goodbye.', 'start': '2', 'end': '5/2'}],
            'ending_word_ids': ['w3']}
        self.sources = {'a': {'media': self.media, 'duration_seconds': '3.0',
                              'role': 'primary'}}
        self.plan = {'version': 1, 'mode': 'supplied_script', 'frame_rate': '30000/1001',
                     'transcripts': {}, 'ranges': [self.span('0', '3', '0', ['w1', 'w2', 'w3'])],
                     'omissions': []}
        self.save_transcript()

    def span(self, start, end, timeline, ids, sid='a'):
        return {'source_id': sid, 'source_sha256': self.media['sha256'],
                'sourceIn': start, 'sourceOut': end, 'timelineIn': timeline,
                'timelineOut': str(Fraction(timeline) + Fraction(end) - Fraction(start)),
                'word_ids': ids, 'reason': 'Retain exact spoken occurrences', 'linked_av': True}

    def save_json(self, path, value):
        (self.root / path).write_text(json.dumps(value), encoding='utf-8')
        return ap.fingerprint(path)

    def save_transcript(self):
        descriptor = dict(self.save_json('transcript.json', self.transcript),
                          revision=self.transcript['revision'])
        self.sources['a']['transcript'] = descriptor
        self.plan['transcripts']['a'] = copy.deepcopy(descriptor)

    def reject(self, message):
        with self.assertRaisesRegex(ed.ValidationError, message):
            ed.validate(self.plan, self.sources)

    def recording_omission(self):
        self.transcript['mode'] = self.plan['mode'] = 'verified_recording'
        self.save_transcript()
        self.plan['ranges'] = [self.span('1', '3', '0', ['w2', 'w3'])]
        omission = {'source_id': 'a', 'word_ids': ['w1'], 'kind': 'retake',
                    'reason': 'First Hello is the abandoned take before the complete second greeting'}
        evidence = dict(omission, media_sha256=self.media['sha256'],
                        transcript_sha256=self.sources['a']['transcript']['sha256'],
                        transcript_revision='r1', approved=True,
                        approved_by='fixture reviewer', approval_id='fixture approval')
        omission['evidence'] = self.save_json('approval.json', evidence)
        self.plan['omissions'] = [omission]
        return evidence

    def test_normalization_is_exact_and_inputs_unchanged(self):
        before = copy.deepcopy((self.plan, self.sources))
        self.plan['ranges'][0]['sourceOut'] = '6/2'
        expected_input = copy.deepcopy(self.plan)
        result = ed.validate(self.plan, self.sources)
        self.assertEqual(result['plan']['frame_rate'], '30000/1001')
        self.assertEqual(result['plan']['ranges'][0]['sourceOut'], '3')
        self.assertEqual(result['retained_word_count'], 3)
        self.assertFalse(result['audiovisual_review_verified'])
        self.assertFalse(result['semantic_truth_verified'])
        self.assertFalse(result['final_export_approved'])
        self.assertEqual(self.plan, expected_input)
        self.assertEqual(self.sources, before[1])
        json.dumps(result, allow_nan=False)

    def test_decimal_rate_is_not_coerced_to_integer(self):
        self.plan['frame_rate'] = '29.97'
        self.assertEqual(ed.validate(self.plan, self.sources)['plan']['frame_rate'], '2997/100')

    def test_exact_duration_rejects_tiny_speed_change(self):
        self.plan['ranges'][0]['timelineOut'] = '30000000000000001/10000000000000000'
        self.reject('duration mismatch')

    def test_invalid_times_and_rates(self):
        for field, value in [('frame_rate', '0'), ('frame_rate', '1/0'),
                             ('frame_rate', 29.97), ('frame_rate', 'NaN'),
                             ('sourceIn', '-1'), ('sourceIn', 0),
                             ('sourceOut', '4'), ('sourceOut', '0')]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.plan)
                target = self.plan if field == 'frame_rate' else self.plan['ranges'][0]
                target[field] = value
                self.reject('positive|invalid|numeric string|bounds')
                self.plan = original

    def test_trimmed_silence_and_touching_primary_ranges(self):
        self.plan['ranges'] = [self.span('0', '1/2', '0', ['w1']),
                               self.span('1', '3/2', '1/2', ['w2']),
                               self.span('2', '5/2', '1', ['w3'])]
        self.assertEqual(ed.validate(self.plan, self.sources)['duration_seconds'], '3/2')

    def test_overlap_rejected(self):
        self.plan['ranges'].append(self.span('0', '1/2', '1', ['w1']))
        self.reject('overlapping primary')

    def test_replay_rejected_even_without_overlap(self):
        self.plan['ranges'].append(self.span('0', '1/2', '3', ['w1']))
        self.reject('replayed word')

    def test_occurrence_ids_disambiguate_repeated_text(self):
        self.plan['ranges'] = [self.span('0', '1/2', '0', ['w2']),
                               self.span('1', '3', '1/2', ['w1', 'w3'])]
        self.reject('timed occurrences')

    def test_phrase_text_is_not_occurrence_identity(self):
        self.plan['ranges'][0]['word_ids'] = ['Hello', 'Hello', 'goodbye.']
        self.reject('duplicate occurrences')

    def test_word_cut_cannot_hide_behind_matching_claim(self):
        self.plan['ranges'] = [self.span('1/4', '3', '0', ['w1', 'w2', 'w3'])]
        self.reject('truncates word')

    def test_reordered_dialogue_rejected(self):
        self.plan['ranges'] = [self.span('1', '3/2', '0', ['w2']),
                               self.span('0', '1/2', '1/2', ['w1']),
                               self.span('2', '3', '1', ['w3'])]
        self.reject('dialogue occurrence order')

    def test_missing_required_word(self):
        self.plan['ranges'] = [self.span('1', '3', '0', ['w2', 'w3'])]
        self.reject('missing word occurrences')

    def test_missing_ending(self):
        self.plan['ranges'] = [self.span('0', '2', '0', ['w1', 'w2'])]
        self.reject('missing required ending')

    def test_reference_inclusion_and_broll_overlay(self):
        self.sources['visual'] = {'role': 'broll', 'media': self.media, 'duration_seconds': '3'}
        self.plan['ranges'].append(self.span('0', '3', '0', [], 'visual'))
        self.assertEqual(ed.validate(self.plan, self.sources)['retained_word_count'], 3)
        self.sources['visual']['role'] = 'reference'
        self.reject('reference-only')

    def test_broll_cannot_claim_dialogue(self):
        self.sources['visual'] = {'role': 'broll', 'media': self.media, 'duration_seconds': '3'}
        self.plan['ranges'].append(self.span('0', '3', '0', ['w1'], 'visual'))
        self.reject('timed occurrences')

    def test_stale_media_transcript_and_range(self):
        for path in ('source.mov', 'transcript.json'):
            with self.subTest(path=path):
                original = (self.root / path).read_bytes()
                (self.root / path).write_bytes(original + b' ')
                self.reject('stale fingerprint')
                (self.root / path).write_bytes(original)
        self.plan['ranges'][0]['source_sha256'] = '0' * 64
        self.reject('stale range')

    def test_stale_revision_or_snapshot_binding(self):
        self.plan['transcripts']['a']['revision'] = 'r0'
        self.reject('stale transcript binding')
        self.sources['a']['transcript']['revision'] = 'r0'
        self.reject('stale transcript revision')

    def test_transcript_source_hash_and_mode_are_authoritative(self):
        for key, value in [('source_id', 'other'), ('media_sha256', '0' * 64),
                           ('mode', 'verified_recording')]:
            with self.subTest(key=key):
                before = self.transcript[key]
                self.transcript[key] = value
                self.save_transcript()
                self.reject('mismatch')
                self.transcript[key] = before

    def test_duplicate_and_invalid_word_truth(self):
        for field, value in [('id', 'w1'), ('start', '0'), ('end', '4'), ('required', 'yes')]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.transcript)
                self.transcript['words'][1][field] = value
                self.save_transcript()
                self.reject('duplicate|timing|boolean')
                self.transcript = original

    def test_script_cannot_mark_words_optional(self):
        self.transcript['words'][0]['required'] = False
        self.save_transcript()
        self.reject('script words must be required')

    def test_ending_contract_required(self):
        for value in ([], ['w1'], ['unknown']):
            with self.subTest(value=value):
                self.transcript['ending_word_ids'] = value
                self.save_transcript()
                self.reject('ending_word_ids|ending must')

    def test_approved_recording_retake(self):
        self.recording_omission()
        result = ed.validate(self.plan, self.sources)
        self.assertEqual((result['retained_word_count'], result['omitted_word_count']), (2, 1))

    def test_optional_recording_words_still_need_evidence(self):
        self.recording_omission()
        self.transcript['words'][0]['required'] = False
        self.save_transcript()
        self.plan['omissions'] = []
        self.reject('missing word occurrences')

    def test_script_omission_forbidden_even_with_approval(self):
        self.recording_omission()
        self.plan['mode'] = self.transcript['mode'] = 'supplied_script'
        self.save_transcript()
        self.reject('supplied-script words cannot be omitted')

    def test_omission_requires_bound_approval(self):
        evidence = self.recording_omission()
        for key, value in [('approved', False), ('approved_by', ''), ('approval_id', ''),
                           ('transcript_revision', 'r0'), ('transcript_sha256', '0' * 64),
                           ('word_ids', ['w2']), ('media_sha256', '0' * 64),
                           ('source_id', 'wrong'), ('reason', 'something else')]:
            with self.subTest(key=key):
                altered = dict(evidence, **{key: value})
                self.plan['omissions'][0]['evidence'] = self.save_json('approval.json', altered)
                self.reject('approval|approved_by|approval_id|binding mismatch')

    def test_stale_approval_file(self):
        self.recording_omission()
        (self.root / 'approval.json').write_text('{}')
        self.reject('stale fingerprint')

    def test_omission_kind_and_reason(self):
        self.recording_omission()
        self.plan['omissions'][0]['kind'] = 'substantive'
        self.reject('substantive omission')
        self.plan['omissions'][0]['kind'] = 'retake'
        self.plan['omissions'][0]['reason'] = 'retake'
        self.reject('reason must be concrete')

    def test_omission_cannot_cover_retained_or_unknown_or_duplicate(self):
        self.recording_omission()
        for ids in (['w2'], ['unknown'], ['w1', 'w1']):
            with self.subTest(ids=ids):
                self.plan['omissions'][0]['word_ids'] = ids
                self.reject('unknown, retained|duplicate occurrences')
        self.plan['omissions'][0]['word_ids'] = ['w1']
        self.plan['omissions'].append(copy.deepcopy(self.plan['omissions'][0]))
        self.reject('duplicate.*omission')

    def test_unknown_fields_and_unlinked_av_rejected(self):
        self.plan['ranges'][0]['speed'] = '2'
        self.reject('unknown fields')
        del self.plan['ranges'][0]['speed']
        self.plan['ranges'][0]['linked_av'] = 1
        self.reject('linked_av')

    def test_missing_or_escaped_local_truth(self):
        for path in ('missing.json', '../outside.json'):
            with self.subTest(path=path):
                self.sources['a']['transcript']['path'] = path
                self.plan['transcripts']['a']['path'] = path
                self.reject('invalid edit evidence')

    def test_all_primary_sources_need_binding_and_coverage(self):
        self.sources['b'] = copy.deepcopy(self.sources['a'])
        self.reject('stale transcript binding')
        data = dict(self.transcript, source_id='b')
        descriptor = dict(self.save_json('second.json', data), revision='r1')
        self.sources['b']['transcript'] = descriptor
        self.plan['transcripts']['b'] = copy.deepcopy(descriptor)
        self.reject('missing required ending')
        self.plan['ranges'].append(self.span('0', '3', '3', ['w1', 'w2', 'w3'], 'b'))
        self.assertEqual(ed.validate(self.plan, self.sources)['retained_word_count'], 6)
        self.plan['ranges'][0]['timelineIn'] = '3'
        self.plan['ranges'][0]['timelineOut'] = '6'
        self.plan['ranges'][1]['timelineIn'] = '0'
        self.plan['ranges'][1]['timelineOut'] = '3'
        self.reject('dialogue occurrence order')


if __name__ == '__main__':
    unittest.main()
