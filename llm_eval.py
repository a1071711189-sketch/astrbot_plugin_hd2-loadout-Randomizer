"""
LLM 配装评价模块
通过 AstrBot 的 LLM 引擎对随机配装进行分析
"""

# AstrBot 4.x 的 LLM 调用方式:
# Star 基类持有 self.context，可通过它获取 LLM 实例
# self.context.get_llm() 返回 LLM 引擎
# 或通过 self.context.text_completion(prompt) 同步调用


async def evaluate_loadout(plugin_instance, event, loadout_text: str, faction_cn: str, case_cn: str) -> str:
    """
    异步调用 LLM 评价配装

    Args:
        plugin_instance: Star 实例 (self)
        event: AstrMessageEvent
        loadout_text: format_for_chat() 的输出文本
        faction_cn: 中文派系名
        case_cn: 中文旅团名

    Returns:
        LLM 评价文本，失败时返回空字符串
    """
    try:
        prompt = (
            "你是《绝地潜兵2》的战术顾问。请用中文简要评价以下随机配装。\n"
            "从三个角度分析（每个角度一句话即可，总共不超过5句话）：\n"
            "1. 协同性：武器和战备之间的配合\n"
            "2. 针对性：面对【{} — {}】时的适用程度\n"
            "3. 改进建议：如果有一个槽位可以换，换什么\n\n"
            "配装详情：\n{}\n\n"
            "请直接输出评价，不要复述配装列表。".format(faction_cn, case_cn, loadout_text)
        )

        # 尝试多种 AstrBot LLM 调用方式
        llm_response = None

        # 方式1: Star.context.get_llm()
        if hasattr(plugin_instance, "context") and plugin_instance.context:
            ctx = plugin_instance.context
            if hasattr(ctx, "get_llm"):
                llm = ctx.get_llm()
                if llm and hasattr(llm, "text_completion"):
                    llm_response = await llm.text_completion(prompt)
            elif hasattr(ctx, "text_completion"):
                llm_response = await ctx.text_completion(prompt)

        # 方式2: 通过 event 发送请求
        if not llm_response and hasattr(event, "request_llm"):
            llm_response = await event.request_llm(prompt)

        # 方式3: 通过 event.get_platform() 的 LLM 能力
        if not llm_response:
            from astrbot.api.message_components import Plain
            platform = event.get_platform()
            if platform and hasattr(platform, "llm_chat"):
                resp = await platform.llm_chat([{"role": "user", "content": prompt}])
                if resp:
                    llm_response = resp.get("content", "") if isinstance(resp, dict) else str(resp)

        if llm_response:
            return "💬 战术评价:\n" + str(llm_response).strip()

    except Exception as e:
        from astrbot.api import logger
        logger.warning("[HD2] LLM evaluation failed: {}".format(e))

    return ""
