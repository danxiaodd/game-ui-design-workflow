from copy import deepcopy
import hashlib
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_reconstruction import validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReconstructionLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.page = self.root / 'page.png'
        self.asset = self.root / 'button.png'
        Image.new('RGB', (1080, 2340), 'white').save(self.page)
        asset = Image.new('RGBA', (30, 20))
        ImageDraw.Draw(asset).rectangle((2, 3, 26, 17), fill=(200, 60, 30, 255))
        asset.putpixel((1, 2), (0, 0, 0, 1))  # subtle shadow remains part of actual bounds
        asset.save(self.asset)
        self.layout_path = self.root / 'layout.yaml'
        self.layout = {
            'schema_version': 1,
            'page': {'id': 'home-v001', 'platform': 'mobile', 'canvas': [1080, 2340],
                     'canvas_policy': 'current', 'reference': {'path': 'page.png', 'sha256': sha(self.page)}},
            'instances': [{'id': 'button-one', 'asset': {'path': 'button.png', 'sha256': sha(self.asset),
                          'provenance': 'layered-source', 'transparent_required': True},
                          'page_rect': [10, 20, 30, 20], 'visible_bbox': [1, 2, 27, 18],
                          'pivot': [0.5, 0.5], 'placement': 'pixel-exact', 'slice': {'type': 'full'}}],
        }

    def write(self, layout):
        self.layout_path.write_text(yaml.safe_dump(layout, sort_keys=False), encoding='utf-8')

    def test_valid_geometry_and_reused_asset_leave_visual_review_pending(self):
        second = deepcopy(self.layout['instances'][0])
        second.update(id='button-two', page_rect=[400, 600, 60, 40], placement='scaled')
        self.layout['instances'].append(second)
        self.write(self.layout)
        result = validate(self.layout_path)
        self.assertEqual(result['instance_count'], 2)
        self.assertEqual(result['instances'][0]['visible_bbox'], [1, 2, 27, 18])
        self.assertEqual(result['visual_review'], 'not-performed')
        self.assertEqual(result['user_approval'], 'not-performed')

    def test_mismatch_in_size_position_alpha_or_asset_hash_fails(self):
        for name in ('size', 'page', 'bounds', 'hash', 'duplicate'):
            layout = deepcopy(self.layout)
            instance = layout['instances'][0]
            if name == 'size': instance['page_rect'][2] += 1
            elif name == 'page': instance['page_rect'][0] = 1070
            elif name == 'bounds': instance['visible_bbox'] = [2, 3, 27, 18]
            elif name == 'hash': instance['asset']['sha256'] = '0' * 64
            else: layout['instances'].append(deepcopy(instance))
            self.write(layout)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate(self.layout_path)

    def test_mobile_canvas_policy_and_reference_dimensions(self):
        Image.new('RGB', (853, 1844), 'white').save(self.page)
        self.layout['page']['reference']['sha256'] = sha(self.page)
        self.layout['page']['canvas'] = [853, 1844]
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, '1080x2340'):
            validate(self.layout_path)
        self.layout['page']['canvas_policy'] = 'historical'
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, 'exception_evidence'):
            validate(self.layout_path)
        self.layout['page']['exception_evidence'] = 'TEST FIXTURE: historical source'
        self.write(self.layout)
        self.assertEqual(validate(self.layout_path)['canvas'], [853, 1844])
        self.layout['page']['canvas'] = [853, 1843]
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            validate(self.layout_path)

    def test_sliced_requires_realistic_margins_and_recorded_review(self):
        instance = self.layout['instances'][0]
        instance['placement'] = 'sliced'
        instance['page_rect'] = [20, 50, 60, 40]
        instance['slice'] = {'type': '9-slice', 'margins': [5, 6, 4, 5], 'review_evidence': 'TEST FIXTURE: previewed'}
        self.write(self.layout)
        self.assertTrue(validate(self.layout_path)['verified'])
        instance['slice']['margins'] = [15, 15, 4, 5]
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, '9-slice'):
            validate(self.layout_path)
        instance['slice']['margins'] = [5, 6, 4, 5]
        instance['slice']['review_evidence'] = ''
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, '9-slice'):
            validate(self.layout_path)

    def test_transparency_and_path_constraints(self):
        Image.new('RGB', (30, 20), 'white').save(self.asset)
        item = self.layout['instances'][0]
        item['asset']['sha256'] = sha(self.asset)
        item['visible_bbox'] = [0, 0, 30, 20]
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, 'transparent pixels'):
            validate(self.layout_path)
        item['asset']['transparent_required'] = False
        self.write(self.layout)
        self.assertTrue(validate(self.layout_path)['verified'])
        item['asset']['path'] = '../button.png'
        self.write(self.layout)
        with self.assertRaisesRegex(ValueError, 'inside layout directory'):
            validate(self.layout_path)

    def test_portable_runner_writes_report_once(self):
        self.write(self.layout)
        report = self.root / 'report.json'
        runner = ROOT / 'skills/game-ui-sprite-sheet-splitter/scripts/run.py'
        command = [sys.executable, str(runner), 'validate_reconstruction', str(self.layout_path), '--report', str(report)]
        first = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(json.loads(report.read_text())['instance_count'], 1)
        original = report.read_bytes()
        second = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(report.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
