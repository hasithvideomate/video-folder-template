"""Offline ledger integration tests; synthetic reports/media are not real AV QA.

Only ROOT, media probing and ffmpeg decoding are mocked. Transport receipts and
user evidence refs represent external attestations, not autonomous execution.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import edit_decisions
import edit_farm as farm
import premiere_writer as writer


class EditFarmTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.patch(ap, 'ROOT', new=self.root)
        self.probe = self.patch(ap, 'probe', side_effect=self.media_info)
        self.decode = self.patch(farm.subprocess, 'run', side_effect=self.decode_only)
        self.bytes('project.prproj', b'saved project fixture')
        self.bytes('Assets/source.mov', b'synthetic source bytes')
        self.bytes('Assets/reference.mov', b'synthetic reference bytes')
        self.json('File/pacing_policy.json', {
            'version': 1, 'required': True,
            'pause_planner': {'max_pause_seconds': .5, 'target_pause_seconds': .24,
                              'sentence_pause_seconds': .4},
            'add_captions': False, 'allow_zoom_or_reframing': False,
            'change_playback_speed': False})
        self.manifest = {'id': 'fixture-run', 'producer_id': 'parent-thread',
                         'intent': 'Tighten supplied speech and preserve every word and ending',
                         'project': 'project.prproj', 'sources': [
                             {'id': 'a', 'path': 'Assets/source.mov', 'role': 'primary'},
                             {'id': 'ref', 'path': 'Assets/reference.mov', 'role': 'reference'}]}
        self.json('manifest.json', self.manifest)
        self.run = self.manifest['id']
        self.writer_args = ('project.prproj', self.run, 'parent-thread')

    def patch(self, obj, name, **kwargs):
        mocked = patch.object(obj, name, **kwargs)
        result = mocked.start()
        self.addCleanup(mocked.stop)
        return result

    def bytes(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return name

    def json(self, name, value):
        return self.bytes(name, json.dumps(value).encode())

    def media_info(self, name):
        return {'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'width': 1280,
             'height': 720, 'avg_frame_rate': '30/1'},
            {'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': '48000', 'channels': 2}],
            'format': {'duration': '2' if str(name).startswith('Exports/') else '3'}}

    def decode_only(self, args, **kwargs):
        self.assertEqual(args[:5], ['ffmpeg', '-nostdin', '-v', 'error', '-xerror'])
        self.assertEqual(args[-6:], ['0:v:0', '-map', '0:a:0', '-f', 'null', '-'])
        self.assertTrue(kwargs['check'])
        return subprocess.CompletedProcess(args, 0)

    def state(self):
        return farm.load_state(self.run)

    def task(self, key):
        return self.state()['tasks'][key]

    def bind(self, key, **overrides):
        receipt = {'taskId': 't3-' + key, 'childThreadId': 'child-' + key,
                   'status': 'running', **overrides}
        path = self.json('transport/' + key + '.dispatch.json', {'structuredContent': receipt})
        farm.bind(self.run, key, path)
        return receipt

    def report(self, key, verdict='pass'):
        task = self.task(key)
        packet = farm.packet_for(task)
        report = {'reviewer_id': task['reviewer_id'], 'packet_hash': packet['packet_hash']}
        if task['role'] in farm.ANALYSIS:
            report.update(status='complete' if verdict == 'pass' else 'blocked',
                          evidence='Synthetic recording analysis fixture; no actual listening claimed.')
        else:
            report.update(reviewed_join_ids=packet['context']['join_ids'], checks={
                name: {'status': verdict, 'method': 'direct_av', 'coverage': 'full_sequence',
                       'evidence': 'Synthetic independent full-playback attestation: ' + name}
                for name in farm.QUALITY_METHODS})
        return report

    def collect(self, key, report=None, **overrides):
        task = self.task(key)
        self.json(task['report_path'], report or self.report(key))
        receipt = {'taskId': task['task_id'], 'childThreadId': task['reviewer_id'],
                   'status': 'completed', 'hasPendingChildRuns': False,
                   'hasPendingQuestion': False, 'pendingApproval': False, **overrides}
        return farm.collect(self.run, key, self.json('transport/' + key + '.done.json', receipt))

    def analysis(self):
        farm.start('manifest.json')
        for role in farm.ANALYSIS:
            key = role + '-r1'
            self.bind(key)
            self.collect(key)

    def record_fixture(self, version='v1'):
        media = ap.fingerprint('Assets/source.mov')
        transcript = {'source_id': 'a', 'media_sha256': media['sha256'],
                      'revision': 'r1', 'mode': 'verified_recording',
                      'words': [{'id': 'w1', 'text': 'Hello', 'start': '0', 'end': '1/2'},
                                {'id': 'w2', 'text': 'goodbye.', 'start': '2', 'end': '5/2'}],
                      'ending_word_ids': ['w2']}
        self.json('transcript.json', transcript)
        desc = dict(ap.fingerprint('transcript.json'), revision='r1')
        self.plan = {'version': 1, 'mode': 'verified_recording', 'frame_rate': '30',
                     'transcripts': {'a': desc}, 'omissions': [], 'ranges': [
                         {'source_id': 'a', 'source_sha256': media['sha256'],
                          'sourceIn': str(a), 'sourceOut': str(a + 1),
                          'timelineIn': str(t), 'timelineOut': str(t + 1),
                          'word_ids': [word], 'reason': 'Retain complete spoken occurrence',
                          'linked_av': True} for a, t, word in [(0, 0, 'w1'), (2, 1, 'w2')]]}
        self.json('decisions.json', self.plan)
        epoch = writer.claim(*self.writer_args)['epoch']
        self.json('intent.json', {'operation': 'apply EDL', 'decisions': 'decisions.json'})
        operation = writer.begin(*self.writer_args, epoch, 'intent.json')
        self.json('receipt.json', {'operation_id': operation['operation_id'], 'status': 'completed'})
        self.json('snapshot.json', {'sequence_id': 'seq-fixture', 'duration': '2', 'ranges': self.plan['ranges']})
        writer.resolve(*self.writer_args, epoch, operation['operation_id'],
                       'receipt.json', 'snapshot.json', 'verified')
        record = {'producer_id': 'parent-thread', 'project': 'project.prproj', 'writer_epoch': epoch,
                  'sequence_id': 'seq-fixture', 'edit_version': version, 'transcripts': {'a': desc},
                  'decisions': 'decisions.json', 'snapshot': 'snapshot.json',
                  'operation_receipts': ['receipt.json'], 'delivery': {
                      'width': 1280, 'height': 720, 'frame_rate': '30', 'audio_required': True,
                      'output': 'Exports/' + version + '.mp4'}}
        self.json('record.json', record)
        return record

    def edited(self):
        self.analysis()
        self.record_fixture()
        farm.record_edit(self.run, 'record.json')
        return self.state()['quality_task']

    def reviewed(self):
        key = self.edited()
        self.bind(key)
        self.collect(key)
        return self.state()['edit']['hash']

    def approved(self):
        edit_hash = self.reviewed()
        farm.approve_export(self.run, edit_hash, 'user-message:fixture-exact-v1-export-approval')

    def queued(self):
        self.approved()
        self.json('render-start.json', {'job_id': 'render-1', 'status': 'queued'})
        self.json('export-intent.json', {'kind': 'export'})
        operation = farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')['writer']
        farm.writer_command(self.run, 'resolve-operation', 'parent-thread', operation=operation['operation_id'],
                            receipt='render-start.json', snapshot='snapshot.json', outcome='verified')
        farm.render_started(self.run, 'render-start.json')
        self.json('render-done.json', {'job_id': 'render-1', 'status': 'completed'})

    def rendered(self):
        self.queued()
        self.bytes('Exports/v1.mp4', b'temporary output fixture bytes, not real video')
        farm.verify_render(self.run, 'render-done.json')
        return self.state()['quality_task']

    def test_stale_review_failure_does_not_erase_render(self):
        old = self.edited(); self.bind(old)
        self.record_fixture('v2'); farm.record_edit(self.run, 'record.json')
        current = self.state()['quality_task']; self.bind(current); self.collect(current)
        farm.approve_export(self.run, self.state()['edit']['hash'], 'user:approved-v2')
        self.json('export-intent.json', {'kind': 'export'})
        op = farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')['writer']
        self.json('accepted.json', {'job_id': 'actual-job-2'})
        farm.writer_command(self.run, 'resolve-operation', 'parent-thread', operation=op['operation_id'],
                            receipt='accepted.json', snapshot='snapshot.json', outcome='verified')
        before = self.state()['render']
        self.assertEqual(self.collect(old, report={'unused': True}, status='failed')['phase'], 'render_pending')
        self.assertEqual(before, self.state()['render'])
        self.assertEqual(self.task(old)['verdict'], 'obsolete')
        with self.assertRaises(ValueError): farm.record_edit(self.run, 'record.json')

    def test_export_acceptance_is_durable_without_render_started(self):
        self.queued()
        self.assertEqual(self.state()['phase'], 'render_pending')
        with self.assertRaises(ValueError):
            farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')

    def test_export_resolution_interruption_cannot_resubmit(self):
        self.approved(); self.json('export-intent.json', {'kind': 'export'})
        op = farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')['writer']
        self.json('accepted.json', {'job_id': 'actual-job'})
        original_save = farm.save
        def fail_after_journal(path, value):
            if str(path).endswith('state.json') and value.get('phase') == 'render_pending':
                raise OSError('simulated process interruption')
            return original_save(path, value)
        with patch.object(farm, 'save', side_effect=fail_after_journal):
            with self.assertRaises(OSError):
                farm.writer_command(self.run, 'resolve-operation', 'parent-thread', operation=op['operation_id'],
                                    receipt='accepted.json', snapshot='snapshot.json', outcome='verified')
        self.assertIsNone(writer.inspect('project.prproj')['pending'])
        self.assertEqual(self.state()['phase'], 'export_submitting')
        with self.assertRaises(ValueError):
            farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')
        farm.render_started(self.run, 'accepted.json')
        self.assertEqual(self.state()['phase'], 'render_pending')

    def test_writer_requires_actual_caller_and_status_never_claims(self):
        farm.start('manifest.json')
        self.assertIsNone(writer.inspect('project.prproj'))
        with self.assertRaises(ValueError):
            farm.writer_command(self.run, 'claim-writer', 'different-thread')
        self.assertIsNone(writer.inspect('project.prproj'))
        farm.writer_command(self.run, 'claim-writer', 'parent-thread')
        for action in ('begin-operation', 'resolve-operation', 'release-writer'):
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, 'invoking coordinator'):
                farm.writer_command(self.run, action, 'different-thread')
        writer.release(*self.writer_args, 1)
        with self.assertRaises(ValueError): farm.idle_writer(self.state())
        self.assertIsNone(writer.inspect('project.prproj')['owner_id'])

    def test_terminal_render_failure_preserves_attempt_and_requires_fresh_version(self):
        self.queued(); render = self.state()['render']
        evidence = {'operation_id': render['operation_id'], 'edit_hash': self.state()['edit']['hash'],
                    'output': render['output'], 'status': 'failed', 'host_terminal': True,
                    'host_evidence': {'job_id': 'render-1', 'status': 'failed'}, 'reason': 'Actual host failure fixture'}
        for changed in ({'status': 'unknown'}, {'host_terminal': False}, {'operation_id': 'wrong'}):
            self.json('failure.json', dict(evidence, **changed))
            with self.assertRaises(ValueError):
                farm.reconcile_render_failure(self.run, 'failure.json', 'parent-thread')
            self.assertEqual(self.state()['phase'], 'render_pending')
        self.bytes(render['output'], b'failed output remains intact')
        self.json('failure.json', evidence)
        farm.reconcile_render_failure(self.run, 'failure.json', 'parent-thread')
        self.assertEqual(self.state()['phase'], 'render_failed')
        history = self.state()['render_history']
        self.assertEqual(history[0]['render'], render)
        self.assertEqual(history[0]['output'], ap.fingerprint(render['output']))
        with self.assertRaises(ValueError):
            farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')
        self.record_fixture('v2'); farm.record_edit(self.run, 'record.json')
        self.assertEqual(self.state()['phase'], 'assembled_review')
        self.assertEqual(self.state()['render_history'], history)

    def test_interrupted_failure_archive_can_finish_without_overwrite(self):
        self.queued(); state = self.state()
        evidence = {'operation_id': state['render']['operation_id'], 'edit_hash': state['edit']['hash'],
                    'output': state['render']['output'], 'status': 'cancelled', 'host_terminal': True,
                    'host_evidence': {'job_id': 'render-1', 'status': 'cancelled'}, 'reason': 'Confirmed cancelled'}
        self.json('failure.json', evidence)
        original_save = farm.save
        def interrupted(path, value):
            if str(path).endswith('state.json') and value.get('phase') == 'render_failed':
                raise OSError('interrupted after failure archive')
            return original_save(path, value)
        with patch.object(farm, 'save', side_effect=interrupted):
            with self.assertRaises(OSError):
                farm.reconcile_render_failure(self.run, 'failure.json', 'parent-thread')
        self.assertEqual(self.state()['phase'], 'render_pending')
        self.json('conflict.json', dict(evidence, reason='different evidence'))
        with self.assertRaisesRegex(ValueError, 'Conflicting archived'):
            farm.reconcile_render_failure(self.run, 'conflict.json', 'parent-thread')
        farm.reconcile_render_failure(self.run, 'failure.json', 'parent-thread')
        self.assertEqual(self.state()['phase'], 'render_failed')
        self.assertEqual(len(self.state()['render_history']), 1)

    def test_export_fence_directory_is_synced_before_writer_clear(self):
        self.approved(); self.json('export-intent.json', {'kind': 'export'})
        op = farm.writer_command(self.run, 'begin-operation', 'parent-thread', intent='export-intent.json')['writer']
        self.json('accepted.json', {'job_id': 'actual-job'})
        events = []; original_sync = farm.sync_directory; original_resolve = writer.resolve
        def synced(path):
            original_sync(path)
            if path == farm.folder(self.run): events.append('fence_synced')
        def resolved(*args):
            self.assertIn('fence_synced', events)
            self.assertEqual(self.state()['phase'], 'export_submitting')
            events.append('journal_clear')
            return original_resolve(*args)
        with patch.object(farm, 'sync_directory', side_effect=synced), patch.object(writer, 'resolve', side_effect=resolved):
            farm.writer_command(self.run, 'resolve-operation', 'parent-thread', operation=op['operation_id'],
                                receipt='accepted.json', snapshot='snapshot.json', outcome='verified')
        self.assertLess(events.index('fence_synced'), events.index('journal_clear'))
        self.assertEqual(self.state()['phase'], 'render_pending')

    def test_full_supplied_video_delivery_without_script(self):
        key = self.rendered()
        self.assertEqual(self.state()['phase'], 'delivery_review')
        self.assertIsNone(self.state()['delivered'])
        self.bind(key)
        result = self.collect(key)
        self.assertEqual(result['phase'], 'delivered_verified')
        self.assertEqual(result['sourceAuthority'], 'verified_recording')
        self.assertEqual(result['delivery']['media'], ap.fingerprint('Exports/v1.mp4'))
        self.assertEqual(result['delivery']['edit_hash'], self.state()['approval']['edit_hash'])
        self.assertEqual(self.state()['approval']['evidence_ref'], 'user-message:fixture-exact-v1-export-approval')
        self.assertEqual(len(self.state()['tasks']), 5)
        self.assertEqual(writer.claim(*self.writer_args)['pending'], None)
        self.decode.assert_called_once()

    def test_absent_script_three_tasks_and_idempotent_start(self):
        first = farm.start('manifest.json')
        originals = {k: ap.local(t['packet']['path']).read_bytes() for k, t in self.state()['tasks'].items()}
        retry = farm.start('manifest.json')
        # JSON persistence sorts mapping keys; action order is not a contract.
        first['tasks'].sort(key=lambda task: task['task'])
        retry['tasks'].sort(key=lambda task: task['task'])
        self.assertEqual(first, retry)
        self.assertEqual(len(first['tasks']), 3)
        self.assertEqual(first['max_parallel_specialists'], 3)
        for key, task in self.state()['tasks'].items():
            self.assertEqual(ap.local(task['packet']['path']).read_bytes(), originals[key])
            request = ap.load(task['request'])
            self.assertIn('clientRequestId', request)
            self.assertIn('No Premiere calls', request['task'])

    def test_source_reviews_never_pass_assembled_edit(self):
        self.analysis()
        self.assertEqual(self.state()['phase'], 'ready_for_edit')
        self.record_fixture()
        result = farm.record_edit(self.run, 'record.json')
        self.assertEqual(result['phase'], 'assembled_review')
        self.assertFalse(self.state()['edit']['decisions_summary']['audiovisual_review_verified'])
        with self.assertRaises(ValueError):
            farm.approve_export(self.run, result['edit_hash'], 'user-message:too-early')

    def test_reference_only_edl_rejected_by_actual_validator(self):
        self.analysis()
        self.record_fixture()
        reference = dict(self.plan['ranges'][0], source_id='ref', word_ids=[],
                         source_sha256=ap.fingerprint('Assets/reference.mov')['sha256'])
        self.plan['ranges'].append(reference)
        self.json('decisions.json', self.plan)
        with self.assertRaisesRegex(edit_decisions.ValidationError, 'reference-only'):
            farm.record_edit(self.run, 'record.json')

    def test_pending_writer_and_wrong_epoch_block_record_edit(self):
        self.analysis()
        record = self.record_fixture()
        for epoch in (0, 2):
            self.json('record.json', dict(record, writer_epoch=epoch))
            with self.subTest(epoch=epoch), self.assertRaises(ValueError):
                farm.record_edit(self.run, 'record.json')
        self.json('record.json', record)
        writer.begin(*self.writer_args, record['writer_epoch'], 'intent.json')
        with self.assertRaisesRegex(ValueError, 'Resolve all writer operations'):
            farm.record_edit(self.run, 'record.json')

    def test_another_writer_cannot_record_edit(self):
        self.analysis()
        self.record_fixture()
        writer.release(*self.writer_args, 1)
        writer.claim('project.prproj', 'other-run', 'other-parent')
        with self.assertRaisesRegex(ValueError, 'owned by another'):
            farm.record_edit(self.run, 'record.json')

    def test_stale_project_edit_report_source_and_packet_block_collection(self):
        key = self.edited()
        self.bind(key)
        paths = ['project.prproj', 'record.json', 'decisions.json', 'snapshot.json',
                 'receipt.json', 'transcript.json', 'Assets/source.mov',
                 self.task('dialogue-r1')['report']['path'], self.task(key)['packet']['path']]
        for path in paths:
            original = ap.local(path).read_bytes()
            self.bytes(path, original + b' ')
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.collect(key)
            self.bytes(path, original)
        self.assertEqual(self.collect(key)['phase'], 'awaiting_user_review')

    def test_sampled_still_pass_and_uncovered_joins_rejected(self):
        key = self.edited()
        self.bind(key)
        report = self.report(key)
        for name in farm.QUALITY_METHODS:
            altered = copy.deepcopy(report)
            altered['checks'][name]['method'] = 'sampled_stills'
            with self.subTest(check=name), self.assertRaisesRegex(ValueError, 'full temporal/audio'):
                self.collect(key, altered)
        report['reviewed_join_ids'] = []
        with self.assertRaisesRegex(ValueError, 'every current join'):
            self.collect(key, report)

    def test_partial_coverage_or_missing_check_cannot_pass(self):
        key = self.edited()
        self.bind(key)
        report = self.report(key)
        report['checks']['pacing_all_joins']['coverage'] = 'sampled'
        with self.assertRaises(ValueError):
            self.collect(key, report)
        del report['checks']['pacing_all_joins']
        with self.assertRaises(ValueError):
            self.collect(key, report)

    def test_task_binding_identity_completion_and_duplicate_dispatch(self):
        farm.start('manifest.json')
        key = 'dialogue-r1'
        with self.assertRaises(ValueError):
            self.bind(key, childThreadId='parent-thread')
        receipt = self.bind(key)
        self.bind(key)  # Exact retry is safe.
        for other in ({'taskId': 'duplicate'}, {'childThreadId': 'changed-child'}):
            with self.subTest(other=other), self.assertRaises(ValueError):
                self.bind(key, **other)
        with self.assertRaises(ValueError):
            self.bind('visual-r1', taskId=receipt['taskId'])
        for invalid in ({'taskId': 'wrong'}, {'childThreadId': 'wrong'}, {'status': 'running'},
                        {'hasPendingChildRuns': True}, {'hasPendingQuestion': True}, {'pendingApproval': True}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.collect(key, **invalid)
        for field, value in [('reviewer_id', 'parent-thread'), ('packet_hash', 'stale')]:
            report = self.report(key)
            report[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.collect(key, report)
        self.collect(key)
        with self.assertRaises(ValueError):
            self.collect(key)
        with self.assertRaises(ValueError):
            self.bind(key)

    def test_bounded_evidence_rereview_keeps_prior_findings(self):
        key = self.edited()
        for round_number in range(1, 4):
            self.bind(key)
            self.collect(key, self.report(key, 'uncertain'))
            evidence = self.bytes('evidence-' + str(round_number), b'new evidence ' + str(round_number).encode())
            if round_number == 3:
                with self.assertRaisesRegex(ValueError, 'three rounds'):
                    farm.rereview(self.run, key, evidence)
                break
            with self.assertRaisesRegex(ValueError, 'New evidence'):
                farm.rereview(self.run, key, 'snapshot.json')
            prior = self.task(key)['report']
            farm.rereview(self.run, key, evidence)
            key = self.state()['quality_task']
            packet = farm.packet_for(self.task(key))
            self.assertEqual(len(packet['previous_findings']), round_number)
            self.assertEqual(packet['previous_findings'][-1], prior)
            self.assertIn(ap.fingerprint(evidence), packet['inputs'])
        self.assertEqual(self.state()['phase'], 'needs_edit_review_evidence')

    def test_failed_worker_has_durable_bounded_retry(self):
        farm.start('manifest.json')
        self.bind('dialogue-r1')
        result = self.collect('dialogue-r1', status='failed')
        self.assertEqual(result['phase'], 'analysis_blocked')
        evidence = self.bytes('tool-recovery.txt', b'Prerequisite fixed; actual recovery evidence fixture')
        farm.rereview(self.run, 'dialogue-r1', evidence)
        self.assertEqual(self.task('dialogue-r2')['state'], 'pending')
        self.assertTrue(ap.local(self.task('dialogue-r1')['failure']['path']).is_file())

    def test_blocked_analysis_can_receive_new_evidence(self):
        farm.start('manifest.json')
        self.bind('dialogue-r1')
        self.collect('dialogue-r1', self.report('dialogue-r1', 'uncertain'))
        evidence = self.bytes('listening-evidence', b'new source evidence')
        farm.rereview(self.run, 'dialogue-r1', evidence)
        self.bind('dialogue-r2')
        self.collect('dialogue-r2')
        self.assertEqual(self.state()['phase'], 'analysis')
        before = self.task('dialogue-r2')
        try:
            farm.rereview(self.run, 'dialogue-r1', evidence)
        except ValueError:
            pass  # Refusal or a true no-op are both safe retry semantics.
        self.assertEqual(self.task('dialogue-r2'), before,
                         'Retry must not erase a completed child and redispatch it')

    def test_duplicate_rereview_preserves_running_transport_binding(self):
        farm.start('manifest.json')
        self.bind('dialogue-r1')
        self.collect('dialogue-r1', self.report('dialogue-r1', 'uncertain'))
        evidence = self.bytes('listening-evidence', b'additional source evidence')
        farm.rereview(self.run, 'dialogue-r1', evidence)
        self.bind('dialogue-r2')
        before = self.task('dialogue-r2')
        try:
            farm.rereview(self.run, 'dialogue-r1', evidence)
        except ValueError:
            pass
        self.assertEqual(self.task('dialogue-r2'), before,
                         'Retry must preserve active task ID and child identity')

    def test_failed_review_requires_revision_not_evidence_retry(self):
        key = self.edited()
        self.bind(key)
        self.assertEqual(self.collect(key, self.report(key, 'fail'))['phase'], 'needs_revision')
        with self.assertRaises(ValueError):
            farm.rereview(self.run, key, self.bytes('new-evidence', b'evidence'))

    def test_stale_export_approval_rejected(self):
        edit_hash = self.reviewed()
        with self.assertRaises(ValueError):
            farm.approve_export(self.run, 'old-hash', 'user-message:fixture')
        with self.assertRaises(ValueError):
            farm.approve_export(self.run, edit_hash, ' ')
        farm.approve_export(self.run, edit_hash, 'user-message:fixture-exact-v1-export-approval')
        self.bytes('project.prproj', b'changed saved project')
        self.json('render-start.json', {'status': 'queued'})
        with self.assertRaisesRegex(ValueError, 'Saved project changed'):
            farm.render_started(self.run, 'render-start.json')

    def test_new_edit_invalidates_previous_approval(self):
        self.approved()
        previous = self.state()['edit']['hash']
        self.record_fixture('v2')
        farm.record_edit(self.run, 'record.json')
        self.assertNotIn('approval', self.state())
        self.assertNotEqual(previous, self.state()['edit']['hash'])
        with self.assertRaises(ValueError):
            farm.approve_export(self.run, previous, 'user-message:old-approval')

    def test_changed_approval_receipt_blocks_render_start(self):
        self.approved()
        self.json('File/edit_farm/runs/' + self.run + '/approval-v1.json',
                  {'evidence_ref': 'user-message:changed-approval'})
        self.json('render-start.json', {'status': 'queued'})
        with self.assertRaises(ValueError):
            farm.render_started(self.run, 'render-start.json')

    def test_queued_missing_and_truncated_output_never_delivered(self):
        self.queued()
        self.assertIsNone(self.state()['delivered'])
        with self.assertRaises(FileNotFoundError):
            farm.verify_render(self.run, 'render-done.json')
        self.bytes('Exports/v1.mp4', b'truncated')
        self.decode.side_effect = subprocess.CalledProcessError(1, ['ffmpeg'], stderr=b'truncated input')
        with self.assertRaises(subprocess.CalledProcessError):
            farm.verify_render(self.run, 'render-done.json')
        self.assertEqual(self.state()['phase'], 'render_pending')
        self.assertIsNone(self.state()['delivered'])

    def test_wrong_dimensions_duration_timebase_and_missing_audio(self):
        self.queued()
        self.bytes('Exports/v1.mp4', b'fixture output')
        original = self.media_info('Exports/v1.mp4')
        mutations = [lambda x: x['streams'][0].update(width=1920, height=1080),
                     lambda x: x['format'].update(duration='1'),
                     lambda x: x['streams'][0].update(avg_frame_rate='25'),
                     lambda x: x['streams'].pop()]
        self.probe.side_effect = None
        for mutate in mutations:
            info = copy.deepcopy(original)
            mutate(info)
            self.probe.return_value = info
            with self.subTest(info=info), self.assertRaises(ValueError):
                farm.verify_render(self.run, 'render-done.json')
        self.decode.assert_not_called()

    def test_stale_render_blocks_independent_delivery_review(self):
        key = self.rendered()
        self.bind(key)
        self.bytes('Exports/v1.mp4', b'changed output')
        with self.assertRaises(ValueError):
            self.collect(key)

    def test_pending_writer_operation_blocks_export_authorization(self):
        edit_hash = self.reviewed()
        writer.begin(*self.writer_args, 1, 'intent.json')
        with self.assertRaises(ValueError, msg='Unknown live host mutation must invalidate readiness'):
            farm.approve_export(self.run, edit_hash, 'user-message:fixture-exact-v1-export-approval')

    def test_pending_writer_operation_blocks_render_start(self):
        self.approved()
        writer.begin(*self.writer_args, 1, 'intent.json')
        self.json('render-start.json', {'status': 'queued'})
        with self.assertRaises(ValueError, msg='Saved file hash cannot fence unknown live host state'):
            farm.render_started(self.run, 'render-start.json')

    def test_rejected_stale_rereview_does_not_poison_next_round(self):
        key = self.edited()
        self.bind(key)
        self.collect(key, self.report(key, 'uncertain'))
        evidence = self.bytes('new-evidence', b'additional temporal evidence')
        original = ap.local('project.prproj').read_bytes()
        self.bytes('project.prproj', b'unsaved-version mismatch fixture')
        with self.assertRaises(ValueError):
            farm.rereview(self.run, key, evidence)
        self.bytes('project.prproj', original)
        farm.rereview(self.run, key, evidence)
        self.assertEqual(self.state()['tasks']['assembled-v1-r2']['state'], 'pending')


if __name__ == '__main__':
    unittest.main()
