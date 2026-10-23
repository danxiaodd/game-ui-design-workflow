from pathlib import Path
import json
import sys
import tempfile
import unittest
import zipfile
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from inspect_image import inspect
from process_sprites import process, verify
from export_asset_pack import export_pack
from export_engine_manifest import export_unity
from split_sprite_sheet import split_sprite_sheet, SplitSettings


class DeterministicAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
        self.source=self.root/'sheet.png'
        im=Image.new('RGBA',(48,24),(0,0,0,0)); draw=ImageDraw.Draw(im)
        draw.rectangle((3,3,18,18),fill=(255,30,10,255)); draw.rectangle((27,5,43,20),fill=(10,80,255,120)); im.save(self.source)
        self.grid={'mode':'grid','columns':2,'rows':1,'names':['red-icon','blue-icon'],'require_transparent':True}

    def test_alpha_pixels_distinguish_real_transparency_opaque_rgba_and_empty(self):
        self.assertTrue(inspect(self.source)['transparent_background'])
        opaque=self.root/'opaque.png'; Image.new('RGBA',(12,12),(255,255,255,255)).save(opaque)
        empty=self.root/'empty.png'; Image.new('RGBA',(12,12),(0,0,0,0)).save(empty)
        self.assertTrue(inspect(opaque)['has_alpha']); self.assertFalse(inspect(opaque)['transparent_background'])
        self.assertFalse(inspect(empty)['transparent_background']); self.assertIsNone(inspect(empty)['visible_bbox'])
        # Baked checkerboard is still opaque RGB.
        board=Image.new('RGB',(12,12),'white'); ImageDraw.Draw(board).rectangle((0,0,5,5),fill='gray'); board.save(opaque)
        self.assertFalse(inspect(opaque)['transparent_background'])

    def test_grid_exact_pixels_order_dimensions_and_zip(self):
        out=self.root/'v001'; manifest=process(self.source,out,self.grid)
        self.assertEqual(manifest['item_count'],2)
        self.assertEqual([i['id'] for i in manifest['items']],['red-icon','blue-icon'])
        with Image.open(self.source) as source, Image.open(out/'blue-icon.png') as item:
            self.assertEqual(item.size,(24,24)); self.assertEqual(item.tobytes(),source.crop((24,0,48,24)).tobytes())
        self.assertEqual(verify(out),{'verified':True,'item_count':2})
        self.assertTrue((out/'contact-sheet.png').is_file())
        with zipfile.ZipFile(out/'sprites.zip') as archive:
            self.assertEqual(set(archive.namelist()),{'sprite-manifest.yaml','items/red-icon.png','items/blue-icon.png'})

    def test_explicit_regions_preserve_partial_alpha_and_known_rect(self):
        manifest=process(self.source,self.root/'regions',{'mode':'regions','items':[{'name':'blue','rect':[26,4,19,18]}]})
        self.assertEqual(manifest['items'][0]['bbox'],[26,4,19,18])
        with Image.open(self.root/'regions/blue.png') as image:
            self.assertEqual(image.getpixel((1,1)),(10,80,255,120))

    def test_trim_keeps_source_dimensions_offset_and_alpha(self):
        manifest=process(self.source,self.root/'trim',{'mode':'trim','name':'both','padding':1})
        item=manifest['items'][0]
        self.assertEqual(item['bbox'],[2,2,43,20]); self.assertEqual(item['original_size'],[48,24]); self.assertEqual(item['trim_offset'],[2,2])

    def test_bad_grid_regions_names_and_empty_fail_before_output(self):
        layouts=[{**self.grid,'columns':5},{**self.grid,'names':['same','same']},
                 {'mode':'regions','items':[{'name':'bad','rect':[47,0,2,2]}]},
                 {'mode':'regions','items':[{'name':'../escape','rect':[0,0,2,2]}]},
                 {'mode':'regions','items':[{'name':'contact-sheet','rect':[0,0,2,2]}]},
                 {'mode':'regions','items':[{'name':'empty','rect':[0,0,2,2]}]}]
        for i,layout in enumerate(layouts):
            out=self.root/f'bad-{i}'
            with self.assertRaises(ValueError): process(self.source,out,layout)
            self.assertFalse(out.exists())

    def test_preserves_existing_version_and_source(self):
        out=self.root/'v001'; original=self.source.read_bytes(); process(self.source,out,self.grid)
        snapshot=(out/'red-icon.png').read_bytes()
        with self.assertRaises(FileExistsError): process(self.source,out,self.grid)
        self.assertEqual(snapshot,(out/'red-icon.png').read_bytes()); self.assertEqual(original,self.source.read_bytes())

    def test_verify_detects_missing_extra_tampered_files_and_zip(self):
        for mode in ('missing','extra','pixels','zip'):
            out=self.root/mode; process(self.source,out,self.grid)
            if mode=='missing': (out/'blue-icon.png').unlink()
            elif mode=='extra': (out/'extra.png').write_bytes((out/'red-icon.png').read_bytes())
            elif mode=='pixels': Image.new('RGBA',(24,24),'green').save(out/'red-icon.png')
            else:
                with zipfile.ZipFile(out/'sprites.zip','w') as z: z.writestr('wrong.txt','wrong')
            with self.assertRaises(ValueError): verify(out)

    def test_batch_exports_actual_png_atlas_three_engines_and_configuration(self):
        pack=self.root/'pack'; process(self.source,pack,self.grid)
        output=self.root/'delivery-v001'; result=export_pack(pack,output,'TEST FIXTURE accepted synthetic pack')
        self.assertEqual(result['sprites'],2); self.assertEqual(result['unity_import'],'unverified')
        for name in ('unity','godot','cocos'):
            self.assertEqual(json.loads((output/f'{name}.json').read_text())['engine'],name)
        with Image.open(output/'atlas/ui.png') as atlas:
            self.assertEqual(atlas.mode,'RGBA')
        self.assertEqual(json.loads((output/'unity.json').read_text())['coordinateOrigin'],'bottom-left')
        with zipfile.ZipFile(output/'delivery.zip') as z: self.assertIsNone(z.testzip())
        self.assertFalse(json.loads((output/'provenance.json').read_text())['native_files_generated'])
        with self.assertRaises(FileExistsError): export_pack(pack,output,'TEST FIXTURE')

    def test_unity_converts_asymmetric_y_and_border(self):
        data=export_unity({'image':'atlas.png','size':[128,256], 'sprites':{'panel':{'region':[7,11,30,40], 'slice':{'type':'9-slice','margins':[1,2,3,4]}}}})
        self.assertEqual(data['sprites'][0]['rect'],[7,205,30,40])
        self.assertEqual(data['sprites'][0]['border'],[1,4,2,3])

    def test_legacy_split_invalid_mapping_force_does_not_destroy_outputs(self):
        folder=self.root/'old'; folder.mkdir(); (folder/'keep.txt').write_text('keep')
        zip_path=self.root/'old.zip'; zip_path.write_text('old')
        with self.assertRaises(ValueError): split_sprite_sheet(self.source,folder,zip_path,SplitSettings(),True,[])
        self.assertEqual((folder/'keep.txt').read_text(),'keep'); self.assertEqual(zip_path.read_text(),'old')
