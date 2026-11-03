import copy
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import kie_tasks as kie
import production_runner as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        for module, name, value in [(ap, 'ROOT', self.root), (kie, 'ROOT', self.root),
                                    (kie, 'STATE', self.root / 'File/generation')]:
            p = patch.object(module, name, value); p.start(); self.addCleanup(p.stop)
        (self.root / '.env').write_text('KIE_API_KEY=offline-fixture-key\nKIE_PROJECT_CAP_CREDITS=100\n')
        p = patch.dict('os.environ', {'KIE_PROJECT_CAP_CREDITS': '100'}); p.start(); self.addCleanup(p.stop)
        for path, value in [('source.txt', 'Hello there.'), ('ref.png', 'image fixture'), ('voice.wav', 'voice fixture')]:
            (self.root / path).write_text(value)
        self.job = {'producer_id': 'producer-thread', 'script': 'source.txt', 'references': ['ref.png'],
                    'voice_reference': 'voice.wav', 'dialogue': 'Hello there.', 'resolution': '720p',
                    'visual_direction': 'Natural presenter', 'gestures': [{'phrase': 'Hello', 'cue': 'Open palm'}],
                    'payload': {'model': 'offline-only', 'input': {}},
                    'prompt_field': 'input.prompt', 'resolution_field': 'input.resolution'}
        self.write('job.json', self.job)
        self.manifest = {'id': 'batch-v1', 'clips': [{'id': 'clip1', 'job': 'job.json', 'cap_credits': '2'}]}
        self.write('manifest.json', self.manifest)
        policy = Path(__file__).resolve().parents[1] / 'pacing_policy.json'
        self.write('File/pacing_policy.json', json.loads(policy.read_text()))
        self.api_calls = []
        def api(method, path, key, body=None):
            self.api_calls.append(method)
            if method == 'POST': return {'code': 200, 'data': {'taskId': 'provider-task'}}
            return {'code': 200, 'data': {'taskId': 'provider-task', 'state': 'success',
                    'resultJson': json.dumps({'resultUrls': ['https://media.example/video.mp4']})}}
        p = patch.object(kie, 'api', side_effect=api); p.start(); self.addCleanup(p.stop)
        info = {'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}, {'codec_type': 'audio'}],
                'format': {'duration': '4'}}
        p = patch.object(ap, 'probe', return_value=info); p.start(); self.addCleanup(p.stop)
        def download(url, path):
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'video fixture')
            runner.save(Path(str(path) + '.download.json'), {'urlHash': ap.digest(url), 'media': ap.fingerprint(runner.rel(path))})
        p = patch.object(runner, 'download', side_effect=download); p.start(); self.addCleanup(p.stop)
        p = patch.object(ap, 'tool_health', return_value={'ffmpeg': {'usable': True}, 'ffprobe': {'usable': True}}); p.start(); self.addCleanup(p.stop)
        p = patch.object(runner, 'prepare_evidence'); p.start(); self.addCleanup(p.stop)

    def write(self, path, data):
        p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data)); return path

    def state(self):
        return runner.read(runner.directory('batch-v1') / 'state.json')

    def start(self):
        result = runner.prepare('manifest.json')
        runner.authorize('batch-v1', result['approvalHash'], 'user-message:fixture-approval')

    def advance(self, count=1):
        for _ in range(count): runner.advance('batch-v1')

    def review_ready(self):
        self.start(); self.advance(5)
        self.assertEqual(self.state()['clips'][0]['stage'], 'review_requested')

    def finish_review(self, check_status='pass'):
        state = self.state(); entry = state['clips'][0]
        result = {'taskId': 'review-task', 'childThreadId': 'reviewer-thread', 'status': 'running'}
        self.write('dispatch.json', result)
        runner.bind_review('batch-v1', 'clip1', 'dispatch.json')
        packet = ap.load(entry['packet'])
        report = {'packet_hash': packet['packet_hash'], 'reviewer_id': 'reviewer-thread',
                  'delegation_id': None, 'checks': {k: {'status': 'pass', 'method': 'direct_av',
                  'coverage': 'full_clip', 'evidence': 'Synthetic offline fixture'} for k in ap.CHECKS}}
        report['checks']['resolution']['method'] = 'ffprobe'
        report['checks']['background_stationary']['status'] = check_status
        self.write(entry['report'], report)
        result['status'] = 'completed'
        self.write('completion.json', result)
        runner.bind_review('batch-v1', 'clip1', 'completion.json', completed=True)
        self.advance()

    def test_prepare_and_advance_without_authorization_are_offline(self):
        runner.prepare('manifest.json'); self.advance(2)
        self.assertEqual(self.api_calls, [])
        self.assertEqual(self.state()['clips'][0]['stage'], 'prepared')

    def test_broken_tools_block_before_paid_submission(self):
        self.start()
        with patch.object(ap, 'tool_health', return_value={'ffmpeg': {'usable': False}, 'ffprobe': {'usable': True}}):
            self.advance()
        self.assertEqual(self.api_calls, [])
        self.assertEqual(self.state()['clips'][0]['errors'], 1)

    def test_review_metadata_is_validated_before_any_preview_or_spend(self):
        for key, value in [('producer_id', None), ('producer_id', ' '), ('voice_mode', 'unsupported'),
                           ('voice_reference', None)]:
            job = copy.deepcopy(self.job); job[key] = value
            self.write('job.json', job)
            with self.assertRaises(ValueError): runner.prepare('manifest.json')
            self.assertEqual(self.api_calls, [])
            self.assertEqual(list((self.root / 'File/generation').glob('*.preview.json')), [])

    def test_prepare_resume_reuses_previews(self):
        first = runner.prepare('manifest.json'); before = self.state()['clips'][0]['preview']
        second = runner.prepare('manifest.json')
        self.assertEqual(first['approvalHash'], second['approvalHash'])
        self.assertEqual(before, self.state()['clips'][0]['preview'])

    def test_full_flow_creates_one_post_and_binds_review(self):
        self.review_ready(); request = ap.load(self.state()['clips'][0]['reviewRequest'])
        self.advance(2)
        self.assertEqual(request, ap.load(self.state()['clips'][0]['reviewRequest']))
        self.finish_review(); self.advance(2)
        self.assertEqual(self.api_calls.count('POST'), 1)
        handoff = runner.read(runner.directory('batch-v1') / 'edit-ready.json')
        self.assertTrue(handoff['ready']); self.assertFalse(handoff['finalExportApproved'])
        self.assertFalse(handoff['editingComplete'])
        self.assertTrue(handoff['autoCut']['required'])
        self.assertEqual(handoff['autoCut']['status'], 'pending')
        self.assertEqual(handoff['autoCut']['policy'], ap.fingerprint('File/pacing_policy.json'))
        original = ap.load(self.state()['clips'][0]['report'])
        self.assertIsNone(original['delegation_id'])

    def test_invalid_pacing_policy_cannot_create_ready_handoff(self):
        self.review_ready(); self.finish_review()
        policy = ap.load('File/pacing_policy.json')
        policy['pause_planner']['target_pause_seconds'] = 2
        self.write('File/pacing_policy.json', policy)
        with self.assertRaises(ValueError): self.advance()
        self.assertFalse(runner.read(runner.directory('batch-v1') / 'edit-ready.json')['ready'])

    def test_failed_review_blocks_handoff(self):
        self.review_ready(); self.finish_review('fail')
        self.assertEqual(self.state()['clips'][0]['stage'], 'rejected')
        self.assertFalse(runner.read(runner.directory('batch-v1') / 'edit-ready.json')['ready'])
        self.advance(3); self.assertEqual(self.api_calls.count('POST'), 1)

    def test_unknown_submission_is_not_retried(self):
        self.start()
        with patch.object(kie, 'api', side_effect=TimeoutError): self.advance()
        state = self.state(); state['clips'][0]['retryAt'] = 0
        runner.save(runner.directory('batch-v1') / 'state.json', state)
        self.advance(2)
        self.assertEqual(self.state()['clips'][0]['stage'], 'unknown_submission')
        self.assertEqual(self.api_calls, [])

    def test_crash_after_submission_resumes_same_operation(self):
        self.start(); state = self.state(); entry = state['clips'][0]
        kie.submit(entry['preview'], entry['approvalHash'])
        self.advance(4)
        self.assertEqual(self.api_calls.count('POST'), 1)
        self.assertEqual(self.state()['clips'][0]['stage'], 'review_requested')

    def test_stale_source_or_bad_approval_prevents_spending(self):
        prepared = runner.prepare('manifest.json')
        with self.assertRaises(ValueError): runner.authorize('batch-v1', 'wrong', 'message')
        (self.root / 'source.txt').write_text('Changed')
        with self.assertRaises(ValueError): runner.authorize('batch-v1', prepared['approvalHash'], 'message')
        with self.assertRaises(ValueError): self.advance()
        self.assertEqual(self.api_calls, [])

    def test_dependency_waits_for_sample_review(self):
        self.manifest['clips'].append({'id': 'clip2', 'job': 'job.json', 'cap_credits': '2', 'depends_on': ['clip1']})
        self.write('manifest.json', self.manifest)
        self.review_ready()
        self.assertEqual(self.state()['clips'][1]['stage'], 'prepared')
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_different_reviewer_and_incomplete_task_refused(self):
        self.review_ready()
        self.write('dispatch.json', {'taskId': 't1', 'childThreadId': 'r1', 'status': 'running'})
        runner.bind_review('batch-v1', 'clip1', 'dispatch.json')
        self.write('dispatch2.json', {'taskId': 't2', 'childThreadId': 'r2', 'status': 'running'})
        with self.assertRaises(ValueError): runner.bind_review('batch-v1', 'clip1', 'dispatch2.json')
        with self.assertRaises(ValueError): runner.bind_review('batch-v1', 'clip1', 'dispatch.json', completed=True)

    def test_wrong_report_author_cannot_pass(self):
        self.review_ready()
        self.finish_review()
        entry = self.state()['clips'][0]
        report = ap.load(entry['report']); report['reviewer_id'] = 'wrong'
        self.write(entry['report'], report)
        with self.assertRaises(ValueError): self.advance()

    def test_invalid_dependency_and_batch_path(self):
        self.manifest['clips'][0]['depends_on'] = ['later']
        self.write('manifest.json', self.manifest)
        with self.assertRaises(ValueError): runner.prepare('manifest.json')
        with self.assertRaises(ValueError): runner.directory('../escape')

    def test_cross_clip_packet_cannot_be_admitted(self):
        self.review_ready()
        entry = self.state()['clips'][0]
        (self.root / 'other.mp4').write_bytes(b'other video fixture')
        self.write(entry['packet'], ap.packet('job.json', 'other.mp4'))
        self.write('dispatch.json', {'taskId': 't1', 'childThreadId': 'r1', 'status': 'running'})
        with self.assertRaises(ValueError): runner.bind_review('batch-v1', 'clip1', 'dispatch.json')
        with self.assertRaises(ValueError): self.advance()
        self.assertFalse(runner.read(runner.directory('batch-v1') / 'edit-ready.json')['ready'])

    def test_bound_report_tampering_invalidates_handoff(self):
        self.review_ready(); self.finish_review()
        entry = self.state()['clips'][0]; bound = ap.load(entry['boundReport'])
        bound['checks']['wording']['evidence'] = 'changed after acceptance'
        self.write(entry['boundReport'], bound)
        with self.assertRaises(ValueError): self.advance()
        self.assertFalse(runner.read(runner.directory('batch-v1') / 'edit-ready.json')['ready'])

    def test_local_recovery_preserves_preview(self):
        self.start(); state = self.state(); entry = state['clips'][0]
        preview_id = entry['preview']; entry['errors'] = 3
        runner.save(runner.directory('batch-v1') / 'state.json', state)
        runner.recover('batch-v1', 'clip1', 'Local prerequisite corrected')
        self.assertEqual(self.state()['clips'][0]['preview'], preview_id)
        self.assertEqual(self.state()['clips'][0]['errors'], 0)
        self.advance(); self.assertEqual(self.api_calls.count('POST'), 1)

    def test_unknown_recovery_requires_reconciled_original_operation(self):
        self.start()
        with patch.object(kie, 'api', side_effect=TimeoutError): self.advance()
        state = self.state(); entry = state['clips'][0]; entry['stage'] = 'unknown_submission'
        runner.save(runner.directory('batch-v1') / 'state.json', state)
        with self.assertRaises(ValueError): runner.recover('batch-v1', 'clip1', 'No evidence')
        path = kie.paths(entry['preview'])[1]; op = kie.load(path)
        op.update(status='submitted', taskId='provider-task'); kie.replace(path, op)
        runner.recover('batch-v1', 'clip1', 'Synthetic fixture: provider task reconciled')
        self.advance(); self.assertEqual(self.api_calls.count('POST'), 0)

    def test_rereview_preserves_findings_and_uses_new_id(self):
        self.review_ready(); self.finish_review('uncertain')
        entry = self.state()['clips'][0]; original = ap.load(entry['reviewRequest'])
        self.write('extra-evidence.json', {'actualEvidence': 'fixture only'})
        runner.rereview('batch-v1', 'clip1', 'extra-evidence.json')
        new = self.state()['clips'][0]
        self.assertEqual(new['reviewRound'], 2)
        request = ap.load(new['reviewRequest'])
        self.assertNotEqual(original['clientRequestId'], request['clientRequestId'])
        self.assertIn(entry['report'], request['task'])
        self.assertTrue((self.root / entry['report']).exists())
        self.write('old-dispatch.json', {'taskId': 'review-task', 'childThreadId': 'reviewer-thread'})
        with self.assertRaises(ValueError): runner.bind_review('batch-v1', 'clip1', 'old-dispatch.json')
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_no_silent_selection_of_multiple_provider_outputs(self):
        self.start(); self.advance(3)
        entry = self.state()['clips'][0]; operation = kie.load(kie.paths(entry['preview'])[1])
        receipt = ap.load(operation['latestReceipt'])
        receipt['receipt']['resultJson'] = json.dumps({'resultUrls': ['https://one.example', 'https://two.example']})
        self.write(operation['latestReceipt'], receipt)
        with self.assertRaises(ValueError): runner.result_url(entry)

    def test_single_advance_reaches_local_preview_and_review_request(self):
        self.start(); result = runner.advance('batch-v1')
        clip = result['clips'][0]
        self.assertEqual(clip['stage'], 'review_requested')
        self.assertEqual(clip['reviewStatus'], 'UNREVIEWED')
        self.assertEqual(clip['mediaPath'], 'Assets/generated/batch-v1/clip1.mp4')
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_parallel_downloads_cover_every_finished_clip(self):
        for n in (2, 3):
            self.manifest['clips'].append({'id': f'clip{n}', 'job': 'job.json', 'cap_credits': '2'})
        self.write('manifest.json', self.manifest)
        self.start()
        with patch.object(runner, 'DOWNLOAD_WORKERS', 3): runner.advance('batch-v1')
        self.assertEqual([c['stage'] for c in self.state()['clips']], ['review_requested'] * 3)
        self.assertEqual(runner.download.call_count, 3)
        self.assertEqual(self.api_calls.count('POST'), 3)

    def test_failed_download_records_error_without_new_paid_request(self):
        self.start()
        with patch.object(runner, 'download', side_effect=ValueError('network')):
            runner.advance('batch-v1')
        entry = self.state()['clips'][0]
        self.assertEqual(entry['stage'], 'download'); self.assertEqual(entry['errors'], 1)
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_fetch_waits_for_provider_then_stops_at_review(self):
        states = iter(['generating', 'generating', 'success'])
        def api(method, path, key, body=None):
            self.api_calls.append(method)
            if method == 'POST': return {'code': 200, 'data': {'taskId': 'provider-task'}}
            return {'code': 200, 'data': {'taskId': 'provider-task', 'state': next(states),
                    'resultJson': json.dumps({'resultUrls': ['https://media.example/video.mp4']})}}
        self.start()
        clock = [1000.0]
        with patch.object(kie, 'api', side_effect=api), \
             patch.object(runner.time, 'time', side_effect=lambda: clock[0]), \
             patch.object(runner.time, 'sleep', side_effect=lambda s: clock.__setitem__(0, clock[0] + s)):
            result = runner.fetch('batch-v1', wait_seconds=60)
        self.assertTrue(result['fetchComplete'])
        self.assertEqual(result['clips'][0]['stage'], 'review_requested')
        self.assertEqual(self.api_calls.count('POST'), 1)
        self.assertEqual(self.api_calls.count('GET'), 3)

    def test_fetch_without_authorization_returns_immediately_offline(self):
        runner.prepare('manifest.json')
        result = runner.fetch('batch-v1', wait_seconds=60)
        self.assertTrue(result['fetchComplete']); self.assertEqual(self.api_calls, [])

    def test_fetch_does_not_wait_on_review_dependency(self):
        self.manifest['clips'].append({'id': 'clip2', 'job': 'job.json', 'cap_credits': '2', 'depends_on': ['clip1']})
        self.write('manifest.json', self.manifest)
        self.start(); result = runner.fetch('batch-v1', wait_seconds=60)
        self.assertTrue(result['fetchComplete'])
        self.assertEqual([c['stage'] for c in result['clips']], ['review_requested', 'prepared'])
        self.assertEqual(self.api_calls.count('POST'), 1)


