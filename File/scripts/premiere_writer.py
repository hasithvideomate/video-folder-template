"""Durable cooperative writer fencing; no host, credential or network calls.

Only cooperating callers are fenced. Call begin BEFORE invoking the host and
resolve only after inspecting its result. Outcomes are caller attestations, not
proof supplied by this helper. Ownership never expires. Replacing the saved
project's inode fails closed except for a verified pending save_project with
matching host project identity and archived evidence; edits to the same file are allowed. Never delete lock/state files to recover an unknown call.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import agentic_pipeline as ap
from kie_tasks import replace


def _id(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 256 or any(
            ord(c) < 32 for c in value):
        raise ValueError('Expected a nonempty ID of at most 256 printable characters')
    return value


def _file(name):
    if not isinstance(name, (str, Path)) or not str(name).strip():
        raise ValueError('Expected a local file path')
    path = ap.local(name)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError('Expected a nonempty local file: ' + str(path))
    return path


def _identity(path):
    stat = path.stat()
    return {'device': stat.st_dev, 'inode': stat.st_ino,
            'birthtime': getattr(stat, 'st_birthtime', None)}


def _sync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _directory(path):
    # State must not be redirected into another project's writer namespace.
    for part in [*reversed(path.parents), path]:
        if part == ap.ROOT or ap.ROOT not in part.parents:
            continue
        if part.is_symlink():
            raise ValueError('Symlinked writer directory')
        if not part.exists():
            part.mkdir(mode=0o700, exist_ok=True)
            _sync_dir(part.parent)


def _save(path, record):
    replace(path, record)
    _sync_dir(path.parent)


@contextmanager
def _locked(project_path, allow_saved_replacement=False):
    project = _file(project_path)
    if project.suffix.lower() != '.prproj':
        raise ValueError('Expected an existing saved .prproj')
    folder = ap.ROOT / 'File/edit_farm/writers'
    _directory(folder)
    key = hashlib.sha256(str(project).encode('utf-8')).hexdigest()
    state = folder / (key + '.json')
    # This inode is permanent: never flock the atomically replaced JSON file.
    with os.fdopen(os.open(str(folder / (key + '.lock')),
                           os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'r+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Writer state is busy') from None
        try:
            if state.is_symlink():
                raise ValueError('Symlinked writer record')
            identity = _identity(_file(project))
            record = None
            if state.exists():
                record = json.loads(state.read_text(encoding='utf-8'))
                if (not isinstance(record, dict) or record.get('version') != 1
                        or type(record.get('epoch')) is not int or record['epoch'] < 1
                        or not isinstance(record.get('history'), list)
                        or not {'run_id', 'owner_id', 'pending'} <= record.keys()):
                    raise ValueError('Invalid writer record; manual inspection required')
                if record.get('project_path') != str(project):
                    raise ValueError('Saved project identity changed')
                if record.get('identity') != identity and not allow_saved_replacement:
                    raise ValueError('Saved project identity changed; reconcile a known save before continuing')
                if record['run_id'] is None:
                    if record['owner_id'] is not None or record['pending'] is not None:
                        raise ValueError('Invalid released writer record')
                else:
                    _id(record['run_id'])
                    _id(record['owner_id'])
                pending = record['pending']
                if pending is not None and (not isinstance(pending, dict)
                        or not {'operation_id', 'epoch', 'intent'} <= pending.keys()
                        or pending['epoch'] != record['epoch']):
                    raise ValueError('Invalid pending operation')
            yield state, record, project, identity
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _owned(record, run_id, owner_id, epoch):
    _id(run_id)
    _id(owner_id)
    if type(epoch) is not int or epoch < 1:
        raise ValueError('Expected a positive integer epoch')
    if record is None or (record['run_id'], record['owner_id'], record['epoch']) != (
            run_id, owner_id, epoch):
        raise ValueError('Writer ownership or epoch mismatch')


def _archive(state, name, label):
    source = _file(name)
    fingerprint = ap.fingerprint(source)
    folder = state.with_suffix('.evidence')
    _directory(folder)
    target = folder / (uuid.uuid4().hex + '-' + label)
    with target.open('xb') as out, source.open('rb') as incoming:
        shutil.copyfileobj(incoming, out)
        out.flush()
        os.fsync(out.fileno())
    copied = ap.fingerprint(target)
    if copied['sha256'] != fingerprint['sha256'] or ap.fingerprint(source) != fingerprint:
        raise ValueError('Evidence changed while being archived')
    _sync_dir(folder)
    return {'source': fingerprint, 'archive': copied}


def inspect(project_path, allow_saved_replacement=False):
    """Read ownership without implicitly claiming it for a stored identity."""
    with _locked(project_path, allow_saved_replacement) as (_, record, __, ___):
        return record


def claim(project_path, run_id, owner_id):
    """Return ownership record. Same-owner retries preserve epoch and pending work."""
    _id(run_id)
    _id(owner_id)
    with _locked(project_path) as (state, record, project, identity):
        if record is not None and record['run_id'] is not None:
            if (record['run_id'], record['owner_id']) != (run_id, owner_id):
                raise ValueError('Project is owned by another run/owner')
            return record
        if record is None:
            record = {'version': 1, 'project_path': str(project), 'identity': identity,
                      'epoch': 0, 'pending': None, 'history': []}
        record.update(run_id=run_id, owner_id=owner_id, epoch=record['epoch'] + 1)
        record['history'].append({'event': 'claim', 'run_id': run_id,
                                  'owner_id': owner_id, 'epoch': record['epoch']})
        _save(state, record)
        return record


def begin(project_path, run_id, owner_id, epoch, intent_path):
    """Persist and return pending intent with a fresh local operation_id before host work."""
    with _locked(project_path) as (state, record, _, __):
        _owned(record, run_id, owner_id, epoch)
        if record['pending'] is not None:
            raise ValueError('Unresolved operation blocks all new host work')
        pending = {'operation_id': uuid.uuid4().hex, 'epoch': epoch,
                   'intent': _archive(state, intent_path, 'intent'), 'outcome': 'unknown'}
        record['pending'] = pending
        record['history'].append({'event': 'begin', **pending})
        _save(state, record)
        return pending


def resolve(project_path, run_id, owner_id, epoch, operation_id,
            receipt_path, snapshot_path, outcome):
    """Return record; only verified/no_effect with both files clear exact pending ID.

    unknown may use None for unavailable evidence and always retains the block.
    Evidence is archived locally; callers must verify its meaning against the
    intent and actual host state. Duplicate/stale resolutions are refused.
    """
    _id(operation_id)
    if outcome not in ('verified', 'no_effect', 'unknown'):
        raise ValueError('Expected verified, no_effect or unknown outcome')
    with _locked(project_path, allow_saved_replacement=True) as (state, record, project, identity):
        _owned(record, run_id, owner_id, epoch)
        pending = record['pending']
        if pending is None or pending['operation_id'] != operation_id:
            raise ValueError('Resolution must match the exact pending operation')
        if outcome != 'unknown':
            _file(receipt_path)
            _file(snapshot_path)
        if record['identity'] != identity:
            archived_intent = pending['intent']['archive']
            if ap.fingerprint(archived_intent['path']) != archived_intent:
                raise ValueError('Archived save intent changed')
            intent = json.loads(ap.local(archived_intent['path']).read_text())
            if (outcome != 'verified' or intent.get('kind') != 'save_project'
                    or intent.get('expected_project_path') != str(project)):
                raise ValueError('Changed project file requires a verified pending save_project')
            expected_id = _id(intent.get('expected_project_id'))
            snapshot = json.loads(_file(snapshot_path).read_text())
            if (snapshot.get('project_path') != str(project) or snapshot.get('project_id') != expected_id
                    or snapshot.get('saved') is not True or not snapshot.get('host_evidence')):
                raise ValueError('Atomic save requires matching fresh host identity/evidence')
            record['history'].append({'event': 'verified_atomic_save', 'old_identity': record['identity'],
                                      'new_identity': identity, 'project_id': expected_id})
            record['identity'] = identity
        evidence = {label: _archive(state, name, label) if name is not None else None
                    for label, name in [('receipt', receipt_path), ('snapshot', snapshot_path)]}
        record['history'].append({'event': 'resolve', 'operation_id': operation_id,
                                  'epoch': epoch, 'outcome': outcome, **evidence})
        if outcome != 'unknown':
            record['pending'] = None
        _save(state, record)
        return record


def release(project_path, run_id, owner_id, epoch):
    """Release only idle ownership, preserving epoch, archived evidence and history."""
    with _locked(project_path) as (state, record, _, __):
        _owned(record, run_id, owner_id, epoch)
        if record['pending'] is not None:
            raise ValueError('Cannot release an unresolved operation')
        record['history'].append({'event': 'release', 'epoch': epoch,
                                  'run_id': run_id, 'owner_id': owner_id})
        record.update(run_id=None, owner_id=None)
        _save(state, record)
        return record
