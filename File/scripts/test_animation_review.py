"""Synthetic report/probe tests; no actual audiovisual quality claims."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import animation_review as review


class AnimationReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = patch.object(ap, 'ROOT', Path(self.temp.name).resolve()); root.start(); self.addCleanup(root.stop)
        for name, content in [('source.txt', 'The ball settles. Hello.'), ('board.png', 'reference'),
                              ('voice.wav', 'reference'), ('clip.mp4', 'media')]:
            (ap.ROOT / name).write_text(content)
        self.job = {'version': 1, 'mode': 'animation', 'producer_id': 'parent', 'shot_id': 'shot-1',
                    'source': 'source.txt', 'source_span': 'The ball settles. Hello.', 'action': 'Ball settles',
                    'start_state': 'Ball rolling', 'end_state': 'Ball settled', 'references': ['board.png'],
                    'protected_beats': ['Settled pose hold'], 'audio_mode': 'silent', 'media_origin': 'generated'}
        self.info = {'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}], 'format': {'duration': '3'}}
        probe = patch.object(ap, 'probe', side_effect=lambda _: self.info); probe.start(); self.addCleanup(probe.stop)
        self.completion = {'status': 'completed', 'taskId': 'task-1', 'childThreadId': 'reviewer'}

    def setup_packet(self):
        (ap.ROOT / 'job.json').write_text(json.dumps(self.job))
        packet = review.packet('job.json', 'clip.mp4')
        report = {'packet_hash': packet['packet_hash'], 'reviewer_id': 'reviewer', 'delegation_id': 'task-1',
                  'checks': {k: {'status': 'pass', 'method': 'direct_av', 'coverage': 'full_clip',
                                 'evidence': 'Synthetic fixture attestation'} for k in packet['checks']}}
        return packet, report

    def test_silent_object_animation_needs_no_fake_dialogue_or_hands(self):
        p, r = self.setup_packet()
        self.assertNotIn('lip_sync', p['checks']); self.assertNotIn('hand_framing', p['checks'])
        self.assertEqual(review.gate(p, r, self.completion)['status'], 'ready_for_edit')

    def test_generated_1080_rejected_supplied_1080_preserved(self):
        self.info['streams'][0].update(width=1920, height=1080)
        p, r = self.setup_packet()
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)
        self.job['media_origin'] = 'supplied'; p, r = self.setup_packet()
        self.assertEqual(review.gate(p, r, self.completion)['status'], 'ready_for_edit')

    def test_dialogue_requires_exact_speech_voice_and_sync(self):
        self.job.update(audio_mode='dialogue', speech='Hello.', speaker='Ball', voice_reference='voice.wav', sound_plan='Only the exact line')
        p, r = self.setup_packet(); self.assertIn('lip_sync', p['checks'])
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)
        self.info['streams'].append({'codec_type': 'audio'})
        self.assertEqual(review.gate(p, r, self.completion)['status'], 'ready_for_edit')
        r['checks']['lip_sync']['method'] = 'direct_audio'
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)
        self.job['speech'] = 'invented dialogue'
        with self.assertRaises(ValueError): self.setup_packet()

    def test_silent_audio_stream_requires_listening(self):
        self.info['streams'].append({'codec_type': 'audio'})
        p, r = self.setup_packet()
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)
        r['silent_audio_evidence'] = {'status': 'pass', 'method': 'direct_audio', 'coverage': 'full_clip', 'evidence': 'Listened: silent fixture'}
        self.assertEqual(review.gate(p, r, self.completion)['status'], 'ready_for_edit')

    def test_stale_reference_invalidates_packet(self):
        p, r = self.setup_packet(); (ap.ROOT/'board.png').write_text('changed')
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)

    def test_independent_actual_completed_task_required(self):
        p, r = self.setup_packet()
        for patch_fields in ({'status': 'running'}, {'childThreadId': 'parent'}, {'taskId': 'other'}, {'hasPendingChildRuns': True}):
            with self.subTest(patch_fields=patch_fields), self.assertRaises(ValueError):
                review.gate(p, r, dict(self.completion, **patch_fields))

    def test_sampled_frames_and_partial_coverage_cannot_pass(self):
        p, r = self.setup_packet()
        for change in ({'method': 'sampled_stills'}, {'coverage': 'partial'}, {'method': 'direct_audio'}):
            altered = copy.deepcopy(r); altered['checks']['motion_integrity'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): review.gate(p, altered, self.completion)

    def test_uncertain_and_fail_stay_out_of_edit(self):
        p, r = self.setup_packet()
        for status, expected in [('uncertain', 'needs_evidence'), ('fail', 'rejected')]:
            r['checks']['staging_contact']['status'] = status
            result = review.gate(p, r, self.completion)
            self.assertEqual(result['status'], expected); self.assertFalse(result['assembled_review_complete'])

    def test_narration_has_no_lip_sync_requirement(self):
        self.job.update(audio_mode='narration', speech='Hello.', speaker='Narrator', voice_reference='voice.wav', sound_plan='Narrator line')
        p, _ = self.setup_packet(); self.assertNotIn('lip_sync', p['checks'])

    def test_packet_cannot_drop_required_checks(self):
        p, r = self.setup_packet(); p['checks'].remove('camera_locked')
        p.pop('packet_hash'); p['packet_hash'] = ap.digest(p)
        r['packet_hash'] = p['packet_hash']; r['checks'].pop('camera_locked')
        with self.assertRaises(ValueError): review.gate(p, r, self.completion)


if __name__ == '__main__': unittest.main()
