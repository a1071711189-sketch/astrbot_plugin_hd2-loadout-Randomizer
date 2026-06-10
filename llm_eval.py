"""
LLM 配装评价模块
通过 AstrBot v4.5.7+ 的 context.llm_generate() 调用 LLM
"""


async def evaluate_loadout(plugin_instance, event, loadout_text: str, faction_cn: str, case_cn: str) -> str:
    try:
        ctx = plugin_instance.context
        umo = event.unified_msg_origin
        provider_id = await ctx.get_current_chat_provider_id(umo=umo)

        prompt = (
            "你是《绝地潜兵2》的战术顾问。请用中文简要评价以下随机配装。\n"
            "从三个角度分析（每个角度一句话即可，总共不超过5句话）：\n"
            "1. 协同性：武器和战备之间的配合\n"
            "2. 针对性：面对【{} — {}】时的适用程度\n"
            "3. 改进建议：如果有一个槽位可以换，换什么\n\n"
            "配装详情：\n{}\n\n"
            "请直接输出评价，不要复述配装列表。".format(faction_cn, case_cn, loadout_text)
        )

        llm_resp = await ctx.llm_generate(
            chat_provider_id=provider_id,
            prompt=prompt,
        )

        response = llm_resp.completion_text
        if response:
            return "\n".join(["💬 战术评价:", response.strip()])

    except Exception as e:
        from astrbot.api import logger
        logger.warning("[HD2] LLM evaluation failed: {}".format(e))

    return ""
