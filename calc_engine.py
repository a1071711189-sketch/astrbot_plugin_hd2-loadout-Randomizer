"""
calc_engine.py — Python 移植 democracy-hub.net 的 CalcEngine

基于 calc.jsx 的完整逻辑：
  - 每个武器对每种敌人有基础伤害值
  - 每个"Case"(子派系配置)定义敌人的出现权重(QTF)
  - 计算: Σ(基础伤害 × QTF) × Sustain修正 × Reload修正 × 职业修正
  - 输出 Light/Medium/Heavy 火力 + Support 分 = Power Score
"""

import json
from typing import Optional
from pathlib import Path

# ── 常量 (对应 CalcConfig) ──────────────────────────────
CLASS_MAP = {"light": "Light", "medium": "Medium", "heavy": "Heavy"}
CLASSES = ["Light", "Medium", "Heavy"]
SAFETY_FACTOR_VAL = 1.5


# ── 数据加载 ────────────────────────────────────────────
def _load_data():
    path = Path(__file__).parent / "data" / "game_data.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

_game_data = None

def get_game_data():
    global _game_data
    if _game_data is None:
        _game_data = _load_data()
    return _game_data


# ── 1. Scenario Data Extractor ────────────────────────────

def _get_scenario_data(enemy_cases, selected_case_name, enemy_map):
    """提取指定 Case 下的有效敌人及其 QTF 权重"""
    case_rows = [r for r in enemy_cases if r.get("case_name") == selected_case_name]
    if not case_rows:
        return None

    enabled_row = next((r for r in case_rows if r.get("factor") == "is_enabled"), None)
    comb_row = next((r for r in case_rows if r.get("factor") == "combined_qtf"), None)

    valid_enemies = []
    total_qtf_val = 0.0
    scenario_qtf = {"Light": 0.0, "Medium": 0.0, "Heavy": 0.0}

    for key in case_rows[0]:
        if key in ("id", "case_name", "factor"):
            continue
        if enabled_row and enabled_row.get(key) == 0:
            continue

        cls_raw = enemy_map.get(key, "").lower()
        cls_tag = CLASS_MAP.get(cls_raw)
        if not cls_tag:
            continue

        mass = float(comb_row.get(key, 0)) if comb_row else 0.0
        # 归一化权重: 用 normalised_combined_qtf 或 combined_qtf
        weight_row = next((r for r in case_rows if r.get("factor") == "normalised_combined_qtf"), comb_row)
        weight_val = float(weight_row.get(key, 0)) if weight_row else 0.0

        valid_enemies.append({
            "key": key,
            "name": key.replace("_", " "),
            "cls": cls_tag,
            "mass": mass,
            "weight": weight_val,
        })
        total_qtf_val += weight_val
        scenario_qtf[cls_tag] += weight_val

    return {"valid_enemies": valid_enemies, "total_qtf_val": total_qtf_val, "scenario_qtf": scenario_qtf}


# ── 2. Item Modifier Calculation ──────────────────────────

def _calculate_reload_modifier(item, reload_speed_mult=1.0):
    """Reload modifier: 缩短换弹时间提高持续火力"""
    mag_size = float(item.get("mag_size", 0) or 0)
    rpm = float(item.get("rpm", 0) or 0)
    reload_t = float(item.get("reload", 0) or 0)
    if mag_size <= 0 or rpm <= 0 or reload_t <= 0 or reload_speed_mult == 1.0:
        return 1.0
    new_reload = reload_t / reload_speed_mult
    mag_empty_time = mag_size / (rpm / 60.0)
    old_cycle = mag_empty_time + reload_t
    new_cycle = mag_empty_time + new_reload
    return old_cycle / new_cycle if new_cycle > 0 else 1.0


def _calculate_item_modifiers(item):
    """计算 Sustain × Reload 修正后的总倍率"""
    lu = float(item.get("limited_use", 1) or 1)
    ae = float(item.get("ammo_economy", 1) or 1)
    hn = float(item.get("handling", 1) or 1)
    sustain = lu * ae * hn

    reload_mult = _calculate_reload_modifier(item)

    total = sustain * reload_mult
    return {"sustain": sustain, "reload": reload_mult, "total": total}


# ── 3. Tactical Objective Score ──────────────────────────

def _calculate_tactical(item, objective_factors):
    """计算任务目标加权后的 Tactical 分数"""
    if not objective_factors:
        return 0.0

    total_tact = 0.0
    max_potential = 0.0

    for obj in objective_factors.values():
        norm_factor = float(obj.get("normalised_factor", 0) or 0)
        item_score = float(item.get(obj.get("objective_group", ""), 0) or 0)
        max_potential += norm_factor * 5.0
        if item_score > 0:
            total_tact += norm_factor * item_score

    if max_potential > 0:
        return (total_tact / max_potential) * 5.0
    return total_tact


