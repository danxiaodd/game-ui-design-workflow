#!/usr/bin/env python3
"""Installed copy lives in <skill>/scripts/run.py; resolve tools independently of CWD."""
import json
from pathlib import Path
import runpy
import sys


def main():
    skill = Path(__file__).resolve().parents[1]
    pointer = skill / 'runtime.json'
    root = (skill / json.loads(pointer.read_text(encoding='utf-8'))['root']).resolve() if pointer.exists() else skill.parents[1]
    if len(sys.argv) < 2 or not sys.argv[1].replace('_', '').isalnum():
        raise SystemExit('Usage: python <skill>/scripts/run.py <tool_name> [arguments]')
    tool = root / 'scripts' / (sys.argv[1] + '.py')
    if not tool.is_file(): raise SystemExit(f'Tool not installed: {tool}')
    sys.path.insert(0, str(tool.parent))
    sys.argv = [str(tool), *sys.argv[2:]]
    runpy.run_path(str(tool), run_name='__main__')

if __name__ == '__main__': main()
