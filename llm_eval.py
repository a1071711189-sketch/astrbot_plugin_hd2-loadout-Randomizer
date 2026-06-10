"""
LLM 配装评价模块
通过 AstrBot v4.5.7+ 的 context.llm_generate() 调用 LLM
并自动携带用户设定的人格提示词
"""


async def evaluate_loadout(plugin_instance, event, loadout_text: str, faction_cn: str, case_cn: str) -> str:
    try:
        ctx = plugin_instance.context
        umo = event.unified_msg_origin
        provider_id = await ctx.get_current_chat_provider_id(umo=umo)

        # 获取用户当前人格的 system_prompt
        system_prompt = ""
        try:
            persona_mgr = ctx.persona_manager
            if persona_mgr:
                # 获取当前会话绑定的 persona_id
                conv_mgr = ctx.conversation_manager
                curr_cid = await conv_mgr.get_curr_conversation_id(umo)
                conversation = await conv_mgr.get_conversation(umo, curr_cid)
                if conversation and conversation.persona_id:
                    persona = persona_mgr.get_persona(conversation.persona_id)
                    if persona and persona.system_prompt:
                        system_prompt = persona.system_prompt
        except Exception:
            pass

        prompt = (
            "请用中文简要评价以下《绝地潜兵2》随机配装。\n"
            "从三个角度分析（每个角度一句话，总共不超过5句话）：\n"
            "1. 协同性：武器和战备之间的配合\n"
            "2. 针对性：面对【{} — {}】时的适用程度\n"
            "3. 改进建议：如果有一个槽位可以换，换什么\n\n"
            "配装详情：\n{}\n\n"
            "请直接输出评价，不要复述配装列表。".format(faction_cn, case_cn, loadout_text)
        )

        kwargs = {"chat_provider_id": provider_id, "prompt": prompt}
        if system_prompt:
            kwargs["system_prompt"] = system_prompt

        llm_resp = await ctx.llm_generate(**kwargs)

        response = llm_resp.completion_text
        if response:
            return "\n".join(["💬 战术评价:", response.strip()])

    except Exception as e:
        from astrbot.api import logger
        logger.warning("[HD2] LLM evaluation failed: {}".format(e))

    return ""
