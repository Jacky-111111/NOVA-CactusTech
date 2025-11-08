from agentuity import AgentRequest, AgentResponse, AgentContext
from openai import AsyncOpenAI

# 初始化 OpenAI 客户端
client = AsyncOpenAI()

# 简单短期记忆（进程内缓存）
short_term_memory = []


async def run(request: AgentRequest, response: AgentResponse, context: AgentContext):
    """
    EchoMinder 主逻辑入口（适配旧版 Agentuity）
    """
    try:
        text = (await request.data.text()).strip()

        # 显示记忆
        if text.lower().startswith("show memory"):
            return response.json({
                "current_memory": short_term_memory
            })

        # 用 LLM 生成一句话摘要
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the key facts and intent in ONE short sentence."},
                {"role": "user", "content": text}
            ]
        )

        summary = completion.choices[0].message.content.strip()

        short_term_memory.append(summary)
        if len(short_term_memory) > 10:
            short_term_memory.pop(0)

        context.logger.info(f"[EchoMinder] Stored summary: {summary}")

        return response.json({
            "received": text,
            "summary": summary,
            "current_memory": short_term_memory
        })

    except Exception as e:
        context.logger.error(f"[EchoMinder] Error: {e}")
        return response.text(f"EchoMinder error: {e}")