---
name: game-concept-image
description: Generate or revise a representative game concept image from a user-approved visual direction using the current environment's real image tool. Use to confirm overall game appearance before formal UI; preserve prompts, actual output versions and feedback, or mark generation/transfer pending when unavailable.
---

# 游戏代表性概念图

概念图用于确认游戏整体样貌，类型始终是 `concept`。不自动登记为正式 UI、可编辑图层或最终开发素材。

## 执行

1. 恢复项目状态，读取原策划摘要、已批准方向和所选参考。确认方向版本的批准依据，缺少时停止并交回 `game-visual-direction`。
2. 按[生成能力与边界](references/image-capabilities.md)核实当前工具。优先当前可用的内置图像生成/编辑；不要求用户为了工作流额外购买 API，不猜工具实际模型。
3. 选择最具代表性的主城、主界面、核心玩法或其他画面。沿用既定游戏规则、镜头和视觉；提示词明确目的、构图、主体、层次、UI 比重、比例和排除项。
4. 将实际提示词保存为 `prompts/concepts/<id>-v001.md`，注明实际传入的参考文件/版本、工具参数、目标尺寸。提示中写了“参考 V2”不能代替真实传图。
5. 工具可用则实际调用。编辑前查看原图；记录编辑底稿。以实际输出尺寸登记，不把目标尺寸当成结果尺寸。
6. 输出文件可访问时：`workflow_state <project> record concept-v001 --kind concept --parent direction-v001 --file <actual.png> --prompt <prompt.md> --tool <actual-tool> --model <actual-or-unknown>`。在项目保存真实输出，再填写全局资源清单（存在时）。
7. 工具不可用时，省略 `--file` 保存相同记录，状态为 `pending-generation`，保留完整提示词。不制造空 PNG 或虚构路径。
8. 已生成但图像仅保存在另一个环境时，保存实际 `--result-ref <tool-result-reference>`，状态为 `pending-transfer`；不要再次生成以补登记。待文件真实传入后登记新版本，用 `--based-on <待传入版本ID>` 关联原任务。
9. 展示实际图或明确待生成/待传入状态，**停止等待用户反馈**。

用户认可后只批准概念图。下一步 `game-ui-specification`/页面设计仍需建立正式页面要求；概念图批准不能批准不存在的页面。用户修改时生成新版本，用 `--based-on <旧版本ID>` 记录底稿/来源，保留所有旧版。

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
