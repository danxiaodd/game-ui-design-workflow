# Game UI Design Workflow · Codex / Cursor

[![Validate](https://github.com/danxiaodd/game-ui-design-workflow/actions/workflows/validate.yml/badge.svg)](https://github.com/danxiaodd/game-ui-design-workflow/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

复用已有游戏策划，从美术视觉探索逐步制作、检查和交付游戏 UI 资源。支持 Codex 与 Cursor，无需 Figma。

**已有策划 → 美术视觉方向案 → 用户确认 → 代表性概念图 → 用户反馈 → 正式 UI 页面 → 用户确认 → 组件/素材 → 确定性切图 → Unity 等引擎交付。**

可以从任一已有阶段开始。指定一个页面、一个道具或一批图片时只完成相应任务；不要求重新创建 GDD、PRD 和交互三份文档。

## 安装

Python 3.10+，CI 使用 3.11。仅依赖 Pillow、PyYAML；无生图 SDK、API Key 或第三方设计服务要求。

```bash
git clone https://github.com/danxiaodd/game-ui-design-workflow.git
cd game-ui-design-workflow
python3 -m pip install -r requirements.txt

# Codex：项目安装（目标目录应已存在）
python3 scripts/install_skills.py --project /absolute/path/to/project --agent codex
# 或个人安装：~/.agents/skills
python3 scripts/install_skills.py --personal --agent codex

# Cursor：保留原安装入口及默认行为
sh install.sh --project /absolute/path/to/project
# Windows 可直接使用 Python 安装器
python scripts/install_skills.py --project C:/Projects/MyGame --agent cursor
```

默认跳过已有同名技能，升级可用 `--force`；预览可用 `--dry-run`。安装器一并部署版本化的脚本、模板、配置和许可证，已安装技能无需依赖原仓库的当前工作目录。旧运行包保留，避免影响被跳过的技能。

本仓库 `.agents/skills/` 的符号链接支持在仓库内直接发现 10 个技能。Windows 未启用 Git symlink 时，使用复制安装器安装到另一个项目。Codex 按[官方规范](https://learn.chatgpt.com/docs/build-skills)发现本地 Skill；需要时重启/重新加载宿主。CLI/IDE 中可用 `/skills` 或 `$技能名`；ChatGPT Work 使用自己的 Skill 安装与选择入口，GitHub 连接本身不会自动安装这些技能或共享本地文件。

## 从已有 GDD 开始

在 Codex 中：

```text
使用 $game-ui-workflow。
项目输出目录：/Projects/MyGame/art-workflow。
读取已有 /Projects/MyGame/Docs/GDD.md 及我指定的系统分册。
先提炼视觉需求，再给出简洁美术视觉方向案并明确推荐，完成后等待我确认。
区分已确定规则、推导/默认值和新增建议，不修改或复制原始策划。
```

方向案覆盖整体风格、人物比例、世界/场景/设施、UI、色彩材质光影及参考理由；首张概念图目标与提示词一起保存。方向确认后再实际生图，概念图不自动成为已批准的正式页面。

已有概念图可以直接说：

```text
使用 $game-ui-page-generator，参考我已认可的概念图，仅设计商店页面。
沿用现有玩法和风格，先完成一页并等待确认，不重新做整套策划。
```

## 技能

| 技能 | 职责 |
|---|---|
| `game-ui-workflow` | 状态恢复、最小路径和阶段编排 |
| `game-visual-direction` | 读取既有资料、简洁美术方向案 |
| `game-concept-image` | 实际代表图生成/编辑、版本与降级 |
| `game-ui-product-design` | 用户需要时编写策划/PRD/交互 |
| `game-ui-specification` | 设计令牌、布局、材质与状态规范 |
| `game-ui-extension` | 页面清单、导航与操作链路 |
| `game-ui-page-generator` | 单页设计、限定精修、视觉验收 |
| `game-ui-component-breakdown` | 组件复用、独立素材/规则合图生产 |
| `game-ui-sprite-sheet-splitter` | 区域/网格/Alpha 裁剪、连通检测、ZIP |
| `game-ui-asset-pipeline` | Atlas、9-slice、Unity/Cocos/Godot 交付 |

## 透明素材与程序切图

复杂道具/角色/装饰优先单独生成；重复小图标可按规则网格生成合图。优先使用实际工具支持的原生透明输出和编辑。当前模型与能力以宿主实际暴露工具为准；没有工具时保存提示词和待生成状态，不制造图片或假路径。

```bash
python3 scripts/inspect_image.py /path/to/actual.png --require-transparent
python3 scripts/process_sprites.py split /path/to/sheet.png \
  --layout config/grid-example.yaml --output /path/to/pack-v001
python3 scripts/process_sprites.py verify /path/to/pack-v001
```

`config/grid-example.yaml` 是示例参数，必须按真实图片布局调整。新工具支持 `grid`、`regions`、`trim`，输出独立 PNG、坐标/尺寸/哈希清单、联系表和 ZIP，拒绝覆盖已有版本。原有 `split_sprite_sheet.py` 保留用于 Alpha/纯色背景连通区域检测。

真实 Alpha 检查不等于边缘或艺术质量通过。复杂背景、粘连与遮挡可要求明确区域、独立素材或人工修正；不承诺无损恢复合成图的原始图层。

## Unity 交付

素材经过用户确认后：

```bash
python3 scripts/export_asset_pack.py /path/to/pack-v001 \
  --output /path/to/delivery-v001 \
  --review-evidence '用户确认该批素材版本的原话与记录位置'
```

交付包包含独立 PNG、Atlas PNG/JSON、Unity/Godot/Cocos JSON、SpriteAtlas 配置建议、来源记录、Unity 导入说明与 ZIP。Unity rect 已转为左下角坐标，border 为左/下/右/上。JSON/配置建议不会自动生成 Unity 原生 `.spriteatlas` 或修改工程；Editor 导入器是后续可选扩展。

原有 `build_sprite_atlas.py`、`export_engine_manifest.py` 和完整契约链路继续可用。

## 状态、确认与恢复

`workflow-state.json` 管阶段版本、来源、能力和确认依据；contracts/manifest 管资源细节。输出和提示词以不可覆盖 ID 保存在 `history/`，批准需要记录真实用户依据。单写入者操作；这是本地工作日志，不是身份认证或权限系统。

```bash
python3 scripts/workflow_state.py /path/to/project resume
```

状态区分待生成、已生成待传入、待确认、已确认及来源/父版本变化。图像成功但本地无法访问时保留真实结果引用，待传入后补登记，不重复生成。

## 示例、验证和边界

- [操作说明：三条可直接使用的路径](docs/SKILL_USAGE.zh-CN.md)
- [视觉探索示例：复用现有策划](examples/visual-exploration/README.md)
- [完整国风案例](examples/guofeng-card-rpg/) · [月宫案例](examples/moon-palace-rpg/) · [Factory v2 商店](examples/factory-v2-shop/)
- [兼容性与工具边界](docs/COMPATIBILITY.md) · [研究与取舍](docs/RESEARCH.zh-CN.md) · [验收记录](docs/VALIDATION.zh-CN.md)
- [原有 Factory v2 管线](docs/GAME_UI_FACTORY_V2.zh-CN.md) · [迁移说明](docs/MIGRATION.md)

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
python3 scripts/validate_skills.py .agents/skills
python3 scripts/validate_project.py examples/guofeng-card-rpg --strict
python3 scripts/validate_project.py examples/moon-palace-rpg --strict
python3 scripts/validate_project.py examples/factory-v2-shop --strict
```

自动化检查不证明真实生图、艺术质量或 Unity 导入已通过。实际运行时分别记录。项目仍为探索/草稿时不会假装生产契约已经严格验收。

保留上游 MIT 许可证与[来源说明](ORIGIN.md)。
