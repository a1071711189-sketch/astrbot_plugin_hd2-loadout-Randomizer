"""
Helldivers 2 - Factions & Brigades Data Model

每个派系有多个"旅"(Brigade/子派系)，对应不同的敌人组合和战术需求。
标签(tags)用于匹配装备的优势方向。
"""

# ── 通用标签 ──────────────────────────────────────────
# 装备/战备可以打上这些标签来标识其优势场景
# anti_swarm:    反虫群/反杂兵
# anti_armor:    反重甲 (Charger, Hulk, Tank, Harvester)
# anti_air:      反空中单位 (Shriekers, Gunships, Elevated Overseers)
# anti_elite:    反精英 (Bile Spewer, Devastator, Overseer)
# anti_structure:反建筑 (Bug Holes, Fabricators, Warp Ships)
# crowd_control: 控场 (EMS, Gas, 击退)
# mobility:      机动性 (Jump Pack, 轻甲)
# survivability: 生存力 (盾包, 重甲, 医疗)
# fire:          火焰伤害 (对虫子高效，对bot低效)
# explosive:     爆炸伤害 (对bot/鱿鱼高效)
# energy:        能量武器 (无限弹药，高温环境)
# precision:     精准 (Diligence, AMR 类)

FACTIONS = {
    "terminids": {
        "id": "terminids",
        "name": "Terminids",
        "name_cn": "终结族",
        "short": "Bugs",
        "short_cn": "虫族",
        "emoji": "🐛",
        "desc": "大量近战杂兵 + 重甲Charger + Bile Titan",
        "weakness_tags": ["fire", "crowd_control", "anti_swarm"],
        "resist_tags": ["explosive"],
    },
    "automatons": {
        "id": "automatons",
        "name": "Automatons",
        "name_cn": "机器人",
        "short": "Bots",
        "short_cn": "机器人",
        "emoji": "🤖",
        "desc": "远程火力 + 重甲Hulk/Tank + 空中Gunship",
        "weakness_tags": ["explosive", "anti_armor", "precision"],
        "resist_tags": ["fire"],
    },
    "illuminate": {
        "id": "illuminate",
        "name": "Illuminate",
        "name_cn": "光能者",
        "short": "Squids",
        "short_cn": "鱿鱼",
        "emoji": "🦑",
        "desc": "混合Voteless杂兵 + 精英Overseer + Harvester",
        "weakness_tags": ["anti_swarm", "anti_elite", "anti_armor"],
        "resist_tags": ["explosive"],
    },
}

