"""Offline: a local git repository stands in for the team template."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import update_template as up


def run(*args, cwd):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.master, self.project = base / 'master', base / 'project'
        for folder in (self.master, self.project):
            (folder / 'File/scripts').mkdir(parents=True)
        self.write(self.master, 'AGENTS.md', 'rule v1')
        self.write(self.master, '.agents/skills/a/SKILL.md', 'skill v1')
        self.write(self.master, 'File/docs/X.md', 'doc v1')
        self.write(self.master, 'File/memory.md', 'MASTER MEMORY MUST NOT COPY')
        run('init', '-q', '-b', 'main', cwd=self.master)
        run('-c', 'user.email=t@t', '-c', 'user.name=t', 'add', '-A', cwd=self.master)
        self.commit('v1')
        self.write(self.project, 'File/template_source.json', json.dumps({'repo': str(self.master), 'branch': 'main'}))
        self.write(self.project, 'File/memory.md', 'project memory')
        self.write(self.project, '.env', 'KIE_API_KEY=secret')
        self.write(self.project, 'Assets/clip.mp4', 'media')
        for name, value in (('ROOT', self.project), ('CACHE', base / 'cache')):
            p = patch.object(up, name, value); p.start(); self.addCleanup(p.stop)

    def write(self, root, rel, text):
        path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)

    def commit(self, message):
        run('-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', message, cwd=self.master)

    def read(self, rel):
        return (self.project / rel).read_text()

    def test_first_sync_installs_shared_files_only(self):
        result = up.update(run_tests=False)
        self.assertEqual(result['status'], 'updated')
        self.assertEqual(self.read('AGENTS.md'), 'rule v1')
        self.assertEqual(self.read('.agents/skills/a/SKILL.md'), 'skill v1')
        self.assertEqual(self.read('File/memory.md'), 'project memory')
        self.assertEqual(self.read('.env'), 'KIE_API_KEY=secret')
        self.assertEqual(self.read('Assets/clip.mp4'), 'media')

    def test_new_rule_and_skill_arrive_on_next_update(self):
        up.update(run_tests=False)
        self.write(self.master, 'AGENTS.md', 'rule v2')
        self.write(self.master, '.agents/skills/b/SKILL.md', 'new skill')
        run('add', '-A', cwd=self.master); self.commit('v2')
        self.assertEqual(up.update(check=True, run_tests=False)['status'], 'update_available')
        self.assertEqual(self.read('AGENTS.md'), 'rule v1')
        result = up.update(run_tests=False)
        self.assertEqual(self.read('AGENTS.md'), 'rule v2')
        self.assertEqual(self.read('.agents/skills/b/SKILL.md'), 'new skill')
        self.assertTrue((self.project / result['backup'] / 'AGENTS.md').exists())
        self.assertEqual(up.update(run_tests=False)['status'], 'up_to_date')

    def test_local_edit_is_kept_and_reported(self):
        up.update(run_tests=False)
        self.write(self.project, 'File/docs/X.md', 'project-specific tweak')
        self.write(self.master, 'File/docs/X.md', 'doc v2'); self.commit('v2')
        result = up.update(run_tests=False)
        self.assertEqual(result['conflicts'], ['File/docs/X.md'])
        self.assertEqual(self.read('File/docs/X.md'), 'project-specific tweak')
        self.assertEqual(up.update(run_tests=False)['conflicts'], ['File/docs/X.md'])
        up.update(force=True, run_tests=False)
        self.assertEqual(self.read('File/docs/X.md'), 'doc v2')

    def test_removed_upstream_file_is_removed_when_unedited(self):
        up.update(run_tests=False)
        run('rm', '-q', 'File/docs/X.md', cwd=self.master); self.commit('drop')
        result = up.update(run_tests=False)
        self.assertEqual(result['remove'], ['File/docs/X.md'])
        self.assertFalse((self.project / 'File/docs/X.md').exists())

    def test_offline_changes_nothing(self):
        self.write(self.project, 'File/template_source.json', json.dumps({'repo': str(self.master) + '-missing'}))
        self.assertEqual(up.update(run_tests=False)['status'], 'offline')
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_master_never_pulls_into_itself(self):
        (self.project / '.git').mkdir()
        self.assertEqual(up.update(run_tests=False)['status'], 'master')


if __name__ == '__main__': unittest.main()
