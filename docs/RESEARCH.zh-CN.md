# 仓库审计与参考取舍

审计日期：2026-10-23。仅修改 `danxiaodd/game-ui-design-workflow` 的 `codex/visual-to-unity` 分支；不修改上游，不合并、不发布。

## 固定版本与实际阅读

| 仓库 | 本次读取提交 | 实际查看内容 | 采纳 |
|---|---|---|---|
| guiguiyan930-source/game-ui-design-workflow（Fork 同基线） | `1ec604638dd1a27198576206eb3e47632725a078` | 8 个 Skill、安装器、初始化/校验、split_sprite_sheet、build_sprite_atlas、export_engine_manifest、契约模板、测试/CI/示例 | 保留原有页面/组件/语义映射/Atlas/三引擎 JSON；策划改为可选 |
| openaigames/OpenAIGamesDesigner | `bf30148e34f259ed8fbf8d1498cb0f8d6d7d4bd3` | game-art-direction 与 game-ui-ux；generation-tool-selection、asset-versions；moodboard.py 与相关目录 | 体验→视觉决定、参考用途/排除项、实际工具边界、不可覆盖版本、选用/验收/接入分离 |
| moli20050328-opsa/game-gui-designer | `cc641cbde50a61b31116ecf5a1636eda052840f2` | SKILL、GUI 原则与 QA 清单、Figma 交付路径 | 局部范围约束、信息权重、模块→整屏检查、缺证据标未验证；不引入 Figma/PSD 路径 |
| ybuild-ai/ai-game-art-pipeline-skill | `ed4a2ce1a94370d5962c7d079cd9404a863e02c7` | SKILL、provider_stub.py、chroma_key_magenta.py、sheet_contact.py、static-assets/runtime-shipping 参考 | 按运行用途选生产方法、优先复用、小批代表素材、确定性后处理、联系表与引擎检查 |

链接：
- [原始工作流](https://github.com/guiguiyan930-source/game-ui-design-workflow)
- [OpenAIGamesDesigner](https://github.com/openaigames/OpenAIGamesDesigner)
- [game-gui-designer](https://github.com/moli20050328-opsa/game-gui-designer)
- [AI Game Art Pipeline Skill](https://github.com/ybuild-ai/ai-game-art-pipeline-skill)

上述版本为本次 clone 的 HEAD，不声称未来仍为最新。研究不仅看 README：OpenAIGamesDesigner 确有本地图板代码；AI Game Art 的提供方入口是接口桩，不等于已接通模型；联系表不是最终素材切分交付器；抠色不保证复杂图像无损分离。没有移植整套框架或复制参考项目实现。

## 原仓库问题与改造

- 总控/页面/延展/校验强制策划三文档：改为引用现有来源，新增方向、概念图技能。
- Cursor-only 安装且只复制 skills：增加 Codex 安装及版本化运行包，外部项目真实执行验证。
- 切图已有连通检测，无指定矩形/明确网格 CLI：新增确定性处理器，保留原脚本，修复失败前清理旧输出及透明标记问题。
- Alpha 仅结构检查：增加真实像素和空图检查；边缘/艺术质量仍人工检查。
- 只有契约维护建议：新增来源哈希、确认依据、版本历史与恢复；不把日志描述成安全授权系统。
- Unity JSON 直接复用上方原点 region 与内部 margins：转换到 Unity 的左下角和左/下/右/上顺序，保留 Godot/Cocos 路径。
- 基线 25 项测试中 3 项失败：安装测试写死 7 个技能，实际已有 8 个；改成动态发现并补安装/流程/像素回归。

## 官方依据与选择

- [Skill 结构、发现与安装目录](https://learn.chatgpt.com/docs/build-skills)：name/description、按需资源、`.agents/skills` 与可选 openai.yaml。
- [OpenAI 图像生成](https://developers.openai.com/api/docs/guides/image-generation)：当前 GPT Image 2.5 Sunburst/Flare 透明输出及编辑；宿主工具未必暴露同样参数或可选模型。
- [Unity 2022.3 Sprite.Create](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Sprite.Create.html) 与 [border](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/SpriteMetaData-border.html)：像素 rect 自下而上、border 为左/下/右/上。

## 本轮范围

无 Figma，无交互 Moodboard 编辑器，无额外云服务/SDK；静态方向案/参考图组织与既有契约足够。Unity 提供真实图片、Sprite/Atlas 数据和导入配置说明，原生 Editor 导入器留作可选扩展。所有真实生图、视觉检查、Editor/实机验证均单独记录，自动化测试不能替代。
