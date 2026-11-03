import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import agentic_pipeline as ap


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.mock = patch.object(ap, 'ROOT', self.root)
        self.mock.start()
        self.probe_mock = patch.object(ap, 'probe', return_value={'streams': [
            {'codec_type': 'video', 'width': 1280, 'height': 720}, {'codec_type': 'audio'}],
            'format': {'duration': '4'}})
        self.probe_mock.start()
        for name, text in [('source.txt', 'Hello there. Goodbye.'), ('ref.png', 'reference'), ('clip.mp4', 'test bytes, not media evidence')]:
            (self.root / name).write_text(text)
        self.job = {'producer_id': 'producer', 'voice_reference': 'ref.png', 'script': 'source.txt', 'references': ['ref.png'],
                    'dialogue': 'Hello there.', 'gestures': [{'phrase': 'Hello', 'cue': 'Open palm greeting'}],
                    'resolution': '720p', 'visual_direction': 'Natural presenter.',
                    'payload': {'model': 'offline-test', 'input': {}},
                    'prompt_field': 'input.prompt', 'resolution_field': 'input.resolution'}
        (self.root / 'job.json').write_text(json.dumps(self.job))
        self.packet = ap.packet('job.json', 'clip.mp4')
        self.report = {'packet_hash': self.packet['packet_hash'], 'reviewer_id': 'reviewer',
                       'delegation_id': 'child-task', 'checks': {k: {'status': 'pass', 'method': 'direct_av',
                       'coverage': 'full_clip', 'evidence': 'Synthetic test claim'} for k in ap.CHECKS}}

        self.report['checks']['resolution']['method'] = 'ffprobe'

    def tearDown(self):
        self.probe_mock.stop(); self.mock.stop(); self.temp.cleanup()

    def test_compile_preserves_dialogue_and_forces_settings(self):
        result = ap.compile_job(self.job)
        self.assertIn(self.job['dialogue'], result['input']['prompt'])
        self.assertEqual(result['input']['resolution'], '720p')
        self.assertNotIn('prompt', self.job['payload']['input'])

    def test_refuse_wrong_source_and_resolution(self):
        for key, value in [('dialogue', 'Invented speech'), ('resolution', '1080p')]:
            job = copy.deepcopy(self.job); job[key] = value
            with self.assertRaises(ValueError): ap.compile_job(job)

    def test_pass_is_edit_only(self):
        result = ap.gate(self.packet, self.report)
        self.assertEqual(result['status'], 'ready_for_edit')
        self.assertFalse(result['final_export_approved'])

    def test_failed_and_unknown_cannot_advance(self):
        for status, expected in [('fail', 'rejected'), ('uncertain', 'needs_evidence')]:
            self.report['checks']['camera_locked']['status'] = status
            self.assertEqual(ap.gate(self.packet, self.report)['status'], expected)

    def test_stale_inputs(self):
        for path in ['source.txt', 'ref.png', 'job.json', 'clip.mp4']:
            p = self.root / path; original = p.read_bytes(); p.write_bytes(b'changed')
            with self.assertRaises(ValueError): ap.gate(self.packet, self.report)
            p.write_bytes(original)

    def test_no_self_review_or_missing_checks(self):
        self.report['reviewer_id'] = 'producer'
        with self.assertRaises(ValueError): ap.gate(self.packet, self.report)
        self.report['reviewer_id'] = 'reviewer'
        del self.report['checks']['lip_sync']
        with self.assertRaises(ValueError): ap.gate(self.packet, self.report)

    def test_sampling_asr_and_wrong_modality_cannot_pass(self):
        for name, method in [('camera_locked', 'sampled_stills'), ('wording', 'asr'),
                             ('lip_sync', 'direct_audio'), ('no_added_text', 'direct_audio')]:
            report = copy.deepcopy(self.report); report['checks'][name]['method'] = method
            with self.assertRaises(ValueError): ap.gate(self.packet, report)
        self.report['checks']['background_stationary']['coverage'] = 'sampled'
        with self.assertRaises(ValueError): ap.gate(self.packet, self.report)

    def test_packet_tamper_and_wrong_report(self):
        self.report['packet_hash'] = 'wrong'
        with self.assertRaises(ValueError): ap.gate(self.packet, self.report)
        self.packet['dialogue'] = 'changed'
        with self.assertRaises(ValueError): ap.validate_packet(self.packet)

    def test_invalid_media_cannot_pass(self):
        for info in [{'streams': [], 'format': {'duration': '4'}},
                     {'streams': [{'codec_type': 'video', 'width': 1920, 'height': 1080},
                                  {'codec_type': 'audio'}], 'format': {'duration': '4'}}]:
            with patch.object(ap, 'probe', return_value=info):
                with self.assertRaises(ValueError): ap.gate(self.packet, self.report)

    def test_normalized_voice_paths(self):
        for path in ['./ref.png', str(self.root / 'ref.png')]:
            self.job['voice_reference'] = path
            (self.root / 'job.json').write_text(json.dumps(self.job))
            p = ap.packet('job.json', 'clip.mp4')
            self.report['packet_hash'] = p['packet_hash']
            self.assertEqual(ap.gate(p, self.report)['status'], 'ready_for_edit')

    def test_baseline_requires_explicit_mode(self):
        del self.job['voice_reference']
        (self.root / 'job.json').write_text(json.dumps(self.job))
        with self.assertRaises(ValueError): ap.packet('job.json', 'clip.mp4')
        self.job['voice_mode'] = 'establish_baseline'
        (self.root / 'job.json').write_text(json.dumps(self.job))
        p = ap.packet('job.json', 'clip.mp4'); self.report['packet_hash'] = p['packet_hash']
        self.report['checks']['voice_continuity']['baseline_established'] = True
        self.assertEqual(ap.gate(p, self.report)['status'], 'ready_for_edit')

    def test_overlapping_fields(self):
        for path in ['input.prompt', 'input.prompt.resolution']:
            self.job['resolution_field'] = path
            with self.assertRaises(ValueError): ap.compile_job(self.job)

    def test_no_overwrite_or_path_escape(self):
        with self.assertRaises(FileExistsError): ap.write('job.json', {})
        with self.assertRaises(ValueError): ap.local('../outside')


if __name__ == '__main__': unittest.main()
