from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import *

from .randomizer import LoadoutRandomizer
from .preset_manager import load_preset, save_preset, delete_preset, apply_preset
from .data.factions import FACTIONS, BRIGADES, get_brigades_for_faction
from .data.warbonds import WARBONDS
from .data.weapons import PRIMARIES, SECONDARIES, GRENADES
from .data.stratagems import STRATAGEMS
from .data.armors import ARMORS
from .data.boosters import BOOSTERS

HELP_TEXT = """
═══ Helldivers 2 Loadout Builder ═══

Commands:
  /loadout              Random loadout (random faction)
  /loadout bugs         Random loadout vs Terminids
  /loadout bots         Random loadout vs Automatons
  /loadout squids       Random loadout vs Illuminate
  /loadout random       Same as no argument

Options (add after faction):
  --lock primary:scorcher secondary:senator   Lock specific slots
  --warbond freedoms_flame                    Only use items from these bonds
  --no-warbond base_game,superstore           Exclude these bonds from pool
  --no sg_451_cookout,flam_40_flamethrower    Exclude specific items by ID
  --mode optimized                            Auto-optimize synergy

Preset (per-user saved filters):
  /loadout preset set --no-warbond exo_experts
  /loadout preset set --lock primary:scorcher
  /loadout preset show
  /loadout preset clear

Details:
  /loadout details warbond freedoms_flame     Show all items in a warbond
  /loadout details warbonds                  List all warbonds with counts

Other:
  /loadout list factions
  /loadout list weapons
  /loadout help
"""



