"""
Helldivers 2 Loadout Randomizer - Core Engine v2

基于 democracy-hub.net CalcEngine 的真实游戏数据:
  - 每个装备对每种敌人的实际伤害值 (enemy_scores)
  - 每个 Case/旅 的敌人权重分布 (enemy_cases + enemy_map)
  - Power Score = Firepower(Light+Medium+Heavy) + Support

支持:
  - 派系/Case 选择与随机
  - Power Score 加权随机 (真实模拟驱动)
  - 槽位锁定
  - Warbond 过滤
  - 战备类别多样性
"""

import random
from typing import Optional
from pathlib import Path

from .data.factions import FACTIONS, BRIGADES, get_brigade, get_brigades_for_faction, get_faction
from .data.weapons import PRIMARIES, SECONDARIES, GRENADES
from .data.stratagems import STRATAGEMS
from .data.armors import ARMORS
from .data.boosters import BOOSTERS
from .data.warbonds import WARBONDS
from .calc_engine import calculate_item_power, get_game_data

# ── Case 名称映射 (DH API 名称 → 内部 Brigade ID) ──────────
# Democracy Hub uses specific case names; our brigades map to them
FACTION_CASES = {
    "terminids": ["NORMAL", "PREDATOR STRAIN", "RUPTURE STRAIN", "SPORE BURST STRAIN"],
    "automatons": ["NORMAL", "JET BRIGADE", "INCINERATION CORPS", "CYBORG LEGION"],
    "illuminate": ["NORMAL", "APPROPRIATORS", "MINDLESS MASSES"],
}

# Brigade → Case name mapping
BRIGADE_CASE_MAP = {
    "standard_terminids": "NORMAL",
    "predator_strain": "PREDATOR STRAIN",
    "bile_spewers": "RUPTURE STRAIN",
    "charger_heavy": "RUPTURE STRAIN",
    "nursing_spewers": "SPORE BURST STRAIN",
    "standard_automatons": "NORMAL",
    "jet_brigade": "JET BRIGADE",
    "incineration_corps": "INCINERATION CORPS",
    "heavy_devastators": "NORMAL",
    "gunship_strider": "CYBORG LEGION",
    "standard_illuminate": "NORMAL",
    "voteless_horde": "MINDLESS MASSES",
    "elevated_overseers": "APPROPRIATORS",
    "harvester_heavy": "NORMAL",
}

# ── 战备类别多样性配置 ───────────────────────────────────
STRATAGEM_CATEGORY_QUOTAS = {
    "support_weapon": (0, 2),
    "backpack": (0, 2),
    "orbital": (0, 3),
    "eagle": (0, 3),
    "sentry": (0, 3),
    "emplacement": (0, 2),
    "vehicle": (0, 2),
}


class LoadoutResult:
    def __init__(self):
        self.faction_id: str = ""
        self.faction_name: str = ""
        self.faction_name_cn: str = ""
        self.faction_emoji: str = ""
        self.case_name: str = ""
        self.brigade_name_cn: str = ""
        self.primary = None
        self.secondary = None
        self.grenade = None
        self.armor = None
        self.booster = None
        self.stratagems: list = []
        self.mode: str = "random"
        self.power_score: float = 0.0

    def format_for_chat(self) -> str:
        lines = []
        lines.append("══ Helldivers 2 Random Loadout ══")
        fc = self.faction_name_cn or self.faction_name
        bc = self.brigade_name_cn or self.case_name
        lines.append(f"🎯 Target: {self.faction_emoji} {fc} — {bc}")
        lines.append(f"⚙️  Mode: {self.mode.upper()}  |  Power: {self.power_score:.1f}")
        lines.append("")
        pn = self.primary.get("name_cn") or self.primary["name"]
        sn = self.secondary.get("name_cn") or self.secondary["name"]
        gn = self.grenade.get("name_cn") or self.grenade["name"]
        an = self.armor.get("name_cn") or self.armor["name"]
        bn = self.booster.get("name_cn") or self.booster["name"]
        lines.append("── Weapons ──")
        lines.append(f"  🔫 Primary:   {pn}")
        lines.append(f"  🔫 Secondary: {sn}")
        lines.append(f"  💣 Grenade:   {gn}")
        lines.append("")
        lines.append("── Gear ──")
        lines.append(f"  🛡️  Armor:    {an}")
        lines.append(f"  ⚡ Booster:   {bn}")
        lines.append("")
        lines.append("── Stratagems ──")
        for i, s in enumerate(self.stratagems, 1):
            sn = s.get("name_cn") or s["name"]
            cat = s.get("category", "?").replace("_", " ").title()
            lines.append(f"  {i}. {sn} [{cat}]")
        lines.append("")
        lines.append("═══ For Super Earth! ═══")
        return "\n".join(lines)


