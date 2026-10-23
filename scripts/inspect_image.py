#!/usr/bin/env python3
"""Inspect actual pixels, not a displayed checkerboard. No image modifications."""
import argparse
import json
from pathlib import Path
from PIL import Image


def inspect(path):
    with Image.open(path) as source:
        source.load()
        has_alpha = 'A' in source.getbands() or 'transparency' in source.info
        alpha = source.convert('RGBA').getchannel('A')
        histogram = alpha.histogram()
        total = source.width * source.height
        bbox = alpha.getbbox()
        edge = list(alpha.crop((0, 0, source.width, 1)).tobytes()) + list(alpha.crop((0, source.height-1, source.width, source.height)).tobytes()) + list(alpha.crop((0, 0, 1, source.height)).tobytes()) + list(alpha.crop((source.width-1, 0, source.width, source.height)).tobytes())
        return {'path': str(path), 'format': source.format, 'mode': source.mode,
                'dimensions': list(source.size), 'has_alpha': has_alpha,
                'alpha_extrema': list(alpha.getextrema()), 'transparent_pixels': histogram[0],
                'partial_alpha_pixels': sum(histogram[1:255]), 'opaque_pixels': histogram[255],
                'transparent_fraction': histogram[0]/total, 'visible_bbox': list(bbox) if bbox else None,
                'visible_edge_pixels': sum(v > 0 for v in edge),
                'transparent_edge_pixels': sum(v == 0 for v in edge),
                'transparent_background': has_alpha and histogram[0] > 0 and bbox is not None,
                'human_review': ['edge contamination', 'subject completeness', 'style consistency', 'text remnants']}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('image', type=Path)
    p.add_argument('--require-transparent', action='store_true'); p.add_argument('--report', type=Path)
    a = p.parse_args()
    try:
        report = inspect(a.image); text = json.dumps(report, ensure_ascii=False, indent=2)
        if a.report:
            with a.report.open('x', encoding='utf-8') as f: f.write(text+'\n')
        print(text)
        return 1 if a.require_transparent and not report['transparent_background'] else 0
    except (OSError, ValueError) as e: print(f'ERROR: {e}'); return 2

if __name__ == '__main__': raise SystemExit(main())
