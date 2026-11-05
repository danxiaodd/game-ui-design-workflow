#!/usr/bin/env python3
"""Versioned visual workflow journal. Approvals require recorded user evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone

KINDS = ('brief', 'direction', 'concept', 'page', 'component', 'delivery')
ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(project, state):
    path = Path(project) / 'workflow-state.json'
    with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8', delete=False) as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write('\n')
        temp = f.name
    os.replace(temp, path)


def load(project):
    state = json.loads((Path(project) / 'workflow-state.json').read_text(encoding='utf-8'))
    if state.get('schema_version') != 1:
        raise ValueError('unsupported state version')
    if not isinstance(state.get('sources'), list) or not isinstance(state.get('artifacts'), dict) or not isinstance(state.get('capabilities'), dict) or not isinstance(state.get('events'), list):
        raise ValueError('invalid state structure')
    visiting, done = set(), set()
    def visit(key):
        if key in visiting or key not in state['artifacts']:
            raise ValueError('cycle or missing artifact parent')
        if key in done:
            return
        visiting.add(key)
        item = state['artifacts'][key]
        if not isinstance(item, dict) or item.get('kind') not in KINDS or item.get('status') not in ('review', 'approved', 'pending-generation', 'pending-transfer'):
            raise ValueError('invalid artifact kind/status')
        for field in ('path', 'prompt'):
            if item.get(field):
                path = (Path(project) / item[field]).resolve()
                if not path.is_relative_to(Path(project).resolve()):
                    raise ValueError('artifact files must stay in project')
        for parent in item.get('parents', []):
            visit(parent)
        visiting.remove(key); done.add(key)
    for key in state['artifacts']:
        visit(key)
    return state


def source_snapshot(state):
    return {s['path']: s['sha256'] for s in state['sources']}


def sources_match(snapshot):
    return all(Path(p).is_file() and digest(p) == value for p, value in snapshot.items())


def register_source(project, path, evidence, role='game-rules'):
    if not evidence.strip():
        raise ValueError('source registration/review requires evidence')
    state = load(project)
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError('source must be a file')
    item = {'path': str(path), 'sha256': digest(path), 'authority': role,
            'read_status': 'read', 'read_evidence': evidence, 'at': now()}
    state['sources'] = [s for s in state['sources'] if s['path'] != str(path)] + [item]
    state['events'].append({'at': now(), 'action': 'source-reviewed', **item})
    save(project, state)
    return item


def initialize(project, sources=()):
    project = Path(project).resolve()
    if (project / 'workflow-state.json').exists():
        return load(project)  # resume is idempotent; never reset decisions
    refs = []
    for source in sources:
        path = Path(source).resolve(strict=True)
        if not path.is_file():
            raise ValueError('source must be a file')
        refs.append({'path': str(path), 'sha256': digest(path), 'authority': 'game-rules',
                     'read_status': 'registered-not-yet-read'})
    project.mkdir(parents=True, exist_ok=True)
    state = {'schema_version': 1, 'sources': refs, 'capabilities': {}, 'artifacts': {}, 'events': []}
    save(project, state)
    return state


def approved(project, state, key):
    item = state['artifacts'].get(key, {})
    path = Path(project) / item.get('path', '__missing__')
    prompt = Path(project) / item.get('prompt', '__missing__')
    prompt_ok = not item.get('prompt') or (prompt.is_file() and digest(prompt) == item['prompt_sha256'])
    return item.get('status') == 'approved' and path.is_file() and digest(path) == item.get('sha256') and prompt_ok and sources_match(item.get('sources', {})) and item.get('sources', {}) == source_snapshot(state) and all(
        approved(project, state, parent) for parent in item.get('parents', []))


def record(project, key, kind, file=None, prompt=None, parents=(), direct_reason=None, tool='none', model='unknown', origin='generated', result_ref=None, based_on=None):
    project = Path(project).resolve()
    state = load(project)
    if not sources_match(source_snapshot(state)):
        raise ValueError('source changed; read and register its new version first')
    if kind not in KINDS or not ID.fullmatch(key):
        raise ValueError('invalid kind or kebab-case version ID')
    if key in state['artifacts']:
        raise ValueError('version ID already exists; create a new version')
    if based_on and based_on not in state['artifacts']:
        raise ValueError('unknown revision/task base')
    if any(parent not in state['artifacts'] for parent in parents):
        raise ValueError('unknown parent')
    if kind in ('concept', 'page', 'component', 'delivery'):
        expected = {'concept': 'direction', 'page': 'concept', 'component': 'page', 'delivery': 'component'}[kind]
        matches = [p for p in parents if state['artifacts'][p]['kind'] == expected]
        if not matches and not (kind in ('page', 'component', 'delivery') and direct_reason):
            raise ValueError(f'{kind} requires an approved {expected}; direct scoped/imported work needs user reason')
        if any(not approved(project, state, p) for p in parents):
            raise ValueError('parent is unapproved, stale or modified')
    if file:
        file = Path(file).resolve(strict=True)
        if kind in ('concept', 'page', 'component'):
            if file.suffix.lower() == '.svg':
                import xml.etree.ElementTree as ET
                try:
                    root = ET.parse(file).getroot()
                except ET.ParseError as e:
                    raise ValueError('invalid SVG output') from e
                if root.tag.split('}')[-1] != 'svg':
                    raise ValueError('invalid SVG output')
            else:
                from PIL import Image
                with Image.open(file) as image:
                    image.verify()
    if prompt:
        prompt = Path(prompt).resolve(strict=True)
    if not file and not prompt:
        raise ValueError('actual file or complete prompt required')
    target = project / 'history' / key
    if target.exists():
        raise FileExistsError('history exists; use a new ID')
    target.mkdir(parents=True)
    item = {'kind': kind, 'status': 'review' if file else ('pending-transfer' if result_ref else 'pending-generation'),
            'parents': list(parents), 'direct_reason': direct_reason, 'origin': origin,
            'tool': tool, 'model': model, 'created_at': now(), 'human_qa': 'unverified',
            'sources': source_snapshot(state), 'result_ref': result_ref, 'based_on': based_on}
    try:
        if file:
            output = target / ('output' + file.suffix.lower())
            shutil.copy2(file, output)
            item.update(path=str(output.relative_to(project)), sha256=digest(output))
        if prompt:
            output = target / 'prompt.md'
            shutil.copy2(prompt, output)
            item.update(prompt=str(output.relative_to(project)), prompt_sha256=digest(output))
        state['artifacts'][key] = item
        state['events'].append({'at': now(), 'action': 'record', 'id': key})
        save(project, state)
    except Exception:
        shutil.rmtree(target)
        raise
    return item


def approve(project, key, evidence):
    state = load(project)
    item = state['artifacts'][key]
    if not evidence.strip() or item['status'] not in ('review', 'approved'):
        raise ValueError('approval requires real output and explicit user evidence')
    path = Path(project) / item['path']
    if digest(path) != item['sha256'] or not sources_match(item.get('sources', {})) or item.get('sources', {}) != source_snapshot(state) or any(not approved(project, state, p) for p in item['parents']):
        raise ValueError('artifact or parent changed; create/review a new version')
    if item.get('prompt') and digest(Path(project) / item['prompt']) != item['prompt_sha256']:
        raise ValueError('prompt changed; create a new version')
    item.update(status='approved', human_qa='user-approved', approval={'evidence': evidence, 'at': now()})
    state['events'].append({'at': now(), 'action': 'approve', 'id': key, 'evidence': evidence})
    save(project, state)


def resume(project):
    state = load(project)
    result = {'sources_changed': [], 'artifacts': {}, 'capabilities': state['capabilities']}
    for source in state['sources']:
        p = Path(source['path'])
        if not p.is_file() or digest(p) != source['sha256']:
            result['sources_changed'].append(source['path'])
    for key, item in state['artifacts'].items():
        status = item['status']
        if item.get('path'):
            p = Path(project) / item['path']
            if not p.is_file() or digest(p) != item['sha256']:
                status = 'modified-or-missing'
        if any(not approved(project, state, p) for p in item['parents']):
            status = 'stale-parent'
        if item.get('prompt'):
            p = Path(project) / item['prompt']
            if not p.is_file() or digest(p) != item['prompt_sha256']:
                status = 'modified-or-missing'
        if not sources_match(item.get('sources', {})) or item.get('sources', {}) != source_snapshot(state):
            status = 'stale-source'
        result['artifacts'][key] = status
    result['next_action'] = ('review-source-changes' if result['sources_changed'] else
                             'resume-pending-or-review-artifacts; never infer user approval')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--source', type=Path, action='append', default=[])
    sub.add_parser('resume')
    src = sub.add_parser('source'); src.add_argument('path', type=Path)
    src.add_argument('--evidence', required=True); src.add_argument('--role', default='game-rules')
    rec = sub.add_parser('record'); rec.add_argument('id'); rec.add_argument('--kind', choices=KINDS, required=True)
    rec.add_argument('--file', type=Path); rec.add_argument('--prompt', type=Path)
    rec.add_argument('--parent', action='append', default=[]); rec.add_argument('--direct-reason')
    rec.add_argument('--tool', default='none'); rec.add_argument('--model', default='unknown')
    rec.add_argument('--result-ref', help='Real external tool output reference; local file transfer still pending.')
    rec.add_argument('--based-on', help='Existing revision or pending task; does not imply its approval.')
    rec.add_argument('--origin', choices=['generated', 'imported', 'processed'], default='generated')
    appr = sub.add_parser('approve'); appr.add_argument('id'); appr.add_argument('--evidence', required=True)
    cap = sub.add_parser('capability'); cap.add_argument('name'); cap.add_argument('--status', choices=['available', 'unavailable', 'unknown'], required=True); cap.add_argument('--evidence', required=True)
    args = p.parse_args()
    try:
        if args.command == 'init': result = initialize(args.project, args.source)
        elif args.command == 'record': result = record(args.project, args.id, args.kind, args.file, args.prompt, args.parent, args.direct_reason, args.tool, args.model, args.origin, args.result_ref, args.based_on)
        elif args.command == 'approve': approve(args.project, args.id, args.evidence); result = {'approved': args.id}
        elif args.command == 'resume': result = resume(args.project)
        elif args.command == 'source': result = register_source(args.project, args.path, args.evidence, args.role)
        else:
            state = load(args.project)
            state['capabilities'][args.name] = {'status': args.status, 'evidence': args.evidence, 'at': now()}
            save(args.project, state); result = state['capabilities']
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, KeyError) as e:
        print(f'ERROR: {e}'); return 2

if __name__ == '__main__':
    raise SystemExit(main())
