"""
Helldivers 2 Warbonds (战争债券) - Auto-generated from localization_table.csv
"""

WARBONDS = {
    "base_game": {
        "id": "base_game",
        "name": "other",
        "name_cn": "other",
    },
    "borderline_justice": {
        "id": "borderline_justice",
        "name": "Borderline Justice",
        "name_cn": "临界正义",
    },
    "chemical_agents": {
        "id": "chemical_agents",
        "name": "Chemical Agents",
        "name_cn": "化学专家",
    },
    "control_group": {
        "id": "control_group",
        "name": "Control Group",
        "name_cn": "变量控制",
    },
    "cutting_edge": {
        "id": "cutting_edge",
        "name": "Cutting Edge",
        "name_cn": "遥遥领先",
    },
    "democratic_detonation": {
        "id": "democratic_detonation",
        "name": "Democratic Detonation",
        "name_cn": "民主爆破",
    },
    "dust_devils": {
        "id": "dust_devils",
        "name": "Dust Devils",
        "name_cn": "尘卷风",
    },
    "entrenched_division": {
        "id": "entrenched_division",
        "name": "Entrenched Division",
        "name_cn": "堑壕之师",
    },
    "exo_experts": {
        "id": "exo_experts",
        "name": "Exo Experts",
        "name_cn": "外骨骼装甲专家",
    },
    "force_of_law": {
        "id": "force_of_law",
        "name": "Force Of Law",
        "name_cn": "法律铁腕",
    },
    "freedoms_flame": {
        "id": "freedoms_flame",
        "name": "Freedom's Flame",
        "name_cn": "自由烈焰",
    },
    "halo": {
        "id": "halo",
        "name": "Halo",
        "name_cn": "民主光环驰援部队",
    },
    "helldivers_mobilise": {
        "id": "helldivers_mobilise",
        "name": "Helldivers Mobilise !",
        "name_cn": "绝地潜兵总动员！",
    },
    "killzone": {
        "id": "killzone",
        "name": "Killzone",
        "name_cn": "正义复仇者",
    },
    "masters_of_ceremony": {
        "id": "masters_of_ceremony",
        "name": "Masters Of Ceremony",
        "name_cn": "典礼官",
    },
    "polar_patriots": {
        "id": "polar_patriots",
        "name": "Polar Patriots",
        "name_cn": "极地爱国者",
    },
    "python_commandos": {
        "id": "python_commandos",
        "name": "Python Commandos",
        "name_cn": "蟒蛇突击兵",
    },
    "redacted_regiment": {
        "id": "redacted_regiment",
        "name": "Redacted Regiment",
        "name_cn": "绝密军团",
    },
    "servants_of_freedom": {
        "id": "servants_of_freedom",
        "name": "Servants Of Freedom",
        "name_cn": "自由公仆",
    },
    "ship_stratagems": {
        "id": "ship_stratagems",
        "name": "Stratagem",
        "name_cn": "舰船",
    },
    "siege_breakers": {
        "id": "siege_breakers",
        "name": "Siege Breakers",
        "name_cn": "破围先锋",
    },
    "standard_issue": {
        "id": "standard_issue",
        "name": "new",
        "name_cn": "新兵",
    },
    "steeled_veterans": {
        "id": "steeled_veterans",
        "name": "Steeled Veterans",
        "name_cn": "铁血老兵",
    },
    "super_citizen": {
        "id": "super_citizen",
        "name": "Super Citizen",
        "name_cn": "超级公民DLC",
    },
    "superstore": {
        "id": "superstore",
        "name": "Superstore",
        "name_cn": "超级商店",
    },
    "truth_enforcers": {
        "id": "truth_enforcers",
        "name": "Truth Enforcers",
        "name_cn": "真理执行者",
    },
    "urban_legends": {
        "id": "urban_legends",
        "name": "Urban Legends",
        "name_cn": "都市传奇",
    },
    "viper_commandos": {
        "id": "viper_commandos",
        "name": "Viper Commandos",
        "name_cn": "毒蛇突击队",
    },
}


def get_warbond(wid: str):
    return WARBONDS.get(wid)

def get_all_warbond_ids():
    return list(WARBONDS.keys())