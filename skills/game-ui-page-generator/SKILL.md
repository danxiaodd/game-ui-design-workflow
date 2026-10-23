---
name: game-ui-page-generator
description: Designs and generates one complete game UI page at a time using an approved style and screen contract, producing a page brief, reproducible image prompt, negative constraints, an actual visual asset when image generation is available, and a manifest entry. Use for home, task, ranking, shop, inventory, character, event, reward, settlement, login, onboarding, HUD, or other game screens.
---

# 游戏 UI 单页视觉生成

一次只完成一个页面，继承项目契约，不把连续页面做成互不相关的风格稿。

独立调用时先恢复项目状态；没有 `workflow-state.json` 就运行 `workflow_state <project> init`，不要求 GDD。实际看过的既有概念图/源图可用 `source <path> --role visual-reference --evidence '<查看与用途>'` 登记。按本次入口登记产物，不依赖先运行总控。

## 前置条件

读取原策划/`source-brief.md`、已确认方向/概念图、项目已有样式与页面契约，以及当前用户范围。GDD/PRD/interaction 不要求按本仓库格式重新创建。

完整探索流程要求方向、概念图已获认可；用户明确指定一个页面时允许直接开始，在状态登记 `--direct-reason '<用户的单页任务范围>'`，补齐最小页面 brief 和局部风格默认值。没有证据时不假装某一张概念图已批准。

没有契约时按当前页需要创建最小样式/页面条目，不初始化与当前任务无关的页面。读取已有源文件中的交互规则，不另造玩法。
样式或布局待确认时输出 draft，不自行批准。

## 页面步骤

1. 确认页面 ID、目的、主操作、状态和比例；核对现有策划或交互资料中该页主流程。
2. 建立信息层级：主视觉、主操作、资源状态、导航、次级入口。
3. 具体说明顶部、中部、底部和悬浮区域，不只写通用布局名称。
4. 列出按钮、卡片、图标、角色、状态栏、导航、气泡和装饰。
5. 从样式契约注入色值、材质、光向、圆角、描边和字体策略。
6. 生成完整正向提示词和反向限制。
7. 图片工具可用时实际生图；不可用时保留提示词并降级。
8. 保存提示与图片，更新页面契约和资源清单。

## 提示文件

保存为 `prompts/pages/<screen-id>.md`，结构必须为：

```markdown
# <页面名称>

## 页面定位
## 视觉约束
## 布局与组件
## 状态
## 图像生成提示词
## 反向限制
## 验收记录
```

正向提示词必须包含：

- 页面名称、游戏类型、平台、比例和参考尺寸
- 顶中底及辅助区域的具体内容
- 主角色、场景或核心玩法焦点
- 契约中的色彩、材质、光源、圆角、描边和图标语言
- 可点击质感、信息层级、中文策略、画面质量
- 与已批准基准页保持一致的要求

反向限制至少包含：

- 乱码、错误文字、商标和未经授权角色
- 按钮变形、错误透视、元素粘连、主体遮挡
- 信息层级混乱、过度复杂、低清晰度
- 违反契约的色调、光向、材质或圆角

## 图片生成

图片工具可用时：

1. 使用工具支持的最接近比例。
2. 文件名使用 `<screen-id>-v<数字>.<ext>`。
3. 将结果保存到 `assets/pages/`。
4. 在 manifest 记录真实路径、尺寸、状态和版本来源。
5. 生图中文字不可读时，不通过验收；生成无文字底板或安排后期排字。

图片工具不可用时：

- 不创建假图片
- `status: pending-generation`
- `approved: false`
- 提示词路径必须有效

## 限定精修与 QA

区分新建设计、局部精修和只读评审。先锁定画布、安全区、主体、布局、既定内容及允许变化的模块；局部调整不能擅改其他模块。
先看修改模块，再看整屏，检查操作优先级、文字/数字可读性、背景是否抢焦点、状态是否可辨、同级对齐与材质一致性。通常两轮即可，残留问题如实登记，不进行无休止自评。
没有截图/输出证据的区域标记未验证；静态图不能证明真实交互可用。正式文本保留 Unity/TMP 排版空间，生成图中文字不可读时不验收。

记录 `workflow_state ... record <page-v001> --kind page --parent <approved-concept> --file <actual.png> --prompt <prompt.md>`；直接单页改用有实际依据的 `--direct-reason`。等待用户确认后单独执行 `approve`，再同步页面 manifest 的批准状态。

## 页面批准

只有同时满足以下条件才把 `approved` 设为 `true`：

- 主操作清楚，页面目的成立
- 比例、安全区和导航合理
- 契约中的视觉语言一致
- 关键状态有对应方案
- 文字可读或已明确采用后期排版
- 用户明确确认该页面版本，且批准依据已记录

## 输出

- 页面说明与提示文件
- 实际视觉稿或明确的待生成状态
- 更新后的 `screen-contract.yaml`
- 更新后的 `asset-manifest.yaml`
- 后续组件拆解建议

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
