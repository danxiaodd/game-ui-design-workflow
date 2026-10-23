# 从已有策划开始视觉探索

这是方向阶段的说明示例，不含生成图片或伪造的用户批准。权威输入直接引用相邻 `../factory-v2-shop/gdd.md`，不复制该文件。

在仓库根目录运行：

```bash
python3 scripts/workflow_state.py /absolute/output/survivor-art init --source examples/factory-v2-shop/gdd.md
```

给 Agent 的请求：

```text
使用 $game-visual-direction，读取 examples/factory-v2-shop/gdd.md。
以原文确定的 2D 欧美卡通生存 Roguelike、战斗间隙补给商店为依据。
参考 examples/visual-exploration/source-brief.md 的标注方法，提出简洁方向案。
未确定的角色、世界、建筑设施不要当成已有游戏系统。
先明确推荐，完成后等我确认；暂不生成图片。
```

参考 `direction-example.md` 是候选方向的写法示范，不代表用户已选择。确认后再交给概念图技能。生图工具不可用时记录完整提示词为 pending-generation。

正式运行后的状态和历史放在用户输出目录，避免将机器绝对路径或示例确认混入真实项目。后续单页、透明素材、切图与 Unity 路径见 [使用说明](../../docs/SKILL_USAGE.zh-CN.md)。
