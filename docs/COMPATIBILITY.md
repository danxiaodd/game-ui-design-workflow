# 兼容性与验证边界

## Codex / Cursor

技能使用 `SKILL.md` 的 name/description 和按需引用。Codex 从项目/用户 `.agents/skills` 发现，支持符号链接；Cursor 保留 `.cursor/skills`。仓库内链接适合 Unix/Git symlink 环境，Windows 可用 Python 复制安装器。

安装器部署共享的版本化运行包和每技能 runner，离开原仓库仍能找到脚本及模板。不要只复制 SKILL.md；项目产物放到用户指定位置。Codex 的发现和元数据以[官方文档](https://learn.chatgpt.com/docs/build-skills)为准，安装路径测试不代表每个宿主已实际执行 Skill。

## 工具环境

- 本地 Codex、ChatGPT Work、其他 Agent 的图像工具、浏览器、凭据和文件系统不共享。
- 核实实际可调用的生成/编辑/参考图能力；模型未知就记录 unknown。
- 无工具：完整提示词 + pending-generation。
- 有真实结果但本地不可读取：真实结果引用 + pending-transfer，传入后补登记，不重复生成。
- 无 Figma、第三方服务或收费 API 前提。无需图像生成 SDK；本仓库的 Python 工具只做确定性本地处理。

官方截至 2026-10-23 的图像文档列出 GPT Image 2.5 Sunburst/Flare 透明输出和编辑支持；宿主暴露的参数及账号可调用能力需逐次核实，详见技能内 `image-capabilities.md`。

## Python / 文件

Python 3.10+；CI 3.11；依赖 Pillow、PyYAML。Windows 使用 python，macOS/Linux 常用 python3；shell 包装器不是 Windows 必需。

PNG/JPEG/WebP/GIF 通过 Pillow 读取真实尺寸与 Alpha 信息。PNG/WebP 声明透明时检查实际透明像素和非空主体；SVG 仅结构/尺寸校验，不等同渲染后的像素透明验收。新 process_sprites 仅导出 PNG，网格必须整除，裁剪区域不得越界。

无损矩形裁剪保留区域内像素；Alpha trim 的非零阈值会有意排除弱像素。纯色抠除不适合所有背景，复杂分离不能保证无损。

## 交付

图片、独立 Sprite、打包 Atlas PNG、引擎 JSON 与配置建议均为真实文件；不生成原生 Unity SpriteAtlas、Godot 场景或 Cocos 工程。Unity JSON 坐标/边距已修正，旧导出应重建。JSON 不会自动写入项目。

还需在目标引擎/设备检查边缘采样、压缩、文字、布局、状态和 9-slice。自动化测试、用户视觉确认、引擎导入与实机检查分别记录。

## 版本

既有 contracts 保持 schema_version 1；新增 workflow-state 是独立的版本日志。待确认输出不会自动批准；状态工具记录用户依据但不验证身份。状态采用原子文件替换，按单写入者使用；不支持多 Agent 同时写同一状态。
