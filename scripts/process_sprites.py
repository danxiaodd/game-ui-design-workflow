#!/usr/bin/env python3
"""Deterministic PNG regions/grid/alpha trim; versioned outputs, integrity checks, contact sheet."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile
import yaml
from PIL import Image, ImageDraw
from inspect_image import inspect

NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regions_for(image, layout):
    mode = layout.get('mode')
    if mode == 'grid':
        cols, rows = layout.get('columns'), layout.get('rows')
        margin, gap = layout.get('margin', 0), layout.get('spacing', 0)
        if any(type(v) is not int or v < 0 for v in (margin, gap)) or any(type(v) is not int or v <= 0 for v in (cols, rows)):
            raise ValueError('positive rows/columns and nonnegative margin/spacing required')
        usable_w = image.width - 2*margin - (cols-1)*gap
        usable_h = image.height - 2*margin - (rows-1)*gap
        if usable_w <= 0 or usable_h <= 0 or usable_w % cols or usable_h % rows:
            raise ValueError('grid does not divide image exactly; use explicit regions')
        w, h = usable_w//cols, usable_h//rows
        names = layout.get('names')
        if not isinstance(names, list) or len(names) != cols*rows:
            raise ValueError('grid names must match rows * columns (row-major)')
        return [{'name': n, 'rect': [margin+(i%cols)*(w+gap), margin+(i//cols)*(h+gap), w, h]}
                for i, n in enumerate(names)]
    if mode == 'trim':
        threshold = layout.get('alpha_threshold', 0)
        if type(threshold) is not int or not 0 <= threshold <= 254:
            raise ValueError('alpha_threshold must be 0..254')
        bbox = image.getchannel('A').point(lambda a: 255 if a > threshold else 0).getbbox()
        if not bbox: raise ValueError('image is fully transparent at selected threshold')
        padding = layout.get('padding', 0)
        if type(padding) is not int or padding < 0: raise ValueError('nonnegative padding required')
        x, y, right, bottom = bbox
        x, y, right, bottom = max(0,x-padding), max(0,y-padding), min(image.width,right+padding), min(image.height,bottom+padding)
        return [{'name': layout.get('name'), 'rect': [x,y,right-x,bottom-y]}]
    if mode == 'regions' and isinstance(layout.get('items'), list): return layout['items']
    raise ValueError('mode must be grid, regions or trim')


def validate_regions(image, regions):
    if not regions: raise ValueError('no regions')
    names = set()
    for r in regions:
        name, rect = r.get('name'), r.get('rect')
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in names or name == 'contact-sheet':
            raise ValueError('unique kebab-case names required')
        if not isinstance(rect, list) or len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError('rect must contain integer x,y,width,height')
        x,y,w,h = rect
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > image.width or y+h > image.height:
            raise ValueError(f'out-of-bounds rect: {name}')
        names.add(name)


def contact_sheet(files, output):
    cols = min(4, len(files)); cell = 180
    board = Image.new('RGB', (cols*cell, ((len(files)+cols-1)//cols)*(cell+28)), '#343434')
    draw = ImageDraw.Draw(board)
    for i, path in enumerate(files):
        with Image.open(path) as source:
            image = source.convert('RGBA'); image.thumbnail((cell-16, cell-16))
            x,y = (i%cols)*cell, (i//cols)*(cell+28)
            # Dark/light background makes alpha edges visible; preview labels are never cut assets.
            for yy in range(y,y+cell,12):
                for xx in range(x,x+cell,12):
                    color = '#777777' if ((xx-x)//12+(yy-y)//12)%2 else '#aaaaaa'
                    draw.rectangle((xx,yy,min(xx+11,x+cell-1),min(yy+11,y+cell-1)), fill=color)
            board.paste(image,(x+(cell-image.width)//2,y+(cell-image.height)//2),image)
            draw.text((x+4,y+cell+4),path.stem[:25],fill='white')
    board.save(output)


def process(source, output, layout):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists(): raise FileExistsError('output already exists; use a new version directory')
    with Image.open(source) as raw:
        image = raw.convert('RGBA')
    regions = regions_for(image, layout); validate_regions(image, regions)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.sprites-', dir=output.parent))
    try:
        items = []
        for r in regions:
            x,y,w,h = r['rect']; name = r['name']
            crop = image.crop((x,y,x+w,y+h)); path = temp / f'{name}.png'; crop.save(path)
            report = inspect(path)
            if report['visible_bbox'] is None: raise ValueError(f'empty sprite: {name}')
            if layout.get('require_transparent') and not report['transparent_background']:
                raise ValueError(f'no actual transparent background: {name}')
            item = {'id': name, 'semantic_name': name, 'path': path.name, 'bbox': r['rect'],
                    'dimensions': [w,h], 'original_size': list(image.size), 'trim_offset': [x,y],
                    'sha256': sha(path), 'transparent_background': report['transparent_background'],
                    'alpha': {k:v for k,v in report.items() if k not in ('path', 'human_review')}}
            for key in ('component_id', 'category', 'state', 'slice'):
                if key in r: item[key] = r[key]
            items.append(item)
        manifest = {'schema_version': 1, 'source_sheet': str(source), 'source_sha256': sha(source),
                    'source_dimensions': list(image.size), 'mode': layout['mode'], 'layout': layout,
                    'item_count': len(items), 'items': items,
                    'review': {'complete': False, 'text_free': False,
                               'required': ['edges', 'subject completeness', 'style', 'text', '9-slice']}}
        (temp/'sprite-manifest.yaml').write_text(yaml.safe_dump(manifest,allow_unicode=True,sort_keys=False),encoding='utf-8')
        contact_sheet([temp/i['path'] for i in items],temp/'contact-sheet.png')
        with zipfile.ZipFile(temp/'sprites.zip','w',zipfile.ZIP_DEFLATED) as archive:
            archive.write(temp/'sprite-manifest.yaml','sprite-manifest.yaml')
            for item in items: archive.write(temp/item['path'],'items/'+item['path'])
        verify(temp)
        # Never replace a version that appeared while processing.
        if output.exists(): raise FileExistsError('output appeared; choose a new version')
        temp.rename(output)
        return manifest
    except Exception:
        shutil.rmtree(temp, ignore_errors=True); raise


def verify(folder):
    folder = Path(folder)
    m = yaml.safe_load((folder/'sprite-manifest.yaml').read_text(encoding='utf-8'))
    items = m['items']
    if m['item_count'] != len(items) or not items: raise ValueError('item count mismatch')
    expected = {i['path'] for i in items}
    if len(expected) != len(items) or expected != {p.name for p in folder.glob('*.png') if p.name != 'contact-sheet.png'}:
        raise ValueError('file count/name mismatch')
    for i in items:
        path = folder/i['path']
        if Path(i['path']).name != i['path'] or path.suffix != '.png' or not NAME.fullmatch(path.stem):
            raise ValueError('unsafe item path')
        if sha(path) != i['sha256'] or inspect(path)['dimensions'] != i['dimensions']:
            raise ValueError('sprite checksum/dimensions mismatch')
    with zipfile.ZipFile(folder/'sprites.zip') as archive:
        names = archive.namelist()
        if len(names) != len(expected)+1 or set(names) != {'items/'+name for name in expected} | {'sprite-manifest.yaml'} or archive.testzip():
            raise ValueError('ZIP count/integrity mismatch')
        for name in names:
            path = folder / (name.removeprefix('items/'))
            if archive.read(name) != path.read_bytes(): raise ValueError('ZIP differs from output')
    return {'verified': True, 'item_count': len(items)}


def main():
    p = argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    split=sub.add_parser('split'); split.add_argument('source',type=Path); split.add_argument('--layout',type=Path,required=True); split.add_argument('--output',type=Path,required=True)
    check=sub.add_parser('verify'); check.add_argument('folder',type=Path)
    a=p.parse_args()
    try:
        result = verify(a.folder) if a.command=='verify' else process(a.source,a.output,yaml.safe_load(a.layout.read_text(encoding='utf-8')))
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,yaml.YAMLError,zipfile.BadZipFile) as e:
        print(f'ERROR: {e}'); return 2

if __name__=='__main__': raise SystemExit(main())
