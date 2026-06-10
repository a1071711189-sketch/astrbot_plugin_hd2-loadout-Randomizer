from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import *

from .randomizer import LoadoutRandomizer
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
        # 移除指令前缀
        if message_str.startswith("/loadout"):
            args_str = message_str[len("/loadout"):].strip()
        else:
            args_str = message_str

        if not args_str or args_str.lower() in ("random", ""):
            result = self.randomizer.randomize(faction_id="random")
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

        result = self.randomizer.randomize(
            faction_id=faction_id,
            brigade_id=brigade_id,
            locked_slots=locked_slots if locked_slots else None,
            warbond_ids=warbond_ids,
            exclude_warbond_ids=exclude_warbond_ids,
            exclude_items=exclude_items,
            mode=mode,
        )

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
                label = "Primary Weapons"
            elif wtype == "secondary":
                pool = SECONDARIES
                label = "Secondary Weapons"
            elif wtype == "grenade":
                pool = GRENADES
                label = "Grenades"
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
                    ("Primary", PRIMARIES),
                    ("Secondary", SECONDARIES),
                    ("Grenade", GRENADES),
                    ("Stratagem", STRATAGEMS),
                    ("Armor", ARMORS),
                    ("Booster", BOOSTERS),
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
            if wname_lower in wdata["name"].lower():
                return wid
            if wname_lower in wdata.get("name_cn", "").lower():
                return wid
        return ""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
