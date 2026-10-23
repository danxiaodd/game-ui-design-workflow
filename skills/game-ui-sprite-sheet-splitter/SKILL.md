---
name: game-ui-sprite-sheet-splitter
description: Splits a generated game UI sprite sheet or component board into individual transparent PNG elements, writes crop metadata, validates dimensions and alpha channels, and packages all PNG files into a ZIP archive. Use after component breakdown when users ask to cut a combined sprite sheet, isolate every button/icon/card/effect, export single elements, remove a solid background, or deliver a downloadable PNG asset pack.
---

# 游戏 UI 雪碧图拆分与 PNG 打包

把组件拆解阶段生成的整张雪碧图进一步切成独立透明 PNG，并打包成可下载 ZIP。不要把“生成组件清单”误当成“已经完成像素级切图”。

独立调用时先恢复项目状态；没有 `workflow-state.json` 就运行 `workflow_state <project> init`，不要求 GDD。实际看过的既有概念图/源图可用 `source <path> --role visual-reference --evidence '<查看与用途>'` 登记。按本次入口登记产物，不依赖先运行总控。

## 前置条件

页面组件包任务读取已有的以下资料：

- 已批准的组件拆解结果
- `contracts/style-contract.yaml`
- `contracts/component-contract.yaml`
- `contracts/asset-manifest.yaml`
- `contracts/sprite-contract.yaml`（存在时）

独立图片批次任务只需实际源图、目标布局/区域、命名和输出要求；不要求先做组件拆解，也不要求 style/component/页面契约。

输入雪碧图必须是实际存在的图片文件。若只有提示词或组件列表，先完成组件图生成。

默认 UI 组件图形不带标题、按钮文案、数字标签和说明编号；文字优先交给 Unity/TMP。用户明确要求保留字形/数字素材时记录用途和例外，不自动抹掉原始内容。

## 适用输入

- 透明背景雪碧图：优先按 Alpha 通道识别。
- 纯色或近似纯色背景：采样四周背景色并移除。
- 同一张图上的按钮、图标、卡片、装饰、特效和角色。

不适合：

- 元素互相遮挡或粘连严重的完整 UI 页面。
- 带复杂场景背景且元素没有间隔的合成图。
- 需要恢复被遮挡像素的素材。

遇到这些情况，应重新生成留有间距的组件雪碧图，而不是强行切割。

## 输入雪碧图规范

组件生图时优先要求：

- 所有元素完整、互不接触、四周留白。
- 统一纯色背景或透明背景。
- 不要文字、编号、水印和说明线。
- 阴影不要跨越到相邻组件。
- 相似状态按固定顺序排列，但不绘制网格线。
- 不要把一个组件拆散成多个远离的碎片。

## 确定性裁剪优先

布局固定时先使用 `process_sprites split <source.png> --layout <layout.yaml> --output <new-version-dir>`：

```yaml
mode: grid
columns: 2
rows: 2
margin: 8
spacing: 8
names: [gold-icon, gem-icon, energy-icon, key-icon]
require_transparent: true
```

网格按从左到右、从上到下排列；尺寸必须整除。区域裁剪使用 `mode: regions`、`items: [{name: gold-icon, rect: [x, y, width, height]}]`，坐标从原图左上角计算。Alpha 裁剪使用 `mode: trim`、`name: gold-icon`、`padding: 4`，保留原始尺寸和偏移，不伪造缺失边缘。
脚本生成 PNG、源哈希/坐标清单、联系表和 ZIP；输出目录必须不存在。运行 `process_sprites verify <dir>` 校验数量、命名、尺寸、哈希及压缩包内容；再人工检查。
不同的剪裁版本使用不同目录，确认原始图片的实际布局后再写参数，不让模型猜网格。

## 原有连通区域拆分

执行：

```bash
python3 scripts/split_sprite_sheet.py <source.png> \
  --output-dir <project>/assets/sprites/<pack-id>/items \
  --zip <project>/packages/<pack-id>-png.zip \
  --mode auto \
  --prefix <pack-id>
```

默认行为：

