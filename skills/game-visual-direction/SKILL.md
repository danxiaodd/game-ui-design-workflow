---
name: game-visual-direction
description: Read existing GDDs, system documents and references to propose a concise game-wide art direction with explicit source facts, visual defaults and recommendations. Use before concept images when the user needs to decide the game's look; do not rewrite game planning or require a PRD.
---

# 游戏美术视觉方向案

读取用户指定资料和已有决定，帮助用户看清整体视觉。先完成可决策的简洁方案，暂不编写几十页生产规范。

1. 读已有 `workflow-state.json` 和来源文件。MD/TXT 直接阅读，PDF/DOCX 用当前可用读取工具；图片用实际看图能力。无法读取则列出缺口，不声称已读。项目内路径、用户授予的外部路径都可以引用。
2. `workflow_state <project> init --source <gdd>` 只登记来源、不复制原文。实际读完后运行 `source <gdd> --evidence '<章节及摘要位置>'`。其他参考资料设置 `--role visual-reference`。
3. 在 `source-brief.md` 提炼定位、玩法、世界观、角色、相机、场景、地标/家业设施、UI 与技术限制。仅保留视觉必需摘要和出处。
4. 将每条关键信息标为「已确定／推导与默认／新增建议」。不凭空增加经济、角色职业、建筑玩法或系统规则。非适用的角色/设施字段写明不适用。
5. 使用[方向案模板](references/art-direction-template.md)形成 `art-direction-v001.md`。可采用现有项目文件名；避免重复建立平行文档。
6. 根据玩法可读性、角色识别、镜头和平台给明确推荐。需要对比时给少量实质不同路线；不为凑数量生成近似候选。
7. 参考图必须实际查看才下视觉结论，记录来源、借鉴部分和排除部分。没有图像检索能力时可以列待查参考，不伪造已看图片。可生成静态参考板；不要求安装交互编辑器。
8. 准备首张概念图的目标与完整提示词。根据游戏选择主城、主界面、核心玩法等代表画面，说明它要帮助决定什么。
9. `workflow_state <project> record direction-v001 --kind direction --file <direction.md> --prompt <prompt.md>`。
10. **提交方案后停止，等待用户确认；不提前生图。** 用户明确认可后才 `approve direction-v001 --evidence '<用户原话与版本>'`，进入 `game-concept-image`。

只询问没有合理默认且阻断设计的问题。已有方向或只做局部素材时直接沿用，不能强迫重走全项目方向阶段。Figma 不作为依赖。

## 可移植脚本调用（Codex / Cursor）

以下 `<SKILL_DIR>` 取本次实际加载的 SKILL.md 所在绝对目录。

```bash
python3 <SKILL_DIR>/scripts/run.py <tool_name> <arguments>
```

本文所有 `python3 scripts/<tool_name>.py ...` / `<tool_name> ...` 命令均可用以上方式执行；工具名不带 `.py`。入口自动定位仓库或安装时一起部署的 runtime，不要求当前目录恰好是本仓库。模板/配置在 runtime 内，工作产物使用用户项目的绝对路径；`init_project` 用 `--workspace` 指定输出集合。优先恢复状态，生成与批准分别登记；无需 Figma。