@register("helloworld", "HD2 Loadout Builder", "Helldivers 2 随机负载构建器", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.randomizer = LoadoutRandomizer()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    @filter.command("loadout")
    async def loadout_command(self, event: AstrMessageEvent):
        """Helldivers 2 随机负载构建器 - 主指令"""
        message_str = event.message_str.strip()
        user_id = event.get_sender_id()
        logger.info(f"[HD2] user={user_id} raw_msg={message_str}")
        # 移除指令前缀和命令词
        parts_all = message_str.split()
        # 找到 "loadout" 的位置，取其后内容
        try:
            idx = [p.lower() for p in parts_all].index("loadout")
            args_str = " ".join(parts_all[idx + 1:])
        except ValueError:
            args_str = ""

        logger.info("[HD2] user={} args={}".format(user_id, repr(args_str)))

        if not args_str or args_str.lower() in ("random", ""):
            user_id = event.get_sender_id()
            preset = apply_preset(user_id)
            logger.debug(f"[HD2] user={user_id} no-args roll, preset={preset}")
            result = self.randomizer.randomize(
                faction_id="random",
                exclude_warbond_ids=preset.get("exclude_warbond_ids"),
                exclude_items=preset.get("exclude_items"),
                locked_slots=preset.get("locked_slots"),
            )
            logger.debug(f"[HD2] no-args result: faction={result.faction_id} case={result.case_name} power={result.power_score}")
            yield event.plain_result(result.format_for_chat())
            return

        # 解析子命令
        parts = args_str.split()
        first = parts[0].lower()

        # 帮助
        if first in ("help", "h", "?"):
            yield event.plain_result(HELP_TEXT)
            return

        # 列出信息
        if first == "list":
            yield event.plain_result(self._handle_list(parts[1:]))
            return

        # 详情命令
        if first == "details":
            yield event.plain_result(self._handle_details(parts[1:]))
            return

        # 预设命令
        if first == "preset":
            yield event.plain_result(self._handle_preset(parts[1:], event))
            return

        # 解析参数
        faction_id = None
        brigade_id = None
        locked_slots = {}
        warbond_ids = None
        exclude_warbond_ids = None
        exclude_items = None
        mode = "random"

        # 派系识别
        faction_aliases = {
            "bugs": "terminids", "bug": "terminids", "terminids": "terminids", "🐛": "terminids",
            "bots": "automatons", "bot": "automatons", "automatons": "automatons", "🤖": "automatons",
            "squids": "illuminate", "squid": "illuminate", "illuminate": "illuminate", "🦑": "illuminate",
            "random": "random",
        }

        i = 0
        if parts and parts[0].lower() in faction_aliases:
            faction_id = faction_aliases[parts[0].lower()]
            i = 1

        if faction_id and faction_id != "random":
            # 旅识别
            brigade_aliases = {}
            for bid, bdata in BRIGADES.items():
                if bdata["faction"] == faction_id:
                    for word in bdata.get("short", "").lower().split():
                        brigade_aliases[word] = bid
                    brigade_aliases[bid] = bid

            if i < len(parts) and parts[i].lower() in brigade_aliases:
                brigade_id = brigade_aliases[parts[i].lower()]
                i += 1

        # 解析选项参数
        current_option = None
        while i < len(parts):
            part = parts[i]

            if part == "--lock":
                current_option = "lock"
                i += 1
            elif part == "--warbond":
                current_option = "warbond"
                warbond_ids = []
                i += 1
            elif part == "--no-warbond":
                current_option = "no_warbond"
                exclude_warbond_ids = []
                i += 1
            elif part == "--no":
                current_option = "no"
                exclude_items = {}
                i += 1
            elif part == "--mode":
                current_option = "mode"
                i += 1
            else:
                if current_option == "lock":
                    # 解析 slot:item_id 对
                    for pair in part.split():
                        if ":" in pair:
                            slot, item_id = pair.split(":", 1)
                            locked_slots[slot.strip()] = item_id.strip()
                elif current_option == "warbond":
                    # warbond名称，可能带引号
                    raw = " ".join(parts[i:]).strip().strip('"').strip("'")
                    i = len(parts)  # consume rest
                    for wname in raw.split(","):
                        wname = wname.strip()
                        # 尝试match warbond
                        matched = self._match_warbond(wname)
                        if matched:
                            warbond_ids.append(matched)
                    break
                elif current_option == "no_warbond":
                    raw = " ".join(parts[i:]).strip().strip('"').strip("'")
                    i = len(parts)
                    for wname in raw.split(","):
                        wname = wname.strip()
                        matched = self._match_warbond(wname)
                        if matched:
                            exclude_warbond_ids.append(matched)
                    break
                elif current_option == "no":
                    raw = " ".join(parts[i:]).strip().strip('"').strip("'")
                    i = len(parts)
                    exclude_items = {"all": [x.strip() for x in raw.split(",") if x.strip()]}
                    break
                elif current_option == "mode":
                    if part.lower() in ("optimized", "optimise", "optimize", "auto"):
                        mode = "optimized"
                i += 1

        if warbond_ids is not None and len(warbond_ids) == 0:
            warbond_ids = None
        if exclude_warbond_ids is not None and len(exclude_warbond_ids) == 0:
            exclude_warbond_ids = None

        # 加载用户预设（命令行参数优先）
        user_id = event.get_sender_id()
        preset = apply_preset(user_id)
        logger.info("[HD2] user={} faction={} warbond={} exclude_wb={} exclude_items={} lock={} mode={} preset={}".format(
            user_id, faction_id, warbond_ids, exclude_warbond_ids, exclude_items,
            locked_slots, mode, preset))
        if preset.get("exclude_warbond_ids") and not exclude_warbond_ids:
            exclude_warbond_ids = preset["exclude_warbond_ids"]
        elif preset.get("exclude_warbond_ids") and exclude_warbond_ids:
            exclude_warbond_ids = list(set(exclude_warbond_ids) | set(preset["exclude_warbond_ids"]))
        if preset.get("exclude_items") and not exclude_items:
            exclude_items = preset["exclude_items"]
        if preset.get("locked_slots") and not locked_slots:
            locked_slots = preset["locked_slots"]
        elif preset.get("locked_slots") and locked_slots:
            for k, v in preset["locked_slots"].items():
                if k not in locked_slots:
                    locked_slots[k] = v

        result = self.randomizer.randomize(
            faction_id=faction_id,
            brigade_id=brigade_id,
            locked_slots=locked_slots if locked_slots else None,
            warbond_ids=warbond_ids,
            exclude_warbond_ids=exclude_warbond_ids,
            exclude_items=exclude_items,
            mode=mode,
        )

        logger.info("[HD2] result: faction={} case={} power={:.1f}".format(
            result.faction_id, result.case_name, result.power_score))
        yield event.plain_result(result.format_for_chat())

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令"""
        user_name = event.get_sender_name()
        message_str = event.message_str
        message_chain = event.get_messages()
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!")

    # ── 辅助方法 ──────────────────────────────────

    def _handle_list(self, args: list) -> str:
        if not args:
            return "Usage: /loadout list <factions|brigades [faction]|warbonds|weapons [primary/secondary/grenade]>"

        sub = args[0].lower()
        if sub in ("faction", "factions"):
            lines = ["── Factions ──"]
            for f in FACTIONS.values():
                cn = f.get("name_cn", "")
                sc = f.get("short_cn", "")
                lines.append(f"  {f['emoji']} {f['name']} / {cn} ({sc})")
            return "\n".join(lines)

        elif sub in ("brigade", "brigades"):
            faction_id = None
            if len(args) > 1:
                faction_aliases = {
                    "bugs": "terminids", "terminids": "terminids",
                    "bots": "automatons", "automatons": "automatons",
                    "squids": "illuminate", "illuminate": "illuminate",
                }
                faction_id = faction_aliases.get(args[1].lower())

            lines = ["── Brigades ──"]
            for b in BRIGADES.values():
                if faction_id and b["faction"] != faction_id:
                    continue
                faction = FACTIONS.get(b["faction"], {})
                lines.append(
                    f"  {faction.get('emoji', '')} [{b['short']}] {b['name']}"
                    f" — {b['desc']}"
                )
            if not lines[1:]:
                lines.append("  (no brigades found)")
            return "\n".join(lines)

        elif sub in ("warbond", "warbonds"):
            lines = ["── Warbonds ──"]
            for w in WARBONDS.values():
                cn = w.get("name_cn", "")
                cn_str = f" ({cn})" if cn else ""
                lines.append(f"  [{w['id']}] {w['name']}{cn_str}")
            return "\n".join(lines)

        elif sub in ("weapon", "weapons"):
            wtype = args[1].lower() if len(args) > 1 else "primary"
            pool = None
            label = ""
            if wtype == "primary":
                pool = PRIMARIES
                label = "主武器"
            elif wtype == "secondary":
                pool = SECONDARIES
                label = "副武器"
            elif wtype == "grenade":
                pool = GRENADES
                label = "投掷物"
            else:
                return f"Unknown weapon type: {wtype}. Use primary/secondary/grenade"

            lines = [f"── {label} ──"]
            for w in pool.values():
                cn = w.get('name_cn', w['name'])
                wb_data = WARBONDS.get(w.get('warbond', ''), {})
                wb_name = wb_data.get('name_cn', w.get('warbond', '?'))
                lines.append(f"  {cn} [{wb_name}]")
            return "\n".join(lines)

        return f"Unknown list type: {sub}"

    def _handle_preset(self, args: list, event) -> str:
        if not args:
            return "Usage: /loadout preset <set|show|clear> [名单]"

        user_id = event.get_sender_id()
        sub = args[0].lower()

        if sub == "set":
            rest = args[1:]
            has_flags = any(p.startswith("--") for p in rest)
            preset = load_preset(user_id)

            if has_flags:
                # 旧方式：--no-warbond / --no / --lock
                i = 0
                current = None
                while i < len(rest):
                    part = rest[i]
                    if part == "--no-warbond":
                        current = "no_wb"; i += 1
                    elif part == "--lock":
                        current = "lock"; i += 1
                    elif part == "--no":
                        current = "no"; i += 1
                    elif current == "no_wb":
                        raw = " ".join(rest[i:]).strip().strip('"').strip("'")
                        preset["exclude_warbond_ids"] = []
                        for wname in raw.split(","):
                            matched = self._match_warbond(wname.strip())
                            if matched:
                                preset["exclude_warbond_ids"].append(matched)
                        break
                    elif current == "lock":
                        for pair in rest[i].split():
                            if ":" in pair:
                                slot, item_id = pair.split(":", 1)
                                preset.setdefault("locked_slots", {})[slot.strip()] = item_id.strip()
                        i += 1
                    elif current == "no":
                        raw = " ".join(rest[i:]).strip().strip('"').strip("'")
                        preset["exclude_items"] = [x.strip() for x in raw.split(",") if x.strip()]
                        break
                    else:
                        i += 1
            else:
                # 智能模式：自动分类空格分隔的中文名 → 债券或物品
                # 先按空格拆分（中文名通常不含空格，除了带引号的）
                tokens = " ".join(rest).split()
                wb_ids = []
                item_ids = []
                unmatched = []
                for token in tokens:
                    wid = self._match_warbond(token)
                    if wid:
                        wb_ids.append(wid)
                        continue
                    item_id = self._match_item(token)
                    if item_id:
                        item_ids.append(item_id)
                        continue
                    unmatched.append(token)
                if wb_ids:
                    preset["exclude_warbond_ids"] = list(set(wb_ids))
                if item_ids:
                    preset["exclude_items"] = list(set(item_ids))
                if unmatched:
                    return "未识别: {}".format(", ".join(unmatched))

            save_preset(user_id, preset)
            lines = ["预设已保存:"]
            if preset.get("exclude_warbond_ids"):
                names = []
                for wid in preset["exclude_warbond_ids"]:
                    wb = WARBONDS.get(wid, {})
                    names.append(wb.get("name_cn", wid))
                lines.append("  排除债券: {}".format(", ".join(names)))
            if preset.get("exclude_items"):
                names = []
                for iid in preset["exclude_items"]:
                    item = self._find_item(iid)
                    if item:
                        names.append(item.get("name_cn", iid))
                    else:
                        names.append(iid)
                lines.append("  排除物品: {}".format(", ".join(names)))
            if preset.get("locked_slots"):
                lines.append("  锁定: {}".format(preset["locked_slots"]))
            return "\n".join(lines)

        elif sub == "show":
            preset = load_preset(user_id)
            if not preset:
                return "你还没有保存预设。\n使用 /loadout preset set --no-warbond <债券> 来创建。"
            lines = ["你的预设:"]
            if preset.get("exclude_warbond_ids"):
                wb_names = []
                for wid in preset["exclude_warbond_ids"]:
                    wb = WARBONDS.get(wid, {})
                    cn = wb.get("name_cn", wid)
                    wb_names.append(cn)
                lines.append(f"  排除债券: {', '.join(wb_names)}")
            if preset.get("exclude_items"):
                item_names = []
                for iid in preset["exclude_items"]:
                    item = self._find_item(iid)
                    item_names.append(item.get("name_cn", iid) if item else iid)
                lines.append("  排除物品: {}".format(", ".join(item_names)))
            if preset.get("locked_slots"):
                lines.append(f"  锁定槽位: {preset['locked_slots']}")
            return "\n".join(lines)

        elif sub == "clear":
            delete_preset(user_id)
            return "预设已清除。"

        return f"Unknown preset action: {sub}"

    def _handle_details(self, args: list) -> str:
        if not args:
            return "Usage: /loadout details <warbond|item> <name>"

        sub = args[0].lower()
        if sub in ("warbond", "warbonds"):
            if len(args) > 1:
                wb_name = " ".join(args[1:])
                wid = self._match_warbond(wb_name)
                if not wid:
                    return f"Unknown warbond: {wb_name}\nUse /loadout details warbonds to list all."
                wb = WARBONDS.get(wid, {})
                cn = wb.get("name_cn", "")
                lines = [f"── {wb['name']} ({cn}) ──"]
                lines.append(f"  ID: {wid}")
                lines.append("")
                all_pools = [
                    ("主武器", PRIMARIES),
                    ("副武器", SECONDARIES),
                    ("投掷物", GRENADES),
                    ("战备", STRATAGEMS),
                    ("盔甲", ARMORS),
                    ("被动", BOOSTERS),
                ]
                for label, pool in all_pools:
                    items = [i for i in pool.values() if i["warbond"] == wid]
                    if items:
                        lines.append(f"  ── {label} ({len(items)}) ──")
                        for it in items:
                            cn_name = it.get("name_cn", it["name"])
                            lines.append(f"    {it['id']:<40s} {cn_name}")
                if not any(1 for _, p in all_pools for i in p.values() if i["warbond"] == wid):
                    lines.append("  (no items)")
                return "\n".join(lines)
            else:
                lines = ["── Warbonds ──"]
                from collections import Counter
                counts = Counter()
                for pool in [PRIMARIES, SECONDARIES, GRENADES, STRATAGEMS, ARMORS, BOOSTERS]:
                    for item in pool.values():
                        counts[item["warbond"]] += 1
                for wid in sorted(counts.keys()):
                    wb = WARBONDS.get(wid, {})
                    cn = wb.get("name_cn", "")
                    cn_str = f" ({cn})" if cn else ""
                    lines.append(f"  [{wid}] {wb.get('name', wid)}{cn_str}  ({counts[wid]} items)")
                return "\n".join(lines)
        return f"Unknown details type: {sub}"

    def _match_warbond(self, wname: str) -> str:
        wname_lower = wname.lower().strip()
        for wid, wdata in WARBONDS.items():
            if wname_lower == wdata["name"].lower():
                return wid
            if wname_lower == wdata.get("name_cn", "").lower():
                return wid
            if wname_lower == wid.lower():
                return wid
        for wid, wdata in WARBONDS.items():
            target = (wdata["name"] + " " + wdata.get("name_cn", "")).lower()
            if wname_lower in target or (len(wname_lower) >= 5 and target in wname_lower):
                return wid
            if wid.lower().startswith(wname_lower) or wname_lower.startswith(wid.lower()):
                return wid
            # 中文: 重合字符 >= min(输入长, 名长) * 0.7
            cn = wdata.get("name_cn", "")
            if cn and len(wname_lower) >= 2 and len(cn) >= 2:
                common = sum(1 for c in wname_lower if c in cn)
                threshold = min(len(wname_lower), len(cn)) * 0.6
                if common >= threshold:
                    return wid
        return ""

    def _match_item(self, name: str) -> str:
        """通过中文名/英文名/ID 匹配物品，返回 item id"""
        name_lower = name.lower().strip()
        pools = [PRIMARIES, SECONDARIES, GRENADES, STRATAGEMS, ARMORS, BOOSTERS]
        # 精确匹配
        for pool in pools:
            for iid, item in pool.items():
                if name_lower == iid.lower():
                    return iid
                if name_lower == item.get("name_cn", "").lower():
                    return iid
                if name_lower == item["name"].lower():
                    return iid
        # 模糊匹配
        for pool in pools:
            for iid, item in pool.items():
                cn = item.get("name_cn", "")
                if len(name_lower) >= 3 and name_lower in cn.lower():
                    return iid
                # 中文重合度
                if cn and len(name_lower) >= 2 and len(cn) >= 2:
                    common = sum(1 for c in name_lower if c in cn)
                    threshold = min(len(name_lower), len(cn)) * 0.6
                    if common >= threshold:
                        return iid
        return ""

    def _find_item(self, iid: str):
        """根据 id 找物品 dict"""
        for pool in [PRIMARIES, SECONDARIES, GRENADES, STRATAGEMS, ARMORS, BOOSTERS]:
            if iid in pool:
                return pool[iid]
        return None

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