BRIGADES = {
    # ── Terminids 各旅 ──
    "standard_terminids": {
        "id": "standard_terminids",
        "faction": "terminids",
        "name": "NORMAL",
        "name_cn": "标准",
        "short": "Standard Bugs",
        "desc": "标准虫族 - 混合杂兵+Charger+Bile Titan",
        "priority_tags": ["anti_swarm", "anti_armor", "crowd_control"],
        "avoid_tags": [],
    },
    "predator_strain": {
        "id": "predator_strain",
        "faction": "terminids",
        "name": "PREDATOR STRAIN",
        "name_cn": "掠食变种",
        "short": "Predator Strain",
        "desc": "掠食者变种 - 大量Stalker/Hunter，高速近战",
        "priority_tags": ["crowd_control", "anti_swarm", "mobility", "fire"],
        "avoid_tags": [],
    },
    "bile_spewers": {
        "id": "bile_spewers",
        "faction": "terminids",
        "name": "RUPTURE STRAIN",
        "name_cn": "爆裂变种",
        "short": "Bile Spewers",
        "desc": "胆汁喷射群 - 大量Spewer，需要远程+爆炸",
        "priority_tags": ["explosive", "anti_elite", "survivability"],
        "avoid_tags": ["fire"],
    },
    "charger_heavy": {
        "id": "charger_heavy",
        "faction": "terminids",
        "name": "RUPTURE STRAIN",
        "name_cn": "爆裂变种",
        "short": "Heavy Bugs",
        "desc": "重甲突击 - 大量Charger + Impaler + Bile Titan",
        "priority_tags": ["anti_armor", "anti_structure", "crowd_control"],
        "avoid_tags": [],
    },
    "nursing_spewers": {
        "id": "nursing_spewers",
        "faction": "terminids",
        "name": "SPORE BURST STRAIN",
        "name_cn": "孢裂变种",
        "short": "Nursery Bugs",
        "desc": "哺育喷射群 - 大量小虫 + Spewer混合",
        "priority_tags": ["anti_swarm", "anti_elite", "fire"],
        "avoid_tags": [],
    },
    # ── Automatons 各旅 ──
    "standard_automatons": {
        "id": "standard_automatons",
        "faction": "automatons",
        "name": "NORMAL",
        "name_cn": "标准",
        "short": "Standard Bots",
        "desc": "标准机器人 - 混合步兵+Devastator+Hulk+Tank",
        "priority_tags": ["anti_armor", "explosive", "precision"],
        "avoid_tags": ["fire"],
    },
    "jet_brigade": {
        "id": "jet_brigade",
        "faction": "automatons",
        "name": "JET BRIGADE",
        "name_cn": "喷气旅",
        "short": "Jet Brigade",
        "desc": "喷气旅 - 大量Jetpack步兵+空中单位",
        "priority_tags": ["anti_air", "anti_swarm", "mobility"],
        "avoid_tags": ["fire"],
    },
    "incineration_corps": {
        "id": "incineration_corps",
        "faction": "automatons",
        "name": "INCINERATION CORPS",
        "name_cn": "燃烧旅",
        "short": "Incinerators",
        "desc": "烈焰军团 - 大量火焰兵+爆炸单位",
        "priority_tags": ["survivability", "precision", "anti_elite"],
        "avoid_tags": [],
    },
    "heavy_devastators": {
        "id": "heavy_devastators",
        "faction": "automatons",
        "name": "NORMAL",
        "name_cn": "标准",
        "short": "Heavy Devs",
        "desc": "重装毁灭者 - 大量Heavy Devastator+盾牌兵",
        "priority_tags": ["anti_armor", "anti_elite", "explosive"],
        "avoid_tags": [],
    },
    "gunship_strider": {
        "id": "gunship_strider",
        "faction": "automatons",
        "name": "CYBORG LEGION",
        "name_cn": "赛博军团",
        "short": "Gunship/Strider",
        "desc": "空中+巨型 - 大量Gunship + Factory Strider",
        "priority_tags": ["anti_air", "anti_armor", "anti_structure"],
        "avoid_tags": ["fire"],
    },
    # ── Illuminate 各旅 ──
    "standard_illuminate": {
        "id": "standard_illuminate",
        "faction": "illuminate",
        "name": "NORMAL",
        "name_cn": "标准",
        "short": "Standard Squids",
        "desc": "标准光能者 - Voteless+Overseer+Harvester混合",
        "priority_tags": ["anti_swarm", "anti_elite", "anti_armor"],
        "avoid_tags": [],
    },
    "voteless_horde": {
        "id": "voteless_horde",
        "faction": "illuminate",
        "name": "MINDLESS MASSES",
        "name_cn": "无票者",
        "short": "Voteless Horde",
        "desc": "无票者潮 - 海量Voteless+少量精英",
        "priority_tags": ["anti_swarm", "crowd_control", "fire"],
        "avoid_tags": [],
    },
    "elevated_overseers": {
        "id": "elevated_overseers",
        "faction": "illuminate",
        "name": "APPROPRIATORS",
        "name_cn": "占领者",
        "short": "Flying Overseers",
        "desc": "飞行监管者 - 大量飞行精英+Harvester",
        "priority_tags": ["anti_air", "anti_elite", "precision"],
        "avoid_tags": [],
    },
    "harvester_heavy": {
        "id": "harvester_heavy",
        "faction": "illuminate",
        "name": "NORMAL",
        "name_cn": "标准",
        "short": "Heavy Harvs",
        "desc": "收割者重点 - 多个Harvester+精英掩护",
        "priority_tags": ["anti_armor", "anti_elite", "anti_structure"],
        "avoid_tags": [],
    },
}


def get_faction(faction_id: str):
    return FACTIONS.get(faction_id)

def get_brigade(brigade_id: str):
    return BRIGADES.get(brigade_id)

def get_brigades_for_faction(faction_id: str):
    return [b for b in BRIGADES.values() if b["faction"] == faction_id]

def get_all_faction_ids():
    return list(FACTIONS.keys())
