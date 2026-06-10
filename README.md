# HD2 Loadout Builder

《绝地潜兵 2》随机战备构建器 — AstrBot 插件。

基于 [democracy-hub.net](https://democracy-hub.net) 的真实游戏数据，为聊天机器人提供智能随机配装功能。

## 功能

- **派系识别**：Bugs / Bots / Squids，支持 9 种 Case（子派系）如 Jet Brigade、Predator Strain 等
- **真实评分**：每个装备对 30+ 种敌人的实际游戏伤害值 × 各 Case 的敌人权重矩阵 → Power Score
- **智能随机**：按 Power Score 加权随机，高分装备概率更高但保留多样性
- **槽位锁定**：锁定指定主武器/副武器/手雷/护甲/战备，只随机未锁定槽位
- **债券筛选**：按 Warbond 包含/排除，精确到单个物品
- **中文支持**：270 条装备完整汉化，输出中文名

## 指令

```
/loadout                     完全随机（随机派系 + 随机 Case）
/loadout bugs                虫子 + 随机 Case
/loadout bots jet            机器人 + Jet Brigade
/loadout squids              鱿鱼 + 随机 Case

/loadout --lock primary:scorcher secondary:senator
/loadout --warbond freedoms_flame,cutting_edge
/loadout --no-warbond base_game,superstore
/loadout --no sg_451_cookout

/loadout list factions
/loadout list warbonds
/loadout list weapons primary
/loadout details warbonds
/loadout details warbond freedoms_flame
/loadout help
```

## 输出示例

```
══ Helldivers 2 Random Loadout ══
🎯 Target: 🤖 Automatons — JET BRIGADE
⚙️  Mode: RANDOM  |  Power: 53.2

── Weapons ──
  🔫 Primary:   PLAS-1 焦土
  🔫 Secondary: P-4 参议员
  💣 Grenade:   G-123 铝热弹

── Gear ──
  🛡️  Armor:    强化（中）
  ⚡ Booster:   绝地喷射仓空间优化

── Stratagems ──
  1. "飞鹰"500KG炸弹 [Eagle]
  2. GR-8 无后座力炮 [Support Weapon]
  3. SH-32 防护罩生成包 [Backpack]
  4. A/AC-8 自动哨戒炮 [Sentry]

═══ For Super Earth! ═══
```

## 安装

将插件目录放入 AstrBot 的 `addons` 目录下，重启机器人即可。

## 数据结构

```
├── main.py                  # AstrBot 插件入口 & 指令注册
├── randomizer.py             # 随机器（Power Score 加权选择 + 多样性保证）
├── calc_engine.py            # democracy-hub CalcEngine Python 移植
├── localization_table.csv    # 装备汉化对照表
└── data/
    ├── game_data.json        # 原始游戏数据（283 装备 × 3 派系 × 敌人数值）
    ├── factions.py            # 派系/旅/Case 定义
    ├── weapons.py             # 主武器 + 副武器 + 手雷（93 件）
    ├── stratagems.py          # 战备（88 件）
    ├── armors.py              # 护甲（71 件，含重量级）
    ├── boosters.py            # 强化剂（18 件）
    └── warbonds.py            # 战争债券（28 个）
```

## 评分原理

不同于人工打分，本插件使用 **democracy-hub.net** 的完整战斗模拟数据：

1. 每个装备存储对每个敌人的**实际游戏伤害值**（`enemy_scores_bugs/bots/squids`）
2. 每个 Case 定义当前场景下**各敌人的出现权重**（QTF 矩阵）
3. 计算：`Σ(伤害 × 权重) × Sustain修正 × Reload修正 + Support分`

同一派系/Case 下 Power Score 越高的装备越适合，随机时按分数加权抽取。

## 数据更新

修改 `localization_table.csv` 后，运行重建脚本同步中文名到 `data/*.py`：

```
python rebuild.py
```

获取最新游戏数据（democracy-hub 更新后）：

```
# 重新抓取 fetch_rankings.php 并覆盖 data/game_data.json
```

## 致谢

- 装备数据源：[democracy-hub.net](https://democracy-hub.net)
- 插件框架：[AstrBot](https://github.com/AstrBotDevs/AstrBot)
