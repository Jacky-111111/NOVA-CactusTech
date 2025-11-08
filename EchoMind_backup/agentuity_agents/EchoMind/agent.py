from agentuity import AgentRequest, AgentResponse, AgentContext
from openai import AsyncOpenAI

client = AsyncOpenAI()

short_term_memory = []

# 手动注册 agent（旧版不支持装饰器）
AGENT_NAME = "EchoMind"
AGENT_DESCRIPTION = "An agent that remembers short-term context and summarizes user input."


def welcome():
    return {
        "welcome": "Welcome to EchoMind! I can summarize and remember your recent context to help LLMs think smarter.",
        "prompts": [
            {
                "data": "Remember this: I am Jack, building EchoMind for NOVA Hackathon.",
                "contentType": "text/plain"
            },
            {
                "data": "Summarize the last 3 memories.",
                "contentType": "text/plain"
            }
        ]
    }


async def run(request: AgentRequest, response: AgentResponse, context: AgentContext):
    try:
        user_message = await request.data.text()

        completion = await client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Summarize the user's message in one concise sentence capturing key info."},
                {"role": "user", "content": user_message},
            ],
        )

        summary = completion.choices[0].message.content.strip()

        short_term_memory.append(summary)
        if len(short_term_memory) > 10:
            short_term_memory.pop(0)

        context.logger.info(f"[EchoMind] Stored summary: {summary}")

        return response.json({
            "received": user_message,
            "summary": summary,
            "current_memory": short_term_memory
        })

    except Exception as e:
        context.logger.error(f"Error in EchoMind agent: {e}")
        return response.text("Sorry, EchoMind encountered an error.")