class RegenerationTests(RunnerTests):
    def setUp(self):
        super().setUp()
        self.manifest['auto_regeneration'] = {'max_attempts_per_clip': 2, 'repair_cap_credits': '10'}
        self.write('manifest.json', self.manifest)
        self.reviews = 0

    def review_take(self, status='fail', correction='Keep both hands fully inside the frame during "Hello".'):
        self.reviews += 1
        entry = self.state()['clips'][0]
        self.assertEqual(entry['stage'], 'review_requested')
        result = {'taskId': f'review-task-{self.reviews}', 'childThreadId': f'reviewer-{self.reviews}', 'status': 'running'}
        self.write('dispatch.json', result); runner.bind_review('batch-v1', 'clip1', 'dispatch.json')
        packet = ap.load(entry['packet'])
        report = {'packet_hash': packet['packet_hash'], 'reviewer_id': result['childThreadId'], 'delegation_id': None,
                  'checks': {k: {'status': 'pass', 'method': 'direct_av', 'coverage': 'full_clip',
                                 'evidence': 'Synthetic offline fixture'} for k in ap.CHECKS}}
        report['checks']['resolution']['method'] = 'ffprobe'
        report['checks']['hand_framing']['status'] = status
        if correction: report['correction'] = correction
        self.write(entry['report'], report)
        result['status'] = 'completed'; self.write('completion.json', result)
        runner.bind_review('batch-v1', 'clip1', 'completion.json', completed=True)
        return runner.advance('batch-v1')

    def test_rejected_take_regenerates_automatically_with_correction_only(self):
        self.start(); runner.advance('batch-v1')
        first = self.state()['clips'][0]['payload']
        self.review_take()
        entry = self.state()['clips'][0]
        self.assertEqual((entry['take'], entry['stage']), (2, 'review_requested'))
        self.assertEqual(self.api_calls.count('POST'), 2)
        self.assertEqual(entry['media']['path'], 'Assets/generated/batch-v1/clip1.t2.mp4')
        prompt = entry['takePayload']['input']['prompt']
        self.assertIn('Keep both hands fully inside the frame', prompt)
        self.assertIn('hand_framing', prompt)
        self.assertIn('Hello there.', prompt)
        self.assertEqual({k: v for k, v in entry['takePayload']['input'].items() if k != 'prompt'},
                         {k: v for k, v in first['input'].items() if k != 'prompt'})
        self.assertEqual(entry['takeHistory'][0]['stage'], 'rejected')
        self.review_take('pass')
        handoff = runner.read(runner.directory('batch-v1') / 'edit-ready.json')
        self.assertTrue(handoff['ready'])
        self.assertEqual(handoff['clips'][0]['media']['path'], 'Assets/generated/batch-v1/clip1.t2.mp4')

    def test_attempt_limit_stops_regeneration(self):
        self.start(); runner.advance('batch-v1')
        self.review_take(); self.review_take(); self.review_take()
        entry = self.state()['clips'][0]
        self.assertEqual((entry['stage'], entry['regenBlocked']), ('rejected', 'attempt_limit_reached'))
        self.assertEqual(self.api_calls.count('POST'), 3)

    def test_repair_credit_cap_stops_regeneration(self):
        self.manifest['auto_regeneration']['repair_cap_credits'] = '3'
        self.write('manifest.json', self.manifest)
        self.start(); runner.advance('batch-v1')
        self.review_take(); self.review_take()
        entry = self.state()['clips'][0]
        self.assertEqual(entry['regenBlocked'], 'repair_credits_exhausted')
        self.assertEqual(self.api_calls.count('POST'), 2)

    def test_missing_correction_or_uncertainty_never_spends(self):
        self.start(); runner.advance('batch-v1')
        self.review_take(correction=None)
        entry = self.state()['clips'][0]
        self.assertEqual((entry['stage'], entry['regenBlocked']), ('rejected', 'no_reviewer_correction'))
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_uncertain_review_does_not_regenerate(self):
        self.start(); runner.advance('batch-v1')
        self.review_take(status='uncertain')
        self.assertEqual(self.state()['clips'][0]['stage'], 'needs_evidence')
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_batch_without_regeneration_scope_does_not_spend(self):
        del self.manifest['auto_regeneration']; self.write('manifest.json', self.manifest)
        self.start(); runner.advance('batch-v1'); self.review_take()
        entry = self.state()['clips'][0]
        self.assertEqual((entry['stage'], entry['regenBlocked']), ('rejected', 'not_authorized'))
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_tampered_regeneration_job_blocks(self):
        self.start(); runner.advance('batch-v1'); self.review_take()
        entry = self.state()['clips'][0]
        job = ap.load(entry['takeJob']); job['dialogue'] = 'Changed words.'
        self.write(entry['takeJob'], job)
        with self.assertRaises(ValueError): runner.advance('batch-v1')

    def test_old_take_reviewer_cannot_review_new_take(self):
        self.start(); runner.advance('batch-v1'); self.review_take()
        self.write('dispatch.json', {'taskId': 'review-task-1', 'childThreadId': 'reviewer-1', 'status': 'running'})
        with self.assertRaises(ValueError): runner.bind_review('batch-v1', 'clip1', 'dispatch.json')

    def test_standing_defaults_enable_regeneration_unless_disabled(self):
        del self.manifest['auto_regeneration']; self.write('manifest.json', self.manifest)
        self.write('File/repair_defaults.json', {'version': 1, 'repairCapCredits': '1000', 'maxAttemptsPerAsset': 2})
        scope = runner.regeneration_scope(self.manifest)
        self.assertEqual((scope['maxAttemptsPerClip'], scope['repairCapCredits']), (2, '1000'))
        self.assertIsNone(runner.regeneration_scope({'auto_regeneration': False}))

    def test_regeneration_scope_is_part_of_single_approval(self):
        approval = ap.load(runner.prepare('manifest.json')['approvalRequest'])
        self.assertEqual(approval['autoRegeneration']['maxAttemptsPerClip'], 2)
        self.assertEqual(approval['autoRegeneration']['repairCapCredits'], '10')


