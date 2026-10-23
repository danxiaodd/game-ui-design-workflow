# 图像能力与环境边界

官方资料核查日期：2026-10-23。
- [Codex Skill 发现规范](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI 图像生成与编辑](https://developers.openai.com/api/docs/guides/image-generation)
- [Images API](https://developers.openai.com/api/reference/resources/images/methods/generate)

官方文档当前列出 `gpt-image-2.5-sunburst`、`gpt-image-2.5-flare` 的生成/编辑、透明背景和 PNG/WebP 输出支持。直接 API 使用 `background: transparent`；具体格式、模型、编辑输入和尺寸依实际接口规范核对。模型支持不等于账号/宿主当前能调用。

## 三层判断

| 层次 | 需要的证据 |
|---|---|
| 模型支持 | 当前官方文档支持生成/编辑/透明的具体参数 |
| 当前环境可调用 | 本次会话真实暴露的工具及参数；不要从其他会话或订阅推断 |
| 生成结果可交付 | 真实文件、像素检查、用户视觉验收与目标引擎检查 |

当前 ChatGPT Work 的内置生图工具可能允许透明背景但不暴露模型选择；如实记录实际工具、未知模型。工具参数与 API 参数不同，按工具说明执行，不能把 `background` 原样套入所有工具。
本地 Codex 可能有内置图像工具，也可能只有 shell；配置第三方工具或 API 是可选扩展。技能不共享 ChatGPT 会话、浏览器、凭据或文件系统。

## 素材生成/编辑

- 单独角色、复杂道具和装饰：原生透明输出，保留完整轮廓与安全边距，不要棋盘格背景。
- 多个小图标：明确行列、固定格子、间距、顺序、统一比例，不绘制网格/编号，生成后按实测布局确定切图参数。
- 背景移除/对象提取：使用真实编辑工具，保留原图并检查半透明阴影、主体颜色、细节与裁切。复杂合成图无法保证无损恢复图层。
- 按钮/面板：背景、边框、装饰、文字尽量在制作时分开；文字优先由 Unity/TMP 排版。
- 仅做像素裁剪不调用模型。网格或明确矩形优先 `process_sprites`，Alpha 连通区域使用原有 `split_sprite_sheet`。
- `inspect_image --require-transparent` 检查实际像素；带 Alpha 通道、显示棋盘格或外观像透明均不是充分证据。

调用前将能力和证据写入状态：`workflow_state <project> capability image-generation --status available --evidence '<本次实际工具和参数>'`。
工具失效时保留任务和结果，记录错误；只在实际重试必要时重试。不伪造成功，不静默切换收费服务。
