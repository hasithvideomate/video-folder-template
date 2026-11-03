#!/usr/bin/env python3
"""Pull the team's latest shared rules, skills, docs and helpers into this project.

Only allowlisted shared paths are ever written. Project media, notes, memory, briefs,
Premiere/After Effects projects, job/run records and credentials are never touched.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE_CONFIG = 'File/template_source.json'
STATE = 'File/.template_sync.json'
CACHE = Path(os.environ.get('TEMPLATE_CACHE', Path.home() / '.cache' / 'video-folder-template'))

# Shared, reusable files. Everything else belongs to the individual project.
SHARED = ('AGENTS.md', '.agents/skills', 'File/docs', 'File/scripts', 'File/agents.md',
          'File/pacing_policy.json', 'File/repair_defaults.json', 'File/README.md',
          'File/START_HERE.md', 'File/template_source.json', '.env.example', '.gitignore')
NEVER = ('.env', '.env.local', '.git')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shared_files(base):
    found = {}
    for entry in SHARED:
        path = base / entry
        items = [path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else []
        for item in items:
            rel = item.relative_to(base).as_posix()
            parts = rel.split('/')
            if (item.is_symlink() or any(p in NEVER or p.startswith('.env') for p in parts)
                    or item.name == '.DS_Store' or '__pycache__' in parts or item.suffix == '.pyc'):
                continue
            found[rel] = item
    return found


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True,
                          timeout=120).stdout.strip()


MASTER_MARKER = 'File/.template_master'


def is_master():
    """The master working copy (marked by an untracked, gitignored file) publishes; it never pulls into itself.

    A project cloned from the repo has .git too, so .git alone does not identify the master."""
    return (ROOT / MASTER_MARKER).exists()


def fetch_source(config):
    repo, branch = config['repo'], config.get('branch', 'main')
    if not repo or repo.startswith('REPLACE'):
        raise SystemExit('Set the team repository in File/template_source.json first.')
    folder = CACHE / hashlib.sha256(repo.encode()).hexdigest()[:16]
    if (folder / '.git').exists():
        git('fetch', '--depth', '1', 'origin', branch, cwd=folder)
        git('reset', '--hard', 'FETCH_HEAD', cwd=folder)
    else:
        folder.parent.mkdir(parents=True, exist_ok=True)
        git('clone', '--depth', '1', '--branch', branch, repo, str(folder))
    git('clean', '-fdx', cwd=folder)
    return folder, git('rev-parse', 'HEAD', cwd=folder)


def plan(source, state):
    """Return installs, removals and conflicts (locally edited shared files are never overwritten)."""
    installed = state.get('files', {})
    incoming = shared_files(source)
    local = shared_files(ROOT)
    first_sync = not installed
    install, remove, conflicts = [], [], []
    for rel, path in incoming.items():
        new = sha(path)
        current = sha(local[rel]) if rel in local else None
        if current == new:
            continue
        locally_edited = current is not None and not first_sync and current != installed.get(rel)
        (conflicts if locally_edited else install).append(rel)
    for rel in installed:
        if rel not in incoming and rel in local:
            (remove if sha(local[rel]) == installed[rel] else conflicts).append(rel)
    return incoming, install, remove, conflicts


def update(check=False, force=False, run_tests=True):
    if is_master():
        return {'status': 'master', 'note': 'This is the master working copy; publish with git instead.'}
    config = json.loads((ROOT / SOURCE_CONFIG).read_text(encoding='utf-8'))
    state_path = ROOT / STATE
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    try:
        source, commit = fetch_source(config)
    except (subprocess.SubprocessError, OSError) as error:
        return {'status': 'offline', 'note': 'Could not reach the team template; nothing changed.',
                'errorType': type(error).__name__}
    incoming, install, remove, conflicts = plan(source, state)
    if force:
        install += [c for c in conflicts if c in incoming]
        remove += [c for c in conflicts if c not in incoming]
        conflicts = []
    result = {'status': 'up_to_date' if not (install or remove) else 'update_available',
              'commit': commit, 'previousCommit': state.get('commit'),
              'install': install, 'remove': remove, 'conflicts': conflicts}
    if check or not (install or remove):
        if not check and commit != state.get('commit') and not conflicts:
            save_state(state_path, commit, incoming, state, conflicts)
        return result
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'File' / 'template_backups' / stamp
    for rel in install + remove:
        target = ROOT / rel
        if target.exists():
            (backup / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup / rel)
    for rel in install:
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + '.template-tmp')
        shutil.copy2(incoming[rel], tmp)
        os.replace(tmp, target)
    for rel in remove:
        (ROOT / rel).unlink()
    save_state(state_path, commit, incoming, state, conflicts)
    result.update(status='updated', backup=str(backup.relative_to(ROOT)) if backup.exists() else None)
    if run_tests and (ROOT / 'File/scripts').is_dir():
        run = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'File/scripts', '-p', 'test_*.py'],
                             cwd=ROOT, capture_output=True, text=True, timeout=600)
        result['tests'] = 'passed' if run.returncode == 0 else 'FAILED'
        if run.returncode:
            result['testOutput'] = run.stderr[-2000:]
    return result


def save_state(path, commit, incoming, previous, conflicts):
    files = {rel: sha(p) for rel, p in incoming.items()}
    # Keep the last-installed hash for skipped conflicts so they keep being reported.
    for rel in conflicts:
        if rel in previous.get('files', {}):
            files[rel] = previous['files'][rel]
        else:
            files.pop(rel, None)
    path.write_text(json.dumps({'commit': commit, 'syncedAt': datetime.now(timezone.utc).isoformat(),
                                'files': files}, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Report available changes without writing')
    parser.add_argument('--force', action='store_true', help='Also overwrite locally edited shared files (backed up)')
    parser.add_argument('--no-tests', action='store_true')
    args = parser.parse_args()
    print(json.dumps(update(args.check, args.force, not args.no_tests), indent=2))


if __name__ == '__main__':
    main()
