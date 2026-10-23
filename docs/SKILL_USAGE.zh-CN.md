# 使用说明：Codex / Cursor

在仓库中运行以下命令；安装到其他项目后，将 `python3 scripts/<tool>.py` 替换为 `python3 <实际技能目录>/scripts/run.py <tool>`。该入口与当前工作目录无关。路径包含空格时按 shell 规则加引号。Windows 使用 `python`。

## 安装与发现

```bash
python3 -m pip install -r requirements.txt
python3 scripts/install_skills.py --project /Projects/MyGame --agent codex
# 或 --personal --agent codex；Cursor 使用 --agent cursor
```

Codex 项目/个人位置分别为 `.agents/skills`、`~/.agents/skills`；Cursor 为 `.cursor/skills`、`~/.cursor/skills`。安装时部署共享 runtime 的版本目录及每技能指针；不要手动只复制一个 SKILL.md。不要同时安装同名项目版与个人版造成重复选择。需要更新时用 `--force`；旧 runtime 留给仍引用它的技能，可在检查无引用后手动清理。

新建一个与仓库无关的项目目录后运行安装器，再让宿主列出 `game-ui-workflow` 等技能。宿主若没有重新加载技能，重启/重新加载；静态检查和安装测试不能证明每个宿主 UI 已实际调用。

## 路径一：已有 GDD → 方向 → 概念图

```text
使用 $game-ui-workflow，读取 /Projects/MyGame/Docs/GDD.md 和指定系统分册。
输出到 /Projects/MyGame/art-workflow。先给出美术视觉方向案，明确推荐并等待我确认。
原策划是规则依据，缺失的视觉信息使用标明默认值，不重做策划三文档。
```

Agent 先实际读取资料，提炼 `source-brief.md`：定位、玩法、世界观、角色、场景/设施、镜头与 UI。PDF/DOCX/图片按当前工具读取；读不了要说明。

```bash
python3 scripts/workflow_state.py /Projects/MyGame/art-workflow init --source /Projects/MyGame/Docs/GDD.md
python3 scripts/workflow_state.py /Projects/MyGame/art-workflow source /Projects/MyGame/Docs/GDD.md \
  --evidence '已读第1–4章；视觉提炼见 source-brief.md'  # 仅在真实读完后记录
```

方向案和首图提示词完成后登记：

```bash
python3 scripts/workflow_state.py /Projects/MyGame/art-workflow record direction-v001 \
  --kind direction --file /path/to/art-direction-v001.md --prompt /path/to/concept-prompt-v001.md
```

到此停止。`approve` 只在用户已经实际确认具体版本后执行，`--evidence` 保存原话/记录位置，不使用示例文字冒充真实批准。

```bash
python3 scripts/workflow_state.py /Projects/MyGame/art-workflow approve direction-v001 \
  --evidence '<真实用户确认方向 V001 的依据>'
```

确认后由 Agent 的**实际可用图像工具**调用生成/编辑，不是由状态脚本生成图像。模型未知则如实写 `unknown`。保存真实输出：

```bash
python3 scripts/workflow_state.py /Projects/MyGame/art-workflow record concept-v001 --kind concept \
  --parent direction-v001 --file /path/to/actual-concept.png --prompt /path/to/actual-prompt.md \
  --tool '<真实工具名>' --model '<实际模型或unknown>'
```

无工具时省略 `--file`，得到 `pending-generation`。已生成但无法传到本地时加 `--result-ref '<真实工具结果引用>'`，得到 `pending-transfer`。传入后使用新 ID，`--based-on concept-v001` 关联任务，不重跑成功生成。两个状态都不能批准为已完成。

展示概念图后再次等待反馈；确认概念图不会批准正式页面。视觉方向修改后保留旧版本，用新 ID 登记。

## 路径二：已有概念图 → 单页面 → 组件

```text
使用 $game-ui-page-generator，已有概念图 /Projects/MyGame/Refs/main-v2.png 已被我选定。
只设计商店页，沿用角色、材质和配色；完成后等待确认。
```

Agent 实际看图并读取玩法资料，建立目标页最小 brief 和必要的 style/screen contracts。局部精修先锁定不可变布局和本次允许修改模块。没有 GDD/PRD/interaction 模板也可以执行。

初始化完整 UI 契约骨架可用：

```bash
python3 scripts/init_project.py my-game --visual --source /Projects/MyGame/Docs/GDD.md \
  --workspace /Projects/MyGame/ArtWorkspaces
```

不会复制/生成三份规划文档。模板是草稿，Agent 按当前页面补实内容后才进入生产验收；`--force` 会刷新模板，不用于日常恢复。

全链路页面记录 approved concept 作为 `--parent`；用户明确只做单页时记录 `--direct-reason '<用户授权的本次单页范围>'`。输出始终先为 review。页面得到确认后再拆组件。

