#!/usr/bin/env python3
"""Export a reviewed deterministic sprite pack using existing atlas/engine pipelines."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
import yaml
from build_sprite_atlas import pack_items
from export_engine_manifest import EXPORTERS
from process_sprites import verify, sha


def export_pack(pack, output, evidence, ppu=100, max_size=2048):
    pack, output = Path(pack).resolve(), Path(output).resolve()
    if output.exists(): raise FileExistsError('delivery exists; choose a new version directory')
    if not evidence.strip(): raise ValueError('explicit user review evidence required')
    if ppu <= 0 or max_size <= 0: raise ValueError('positive PPU/max size required')
    verify(pack)
    manifest = yaml.safe_load((pack/'sprite-manifest.yaml').read_text(encoding='utf-8'))
    for item in manifest['items']:
        slice_data = item.get('slice', {'type': 'full'})
        if slice_data.get('type') == '9-slice':
            m = slice_data.get('margins'); w,h = item['dimensions']
            if not isinstance(m,list) or len(m)!=4 or any(type(v) is not int or v<0 for v in m) or m[0]+m[1]>=w or m[2]+m[3]>=h:
                raise ValueError(f'invalid 9-slice: {item["id"]}')
    atlas_image, entries = pack_items(pack, manifest['items'], (max_size,max_size), 2, True)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.delivery-',dir=output.parent))
    try:
        (temp/'sprites').mkdir(); (temp/'atlas').mkdir()
        for item in manifest['items']: shutil.copy2(pack/item['path'],temp/'sprites'/item['path'])
        atlas_image.save(temp/'atlas/ui.png')
        for entry in entries: entry['source_path'] = 'sprites/'+Path(entry['source_path']).name
        atlas = {'schema_version':1,'atlas_id':output.name,'image':'atlas/ui.png',
                 'size':list(atlas_image.size),'sprites':{i['semantic_name']:i for i in entries},'coordinate_origin':'top-left'}
        (temp/'atlas/ui.json').write_text(json.dumps(atlas,indent=2)+'\n',encoding='utf-8')
        for engine, exporter in EXPORTERS.items():
            payload = {'schema_version':1,'engine':engine,'atlas_size':atlas['size'],**exporter(atlas)}
            if engine == 'unity':
                for item in payload['sprites']: item['pixelsPerUnit'] = ppu
                payload['importSettings'] = {'textureType':'Sprite','alphaIsTransparency':True,'mipmapEnabled':False,
                                             'spriteMeshType':'FullRect','pixelsPerUnit':ppu}
            (temp/f'{engine}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        settings = {'kind':'configuration-recipe-not-native-spriteatlas','source':'sprites/',
                    'includeInBuild':True,'allowRotation':False,'tightPacking':False,'padding':4,
                    'filterMode':'choose Point for pixel art or Bilinear for painted UI',
                    'maxTextureSize':max_size,'platformCompression':'choose per target and verify edges on device'}
        (temp/'unity-spriteatlas-settings.json').write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
        provenance = {'source_manifest_sha256':sha(pack/'sprite-manifest.yaml'), 'source_pack':str(pack),
                      'source_image_sha256':manifest['source_sha256'],'layout':manifest['layout'],
                      'review_evidence':evidence,'human_visual_review':'recorded-user-evidence',
                      'unity_editor_import':'unverified','native_files_generated':False,
                      'sprites':manifest['items']}
        (temp/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        guide = '''# Unity 资源交付\n\n本包包含独立 sprites/、atlas/ui.png、区域清单与 Unity/Godot/Cocos JSON。JSON 是交接数据，不会自动导入。\n\n1. 独立 PNG：复制 sprites/ 到 Unity Assets；Texture Type=Sprite，Sprite Mode=Single。按 unity.json 的同名条目设置 Pivot、PPU、Border（左/下/右/上），默认 Mesh Type=Full Rect、关闭 Mip Maps。\n2. 已打包图：复制 atlas/ui.png，使用 Multiple；Sprite Editor 按 unity.json 的左下角 rect 手动建立 Sprite 并 Apply。\n3. 需要 Unity 原生 SpriteAtlas：在 Unity 创建 Sprite Atlas，把独立 sprites 加入 Objects for Packing；参考 unity-spriteatlas-settings.json，勿把该 JSON 重命名为 .spriteatlas。\n4. 九宫格：UGUI Image Type=Sliced；人工检查边框、拉伸中心和不同尺寸。\n5. 字体与按钮文字由 UGUI/TMP 独立排版；按项目画布设置显示尺寸。Alpha 裁剪素材的原始尺寸/偏移见 provenance.json，不能丢掉偏移后声称动画锚点不变。\n6. 在目标设备检查边缘采样、缩放、压缩、图集大小和一致性。当前未执行 Unity Editor 导入；图片检查通过不等于引擎验证通过。\n\n平台压缩、Filter Mode 和 Max Size 需要按项目选择；未自动修改现有 Unity 配置。\n'''
        (temp/'UNITY-IMPORT.md').write_text(guide,encoding='utf-8')
        files=sorted(p for p in temp.rglob('*') if p.is_file())
        with zipfile.ZipFile(temp/'delivery.zip','w',zipfile.ZIP_DEFLATED) as archive:
            for f in files: archive.write(f,f.relative_to(temp).as_posix())
        with zipfile.ZipFile(temp/'delivery.zip') as archive:
            if archive.testzip(): raise ValueError('delivery ZIP failed integrity check')
            for f in files:
                if archive.read(f.relative_to(temp).as_posix()) != f.read_bytes(): raise ValueError('delivery mismatch')
        if output.exists(): raise FileExistsError('output appeared; use a new version')
        temp.rename(output)
        return {'output':str(output),'sprites':len(entries),'unity_import':'unverified'}
    except Exception:
        shutil.rmtree(temp,ignore_errors=True); raise


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('pack',type=Path)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--review-evidence',required=True)
    p.add_argument('--ppu',type=float,default=100); p.add_argument('--max-size',type=int,default=2048)
    a=p.parse_args()
    try: print(json.dumps(export_pack(a.pack,a.output,a.review_evidence,a.ppu,a.max_size),ensure_ascii=False)); return 0
    except (OSError,ValueError,KeyError,TypeError,yaml.YAMLError,zipfile.BadZipFile) as e: print(f'ERROR: {e}'); return 2

if __name__=='__main__': raise SystemExit(main())
