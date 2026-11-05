#!/usr/bin/env python3
"""Install portable skills and a versioned local runtime for Codex or Cursor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PARTS = ('scripts', 'templates', 'config', 'schemas')


def runtime_files(root):
    return sorted(p for part in PARTS for p in (root / part).rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')


def install(target, force=False, dry_run=False):
    target = Path(target).resolve()
    files = runtime_files(ROOT)
    stamp = hashlib.sha256()
    for path in files + [ROOT / 'LICENSE', ROOT / 'ORIGIN.md']:
        stamp.update(str(path.relative_to(ROOT)).encode())
        stamp.update(path.read_bytes())
    runtime = target / '.game-ui-runtime' / stamp.hexdigest()[:16]
    if not dry_run and not runtime.exists():
        runtime.mkdir(parents=True)
        for path in files + [ROOT / 'LICENSE', ROOT / 'ORIGIN.md']:
            out = runtime / path.relative_to(ROOT)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, out)
    installed = skipped = 0
    for source in sorted((ROOT / 'skills').iterdir()):
        if not (source / 'SKILL.md').is_file():
            continue
        destination = target / source.name
        if (destination.exists() or destination.is_symlink()) and not force:
            print(f'SKIP: {destination} already exists (use --force to replace)')
            skipped += 1
            continue
        if dry_run:
            print(f'WOULD INSTALL: {source} -> {destination}')
        else:
            if destination.is_symlink(): destination.unlink()
            elif destination.exists(): shutil.rmtree(destination)
            shutil.copytree(source, destination)
            (destination / 'runtime.json').write_text(json.dumps({
                'root': os.path.relpath(runtime, destination)
            }, indent=2)+'\n', encoding='utf-8')
            print(f'INSTALLED: {destination}')
        installed += 1
    print(f'Done: {installed} installed, {skipped} skipped. Target: {target}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    scope = p.add_mutually_exclusive_group(required=True)
    scope.add_argument('--project', type=Path); scope.add_argument('--personal', action='store_true')
    p.add_argument('--agent', choices=['cursor', 'codex'], default='cursor')
    p.add_argument('--force', action='store_true'); p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    if a.project and not a.project.is_dir(): p.error('project directory does not exist')
    parent = a.project if a.project else Path.home()
    target = parent / ('.agents' if a.agent == 'codex' else '.cursor') / 'skills'
    install(target, a.force, a.dry_run)
    return 0

if __name__ == '__main__': raise SystemExit(main())
