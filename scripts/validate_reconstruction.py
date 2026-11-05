#!/usr/bin/env python3
"""Validate real assets and page placement; does not claim visual or user approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml
from PIL import Image

ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
HASH = re.compile(r'^[0-9a-f]{64}$')


def checked_file(root, entry, label):
    if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
        raise ValueError(f'{label}: path and sha256 are required')
    path = Path(entry['path'])
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'{label}: path must remain inside layout directory')
    path = (root / path).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'{label}: invalid or escaping file path')
    expected = entry.get('sha256')
    if not isinstance(expected, str) or not HASH.fullmatch(expected):
        raise ValueError(f'{label}: valid lowercase SHA256 required')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f'{label}: sha256 mismatch')
    return path


def ints(value, length, label, *, positive=False):
    if not isinstance(value, list) or len(value) != length or any(type(v) is not int for v in value):
        raise ValueError(f'{label}: expected {length} integers')
    if positive and any(v <= 0 for v in value):
        raise ValueError(f'{label}: dimensions must be positive')
    return value


def validate(layout_path):
    layout_path = Path(layout_path).resolve(strict=True)
    root = layout_path.parent
    data = yaml.safe_load(layout_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('schema_version must be 1')
    page = data.get('page')
    if not isinstance(page, dict) or not isinstance(page.get('id'), str) or not ID.fullmatch(page['id']):
        raise ValueError('page.id must be kebab-case')
    platform = page.get('platform')
    if platform not in ('mobile', 'other'):
        raise ValueError('page.platform must be mobile or other')
    canvas = ints(page.get('canvas'), 2, 'page.canvas', positive=True)
    policy = page.get('canvas_policy')
    if policy not in ('current', 'historical', 'user-override'):
        raise ValueError('page.canvas_policy must be current, historical, or user-override')
    if policy != 'current' and (not isinstance(page.get('exception_evidence'), str) or not page['exception_evidence'].strip()):
        raise ValueError('historical and user-override require exception_evidence')
    if platform == 'mobile' and policy == 'current' and canvas != [1080, 2340]:
        raise ValueError('current mobile page must use 1080x2340 canvas')
    reference = checked_file(root, page.get('reference'), 'page.reference')
    with Image.open(reference) as image:
        image.load()
        if list(image.size) != canvas:
            raise ValueError('page.reference dimensions do not match page.canvas')

    instances = data.get('instances')
    if not isinstance(instances, list) or not instances:
        raise ValueError('instances must be a non-empty list')
    ids, results = set(), []
    for item in instances:
        if not isinstance(item, dict):
            raise ValueError('each instance must be a mapping')
        name = item.get('id')
        if not isinstance(name, str) or not ID.fullmatch(name) or name in ids:
            raise ValueError('instance ids must be unique kebab-case strings')
        ids.add(name)
        asset = item.get('asset')
        path = checked_file(root, asset, name)
        if asset.get('provenance') not in ('layered-source', 'reconstructed', 'original-crop'):
            raise ValueError(f'{name}: unknown asset provenance')
        if type(asset.get('transparent_required')) is not bool:
            raise ValueError(f'{name}: transparent_required must be boolean')
        with Image.open(path) as image:
            image.load()
            if image.format != 'PNG':
                raise ValueError(f'{name}: asset must be PNG')
            dimensions = list(image.size)
            has_alpha = 'A' in image.getbands() or 'transparency' in image.info
            alpha = image.convert('RGBA').getchannel('A')
            bbox = alpha.getbbox()
            if asset['transparent_required'] and (not has_alpha or alpha.histogram()[0] == 0):
                raise ValueError(f'{name}: actual transparent pixels are required')
        if bbox is None:
            raise ValueError(f'{name}: asset is fully transparent')
        visible = ints(item.get('visible_bbox'), 4, f'{name}.visible_bbox')
        if visible != list(bbox):
            raise ValueError(f'{name}: visible_bbox differs from actual alpha>0 bounds {list(bbox)}')
        x, y, width, height = ints(item.get('page_rect'), 4, f'{name}.page_rect')
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > canvas[0] or y + height > canvas[1]:
            raise ValueError(f'{name}: page_rect is outside page canvas')
        pivot = item.get('pivot')
        if not isinstance(pivot, list) or len(pivot) != 2 or any(type(v) not in (int, float) or not 0 <= v <= 1 for v in pivot):
            raise ValueError(f'{name}: pivot must contain two numbers from 0 to 1')
        placement = item.get('placement')
        if placement not in ('pixel-exact', 'scaled', 'sliced'):
            raise ValueError(f'{name}: invalid placement')
        if placement == 'pixel-exact' and dimensions != [width, height]:
            raise ValueError(f'{name}: pixel-exact dimensions do not match page_rect')
        slicing = item.get('slice')
        if not isinstance(slicing, dict):
            raise ValueError(f'{name}: slice mapping is required')
        if placement == 'sliced':
            margins = ints(slicing.get('margins'), 4, f'{name}.slice.margins')
            left, right, top, bottom = margins
            evidence = slicing.get('review_evidence')
            if (slicing.get('type') != '9-slice' or min(margins) < 0 or
                    left + right >= min(dimensions[0], width) or top + bottom >= min(dimensions[1], height) or
                    not isinstance(evidence, str) or not evidence.strip()):
                raise ValueError(f'{name}: invalid or unreviewed 9-slice margins')
        elif slicing.get('type') != 'full':
            raise ValueError(f'{name}: pixel-exact and scaled placement require full slice')
        results.append({'id': name, 'dimensions': dimensions, 'page_rect': [x, y, width, height],
                        'visible_bbox': visible, 'placement': placement, 'provenance': asset['provenance']})
    return {'verified': True, 'page_id': page['id'], 'canvas': canvas, 'instance_count': len(results),
            'instances': results, 'visual_review': 'not-performed', 'user_approval': 'not-performed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('layout', type=Path)
    parser.add_argument('--report', type=Path, help='write a new JSON report without overwriting')
    args = parser.parse_args()
    try:
        result = validate(args.layout)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.report:
            with args.report.open('x', encoding='utf-8') as stream:
                stream.write(text + '\n')
        print(text)
        return 0
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print(f'ERROR: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
