---
name: game-ui-workflow
description: Route game visual exploration and UI production from existing GDDs, approved concepts, individual pages or asset batches through visual direction, real concept generation, UI design, deterministic slicing and Unity/Godot/Cocos handoff. Use for multi-stage game art/UI work, resuming projects or choosing the next step; do not require rewriting existing planning docs.
---

# 游戏视觉与 UI 总控

先读取项目事实，再选择当前请求所需的最短路径。已有 GDD 是游戏规则权威；不覆盖、复制或重新编写原始策划，不将 AI 建议当成既定规则。

## 启动与恢复

1. 确定项目目录和用户本次范围。已有 `workflow-state.json` 时先运行 `workflow_state <project> resume`，读取待生成、待确认、版本依赖及变化的来源。
2. 读取用户指定的资料、参考和已有契约；只加载当前阶段需要的内容。
3. 新项目只做视觉探索时，运行 `workflow_state <project> init --source <existing-gdd>`。需要 UI 契约骨架时运行 `init_project <id> --visual --source <gdd> --workspace <output-collection>`。不生成重复的 GDD/PRD/交互文档。
4. 资料实际读完后用 `workflow_state <project> source <path> --evidence '<章节及提炼位置>'` 登记；哈希登记不等于已经阅读。
5. 当前环境重新检查图像生成/编辑、参考图传入、文件读取、Python/Pillow、预览工具。记录能力及证据，不继承另一台机器的可用状态；不自动索取 API Key 或引入服务。
6. 普通缺项采用标明的默认值，仅询问会阻断继续的关键问题。未获得资料读取能力时明确缺项，不编造原文。

## 路由

| 当前输入/目标 | 技能及路径 |
|---|---|
| 已有 GDD/系统分册，想看清游戏样貌 | `game-visual-direction` → 用户确认 → `game-concept-image` → 用户反馈 |
| 已批准方向，需要概念图 | `game-concept-image` |
| 已认可概念图，需要正式 UI | `game-ui-specification` → 必要的 `game-ui-extension` → `game-ui-page-generator` |
| 明确只设计一个页面 | 直接 `game-ui-page-generator`，补最小页面 brief 和局部风格，不重走 A–C |
| 已批准页面，需要素材 | `game-ui-component-breakdown` |
| 独立角色/道具/素材批处理 | 直接组件技能，记录独立任务范围，不强制提供源页面 |
| 已有图片，需要裁剪/切图 | `game-ui-sprite-sheet-splitter` |
| 需要 Atlas/9-slice/引擎交付 | `game-ui-asset-pipeline` |
| 用户明确需要编写策划 | 可选 `game-ui-product-design` |

子技能是按需加载的工作步骤，不代表另行启动 Agent。没有必要时不增加页面、管理工具或文档。

## A–E 工作流与停止条件

### A 读取既有策划

提炼定位、玩法、世界观、角色、场景、地标/家业设施、相机及 UI 需求。简短摘要写入 `source-brief.md`，使用「已确定（出处）／推导与默认／新增建议」标记。引用原资料位置，不复制整份策划。规则冲突以原文为准。

### B 视觉方向

由 `game-visual-direction` 形成简洁方向案：整体定位、人物比例、世界场景与设施、UI、色彩材质形状光影密度、推荐/排除方向、参考理由、首图目标和提示词。路线有实质差异时才给 2–3 个，始终明确推荐。**完成后停止等待用户确认，不自行开始概念图。**

### C 概念图

仅在方向得到确认后调用实际可用的图像工具。概念图独立登记为 `concept`，用于理解样貌；不自动成为正式 UI 或生产资产。工具缺失保存完整提示词为 `pending-generation`；生成结果无法传入本地时登记 `pending-transfer` 和真实结果引用。**展示后停止等待反馈。**

### D 正式 UI

视觉被认可或用户明确指定单页任务后，按需建立样式令牌、页面清单、布局、交互和状态。一次设计一个页面，保存 brief、提示词、实际图及版本。用真实视觉证据检查安全区、可读性、状态和一致性；用户确认后再生产该页组件。不得以脚本检查通过替代用户批准。

### E 素材与交付

优先规划独立背景、边框、装饰、图标和文字层。复杂素材独立生成，重复小素材可规则合图后程序切分。检查真实 Alpha、尺寸、边缘、完整性及来源；经确认的语义素材再进入 Atlas/9-slice/引擎清单。不承诺从完整合成图无损恢复图层。

## 状态与版本

- `workflow-state.json` 管阶段、能力、确认依据和不可覆盖的版本关系；原有 contracts/manifest 管组件、页面和资源细节，不再复制第二套完整清单。
- `workflow_state record` 保存输出/提示词副本到 `history/<version-id>/`；同 ID 拒绝覆盖。待生成提示词恢复时沿用已保存任务，实际返回后登记新版本并记录关联，不重复发起成功任务。
- `approve` 只在用户实际确认后执行，`--evidence` 写明原话、版本与上下文，禁止 AI 自签。该脚本记录依据，不能验证说话者身份，不是权限系统。
- 来源、提示词、父版本发生变化时先复核；不得重写旧版或把历史批准直接转给新稿。
- 独立页面/资产任务用 `--direct-reason` 记录用户实际范围；不将它作为完整流程绕过确认的借口。
- 单写入者运行状态命令，结束时运行 `validate_project <project>`。UI 契约阶段存在草稿时允许报告未完成项，不假装严格交付通过。

每次停下简要交代：完成了什么、真实产物、待确认版本、下一步及进入条件。无需输出冗长表单。

## 工具与文件边界

无需 Figma 账号、API、插件或文件；产物使用 Markdown/JSON/YAML/PNG/SVG，HTML 仅作可选预览。原有 Unity/Cocos/Godot 能力保留。技能不会赋予图像接口、浏览器、第三方服务或跨机器文件访问；必须逐项核实。

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