class GrantAndUploadTests(RunnerTests):
    def setUp(self):
        super().setUp()
        from datetime import datetime, timedelta, timezone
        self.now = datetime.now(timezone.utc)
        self.uploads = []
        def upload(path, min_hours=6):
            self.uploads.append(path)
            return {'file': ap.fingerprint(path), 'downloadUrl': f'https://tempfile.example/{len(self.uploads)}',
                    'expiresAt': (self.now + timedelta(hours=self.hours)).isoformat()}
        self.hours = 24
        p = patch.object(kie, 'upload', side_effect=upload); p.start(); self.addCleanup(p.stop)
        self.grant = {'id': 'grant-v1', 'script': 'source.txt', 'references': ['ref.png'],
                      'voice_references': ['voice.wav'], 'models': ['offline-only'],
                      'per_clip_cap_credits': '2', 'original_cap_credits': '4',
                      'max_attempts_per_clip': 2, 'repair_cap_credits': '10'}
        self.manifest['auto_regeneration'] = {'max_attempts_per_clip': 2, 'repair_cap_credits': '10'}
        self.write('manifest.json', self.manifest)

    def approve_grant(self):
        self.write('grant.json', self.grant)
        request = runner.grant_prepare('grant.json')
        runner.grant_authorize(request['approvalHash'], 'user-message:one-time-project-grant')

    def test_grant_authorizes_batch_without_per_batch_approval(self):
        self.approve_grant()
        result = runner.prepare('manifest.json')
        self.assertEqual(result['grantStatus'], 'authorized_by_project_grant')
        self.assertTrue(result['authorized'])
        runner.advance('batch-v1')
        self.assertEqual(self.state()['clips'][0]['stage'], 'review_requested')
        self.assertEqual(self.api_calls.count('POST'), 1)

    def test_no_grant_means_no_spend(self):
        result = runner.prepare('manifest.json')
        self.assertEqual(result['grantStatus'], 'no_project_grant')
        runner.advance('batch-v1'); self.assertEqual(self.api_calls, [])

    def test_grant_scope_is_enforced(self):
        self.approve_grant()
        (self.root / 'other.png').write_text('different avatar')
        job = dict(self.job, references=['other.png']); self.write('job.json', job)
        self.assertEqual(runner.prepare('manifest.json')['grantStatus'], 'reference_not_in_grant')
        runner.advance('batch-v1'); self.assertEqual(self.api_calls, [])

    def test_grant_credit_total_spans_batches(self):
        self.approve_grant()
        runner.prepare('manifest.json')
        for n in (2, 3):
            self.write(f'manifest{n}.json', {'id': f'batch-v{n}', 'clips': [{'id': 'clip1', 'job': 'job.json', 'cap_credits': '2'}]})
        self.assertEqual(runner.prepare('manifest2.json')['grantStatus'], 'authorized_by_project_grant')
        self.assertEqual(runner.prepare('manifest3.json')['grantStatus'], 'grant_credits_exhausted')

    def test_admitted_take_can_be_next_batch_voice(self):
        self.approve_grant(); runner.prepare('manifest.json'); runner.advance('batch-v1')
        self.finish_review()
        media = self.state()['clips'][0]['media']['path']
        self.write('job2.json', dict(self.job, voice_reference=media))
        self.write('manifest2.json', {'id': 'batch-v2', 'clips': [{'id': 'clip2', 'job': 'job2.json', 'cap_credits': '2'}]})
        self.assertEqual(runner.prepare('manifest2.json')['grantStatus'], 'authorized_by_project_grant')

    def test_changed_grant_reference_blocks(self):
        self.approve_grant()
        (self.root / 'ref.png').write_text('swapped')
        with self.assertRaises(ValueError): runner.prepare('manifest.json')
        self.assertEqual(self.api_calls, [])

    def upload_job(self):
        self.job['payload'] = {'model': 'offline-only', 'input': {'image_url': '', 'audio_url': ''}}
        self.job['uploads'] = {'input.image_url': 'ref.png', 'input.audio_url': ['voice.wav']}
        self.write('job.json', self.job)

    def test_references_upload_automatically_into_payload(self):
        self.upload_job(); self.approve_grant()
        runner.prepare('manifest.json')
        payload = self.state()['clips'][0]['payload']['input']
        urls = {r['field']: r['urls'] for r in self.state()['clips'][0]['uploads']}
        self.assertEqual(payload['image_url'], urls['input.image_url'][0])
        self.assertEqual(payload['audio_url'], urls['input.audio_url'])
        self.assertEqual(sorted(self.uploads), ['ref.png', 'voice.wav'])
        runner.advance('batch-v1')
        self.assertEqual(self.state()['clips'][0]['stage'], 'review_requested')

    def test_unselected_file_cannot_be_uploaded(self):
        self.upload_job(); self.job['uploads'] = {'input.image_url': 'source.txt'}; self.write('job.json', self.job)
        with self.assertRaises(ValueError): runner.prepare('manifest.json')
        self.assertEqual(self.uploads, [])

    def test_tampered_resolved_job_blocks(self):
        self.upload_job(); self.approve_grant(); runner.prepare('manifest.json')
        entry = self.state()['clips'][0]
        job = ap.load(entry['job']); job['payload']['input']['image_url'] = 'https://elsewhere.example/x'
        self.write(entry['job'], job)
        with self.assertRaises(ValueError): runner.advance('batch-v1')
        self.assertEqual(self.api_calls, [])

    def test_expired_uploads_block_first_submission(self):
        self.upload_job(); self.hours = 0.5; self.approve_grant(); runner.prepare('manifest.json')
        runner.advance('batch-v1')
        entry = self.state()['clips'][0]
        self.assertEqual(entry['errors'], 1); self.assertEqual(self.api_calls, [])

    def test_regeneration_refreshes_expiring_uploads(self):
        self.upload_job(); self.approve_grant(); runner.prepare('manifest.json'); runner.advance('batch-v1')
        before = self.state()['clips'][0]['payload']['input']
        reviews = RegenerationTests.review_take
        with patch.object(runner, 'UPLOAD_REFRESH_HOURS', 25):
            self.reviews = 0; reviews(self)
        entry = self.state()['clips'][0]
        self.assertEqual((entry['take'], entry['stage']), (2, 'review_requested'))
        self.assertEqual(len(self.uploads), 4)
        after = entry['takePayload']['input']
        self.assertNotEqual(after['image_url'], before['image_url'])
        self.assertEqual(self.api_calls.count('POST'), 2)
        runner.advance('batch-v1')  # revalidates refreshed base against its receipts

    def test_tampered_refreshed_base_blocks(self):
        self.upload_job(); self.approve_grant(); runner.prepare('manifest.json'); runner.advance('batch-v1')
        with patch.object(runner, 'UPLOAD_REFRESH_HOURS', 25):
            self.reviews = 0; RegenerationTests.review_take(self)
        entry = self.state()['clips'][0]
        base = ap.load(entry['takeBase']); base['payload']['input']['image_url'] = 'https://elsewhere.example'
        self.write(entry['takeBase'], base)
        with self.assertRaises(ValueError): runner.advance('batch-v1')

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg not installed')
class EvidenceTests(unittest.TestCase):
    def test_single_pass_evidence_includes_contact_sheet(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with patch.object(ap, 'ROOT', root):
                media = root / 'clip.mp4'
                subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=1280x720:rate=24:duration=3',
                                '-f', 'lavfi', '-i', 'sine=duration=3', '-shortest', '-c:v', 'libx264',
                                '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(media)], check=True)
                folder = root / 'clip.evidence'
                runner.prepare_evidence(media, folder)
                names = sorted(p.name for p in folder.iterdir())
                self.assertIn('contact.jpg', names); self.assertIn('audio.wav', names)
                self.assertEqual(len([n for n in names if n.startswith('frame-')]), 12)
                index = runner.read(folder / 'index.json')
                self.assertIn('contact.jpg', json.dumps(index['artifacts']))


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        p = patch.object(ap, 'ROOT', self.root); p.start(); self.addCleanup(p.stop)

    def response(self, data=b'complete video bytes', length=None):
        response = BytesIO(data)
        response.status = 200
        response.headers = {'Content-Length': str(len(data) if length is None else length)}
        return response

    def test_bounded_download_no_credentials_and_saved_provenance(self):
        from unittest.mock import Mock
        opener = Mock(); opener.open.return_value = self.response()
        destination = self.root / 'clip.mp4'
        with patch.object(runner.socket, 'getaddrinfo', return_value=[(None, None, None, None, ('8.8.8.8', 443))]), patch.object(runner.urllib.request, 'build_opener', return_value=opener):
            runner.download('https://media.example/clip?signature=private', destination)
        request = opener.open.call_args[0][0]
        self.assertIsNone(request.get_header('Authorization'))
        self.assertIsNone(request.get_header('Cookie'))
        receipt = runner.read(Path(str(destination) + '.download.json'))
        self.assertEqual(receipt['media'], ap.fingerprint('clip.mp4'))
        self.assertNotIn('signature=private', json.dumps(receipt))

    def test_truncated_download_never_becomes_media(self):
        from unittest.mock import Mock
        opener = Mock(); opener.open.return_value = self.response(length=100)
        destination = self.root / 'clip.mp4'
        with patch.object(runner.socket, 'getaddrinfo', return_value=[(None, None, None, None, ('8.8.8.8', 443))]), patch.object(runner.urllib.request, 'build_opener', return_value=opener):
            with self.assertRaises(ValueError): runner.download('https://media.example/clip', destination)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob('.download-*')), [])

    def test_private_and_credentialed_urls_refused_without_fetch(self):
        with patch.object(runner.urllib.request, 'build_opener') as opener:
            for url in ['http://example.com/a', 'https://user:password@example.com/a']:
                with self.assertRaises(ValueError): runner.download(url, self.root / 'clip.mp4')
            with patch.object(runner.socket, 'getaddrinfo', return_value=[(None, None, None, None, ('127.0.0.1', 443))]):
                with self.assertRaises(ValueError): runner.download('https://local.example/a', self.root / 'clip.mp4')
            opener.assert_not_called()


if __name__ == '__main__': unittest.main()