# ── 4. Support Stats ──────────────────────────────────────

def _calculate_support(item, total_mod, tactical):
    """生存/效用/控制/战术 加权求和"""
    survival = (float(item.get("survival", 0) or 0)) * 1.5 * total_mod
    utility = (float(item.get("utility", 0) or 0)) * 0.6 * total_mod
    control = (float(item.get("control", 0) or 0)) * 0.9 * total_mod
    tactical_mod = tactical * 1.0 * total_mod

    total_support = survival + utility + control + tactical_mod
    return {
        "survival": survival,
        "utility": utility,
        "control": control,
        "tactical": tactical_mod,
        "total": total_support,
    }


# ── 5. 核心计算: 单物品 vs 派系+Case ─────────────────────

def calculate_item_power(item, enemy_cases, case_name, enemy_map, objective_factors, faction_key="bugs"):
    """
    计算单个装备在指定派系+Case下的综合得分

    参数:
        item: 装备 dict (含 enemy_scores_bugs/bots/squids)
        faction_key: "bugs" | "bots" | "squids" - 用于选择正确的 enemy_scores
    """
    scenario = _get_scenario_data(enemy_cases, case_name, enemy_map)
    if not scenario or not scenario["valid_enemies"]:
        return None

    valid_enemies = scenario["valid_enemies"]
    enemy_count = len(valid_enemies)

    # 缩放因子: 将总分映射到 0-15 范围
    max_fp = enemy_count * 5.0
    scale = 15.0 / max_fp if max_fp > 0 else 0.0

    # 各类别最大火力
    total_qtf = scenario["total_qtf_val"]
    max_class_fp = {}
    for cls in CLASSES:
        max_class_fp[cls] = (scenario["scenario_qtf"][cls] / total_qtf) * 15.0 if total_qtf > 0 else 0.0

    # 计算修正
    mods = _calculate_item_modifiers(item)
    total_mod = mods["total"]

    tactical = _calculate_tactical(item, objective_factors)
    support = _calculate_support(item, total_mod, tactical)

    # 对每个敌人的火力贡献
    enemy_scores = item.get(f"enemy_scores_{faction_key}", {})
    class_contribs = {"Light": 0.0, "Medium": 0.0, "Heavy": 0.0}

    for enemy in valid_enemies:
        key = enemy["key"]
        cls = enemy["cls"]
        base_score = float(enemy_scores.get(key, 0) or 0)
        weight = enemy["weight"]
        factored = base_score * weight * total_mod * scale
        class_contribs[cls] += factored

    firepower = sum(class_contribs.values())
    power = firepower + support["total"]

    return {
        "light": round(class_contribs["Light"], 4),
        "medium": round(class_contribs["Medium"], 4),
        "heavy": round(class_contribs["Heavy"], 4),
        "firepower": round(firepower, 4),
        "support": round(support["total"], 4),
        "power": round(power, 4),
        "support_detail": support,
    }


def calculate_loadout_power(loadout_items, enemy_cases, case_name, enemy_map, objective_factors):
    """
    计算整个负载的 Power Score (4个stratagem + weapons + armor + booster + grenade)

    loadout_items: list of item dicts
    """
    if not loadout_items:
        return None

    scenario = _get_scenario_data(enemy_cases, case_name, enemy_map)
    if not scenario:
        return None

    # 对每个item分别计算后求和
    item_results = []
    total_light = 0.0
    total_medium = 0.0
    total_heavy = 0.0
    total_support = 0.0

    for item in loadout_items:
        result = calculate_item_power(item, enemy_cases, case_name, enemy_map, objective_factors)
        if result:
            total_light += result["light"]
            total_medium += result["medium"]
            total_heavy += result["heavy"]
            total_support += result["support"]
            item_results.append(result)

    total_firepower = total_light + total_medium + total_heavy
    return {
        "light": round(total_light, 4),
        "medium": round(total_medium, 4),
        "heavy": round(total_heavy, 4),
        "firepower": round(total_firepower, 4),
        "support": round(total_support, 4),
        "power": round(total_firepower + total_support, 4),
        "item_results": item_results,
    }


# ── 6. Faction Weights ────────────────────────────────────

def get_faction_weights(enemy_cases, enemy_map, case_name):
    """计算指定Case下 Light/Medium/Heavy 敌人的权重分布"""
    scenario = _get_scenario_data(enemy_cases, case_name, enemy_map)
    if not scenario:
        return None

    total_qtf = scenario["total_qtf_val"]
    result = {}
    for cls in CLASSES:
        if total_qtf > 0:
            result[cls] = scenario["scenario_qtf"][cls] / total_qtf
        else:
            result[cls] = 0.0
    return result