1. 输入有透明通道时按 Alpha 检测。
2. 输入不透明时采样边缘背景色。
3. 合并距离较近的像素区域。
4. 过滤过小噪点。
5. 每个元素增加安全边距。
6. 导出独立透明 PNG。
7. 生成 `sprite-manifest.yaml`。
8. 生成包含 manifest 和全部 PNG 的 ZIP。

## 语义 mapping

自动序号不能作为最终资产名。准备按检测顺序排列的 YAML：

```yaml
items:
  - semantic_name: shop-buy-button-normal
    component_id: shop-buy-button
    category: button
    state: normal
    slice: {type: 9-slice, margins: [36, 36, 28, 28]}
```

执行时增加：

```bash
--mapping mappings/shop-components.yaml
```

工具会用 `semantic_name` 作为 PNG 文件名，并把组件 ID、分类、状态与 slice 写入 manifest。命名和切图方式分别遵循组件技能的语义命名规范与[切图规则](references/slice-rules.md)。

自动切割不会自动识别或修复文字。源雪碧图仍有文字时，先执行以下任一操作，再开始切割：

1. 优先重新生成无文字雪碧图。
2. 无法重生时，对文字区域做蒙版修复或内容填充，补回底板纹理。
3. 修复后重新检查，不能只把文字裁掉而留下透明洞、色块或残影。

不得把含非预期文字的切片标记为批准；明确授权的字形/数字素材按其用途验收。

## 参数调整

元素被拆得太碎：

```bash
--connect-gap 6
```

多个元素被粘成一张：

```bash
--connect-gap 0
```

背景残留：

```bash
--mode background --background-tolerance 16
```

浅色组件被误删：

```bash
--background-tolerance 8
```

小图标被过滤：

```bash
--min-area 16
```

需要更多裁切留白：

```bash
--padding 8
```

优先输出到新版本目录。仅在用户明确要求替换可丢弃的中间结果时使用旧脚本的 `--force`，不得覆盖已批准包。

## 项目契约

页面组件包将结果写入 `contracts/sprite-contract.yaml`；独立图片批次以输出的 `sprite-manifest.yaml` 为资源明细，不要求建立整套 UI 契约：

- 源雪碧图与源页面
- 检测模式和阈值
- 输出目录和 ZIP 路径
- 单元素 ID、路径、原图坐标、尺寸和透明状态
- 人工检查状态

在 `asset-manifest.yaml` 至少登记：

- 原始雪碧图：`kind: sprite-sheet`
- 最终压缩包：`kind: package`

单元素明细由 `sprite-contract.yaml` 管理，避免大型组件包让全局 manifest 失控。

## 人工验收

自动切图后逐项检查：

- 每个文件只包含一个完整元素。
- 元素没有被裁断。
- 相邻元素没有粘连。
- 阴影、发光和半透明边缘完整。
- 背景已透明，无白边、色边和脏点。
- 不含标题、按钮文案、数字标签、水印或文字残影。
- 文件名、坐标和尺寸与 manifest 一致。
- ZIP 可以解压，包含全部 PNG 和 manifest。

误切时先调整阈值重新生成；仍无法解决时，在 `sprite-contract.yaml` 记录人工裁切框，不要把错误结果标记为批准。

## 文件命名

```text
<pack-id>-001.png
<pack-id>-002.png
<pack-id>-003.png
...
<pack-id>-png.zip
```

确定组件语义后可重命名为：

```text
button-primary-default.png
nav-home-selected.png
currency-gold.png
effect-crescent-glow.png
```

重命名后同步更新 manifest，不能只改文件名。

## 完成定义

- 原始雪碧图可追踪
- 每个元素是独立透明 PNG
- 自动坐标和实际尺寸已记录
- 人工验收通过
- 默认无文字组件包记录 `review.text_free: true`；字形/数字任务记录明确例外
- ZIP 包存在且可解压
- 最终 PNG 使用语义名称；页面组件包还需关联 component ID
- 独立批次通过 `process_sprites verify`；完整 UI 项目通过契约严格校验
- 交付说明记录解压和使用方式；项目已有 `quickstart.md` 时更新该文件

需要继续生成 Atlas 和引擎 JSON 时，调用 `game-ui-asset-pipeline`。

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
