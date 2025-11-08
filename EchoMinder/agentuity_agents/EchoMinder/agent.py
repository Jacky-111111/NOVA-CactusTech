from agentuity import AgentRequest, AgentResponse, AgentContext
from openai import AsyncOpenAI
import json, os

# ==============================
# 初始化 OpenAI 客户端
# ==============================
client = AsyncOpenAI()

# ==============================
# 三层记忆结构
# ==============================
short_term_memory = []     # 近期对话摘要
summary_memory = []        # 中期主题总结
long_term_memory = []      # 持久化记忆（写入文件）

LONG_TERM_FILE = "echominder_long_term.json"
SHORT_TERM_LIMIT = 10
SUMMARY_LIMIT = 10


# ==============================
# 工具函数
# ==============================
def load_long_term():
    """加载长期记忆"""
    global long_term_memory
    if os.path.exists(LONG_TERM_FILE):
        try:
            with open(LONG_TERM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    long_term_memory = [str(x) for x in data]
        except Exception:
            long_term_memory = []


def save_long_term():
    """保存长期记忆"""
    try:
        with open(LONG_TERM_FILE, "w", encoding="utf-8") as f:
            json.dump(long_term_memory, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# 启动时加载
load_long_term()


# ==============================
# 主逻辑入口
# ==============================
async def run(request: AgentRequest, response: AgentResponse, context: AgentContext):
    """
    EchoMinder 主逻辑入口（保持与 Agentuity 兼容）
    """
    try:
        text = (await request.data.text()).strip()
        if not text:
            return response.text("⚠️ Empty input — please say something for EchoMinder to process.")

        text_lower = text.lower()

        # =========================================
        # 1️⃣ 显示当前记忆
        # =========================================
        if text_lower.startswith("show memory") or text_lower.startswith("recall"):
            return response.json({
                "mode": "recall",
                "short_term_memory": short_term_memory[-5:],
                "summary_memory": summary_memory[-5:],
                "long_term_memory": long_term_memory[-5:]
            })

        # =========================================
        # 2️⃣ 存储长期记忆（用户主动）
        # =========================================
        if text_lower.startswith("remember ") or text_lower.startswith("remember that"):
            fact = text.replace("remember that", "").replace("remember", "").strip()
            if not fact:
                fact = text
            long_term_memory.append(fact)
            save_long_term()
            context.logger.info(f"[EchoMinder] Stored fact: {fact}")
            return response.json({
                "mode": "manual_store",
                "stored": fact,
                "long_term_count": len(long_term_memory)
            })

        # =========================================
        # 3️⃣ 普通消息：生成摘要并更新短期记忆
        # =========================================
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are EchoMinder, an AI that extracts the key idea from each message in one concise sentence."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        summary = completion.choices[0].message.content.strip()
        if not summary or "please provide" in summary.lower():
            summary = f"User said: {text}"

        # 更新短期记忆
        short_term_memory.append(summary)
        if len(short_term_memory) > SHORT_TERM_LIMIT:
            short_term_memory.pop(0)

        # 更新中期记忆
        summary_memory.append(summary)
        if len(summary_memory) > SUMMARY_LIMIT:
            # 将中期记忆打包进长期
            merged = " | ".join(summary_memory[-SUMMARY_LIMIT:])
            long_term_memory.append(merged)
            save_long_term()
            summary_memory.clear()
            context.logger.info("[EchoMinder] Consolidated summaries into long-term memory.")

        # =========================================
        # 返回结果
        # =========================================
        context.logger.info(f"[EchoMinder] Stored summary: {summary}")
        return response.json({
            "mode": "encode",
            "received": text,
            "summary": summary,
            "short_term_memory_tail": short_term_memory[-5:],
            "summary_memory_tail": summary_memory[-5:],
            "long_term_count": len(long_term_memory),
            "hint": "You can say 'remember ...' or 'show memory' to interact with EchoMinder’s memory."
        })

    except Exception as e:
        context.logger.error(f"[EchoMinder] Error: {e}")
        return response.text(f"EchoMinder error: {e}")