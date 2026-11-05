---
name: game-ui-product-design
description: Write or revise game design docs, PRDs and UI interaction specifications only when the user requests planning work. Use for 游戏策划、PRD、产品需求、交互流程、状态机; existing planning documents should be read by the visual workflow without requiring this skill or rewriting them.
---

# 可选的游戏策划、PRD 与交互设计

只在用户需要编写或修改策划时执行。已有 GDD/系统分册进入视觉探索应调用 `game-visual-direction`，不以缺少本仓库格式的三份文件阻断。

## 输入和范围

读取用户指定原资料、项目摘要、既有决定和页面契约。确认本次授权修改哪些文件；原始外部策划未获修改授权时只引用，不覆盖。不要求同时生成三份文档。

## 按需产物

- `gdd.md`：一句话定位、目标玩家、核心循环、系统及优先级、经济与养成概述、世界观与约束。不假装已有服务端公式。
- `prd.md`：目标、非目标、P0/P1/P2、页面范围、数据依赖、边界与验收要求。
- `interaction.md`：导航、分页面目的与进出、操作流程、控件行为、默认/加载/空/失败/锁定等状态、跨页链路。

沿用已有文档位置。新建时可从 runtime 的 `templates/spec-kit/` 选需要的模板，不另起重复权威来源。未知但非阻断信息使用标注默认值。

## 检查与确认

核心玩法、页面范围和操作状态互不矛盾；新建议与既定规则明确区分。先保持 `draft`，输出需要用户决定的内容并停止。仅在用户明确批准实际文档后记录批准依据；不要把生成文档视为批准。

规划完成后按实际需求进入视觉方向或正式 UI，不强制从头重走。

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