class LoadoutRandomizer:
    def __init__(self, seed=None):
        self.rng = random.Random(seed) if seed else random
        self._game_data = None

    @property
    def game_data(self):
        if self._game_data is None:
            self._game_data = get_game_data()
        return self._game_data

    def randomize(
        self,
        faction_id: Optional[str] = None,
        brigade_id: Optional[str] = None,
        locked_slots: Optional[dict] = None,
        warbond_ids: Optional[list] = None,
        exclude_warbond_ids: Optional[list] = None,
        exclude_items: Optional[dict] = None,
        mode: str = "random",
    ) -> LoadoutResult:
        locked_slots = locked_slots or {}
        result = LoadoutResult()
        result.mode = mode

        # Step 1: 确定派系
        faction = self._resolve_faction(faction_id)
        result.faction_id = faction["id"]
        result.faction_name = faction.get("name_cn", faction["name"])
        result.faction_emoji = faction["emoji"]

        # Step 2: 确定 Case
        if brigade_id and brigade_id != "random":
            case_name = BRIGADE_CASE_MAP.get(brigade_id)
            if not case_name:
                case_name = self._random_case(faction)
        else:
            case_name = self._random_case(faction)
        result.case_name = case_name

        # Map DH case name to Chinese if available
        case_cn = case_name
        for b in BRIGADES.values():
            if b.get("name", "").upper() == case_name.upper():
                case_cn = b.get("name_cn", case_name)
                break
        result.case_name = case_cn

        # 查找中文Case名
        for b in BRIGADES.values():
            if b.get("faction") == result.faction_id and b.get("name") == case_name:
                result.brigade_name_cn = b.get("name_cn", case_name)
                break
        if not result.brigade_name_cn:
            result.brigade_name_cn = case_name

        # Step 3: 获取派系战斗数据
        faction_data = self.game_data.get(faction["short"].lower(), {})
        enemy_cases = faction_data.get("enemy_cases", [])
        enemy_map = faction_data.get("enemy_map", {})
        objective_factors = faction_data.get("objective_factors", {})

        # Step 4: 构建候选池
        all_primaries = list(PRIMARIES.values())
        all_secondaries = list(SECONDARIES.values())
        all_grenades = list(GRENADES.values())
        all_stratagems = list(STRATAGEMS.values())
        all_armors = list(ARMORS.values())
        all_boosters = list(BOOSTERS.values())

        if warbond_ids:
            all_primaries = [w for w in all_primaries if w["warbond"] in warbond_ids]
            all_secondaries = [w for w in all_secondaries if w["warbond"] in warbond_ids]
            all_grenades = [w for w in all_grenades if w["warbond"] in warbond_ids]
            all_stratagems = [s for s in all_stratagems if s["warbond"] in warbond_ids]
            all_armors = [a for a in all_armors if a["warbond"] in warbond_ids]
            all_boosters = [b for b in all_boosters if b["warbond"] in warbond_ids]

        if exclude_warbond_ids:
            all_primaries = [w for w in all_primaries if w["warbond"] not in exclude_warbond_ids]
            all_secondaries = [w for w in all_secondaries if w["warbond"] not in exclude_warbond_ids]
            all_grenades = [w for w in all_grenades if w["warbond"] not in exclude_warbond_ids]
            all_stratagems = [s for s in all_stratagems if s["warbond"] not in exclude_warbond_ids]
            all_armors = [a for a in all_armors if a["warbond"] not in exclude_warbond_ids]
            all_boosters = [b for b in all_boosters if b["warbond"] not in exclude_warbond_ids]

        if exclude_items:
            exclude_ids = set(exclude_items.get("all", []))
            all_primaries = [w for w in all_primaries if w["id"] not in exclude_ids]
            all_secondaries = [w for w in all_secondaries if w["id"] not in exclude_ids]
            all_grenades = [w for w in all_grenades if w["id"] not in exclude_ids]
            all_stratagems = [s for s in all_stratagems if s["id"] not in exclude_ids]
            all_armors = [a for a in all_armors if a["id"] not in exclude_ids]
            all_boosters = [b for b in all_boosters if b["id"] not in exclude_ids]

        # Score function using real calc engine
        faction_key = faction["short"].lower()  # "bugs", "bots", "squids"
        def power_score(item):
            if f"enemy_scores_{faction_key}" not in item:
                return 0.1
            r = calculate_item_power(item, enemy_cases, case_name, enemy_map, objective_factors, faction_key)
            return r["power"] if r else 0.1

        # Step 5: 选择装备
        if "primary" in locked_slots:
            result.primary = PRIMARIES.get(locked_slots["primary"])
        if not result.primary:
            result.primary = self._weighted_choice(all_primaries, power_score)

        if "secondary" in locked_slots:
            result.secondary = SECONDARIES.get(locked_slots["secondary"])
        if not result.secondary:
            result.secondary = self._weighted_choice(all_secondaries, power_score)

        if "grenade" in locked_slots:
            result.grenade = GRENADES.get(locked_slots["grenade"])
        if not result.grenade:
            result.grenade = self._weighted_choice(all_grenades, power_score)

        if "armor" in locked_slots:
            result.armor = ARMORS.get(locked_slots["armor"])
        if not result.armor:
            result.armor = self._weighted_choice(all_armors, power_score)

        if "booster" in locked_slots:
            result.booster = BOOSTERS.get(locked_slots["booster"])
        if not result.booster:
            result.booster = self._weighted_choice(all_boosters, power_score)

        # Stratagems with diversity
        locked_strat_ids = set()
        for k, v in locked_slots.items():
            if k.startswith("stratagem") and v:
                locked_strat_ids.add(v)

        result.stratagems = self._pick_stratagems(
            all_stratagems, locked_strat_ids, power_score, mode
        )

        # Step 6: 计算总 Power Score
        all_items = [result.primary, result.secondary, result.grenade,
                     result.armor, result.booster] + result.stratagems
        all_items = [i for i in all_items if i]
        total_power = sum(power_score(i) for i in all_items)
        result.power_score = round(total_power, 1)

        return result

    def _resolve_faction(self, faction_id: Optional[str]):
        if faction_id and faction_id != "random":
            f = get_faction(faction_id)
            if f:
                return f
        return self.rng.choice(list(FACTIONS.values()))

    def _random_case(self, faction):
        faction_key = faction["id"]
        cases = FACTION_CASES.get(faction_key, ["NORMAL"])
        return self.rng.choice(cases)

    def _weighted_choice(self, items, score_fn):
        if not items:
            return None
        scores = [score_fn(item) for item in items]
        if all(s <= 0 for s in scores):
            return self.rng.choice(items)
        weights = [max(s, 0.01) ** 1.5 for s in scores]
        total_w = sum(weights)
        r = self.rng.uniform(0, total_w)
        cum = 0
        for item, w in zip(items, weights):
            cum += w
            if r <= cum:
                return item
        return items[-1]

    def _pick_stratagems(self, pool, locked_ids, score_fn, mode):
        result = []
        used = {}
        for sid in locked_ids:
            item = STRATAGEMS.get(sid)
            if item:
                result.append(item)
                cat = item.get("category", "other")
                used[cat] = used.get(cat, 0) + 1

        remaining = 4 - len(result)
        if remaining <= 0:
            return result[:4]

        for _ in range(remaining):
            valid = []
            for item in pool:
                if item in result:
                    continue
                cat = item.get("category", "other")
                quota = STRATAGEM_CATEGORY_QUOTAS.get(cat, (0, 3))
                if used.get(cat, 0) < quota[1]:
                    valid.append(item)
            if not valid:
                valid = [item for item in pool if item not in result]
            if not valid:
                break
            chosen = self._weighted_choice(valid, score_fn)
            result.append(chosen)
            cat = chosen.get("category", "other")
            used[cat] = used.get(cat, 0) + 1

        return result
