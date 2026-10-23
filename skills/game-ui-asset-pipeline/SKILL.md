---
name: game-ui-asset-pipeline
description: Packs semantically named transparent game UI PNG files into an atlas, preserves component states and reviewed 9-slice metadata, and exports deterministic JSON handoff manifests for Godot, Unity, Cocos, or generic consumers. Use after sprite-sheet splitting when users ask for atlas packing, nine-patch metadata, engine delivery, Unity sprites, Godot regions, Cocos frames, or a Game UI Factory production handoff.
---

# 游戏 UI Atlas 与引擎交付

把已经批准的语义 PNG 转换成 Atlas 与引擎 JSON。此技能不执行像素识别，不自动猜测语义，也不声称生成原生引擎工程文件。

独立调用时先恢复项目状态；没有 `workflow-state.json` 就运行 `workflow_state <project> init`，不要求 GDD。实际看过的既有概念图/源图可用 `source <path> --role visual-reference --evidence '<查看与用途>'` 登记。按本次入口登记产物，不依赖先运行总控。

## 页面契约管线的前置条件

- `sprite-contract.yaml` 状态为 `approved`
- 所有 PNG 使用语义名称
- 每个 item 关联 `component_id`、`state` 和 `slice`
- `review.text_free: true`
- 9-slice margins 已人工预览

## 切图方式

- `9-slice`：按钮、面板、弹窗、进度条
- `full`：卡片、角色、徽章、背景
- `1:1`：图标、货币
- `tile`：可重复纹理

9-slice margins 格式：

```yaml
slice:
  type: 9-slice
  margins: [left, right, top, bottom]
```

## 独立素材包直接交付

新切图工具的输出可直接运行 `export_asset_pack <processed-pack-dir> --output <new-delivery-dir> --review-evidence '<用户确认该批素材的依据>'`。
该工具复用原有 Atlas 打包和引擎 exporter，复制独立 PNG、输出 Atlas、Unity/Godot/Cocos JSON、SpriteAtlas 配置建议、来源哈希与质量状态，并打包 ZIP。不要求独立资产任务建立虚构页面。
正式页面项目仍使用下述契约链路。切图清单的 item path 转为项目相对路径后登记到 sprite contract；关联 component/state/slice，不能只把相对文件名原样粘入。

## Atlas

读取 `contracts/atlas-contract.yaml`，执行：

```bash
python3 scripts/build_sprite_atlas.py specs/<project-id>
```

配置新的输出版本路径，避免覆盖已批准包。内置打包器：

- 使用透明 PNG
- 不旋转素材
- 可补齐到 2 的幂尺寸
- 保存 region、pivot、state、component ID 和 slice
- 生成 Atlas PNG 与 JSON
- 更新 atlas contract 为 `packed`

打包完成后人工检查，再将状态改为 `approved`。

## 引擎 JSON

读取 `contracts/export-contract.yaml`，执行：

```bash
python3 scripts/export_engine_manifest.py specs/<project-id>
```

支持：

- Godot JSON：texture、region、patch margins
- Unity JSON：Sprite Multiple rect、pivot、border、pixels per unit
- Cocos JSON：frame rect、original size、cap insets
- Generic JSON：Atlas 与 sprite metadata

这些文件是确定性交付清单。原生 `.tres`、`.tscn`、Unity SpriteAtlas 和 Cocos 工程导入器不在内置实现范围内。

## Unity 使用边界

Unity JSON 使用左下角坐标，border 顺序为 `[left,bottom,right,top]`；本仓库 slice margins 使用 `[left,right,top,bottom]`，exporter 负责转换。原有旧版 Unity JSON 需要重新导出。
单张 PNG 可按 Sprite Single 导入；已打包图按 Multiple 使用清单 rect。单张源图可加入 Unity SpriteAtlas；已打包图可直接作为 Multiple texture 使用。不要把 PNG 图集声明为原生 `.spriteatlas`。
提供导入说明并在真实 Unity 中检查 9-slice、缩放、边缘采样、压缩和 TMP 排字。本轮不生成原生 Editor 导入器，JSON 不会自行修改 Unity 项目。

## 人工验收

- Atlas 无重叠、裁断和透明污染
- region 与源 PNG 尺寸一致
- 9-slice 留有可拉伸中心
- 所有语义名称唯一
- 引擎 JSON 引用同一 Atlas
- 禁止把 native project files 标记为已生成

## 完成定义（按入口验收）

- 页面契约管线：`atlas-contract.yaml` 状态为 `approved`
- Atlas PNG 与 JSON 存在
- 页面契约管线：`export-contract.yaml` 状态为 `approved`
- 每个目标引擎 JSON 存在并可解析
- 页面项目严格校验通过；独立包则校验输入 pack 和实际交付 ZIP，不创建不相关契约

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
