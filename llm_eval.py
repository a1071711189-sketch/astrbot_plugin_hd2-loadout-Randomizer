"""
LLM 配装评价模块
通过 AstrBot 的 LLM 引擎对随机配装进行分析
"""


async def evaluate_loadout(plugin_instance, event, loadout_text: str, faction_cn: str, case_cn: str) -> str:
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

        if not hasattr(plugin_instance, "context") or not plugin_instance.context:
            return ""

        ctx = plugin_instance.context
        response = None

        # 尝试1: context.text_completion (AstrBot v4 常见方式)
        if hasattr(ctx, "text_completion"):
            try:
                result = ctx.text_completion(prompt)
                # ProviderRequest 不是 awaitable，直接同步返回
                if hasattr(result, "result"):
                    response = str(result.result)
                elif hasattr(result, "text"):
                    response = str(result.text)
                elif isinstance(result, str):
                    response = result
                else:
                    # 可能是 awaitable
                    try:
                        resp = await result
                        if hasattr(resp, "text"):
                            response = str(resp.text)
                        elif hasattr(resp, "result"):
                            response = str(resp.result)
                        elif isinstance(resp, str):
                            response = resp
                        elif isinstance(resp, dict):
                            response = resp.get("content", resp.get("text", str(resp)))
                    except:
                        pass
            except Exception as e:
                from astrbot.api import logger
                logger.debug("[HD2] text_completion failed: {}".format(e))

        # 尝试2: LLMProvider
        if not response:
            try:
                provider = ctx.get_using_provider()
                if provider and hasattr(provider, "text_chat"):
                    response = await provider.text_chat(prompt)
                    if hasattr(response, "completion_text"):
                        response = str(response.completion_text)
                    elif isinstance(response, str):
                        pass
                    elif isinstance(response, dict):
                        response = response.get("content", response.get("text", str(response)))
            except:
                pass

        # 尝试3: 直接 pipeline
        if not response:
            try:
                from astrbot.core.pipeline import ProcessPipeline
                pipeline = ProcessPipeline()
                pipeline_resp = await pipeline.text_completion(prompt, ctx)
                if pipeline_resp:
                    response = str(pipeline_resp)
            except:
                pass

        if response:
            response = str(response).strip()
            if response:
                return "💬 战术评价:\n" + response

    except Exception as e:
        from astrbot.api import logger
        logger.warning("[HD2] LLM evaluation failed: {}".format(e))

    return ""
