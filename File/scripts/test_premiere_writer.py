import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import premiere_writer as writer


class WriterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        mocked = patch.object(ap, 'ROOT', self.root)
        mocked.start()
        self.addCleanup(mocked.stop)
        self.project = self.root / 'project.prproj'
        self.project.write_bytes(b'saved project')
        for name in ('intent', 'receipt', 'snapshot'):
            (self.root / name).write_text(name + ' evidence')
        key = hashlib.sha256(str(self.project).encode()).hexdigest()
        self.state = self.root / 'File/edit_farm/writers' / (key + '.json')
        self.args = (self.project, 'run-a', 'owner-a')

    def claim(self):
        return writer.claim(*self.args)['epoch']

    def begin(self, epoch=1):
        return writer.begin(*self.args, epoch, 'intent')

    def resolve(self, op, outcome='verified', epoch=1):
        return writer.resolve(*self.args, epoch, op, 'receipt', 'snapshot', outcome)

    def test_two_runs_and_owners_collide_persistently(self):
        self.assertEqual(self.claim(), 1)
        for run, owner in [('run-b', 'owner-b'), ('run-a', 'owner-b'), ('run-b', 'owner-a')]:
            with self.assertRaises(ValueError):
                writer.claim(self.project, run, owner)
        self.assertEqual(self.claim(), 1)
        # A new process has no in-memory ownership and must still refuse.
        result = subprocess.run([sys.executable, '-B', '-c',
            'from pathlib import Path; import agentic_pipeline as ap; import premiere_writer as w; '
            'import sys; ap.ROOT=Path(sys.argv[1]); w.claim("project.prproj", "run-b", "owner-b")',
            str(self.root)], cwd=Path(__file__).parent, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('owned by another', result.stderr)

    def test_stale_fences_on_all_mutations(self):
        self.claim()
        operation = self.begin()['operation_id']
        for epoch in (0, 2, True, '1'):
            for action in (lambda: self.begin(epoch), lambda: self.resolve(operation, epoch=epoch),
                           lambda: writer.release(*self.args, epoch)):
                with self.subTest(epoch=epoch), self.assertRaises(ValueError):
                    action()
        for run, owner in [('run-b', 'owner-a'), ('run-a', 'owner-b')]:
            with self.assertRaises(ValueError):
                writer.resolve(self.project, run, owner, 1, operation,
                               'receipt', 'snapshot', 'verified')

    def test_unknown_blocks_begin_release_and_reclaim_recovery(self):
        self.claim()
        pending = self.begin()
        record = writer.resolve(*self.args, 1, pending['operation_id'], None, None, 'unknown')
        self.assertEqual(record['pending'], pending)
        self.assertEqual(writer.claim(*self.args)['pending'], pending)
        with self.assertRaises(ValueError):
            self.begin()
        with self.assertRaises(ValueError):
            writer.release(*self.args, 1)
        record = self.resolve(pending['operation_id'])
        self.assertIsNone(record['pending'])
        self.assertEqual([e['outcome'] for e in record['history'] if e['event'] == 'resolve'],
                         ['unknown', 'verified'])

    def test_exact_operation_only_no_replay(self):
        self.claim()
        first = self.begin()['operation_id']
        before = self.state.read_bytes()
        with self.assertRaises(ValueError):
            self.resolve('invented-operation')
        self.assertEqual(self.state.read_bytes(), before)
        self.resolve(first)
        with self.assertRaises(ValueError):
            self.resolve(first)
        second = self.begin()['operation_id']
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            self.resolve(first)
        self.assertIsNone(self.resolve(second, 'no_effect')['pending'])

    def test_verified_known_atomic_project_save_can_reconcile(self):
        self.claim()
        (self.root / 'intent').write_text(json.dumps({'kind': 'save_project',
            'expected_project_path': str(self.project), 'expected_project_id': 'host-project-1'}))
        pending = self.begin()
        temporary = self.root / 'saved.tmp'; temporary.write_bytes(b'updated project')
        temporary.replace(self.project)
        with self.assertRaises(ValueError): self.claim()
        (self.root / 'snapshot').write_text(json.dumps({'project_path': str(self.project),
            'project_id': 'host-project-1', 'saved': True, 'host_evidence': {'fixture': 'readback'}}))
        result = self.resolve(pending['operation_id'])
        self.assertIsNone(result['pending'])
        self.assertEqual(self.claim(), 1)
        self.assertTrue(any(h['event'] == 'verified_atomic_save' for h in result['history']))

    def test_release_reclaim_preserves_history_and_increases_epoch(self):
        self.claim()
        operation = self.begin()['operation_id']
        resolved = self.resolve(operation)
        released = writer.release(*self.args, 1)
        self.assertEqual(released['epoch'], 1)
        self.assertIsNone(released['owner_id'])
        self.assertEqual(released['history'][:-1], resolved['history'])
        self.assertEqual(self.claim(), 2)
        with self.assertRaises(ValueError):
            self.begin(1)
        writer.release(*self.args, 2)
        self.assertEqual(writer.claim(self.project, 'run-b', 'owner-b')['epoch'], 3)

    def test_archives_preserve_original_bytes_and_fingerprints(self):
        self.claim()
        pending = self.begin()
        self.assertEqual(pending['intent']['source'], ap.fingerprint('intent'))
        record = self.resolve(pending['operation_id'])
        evidence = [pending['intent'], record['history'][-1]['receipt'],
                    record['history'][-1]['snapshot']]
        for item in evidence:
            original = ap.local(item['source']['path']).read_bytes()
            ap.local(item['source']['path']).write_bytes(b'changed')
            self.assertEqual(ap.local(item['archive']['path']).read_bytes(), original)
            self.assertEqual(ap.fingerprint(item['archive']['path']), item['archive'])

    def test_changed_identity_fails_closed_but_content_edits_are_allowed(self):
        self.claim()
        self.project.write_bytes(b'edited in place')
        self.assertEqual(self.claim(), 1)
        replacement = self.root / 'new.prproj'
        replacement.write_bytes(b'replacement')
        replacement.replace(self.project)
        for action in (self.claim, self.begin, lambda: writer.release(*self.args, 1)):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                action()

    def test_canonical_aliases_share_lock(self):
        alias = self.root / 'alias.prproj'
        alias.symlink_to(self.project)
        self.claim()
        with self.assertRaises(ValueError):
            writer.claim(alias, 'run-b', 'owner-b')
        self.assertEqual(writer.claim(alias, 'run-a', 'owner-a')['epoch'], 1)
        self.assertEqual(len(list(self.state.parent.glob('*.json'))), 1)

    def test_flock_blocks_concurrent_state_access(self):
        self.claim()
        with self.state.with_suffix('.lock').open('rb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, 'busy'):
                self.claim()
        self.assertEqual(self.claim(), 1)

    def test_input_validation_and_required_resolution_evidence(self):
        for bad in ('', '  ', None, 1, 'line\nbreak'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                writer.claim(self.project, bad, 'owner-a')
        (self.root / 'empty.prproj').touch()
        for bad in ('', None, '../outside.prproj', 'missing.prproj', 'intent', 'empty.prproj', '.'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                writer.claim(bad, 'run-a', 'owner-a')
        with self.assertRaises(ValueError):
            self.begin()
        self.claim()
        for bad in ('', None, 'missing', '.', '../outside'):
            with self.assertRaises(ValueError):
                writer.begin(*self.args, 1, bad)
        operation = self.begin()['operation_id']
        for outcome in ('success', '', None):
            with self.assertRaises(ValueError):
                self.resolve(operation, outcome)
        for outcome in ('verified', 'no_effect'):
            for receipt, snapshot in [(None, 'snapshot'), ('receipt', None),
                                      ('empty.prproj', 'snapshot'), ('receipt', 'missing')]:
                with self.assertRaises(ValueError):
                    writer.resolve(*self.args, 1, operation, receipt, snapshot, outcome)
        self.assertIsNotNone(json.loads(self.state.read_text())['pending'])

    def test_invalid_or_redirected_state_is_not_reset(self):
        self.claim()
        self.state.write_text('{}')
        with self.assertRaises(ValueError):
            self.claim()
        self.state.unlink()
        self.state.symlink_to(self.root / 'receipt')
        with self.assertRaises(ValueError):
            self.claim()


if __name__ == '__main__':
    unittest.main()