面板从生产阶段规划背景/边框/装饰/文字分开。复杂素材单独生成；小素材可规则合图。透明素材原生生成/编辑后运行真实 Alpha 检查，主体完整性和风格仍需看图。单独道具任务不要求虚构源页面，使用真实独立范围记录。

## 路径三：已有合图 → 确定性切分 → Unity

先检查原图实际像素：

```bash
python3 scripts/inspect_image.py /path/to/sheet.png --require-transparent --report /path/to/alpha-report-v001.json
```

报告包含真实尺寸、Alpha 是否存在、透明/不透明/半透明像素、可见边界和边缘触碰。全不透明 RGBA 和全透明空图不能通过透明素材要求。检查不能识别所有脏边、棋盘格绘图、色边或主体缺失；联系表和原图需人工查看。

网格布局（参数按真实图片调整）：

```yaml
mode: grid
columns: 2
rows: 2
margin: 8
spacing: 8
names: [gold-icon, gem-icon, energy-icon, key-icon]
require_transparent: true
```

区域裁剪：

```yaml
mode: regions
require_transparent: true
items:
  - name: primary-button-default
    rect: [20, 30, 200, 80]  # 左上角x/y、宽、高，单位像素
    component_id: primary-button
    category: control
    state: default
    slice: {type: 9-slice, margins: [12, 14, 10, 8]} # 左、右、上、下；须人工确认
```

Alpha 边界裁剪：

```yaml
mode: trim
name: potion-red
padding: 4
alpha_threshold: 0
require_transparent: true
```

默认阈值保留所有非零 Alpha。抬高阈值可能舍弃微弱发光边缘，需要人工确认。清单保留原始尺寸和偏移；裁剪不自动计算角色动画/物理锚点。

```bash
python3 scripts/process_sprites.py split /path/to/sheet.png --layout /path/to/layout.yaml --output /path/to/pack-v001
python3 scripts/process_sprites.py verify /path/to/pack-v001
```

输出：语义 PNG、`sprite-manifest.yaml`、`contact-sheet.png`、`sprites.zip`。ZIP 的 PNG 在 `items/` 下，联系表不属于生产 Sprite。目录必须是新版本；无效区域、非整除网格、重复/不安全命名、空素材会失败，不产生半成品交付目录。

布局不规则且对象分离清楚时可以沿用 `split_sprite_sheet.py` 的 Alpha/纯色背景连通检测。复杂背景用实际图像编辑能力、重新独立生成或明确区域处理；不能保证无损分离。

检查每件素材、半透明边缘和 9-slice 后，由用户确认该批版本，再运行：

```bash
python3 scripts/export_asset_pack.py /path/to/pack-v001 --output /path/to/delivery-v001 \
  --review-evidence '<真实用户确认该批素材版本的依据>' --ppu 100 --max-size 2048
```

交付包含独立 PNG、Atlas、三个引擎及 generic JSON、SpriteAtlas 配置建议、来源哈希、ZIP 和 `UNITY-IMPORT.md`。`--review-evidence` 是审计记录，不会认证说话者，也不能由 Agent 自签替代确认。

Unity 可选择独立 PNG Single 导入后由 Unity 建 SpriteAtlas，或已打包 PNG Multiple 并按 JSON rect 切分。不要将配置 JSON 重命名为 `.spriteatlas`。文字交给 TMP，9-slice 在 UGUI 的 Sliced 模式下检查。

## 既有契约与引擎导出

原有页面项目继续维护 style、screen、component、sprite、atlas、export contracts 和 asset-manifest。

```bash
python3 scripts/build_sprite_atlas.py /path/to/project
python3 scripts/export_engine_manifest.py /path/to/project
python3 scripts/validate_project.py /path/to/project --strict
```

先设置新的输出版本路径。Unity rect 已修正为左下角，border 为 `[left,bottom,right,top]`；内部 slice margins 仍为 `[left,right,top,bottom]`。历史 Unity JSON 应重新生成，Godot/Cocos 语义不变。

直接资产包用 `process_sprites verify` 和交付 ZIP 验证即可，不要求建立不相关的页面契约。探索期工作区可只含 workflow-state；只有进入完整 UI 契约阶段才要求对应文档齐全。

## 恢复与限制

```bash
python3 scripts/workflow_state.py /path/to/project resume
```

读取待生成/待传入/待确认和历史批准；修改输出、提示词、来源或批准父版本会被识别。来源变化先重新读取并登记，新设计用新版本；历史批准不自动转移。
状态文件只支持单写入者，不是并发数据库。来源绝对路径迁移后需重新定位并登记。GDD 格式解析和语义提炼由 Agent 及可用读取工具完成，哈希登记不表示已阅读。工作流脚本不调用模型 API。
